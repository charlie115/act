import asyncio
import json
import math
import pickle
import threading

from channels.generic.websocket import AsyncWebsocketConsumer
from platform_common.integrations.infocore import get_infocore_redis_connection
from urllib.parse import parse_qsl

from users.models import User  # noqa: F401


REDIS_CLI = get_infocore_redis_connection()


def _normalize_signature_value(value):
    if value is None:
        return None

    if isinstance(value, float) and math.isnan(value):
        return None

    try:
        if value != value:
            return None
    except Exception:
        pass

    return value


class KlineConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._thread = None
        self._stop = False
        self._channel_name = None
        self._initialized = False
        self._row_signatures = {}
        self._record_columns = None

    async def connect(self):
        # # Authentication
        # if type(self.scope["user"]) != User:
        #     await self.close()
        
        query_params = dict(parse_qsl(self.scope["query_string"].decode()))
        target_market_code = query_params.get("target_market_code", None)
        origin_market_code = query_params.get("origin_market_code", None)
        interval = query_params.get("interval", None)
        self._base_asset = query_params.get("base_asset", None)

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

            self._channel_name = (
                f"INFO_CORE|{target_market_code}:{origin_market_code}_{interval}_now"
            )

            self._thread = threading.Thread(target=asyncio.run, args=(self.publish(),))
            self._thread.start()

    async def publish(self):
        while not self._stop:
            stream = REDIS_CLI.xread(
                streams={self._channel_name: "$"},
                count=1,
                block=0,
            )
            if stream:
                stream = stream[0]

                data = {
                    "result": None,
                    "type": "publish",
                    "status": "OK",
                }

                try:
                    stream_key, stream_data = stream
                    entry_id, entry_data = stream_data[0]
                    kline_df = pickle.loads(entry_data[b"data"])
                    if self._base_asset:
                        concise_kline_df = kline_df[kline_df["base_asset"] == self._base_asset]
                    else:
                        concise_kline_df = kline_df.drop(columns=[
                            "tp_open",
                            "tp_high",
                            "tp_high",
                            "tp_low",
                            "tp_close",
                            "LS_open",
                            "LS_high",
                            "LS_low",
                            "SL_open",
                            "SL_high",
                            "SL_low",
                            "datetime_now",
                        ])

                    if concise_kline_df.empty:
                        continue

                    records = concise_kline_df.to_dict(orient="records")
                    if self._record_columns is None:
                        self._record_columns = [
                            column for column in concise_kline_df.columns if column != "base_asset"
                        ]

                    changed_records = []
                    next_signatures = {}
                    for record in records:
                        base_asset = record.get("base_asset")
                        if not base_asset:
                            continue
                        signature = tuple(
                            _normalize_signature_value(record.get(column))
                            for column in self._record_columns
                        )
                        next_signatures[base_asset] = signature
                        if not self._initialized or self._row_signatures.get(base_asset) != signature:
                            changed_records.append(record)

                    self._row_signatures = next_signatures
                    if not changed_records and self._initialized:
                        continue

                    self._initialized = True
                    data["result"] = json.dumps(changed_records, ensure_ascii=False)

                except Exception as err:
                    data["status"] = "ERROR"
                    data["error"] = {"message": str(err)}

                await self.send(json.dumps(data))

    async def disconnect(self, code):
        self._stop = True

        if self._thread:
            del self._thread

        super().disconnect(code)
