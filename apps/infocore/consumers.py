import asyncio
import json
import pickle
import threading

from channels.generic.websocket import AsyncWebsocketConsumer
from django_redis import get_redis_connection
from urllib.parse import parse_qsl

from users.models import User  # noqa: F401


REDIS_CLI = get_redis_connection("default")


class KlineConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._redis_ps = None
        self._thread = None
        self._stop = False

    def __del__(self, *args, **kwargs):
        # Cleanup
        if self._redis_ps:
            self._redis_ps.close()

    async def connect(self):
        # # Authentication
        # if type(self.scope["user"]) != User:
        #     await self.close()

        query_params = dict(parse_qsl(self.scope["query_string"].decode()))
        target_market_code = query_params.get("target_market_code", None)
        origin_market_code = query_params.get("origin_market_code", None)
        interval = query_params.get("interval", None)

        if target_market_code and origin_market_code and interval:
            await self.accept()

            await self.send(
                json.dumps(
                    {
                        "result": "Connected to AWC websocket!",
                        "type": "connect",
                        "status": "OK",
                    }
                )
            )

            channel_name = (
                f"INFO_CORE|{target_market_code}:{origin_market_code}_{interval}_now"
            )

            self._redis_ps = REDIS_CLI.pubsub(ignore_subscribe_messages=True)
            self._redis_ps.subscribe(channel_name)

            self._thread = threading.Thread(target=asyncio.run, args=(self.publish(),))
            self._thread.start()

    async def publish(self):
        while not self._stop:
            message = self._redis_ps.get_message()
            if message and message.get("type", None) == "message":
                data = {
                    "result": None,
                    "type": "publish",
                    "status": "OK",
                }

                try:
                    data["result"] = pickle.loads(message["data"]).to_json(
                        orient="records"
                    )
                except TypeError as err:
                    data["status"] = "UNAVAILABLE"
                    data["error"] = {"message": str(err)}
                except Exception as err:
                    data["status"] = "ERROR"
                    data["error"] = {"message": str(err)}

                await self.send(json.dumps(data))
                await asyncio.sleep(0.05)

    async def disconnect(self, code):
        self._stop = True

        if self._thread:
            del self._thread

        if self._redis_ps:
            self._redis_ps.unsubscribe()

        super().disconnect(code)
