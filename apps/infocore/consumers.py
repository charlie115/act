import asyncio
import json
import pickle

from channels.generic.websocket import AsyncWebsocketConsumer
from django_redis import get_redis_connection
from urllib.parse import parse_qsl

from users.models import User  # noqa: F401

redis_conn = get_redis_connection("default")


class KlineConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._thread = None
        self._redis_ps = redis_conn.pubsub(ignore_subscribe_messages=True)

    def __del__(self, *args, **kwargs):
        # Cleanup
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
            self._redis_ps.subscribe(**{channel_name: self._callback})
            self._thread = self._redis_ps.run_in_thread(sleep_time=60, daemon=True)

    async def publish(self, message):
        if message and message.get("type", None) == "message":
            data = {
                "result": None,
                "type": "publish",
                "status": "OK",
            }

            try:
                data["result"] = pickle.loads(message["data"]).to_json(orient="records")
            except TypeError as err:
                data["status"] = "UNAVAILABLE"
                data["error"] = {"message": str(err)}
            except Exception as err:
                data["status"] = "ERROR"
                data["error"] = {"message": str(err)}

            await self.send(json.dumps(data))

    def _callback(self, message):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(self.publish(message))
        loop.close()

    async def disconnect(self, code):
        self._redis_ps.unsubscribe()
        self._thread.stop()
        self._thread._running.set()

        super().disconnect(code)
