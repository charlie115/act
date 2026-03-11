import os
import sys
import pymongo
from loggers.logger import TradeCoreLogger


class InitDBClient:
    def __init__(self, host, port, user, passwd, logging_dir=None):
        self.logger = None
        self.host = host
        self.port = port
        self.username = user
        self.password = passwd
        self.uri = f"mongodb://{user}:{passwd}@{host}:{port}/"
        if logging_dir is not None:
            self.logger = TradeCoreLogger("InitDBClient", logging_dir).logger

    def get_conn(self):
        mongo_client = pymongo.MongoClient(self.uri)
        return mongo_client
