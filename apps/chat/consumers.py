import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from datetime import datetime
from django.conf import settings
from django.core.cache import cache
from django_redis import get_redis_connection
from pymongo import MongoClient
from pytz import timezone

from lib.datetime import ASIA_SEOUL_TZ, DATE_TIME_FORMAT, DATE_FORMAT_NUM


REDIS_CLI = get_redis_connection("default")
MONGODB_CLI = MongoClient(
    host=settings.MONGODB["HOST"],
    port=settings.MONGODB["PORT"],
    username=settings.MONGODB["USERNAME"],
    password=settings.MONGODB["PASSWORD"],
)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.mongodb = MONGODB_CLI.get_database(settings.MONGO_CHAT_DB)
        self.headers = {
            header[0].decode(): header[1].decode() for header in self.scope["headers"]
        }

        self.ip = self.headers["host"].split(":")[0]
        self.ip_blocklist = []
        self.email_blocklist = []

        self.group_name = "chat"
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)

        if "username" in data and "message" in data:
            now_kst = datetime.now(tz=timezone(ASIA_SEOUL_TZ))

            chat = {
                "type": "chatbox_message",
                "email": data["email"],
                "username": data["username"],
                "message": data["message"],
                "ip": self.ip,
                "datetime": now_kst.strftime(DATE_TIME_FORMAT),
                "status": "OK",
            }

            await self.save_chat(chat, collection=now_kst.strftime(DATE_FORMAT_NUM))

            await self.get_blocklist()

            if data["email"] in self.email_blocklist or self.ip in self.ip_blocklist:
                chat["message"] = None
                chat["status"] = "BLOCKED"

            await self.channel_layer.group_send(self.group_name, chat)

    async def chatbox_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "message": event["message"],
                    "username": event["username"],
                    "datetime": event["datetime"],
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
        self.email_blocklist = list(blocklist.values_list("target_email", flat=True))
        self.ip_blocklist = list(blocklist.values_list("target_ip", flat=True))
