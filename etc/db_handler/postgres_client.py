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
        if logging_dir is not None:
            self.logger = KimpBotLogger("InitDBClient", logging_dir).logger
        if create_database is True:
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
        self.pool = ThreadedConnectionPool(pool_min_con, pool_max_con, host=host, port=port, user=user, password=passwd, database=database)

    def get_conn(self):
        conn = psycopg2.connect(host=self.host, port=self.port, user=self.user, password=self.passwd, database=self.database)
        return conn

    def create_all_tables(self):
        self.create_trade_config()
        self.create_trade()
        self.create_trade_log()
        self.create_repeat_trade()
        self.create_exchange_api_key()
        self.create_order_history()
        self.create_trade_history()
        self.create_pnl_history()

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
    
    def is_table_empty(self, table_name):
        conn = self.get_conn()
        cur = conn.cursor()        
        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cur.fetchone()[0]
        conn.close()
        return count == 0

    def get_column_names(self, table_name):
        conn = self.get_conn()
        curr = conn.cursor()
        curr.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position;
        """, (table_name,))
        column_names = [row[0] for row in curr.fetchall()]
        conn.close()
        return column_names

    def create_trade_config(self, table_name='trade_config'):
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
                uuid UUID DEFAULT gen_random_uuid() UNIQUE,
                user UUID NOT NULL,
                telegram_id BIGINT NOT NULL,
                send_times INTEGER,
                send_term INTEGER,
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
                target_market_risk_threshold_p NUMERIC(6, 3),
                origin_market_risk_threshold_p NUMERIC(6, 3),
                repeat_limit_p NUMERIC(6, 3),
                repeat_limit_direction TEXT,
                repeat_num_limit INTEGER,
                on_off BOOLEAN,
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
                uuid UUID DEFAULT gen_random_uuid() UNIQUE,
                trade_config_uuid UUID NOT NULL,
                registered_datetime TIMESTAMP,
                last_updated_datetime TIMESTAMP,
                base_asset TEXT NOT NULL,
                usdt_conversion BOOLEAN NOT NULL,
                low NUMERIC(8, 3) NOT NULL,
                high NUMERIC(8, 3) NOT NULL,
                trigger_switch SMALLINT,
                trade_switch SMALLINT,
                trade_capital INTEGER,
                last_trade_history_uuid UUID,
                status TEXT,
                remark TEXT,
                FOREIGN KEY (trade_config_uuid) REFERENCES trade_config(uuid)
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

    def create_trade_log(self, table_name='trade_log'):
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
                uuid UUID UNIQUE,
                trade_config_uuid UUID NOT NULL,
                registered_datetime TIMESTAMP,
                last_updated_datetime TIMESTAMP,
                base_asset TEXT NOT NULL,
                usdt_conversion BOOLEAN NOT NULL,
                low NUMERIC(8, 3) NOT NULL,
                high NUMERIC(8, 3) NOT NULL,
                trade_capital INTEGER,
                deleted BOOLEAN,
                status TEXT,
                remark TEXT,
                FOREIGN KEY (trade_config_uuid) REFERENCES trade_config(uuid)
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
                uuid UUID DEFAULT gen_random_uuid() UNIQUE,
                trade_uuid UUID NOT NULL,
                registered_datetime TIMESTAMP,
                last_update_datetime TIMESTAMP,
                pauto_num NUMERIC(6, 3),
                switch SMALLINT,
                auto_trade_switch SMALLINT,
                enter_target_market_order_id TEXT,
                enter_origin_market_order_id TEXT,
                exit_target_market_order_id TEXT,
                exit_origin_market_order_id TEXT,
                status TEXT,
                remark TEXT,
                FOREIGN KEY (trade_uuid) REFERENCES trade(uuid)
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

    def create_exchange_api_key(self, table_name='exchange_api_key'):
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
                uuid UUID DEFAULT gen_random_uuid() UNIQUE,
                trade_config_uuid UUID NOT NULL,
                registered_datetime TIMESTAMP,
                last_update_datetime TIMESTAMP,
                market_code TEXT NOT NULL,
                exchange TEXT NOT NULL,
                spot BOOLEAN NOT NULL,
                futures BOOLEAN NOT NULL,
                access_key BYTEA NOT NULL,
                secret_key BYTEA NOT NULL,
                passphrase BYTEA,
                remark TEXT,
                FOREIGN KEY (trade_config_uuid) REFERENCES trade_config(uuid)
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

    def create_order_history(self, table_name='order_history'):
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
                order_id TEXT UNIQUE,
                trade_config_uuid UUID NOT NULL,
                trade_uuid UUID NOT NULL,
                registered_datetime TIMESTAMP,
                order_type TEXT NOT NULL,
                market_code TEXT NOT NULL,
                symbol TEXT NOT NULL,
                quote_asset TEXT NOT NULL,
                side TEXT NOT NULL,
                price NUMERIC(21, 11) NOT NULL,
                qty NUMERIC(22, 9) NOT NULL,
                fee NUMERIC(15, 9),
                remark TEXT,
                FOREIGN KEY (trade_config_uuid) REFERENCES trade_config(uuid)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE,
                FOREIGN KEY (trade_uuid) REFERENCES trade_log(uuid)
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

    def create_trade_history(self, table_name='trade_history'):
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
                uuid UUID DEFAULT gen_random_uuid() UNIQUE,
                trade_config_uuid UUID NOT NULL,
                trade_uuid UUID NOT NULL,
                registered_datetime TIMESTAMP,
                trade_side TEXT NOT NULL,
                base_asset TEXT NOT NULL,
                target_order_id TEXT NOT NULL,
                origin_order_id TEXT NOT NULL,
                target_premium_value NUMERIC(8, 3) NOT NULL,
                executed_premium_value NUMERIC(8, 3) NOT NULL,
                slippage_p NUMERIC(6, 3) NOT NULL,
                dollar NUMERIC(5, 1) NOT NULL,
                remark TEXT,
                FOREIGN KEY (trade_config_uuid) REFERENCES trade_config(uuid)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE,
                FOREIGN KEY (trade_uuid) REFERENCES trade_log(uuid)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE,
                FOREIGN KEY (target_order_id) REFERENCES order_history(order_id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE,
                FOREIGN KEY (origin_order_id) REFERENCES order_history(order_id)
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

    def create_pnl_history(self, table_name='pnl_history'):
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
                uuid UUID DEFAULT gen_random_uuid() UNIQUE,
                trade_config_uuid UUID NOT NULL,
                trade_uuid UUID NOT NULL,
                registered_datetime TIMESTAMP,
                market_code_combination TEXT NOT NULL,
                enter_trade_history_uuid UUID NOT NULL,
                exit_trade_history_uuid UUID NOT NULL,
                realized_premium_gap_p NUMERIC(6, 3) NOT NULL,
                target_currency TEXT NOT NULL,
                target_pnl NUMERIC(13, 6) NOT NULL,
                target_total_fee NUMERIC(13, 6) NOT NULL,
                target_pnl_after_fee NUMERIC(13, 6) NOT NULL,
                origin_currency TEXT NOT NULL,
                origin_pnl NUMERIC(13, 6) NOT NULL,
                origin_total_fee NUMERIC(13, 6) NOT NULL,
                origin_pnl_after_fee NUMERIC(13, 6) NOT NULL,
                total_currency TEXT NOT NULL,
                total_pnl NUMERIC(13, 6) NOT NULL,
                total_pnl_after_fee NUMERIC(13, 6) NOT NULL,
                total_pnl_after_fee_kimp NUMERIC(13, 6),
                remark TEXT,
                FOREIGN KEY (trade_config_uuid) REFERENCES trade_config(uuid)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE,
                FOREIGN KEY (trade_uuid) REFERENCES trade_log(uuid)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE,
                FOREIGN KEY (enter_trade_history_uuid) REFERENCES trade_history(uuid)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE,
                FOREIGN KEY (exit_trade_history_uuid) REFERENCES trade_history(uuid)
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