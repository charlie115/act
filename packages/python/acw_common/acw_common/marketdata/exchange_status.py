import logging
import threading
import time
from traceback import format_exc

_PREFIX = "servercheck:"
_SERVERCHECK_CACHE = {}
_SERVERCHECK_CACHE_LOCK = threading.Lock()
_SERVERCHECK_CACHE_TTL = 0.5


def fetch_market_servercheck(market_code, redis_client):
    """
    Check if a market is under server maintenance.

    Uses an in-memory cache (0.5s TTL) to avoid hitting Redis on every call.
    """
    now = time.time()
    with _SERVERCHECK_CACHE_LOCK:
        cached = _SERVERCHECK_CACHE.get(market_code)
        if cached and cached["expires_at"] > now:
            return cached["value"]

    fetched_data = redis_client.get_data(f"{_PREFIX}{market_code}")
    if fetched_data:
        decoded_data = fetched_data.decode("utf-8")
        result = decoded_data == "true"
    else:
        result = False

    with _SERVERCHECK_CACHE_LOCK:
        _SERVERCHECK_CACHE[market_code] = {
            "value": result,
            "expires_at": now + _SERVERCHECK_CACHE_TTL,
        }
    return result


def store_markets_servercheck(acw_api, redis_client, ex=60):
    """Fetch exchange status from API and store in Redis."""
    exchange_statuses = acw_api.get_exchange_status()
    for each_exchange_status in exchange_statuses:
        servercheck = bool(each_exchange_status["server_check"])
        redis_client.set_data(
            f"{_PREFIX}{each_exchange_status['market_code']}",
            "true" if servercheck else "false",
            ex,
        )


def store_markets_servercheck_loop(acw_api, redis_client, logger=None, interval_secs=5):
    """Continuously poll exchange status and store in Redis."""
    if logger is None:
        logger = logging.getLogger("store_markets_servercheck_loop")
    logger.info(f"Starting store_markets_servercheck_loop with interval_secs: {interval_secs}")
    while True:
        try:
            store_markets_servercheck(acw_api, redis_client, ex=interval_secs * 5)
        except Exception as e:
            logger.error(f"Error in store_markets_servercheck_loop: {e}, {format_exc()}")
        time.sleep(interval_secs)
