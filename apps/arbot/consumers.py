import asyncio
import json
import pickle

from channels.generic.websocket import AsyncWebsocketConsumer
from django_redis import get_redis_connection
from threading import Thread, Event
from urllib.parse import parse_qsl


redis_conn = get_redis_connection("default")


class CoinConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._thread = None
        self._stop_event = Event()

    async def connect(self):
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

        query_params = dict(parse_qsl(self.scope["query_string"].decode()))
        exchange_market_1 = query_params.get("exchange_market_1", None)
        exchange_market_2 = query_params.get("exchange_market_2", None)
        period = query_params.get("period", None)

        if exchange_market_1 and exchange_market_2 and period:
            self.cache_key = (
                f"INFO_CORE|{exchange_market_1}:{exchange_market_2}_{period}_now"
            )

            self._thread = Thread(target=self._callback)
            self._thread.start()

    async def process_requests(self):
        while True:
            if not self._stop_event.is_set():
                try:
                    data = {
                        "result": pickle.loads(redis_conn.get(self.cache_key)).to_json(
                            orient="records"
                        ),
                        "type": "push",
                        "status": "OK",
                    }
                except TypeError:
                    data = {
                        "result": "",
                        "type": "push",
                        "status": "UNAVAILABLE",
                    }
                await self.send(json.dumps(data))
                await asyncio.sleep(0.5)
            else:
                break

    def _callback(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(self.process_requests())
        loop.close()

    async def disconnect(self, code):
        self._stop_event.set()
        super().disconnect(code)
