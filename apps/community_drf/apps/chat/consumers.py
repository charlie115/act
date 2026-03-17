import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from datetime import datetime
from django.conf import settings
from django.core.cache import cache
from platform_common.integrations.chat import (
    get_chat_mongo_client,
    get_chat_redis_connection,
)

from lib.datetime import DATE_FORMAT_NUM, TZ_ASIA_SEOUL, TZ_UTC
from users.models import UserBlocklist


REDIS_CLI = get_chat_redis_connection(client_name="django")
MONGODB_CLI = get_chat_mongo_client(appname="django-chat-ws")


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close()
            return

        self.user = user
        self.mongodb = MONGODB_CLI.get_database(settings.MONGO_CHAT_DB)
        self.headers = {
            header[0].decode(): header[1].decode() for header in self.scope["headers"]
        }

        self.ip = self.headers.get(
            "x-real-ip",
            self.headers.get("x-forwarded-for", self.headers["host"].split(":")[0]),
        )
        self.ip_blocklist = []
        self.username_blocklist = []

        self.group_name = "chat"
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)

        if "message" in data:
            now = datetime.now(TZ_UTC)

            chat = {
                "type": "chatbox_message",
                "email": self.user.email,
                "username": self.user.username,
                "message": data.get("message"),
                "ip": self.ip,
                "datetime": now,
                "status": "OK",
            }

            await self.get_blocklist()

            if (
                self.user.username in self.username_blocklist
                and self.ip in self.ip_blocklist
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
                }
            )
        )

    @database_sync_to_async
    def save_chat(self, chat, collection):
        # To avoid overwriting the same chat variable sent to websocket
        # TypeError: can not serialize 'ObjectId' object
        _chat = chat.copy()

        chats = self.mongodb[collection]
        chats.insert_one(_chat)

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    @database_sync_to_async
    def get_blocklist(self):
        blocklist = cache.get(settings.REDIS_CHAT_BLOCKLIST_KEY)
        if blocklist is None:
            blocklist = UserBlocklist.objects.all()
            username_list = list(blocklist.values_list("target_username", flat=True))
            ip_list = list(blocklist.values_list("target_ip", flat=True))
            cache.set(
                settings.REDIS_CHAT_BLOCKLIST_KEY,
                {"usernames": username_list, "ips": ip_list},
                timeout=None,
            )
        else:
            username_list = blocklist.get("usernames", [])
            ip_list = blocklist.get("ips", [])
        self.username_blocklist = [
            username for username in username_list if bool(username)
        ]
        self.ip_blocklist = ip_list
