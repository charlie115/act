import os
import sys
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from loggers.logger import KimpBotLogger

class InitDBClient:
    def __init__(self, host, port, user, passwd, database, create_database=True, pool_min_con=1, pool_max_con=20, logging_dir=None):
        self.logger = None
        self.host = host
        self.port = port
        self.user = user
        self.passwd = passwd
        self.database = database
        self.pool = ThreadedConnectionPool(pool_min_con, pool_max_con, host=host, port=port, user=user, password=passwd, database=database)
        if logging_dir is not None:
            self.logger = KimpBotLogger("InitDBClient", logging_dir).logger
        if create_database:
            conn = psycopg2.connect(host=host, port=port, user=user, password=passwd, database='postgres')
            conn.autocommit = True
            curr = conn.cursor()
            res = curr.execute(f"SELECT 1 FROM pg_database WHERE datname='{database}'")
            res = curr.fetchone()
            if res is None:
                if self.logger is not None:
                    self.logger.info(f"InitDBClient|SCHEMA: {database} does not exist. Creating...")
                else:
                    print(f"InitDBClient|SCHEMA: {database} does not exist. Creating...")
                curr.execute(f"CREATE DATABASE {database}")
            else:
                if self.logger is not None:
                    self.logger.info(f"InitDBClient|SCHEMA: {database} already exists.")
                else:
                    print(f"InitDBClient|SCHEMA: {database} already exists.")
            curr.close()
            conn.close()

    def get_conn(self):
        conn = psycopg2.connect(host=self.host, port=self.port, user=self.user, password=self.passwd, database=self.database)
        return conn

    def create_all_tables(self):
        self.create_user_info()
        self.create_exchange_config()
        self.create_trade()

    def check_table_exist(self, table_name):
        query = f"""
        SELECT EXISTS (
           SELECT FROM information_schema.tables 
           WHERE  table_schema = 'public'
           AND table_name   = '{table_name}'
        );
        """
        conn = self.get_conn()
        curr = conn.cursor()
        curr.execute(query)
        exist_flag = curr.fetchone()[0]
        return exist_flag
    
    def create_user_info(self, table_name='user_info'):
        # First check whether the table exists
        if self.check_table_exist(table_name):
            if self.logger is not None:
                self.logger.info(f"InitDBClient|TABLE: {table_name} already exists.")
            else:
                print(f"InitDBClient|TABLE: {table_name} already exists.")
            return
        query = f"""
            CREATE TABLE IF NOT EXISTS {table_name}
            (
                id SERIAL PRIMARY KEY,
                user_uuid TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                telegram_id BIGINT,
                telegram_name TEXT,
                registered_datetime TIMESTAMP,
                status TEXT,
                send_times INTEGER,
                send_term INTEGER,
                remark TEXT
            )"""
        conn = self.get_conn()
        curr = conn.cursor()
        curr.execute(query)
        conn.commit()
        curr.close()
        conn.close()
        if self.logger is not None:
            self.logger.info(f"InitDBClient|TABLE: {table_name} created.")
        else:
            print(f"InitDBClient|TABLE: {table_name} created.")

    def create_exchange_config(self, table_name='exchange_config'):
        # First check whether the table exists
        if self.check_table_exist(table_name):
            if self.logger is not None:
                self.logger.info(f"InitDBClient|TABLE: {table_name} already exists.")
            else:
                print(f"InitDBClient|TABLE: {table_name} already exists.")
            return
        query = f"""
            CREATE TABLE IF NOT EXISTS {table_name}
            (
                id SERIAL PRIMARY KEY,
                user_uuid TEXT NOT NULL, 
                registered_datetime TIMESTAMP,
                service_datetime_end TIMESTAMP, -- PostgreSQL uses TIMESTAMP for both date and time
                target_market_code TEXT NOT NULL,
                origin_market_code TEXT NOT NULL,
                target_market_uid TEXT,
                origin_market_uid TEXT,
                target_market_referral_use BOOLEAN,
                origin_market_referral_use BOOLEAN,
                target_market_cross BOOLEAN,
                target_market_leverage INTEGER,
                origin_market_cross BOOLEAN,
                origin_market_leverage INTEGER,
                target_market_margin_call SMALLINT,
                origin_market_margin_call SMALLINT,
                target_market_safe_reverse BOOLEAN,
                origin_market_safe_reverse BOOLEAN,
                target_market_risk_threshold_p REAL,
                origin_market_risk_threshold_p REAL,
                repeat_limit_p REAL,
                repeat_limit_direction TEXT,
                repeat_num_limit INTEGER,
                on_off BOOLEAN,
                remark TEXT,
                FOREIGN KEY (user_uuid) REFERENCES user_info(user_uuid)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
            )"""
        conn = self.get_conn()
        curr = conn.cursor()
        curr.execute(query)
        conn.commit()
        curr.close()
        conn.close()
        if self.logger is not None:
            self.logger.info(f"InitDBClient|TABLE: {table_name} created.")
        else:
            print(f"InitDBClient|TABLE: {table_name} created.")

    def create_trade(self, table_name='trade'):
        # First check whether the table exists
        if self.check_table_exist(table_name):
            if self.logger is not None:
                self.logger.info(f"InitDBClient|TABLE: {table_name} already exists.")
            else:
                print(f"InitDBClient|TABLE: {table_name} already exists.")
            return
        query = f"""
            CREATE TABLE IF NOT EXISTS {table_name}
            (
                id SERIAL PRIMARY KEY,
                user_uuid TEXT NOT NULL,
                registered_datetime TIMESTAMP,
                last_updated_datetime TIMESTAMP,
                uuid TEXT NOT NULL,
                connected_repeat_uuid TEXT,
                base_asset TEXT NOT NULL,
                usdt_conversion BOOLEAN NOT NULL,
                target_market_code TEXT NOT NULL,
                origin_market_code TEXT NOT NULL,
                low REAL NOT NULL,
                high REAL NOT NULL,
                trigger_switch SMALLINT,
                trade_switch SMALLINT,
                trade_capital REAL,
                enter_target_market_order_id TEXT,
                enter_origin_market_order_id TEXT,
                exit_target_market_order_id TEXT,
                exit_origin_market_order_id TEXT,
                status TEXT,
                remark TEXT,
                FOREIGN KEY (user_uuid) REFERENCES user_info(user_uuid)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
            )"""
        conn = self.get_conn()
        curr = conn.cursor()
        curr.execute(query)
        conn.commit()
        curr.close()
        conn.close()
        if self.logger is not None:
            self.logger.info(f"InitDBClient|TABLE: {table_name} created.")
        else:
            print(f"InitDBClient|TABLE: {table_name} created.")

    def create_repeat_trade(self, table_name='repeat_trade'):
        # First check whether the table exists
        if self.check_table_exist(table_name):
            if self.logger is not None:
                self.logger.info(f"InitDBClient|TABLE: {table_name} already exists.")
            else:
                print(f"InitDBClient|TABLE: {table_name} already exists.")
            return
        query = f"""
            CREATE TABLE IF NOT EXISTS {table_name}
            (
                id SERIAL PRIMARY KEY,
                user_uuid TEXT NOT NULL,
                last_update_datetime TIMESTAMP,
                uuid TEXT NOT NULL,
                base_asset TEXT NOT NULL,
                usdt_conversion BOOLEAN NOT NULL,
                auto_low REAL,
                auto_high REAL,
                pauto_num REAL,
                switch SMALLINT,
                auto_trade_switch SMALLINT,
                auto_trade_capital REAL,
                enter_target_market_order_id TEXT,
                enter_origin_market_order_id TEXT,
                exit_target_market_order_id TEXT,
                exit_origin_market_order_id TEXT,
                status TEXT NOT NULL,
                remark TEXT,
                FOREIGN KEY (user_uuid) REFERENCES user_info(user_uuid)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
            )"""
        conn = self.get_conn()
        curr = conn.cursor()
        curr.execute(query)
        conn.commit()
        curr.close()
        conn.close()
        if self.logger is not None:
            self.logger.info(f"InitDBClient|TABLE: {table_name} created.")
        else:
            print(f"InitDBClient|TABLE: {table_name} created.")