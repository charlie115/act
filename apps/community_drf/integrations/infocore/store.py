from django.conf import settings
from django_redis import get_redis_connection
from pymongo import MongoClient


def get_infocore_redis_connection(client_name=None):
    redis_cli = get_redis_connection("default")
    if client_name:
        redis_cli.client_setname(client_name)
    return redis_cli


def get_infocore_mongo_client(appname):
    return MongoClient(
        host=settings.MONGODB["HOST"],
        port=settings.MONGODB["PORT"],
        username=settings.MONGODB["USERNAME"],
        password=settings.MONGODB["PASSWORD"],
        appname=appname,
    )

