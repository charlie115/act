import json
import logging
import time

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from datetime import datetime
from django.conf import settings
from django.core.cache import cache
from platform_common.integrations.chat import (
    get_chat_mongo_client,
    get_chat_redis_connection,
)
from pymongo.errors import PyMongoError

from lib.datetime import DATE_FORMAT_NUM, TZ_ASIA_SEOUL, TZ_UTC
from lib.validators.nickname import validate_nickname_format, validate_nickname_not_reserved
from users.models import User, UserBlocklist


REDIS_CLI = get_chat_redis_connection(client_name="django")
MONGODB_CLI = get_chat_mongo_client(appname="django-chat-ws")

# Maximum allowed message length (characters)
MAX_MESSAGE_LENGTH = 2000

# Blocklist cache TTL in seconds (5 minutes)
BLOCKLIST_CACHE_TTL = 300

# Minimum interval between messages for anonymous users (seconds)
ANON_RATE_LIMIT_SECONDS = 3

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")

        self.is_anon = not user or not user.is_authenticated
        self.mongodb = MONGODB_CLI.get_database(settings.MONGO_CHAT_DB)
        self.headers = {
            header[0].decode(): header[1].decode() for header in self.scope["headers"]
        }

        # S4-BUG3 fix: use .get() with fallback for host header
        host = self.headers.get("host", "")
        self.ip = self.headers.get(
            "x-real-ip",
            self.headers.get("x-forwarded-for", host.split(":")[0]),
        )
        self.ip_blocklist = []
        self.username_blocklist = []

        if self.is_anon:
            self.user = None
            self.nickname = None  # Will be set from first message
            self._last_message_time = 0.0
        else:
            self.user = user
            self.nickname = getattr(user, "chat_nickname", None) or user.username

        self.group_name = "chat"
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        await self.accept()

    async def receive(self, text_data):
        # S4-BUG2 fix: handle malformed JSON gracefully
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({"error": "Invalid JSON"}))
            return

        if "message" in data:
            message = data.get("message")

            # S4-BUG6 fix: validate message length
            if not message or not isinstance(message, str):
                return
            if len(message) > MAX_MESSAGE_LENGTH:
                await self.send(text_data=json.dumps({
                    "error": f"Message too long (max {MAX_MESSAGE_LENGTH} characters)"
                }))
                return

            # --- Anonymous user handling ---
            if self.is_anon:
                # Rate limit: reject if < ANON_RATE_LIMIT_SECONDS since last message
                now_monotonic = time.monotonic()
                if now_monotonic - self._last_message_time < ANON_RATE_LIMIT_SECONDS:
                    await self.send(text_data=json.dumps({
                        "error": "Please wait a few seconds between messages."
                    }))
                    return
                self._last_message_time = now_monotonic

                # Read nickname from message data
                client_nickname = data.get("nickname")
                if not client_nickname or not isinstance(client_nickname, str):
                    await self.send(text_data=json.dumps({
                        "error": "Nickname is required for anonymous users."
                    }))
                    return

                # Validate nickname format and reserved words
                valid, error = validate_nickname_format(client_nickname)
                if not valid:
                    await self.send(text_data=json.dumps({"error": error}))
                    return

                valid, error = validate_nickname_not_reserved(client_nickname)
                if not valid:
                    await self.send(text_data=json.dumps({"error": error}))
                    return

                # Ensure the nickname is not a registered user's chat_nickname or username
                is_taken = await self._is_nickname_taken_by_user(client_nickname)
                if is_taken:
                    await self.send(text_data=json.dumps({
                        "error": "This nickname belongs to a registered user."
                    }))
                    return

                self.nickname = client_nickname
                email = ""
                username = client_nickname
            else:
                # Authenticated: always use server-side nickname, ignore client-sent
                email = self.user.email
                username = self.nickname

            now = datetime.now(TZ_UTC)

            chat = {
                "type": "chatbox_message",
                "email": email,
                "username": username,
                "message": message,
                "ip": self.ip,
                "datetime": now,
                "status": "OK",
                "is_anon": self.is_anon,
            }

            await self.get_blocklist()

            # S4-BUG1 fix: block if username OR IP matches (not AND)
            # For anonymous users, check by IP; for logged-in, check by username or IP
            if self.is_anon:
                if self.ip in self.ip_blocklist:
                    chat["status"] = "BLOCKED"
            else:
                if (
                    self.user.username in self.username_blocklist
                    or self.ip in self.ip_blocklist
                ):
                    chat["status"] = "BLOCKED"

            # Mongodb collection is in KST to be easier for devs viewing the db
            await self.save_chat(
                chat,
                collection=now.astimezone(TZ_ASIA_SEOUL).strftime(DATE_FORMAT_NUM),
            )

            chat["datetime"] = chat["datetime"].isoformat()
            await self.channel_layer.group_send(self.group_name, chat)

    async def chatbox_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "message": event["message"],
                    "username": event["username"],
                    "datetime": event["datetime"],
                    "status": event["status"],
                    "is_anon": event.get("is_anon", False),
                }
            )
        )

    @database_sync_to_async
    def save_chat(self, chat, collection):
        # To avoid overwriting the same chat variable sent to websocket
        # TypeError: can not serialize 'ObjectId' object
        _chat = chat.copy()

        # S4-BUG8 fix: handle MongoDB errors gracefully
        try:
            chats = self.mongodb[collection]
            chats.insert_one(_chat)
        except PyMongoError:
            logger.exception("Failed to save chat message to MongoDB")

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    @database_sync_to_async
    def get_blocklist(self):
        blocklist = cache.get(settings.REDIS_CHAT_BLOCKLIST_KEY)
        if not isinstance(blocklist, dict):
            # Cache miss or stale format (e.g., raw QuerySet from old code)
            qs = UserBlocklist.objects.all()
            username_list = list(qs.values_list("target_username", flat=True))
            ip_list = list(qs.values_list("target_ip", flat=True))
            cache.set(
                settings.REDIS_CHAT_BLOCKLIST_KEY,
                {"usernames": username_list, "ips": ip_list},
                timeout=BLOCKLIST_CACHE_TTL,
            )
        else:
            username_list = blocklist.get("usernames", [])
            ip_list = blocklist.get("ips", [])
        self.username_blocklist = [
            username for username in username_list if bool(username)
        ]
        self.ip_blocklist = ip_list

    @database_sync_to_async
    def _is_nickname_taken_by_user(self, nickname):
        """Check if the nickname matches any registered user's chat_nickname or username (case-insensitive)."""
        from django.db.models import Q

        return User.objects.filter(
            Q(chat_nickname__iexact=nickname) | Q(username__iexact=nickname)
        ).exists()
