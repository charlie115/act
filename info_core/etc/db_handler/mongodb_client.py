import os
import sys
import pymongo
upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from loggers.logger import InfoCoreLogger


class InitDBClient:
    def __init__(self, host, port, user, passwd, logging_dir=None):
        self.logger = None
        self.host = host
        self.port = port
        self.username = user
        self.password = passwd
        self.uri = f"mongodb://{user}:{passwd}@{host}:{port}/"
        if logging_dir is not None:
            self.logger = InfoCoreLogger("InitDBClient", logging_dir).logger

    def get_conn(self):
        mongo_client = pymongo.MongoClient(self.uri)
        return mongo_client
