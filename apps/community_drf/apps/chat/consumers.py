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

        if "username" in data and "message" in data:
            now = datetime.now(TZ_UTC)

            chat = {
                "type": "chatbox_message",
                "email": data.get("email", None),
                "username": data.get("username"),
                "message": data.get("message"),
                "ip": self.ip,
                "datetime": now,
                "status": "OK",
            }

            await self.get_blocklist()

            if (
                data.get("username", None) in self.username_blocklist
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

    async def save_chat(self, chat, collection):
        # To avoid overwriting the same chat variable sent to websocket
        # TypeError: can not serialize 'ObjectId' object
        _chat = chat.copy()

        chats = self.mongodb[collection]
        chats.insert_one(_chat)

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    @database_sync_to_async
    def get_blocklist(self):
        blocklist = cache.get("acw:user:blocklist")
        if blocklist is None:
            blocklist = UserBlocklist.objects.all()
            cache.set(
                settings.REDIS_CHAT_BLOCKLIST_KEY,
                blocklist,
                timeout=None,
            )
        self.username_blocklist = [
            username
            for username in blocklist.values_list("target_username", flat=True)
            if bool(username)
        ]
        self.ip_blocklist = list(blocklist.values_list("target_ip", flat=True))
