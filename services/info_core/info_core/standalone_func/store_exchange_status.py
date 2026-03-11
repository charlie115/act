from loggers.logger import InfoCoreLogger
from threading import Thread
import time
from traceback import format_exc
from etc.redis_connector.redis_helper import RedisHelper

local_redis = RedisHelper()
prefix = "servercheck:"

def fetch_market_servercheck(market_code):
    fetched_data = local_redis.get_data(f"{prefix}{market_code}")
    if fetched_data:
        decoded_data = fetched_data.decode('utf-8')
        if decoded_data == "true":
            return True
        else:
            return False
    return False

def store_markets_servercheck(acw_api, ex=60):
    exchange_statuses = acw_api.get_exchange_status()
    for each_exchange_status in exchange_statuses:
        servercheck = False
        if each_exchange_status['server_check']:
            servercheck = True
            local_redis.set_data(f"{prefix}{each_exchange_status['market_code']}", "true" if servercheck else "false", ex)
        else:
            local_redis.set_data(f"{prefix}{each_exchange_status['market_code']}", "true" if servercheck else "false", ex)

def store_markets_servercheck_loop(acw_api, logging_dir=None, interval_secs=5):
    logger = InfoCoreLogger(f"store_markets_servercheck_loop", logging_dir).logger
    logger.info(f"Starting store_markets_servercheck_loop with interval_secs: {interval_secs}")
    while True:
        try:
            servercheck = store_markets_servercheck(acw_api, ex=interval_secs*5)
        except Exception as e:
            logger.error(f"Error in store_markets_servercheck_loop: {e}, {format_exc()}")
        time.sleep(interval_secs)