import os
import sys
import psycopg2
from loggers.logger import InfoCoreLogger

class InitDBClient:
    def __init__(self, host, port, user, passwd, database, create_database=True, logging_dir=None):
        self.logger = None
        self.host = host
        self.port = port
        self.user = user
        self.passwd = passwd
        self.database = database
        if logging_dir is not None:
            self.logger = InfoCoreLogger("InitDBClient", logging_dir).logger
        if create_database:
            conn = psycopg2.connect(host=host, port=port, user=user, password=passwd)
            conn.autocommit = True
            curr = conn.cursor()
            res = curr.execute(f"SELECT 1 FROM pg_database WHERE datname='{database}'")
            res = curr.fetchone()
            if res is None:
                if self.logger is not None:
                    self.logger.info(f"InitDBClient|SCHEMA: {database} does not exist. Creating...")
                curr.execute(f"CREATE DATABASE {database}")
            else:
                if self.logger is not None:
                    self.logger.info(f"InitDBClient|SCHEMA: {database} already exists.")
            curr.close()
            conn.close()

    def get_conn(self):
        conn = psycopg2.connect(host=self.host, port=self.port, user=self.user, password=self.passwd, database=self.database)
        return conn
