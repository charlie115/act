import asyncio
import json
import math
import pickle
from datetime import date, datetime
from functools import partial
from zoneinfo import ZoneInfo

from channels.generic.websocket import AsyncWebsocketConsumer
from platform_common.integrations.infocore import get_infocore_redis_connection
from urllib.parse import parse_qsl

from users.models import User  # noqa: F401


REDIS_CLI = get_infocore_redis_connection()
KST = ZoneInfo("Asia/Seoul")
UTC = ZoneInfo("UTC")


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


def _normalize_stream_id(value):
    if isinstance(value, bytes):
        return value.decode()
    return value


def _json_safe_value(value):
    normalized = _normalize_signature_value(value)
    if normalized is None:
        return None

    if isinstance(normalized, bytes):
        return normalized.decode()

    if isinstance(normalized, (datetime, date)):
        if isinstance(normalized, datetime):
            if normalized.tzinfo is None:
                normalized = normalized.replace(tzinfo=UTC)
            normalized = normalized.astimezone(KST)
        return normalized.isoformat()

    if hasattr(normalized, "isoformat") and not isinstance(normalized, str):
        try:
            return normalized.isoformat()
        except Exception:
            pass

    if hasattr(normalized, "item"):
        try:
            return normalized.item()
        except Exception:
            pass

    return normalized


class KlineConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._publish_task = None
        self._stop = False
        self._channel_name = None
        self._initialized = False
        self._row_signatures = {}
        self._record_columns = None

    async def connect(self):
        # Authentication
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close()
            return

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

            self._publish_task = asyncio.ensure_future(self.publish())

    def _build_publish_payload(self, entry_data):
        data = {
            "result": None,
            "type": "publish",
            "status": "OK",
        }

        try:
            kline_df = pickle.loads(entry_data[b"data"])
            if self._base_asset:
                concise_kline_df = kline_df[kline_df["base_asset"] == self._base_asset]
            else:
                concise_kline_df = kline_df.drop(
                    columns=[
                        "tp_open",
                        "tp_high",
                        "tp_low",
                        "tp_close",
                        "LS_open",
                        "LS_high",
                        "LS_close",
                        "LS_low",
                        "SL_open",
                        "SL_high",
                        "SL_low",
                        "datetime_now",
                    ]
                )

            if concise_kline_df.empty:
                return None

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
                return None

            self._initialized = True
            if self._base_asset:
                changed_records = [
                    {key: _json_safe_value(value) for key, value in record.items()}
                    for record in changed_records
                ]

            data["result"] = json.dumps(changed_records, ensure_ascii=False)
            return data
        except Exception as err:
            data["status"] = "ERROR"
            data["error"] = {"message": str(err)}
            return data

    async def publish(self):
        loop = asyncio.get_running_loop()
        last_entry_id = "0-0"
        latest_entries = await loop.run_in_executor(
            None, partial(REDIS_CLI.xrevrange, self._channel_name, count=1)
        )
        if latest_entries:
            latest_entry_id, latest_entry_data = latest_entries[0]
            last_entry_id = _normalize_stream_id(latest_entry_id)
            latest_payload = self._build_publish_payload(latest_entry_data)
            if latest_payload is not None:
                await self.send(json.dumps(latest_payload))

        while not self._stop:
            stream = await loop.run_in_executor(
                None,
                partial(
                    REDIS_CLI.xread,
                    streams={self._channel_name: last_entry_id},
                    count=10,
                    block=1000,
                ),
            )
            if stream:
                stream_key, stream_data = stream[0]
                for entry_id, entry_data in stream_data:
                    last_entry_id = _normalize_stream_id(entry_id)
                    payload = self._build_publish_payload(entry_data)
                    if payload is not None:
                        await self.send(json.dumps(payload))

    async def disconnect(self, code):
        self._stop = True

        if self._publish_task:
            self._publish_task.cancel()
            try:
                await self._publish_task
            except asyncio.CancelledError:
                pass
            self._publish_task = None

        await super().disconnect(code)
