import os
import sys
import pymysql
from mysql.connector import pooling
upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from loggers.logger import KimpBotLogger

class InitDBPool:
    def __init__(self, host, port, user, passwd, database, pool_name=None, logging_dir=None):
        self.connection_pool = pooling.MySQLConnectionPool(
            pool_name=pool_name,
            pool_size=5,
            pool_reset_session=True,
            host=host,
            port=port,
            database=database,
            user=user,
            password=passwd,
            autocommit=True
        )


class InitDBClient:
    def __init__(self, host, port, user, passwd, database, create_database=False, logging_dir=None):
        self.create_schema_tables_logger = None
        if logging_dir is not None:
            self.create_schema_tables_logger = KimpBotLogger("create_schema_tables_logger", logging_dir).logger
        if create_database:
            conn = pymysql.connect(
                host=host,
                port=port,
                user=user,
                passwd=passwd,
                charset='utf8mb4'
            )
            curr = conn.cursor()
            res = curr.execute(f"""CREATE DATABASE IF NOT EXISTS {database}""")
            curr.close()
            conn.close()
            if self.create_schema_tables_logger is not None:
                if res == 1:
                    self.create_schema_tables_logger.info(f"InitDBClient|SCHEMA: {database} has been created.")
                else:
                    self.create_schema_tables_logger.info(f"InitDBClient|SCHEMA: {database} already exists.")
        self.conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            passwd=passwd,
            database=database,
            charset='utf8mb4'
        )
        self.curr = self.conn.cursor(pymysql.cursors.DictCursor)
        if self.create_schema_tables_logger is not None:
            self.create_schema_tables_logger.info(f"InitDBClient|Mariadb client has been connected to {host} - {database}.")

    def create_all_table(self, master_node=False):
        self.create_user_info()
        self.create_addcoin()
        self.create_addcir()
        self.create_trade_history()
        self.create_pnl_history()
        self.create_user_log()
        self.create_kimp_diff()
        self.create_user_api_key()
        self.create_messages()
        
        if master_node:
            self.create_master_user_info()
            self.create_payment_history()
            self.create_server_check()
            self.create_price_info()
            self.create_dollar200()
            self.create_funding_info()
            self.create_executives()
            self.create_refer_coupon()

    def create_master_user_info(self, table_name='master_user_info'):
        res = self.curr.execute(f"""SHOW TABLES LIKE '{table_name}'""")
        if self.create_schema_tables_logger is not None:
            if res == 0:
                self.create_schema_tables_logger.info(f"create_master_user_info|TABLE {table_name} has been created.")
            else:
                self.create_schema_tables_logger.info(f"create_master_user_info|TABLE {table_name} already exists.")
        sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name}
        (
        id int(10) NOT NULL AUTO_INCREMENT PRIMARY KEY,
        datetime datetime,
        status text,
        referral_code text,
        user_id bigint,
        user_name text,
        registered_node text,
        webuser_email text,
        webuser_nickname text,
        remark text
        )
        """
        self.curr.execute(sql)

    def create_user_info(self, table_name='user_info'):
        res = self.curr.execute(f"""SHOW TABLES LIKE '{table_name}'""")
        if self.create_schema_tables_logger is not None:
            if res == 0:
                self.create_schema_tables_logger.info(f"create_user_info|TABLE {table_name} has been created.")
            else:
                self.create_schema_tables_logger.info(f"create_user_info|TABLE {table_name} already exists.")
        sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name}
        (
        user_id bigint NOT NULL PRIMARY KEY,
        register_origin text,
        datetime timestamp,
        datetime_end datetime,
        status text,
        user_name text,
        okx_uid int,
        referral_use tinyint,
        referral_code text,
        interest_coin text,
        okx_leverage int,
        okx_cross tinyint,
        okx_margin_call tinyint,
        safe_reverse tinyint,
        alarm_num int,
        alarm_period int,
        kimp_diff float,
        addcir_limit float,
        addcir_num_limit int,
        exd_percent float,
        kimp_diff_wallet tinyint,
        kimp_diff_coin longblob,
        on_off tinyint,
        remark text
        )
        """
        self.curr.execute(sql)
    
    def create_addcoin(self, table_name='addcoin'):
        res = self.curr.execute(f"""SHOW TABLES LIKE '{table_name}'""")
        if self.create_schema_tables_logger is not None:
            if res == 0:
                self.create_schema_tables_logger.info(f"create_addcoin|TABLE {table_name} has been created.")
            else:
                self.create_schema_tables_logger.info(f"create_addcoin|TABLE {table_name} already exists.")
        sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name}
        (
        id int(10) NOT NULL AUTO_INCREMENT PRIMARY KEY,
        user_id bigint,
        datetime timestamp,
        last_updated_timestamp bigint,
        redis_uuid text,
        symbol text,
        addcoin_uuid text,
        high float,
        low float,
        rolling_window int,
        switch tinyint,
        auto_trade_switch int,
        auto_trade_capital float,
        enter_upbit_uuid text,
        enter_okx_orderId text,
        exit_upbit_uuid text,
        exit_okx_orderId text,
        remark text,
        FOREIGN KEY(user_id) REFERENCES user_info(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
        )
        """
        self.curr.execute(sql)

    def create_addcir(self, table_name='addcir'):
        res = self.curr.execute(f"""SHOW TABLES LIKE '{table_name}'""")
        if self.create_schema_tables_logger is not None:
            if res == 0:
                self.create_schema_tables_logger.info(f"create_addcir|TABLE {table_name} has been created.")
            else:
                self.create_schema_tables_logger.info(f"create_addcir|TABLE {table_name} already exists.")
        sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name}
        (
        id int(10) NOT NULL AUTO_INCREMENT PRIMARY KEY,
        user_id bigint,
        datetime timestamp,
        last_updated_timestamp bigint,
        redis_uuid text,
        symbol text,
        addcir_uuid text,
        auto_low float,
        auto_high float,
        pauto_num float,
        fauto_num float,
        cir_trade_switch tinyint,
        cir_trade_capital float,
        cir_trade_num int,
        remark text,
        FOREIGN KEY(user_id) REFERENCES user_info(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
        )
        """
        self.curr.execute(sql)

    def create_kimp_diff(self, table_name='kimp_diff'):
        res = self.curr.execute(f"""SHOW TABLES LIKE '{table_name}'""")
        if self.create_schema_tables_logger is not None:
            if res == 0:
                self.create_schema_tables_logger.info(f"create_kimp_diff|TABLE {table_name} has been created.")
            else:
                self.create_schema_tables_logger.info(f"create_kimp_diff|TABLE {table_name} already exists.")
        sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name}
        (
        id int(10) NOT NULL AUTO_INCREMENT PRIMARY KEY,
        datetime timestamp,
        user_id bigint,
        exchange text,
        symbol text,
        remark text,
        FOREIGN KEY(user_id) REFERENCES user_info(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
        )
        """
        self.curr.execute(sql)

    def create_trade_history(self, table_name='trade_history'):
        res = self.curr.execute(f"""SHOW TABLES LIKE '{table_name}'""")
        if self.create_schema_tables_logger is not None:
            if res == 0:
                self.create_schema_tables_logger.info(f"create_trade_history|TABLE {table_name} has been created.")
            else:
                self.create_schema_tables_logger.info(f"create_trade_history|TABLE {table_name} already exists.")
        sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name}
        (
        id int(10) NOT NULL AUTO_INCREMENT PRIMARY KEY,
        user_id bigint,
        datetime timestamp,
        timestamp bigint,
        symbol text,
        addcoin_redis_uuid text,
        dollar float,
        upbit_uuid text,
        upbit_side text,
        upbit_price float,
        upbit_qty double,
        okx_orderId text,
        okx_mgnMode text,
        okx_leverage int,
        okx_side text,
        okx_price float,
        okx_price_krw float,
        okx_liquidation_price float,
        okx_qty double,
        targeted_kimp float,
        executed_kimp float,
        targeted_usdt float,
        executed_usdt float,
        remark text,
        FOREIGN KEY(user_id) REFERENCES user_info(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
        )
        """
        self.curr.execute(sql)

    def create_pnl_history(self, table_name='pnl_history'):
        res = self.curr.execute(f"""SHOW TABLES LIKE '{table_name}'""")
        if self.create_schema_tables_logger is not None:
            if res == 0:
                self.create_schema_tables_logger.info(f"create_pnl_history|TABLE {table_name} has been created.")
            else:
                self.create_schema_tables_logger.info(f"create_pnl_history|TABLE {table_name} already exists.")
        sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name}
        (
        id int(10) NOT NULL AUTO_INCREMENT PRIMARY KEY,
        user_id bigint,
        datetime timestamp,
        timestamp bigint,
        redis_uuid text,
        symbol text,
        dollar_enter float,
        dollar_exit float,
        kimp_enter float,
        kimp_exit float,
        usdt_enter float,
        usdt_exit float,
        upbit_enter_value float,
        upbit_enter_fee float,
        upbit_exit_value float,
        upbit_exit_fee float,
        upbit_pnl float,
        okx_enter_value float,
        okx_enter_fee float,
        okx_enter_value_krw float,
        okx_exit_value float,
        okx_exit_fee float,
        okx_exit_value_krw float,
        okx_pnl float,
        okx_pnl_krw float,
        okx_pnl_after_kimp float,
        okx_pnl_krw_after_kimp float,
        total_pnl float,
        total_pnl_after_kimp float,
        remark text,
        FOREIGN KEY(user_id) REFERENCES user_info(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
        )
        """
        self.curr.execute(sql)

    def create_user_log(self, table_name='user_log'):
        res = self.curr.execute(f"""SHOW TABLES LIKE '{table_name}'""")
        if self.create_schema_tables_logger is not None:
            if res == 0:
                self.create_schema_tables_logger.info(f"create_user_log|TABLE {table_name} has been created.")
            else:
                self.create_schema_tables_logger.info(f"create_user_log|TABLE {table_name} already exists.")
        sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name}
        (
        id int(10) NOT NULL AUTO_INCREMENT PRIMARY KEY,
        datetime timestamp,
        user_id bigint,
        webuser_id text,
        email text,
        origin text,
        func_name text,
        input text,
        remark text,
        FOREIGN KEY(user_id) REFERENCES user_info(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
        )
        """
        self.curr.execute(sql)
    
    def create_user_api_key(self, table_name='user_api_key'):
        res = self.curr.execute(f"""SHOW TABLES LIKE '{table_name}'""")
        if self.create_schema_tables_logger is not None:
            if res == 0:
                self.create_schema_tables_logger.info(f"create_user_api_key|TABLE {table_name} has been created.")
            else:
                self.create_schema_tables_logger.info(f"create_user_api_key|TABLE {table_name} already exists.")
        sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name}
        (
        id int(10) NOT NULL AUTO_INCREMENT PRIMARY KEY,
        datetime timestamp,
        user_id bigint,
        webuser_id text,
        email text,
        exchange text,
        access_key blob,
        secret_key blob,
        passphrase blob,
        remark text,
        FOREIGN KEY(user_id) REFERENCES user_info(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
        )
        """
        self.curr.execute(sql)

    def create_messages(self, table_name='messages'):
        res = self.curr.execute(f"""SHOW TABLES LIKE '{table_name}'""")
        if self.create_schema_tables_logger is not None:
            if res == 0:
                self.create_schema_tables_logger.info(f"create_messages|TABLE {table_name} has been created.")
            else:
                self.create_schema_tables_logger.info(f"create_messages|TABLE {table_name} already exists.")
        sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name}
        (
        id int(10) NOT NULL AUTO_INCREMENT PRIMARY KEY,
        datetime timestamp,
        user_id bigint,
        webuser_id text,
        origin text,
        func_name text,
        category text,
        type text,
        code int,
        title text,
        content text,
        read_flag tinyint,
        delete_flag tinyint,
        remark text,
        FOREIGN KEY(user_id) REFERENCES user_info(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
        )
        """
        self.curr.execute(sql)

    # MASTER
    def create_server_check(self, table_name='server_check'):
        res = self.curr.execute(f"""SHOW TABLES LIKE '{table_name}'""")
        if self.create_schema_tables_logger is not None:
            if res == 0:
                self.create_schema_tables_logger.info(f"create_server_check|TABLE {table_name} has been created.")
            else:
                self.create_schema_tables_logger.info(f"create_server_check|TABLE {table_name} already exists.")
        sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name}
        (
        id int(10) NOT NULL AUTO_INCREMENT PRIMARY KEY,
        datetime timestamp,
        exchange text,
        server_check_start datetime,
        server_check_end datetime,
        server_check_flag tinyint,
        remark text
        )
        """
        self.curr.execute(sql)

    # MASTER
    def create_payment_history(self, table_name='payment_history'):
        res = self.curr.execute(f"""SHOW TABLES LIKE '{table_name}'""")
        if self.create_schema_tables_logger is not None:
            if res == 0:
                self.create_schema_tables_logger.info(f"create_payment_history|TABLE {table_name} has been created.")
            else:
                self.create_schema_tables_logger.info(f"create_payment_history|TABLE {table_name} already exists.")
        sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name}
        (
        id int(10) NOT NULL AUTO_INCREMENT PRIMARY KEY,
        user_id bigint,
        datetime timestamp,
        symbol text,
        txid text,
        volume float,
        internal tinyint,
        destination_address text,
        remark text
        )
        """
        self.curr.execute(sql)

    # MASTER
    def create_price_info(self, table_name="price_info"):
        res = self.curr.execute(f"""SHOW TABLES LIKE '{table_name}'""")
        if self.create_schema_tables_logger is not None:
            if res == 0:
                self.create_schema_tables_logger.info(f"create_price_info|TABLE {table_name} has been created.")
            else:
                self.create_schema_tables_logger.info(f"create_price_info|TABLE {table_name} already exists.")
        sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name}
        (
        id int(10) NOT NULL AUTO_INCREMENT PRIMARY KEY,
        datetime timestamp,
        exchange text,
        symbol text,
        price float,
        remark text
        )
        """
        self.curr.execute(sql)

    # MASTER
    def create_dollar200(self, table_name='dollar200'):
        res = self.curr.execute(f"""SHOW TABLES LIKE '{table_name}'""")
        if self.create_schema_tables_logger is not None:
            if res == 0:
                self.create_schema_tables_logger.info(f"create_dollar200|TABLE {table_name} has been created.")
            else:
                self.create_schema_tables_logger.info(f"create_dollar200|TABLE {table_name} already exists.")
        sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name}
        (
        id int(10) NOT NULL AUTO_INCREMENT PRIMARY KEY,
        last_updated_time timestamp
        )
        """
        self.curr.execute(sql)

    # MASTER
    def create_funding_info(self, table_name='funding_info'):
        res = self.curr.execute(f"""SHOW TABLES LIKE '{table_name}'""")
        if self.create_schema_tables_logger is not None:
            if res == 0:
                self.create_schema_tables_logger.info(f"create_funding_info|TABLE {table_name} has been created.")
            else:
                self.create_schema_tables_logger.info(f"create_funding_info|TABLE {table_name} already exists.")
        sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name}
        (
        id int(10) NOT NULL AUTO_INCREMENT PRIMARY KEY,
        symbol TEXT,
        okx_symbol TEXT,
        fundingrate FLOAT,
        fundingtime DATETIME,
        nextfundingrate FLOAT,
        nextfundingtime DATETIME,
        last_updated_time DATETIME,
        exchange TEXT,
        rec TEXT
        )
        """
        self.curr.execute(sql)

    # MASTER
    def create_executives(self, table_name='executives'):
        res = self.curr.execute(f"""SHOW TABLES LIKE '{table_name}'""")
        if self.create_schema_tables_logger is not None:
            if res == 0:
                self.create_schema_tables_logger.info(f"create_executive_list|TABLE {table_name} has been created.")
            else:
                self.create_schema_tables_logger.info(f"create_executive_list|TABLE {table_name} already exists.")
        sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name}
        (
        id int(10) NOT NULL AUTO_INCREMENT PRIMARY KEY,
        datetime TIMESTAMP,
        user_uuid TEXT,
        email TEXT,
        user_id BIGINT,
        permission_group TEXT,
        user_name TEXT,
        remark TEXT
        )
        """
        self.curr.execute(sql)

    # MASTER
    def create_refer_coupon(self, table_name='refer_coupon'):
        res = self.curr.execute(f"""SHOW TABLES LIKE '{table_name}'""")
        if self.create_schema_tables_logger is not None:
            if res == 0:
                self.create_schema_tables_logger.info(f"create_refer_coupon|TABLE {table_name} has been created.")
            else:
                self.create_schema_tables_logger.info(f"create_refer_coupon|TABLE {table_name} already exists.")
        sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name}
        (
        id int(10) NOT NULL AUTO_INCREMENT PRIMARY KEY,
        datetime TIMESTAMP,
        user_uuid TEXT,
        email TEXT,
        user_id BIGINT,
        user_name TEXT,
        coupon_uuid TEXT,
        coupon_memo TEXT,
        service_period FLOAT,
        used_flag TINYINT,
        used_node TEXT,
        used_by_user_id BIGINT,
        used_by_user_uuid TEXT,
        used_by_user_email TEXT,
        delete_flag TINYINT,
        remark TEXT
        )
        """
        self.curr.execute(sql)