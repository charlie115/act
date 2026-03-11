from integrations.infocore.store import (
    get_infocore_mongo_client,
    get_infocore_redis_connection,
)


def get_chat_redis_connection(client_name=None):
    return get_infocore_redis_connection(client_name=client_name)


def get_chat_mongo_client(appname):
    return get_infocore_mongo_client(appname=appname)

