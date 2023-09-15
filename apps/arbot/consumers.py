import asyncio
import json
import pickle

from channels.generic.websocket import AsyncWebsocketConsumer
from django_redis import get_redis_connection
from urllib.parse import parse_qsl


redis_conn = get_redis_connection("default")


class CoinConsumer(AsyncWebsocketConsumer):
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
            cache_key = f"{exchange_market_1}:{exchange_market_2}_{period}_now"

            while True:
                await self.send(
                    json.dumps(
                        {
                            "result": pickle.loads(redis_conn.get(cache_key)).to_json(
                                orient="records"
                            ),
                            "type": "push",
                        }
                    )
                )
                await asyncio.sleep(0.5)
