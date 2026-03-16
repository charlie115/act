"""Backward-compatible wrapper around acw_common.marketdata.exchange_status."""

from _acw_common import ensure_acw_common_on_path

ensure_acw_common_on_path()

from functools import partial  # noqa: E402

from etc.redis_connector.redis_helper import RedisHelper  # noqa: E402
from loggers.logger import InfoCoreLogger  # noqa: E402
from acw_common.marketdata.exchange_status import (  # noqa: E402
    fetch_market_servercheck as _fetch,
    store_markets_servercheck as _store,
    store_markets_servercheck_loop as _loop,
)

_local_redis = RedisHelper()


def fetch_market_servercheck(market_code):
    return _fetch(market_code, _local_redis)


def store_markets_servercheck(acw_api, ex=60):
    return _store(acw_api, _local_redis, ex=ex)


def store_markets_servercheck_loop(acw_api, logging_dir=None, interval_secs=5):
    logger = InfoCoreLogger("store_markets_servercheck_loop", logging_dir).logger
    return _loop(acw_api, _local_redis, logger=logger, interval_secs=interval_secs)
