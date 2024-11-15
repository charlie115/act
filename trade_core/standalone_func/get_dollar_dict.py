from etc.redis_connector.redis_helper import RedisHelper

def get_dollar_dict():
    local_redis = RedisHelper()
    dollar_dict = local_redis.get_dict('INFO_CORE|dollar')
    return dollar_dict