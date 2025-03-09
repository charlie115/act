def get_dollar_dict(redis_client):
    dollar_dict = redis_client.get_dict('INFO_CORE|dollar')
    return dollar_dict