import sys
import os
import pandas as pd
from threading import Thread
from multiprocessing import Process, Manager
import datetime
import uuid
import json
import _pickle as pickle
import time
import traceback
import asyncio # For MarginCallback

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from data_process.processor import InitDataProcessor
from etc.db_handler.create_schema_tables import InitDBClient, InitDBPool
from etc.register_msg import register
from loggers.logger import KimpBotLogger

def krw(krw_num):
    return format(krw_num, ',')

def redis_uuid_to_display_id(df, redis_uuid):
    if len(df) == 0:
        return '없음'
    if redis_uuid is None:
        return '없음'
    corr_df = df[df['redis_uuid']==redis_uuid]['user_id']
    if len(corr_df) == 0:
        return redis_uuid
    user_id = corr_df.values[0]
    user_setting_df = df[df['user_id']==user_id].reset_index(drop=True)
    converted_display_id = int(user_setting_df[user_setting_df['redis_uuid']==redis_uuid].index[0]) + 1
    return converted_display_id

def display_id_to_redis_uuid(user_id, df, display_id):
    if len(df) == 0:
        return
    user_setting_df = df[df['user_id']==user_id].reset_index(drop=True)
    try:
        redis_uuid = user_setting_df.iloc[display_id-1, :]['redis_uuid']
    except IndexError:
        redis_uuid = None
    return redis_uuid

class InitSnatcher:
    # def __init__(self, logging_dir, node, encryption_key, local_db_dict, remote_db_dict, get_kimp_df_func, get_wa_kimp_dict_func, get_dollar_dict, \
    #     monitor_bot_token=None, monitor_bot_url=None, telegram_bot=None, kline_schema_name='coin_kimp_kline', admin_id=1390695186, \
    #         read_only_binance_access_key="kP5QOKAkN8XQ43f8GOu2HAnaV8vFMhrcT7wd0Zohgy8EwIfl6qYBB9HybOoes2i9", read_only_binance_secret_key="rydpSfGlA7Ba5c2JNaPK26SQy5nuBi4nLsu9Ot75u7qfygrlgmzWNeuGujEWbqwV"):
    def __init__(self, logging_dir, node, encryption_key, local_db_dict, remote_db_dict, kimp_core, \
        monitor_bot_token=None, monitor_bot_url=None, telegram_bot=None, kline_schema_name='coin_kimp_kline', admin_id=1390695186, \
            read_only_okx_access_key="", read_only_okx_secret_key=""):
        
        self.node = node
        self.logging_dir = logging_dir
        self.snatcher_logger = KimpBotLogger("snatcher", logging_dir).logger
        self.get_dollar_dict = kimp_core.get_dollar_dict
        self.monitor_bot_token = monitor_bot_token
        self.monitor_bot_url = monitor_bot_url
        self.get_kimp_df_func = kimp_core.get_kimp_df_func
        self.get_wa_kimp_dict_func = kimp_core.get_wa_kimp_dict_func
        self.upbit_server_check = False
        self.okx_server_check = False
        self.encryption_key = encryption_key
        self.local_db_dict = local_db_dict
        self.remote_db_dict = remote_db_dict
        self.telegram_bot = telegram_bot
        self.kline_schema_name = kline_schema_name
        self.admin_id = admin_id
        self.local_db_pool = InitDBPool(**local_db_dict, pool_name='snatcher_pool').connection_pool
        self.local_db_client_userinfo = InitDBClient(**local_db_dict)
        self.local_db_client_user_api_key = InitDBClient(**local_db_dict)
        # self.local_db_client_addcoin = InitDBClient(**local_db_dict)
        # self.local_db_client_addcir = InitDBClient(**local_db_dict)
        self.local_db_client_trade_history = InitDBClient(**local_db_dict)
        self.remote_db_client_funding = InitDBClient(**remote_db_dict)
        # self.redis_client_1 = InitRedis(db=1)
        # self.redis_client_2 = InitRedis(db=2)
        # self.redis_client_3 = InitRedis(db=3)
        # self.redis_client_4 = InitRedis(db=4)

        # Server Check Error Init
        # self.high_low_loop_stop_flag = False
        self.upbit_server_error_switch = False
        self.okx_server_error_switch = False
        
        # Initiate data processor
        self.data_processor = InitDataProcessor(logging_dir, remote_db_dict, kline_schema_name=self.kline_schema_name)

        # Initiate Upbit, Okx Adaptors
        # self.upbit_adaptor = InitUpbitAdaptor(None, None, logging_dir=logging_dir)
        self.upbit_adaptor = kimp_core.upbit_adaptor
        # self.binance_adaptor = InitBinanceAdaptor(read_only_binance_access_key, read_only_binance_secret_key, logging_dir=logging_dir)
        self.okx_adaptor = kimp_core.okx_adaptor

        if self.snatcher_logger is not None:
            self.snatcher_logger.info(f"Local Mariadb client has been connected to {local_db_dict['host']} - {local_db_dict['database']}.")
        self.remote_db_client = InitDBClient(**remote_db_dict)
        if self.snatcher_logger is not None:
            self.snatcher_logger.info(f"Remote Mariadb client has been connected to {remote_db_dict['host']} - {remote_db_dict['database']}.")
                                             
        # Initiate userinfo Dataframe
        self.local_db_client_userinfo.curr.execute("""DESCRIBE user_info""")
        userinfo_description = self.local_db_client_userinfo.curr.fetchall()
        col_names = [x['Field'] for x in userinfo_description if x['Field'] != 'id']
        self.userinfo_df = pd.DataFrame(columns=col_names)
        # Initiate user_api_key DataFrame
        self.local_db_client_userinfo.curr.execute("""DESCRIBE user_api_key""")
        user_api_key_description = self.local_db_client_userinfo.curr.fetchall()
        col_names = [x['Field'] for x in user_api_key_description if x['Field'] != 'id']
        self.user_api_key_df = pd.DataFrame(columns=col_names)
        # Initiate addcoin DataFrame
        addcoin_conn = self.local_db_pool.get_connection()
        addcoin_curr = addcoin_conn.cursor(dictionary=True)
        addcoin_curr.execute("""DESCRIBE addcoin""")
        addcoin_description = addcoin_curr.fetchall()
        self.addcoin_col_names = [x['Field'] for x in addcoin_description if x['Field'] != 'id']
        self.addcoin_df = pd.DataFrame(columns=self.addcoin_col_names)
        addcoin_conn.close()
        # Initiate addcir DataFrame
        addcir_conn = self.local_db_pool.get_connection()
        addcir_curr = addcir_conn.cursor(dictionary=True)
        addcir_curr.execute("""DESCRIBE addcir""")
        addcir_description = addcir_curr.fetchall()
        self.addcir_col_names = [x['Field'] for x in addcir_description if x['Field'] != 'id']
        self.addcir_df = pd.DataFrame(columns=self.addcir_col_names)
        # Initiate trade_history DataFrame
        self.local_db_client_trade_history.curr.execute("""DESCRIBE trade_history""")
        trade_history_description = self.local_db_client_trade_history.curr.fetchall()
        col_names = [x['Field'] for x in trade_history_description if x['Field'] != 'id']
        self.trade_history_df = pd.DataFrame(columns=col_names)
        # Initiate okx_futures_exchange_info DataFrame
        # self.okx_futures_exchange_info_df = self.okx_adaptor.get_instrument_info()
        # Initiate funding DataFrame
        self.remote_db_client_funding.curr.execute("""DESCRIBE funding_info""")
        funding_description = self.remote_db_client_funding.curr.fetchall()
        col_names = [x['Field'] for x in funding_description if x['Field'] != 'id']
        self.funding_df = pd.DataFrame(columns=col_names)

        # Start loading to memory threads
        self.start_monitor_load_userinfo()
        self.start_monitor_load_user_api_key()
        self.start_monitor_load_trade_history()
        # self.start_monitor_load_addcoin() # Not going to use Memory anymore. it will be handled in high low loop
        # self.start_monitor_load_addcir() # Not going to use Memory anymore. it will be handled in high low loop
        # self.start_monitor_load_okx_futures_exchange_info()
        self.start_monitor_load_funding_info()
        self.start_monitor_apply_addcir_limit()
        # self.start_monitor_margin_call() # Binance USD-M Futures MarginCallback

############# Trading Message function ####################################################################################
    def register_trading_msg(self, user_id, func_name, category, type, title, content, webuser_id=None, code=None, read_flag=0, delete_flag=0, remark=None):
        try:
            conn = self.local_db_pool.get_connection()
            curr = conn.cursor(dictionary=True)
            sql = """INSERT INTO messages(user_id, webuser_id, origin, func_name, category, type, code, title, content, read_flag, delete_flag, remark)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            val = [user_id, webuser_id, self.node, func_name, category, type, code, title.replace('<b>','').replace('</b>',''), content.replace('<b>','').replace('</b>',''), read_flag, delete_flag, remark]
            curr.execute(sql, val)
            conn.close()
        except:
            self.snatcher_logger.error(f"register_trading_msg|register_trading_msg got error!: {traceback.format_exc()}")

############# load and monitor thread functions ###########################################################################
    def load_userinfo(self, userinfo_table_name='user_info'):
        self.local_db_client_userinfo.conn.ping()
        res = self.local_db_client_userinfo.curr.execute(f"""SELECT * FROM {userinfo_table_name}""")
        if res == 0:
            self.userinfo_df = pd.DataFrame(columns=self.userinfo_df.columns)
            self.local_db_client_userinfo.conn.close()
            return
        temp_user_info_df = pd.DataFrame(self.local_db_client_userinfo.curr.fetchall())
        temp_user_info_df = temp_user_info_df.where(temp_user_info_df.notnull(), None)
        self.userinfo_df = temp_user_info_df
        self.local_db_client_userinfo.conn.close()

    # def load_userinfo_to_redis(self, db_dict, userinfo_table_name='user_info'):
    #     db_client = InitDBClient(**db_dict)
    #     # Fetch column names
    #     db_client.curr.execute(f"""DESCRIBE {userinfo_table_name}""")
    #     fetched_list = db_client.curr.fetchall()
    #     column_names = [x['Field'] for x in fetched_list if x['Field'] not in ['user_id', 'datetime', 'datetime_end']]

    #     sql = "SELECT user_id, DATE_FORMAT(datetime, '%Y-%m-%d %T') as datetime, DATE_FORMAT(datetime_end, '%Y-%m-%d %T') as datetime_end"
    #     for each_col in column_names:
    #         sql += ", " + each_col

    #     sql += f" FROM {userinfo_table_name}"
        
    #     db_client.curr.execute(sql)
    #     userinfo_dict_list = db_client.curr.fetchall()
    #     db_client.conn.close()

    #     if len(userinfo_dict_list) == 0:
    #         self.redis_client_1.redis_conn.flushdb()
    #         return

    #     db_whole_key_list = []
    #     for each_userinfo in userinfo_dict_list:
    #         user_id = each_userinfo['user_id']
    #         db_whole_key_list.append(user_id)
    #         self.redis_client_1.set_data(user_id, json.dumps(each_userinfo))

    #     redis_whole_key_list = [int(x) for x in self.redis_client_1.redis_conn.scan(0)[1]]

    #     for not_existing_key in [x for x in redis_whole_key_list if x not in db_whole_key_list]:
    #         self.redis_client_1.redis_conn.delete(not_existing_key)

    def start_monitor_load_userinfo(self, load_loop_secs=1, monitor_loop_secs=2.5):
        self.snatcher_logger.info(f"start_monitor_load_userinfo|start_monitor_load_userinfo started.")
        def monitor_loop_load_userinfo():
            input_type = 'monitor'
            title = 'loop_load_userinfo stopped! restarting loop_load_userinfo thread..'
            def loop_load_userinfo():
                while True:
                    try:
                        self.load_userinfo()
                        # self.load_userinfo_to_redis(self.local_db_dict)
                        time.sleep(load_loop_secs)
                    except Exception as e:
                        self.snatcher_logger.error(f"loop_load_userinfo|load_userinfo got error!: {e}")
                        self.snatcher_logger.error(f"{traceback.format_exc()}")
                        time.sleep(10)
            self.loop_load_userinfo_thread = Thread(target=loop_load_userinfo, daemon=True)
            self.loop_load_userinfo_thread.start()

            while True:
                if not self.loop_load_userinfo_thread.is_alive():
                    self.snatcher_logger.error(f"monitior_loop_load_userinfo|loop_load_userinfo stopped! restarting loop_load_userinfo thread..")
                    register(self.monitor_bot_token, self.monitor_bot_url, self.admin_id, self.node, input_type, title, "restarting loop_load_userinfo thread..")
                    self.loop_load_userinfo_thread = Thread(target=loop_load_userinfo, daemon=True)
                    self.loop_load_userinfo_thread.start()
                time.sleep(monitor_loop_secs)
        self.monitor_loop_load_userinfo_thread = Thread(target=monitor_loop_load_userinfo, daemon=True)
        self.monitor_loop_load_userinfo_thread.start()

    def load_user_api_key(self, user_api_key_table_name='user_api_key'):
        self.local_db_client_user_api_key.conn.ping()
        sql = """
        SELECT id, datetime, user_id, webuser_id, email, exchange,
        CONVERT(AES_DECRYPT(UNHEX(access_key), SHA2('{encryption_key}', 256)) USING UTF8) as access_key,
        CONVERT(AES_DECRYPT(UNHEX(secret_key), SHA2('{encryption_key}', 256)) USING UTF8) as secret_key,
        CONVERT(AES_DECRYPT(UNHEX(passphrase), SHA2('{encryption_key}', 256)) USING UTF8) as passphrase,
        remark
        FROM {user_api_key_table_name}
        """.format(encryption_key=self.encryption_key, user_api_key_table_name=user_api_key_table_name)
        res = self.local_db_client_user_api_key.curr.execute(sql)
        if res == 0:
            self.user_api_key_df = pd.DataFrame(columns=self.user_api_key_df.columns)
            self.local_db_client_user_api_key.conn.close()
            return
        temp_user_api_key_df = pd.DataFrame(self.local_db_client_user_api_key.curr.fetchall())
        temp_user_api_key_df = temp_user_api_key_df.where(temp_user_api_key_df.notnull(), None)
        self.user_api_key_df = temp_user_api_key_df
        self.local_db_client_user_api_key.conn.close()

    def start_monitor_load_user_api_key(self, load_loop_secs=1, monitor_loop_secs=2.5):
        self.snatcher_logger.info(f"start_monitor_load_user_api_key|start_monitor_load_user_api_key started.")
        def monitor_loop_load_user_api_key():
            input_type = 'monitor'
            title = 'load_user_api_key stopped! restarting load_user_api_key thread..'
            def load_user_api_key():
                while True:
                    try:
                        self.load_user_api_key()
                        # self.load_user_api_key_to_redis(self.local_db_dict)
                        time.sleep(load_loop_secs)
                    except Exception as e:
                        self.snatcher_logger.error(f"load_user_api_key|load_user_api_key got error!: {e}")
                        self.snatcher_logger.error(f"{traceback.format_exc()}")
                        time.sleep(10)
            self.load_user_api_key_thread = Thread(target=load_user_api_key, daemon=True)
            self.load_user_api_key_thread.start()
            
            while True:
                if not self.load_user_api_key_thread.is_alive():
                    self.snatcher_logger.error(f"monitor_loop_load_user_api_key|loop_load_user_api_key stopped! restarting loop_load_user_api_key thread..")
                    register(self.monitor_bot_token, self.monitor_bot_url, self.admin_id, self.node, input_type, title, "restarting load_user_api_key thread..")
                    self.load_user_api_key_thread = Thread(target=load_user_api_key, daemon=True)
                    self.load_user_api_key_thread.start()
                time.sleep(monitor_loop_secs)
        self.monitor_load_user_api_key_thread = Thread(target=monitor_loop_load_user_api_key, daemon=True)
        self.monitor_load_user_api_key_thread.start()

    def load_trade_history(self, trade_history_table_name='trade_history'):
        self.local_db_client_trade_history.conn.ping()
        res = self.local_db_client_trade_history.curr.execute(f"""SELECT * FROM {trade_history_table_name}""")
        if res == 0:
            self.trade_history_df = pd.DataFrame(columns=self.trade_history_df.columns)
            self.local_db_client_trade_history.conn.close()
            return
        temp_trade_history_df = pd.DataFrame(self.local_db_client_trade_history.curr.fetchall())
        temp_trade_history_df = temp_trade_history_df.where(temp_trade_history_df.notnull(), None)
        self.trade_history_df = temp_trade_history_df
        self.local_db_client_trade_history.conn.close()

    def start_monitor_load_trade_history(self, load_loop_secs=2, monitor_loop_secs=2.5):
        self.snatcher_logger.info(f"start_monitor_load_trade_history|start_monitor_load_trade_history started.")
        def monitor_loop_load_trade_history():
            input_type = 'monitor'
            title = 'loop_load_trade_history stopped! restarting loop_load_trade_history thread..'
            def loop_load_trade_history():
                while True:
                    try:
                        self.load_trade_history()
                        time.sleep(load_loop_secs)
                    except Exception as e:
                        self.snatcher_logger.error(f"loop_load_trade_history|load_trade_history got error!: {e}")
                        self.snatcher_logger.error(f"{traceback.format_exc()}")
                        time.sleep(10)
            self.loop_load_trade_history_thread = Thread(target=loop_load_trade_history, daemon=True)
            self.loop_load_trade_history_thread.start()

            while True:
                if not self.loop_load_trade_history_thread.is_alive():
                    self.snatcher_logger.error(f"monitior_loop_load_trade_history|loop_load_trade_history stopped! restarting loop_load_trade_history thread..")
                    register(self.monitor_bot_token, self.monitor_bot_url, self.admin_id, self.node, input_type, title, "restarting loop_load_trade_history thread..")
                    self.loop_load_trade_history_thread = Thread(target=loop_load_trade_history, daemon=True)
                    self.loop_load_trade_history_thread.start()
                time.sleep(monitor_loop_secs)
        self.monitor_loop_load_trade_history_thread = Thread(target=monitor_loop_load_trade_history, daemon=True)
        self.monitor_loop_load_trade_history_thread.start()

    # def load_okx_futures_exchange_info(self):
    #     self.okx_futures_exchange_info_df = self.okx_adaptor.get_instrument_info()
    
    # def start_monitor_load_okx_futures_exchange_info(self, load_loop_secs=3600*6, monitor_loop_secs=30):
    #     self.snatcher_logger.info(f"start_monitor_load_okx_futures_exchange_info|start_monitor_load_okx_futures_exchange_info started.")
    #     def monitor_load_okx_futures_exchange_info():
    #         input_type = 'monitor'
    #         title = 'loop_load_okx_futures_exchange stopped! restartin loop_load_okx_futures_exchange thread..'
    #         def loop_load_okx_futures_exchange_info():
    #             while True:
    #                 try:
    #                     self.load_okx_futures_exchange_info()
    #                     time.sleep(load_loop_secs)
    #                 except Exception as e:
    #                     self.snatcher_logger.error(f"loop_load_okx_futures_exchange_info|loop_load_okx_futures_exchange_info got error!: {e}")
    #                     self.snatcher_logger.error(f"{traceback.format_exc()}")
    #                     time.sleep(60)
    #         self.loop_load_okx_futures_exchange_info_thread = Thread(target=loop_load_okx_futures_exchange_info, daemon=True)
    #         self.loop_load_okx_futures_exchange_info_thread.start()

    #         while True:
    #             if not self.loop_load_okx_futures_exchange_info_thread.is_alive():
    #                 self.snatcher_logger.error(f"monitor_load_okx_futures_exchange_info|loop_load_okx_futures_exchange_info stopped! restarting loop_load_okx_futures_exchange_info thread..")
    #                 register(self.monitor_bot_token, self.monitor_bot_url, self.admin_id, self.node, input_type, title, "restarting loop_load_okx_futures_exchange_info thread..")
    #                 self.loop_load_okx_futures_exchange_info_thread = Thread(target=loop_load_okx_futures_exchange_info, daemon=True)
    #                 self.loop_load_okx_futures_exchange_info_thread.start()
    #             time.sleep(monitor_loop_secs)
    #     self.monitor_load_okx_futures_exchange_info_thread = Thread(target=monitor_load_okx_futures_exchange_info, daemon=True)
    #     self.monitor_load_okx_futures_exchange_info_thread.start()

    def load_funding_info(self, funding_info_table_name='funding_info'):
        self.remote_db_client_funding.conn.ping()
        res = self.remote_db_client_funding.curr.execute(f"SELECT * FROM {funding_info_table_name}")
        if res == 0:
            self.funding_df = pd.DataFrame(columns=self.funding_df.columns)
            self.remote_db_client_funding.conn.close()
            return
        fetched_df = pd.DataFrame(self.remote_db_client_funding.curr.fetchall())
        self.funding_df = fetched_df.drop('index', axis=1)
        self.remote_db_client_funding.conn.close()

    def start_monitor_load_funding_info(self, load_loop_secs=5, monitor_loop_secs=2.5):
        self.snatcher_logger.info(f"start_monitor_load_funding_info|start_monitor_load_funding_info started.")
        def monitor_loop_load_funding_info():
            input_type = 'monitor'
            title = 'loop_load_funding_info stopped! restarting loop_load_funding_info thread..'
            def loop_load_funding_info():
                while True:
                    try:
                        self.load_funding_info()
                        time.sleep(load_loop_secs)
                    except Exception as e:
                        self.snatcher_logger.error(f"loop_load_funding_info|load_funding_info got error!: {e}")
                        self.snatcher_logger.error(f"{traceback.format_exc()}")
                        time.sleep(2.5)
            self.loop_load_funding_info_thread = Thread(target=loop_load_funding_info, daemon=True)
            self.loop_load_funding_info_thread.start()

            while True:
                if not self.loop_load_funding_info_thread.is_alive():
                    self.snatcher_logger.error(f"monitior_loop_load_funding_info|loop_load_funding_info stopped! restarting loop_load_funding_info thread..")
                    register(self.monitor_bot_token, self.monitor_bot_url, self.admin_id, self.node, input_type, title, "restarting loop_load_funding_info thread..")
                    self.loop_load_funding_info_thread = Thread(target=loop_load_funding_info, daemon=True)
                    self.loop_load_funding_info_thread.start()
                time.sleep(monitor_loop_secs)
        self.monitor_loop_load_funding_info_thread = Thread(target=monitor_loop_load_funding_info, daemon=True)
        self.monitor_loop_load_funding_info_thread.start()

    def apply_addcir_limit(self, apply_loop_secs):
        time.sleep(5)
        try:
            while True:
                time.sleep(apply_loop_secs)
                if len(self.userinfo_df) == 0:
                    continue
                valid_user_info_df = self.userinfo_df[self.userinfo_df['datetime_end']>=datetime.datetime.now()].reset_index(drop=True)
                if len(self.addcir_df) == 0 or len(valid_user_info_df) == 0:
                    continue
                merged_df = self.get_kimp_df_func()
                merged_df = merged_df.sort_values('acc_trade_price_24h', ascending=False).reset_index(drop=True)
                wa_kimp_dict = self.get_wa_kimp_dict_func()
                weighted_avg_kimp = wa_kimp_dict['wa_kimp']
                # weighted_avg_kimp = (merged_df['acc_trade_price_24h']/merged_df['acc_trade_price_24h'].sum() * merged_df['tp_kimp']).sum()
                # merged_addcir_df = self.addcir_df.merge(valid_user_info_df[['user_id','addcir_limit']], on='user_id').dropna(subset=['addcir_limit']) # Deprecated
                merged_addcir_df = self.addcir_df.merge(valid_user_info_df[['user_id','addcir_limit']], on='user_id')
                merged_addcir_df.loc[:, 'addcir_limit'] = merged_addcir_df['addcir_limit'].fillna(9999)

                # filtering for deactivate
                to_deactivate_df = merged_addcir_df[(merged_addcir_df['addcir_limit']<=(weighted_avg_kimp*100))&(merged_addcir_df['cir_trade_switch']==1)]
                if len(to_deactivate_df['redis_uuid'].to_list()) != 0:
                    remark = '/addcirl 설정으로 인한 비활성화'
                    # apply it to the DataFrame(Local Memory) first
                    for each_addcir_redis_uuid in to_deactivate_df['redis_uuid']:
                        corr_index = self.addcir_df[self.addcir_df['redis_uuid']==each_addcir_redis_uuid].index[0]
                        self.addcir_df.loc[corr_index, 'cir_trade_switch'] = 0
                        self.addcir_df.loc[corr_index, 'remark'] = remark
                    redis_uuid_list_str = ','.join(["\'" + x + "\'" for x in to_deactivate_df['redis_uuid'].to_list()])
                    timestamp_now = datetime.datetime.now().timestamp()*10000000
                    db_client = InitDBClient(**self.local_db_dict)
                    db_client.curr.execute("""UPDATE addcir SET last_updated_timestamp=%s, cir_trade_switch=%s, remark=%s WHERE redis_uuid in ({redis_uuid_list_str})""".format(redis_uuid_list_str=redis_uuid_list_str), (timestamp_now, 0, remark))
                    db_client.conn.commit()
                    db_client.conn.close()
                # filtering for re-activate
                to_reactivate_df = merged_addcir_df[(merged_addcir_df['addcir_limit']>(weighted_avg_kimp*100))&(merged_addcir_df['cir_trade_switch']==0)&(merged_addcir_df['remark'].str.contains('/addcirl'))]
                if len(to_reactivate_df['redis_uuid'].to_list()) != 0:
                    remark = None
                    # apply it to the DataFrame(Local Memory) first
                    for each_addcir_redis_uuid in to_reactivate_df['redis_uuid']:
                        corr_index = self.addcir_df[self.addcir_df['redis_uuid']==each_addcir_redis_uuid].index[0]
                        self.addcir_df.loc[corr_index, 'cir_trade_switch'] = 0
                        self.addcir_df.loc[corr_index, 'remark'] = remark
                    redis_uuid_list_str = ','.join(["\'" + x + "\'" for x in to_reactivate_df['redis_uuid'].to_list()])
                    timestamp_now = datetime.datetime.now().timestamp()*10000000
                    db_client = InitDBClient(**self.local_db_dict)
                    db_client.curr.execute("""UPDATE addcir SET last_updated_timestamp=%s, cir_trade_switch=%s, remark=%s WHERE redis_uuid in ({redis_uuid_list_str})""".format(redis_uuid_list_str=redis_uuid_list_str), (timestamp_now, 1, remark))
                    db_client.conn.commit()
                    db_client.conn.close()
        except Exception:
            self.snatcher_logger.error(f"apply_addcir_limit|{traceback.format_exc()}")

    def start_monitor_apply_addcir_limit(self, monitor_loop_secs=2.5, apply_loop_secs=1):
        self.snatcher_logger.info(f"apply_addcir_limit|apply_addcir_limit started.")
        def monitor_apply_addcir_limit():
            input_type = 'monitor'
            title = 'apply_addcir_limit stopped! restarting apply_addcir_limit thread..'
            self.apply_addcir_limit_thread = Thread(target=self.apply_addcir_limit, args=(apply_loop_secs,), daemon=True)
            self.apply_addcir_limit_thread.start()

            while True:
                if not self.apply_addcir_limit_thread.is_alive():
                    self.snatcher_logger.error(f"monitor_apply_addcir_limit|apply_addcir_limit stopped! restarting apply_addcir_limit thread..")
                    register(self.monitor_bot_token, self.monitor_bot_url, self.admin_id, self.node, input_type, title, "restarting apply_addcir_limit thread..")
                    self.apply_addcir_limit_thread = Thread(target=self.apply_addcir_limit, args=(apply_loop_secs,), daemon=True)
                    self.apply_addcir_limit_thread.start()
                time.sleep(monitor_loop_secs)
        self.monitor_apply_addcir_limit_thread = Thread(target=monitor_apply_addcir_limit, daemon=True)
        self.monitor_apply_addcir_limit_thread.start()

############# MarginCall monitoring functions #####################################################################

    # # Functions for monitoring binance margin call
    # def margin_call_callback(self, res, user_id, user_binance_margin_call):
    #     try:
    #         # user_binance_margin_call == None -> Do nothing,
    #         # user_binance_margin_call == 1 -> Only warning message, 
    #         # user_binance_margin_call == 2 -> message & auto exit
    #         if user_binance_margin_call == None:
    #             return

    #         elif user_binance_margin_call == 1 or user_binance_margin_call == 2:
    #             margin_type = res['p'][0]['mt'] # CROSSED or ISOLATED
    #             symbol = res['p'][0]['s'].replace('USDT', '')
    #             position_side = res['p'][0]['ps']
    #             mark_price = float(res['p'][0]['mp'])
    #             position_amount = float(res['p'][0]['pa'])
    #             unrealized_pnl = float(res['p'][0]['up'])
    #             # Send margin call message
    #             try: # Math.round(-(1-each_pos.entryPrice/each_pos.markPrice)/(1/each_pos.leverage)*1000)/10}%
    #                 body = f"<b>마진콜 경고!</b> 바이낸스 {symbol}USDT 의 <b>미실현손익이 위험수위</b>에 도달했습니다.\n"
    #             except:
    #                 body = f"<b>마진콜 경고!</b> 바이낸스 {symbol}USDT 의 미실현손익이 <b>{round((unrealized_pnl/position_amount)*100, 1)}%</b> 에 도달했습니다.\n"
    #             body += f"바이낸스 포지션: {position_side}, 마진타입: {margin_type}\n"
    #             body += f"{symbol}USDT 현재 Mark가격: {mark_price}USDT"
    #             self.telegram_bot.send_thread(user_id, body, 5, 5, 'html')
    #             self.register_trading_msg(user_id, "margin_call_callback", "user_msg", 'warning', "마진콜 경고", body)

    #             # If user_binance_margin_call == 2, execute auto exit
    #             if user_binance_margin_call == 2:
    #                 body = f"마진콜 모니터링 설정에 따라, 자동거래(Addcoin)에 진입되어 있는 바이낸스와 업비트 포지션을 자동정리합니다."
    #                 self.telegram_bot.send_thread(user_id, body, 'html')
    #                 self.register_trading_msg(user_id, "margin_call_callback", "user_msg", 'normal', "마진콜 자동정리", body)
    #                 waiting_df = self.addcoin_df[(self.addcoin_df['user_id']==user_id)&(self.addcoin_df['symbol'].str.contains(symbol))&(self.addcoin_df['auto_trade_switch']==-1)]
    #                 if len(waiting_df) == 0:
    #                     body = f"{symbol}USDT는 /addcoin 으로 김프거래에 진입되어있는 상태가 아닙니다.\n"
    #                     body += f"포지션 자동정리를 취소합니다."
    #                     self.telegram_bot.send_thread(chat_id=user_id, text=body)
    #                     self.register_trading_msg(user_id, "margin_call_callback", "user_msg", 'normal', "마진콜 자동정리 취소", body)
    #                     return
    #             # There's waiting trade
    #             for row_tup in waiting_df.iterrows():
    #                 # load api keys
    #                 try:
    #                     user_upbit_access_key, user_upbit_secret_key = self.user_api_key_df[(self.user_api_key_df['user_id']==user_id)&(self.user_api_key_df['exchange']=='UPBIT')]\
    #                     .sample(n=1)[['access_key', 'secret_key']].values[0]
    #                     user_binance_access_key, user_binance_secret_key =  self.user_api_key_df[(self.user_api_key_df['user_id']==user_id)&(self.user_api_key_df['exchange']=='BINANCE')]\
    #                     .sample(n=1)[['access_key', 'secret_key']].values[0]
    #                 except:
    #                     self.snatcher_logger.error(f"margin_call_callback|{traceback.format_exc()}")
    #                     raise Exception("margin_call_callback|API Key load error")
    #                 row = row_tup[1]
    #                 redis_uuid = row['redis_uuid']
    #                 symbol = row['symbol'].replace('USDT', '')
    #                 # Order record validation
    #                 if row['enter_upbit_uuid'] == None or row['enter_binance_orderId'] == None:
    #                     body = f"거래ID:{redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}({symbol})에 대한 진입기록이 조회되지 않습니다.\n"
    #                     body += f"포지션 자동정리를 취소합니다."
    #                     self.telegram_bot.send_thread(chat_id=user_id, text=body)
    #                     self.register_trading_msg(user_id, "margin_call_callback", "user_msg", 'normal', "마진콜 자동정리 취소", body)
    #                     continue
    #                 # # UPDATE DataFrame memory
    #                 # user_alarm_df.loc[row['id'], 'auto_trade_switch'] = 1
    #                 corr_index = self.addcoin_df[self.addcoin_df['redis_uuid']==redis_uuid].index[0]
    #                 self.addcoin_df.loc[corr_index, 'auto_trade_switch'] = 1
    #                 # UPDATE database
    #                 db_client = InitDBClient(**self.local_db_dict)
    #                 db_client.curr.execute("""UPDATE addcoin SET last_updated_timestamp=%s, auto_trade_switch=%s WHERE redis_uuid=%s""", (datetime.datetime.now().timestamp()*10000000, 1, row['redis_uuid']))
    #                 db_client.conn.commit()

    #                 upbit_exit_qty = self.trade_history_df[self.trade_history_df['upbit_uuid']==row['enter_upbit_uuid']]['upbit_qty'].values[0]
    #                 binance_exit_qty = self.trade_history_df[self.trade_history_df['upbit_uuid']==row['enter_upbit_uuid']]['binance_qty'].values[0]
    #                 exit_id_list = []
    #                 self.exit_func(self.get_kimp_df_func(), self.get_dollar_dict()['price'], user_id, redis_uuid, symbol, (upbit_exit_qty,binance_exit_qty), \
    #                     user_upbit_access_key, user_upbit_secret_key, user_binance_access_key, user_binance_secret_key, exit_id_list)
    #                 try:
    #                     self.exec_pnl(self.get_kimp_df_func(), user_id, redis_uuid, exit_id_list[0], self.get_dollar_dict()['price'])
    #                 except Exception as e:
    #                     self.snatcher_logger.error(f"margin_call_callback 에서 exit_func 이후 exec_pnl 실패|{traceback.format_exc()}")
    #                     body = traceback.format_exc(e)
    #                     register(self.monitor_bot_token, self.monitor_bot_url, self.admin_id, self.node, 'error', "margin_call_callback 에서 exec_pnl 에러 발생", body)
    #                 try:
    #                     db_client.curr.execute("""UPDATE addcoin SET last_updated_timestamp=%s, exit_upbit_uuid=%s, exit_binance_orderId=%s WHERE redis_uuid=%s""", (datetime.datetime.now().timestamp()*10000000, exit_id_list[0], exit_id_list[1], row['redis_uuid']))
    #                     db_client.conn.commit()
    #                     db_client.conn.close()
    #                 except Exception as e:
    #                     db_client.conn.close()
    #                     self.snatcher_logger.error(f"margin_call_callback 에서 exit_func 이후 uuid, orderId UPDATE 실패|{traceback.format_exc()}")
    #                     title = "margin_call_callback 에서 exit_func 이후 uuid, orderId UPDATE 실패"
    #                     body = f"{title}\n"
    #                     body += f"user_id: {user_id}, redis_uuid: {row['redis_uuid']}, symbol: {symbol}\n"
    #                     body += f"Error: {e}"
    #                     self.telegram_bot.send_thread(chat_id=self.admin_id, text=body)
    #                     self.register_trading_msg(self.admin_id, "margin_call_callback", "admin_msg", 'error', title, body)
    #         else:
    #             return
    #     except Exception as e:
    #         self.snatcher_logger.error(f"margin_call_callback|{traceback.format_exc()}")
    #         title = "margin_call_callback 에서 에러 발생!"
    #         body = f"{title}\n"
    #         body += f"error: {e}"
    #         self.telegram_bot.send_thread(chat_id=self.admin_id, text=body)
    #         self.register_trading_msg(self.admin_id, "margin_call_callback", "admin_msg", 'error', title, body)
    #         return

    # def liquidation_callback(self, res, user_id, user_binance_margin_call):
    #     try:
    #         # user_binance_margin_call == None -> Do nothing,
    #         # user_binance_margin_call == 1 -> Only warning message, 
    #         # user_binance_margin_call == 2 -> message & auto exit
    #         if user_binance_margin_call == None:
    #             return

    #         elif user_binance_margin_call == 1 or user_binance_margin_call == 2:
    #             symbol = res['o']['s'] # EX: BTCUSDT
    #             symbol = symbol.replace('USDT', '')
    #             side = res['o']['S'] # BUY or SELL
    #             qty = res['o']['q']
    #             # Send Liquidation message
    #             body = f"<b>청산 알람!</b> 바이낸스 {symbol}USDT {qty}개가 강제청산되었습니다.\n"
    #             body += f"/pos 명령어 혹은 웹 자산현황을 통해 헷지상태를 확인 해 주십시오."
    #             self.telegram_bot.send_thread(user_id, body, 5, 5, 'html')
    #             self.register_trading_msg(user_id, "liquidation_callback", "user_msg", 'warning', "강제청산알람", body)
    #             # Temporary
    #             register(self.monitor_bot_token, self.monitor_bot_url, self.admin_id, self.node, 'monitor', 'liquidation alarm', f"liquidation warning message sent to user_id: {user_id}")

    #             if user_binance_margin_call == 2:
    #                 body = f"바이낸스 숏포지션이 청산되었으므로 마진콜 모니터링 설정에 따라, 자동거래(Addcoin)에 진입되어 있는 업비트 포지션을 자동정리합니다."
    #                 self.telegram_bot.send_thread(user_id, body, 'html')
    #                 self.register_trading_msg(user_id, "liquidation_callback", "user_msg", 'normal', "강제청산 자동정리", body)
    #                 waiting_df = self.addcoin_df[(self.addcoin_df['user_id']==user_id)&(self.addcoin_df['symbol'].str.contains(symbol))&(self.addcoin_df['auto_trade_switch']==-1)]
    #                 if len(waiting_df) == 0:
    #                     body = f"{symbol}는 /addcoin 으로 김프거래에 진입되어있는 상태가 아닙니다.\n"
    #                     body += f"포지션 자동정리를 취소합니다."
    #                     self.telegram_bot.send_thread(chat_id=user_id, text=body)
    #                     self.register_trading_msg(user_id, "liquidation_callback", "user_msg", 'normal', "청산 자동정리 취소", body)
    #                     return
    #             # There's waiting trade
    #             for row_tup in waiting_df.iterrows():
    #                 # load api keys
    #                 try:
    #                     user_upbit_access_key, user_upbit_secret_key = self.user_api_key_df[(self.user_api_key_df['user_id']==user_id)&(self.user_api_key_df['exchange']=='UPBIT')]\
    #                     .sample(n=1)[['access_key', 'secret_key']].values[0]
    #                     user_binance_access_key, user_binance_secret_key =  self.user_api_key_df[(self.user_api_key_df['user_id']==user_id)&(self.user_api_key_df['exchange']=='BINANCE')]\
    #                     .sample(n=1)[['access_key', 'secret_key']].values[0]
    #                 except:
    #                     self.snatcher_logger.error(f"liquidation_callback|{traceback.format_exc()}")
    #                     raise Exception("liquidation_callback|API Key load error")
    #                 row = row_tup[1]
    #                 redis_uuid = row['redis_uuid']
    #                 symbol = row['symbol'].replace('USDT', '')
    #                 # Order record validation
    #                 if row['enter_upbit_uuid'] == None or row['enter_binance_orderId'] == None:
    #                     body = f"거래ID:{redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}({symbol})에 대한 진입기록이 조회되지 않습니다.\n"
    #                     body += f"포지션 자동정리를 취소합니다."
    #                     self.telegram_bot.send_thread(chat_id=user_id, text=body)
    #                     self.register_trading_msg(user_id, "liquidation_callback", "user_msg", 'normal', "강제청산 자동정리 취소", body)
    #                     continue
    #                 # # UPDATE DataFrame memory
    #                 # user_alarm_df.loc[row['id'], 'auto_trade_switch'] = 1
    #                 corr_index = self.addcoin_df[self.addcoin_df['redis_uuid']==redis_uuid].index[0]
    #                 self.addcoin_df.loc[corr_index, 'auto_trade_switch'] = 1
    #                 # UPDATE database
    #                 db_client = InitDBClient(**self.local_db_dict)
    #                 db_client.curr.execute("""UPDATE addcoin SET last_updated_timestamp=%s, auto_trade_switch=%s WHERE redis_uuid=%s""", (datetime.datetime.now().timestamp()*10000000, 1, row['redis_uuid']))
    #                 db_client.conn.commit()

    #                 upbit_exit_qty = self.trade_history_df[self.trade_history_df['upbit_uuid']==row['enter_upbit_uuid']]['upbit_qty'].values[0]
    #                 binance_exit_qty = 0
    #                 exit_id_list = []
    #                 self.exit_func(self.get_kimp_df_func(), self.get_dollar_dict()['price'], user_id, redis_uuid, symbol, (upbit_exit_qty,binance_exit_qty), \
    #                     user_upbit_access_key, user_upbit_secret_key, user_binance_access_key, user_binance_secret_key, exit_id_list)
    #                 try:
    #                     db_client.curr.execute("""UPDATE addcoin SET last_updated_timestamp=%s, exit_upbit_uuid=%s, exit_binance_orderId=%s WHERE redis_uuid=%s""", (datetime.datetime.now().timestamp()*10000000, exit_id_list[0], exit_id_list[1], row['redis_uuid']))
    #                     db_client.conn.commit()
    #                     db_client.conn.close()
    #                 except Exception as e:
    #                     db_client.conn.close()
    #                     self.snatcher_logger.error(f"liquidation_callback 에서 exit_func 이후 uuid, orderId UPDATE 실패|{traceback.format_exc()}")
    #                     title = "liquidation_callback 에서 exit_func 이후 uuid, orderId UPDATE 실패"
    #                     body = f"{title}\n"
    #                     body += f"user_id: {user_id}, redis_uuid: {row['redis_uuid']}, symbol: {symbol}\n"
    #                     body += f"Error: {e}"
    #                     self.telegram_bot.send_thread(chat_id=self.admin_id, text=body)
    #                     self.register_trading_msg(self.admin_id, "liquidation_callback", "admin_msg", 'error', title, body)
    #                     register(self.monitor_bot_token, self.monitor_bot_url, self.admin_id, self.node, 'error', title, body)
    #         else:
    #             return



    #     except Exception as e:
    #         self.snatcher_logger.error(f"liquidation_callback|{traceback.format_exc()}")
    #         title = "liquidation_callback 에서 에러 발생!"
    #         body = f"{title}]n"
    #         body += f"error: {e}"
    #         self.telegram_bot.send_thread(chat_id=self.admin_id, text=body)
    #         self.register_trading_msg(self.admin_id, "liquidation_callback", "admin_msg", "error", title, body)
    #         register(self.monitor_bot_token, self.monitor_bot_url, self.admin_id, self.node, 'error', title, body)

    # async def user_binance_futures_socket(self, user_binance_access_key, user_binance_secret_key, user_id):
    #     client = await AsyncClient.create(user_binance_access_key, user_binance_secret_key)
    #     bm = BinanceSocketManager(client)
    #     # start any sockets here, i.e a trade socket
    #     ts = bm.futures_socket()
    #     # then start receiving messages
    #     async with ts as tscm:
    #         while True:
    #             # Load user_binance_margin_call
    #             user_binance_margin_call = self.userinfo_df[self.userinfo_df['user_id']==user_id]['binance_margin_call'].values[0]
    #             try:
    #                 user_on_off = self.userinfo_df[self.userinfo_df['user_id']==user_id]['on_off'].values[0]
    #                 if user_on_off != 1:
    #                     continue
    #             except:
    #                 title = "user_binance_futures_socket on_off 세팅 에러"
    #                 body = f"{title}\n"
    #                 body += f"error: {e}"
    #                 self.register_trading_msg(self.admin_id, "user_binance_futures_socket", "admin_msg", "error", title, body)
    #             res = await tscm.recv()
    #             self.snatcher_logger.info(f"user_binance_futures_socket user_id: {user_id}, res['e']: {res['e']}") # test
    #             self.snatcher_logger.info(f"res: {res}") # test
    #             if res['e'] == "MARGIN_CALL":
    #                 self.margin_call_callback(res, user_id, user_binance_margin_call)
    #             try:
    #                 if res['e'] == "ORDER_TRADE_UPDATE" and res['o']['o'] == 'LIQUIDATION':
    #                     self.liquidation_callback(res, user_id, user_binance_margin_call)
    #             except Exception as e:
    #                 title = "user_binance_futures_socket 에서 에러 발생!"
    #                 body = f"{title}]n"
    #                 body += f"error: {e}"
    #                 self.telegram_bot.send_thread(chat_id=self.admin_id, text=body)
    #                 self.register_trading_msg(self.admin_id, "user_binance_futures_socket", "admin_msg", "error", title, body)
    #             # # test
    #             # if res['e'] == "ACCOUNT_UPDATE" and user_id == self.admin_id:
    #             #     body = f"margin_call websocket TEST\n"
    #             #     body += f"res margin_type: {res['a']['P'][0]['mt']}\n"
    #             #     body += f"user_id: {user_id}"
    #             #     self.telegram_bot.send_thread(chat_id=self.admin_id, text=body)
    #             time.sleep(0.3)

    # def user_binance_futures_socket_th(self, user_id, user_binance_access_key, user_binance_secret_key):
    #     asyncio.run(self.user_binance_futures_socket(user_binance_access_key, user_binance_secret_key, user_id))

    # def start_monitor_margin_call(self, loop_secs=3, monitor_loop_secs=2.5):
    #     time.sleep(3)
    #     self.snatcher_logger.info(f"start_monitor_margin_call|start_monitor_margin_call started.")
    #     def monitor_margin_call_loop():
    #         input_type = 'monitor'
    #         title = 'monitor_margin_call stopped! restarting monitor_margin_call thread..'
    #         monitoring_list = []
    #         def monitor_margin_call():
    #             try:
    #                 while True:
    #                     time.sleep(loop_secs)
    #                     # Add monitoring thread if there isn't one
    #                     binance_api_key_user_id_list = self.user_api_key_df[self.user_api_key_df['exchange']=='BINANCE']['user_id'].to_list()
    #                     filtered_user_info_df = self.userinfo_df[(self.userinfo_df['user_id'].isin(binance_api_key_user_id_list))&(self.userinfo_df['datetime_end']>datetime.datetime.now())&(self.userinfo_df['on_off']==1)]

    #                     for row_tup in filtered_user_info_df.iterrows():
    #                         row = row_tup[1]
    #                         try:
    #                             user_binance_access_key, user_binance_secret_key =  self.user_api_key_df[(self.user_api_key_df['user_id']==row['user_id'])&(self.user_api_key_df['exchange']=='BINANCE')]\
    #                             .sample(n=1)[['access_key', 'secret_key']].values[0]
    #                         except:
    #                             self.snatcher_logger.error(f"start_monitor_margin_call|{traceback.format_exc()}")
    #                             raise Exception("start_monitor_margin_call|API Key load error")
    #                         if monitoring_list == []:
    #                             monitor_thread_tup = (row['user_id'], Thread(target=self.user_binance_futures_socket_th, args=(row['user_id'], user_binance_access_key, user_binance_secret_key), daemon=True))
    #                             monitor_thread_tup[1].start()
    #                             monitoring_list.append(monitor_thread_tup)
    #                             self.snatcher_logger.info(f"user_id: {row['user_id']}'s MarginCall monitor thread has been initiated.")
    #                         elif row['user_id'] not in [x[0] for x in monitoring_list]:
    #                             monitor_thread_tup = (row['user_id'], Thread(target=self.user_binance_futures_socket_th, args=(row['user_id'], user_binance_access_key, user_binance_secret_key), daemon=True))
    #                             monitor_thread_tup[1].start()
    #                             monitoring_list.append(monitor_thread_tup)
    #                             self.snatcher_logger.info(f"user_id: {row['user_id']}'s MarginCall monitor thread has been initiated.")
    #                         time.sleep(0.25)
    #                     # Remove dead thread or unauthorized thread from the list
    #                     for i,each_tup in enumerate(monitoring_list):
    #                         user_id = monitoring_list[i][0]
    #                         if each_tup[1].is_alive() == False:
    #                             self.snatcher_logger.error(f"user_id: {user_id}'s margin_call monitoring thread has died!")
    #                             body = f"user_id: {user_id}'s margin_call monitoring thread has died!"
    #                             self.telegram_bot.send_thread(chat_id=self.admin_id, text=body)
    #                             self.register_trading_msg(self.admin_id, "monitor_margin_call", "admin_msg", 'error', 'margin_call monitoring thread has died!', body)
    #                             monitoring_list.pop(i)
    #                         # Service period expired
    #                         if (self.userinfo_df[self.userinfo_df['user_id']==user_id]['datetime_end'] < datetime.datetime.now()).values[0]:
    #                             monitoring_list.pop(i)
    #             except Exception:
    #                 self.snatcher_logger.error(f"monitor_margin_call|{traceback.format_exc()}")
    #         self.monitor_margin_call_thread = Thread(target=monitor_margin_call, daemon=True)
    #         self.monitor_margin_call_thread.start()
    #         while True:
    #             if not self.monitor_margin_call_thread.is_alive():
    #                 self.snatcher_logger.error(f"monitor_margin_call|monitor_margin_call stopped! restarting monitor_margin_call thread..")
    #                 register(self.monitor_bot_token, self.monitor_bot_url, self.admin_id, self.node, input_type, title, "restarting monitor_margin_call thread..")
    #                 self.monitor_margin_call_thread = Thread(target=monitor_margin_call, daemon=True)
    #                 self.monitor_margin_call_thread.start()
    #             time.sleep(monitor_loop_secs)
    #     self.start_monitor_margin_call_thread = Thread(target=monitor_margin_call_loop, daemon=True)
    #     self.start_monitor_margin_call_thread.start()



############# trading trigger functions ###########################################################################
    def start_monitor_high_low_loop(self, loop_secs=0.05, monitor_loop_secs=2.5):
        if self.telegram_bot is None:
            self.snatcher_logger.error(f"start_monitor_high_low_loop|telegram_bot hasn't been set. Please run after setting the telegram bot.")
            return
        self.snatcher_logger.info(f"start_monitor_high_low_loop|start_monitor_high_low_loop started.")
        def start_monitor_high_low_loop_func():
            def high_low_loop_func():
                try:
                    jump_num = 0
                    while self.upbit_server_error_switch is False and self.okx_server_error_switch is False and self.upbit_server_check is False and self.okx_server_check is False:
                        time.sleep(loop_secs)
                        if jump_num > 100000000:
                            jump_num = 0
                        conn = self.local_db_pool.get_connection()
                        curr = conn.cursor(dictionary=True)
                        curr.execute("""SELECT * FROM addcoin""")
                        fetched = curr.fetchall()
                        if len(fetched) != 0:
                            self.addcoin_df = pd.DataFrame(fetched)
                        else:
                            self.addcoin_df = pd.DataFrame(columns=self.addcoin_col_names)
                        curr.execute("""SELECT * FROM addcir""")
                        fetched = curr.fetchall()
                        conn.close()
                        if len(fetched) != 0:
                            self.addcir_df = pd.DataFrame(fetched)
                        else:
                            self.addcir_df = pd.DataFrame(columns=self.addcir_col_names)
                        if len(self.addcoin_df) == 0:
                            time.sleep(loop_secs)
                            continue
                        # addcoin_df = test_snatcher.redis_client_3.read_json_to_df()
                        # userinfo_df = test_snatcher.redis_client_1.read_json_to_df()
                        valid_user_id_list = self.userinfo_df[self.userinfo_df['datetime_end']>=datetime.datetime.now()]['user_id'].to_list()
                        filtered_addcoin_df = self.addcoin_df[self.addcoin_df['user_id'].isin(valid_user_id_list)].reset_index(drop=True)
                        # If there's no valid user
                        if len(filtered_addcoin_df) == 0:
                            time.sleep(loop_secs)
                            continue
                        filtered_addcoin_df['merge_symbol'] = filtered_addcoin_df['symbol'].apply(lambda x: x+'USDT' if 'USDT' not in x else x)
                        # merged_df = get_kimp_df_func()
                        merged_df = self.get_kimp_df_func()
                        merged_addcoin_df = filtered_addcoin_df.merge(merged_df, left_on='merge_symbol', right_on='symbol')
                        merged_addcoin_df['enter_value'] = merged_addcoin_df.apply(lambda x: x['enter_kimp']*100 if 'USDT' not in x['symbol_x'] else x['enter_usdt'], axis=1)
                        merged_addcoin_df['exit_value'] = merged_addcoin_df.apply(lambda x: x['exit_kimp']*100 if 'USDT' not in x['symbol_x'] else x['exit_usdt'], axis=1)
                        # switch None: 최초, 0: 하향돌파 시, 1: 상향돌파 시
                        # auto_trade_switch 0: 진입대기, -1: 탈출대기, 1:탈출완료, 2:탈출에러
                        # case 1. switch None or False(0), High 돌파
                        high_break_alarm_uuid_list = (merged_addcoin_df[((merged_addcoin_df['switch'].isnull())|(merged_addcoin_df['switch']==False))
                                    &(merged_addcoin_df['exit_value']>=merged_addcoin_df['high'])]['redis_uuid'].to_list())
                        high_break_addcoin_df = self.addcoin_df[self.addcoin_df['redis_uuid'].isin(high_break_alarm_uuid_list)]#.drop('merge_symbol', axis=1)
                        # case 2. switch None or True(1), Low 돌파
                        low_break_alarm_uuid_list = (merged_addcoin_df[((merged_addcoin_df['switch'].isnull())|(merged_addcoin_df['switch']==True))
                                    &(merged_addcoin_df['enter_value']<=merged_addcoin_df['low'])]['redis_uuid'].to_list())
                        low_break_addcoin_df = self.addcoin_df[self.addcoin_df['redis_uuid'].isin(low_break_alarm_uuid_list)]#.drop('merge_symbol', axis=1)

                        if len(high_break_addcoin_df) != 0:
                            high_break_redis_uuid_list = high_break_addcoin_df['redis_uuid'].to_list()
                            # UPDATE database
                            conn = self.local_db_pool.get_connection()
                            curr = conn.cursor(dictionary=True)
                            sql = f"""UPDATE addcoin SET switch='1' WHERE redis_uuid IN ("""
                            for i, addcoin_redis_uuid in enumerate(high_break_redis_uuid_list):
                                sql += "'"+addcoin_redis_uuid+"'"
                                if i != len(high_break_redis_uuid_list) - 1:
                                    sql += ','
                            sql += ")"
                            curr.execute(sql)
                            conn.close()

                            # Start thread
                            high_break_process_th = Thread(target=self.high_break_process, args=(self.local_db_dict, high_break_addcoin_df, merged_df, self.userinfo_df, self.user_api_key_df, self.trade_history_df, self.get_dollar_dict()['price']), daemon=True)
                            high_break_process_th.start()

                        if len(low_break_addcoin_df) != 0:
                            low_break_redis_uuid_list = low_break_addcoin_df['redis_uuid'].to_list()
                            # UPDATE database
                            start = time.time() # TEST
                            conn = self.local_db_pool.get_connection()
                            curr = conn.cursor(dictionary=True)
                            sql = f"""UPDATE addcoin SET switch='0' WHERE redis_uuid IN ("""
                            for i, addcoin_redis_uuid in enumerate(low_break_redis_uuid_list):
                                sql += "'"+addcoin_redis_uuid+"'"
                                if i != len(low_break_redis_uuid_list) - 1:
                                    sql += ','
                            sql += ")"
                            curr.execute(sql)
                            conn.close()
                            self.snatcher_logger.info(f"low break update time: {time.time()-start}")

                            # Start thread
                            low_break_process_th = Thread(target=self.low_break_process, args=(self.local_db_dict, low_break_addcoin_df, merged_df, self.userinfo_df, self.user_api_key_df, self.get_dollar_dict()['price']), daemon=True)
                            # low_break_process_th = Thread(target=self.test_func, daemon=True)
                            low_break_process_th.start()

                        # Repeating trade cycle according to the addcir settings
                        filtered_addcir_df = self.addcir_df[self.addcir_df['user_id'].isin(valid_user_id_list)].reset_index(drop=True)
                        if len(filtered_addcir_df) != 0 and jump_num % 50 == 0:
                            addcir_merged_df = self.addcoin_df.merge(filtered_addcir_df, left_on='addcoin_uuid', right_on='addcir_uuid').dropna(subset=['addcoin_uuid', 'addcir_uuid'])
                            addcir_merged_df = addcir_merged_df[addcir_merged_df['cir_trade_switch']==1]
                            # Case 1. auto_trade_switch == 1 (탈출완료)
                            complete_merged_df = addcir_merged_df[addcir_merged_df['auto_trade_switch']==1]
                            if len(complete_merged_df) != 0:
                                addcir_addcoin_register_th = Thread(target=self.addcir_addcoin_register, args=(complete_merged_df, filtered_addcir_df, self.addcoin_df), daemon=True)
                                addcir_addcoin_register_th.start()
                            # Case 2. auto_trade_switch == 0 (진입대기)
                            waiting_merged_df = addcir_merged_df[addcir_merged_df['auto_trade_switch']==0]
                            if len(waiting_merged_df) != 0:
                                addcir_addcoin_refresh_th = Thread(target=self.addcir_addcoin_refresh, args=(waiting_merged_df, filtered_addcir_df, self.addcoin_df), daemon=True)
                                addcir_addcoin_refresh_th.start()
                        jump_num += 1
                except Exception:
                    self.snatcher_logger.info(f"Error occured in high_low_loop_func|{traceback.format_exc()}")
            self.high_low_loop_thread = Thread(target=high_low_loop_func, daemon=True)
            self.high_low_loop_thread.start()
            while True:
                time.sleep(monitor_loop_secs)
                if not self.high_low_loop_thread.is_alive():
                    self.snatcher_logger.error(f"high_low_loop_thread|high_low_loop_thread stopped! restarting high_low_loop_thread thread..")
                    title = 'high_low_loop_thread stopped! restarting high_low_loop_thread thread..'
                    register(self.monitor_bot_token, self.monitor_bot_url, self.admin_id, self.node, "monitor", title, "restarting high_low_loop_thread thread..")
                    self.high_low_loop_thread = Thread(target=high_low_loop_func, daemon=True)
                    self.high_low_loop_thread.start()
        self.start_monitor_high_low_loop_thread = Thread(target=start_monitor_high_low_loop_func, daemon=True)
        self.start_monitor_high_low_loop_thread.start()

    def stop_high_low_loop(self):
        self.upbit_server_error_switch = True
        self.okx_server_error_switch = True
        time.sleep(3)
        self.snatcher_logger.info(f"stop_high_low_loop|high_low_loop_thread.is_alive(): {self.high_low_loop_thread.is_alive()}")

    def high_break_process(self, db_dict, high_break_addcoin_df, merged_df, userinfo_df, user_api_key_df, trade_history_df, dollar):
        # self.snatcher_logger.info(f"high_break_process executed")
        for row_tup in high_break_addcoin_df.iterrows():
            def row_thread(row_tup, merged_df):
                try:
                    each_addcoin_series = row_tup[1]
                    user_id = int(each_addcoin_series['user_id'])
                    redis_uuid = each_addcoin_series['redis_uuid']
                    upbit_enter_uuid = each_addcoin_series['enter_upbit_uuid']
                    mgnMode = trade_history_df[trade_history_df['upbit_uuid']==upbit_enter_uuid]['okx_mgnMode'].values[0]
                    # one_user_info_df = userinfo_df[userinfo_df['user_id']==user_id]
                    # user_okx_leverage = int(one_user_info_df['okx_leverage'].values[0])
                    # user_okx_cross = int(one_user_info_df['okx_cross'].values[0])
                    if 'USDT' in each_addcoin_series['symbol']:
                        usdt_convert_switch = True
                    else:
                        usdt_convert_switch = False

                    # each_addcoin_series['auto_trade_switch'] == 0: 진입대기, -1: 탈출대기, 1:탈출완료
                    if each_addcoin_series['auto_trade_switch'] == -1:
                        # load api keys
                        user_upbit_access_key, user_upbit_secret_key = user_api_key_df[(user_api_key_df['user_id']==user_id)&(user_api_key_df['exchange']=='UPBIT')]\
                        .sample(n=1)[['access_key', 'secret_key']].values[0]
                        user_okx_access_key, user_okx_secret_key, user_okx_passphrase =  user_api_key_df[(user_api_key_df['user_id']==user_id)&(user_api_key_df['exchange']=='OKX')]\
                        .sample(n=1)[['access_key', 'secret_key', 'passphrase']].values[0]

                        # Execute exit trade
                        exit_id_list = [] # for updating upbit uuid and okx orderId
                        one_trade_history_df = trade_history_df[trade_history_df['upbit_uuid']==each_addcoin_series['enter_upbit_uuid']]
                        upbit_exit_qty = one_trade_history_df['upbit_qty'].values[0]
                        okx_exit_qty = one_trade_history_df['okx_qty'].values[0]
                        # enter_dollar_price = one_trade_history_df['dollar'].values[0]
                        self.exit_func(merged_df, 
                            dollar, 
                            user_id, 
                            redis_uuid,
                            mgnMode,
                            each_addcoin_series['symbol'].replace('USDT',''), 
                            (upbit_exit_qty,okx_exit_qty), 
                            user_upbit_access_key,
                            user_upbit_secret_key,
                            user_okx_access_key,
                            user_okx_secret_key,
                            user_okx_passphrase,
                            exit_id_list)
                        # UPDATE exit info and auto_trade_switch into the database
                        db_client = InitDBClient(**db_dict)
                        try:
                            sql = """UPDATE addcoin SET
                            last_updated_timestamp=%s,
                            exit_upbit_uuid=%s,
                            exit_okx_orderId=%s,
                            auto_trade_switch=%s WHERE redis_uuid=%s"""
                            val = (
                                datetime.datetime.now().timestamp()*10000000,
                                exit_id_list[0],
                                exit_id_list[1],
                                1,
                                redis_uuid
                            )
                            db_client.curr.execute(sql, val)
                            db_client.conn.commit()
                            self.exec_pnl(merged_df, user_id, redis_uuid, exit_id_list[0], dollar)
                        except Exception as e:
                            self.snatcher_logger.error(f"high_break_process|high_low_filter 에서 exit_func 이후 uuid, orderId UPDATE 실패 {traceback.format_exc()}")
                            title = "high_low_filter 에서 exit_func 이후 uuid, orderId UPDATE 실패"
                            body = f"{title}\n"
                            body += f"user_id: {user_id}, addcoin_redis_id: {redis_uuid}, symbol: {each_addcoin_series['symbol']}\n"
                            body += f"Error: {e}"
                            self.telegram_bot.send_thread(self.admin_id, body)
                            self.register_trading_msg(self.admin_id, "high_break_process", "admin_msg", 'error', title, body)
                            register(self.monitor_bot_token, self.monitor_bot_url, self.admin_id, self.node, 'error', 'high_low_filter 에서 exit_func 이후 uuid, orderId UPDATE 실패', str(e))
                            self.deactivate_addcoin(redis_uuid)
                            self.deactivate_addcoin_addcir(user_id, redis_uuid, '/addcoin 김프 탈출 거래 실패')
                        db_client.conn.close()

                    # update switch to the database
                    sql = "UPDATE addcoin SET switch=%s, last_updated_timestamp=%s WHERE redis_uuid=%s"
                    val = (1, int(datetime.datetime.now().timestamp()*10000000), redis_uuid)
                    db_client = InitDBClient(**db_dict)
                    db_client.curr.execute(sql, val)
                    db_client.conn.commit()
                    db_client.conn.close()
                    
                    # load results
                    current_symbol_df = merged_df[merged_df['symbol']==each_addcoin_series['symbol'].replace('USDT', '')+'USDT']
                    current_upbit_trade_price = current_symbol_df['trade_price'].iloc[0]
                    current_enter_kimp = current_symbol_df['enter_kimp'].iloc[0]
                    current_exit_kimp = current_symbol_df['exit_kimp'].iloc[0]
                    current_enter_usdt = current_symbol_df['enter_usdt'].iloc[0]
                    current_exit_usdt = current_symbol_df['exit_usdt'].iloc[0]
                    current_signed_change_rate = current_symbol_df['signed_change_rate'].iloc[0]
                    market_state = current_symbol_df['upbit_market_state'].iloc[0]
                    delisting_date = current_symbol_df['upbit_delisting_date'].iloc[0]
                    market_warning = current_symbol_df['upbit_market_warning'].iloc[0]
                    is_trading_suspended = current_symbol_df['upbit_is_trading_suspended'].iloc[0]

                    user_dict = userinfo_df[userinfo_df['user_id']==user_id][['alarm_num','alarm_period']].to_dict(orient='records')[0]
                    if usdt_convert_switch == False:
                        title = f"<b>{each_addcoin_series['symbol']}탈출김프 {each_addcoin_series['high']}% 상향돌파</b>"
                        body = f"{title} (달러:{krw(dollar)}원)\n"
                        body += f"<b>현재 {each_addcoin_series['symbol']}탈출김프: {round(current_exit_kimp*100,4)}%|테더환산: {round(current_exit_usdt,1)}</b>\n"
                    else:
                        title = f"<b>{each_addcoin_series['symbol'].replace('USDT','')}탈출환산값 {round(each_addcoin_series['high'],1)}원 상향돌파</b>"
                        body = f"{title} (달러:{krw(dollar)}원)\n"
                        body += f"<b>현재 {each_addcoin_series['symbol'].replace('USDT','')}탈출김프: {round(current_exit_kimp*100,4)}%|테더환산: {round(current_exit_usdt,1)}</b>\n"
                    signed_change_rate = round(current_signed_change_rate*100,2)
                    if signed_change_rate > 0:
                        temp_str = '+'
                    else:
                        temp_str = ''
                    body += f"거래ID: <b>{redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}</b>\n"
                    body += f"업비트 {each_addcoin_series['symbol']}: {krw(round(current_upbit_trade_price))}원 ({temp_str}{signed_change_rate})%\n"
                    body += f"업비트 Market상태: {market_state}\n"
                    body += f"업비트 상장폐지일: {delisting_date}\n"
                    body += f"업비트 경고종목: {market_warning}\n"
                    body += f"업비트 거래일시중지: {is_trading_suspended}"
                    self.telegram_bot.send_thread(user_id, body, user_dict['alarm_num'], user_dict['alarm_period'], 'html')
                    self.register_trading_msg(user_id, "high_break_process", "user_msg", 'normal', title, body)
                except Exception:
                    self.snatcher_logger.error(f"high_break_process|{traceback.format_exc()}")
            row_th = Thread(target=row_thread, args=(row_tup, merged_df), daemon=True)
            row_th.start()

    def low_break_process(self, db_dict, low_break_addcoin_df, merged_df, userinfo_df, user_api_key_df, dollar):
        for row_tup in low_break_addcoin_df.iterrows():
            def row_thread(row_tup, merged_df):
                try:
                    each_addcoin_series = row_tup[1]
                    user_id = int(each_addcoin_series['user_id'])
                    redis_uuid = each_addcoin_series['redis_uuid']
                    addcoin_uuid = each_addcoin_series['addcoin_uuid']
                    user_okx_leverage = int(userinfo_df[userinfo_df['user_id']==user_id]['okx_leverage'].values[0])
                    user_okx_cross = int(userinfo_df[userinfo_df['user_id']==user_id]['okx_cross'].values[0])
                    if 'USDT' in each_addcoin_series['symbol']:
                        usdt_convert_switch = True
                    else:
                        usdt_convert_switch = False

                    # each_addcoin_series['auto_trade_switch'] == 0: 진입대기, -1: 탈출대기, 1:탈출완료, 2:탈출에러
                    if each_addcoin_series['auto_trade_switch'] == 0:
                        # Load api keys
                        user_upbit_access_key, user_upbit_secret_key = user_api_key_df[(user_api_key_df['user_id']==user_id)&(user_api_key_df['exchange']=='UPBIT')]\
                            .sample(n=1)[['access_key', 'secret_key']].values[0]
                        user_okx_access_key, user_okx_secret_key, user_okx_passphrase =  user_api_key_df[(user_api_key_df['user_id']==user_id)&(user_api_key_df['exchange']=='OKX')]\
                            .sample(n=1)[['access_key', 'secret_key', 'passphrase']].values[0]

                        # Execute enter trade
                        enter_id_list = [] # for updating upbit uuid and okx orderId
                        self.enter_func(merged_df,
                            dollar,
                            user_id,
                            redis_uuid,
                            each_addcoin_series['symbol'].replace('USDT',''),
                            each_addcoin_series['auto_trade_capital'],
                            user_upbit_access_key,
                            user_upbit_secret_key,
                            user_okx_access_key,
                            user_okx_secret_key,
                            user_okx_passphrase,
                            user_okx_leverage,
                            user_okx_cross,
                            enter_id_list)            
                        # UPDATE auto_trade_switch in the database
                        db_client = InitDBClient(**db_dict)
                        timestamp_now = datetime.datetime.now().timestamp()*10000000
                        db_client.curr.execute("""UPDATE addcoin SET last_updated_timestamp=%s, switch=%s, auto_trade_switch=%s WHERE redis_uuid=%s""", (timestamp_now, 0, -1, redis_uuid))
                        db_client.conn.commit()
                        # If an error has been occured while enter_func, cancel the registered alarm
                        if enter_id_list == []:
                            body = f"high_low_filter 에서 enter_func 이후 uuid, orderId UPDATE 실패\n"
                            body += f"enter_id_list == []\n"
                            body += f"user_id: {user_id}, addcoin_redis_uuid: {redis_uuid}, symbol: {each_addcoin_series['symbol']}\n"
                            # bot.send_message(chat_id=admin_id, text=body) # comment on purpose

                            body = f"김프 진입 거래가 실패하여, {each_addcoin_series['symbol']}의 <b>등록된 자동거래 설정을 취소</b>합니다.\n"
                            self.telegram_bot.send_thread(user_id, body, 'html')
                            self.register_trading_msg(user_id, "low_break_process", "user_msg", 'warning', '김프 진입거래 실패로 인한 자동거래 삭제', body)
                            db_client.curr.execute("""DELETE FROM addcoin WHERE redis_uuid=%s""", redis_uuid)
                            self.deactivate_addcoin_addcir(user_id, redis_uuid, '/addcoin 김프 진입 거래 실패')
                            db_client.conn.commit()
                        else:
                            # When enter_func is processed successfully
                            timestamp_now = datetime.datetime.now().timestamp()*10000000
                            db_client.curr.execute("""UPDATE addcoin SET last_updated_timestamp=%s, enter_upbit_uuid=%s, enter_okx_orderId=%s WHERE redis_uuid=%s""", (timestamp_now, enter_id_list[0], enter_id_list[1], redis_uuid))
                            db_client.conn.commit()
                            self.exec_cgh(user_id, redis_uuid)
                        db_client.conn.close()
                        
                    # update switch to the database
                    timestamp_now = datetime.datetime.now().timestamp()*10000000
                    sql = "UPDATE addcoin SET switch=%s, last_updated_timestamp=%s WHERE redis_uuid=%s"
                    val = (0, int(timestamp_now), redis_uuid)
                    db_client = InitDBClient(**db_dict)
                    db_client.curr.execute(sql, val)
                    db_client.conn.commit()
                    db_client.conn.close()
                    
                    # load results
                    current_symbol_df = merged_df[merged_df['symbol']==each_addcoin_series['symbol'].replace('USDT', '')+'USDT']
                    current_upbit_trade_price = current_symbol_df['trade_price'].iloc[0]
                    current_enter_kimp = current_symbol_df['enter_kimp'].iloc[0]
                    current_exit_kimp = current_symbol_df['exit_kimp'].iloc[0]
                    current_enter_usdt = current_symbol_df['enter_usdt'].iloc[0]
                    current_exit_usdt = current_symbol_df['exit_usdt'].iloc[0]
                    current_signed_change_rate = current_symbol_df['signed_change_rate'].iloc[0]
                    market_state = current_symbol_df['upbit_market_state'].iloc[0]
                    delisting_date = current_symbol_df['upbit_delisting_date'].iloc[0]
                    market_warning = current_symbol_df['upbit_market_warning'].iloc[0]
                    is_trading_suspended = current_symbol_df['upbit_is_trading_suspended'].iloc[0]

                    user_dict = userinfo_df[userinfo_df['user_id']==user_id][['alarm_num','alarm_period']].to_dict(orient='records')[0]
                    if usdt_convert_switch == False:
                        title = f"<b>{each_addcoin_series['symbol']}진입김프 {each_addcoin_series['low']}% 하향돌파</b>"
                        body =  f"{title} (달러:{krw(dollar)}원)\n"
                        body += f"<b>현재 {each_addcoin_series['symbol']}진입김프: {round(current_enter_kimp*100,4)}%|테더환산: {round(current_enter_usdt,1)}</b>\n"
                    else:
                        title = f"<b>{each_addcoin_series['symbol'].replace('USDT','')}진입환산값 {round(each_addcoin_series['low'],1)}원 하향돌파</b>"
                        body = f"{title} (달러:{krw(dollar)}원)\n"
                        body += f"<b>현재 {each_addcoin_series['symbol'].replace('USDT','')}진입김프: {round(current_enter_kimp*100,4)}%|테더환산: {round(current_enter_usdt,1)}</b>\n"
                    signed_change_rate = round(current_signed_change_rate*100,2)
                    if signed_change_rate > 0:
                        temp_str = '+'
                    else:
                        temp_str = ''
                    body += f"거래ID: <b>{redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}</b>\n"
                    body += f"업비트 {each_addcoin_series['symbol']}: {krw(round(current_upbit_trade_price))}원 ({temp_str}{signed_change_rate})%\n"
                    body += f"업비트 Market상태: {market_state}\n"
                    body += f"업비트 상장폐지일: {delisting_date}\n"
                    body += f"업비트 경고종목: {market_warning}\n"
                    body += f"업비트 거래일시중지: {is_trading_suspended}"
                    self.telegram_bot.send_thread(user_id, body, user_dict['alarm_num'], user_dict['alarm_period'], 'html')
                    self.register_trading_msg(user_id, "low_break_process", "user_msg", 'normal', title, body)

                    # For deleting addcoin settings according to the balance.
                    if each_addcoin_series['auto_trade_switch'] == 0:
                        time.sleep(2)
                        self.cancel_addcoin(user_id, user_upbit_access_key, user_upbit_secret_key, user_okx_access_key, user_okx_secret_key, user_okx_passphrase)
                except Exception:
                    self.snatcher_logger.error(f"low_break_process|{traceback.format_exc()}")
            row_th = Thread(target=row_thread, args=(row_tup, merged_df), daemon=True)
            row_th.start()

    def addcir_addcoin_register(self, complete_merged_df, addcir_df, addcoin_df):
        for row_tup in complete_merged_df.iterrows():
            def register_thread():
                complete_merged_row = row_tup[1]
                addcoin_redis_uuid = complete_merged_row['redis_uuid_x']
                addcir_redis_uuid = complete_merged_row['redis_uuid_y']
                user_id = int(complete_merged_row['user_id_x'])
                # load api keys
                try:
                    user_upbit_access_key, user_upbit_secret_key = self.user_api_key_df[(self.user_api_key_df['user_id']==user_id)&(self.user_api_key_df['exchange']=='UPBIT')]\
                    .sample(n=1)[['access_key', 'secret_key']].values[0]
                    user_okx_access_key, user_okx_secret_key, user_okx_passphrase =  self.user_api_key_df[(self.user_api_key_df['user_id']==user_id)&(self.user_api_key_df['exchange']=='OKX')]\
                    .sample(n=1)[['access_key', 'secret_key', 'passphrase']].values[0]
                except:
                    self.snatcher_logger.error(f"addcir_addcoin_register|{traceback.format_exc()}")
                    raise Exception("addcir_addcoin_register|API Key load error")
                user_addcir_num_limit = self.userinfo_df[self.userinfo_df['user_id']==user_id]['addcir_num_limit'].values[0]
                user_cir_trade_num = int(complete_merged_row['cir_trade_num'])
                addcoin_series = addcoin_df[addcoin_df['redis_uuid']==addcoin_redis_uuid].iloc[0,:]
                user_addcir_df = addcir_df[addcir_df['redis_uuid']==addcir_redis_uuid]
                if user_addcir_num_limit != None:
                    user_addcir_num_limit = int(user_addcir_num_limit)
                    if user_cir_trade_num >= user_addcir_num_limit:
                        return
                    else:
                        self.exec_addcoin_register(addcoin_series, user_addcir_df)
                else:
                    self.exec_addcoin_register(addcoin_series, user_addcir_df)
            register_thread_th = Thread(target=register_thread, daemon=True)
            register_thread_th.start()

    def exec_addcoin_register(self, row, user_addcir_df, baseline_num=2):
        try:
            switch = 1
            auto_trade_switch = 0
            
            user_id = int(row['user_id'])
            cir_trade_capital = int(user_addcir_df['cir_trade_capital'].values[0])
            addcir_redis_uuid = user_addcir_df['redis_uuid'].values[0]
            addcir_uuid = user_addcir_df['addcir_uuid'].values[0]

            # # Apply addcoin re-registration into the DataFrame(Local Memory)
            # corr_index = self.addcoin_df[self.addcoin_df['addcoin_uuid']==addcir_uuid].index[0]
            # self.addcoin_df.loc[corr_index, 'switch'] = switch
            # self.addcoin_df.loc[corr_index, 'auto_trade_switch'] = auto_trade_switch

            # user_leverage = user_info_df[user_info_df['user_id']==user_id]['okx_leverage'].values[0]
            db_client = InitDBClient(**self.local_db_dict)
            db_client.curr.execute("""SELECT * FROM addcir WHERE redis_uuid=%s""", (addcir_redis_uuid))
            fetched_user_addcir_df = pd.DataFrame(db_client.curr.fetchall())
            db_client.conn.close()
            cir_auto_low = fetched_user_addcir_df['auto_low'].values[0]
            if cir_auto_low is not None:
                cir_auto_low = float(cir_auto_low)
            cir_auto_high = fetched_user_addcir_df['auto_high'].values[0]
            if cir_auto_high is not None:
                cir_auto_high = float(cir_auto_high)
            cir_auto_pauto_num = fetched_user_addcir_df['pauto_num'].values[0]
            if cir_auto_pauto_num is not None:
                cir_auto_pauto_num = float(cir_auto_pauto_num)

            if 'USDT' in row['symbol']:
                unit_str = '원'
            else:
                unit_str = '%'

            # AUTO
            if cir_auto_low != None:
                body = f"/addcir 설정에 따라, 자동으로 auto 김프거래를 재등록합니다.\n"
                body += f"코인: {row['symbol']}, Low: {cir_auto_low}{unit_str}, High: {cir_auto_high}{unit_str}\n"
                body += f"진입금액: {krw(round(cir_trade_capital))}원\n"
                body += f"등록된 자동거래는 /addcoin 을 통해 확인 가능합니다."
                self.telegram_bot.send_thread(chat_id=user_id, text=body)
                self.register_trading_msg(user_id, "exec_addcoin_register", "user_msg", 'normal', '반복거래설정(addcir)로 인한 자동거래(addcoin) 자동 재등록', body)
                # Execute AUTO addcoin registration
                db_client = InitDBClient(**self.local_db_dict)
                sql = """
                UPDATE addcoin SET 
                last_updated_timestamp=%s,
                high=%s,
                low=%s,
                switch=%s,
                auto_trade_switch=%s,
                auto_trade_capital=%s
                WHERE addcoin_uuid=%s
                """
                timestamp_now = datetime.datetime.now().timestamp()*10000000
                val = [timestamp_now, cir_auto_high, cir_auto_low, switch, auto_trade_switch, cir_trade_capital, addcir_uuid]
                db_client.curr.execute(sql, val)
                db_client.conn.commit()
                db_client.conn.close()
                addcir_display_id = redis_uuid_to_display_id(self.addcir_df, addcir_redis_uuid)
                addcoin_redis_uuid = self.addcoin_df[self.addcoin_df['addcoin_uuid']==addcir_uuid]['redis_uuid'].values[0]
                addcoin_display_id = redis_uuid_to_display_id(self.addcoin_df, addcoin_redis_uuid)
                body = f"{row['symbol']}(반복ID:{addcir_display_id})의 /addcoin 설정(거래ID:{addcoin_display_id})이 /addcir 설정에 따라 정상적으로 재등록되었습니다.\n"
                body += f"설정된 Low 값: {cir_auto_low}{unit_str}, High 값: {cir_auto_high}{unit_str}"
                self.telegram_bot.send_thread(user_id, body)
                self.register_trading_msg(user_id, "exec_addcoin_register", "user_msg", 'normal', '반복거래설정(addcir)로 인한 자동거래(addcoin) 자동 재등록', body)

            # PAUTO
            elif cir_auto_pauto_num != None:
                body = f"/addcir 설정에 따라, 자동으로 pauto 김프거래를 재등록합니다.\n"
                body += f"코인: {row['symbol']}, 김프폭%: {cir_auto_pauto_num}%\n"
                body += f"진입금액: {krw(round(cir_trade_capital))}원\n"
                body += f"등록된 자동거래는 /addcoin 을 통해 확인 가능합니다."
                self.telegram_bot.send_thread(chat_id=user_id, text=body)
                self.register_trading_msg(user_id, "exec_addcoin_register", "user_msg", 'normal', '반복거래설정(addcir)로 인한 자동거래(addcoin) 자동 재등록', body)
                # Execute PAUTO addcoin registration
                # use multiprocessing for drawing a plot
                manager = Manager()
                return_dict = manager.dict()
                get_plot_proc = Process(target=self.data_processor.get_pboundary_plot, args=(row['symbol'], 1, cir_auto_pauto_num, return_dict), daemon=True)
                get_plot_proc.start()
                get_plot_proc.join()
                buf, lower_bound, upper_bound = return_dict['return']
                db_client = InitDBClient(**self.local_db_dict)
                sql = """
                UPDATE addcoin SET 
                last_updated_timestamp=%s,
                high=%s,
                low=%s,
                switch=%s,
                auto_trade_switch=%s,
                auto_trade_capital=%s
                WHERE addcoin_uuid=%s
                """
                timestamp_now = datetime.datetime.now().timestamp()*10000000
                val = [timestamp_now, upper_bound, lower_bound, switch, auto_trade_switch, cir_trade_capital, addcir_uuid]
                db_client.curr.execute(sql, val)
                db_client.conn.commit()
                db_client.conn.close()
                addcir_display_id = redis_uuid_to_display_id(self.addcir_df, addcir_redis_uuid)
                addcoin_redis_uuid = self.addcoin_df[self.addcoin_df['addcoin_uuid']==addcir_uuid]['redis_uuid'].values[0]
                addcoin_display_id = redis_uuid_to_display_id(self.addcoin_df, addcoin_redis_uuid)
                body = f"{row['symbol']}(반복ID:{addcir_display_id})의 /addcoin 설정(거래ID:{addcoin_display_id})이 /addcir 설정에 따라 정상적으로 재등록되었습니다.\n"
                body += f"설정된 Low 값: {lower_bound}{unit_str}, High 값: {upper_bound}{unit_str}"
                self.telegram_bot.send_thread(user_id, body)
                self.register_trading_msg(user_id, "exec_addcoin_register", "user_msg", 'normal', '반복거래설정(addcir)로 인한 자동거래(addcoin) 자동 재등록', body)

            # increase cir_trade_num
            db_client = InitDBClient(**self.local_db_dict)
            db_client.curr.execute("""UPDATE addcir SET last_updated_timestamp=%s, cir_trade_num=%s WHERE redis_uuid=%s""", (datetime.datetime.now().timestamp()*10000000, int(fetched_user_addcir_df['cir_trade_num'].values[0]+1), addcir_redis_uuid))
            db_client.conn.commit()
            db_client.conn.close()
        except Exception as e:
            time.sleep(3)
            self.snatcher_logger.error(f"exec_addcoin_register|{traceback.format_exc()}")
            title = f"error occured in exec_addcoin_register"
            body = f"{title}\n"
            body += f"user_id: {user_id}\n"
            body += f"addcir_redis_uuid: {addcir_redis_uuid}\n"
            body += f"cir_trade_capital: {cir_trade_capital}\n"
            body += f"error: {e}"
            self.telegram_bot.send_thread(chat_id=self.admin_id, text=body)
            self.register_trading_msg(self.admin_id, "exec_addcoin_register", "admin_msg", 'error', title, body)

    # verbose -> every 3minute, shows tracing kimp trend, verbose=True <- FOR TEST
    def addcir_addcoin_refresh(self, waiting_merged_df, addcir_df, addcoin_df, refresh_min=3, verbose=False):
        for row_tup in waiting_merged_df.iterrows():
            waiting_merged_row = row_tup[1]
            addcoin_redis_uuid = waiting_merged_row['redis_uuid_x']
            addcir_redis_uuid = waiting_merged_row['redis_uuid_y']
            user_id = int(waiting_merged_row['user_id_x'])
            if len(self.user_api_key_df[(self.user_api_key_df['user_id']==user_id)&(self.user_api_key_df['exchange']=='UPBIT')]) == 0 or \
                len(self.user_api_key_df[(self.user_api_key_df['user_id']==user_id)&(self.user_api_key_df['exchange']=='OKX')]) == 0:
                continue
            def refresh_thread():
                # load api keys
                try:
                    user_upbit_access_key, user_upbit_secret_key = self.user_api_key_df[(self.user_api_key_df['user_id']==user_id)&(self.user_api_key_df['exchange']=='UPBIT')]\
                    .sample(n=1)[['access_key', 'secret_key']].values[0]
                    user_okx_access_key, user_okx_secret_key, user_okx_passphrase =  self.user_api_key_df[(self.user_api_key_df['user_id']==user_id)&(self.user_api_key_df['exchange']=='OKX')]\
                    .sample(n=1)[['access_key', 'secret_key', 'passphrase']].values[0]
                except:
                    self.snatcher_logger.error(f"addcir_addcoin_refresh| user_id: {user_id}, {traceback.format_exc()}")
                    raise Exception("addcir_addcoin_refresh|API Key load error")
                addcoin_series = addcoin_df[addcoin_df['redis_uuid']==addcoin_redis_uuid].iloc[0,:]
                user_addcir_df = addcir_df[addcir_df['redis_uuid']==addcir_redis_uuid]
                self.exec_addcoin_refresh(addcoin_series, user_addcir_df, refresh_min, verbose)
            refresh_thread_th = Thread(target=refresh_thread, daemon=True)
            refresh_thread_th.start()

    def exec_addcoin_refresh(self, row, user_addcir_df, refresh_min, verbose):
        # if it's been more than 3 minutes, re-register addcoin
        try:
            if row['datetime'] + datetime.timedelta(minutes=int(refresh_min)) < datetime.datetime.now():
                user_addcir_df = user_addcir_df.where(pd.notna(user_addcir_df), None)
                user_id = int(row['user_id'])
                symbol = user_addcir_df['symbol'].values[0]
                pauto_num = user_addcir_df['pauto_num'].values[0]
                fauto_num = user_addcir_df['fauto_num'].values[0]
                auto_trade_capital = int(user_addcir_df['cir_trade_capital'].values[0])
                addcir_redis_uuid = user_addcir_df['redis_uuid'].values[0]
                addcir_uuid = user_addcir_df['addcir_uuid'].values[0]

                # AUTO
                if user_addcir_df['auto_low'].values[0] != None:
                    # No need to refresh
                    return
                # PAUTO
                elif user_addcir_df['pauto_num'].values[0] != None:
                    # Execute AUTO addcoin registration
                    # use multiprocessing for drawing a plot
                    manager = Manager()
                    return_dict = manager.dict()
                    get_plot_proc = Process(target=self.data_processor.get_pboundary_plot, args=(row['symbol'], 1, pauto_num, return_dict), daemon=True)
                    get_plot_proc.start()
                    get_plot_proc.join()
                    buf, lower_bound, upper_bound = return_dict['return']
                    db_client = InitDBClient(**self.local_db_dict)
                    sql = """
                    UPDATE addcoin SET 
                    last_updated_timestamp=%s,
                    high=%s,
                    low=%s,
                    switch=%s,
                    auto_trade_switch=%s,
                    auto_trade_capital=%s
                    WHERE addcoin_uuid=%s
                    """
                    switch = 1
                    auto_trade_switch = 0
                    val = [datetime.datetime.now().timestamp()*10000000, upper_bound, lower_bound, switch, auto_trade_switch, auto_trade_capital, addcir_uuid]
                    db_client.curr.execute(sql, val)
                    db_client.conn.commit()
                    db_client.conn.close()
                    if verbose:
                        addcir_display_id = redis_uuid_to_display_id(self.addcir_df, addcir_redis_uuid)
                        addcoin_redis_uuid = self.addcoin_df[self.addcoin_df['addcoin_uuid']==addcir_uuid]['redis_uuid'].values[0]
                        addcoin_display_id = redis_uuid_to_display_id(self.addcoin_df, addcoin_redis_uuid)
                        body = f"반복ID: {addcir_display_id} 에 의해 /addcoin (거래ID: {addcoin_display_id}) 의 pauto 설정이 갱신되었습니다."
                        self.telegram_bot.send_thread(user_id, body)
                        self.register_trading_msg(user_id, "exec_addcoin_refresh", "user_msg", 'normal', '반복거래설정으로 인한 자동거래 진입값 갱신', body)
                else:
                    trade_type = -1
                    self.snatcher_logger.error(f"exec_addcoin_refresh|trade type error, neither auto or pauto.")
        except Exception:
            self.snatcher_logger.error(f"exec_addcoin_refresh|{traceback.format_exc()}")

    def enter_func(self, kimp_df, dollar, user_id, redis_uuid, symbol, value_krw, user_upbit_access_key, user_upbit_secret_key, user_okx_access_key, user_okx_secret_key, user_okx_passphrase, leverage, okx_cross, enter_id_list=None, balance_check=False, change_margin_leverage=False):
        try:
            symbol_df = kimp_df[kimp_df['symbol']==symbol]
            # calculate entering capital
            usdt_converted_dollar = symbol_df[['enter_usdt','exit_usdt']].mean(axis=1).values[0]
            value_usd = value_krw/(usdt_converted_dollar*1.005) # 0.5% margin for the enter amount of KRW
            # upbit_trade_price = symbol_df['trade_price'].iloc[0]
            upbit_ask_price = symbol_df['upbit_ask_price'].iloc[0]
            # upbit_bid_price = symbol_df['upbit_bid_price'].iloc[0]
            okx_bid_price = symbol_df['okx_bid_price'].iloc[0]
            # okx_bid_price_krw = symbol_df['okx_bid_price_krw'].iloc[0]
            # okx_ask_price = symbol_df['okx_ask_price'].iloc[0]
            # okx_ask_price_krw = symbol_df['okx_ask_price_krw'].iloc[0]
            targeted_kimp = symbol_df['enter_kimp'].iloc[0]
            if okx_cross == 0:
                mgnMode = "cross"
            else:
                mgnMode = "isolated"

            # BTC, ETH, BCH, LTC -> 0.001 까지 가능
            if symbol in ['BTC','ETH','BCH','LTC']:
                enter_quantity = round(value_usd / okx_bid_price, 3)
                if enter_quantity*okx_bid_price > value_usd:
                    enter_quantity = round((enter_quantity - 0.001), 3)

            # ETC, NEO, LINK -> 0.01 까지 가능
            elif symbol in ['ETC','NEO', 'LINK']:
                enter_quantity = round(value_usd / okx_bid_price, 2)
                if enter_quantity*okx_bid_price > value_usd:
                    enter_quantity = round((enter_quantity - 0.01), 2)
            else:
                enter_quantity = value_usd // okx_bid_price

            if enter_quantity == 0:
                # print(f"투입금액이 {symbol} 1개의 가격보다 낮습니다. \n주문을 취소합니다.")
                body = f"투입금액이 {symbol} 1개의 가격보다 낮습니다. \n주문을 취소합니다."
                self.telegram_bot.send_thread(chat_id=user_id, text=body)
                self.register_trading_msg(user_id, "enter_func", "user_msg", 'warning', '최소주문금액으로 인한 주문 취소', body)
                return
            
            okx_sz = self.okx_adaptor.convert_qty_to_sz(symbol+'-USDT-SWAP', enter_quantity)
            if okx_sz < 1:
                body = f"Okx 거래소의 {symbol}무기한계약의 최소 거래 개수는 {1/okx_sz*enter_quantity}개 입니다.\n주문을 취소합니다."
                self.telegram_bot.send_thread(chat_id=user_id, text=body)
                self.register_trading_msg(user_id, "enter_func", "user_msg", 'warning', 'OKX 최소주문개수(sz)로 인한 주문 취소', body)
                return

            modified_input_value_usd = okx_bid_price*enter_quantity
            modified_input_value_krw = upbit_ask_price*enter_quantity

            if balance_check:
                upbit_return_dict = {}
                upbit_balance_df_thread = Thread(target=self.upbit_adaptor.get_upbit_spot_balance, args=(user_upbit_access_key, user_upbit_secret_key, upbit_return_dict), daemon=True)
                upbit_balance_df_thread.start()
                okx_usdm_balance_df = self.okx_adaptor.get_okx_trade_balance(user_okx_access_key, user_okx_secret_key, user_okx_passphrase)
                upbit_balance_df_thread.join()
                upbit_balance_df = upbit_return_dict['res']
                upbit_krw_balance = upbit_balance_df[upbit_balance_df['currency']=='KRW']['balance'].iloc[0]
                okx_usdt_balance = okx_usdm_balance_df[okx_usdm_balance_df['ccy']=='USDT']['availBal'].iloc[0]
                enter_switch = True
                body = ''
                if upbit_krw_balance < modified_input_value_krw * 1.0:
                    body += f"업비트 잔고가 {krw(modified_input_value_krw-upbit_krw_balance)}원 부족합니다.\n"
                    body += f"업비트 진입 금액: {krw(modified_input_value_krw)}원, 업비트 잔고: {krw(upbit_krw_balance)}원\n"
                    if enter_switch:
                        enter_switch = False

                if okx_usdt_balance < (modified_input_value_usd * 1.0)/leverage:
                    body += f"OKX 잔고가 {modified_input_value_usd/leverage-okx_usdt_balance}USDT 부족합니다.\n"
                    body += f"OKX 진입 금액: {modified_input_value_usd/leverage}USDT (레버리지{leverage}배) OKX 잔고: {okx_usdt_balance}USDT\n"
                    if enter_switch:
                        enter_switch = False

                if enter_switch == False:
                    body += f"잔고가 부족하여 거래진입을 중지합니다."
                    self.telegram_bot.send_thread(chat_id=user_id, text=body)
                    self.register_trading_msg(user_id, "enter_func", "user_msg", 'warning', '잔고 부족으로 인한 거래진입중단', body)
                    return

            # Start trading
            okx_symbol = symbol + '-USDT-SWAP'
            upbit_symbol = 'KRW-' + symbol

            # Deprecated. => this will be handled in addcoin function in telegram_bot.
            # Change margin type for Okx before trading
            if change_margin_leverage:
                # okx_cross == 0 -> isolated, okx_cross == 1 -> cross
                if okx_cross == 0:
                    res = self.okx_adaptor.okx_change_leverage(user_okx_access_key, user_okx_secret_key, user_okx_passphrase, okx_symbol, leverage, mgnMode)
                    if res['sCode'] == "0":
                        body = f"{okx_symbol} 마켓이 격리(Isolated)마진, 레버리지 {leverage}배로 변경되었습니다.\n"
                    else:
                        raise Exception(f"마진모드설정에서 에러가 발생했습니다. okx_cross: {okx_cross}, okx_leverage: {leverage} error:{res['sMsg']}")
                elif okx_cross == 1:
                    res = self.okx_adaptor.okx_change_leverage(user_okx_access_key, user_okx_secret_key, user_okx_passphrase, okx_symbol, leverage, mgnMode)
                    if res['sCode'] == "0":
                        body = f"{okx_symbol} 마켓이 교차(Cross)마진, 레버리지 {leverage}배로 변경되었습니다.\n"
                    else:
                        raise Exception(f"마진모드설정에서 에러가 발생했습니다. okx_cross: {okx_cross}, okx_leverage: {leverage} error:{res['sMsg']}")
            else:
                res = {'leverage': self.userinfo_df[self.userinfo_df['user_id']==user_id]['okx_leverage'].values[0]}

            okx_return_dict = {}                        
            okx_enter_th = Thread(target=self.okx_adaptor.okx_market_enter, args=(user_okx_access_key, user_okx_secret_key, user_okx_passphrase, okx_symbol, enter_quantity, mgnMode, okx_return_dict), daemon=True)
            okx_enter_th.start()                        
            # upbit_enter_res = self.upbit_adaptor.upbit_market_enter(user_upbit_access_key, user_upbit_secret_key, upbit_symbol, str(modified_input_value_krw))
            upbit_enter_res = self.upbit_adaptor.upbit_limit_market_enter(user_upbit_access_key, user_upbit_secret_key, upbit_symbol, enter_quantity, upbit_ask_price)
            okx_enter_th.join()                        
            okx_enter_res = okx_return_dict['res']
            ## Example 
            # {'clOrdId': '',
            # 'ordId': '586947436766162944',
            # 'sCode': '0',
            # 'sMsg': 'Order placed',
            # 'tag': ''}
            # Okx response validation process
            okx_error_switch = False
            if okx_return_dict['state'] == 'OK':
                body = f"<b>거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}</b>({symbol})의 OKX SHORT거래가 정상적으로 진행되었습니다."
                self.telegram_bot.send_thread(user_id, body, parse_mode='html')
                self.register_trading_msg(user_id, "enter_func", "user_msg", 'normal', f'거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}({symbol}) OKX SHORT 거래 성공', body)
            else:
                okx_error_switch = True
                body = f"<b>거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}</b>({symbol})의 OKX SHORT거래에 에러가 발생했습니다.\n"
                body += f"ERROR: {okx_enter_res['sMsg']}"
                self.telegram_bot.send_thread(user_id, body, parse_mode='html')
                self.register_trading_msg(user_id, "enter_func", "user_msg", 'error', f'거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}({symbol}) OKX SHORT 거래 실패', body)
                register(self.monitor_bot_token, self.monitor_bot_url, user_id, self.node, 'error', f'거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}({symbol}) OKX SHORT 거래 실패', body)

            # Upbit response validation process
            upbit_error_switch = False
            if upbit_enter_res['response']['status_code'] == 201:
                body = f"<b>거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}</b>({symbol})의 업비트 매수거래가 정상적으로 진행되었습니다."
                self.telegram_bot.send_thread(user_id, body, parse_mode='html')
                self.register_trading_msg(user_id, "enter_func", "user_msg", 'normal', f'거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}({symbol}) 업비트 매수 거래 성공', body)
            else:
                upbit_error_switch = True
                body = f"<b>거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}</b>({symbol})의 업비트 매수거래에 에러가 발생했습니다.\n"
                body += f"{upbit_enter_res['result']['error']['message']}"
                self.telegram_bot.send_thread(user_id, body, parse_mode='html')
                self.register_trading_msg(user_id, "enter_func", "user_msg", 'error', f'거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}({symbol}) 업비트 매수 거래 실패', body)
                register(self.monitor_bot_token, self.monitor_bot_url, user_id, self.node, 'error', f'거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}({symbol}) 업비트 매수 거래 실패', body)

            if okx_error_switch or upbit_error_switch:
                body = f"<b>경고! 거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}({symbol})의 진입 시 오류가 발생하여 거래가 정상적으로 처리되지 않았습니다.</b>\n"
                body += f"업비트 혹은 OKX에서 거래 상황을 확인 하시기 바랍니다.\n"
                body += f"TRADE ERROR가 TRUE인 곳에서 에러가 발생하였습니다.\n"
                body += f"TRADE ERROR| 업비트: {upbit_error_switch}, OKX: {okx_error_switch}"
                if okx_error_switch == True:
                    body += f"\nOKX 에러: {okx_enter_res['sMsg']}"
                if upbit_error_switch == True:
                    body += f"\n업비트 에러: {upbit_enter_res['result']['error']['message']}"
                self.telegram_bot.send_thread(user_id, body, 5, 5, parse_mode='html')
                self.register_trading_msg(user_id, "enter_func", "user_msg", 'error', f'거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}({symbol}) 진입 시 오류 발생', body)
                register(self.monitor_bot_token, self.monitor_bot_url, user_id, self.node, 'error', f'거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}({symbol}) 진입 시 오류 발생', body, send_counts=1)

                body = f"<b>거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}</b>({symbol})의 진입 시 거래 정상처리 되지 않음.\n"
                body += f"TRADE ERROR| 업비트: {upbit_error_switch}, OKX: {okx_error_switch}\n"
                body += f"user_id: {user_id}, symbol: {symbol}"
                if okx_error_switch == True:
                    body += f"\nOKX 에러: {okx_enter_res['sMsg']}"
                if upbit_error_switch == True:
                    body += f"\n업비트 에러: {upbit_enter_res['result']['error']['message']}"
                self.telegram_bot.send_thread(chat_id=self.admin_id, text=body, parse_mode='html')
                self.register_trading_msg(self.admin_id, "enter_func", "admin_msg", 'error', f'유저 거래({symbol}) 진입 시 정상처리 되지 않음.', body)
                user_safe_reverse = self.userinfo_df[self.userinfo_df['user_id']==user_id]['safe_reverse'].values[0]
                if user_safe_reverse == 1:
                    self.revert_position('enter', user_id, redis_uuid, user_upbit_access_key, user_upbit_secret_key, user_okx_access_key, user_okx_secret_key, user_okx_passphrase, upbit_error_switch, okx_error_switch, upbit_enter_res, okx_enter_res, mgnMode)
                return

            okx_orderId = okx_enter_res['ordId']
            upbit_uuid = upbit_enter_res['result']['uuid']
            # This is for updating addcoin database
            if enter_id_list != None:
                enter_id_list.append(upbit_uuid)
                enter_id_list.append(okx_orderId)

            # waiting for 5 sec before fetching order
            time.sleep(5)
            okx_waiting_count = 0
            while okx_waiting_count <= 10: # Waiting for fetching order info
                okx_order_info_dict = self.okx_adaptor.okx_order_info(user_okx_access_key, user_okx_secret_key, user_okx_passphrase, okx_symbol, okx_orderId)
                if okx_order_info_dict['sCode'] != '0':
                    time.sleep(2)
                    okx_waiting_count += 1
                    if okx_waiting_count == 10:
                        raise Exception(okx_order_info_dict['sMsg'])
                else:
                    break

            upbit_order_info_dict = self.upbit_adaptor.upbit_order_info(user_upbit_access_key, user_upbit_secret_key, upbit_uuid)
            upbit_waiting_count = 0
            while float(upbit_order_info_dict['result']['executed_volume']) == 0: # Waiting for fetching order info
                if upbit_waiting_count == 10:
                    break
                body = f"enter_func 에서 float(upbit_order_info_dict['result']['executed_volume']) == 0 발생!\n"
                body += f"user_id: {user_id}, upbit_uuid: {upbit_uuid}"
                self.telegram_bot.send_thread(self.admin_id, body)
                self.register_trading_msg(user_id, "enter_func", "admin_msg", 'error', f'enter_func 업비트 order info 딜레이 발생', body)
                time.sleep(1)
                upbit_order_info_dict = self.upbit_adaptor.upbit_order_info(user_upbit_access_key, user_upbit_secret_key, upbit_uuid)
                upbit_waiting_count += 1


            okx_price = float(okx_order_info_dict['avgPx'])
            okx_price_krw = okx_price * dollar
            okx_qty = okx_order_info_dict['executedQty']
            okx_side = okx_order_info_dict['side']

            try:
                upbit_price = round(sum([float(x['funds']) for x in upbit_order_info_dict['result']['trades']]) / sum([float(x['volume']) for x in upbit_order_info_dict['result']['trades']]), 2) # New one for both limit_market_order and market_order
            except Exception as e:
                upbit_price = float(upbit_order_info_dict['result']['price']) / float(upbit_order_info_dict['result']['executed_volume']) # Original one only for Market order
                register(self.monitor_bot_token, self.monitor_bot_url, self.admin_id, self.node, 'error', f'upbit_price 계산과정에서 에러 발생.', traceback.format_exc())
            try:
                upbit_qty = sum([float(x['volume']) for x in upbit_order_info_dict['result']['trades']]) # New one for both limit_market_order and market_order
            except Exception as e:
                upbit_qty = upbit_order_info_dict['result']['executed_volume'] # Original one only for market_order
                register(self.monitor_bot_token, self.monitor_bot_url, self.admin_id, self.node, 'error', f'upbit_qty 계산과정에서 에러 발생.', traceback.format_exc())
            upbit_side = upbit_order_info_dict['result']['side']

            executed_kimp = (upbit_price - okx_price_krw) / okx_price_krw

            db_client = InitDBClient(**self.local_db_dict)
            sql = """INSERT INTO trade_history
            (
                user_id,
                datetime,
                timestamp,
                symbol,
                addcoin_redis_uuid,
                dollar,
                upbit_uuid,
                upbit_price,
                upbit_side,
                upbit_qty,
                okx_orderId,
                okx_mgnMode,
                okx_leverage,
                okx_side,
                okx_price,
                okx_price_krw,
                okx_liquidation_price,
                okx_qty,
                targeted_kimp,
                executed_kimp
            )
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """
            now_datetime = datetime.datetime.now()
            val = (user_id, now_datetime, now_datetime.timestamp()*10000000, symbol, redis_uuid, float(dollar), upbit_uuid, float(upbit_price), upbit_side, float(upbit_qty), okx_orderId, mgnMode, int(res['leverage']), okx_side, okx_price, okx_price_krw, okx_liquidation_price, okx_qty, float(targeted_kimp), float(executed_kimp))
            db_client.curr.execute(sql, val)
            db_client.conn.commit()
            db_client.conn.close()

            body = f"<b>거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}</b>\n"
            body += f"최초설정 OKX 투입금액: {round(value_usd,2)}USD\n"
            body += f"OKX 최대 투입 가능 {symbol}개수: {enter_quantity}\n"
            body += f"수정된 OKX 진입 금액: {round(modified_input_value_usd,2)}USDT ({symbol} {enter_quantity}개)\n"
            body += f"OKX {okx_symbol} 가격: {round(okx_price,2)}USDT, SHORT수량: {okx_qty}개\n"
            body += f"OKX {okx_symbol} KRW가격: {krw(round(okx_price_krw))}원\n"
            body += f"OKX 실제투입금액: {round(modified_input_value_usd/res['leverage'],2)}USDT (레버리지: {res['leverage']}배)\n"
            body += f"수정된 업비트 진입 금액: {krw(round(modified_input_value_krw))}원 ({symbol} {enter_quantity}개)\n"
            body += f"업비트 {symbol} 가격: {krw(round(upbit_price))}원, 매수수량: {upbit_qty}개\n"
            body += f"현재 달러환율: {krw(dollar)}원\n"
            body += f"<b>타겟 kimp: {round(targeted_kimp*100,3)}%</b>, 타겟 USDT환산: {round((1+targeted_kimp)*dollar, 1)}원\n"
            body += f"<b>실행 kimp: {round(executed_kimp*100,3)}%</b>, 실행 USDT환산: {round((1+executed_kimp)*dollar, 1)}원"
            self.telegram_bot.send_thread(user_id, body, parse_mode='html')
            self.register_trading_msg(user_id, "enter_func", "user_msg", 'normal', f'거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)} 김프거래 진입체결', body)
            return
        except Exception as e:
            self.snatcher_logger.error(f"enter_func|{traceback.format_exc()}")
            body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
            try:
                body += f"<b>거래ID: {redis_uuid}</b>\n"
            except:
                body += f"<b>거래ID: {None}</b>\n"
            try:
                body += f"코인심볼: {symbol}\n"
            except:
                body += f"코인심볼: {None}\n"
            try:
                body += f"업비트 매수수량: {upbit_qty}개\n"
            except:
                body += f"업비트 매수수량: {None}개\n"
            try:
                body += f"OKX SHORT수량: {okx_qty}개\n"
            except:
                body += f"OKX SHORT수량: {None}개\n"
            body += f"error: {e}\n"
            self.telegram_bot.send_thread(user_id, body)
            self.register_trading_msg(user_id, "enter_func", "user_msg", 'error', f'김프거래 진입과정에서 에러 발생', body)
            register(self.monitor_bot_token, self.monitor_bot_url, user_id, self.node, 'error', f'김프거래 진입과정에서 에러 발생', body)
            try:
                self.telegram_bot.send_thread(self.admin_id, body)
                self.register_trading_msg(self.admin_id, "enter_func", "admin_msg", 'error', f'김프거래 진입과정에서 알 수 없는 에러 발생', body)
                register(self.monitor_bot_token, self.monitor_bot_url, self.admin_id, self.node, 'error', 'error occured in enter_func', str(e))
                body = f"enter_func 에서 오류발생! user_id: {user_id}\n"
                try:
                    body += f"<b>거래ID: {redis_uuid}</b>\n"
                except:
                    body += f"<b>거래ID: {None}</b>\n"
                try:
                    body += f"코인심볼: {symbol}\n"
                except:
                    body += f"코인심볼: {None}\n"
                try:
                    body += f"업비트 매수수량: {upbit_qty}개\n"
                except:
                    body += f"업비트 매수수량: {None}개\n"
                try:
                    body += f"OKX SHORT수량: {okx_qty}개\n"
                except:
                    body += f"OKX SHORT수량: {None}개\n"
                body += f"okx_orderId: {okx_orderId}\n"
                body += f"upbit_uuid: {upbit_uuid}\n"
                body += f"okx_error_switch: {okx_error_switch}\n"
                body += f"upbit_error_switch: {upbit_error_switch}\n"
                body += f"Error: {e}"
                self.telegram_bot.send_thread(self.admin_id, body)
                self.register_trading_msg(self.admin_id, "enter_func", "admin_msg", 'error', f'김프거래 진입과정에서 알 수 없는 에러 발생', body)
                register(self.monitor_bot_token, self.monitor_bot_url, self.admin_id, self.node, 'error', 'error occured in enter_func', str(e))
            except Exception as e:
                self.telegram_bot.send_thread(self.admin_id, body)
                self.register_trading_msg(self.admin_id, "enter_func", "admin_msg", 'error', f'김프거래 진입과정에서 알 수 없는 에러 발생', body)
                body = f"enter_func 에서 오류발생! user_id: {user_id}\n"
                try:
                    body += f"<b>거래ID: {redis_uuid}</b>\n"
                except:
                    body += f"<b>거래ID: {None}</b>\n"
                try:
                    body += f"코인심볼: {symbol}\n"
                except:
                    body += f"코인심볼: {None}\n"
                try:
                    body += f"업비트 매수수량: {upbit_qty}개\n"
                except:
                    body += f"업비트 매수수량: {None}개\n"
                try:
                    body += f"OKX SHORT수량: {okx_qty}개\n"
                except:
                    body += f"OKX SHORT수량: {None}개\n"
                body += f"okx_error_switch: {okx_error_switch}\n"
                body += f"upbit_error_switch: {upbit_error_switch}\n"
                body += f"Error: {e}"
                self.telegram_bot.send_thread(self.admin_id, body)
                self.register_trading_msg(self.admin_id, "enter_func", "admin_msg", 'error', f'김프거래 진입과정에서 알 수 없는 에러 발생', body)
                register(self.monitor_bot_token, self.monitor_bot_url, self.admin_id, self.node, 'error', 'error occured in enter_func', str(e))
                return

    def exit_func(self, kimp_df, dollar, user_id, redis_uuid, mgnMode, symbol, exit_qty, user_upbit_access_key, user_upbit_secret_key, user_okx_access_key, user_okx_secret_key, user_okx_passphrase, exit_id_list=None):
        try:            
            okx_symbol = symbol + '-USDT-SWAP'
            upbit_symbol = 'KRW-' + symbol

            # Fetch position info from okx and upbit
            okx_return_dict = {}
            okx_position_information_thread = Thread(target=self.okx_adaptor.okx_position_information, args=(user_okx_access_key, user_okx_secret_key, user_okx_passphrase, okx_symbol, okx_return_dict), daemon=True)
            okx_position_information_thread.start()
            upbit_remaining_qty = self.upbit_adaptor.upbit_position_information(user_upbit_access_key, user_upbit_secret_key, symbol)
            okx_position_information_thread.join()
            if okx_return_dict['state'] == 'OK':
                okx_position_dict = okx_return_dict['res']
                okx_remaining_qty = okx_position_dict[mgnMode][0]['qty']
                if okx_remaining_qty < 0:
                    okx_remaining_pos = 'SHORT'
                else:
                    okx_remaining_pos = 'LONG'
            else:
                raise Exception(okx_return_dict)

            # If exit_qty == None, exit all remaining qty
            if exit_qty == None:
                body = f"EXIT수량이 명시되지 않아, 진입되어있는 모든 {symbol}을 정리합니다."
                self.telegram_bot.send_thread(user_id, body)
                self.register_trading_msg(user_id, "exit_func", "user_msg", 'normal', f'{symbol} 전량 정리 거래 실행', body)

                okx_return_dict = {}
                okx_exit_th = Thread(target=self.okx_adaptor.okx_market_exit, args=(user_okx_access_key, user_okx_secret_key, user_okx_passphrase, okx_symbol, okx_remaining_qty, mgnMode, okx_return_dict), daemon=True)
                okx_exit_th.start()
                upbit_exit_res = self.upbit_adaptor.upbit_market_exit(user_upbit_access_key, user_upbit_secret_key, upbit_symbol, str(upbit_remaining_qty))
                okx_exit_th.join()

                okx_exit_res = okx_return_dict['res']
                # OKX response validation process
                okx_error_switch = False
                if okx_return_dict['state'] == 'OK':
                    body = f"<b>거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}</b>({symbol})의 OKX LONG거래가 정상적으로 진행되었습니다."
                    self.telegram_bot.send_thread(user_id, body)
                    self.register_trading_msg(user_id, "exit_func", "user_msg", 'normal', f'거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}({symbol}) OKX LONG 거래 성공', body)
                else:
                    okx_error_switch = True
                    body = f"<b>거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}</b>({symbol})의 OKX LONG거래에 에러가 발생했습니다.\n"
                    body += f"ERROR: {okx_exit_res['sMsg']}"
                    self.telegram_bot.send_thread(user_id, body)
                    self.register_trading_msg(user_id, "exit_func", "user_msg", 'error', f'거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}({symbol}) OKX LONG 거래 실패', body)
                    register(self.monitor_bot_token, self.monitor_bot_url, user_id, self.node, 'error', f'거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}({symbol}) OKX LONG 거래 실패', body)

                # Upbit response validation process
                upbit_error_switch = False
                if upbit_exit_res['response']['status_code'] == 201:
                    body = f"<b>거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}</b>({symbol})의 업비트 매도거래가 정상적으로 진행되었습니다."
                    self.telegram_bot.send_thread(user_id, body)
                    self.register_trading_msg(user_id, "exit_func", "user_msg", 'normal', f'거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}({symbol}) 업비트 매도 거래 성공', body)
                else:
                    upbit_error_switch = True
                    body = f"<b>거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}</b>({symbol})의 업비트 매도거래에 에러가 발생했습니다.\n"
                    body += f"{upbit_exit_res['result']['error']['message']}"
                    self.telegram_bot.send_thread(user_id, body)
                    self.register_trading_msg(user_id, "exit_func", "user_msg", 'error', f'거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}({symbol}) 업비트 매도 거래 실패', body)
                    register(self.monitor_bot_token, self.monitor_bot_url, user_id, self.node, 'error', f'거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}({symbol}) 업비트 매도 거래 실패', body)

                if okx_error_switch or upbit_error_switch:
                    body = f"<b>경고! 거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}({symbol})의 탈출 시 오류가 발생하여 거래가 정상적으로 처리되지 않았습니다.</b>\n"
                    body += f"업비트 혹은 바이낸스에서 거래 상황을 확인 하시기 바랍니다.\n"
                    body += f"TRADE ERROR| 업비트: {upbit_error_switch}, OKX: {okx_error_switch}"
                    if okx_error_switch == True:
                        body += f"\nOKX 에러: {okx_exit_res['sMsg']}"
                    if upbit_error_switch == True:
                        body += f"\n업비트 에러: {upbit_exit_res['result']['error']['message']}"
                    self.telegram_bot.send_thread(user_id, body, 10, 5)
                    self.register_trading_msg(user_id, "exit_func", "user_msg", 'error', f'거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}({symbol}) 탈출 시 오류 발생', body)
                    register(self.monitor_bot_token, self.monitor_bot_url, user_id, self.node, 'error', f'거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}({symbol}) 탈출 시 오류 발생', body, send_counts=1)
                    self.register_trading_msg(self.admin_id, "exit_func", "admin_msg", 'error', f'유저 수동거래({symbol}) 탈출 시 정상처리 되지 않음.', body)
                    return
                try:
                    okx_orderId = okx_exit_res['ordId']
                except Exception as e:
                    okx_orderId = e
                try:
                    upbit_uuid = upbit_exit_res['result']['uuid']
                except Exception as e:
                    upbit_uuid = e

            else:
                upbit_exit_qty = exit_qty[0]
                okx_exit_qty = exit_qty[1]
                if upbit_exit_qty > upbit_remaining_qty or okx_exit_qty > abs(okx_remaining_qty):
                    body = f"OKX 선물보유량: {okx_symbol} {okx_remaining_pos} {abs(okx_remaining_qty)}개, 업비트 코인보유량: {symbol} {upbit_remaining_qty}개\n"
                    body += f"정리 수량({symbol} 업비트:{upbit_exit_qty}개, 바이낸스: {okx_exit_qty}개)이 현재 거래소 보유개수보다 많으므로 보유한 모든 코인을 정리합니다.\n"
                    self.telegram_bot.send_thread(user_id, body)
                    self.register_trading_msg(user_id, "exit_func", "user_msg", 'normal', f'보유한 모든 {symbol} 정리', body)
                    upbit_remaining_qty = self.upbit_adaptor.upbit_position_information(user_upbit_access_key, user_upbit_secret_key, symbol)
                    upbit_exit_qty = min(upbit_exit_qty, upbit_remaining_qty)
                    okx_exit_qty = min(okx_exit_qty, abs(okx_remaining_qty))

                okx_return_dict = {}
                okx_exit_th = Thread(target=self.okx_adaptor.okx_market_exit, args=(user_okx_access_key, user_okx_secret_key, user_okx_passphrase, okx_symbol, okx_exit_qty, mgnMode, okx_return_dict), daemon=True)
                okx_exit_th.start()
                upbit_exit_res = self.upbit_adaptor.upbit_market_exit(user_upbit_access_key, user_upbit_secret_key, upbit_symbol, str(upbit_exit_qty))
                okx_exit_th.join()

                okx_exit_res = okx_return_dict['res']
                # OKX response validation process
                okx_error_switch = False
                if okx_return_dict['state'] == 'OK':
                    body = f"<b>거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}</b>({symbol})의 OKX LONG거래가 정상적으로 진행되었습니다."
                    self.telegram_bot.send_thread(user_id, body, parse_mode='html')
                    self.register_trading_msg(user_id, "exit_func", "user_msg", 'normal', f'거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}({symbol}) OKX LONG 거래 성공', body)
                else:
                    okx_error_switch = True
                    body = f"<b>거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}</b>({symbol})의 OKX LONG거래에 에러가 발생했습니다.\n"
                    body += f"ERROR: {okx_exit_res['sMsg']}"
                    self.telegram_bot.send_thread(user_id, body, parse_mode='html')
                    self.register_trading_msg(user_id, "exit_func", "user_msg", 'error', f'거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}({symbol}) OKX LONG 거래 실패', body)
                    register(self.monitor_bot_token, self.monitor_bot_url, user_id, self.node, 'error', f'거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}({symbol}) OKX LONG 거래 실패', body)

                # Upbit response validation process
                upbit_error_switch = False
                if upbit_exit_res['response']['status_code'] == 201:
                    body = f"<b>거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}</b>({symbol})의 업비트 매도거래가 정상적으로 진행되었습니다."
                    self.telegram_bot.send_thread(user_id, body, parse_mode='html')
                    self.register_trading_msg(user_id, "exit_func", "user_msg", 'normal', f'거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}({symbol}) 업비트 매도 거래 성공', body)
                else:
                    upbit_error_switch = True
                    body = f"<b>거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}</b>({symbol})의 업비트 매도거래에 에러가 발생했습니다.\n"
                    body += f"{upbit_exit_res['result']['error']['message']}"
                    self.telegram_bot.send_thread(user_id, body, parse_mode='html')
                    self.register_trading_msg(user_id, "exit_func", "user_msg", 'error', f'거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}({symbol}) 업비트 매도 거래 실패', body)
                    register(self.monitor_bot_token, self.monitor_bot_url, user_id, self.node, 'error', f'거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}({symbol}) 업비트 매도 거래 실패', body)

                if okx_error_switch or upbit_error_switch:
                    body = f"경고! <b>거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}</b>({symbol})의 탈출 시 오류가 발생하여 거래가 정상적으로 처리되지 않았습니다.\n"
                    body += f"업비트 혹은 OKX에서 거래 상황을 확인 하시기 바랍니다.\n"
                    body += f"TRADE ERROR가 TRUE인 곳에서 에러가 발생하였습니다.\n"
                    body += f"TRADE ERROR| 업비트: {upbit_error_switch}, OKX: {okx_error_switch}"
                    if okx_error_switch == True:
                        body += f"\nOKX 에러: {okx_exit_res['sMsg']}"
                    if upbit_error_switch == True:
                        body += f"\n업비트 에러: {upbit_exit_res['result']['error']['message']}"
                    self.telegram_bot.send_thread(user_id, body, 10, 5, parse_mode='html')
                    self.register_trading_msg(user_id, "exit_func", "user_msg", 'error', f'거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}({symbol}) 탈출 시 오류 발생', body)
                    register(self.monitor_bot_token, self.monitor_bot_url, user_id, self.node, 'error', f'거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}({symbol}) 탈출 시 오류 발생', body, send_counts=1)

                    body = f"<b>거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}</b>({symbol})의 탈출 시 거래 정상처리 되지 않음.\n"
                    body += f"TRADE ERROR| 업비트: {upbit_error_switch}, OKX: {okx_error_switch}\n"
                    body += f"user_id: {user_id}, symbol: {symbol}"
                    if okx_error_switch == True:
                        body += f"\nOKX 에러: {okx_exit_res['sMsg']}"
                    if upbit_error_switch == True:
                        body += f"\n업비트 에러: {upbit_exit_res['result']['error']['message']}"
                    self.telegram_bot.send_thread(self.admin_id, body, parse_mode='html')
                    self.register_trading_msg(self.admin_id, "exit_func", "admin_msg", 'error', f'유저 거래({symbol}) 탈출 시 정상처리 되지 않음.', body)

                    user_safe_reverse = self.userinfo_df[self.userinfo_df['user_id']==user_id]['safe_reverse'].values[0]
                    if exit_qty != None and user_safe_reverse == 1:
                        self.revert_position('exit', user_id, redis_uuid, user_upbit_access_key, user_upbit_secret_key, user_okx_access_key, user_okx_secret_key, user_okx_passphrase, upbit_error_switch, okx_error_switch, upbit_exit_res, okx_exit_res, mgnMode)
                    return
                
                try:
                    okx_orderId = okx_exit_res['ordId']
                except Exception as e:
                    okx_orderId = e
                try:
                    upbit_uuid = upbit_exit_res['result']['uuid']
                except Exception as e:
                    upbit_uuid = e

            if exit_id_list != None:
                exit_id_list.append(upbit_uuid)
                exit_id_list.append(okx_orderId)

            # waiting for 5 sec before fetching order
            time.sleep(5)
            okx_waiting_count = 0
            while okx_waiting_count <= 10: # Waiting for fetching order info
                okx_order_info_dict = self.okx_adaptor.okx_order_info(user_okx_access_key, user_okx_secret_key, user_okx_passphrase, okx_symbol, okx_orderId)
                if okx_order_info_dict['sCode'] == '0':
                    break
                else:
                    time.sleep(2)
                    okx_waiting_count += 1
                    if okx_waiting_count == 10:
                        raise okx_order_info_dict['sMsg']

            upbit_order_info_dict = self.upbit_adaptor.upbit_order_info(user_upbit_access_key, user_upbit_secret_key, upbit_uuid)
            # read trades for calculating avg price
            
            res_df = pd.DataFrame(upbit_order_info_dict['result']['trades'])
            upbit_waiting_count = 0
            # Fetch until the response from Upbit is loaded
            while 'price' not in res_df.columns:
                if upbit_waiting_count == 10:
                    break
                body = f"exit_func 에서 upbit_order_info_dict fetch에러 발생!\n"
                body += f"None of [Index(['price', 'volume', 'funds'], dtype='object')] are in the [columns]\n"
                body += f"user_id: {user_id}, upbit_uuid: {upbit_uuid}"
                time.sleep(1)
                upbit_order_info_dict = self.upbit_adaptor.upbit_order_info(user_upbit_access_key, user_upbit_secret_key, upbit_uuid)
                res_df = pd.DataFrame(upbit_order_info_dict['result']['trades'])
                upbit_waiting_count += 1

            res_df.loc[:,['price', 'volume', 'funds']] = res_df[['price','volume','funds']].astype(float)
            upbit_avg_price = (res_df['volume']/res_df['volume'].sum() * res_df['price']).sum()

            okx_price = float(okx_order_info_dict['avgPx'])
            okx_price_krw = float(okx_price) * dollar
            okx_qty = okx_order_info_dict['executedQty']
            okx_side = okx_order_info_dict['side']
            
            upbit_price = upbit_avg_price
            upbit_qty = upbit_order_info_dict['result']['executed_volume']
            upbit_side = upbit_order_info_dict['result']['side']

            targeted_kimp = kimp_df[kimp_df['symbol']==symbol]['exit_kimp'].iloc[0]
            executed_kimp = (upbit_price - okx_price_krw) / okx_price_krw

            db_client = InitDBClient(**self.local_db_dict)
            sql = """INSERT INTO trade_history
            (
                user_id,
                datetime,
                timestamp,
                symbol,
                addcoin_redis_uuid,
                dollar,
                upbit_uuid,
                upbit_price,
                upbit_side,
                upbit_qty,
                okx_orderId,
                okx_mgnMode,
                okx_side,
                okx_price,
                okx_price_krw,
                okx_qty,
                targeted_kimp,
                executed_kimp
            )
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """
            datetime_now = datetime.datetime.now()
            val = (user_id, datetime_now, datetime_now.timestamp()*10000000,symbol, redis_uuid, float(dollar), upbit_uuid, float(upbit_price), upbit_side, float(upbit_qty), okx_orderId, mgnMode, okx_side, float(okx_price), float(okx_price_krw), float(okx_qty), float(targeted_kimp), float(executed_kimp))
            db_client.curr.execute(sql, val)
            db_client.conn.commit()
            db_client.conn.close()

            body = f"<b>거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}</b>\n"
            body += f"OKX {okx_symbol} 가격: {round(okx_price,2)}USDT, LONG수량: {okx_qty}개\n"
            body += f"OKX {okx_symbol} KRW가격: {krw(float(okx_price)*dollar)}원\n"
            body += f"업비트 {symbol} 가격: {krw(round(upbit_price))}원, 매도수량: {upbit_qty}개\n"
            body += f"현재 달러환율: {krw(dollar)}원\n"
            body += f"<b>타겟 kimp: {round(targeted_kimp*100,3)}%</b>, 타겟 USDT환산: {round((1+targeted_kimp)*dollar, 1)}원\n"
            body += f"<b>실행 kimp: {round(executed_kimp*100,3)}%</b>, 실행 USDT환산: {round((1+executed_kimp)*dollar, 1)}원"
            self.telegram_bot.send_thread(user_id, body, parse_mode='html')
            self.register_trading_msg(user_id, "exit_func", "user_msg", 'normal', f'거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)} 김프거래 탈출체결', body)
            return
        except Exception as e:  
            body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
            try:
                body += f"<b>거래ID: {redis_uuid}</b>\n"
            except:
                body += f"<b>거래ID: {None}</b>\n"
            try:
                body += f"코인심볼: {symbol}\n"
            except:
                body += f"코인심볼: {None}\n"
            try:
                body += f"업비트 매도수량: {upbit_qty}개\n"
            except:
                body += f"업비트 매도수량: {None}개\n"
            try:
                body += f"OKX LONG수량: {okx_qty}개\n"
            except:
                body += f"OKX LONG수량: {None}개\n"
            body += f"error: {e}"
            self.telegram_bot.send_thread(user_id, body)
            self.register_trading_msg(user_id, "exit_func", "user_msg", 'error', f'김프거래 탈출과정에서 에러 발생', body)
            register(self.monitor_bot_token, self.monitor_bot_url, user_id, self.node, 'error', f'김프거래 탈출과정에서 에러 발생', body)
            try:
                body = f"exit_func 에서 오류발생! user_id: {user_id}\n"
                try:
                    body += f"<b>거래ID: {redis_uuid}</b>\n"
                except:
                    body += f"<b>거래ID: {None}</b>\n"
                try:
                    body += f"코인심볼: {symbol}\n"
                except:
                    body += f"코인심볼: {None}\n"
                try:
                    body += f"업비트 매도수량: {upbit_qty}개\n"
                except:
                    body += f"업비트 매도수량: {None}개\n"
                try:
                    body += f"OKX LONG수량: {okx_qty}개\n"
                except:
                    body += f"OKX LONG수량: {None}개\n"
                body += f"okx_orderId: {okx_orderId}\n"
                body += f"upbit_uuid: {upbit_uuid}\n"
                body += f"okx_error_switch: {okx_error_switch}\n"
                body += f"upbit_error_switch: {upbit_error_switch}\n"
                body += f"Error: {e}"
                self.telegram_bot.send_thread(self.admin_id, body)
                self.register_trading_msg(self.admin_id, "exit_func", "admin_msg", 'error', f'김프거래 탈출과정에서 알 수 없는 에러 발생', body)
                register(self.monitor_bot_token, self.monitor_bot_url, self.admin_id, self.node, 'error', 'error occured in exit_func', str(e))
                return
            except:
                body = f"exit_func 에서 오류발생! user_id: {user_id}\n"
                try:
                    body += f"<b>거래ID: {redis_uuid}</b>\n"
                except:
                    body += f"<b>거래ID: {None}</b>\n"
                try:
                    body += f"코인심볼: {symbol}\n"
                except:
                    body += f"코인심볼: {None}\n"
                try:
                    body += f"업비트 매도수량: {upbit_qty}개\n"
                except:
                    body += f"업비트 매도수량: {None}개\n"
                try:
                    body += f"OKX LONG수량: {okx_qty}개\n"
                except:
                    body += f"OKX LONG수량: {None}개\n"
                body += f"okx_return_dict: {okx_return_dict}\n"
                body += f"upbit_exit_res: {upbit_exit_res}\n"
                body += f"okx_error_switch: {okx_error_switch}\n"
                body += f"upbit_error_switch: {upbit_error_switch}\n"
                body += f"Error: {e}"
                self.telegram_bot.send_thread(self.admin_id, body)
                self.register_trading_msg(self.admin_id, "exit_func", "admin_msg", 'error', f'김프거래 탈출과정에서 알 수 없는 에러 발생', body)
                register(self.monitor_bot_token, self.monitor_bot_url, self.admin_id, self.node, 'error', 'error occured in exit_func', str(e))
                return
    
    def exec_pnl(self, merged_df, user_id, redis_uuid, upbit_exit_uuid, dollar, upbit_fee_rate=0.0005, okx_fee_rate=0.0005):
        try:
            dollar = float(dollar)
            # Load trade_history
            db_client = InitDBClient(**self.local_db_dict)
            db_client.curr.execute("""SELECT * FROM trade_history""")
            trade_history_df = pd.DataFrame(db_client.curr.fetchall())
            db_client.conn.close()
            if len(trade_history_df) == 0:
                db_client.conn.ping()
                col_names = []
                db_client.curr.execute("""DESCRIBE trade_history""")
                fetched_dict = db_client.curr.fetchall()
                for each_field in fetched_dict:
                    col_names.append(each_field['Field'])
                trade_history_df = pd.DataFrame(columns=col_names)
                db_client.conn.close()
            else:
                trade_history_df = trade_history_df.where(trade_history_df.notnull(), None)

            # Avg weighted kimp
            # weighted avg of kimp from BTC, XRP, EOS, XLM
            filtered_df = merged_df[merged_df['symbol'].isin(['BTC','XRP','EOS','XLM'])]
            weighted_avg_kimp = float((filtered_df['tp_kimp']*(filtered_df['acc_trade_price_24h']/filtered_df['acc_trade_price_24h'].sum())).sum())

            one_addcoin_df = self.addcoin_df[self.addcoin_df['redis_uuid']==redis_uuid]
            symbol = one_addcoin_df['symbol'].values[0].replace('USDT', '')
            upbit_enter_uuid = one_addcoin_df['enter_upbit_uuid'].values[0]
            # ENTER INFO
            enter_trade_history_df = trade_history_df[trade_history_df['upbit_uuid']==upbit_enter_uuid]
            enter_dollar = float(enter_trade_history_df['dollar'].values[0])
            enter_executed_kimp = enter_trade_history_df['executed_kimp'].values[0]
            if enter_executed_kimp is not None:
                enter_executed_kimp = float(enter_executed_kimp)
            enter_executed_usdt = enter_trade_history_df['executed_usdt'].values[0]
            if enter_executed_usdt is not None:
                enter_executed_usdt = float(enter_executed_usdt)
            okx_enter_usdt = float((enter_trade_history_df['okx_qty'] * enter_trade_history_df['okx_price']).values[0])
            upbit_enter_krw = float((enter_trade_history_df['upbit_qty'] * enter_trade_history_df['upbit_price']).values[0])
            # EXIT INFO
            exit_trade_history_df = trade_history_df[trade_history_df['upbit_uuid']==upbit_exit_uuid]
            exit_dollar = float(exit_trade_history_df['dollar'].values[0])
            exit_executed_kimp = exit_trade_history_df['executed_kimp'].values[0]
            if exit_executed_kimp is not None:
                exit_executed_kimp = float(exit_executed_kimp)
            exit_executed_usdt = exit_trade_history_df['executed_usdt'].values[0]
            if exit_executed_usdt is not None:
                exit_executed_usdt = float(exit_executed_usdt)
            okx_exit_usdt = float((exit_trade_history_df['okx_qty'] * exit_trade_history_df['okx_price']).values[0])
            upbit_exit_krw = float((exit_trade_history_df['upbit_qty'] * exit_trade_history_df['upbit_price']).values[0])

            upbit_enter_fee = upbit_enter_krw * upbit_fee_rate
            upbit_exit_fee = upbit_exit_krw * upbit_fee_rate
            upbit_total_fee = upbit_enter_fee + upbit_exit_fee
            okx_enter_fee = okx_enter_usdt * okx_fee_rate
            okx_exit_fee = okx_exit_usdt * okx_fee_rate
            okx_total_fee = okx_enter_fee + okx_exit_fee

            kimp_gap = exit_executed_kimp - enter_executed_kimp
            upbit_pnl = upbit_exit_krw - upbit_enter_krw
            okx_pnl = -(okx_exit_usdt - okx_enter_usdt)
            total_pnl_krw = upbit_pnl + okx_pnl*dollar
            total_pnl_krw_after_kimp = upbit_pnl + okx_pnl*dollar*(1+weighted_avg_kimp)

            body = f"<b>김프거래(거래ID: {redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}) 탈출 손익</b>\n\n"
            body += f"업비트 진입 수수료: <b>{krw(round(upbit_enter_fee))}</b>원\n"
            body += f"업비트 탈출 수수료: <b>{krw(round(upbit_exit_fee))}</b>원\n"
            body += f"업비트 총 수수료: <b>{krw(round(upbit_total_fee))}</b>원\n"
            body += f"OKX 진입 수수료: <b>{round(okx_enter_fee,3)}</b>USD\n"
            body += f"OKX 탈출 수수료: <b>{round(okx_exit_fee,3)}</b>USD\n"
            body += f"OKX 총 수수료: <b>{round(okx_total_fee,3)}</b>USD\n"
            body += f"환율 적용 후 양측 총 수수료: <b>{krw(round(upbit_total_fee+okx_total_fee*dollar))}</b>원\n"
            body += f"김프,환율 적용 후 양측 총 수수료: <b>{krw(round(upbit_total_fee+okx_total_fee*dollar*(1+weighted_avg_kimp)))}</b>원\n\n"
            body += f"업비트 손익: <b>{krw(round(upbit_pnl))}</b>원\n"
            body += f"OKX 손익: <b>{round(okx_pnl,3)}</b>USD\n"
            body += f"환율 적용 후 합산 손익: <b>{krw(round(total_pnl_krw))}</b>원\n"
            body += f"김프,환율 적용 후 합산 손익: <b>{krw(round(total_pnl_krw_after_kimp))}</b>원\n\n"
            body += f"수수료,환율 적용 후 합산 손익: <b>{krw(round(upbit_pnl-upbit_total_fee+(okx_pnl-okx_total_fee)*dollar))}</b>원\n"
            body += f"수수료,김프,환율 적용 후 합산 손익: <b>{krw(round(upbit_pnl-upbit_total_fee+(okx_pnl-okx_total_fee)*dollar*(1+weighted_avg_kimp)))}</b>원"
            self.telegram_bot.send_thread(user_id, body, parse_mode='html')
            self.register_trading_msg(user_id, "exec_pnl", "user_msg", 'normal', f'김프거래 탈출 손익', body)

            # INSERT PNL results into the pnl_history table
            db_client = InitDBClient(**self.local_db_dict)
            sql = """
            INSERT INTO pnl_history(
                user_id,
                timestamp,
                redis_uuid,
                symbol,
                dollar_enter,
                dollar_exit,
                kimp_enter,
                kimp_exit,
                usdt_enter,
                usdt_exit,
                upbit_enter_value,
                upbit_enter_fee,
                upbit_exit_value,
                upbit_exit_fee,
                upbit_pnl,
                okx_enter_value,
                okx_enter_fee,
                okx_enter_value_krw,
                okx_exit_value,
                okx_exit_fee,
                okx_exit_value_krw,
                okx_pnl,
                okx_pnl_krw,
                okx_pnl_after_kimp,
                total_pnl,
                total_pnl_after_kimp,
                remark
            ) VALUES(%s, %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """
            val = [
                user_id,
                datetime.datetime.now().timestamp()*10000000,
                redis_uuid,
                symbol,
                enter_dollar,
                exit_dollar,
                enter_executed_kimp,
                exit_executed_kimp,
                enter_executed_usdt,
                exit_executed_usdt,
                upbit_enter_krw,
                upbit_enter_fee,
                upbit_exit_krw,
                upbit_exit_fee,
                upbit_pnl-upbit_total_fee,
                okx_enter_usdt,
                okx_enter_fee,
                okx_enter_usdt * enter_dollar,
                okx_exit_usdt,
                okx_exit_fee,
                okx_exit_usdt * exit_dollar,
                okx_pnl-okx_total_fee,
                okx_pnl * dollar,
                okx_pnl * dollar * (1+weighted_avg_kimp),
                upbit_pnl-upbit_total_fee+(okx_pnl-okx_total_fee)*dollar,
                upbit_pnl-upbit_total_fee+(okx_pnl-okx_total_fee)*dollar*(1+weighted_avg_kimp),
                "trading fee has already been applied to pnl"
            ]
            db_client.curr.execute(sql, val)
            db_client.conn.commit()
            db_client.conn.close()
            return
        except Exception as e:
            self.snatcher_logger.error(f"exec_pnl|{traceback.format_exc()}")
            body = f"Error occured in exec_pnl func\n"
            body += f"Error: {e}"
            self.telegram_bot.send_thread(self.admin_id, body)
            self.register_trading_msg(self.admin_id, "exec_pnl", "admin_msg", 'error', f'김프거래 탈출 손익(exec_pnl) 에러발생', body)
            register(self.monitor_bot_token, self.monitor_bot_url, self.admin_id, self.node, 'error', 'Error occured in exec_pnl func', str(e))
            return

    def deactivate_addcoin(self, redis_uuid):
        db_client = InitDBClient(**self.local_db_dict)
        db_client.curr.execute("""UPDATE addcoin SET last_updated_timestamp=%s, auto_trade_switch=%s WHERE redis_uuid=%s""", (datetime.datetime.now().timestamp()*10000000, 2, redis_uuid))
        db_client.conn.commit()
        db_client.conn.close()
        return

    def deactivate_addcoin_addcir(self, user_id, redis_uuid, remark):
        try:
            db_client = InitDBClient(**self.local_db_dict)
            db_client.curr.execute("""SELECT * FROM addcir""")
            addcir_df = pd.DataFrame(db_client.curr.fetchall())
            if len(addcir_df) == 0:
                return
            addcir_df = addcir_df.where(addcir_df.notnull(), None)
            if redis_uuid == 'ALL': # 로직 변경으로 Deprecated 됨
                db_client.curr.execute("""UPDATE addcir SET cir_trade_switch=%s, remark=%s WHERE user_id=%s""", (0, remark, user_id))
                db_client.conn.commit()
                body = f"등록된 모든 코인의 /addcir 반복거래 설정이 비활성화 되었습니다."
                self.telegram_bot.send_thread(user_id, body)
                self.register_trading_msg(user_id, "deactivate_addcoin_addcir", "user_msg", 'normal', f'등록된 모든 /addcir 비활성화', body)
            else:
                # Fetch uuid for addcoin
                db_client.curr.execute("""SELECT addcoin_uuid FROM addcoin WHERE redis_uuid=%s""", redis_uuid)
                addcoin_uuid = db_client.curr.fetchall()[0]['addcoin_uuid']
                if len(addcir_df[(addcir_df['addcir_uuid']==addcoin_uuid)&(addcir_df['cir_trade_switch']==1)]) == 1:
                    addcir_redis_uuid = addcir_df[addcir_df['addcir_uuid']==addcoin_uuid]['redis_uuid'].values[0]
                    addcir_symbol = addcir_df[addcir_df['addcir_uuid']==addcoin_uuid]['symbol'].values[0]
                    db_client.curr.execute("""UPDATE addcir SET cir_trade_switch=%s, remark=%s WHERE redis_uuid=%s""", (0, remark, addcir_redis_uuid))
                    db_client.conn.commit()
                    body = f"등록된 {addcir_symbol}(반복ID: {addcir_redis_uuid})의 /addcir 반복거래 설정이 비활성화 되었습니다."
                    self.telegram_bot.send_thread(user_id, body)
                    self.register_trading_msg(user_id, "deactivate_addcoin_addcir", "user_msg", 'normal', f'등록된 /addcir 비활성화', body)
            db_client.conn.close()
            return
        except Exception as e:
            self.snatcher_logger.error(f"deactivate_addcoin_addcir|{traceback.format_exc()}")
            body = f"Error occured in deactivate_addcoin_addcir func\n"
            body += f"Error: {e}"
            self.telegram_bot.send_thread(self.admin_id, body)
            self.register_trading_msg(self.admin_id, "deactivate_addcoin_addcir", "admin_msg", 'error', f'deactivate_addcoin_addcir 에서 에러 발생', body)
            register(self.monitor_bot_token, self.monitor_bot_url, self.admin_id, self.node, 'error', 'Error occured in deactivate_addcoin_addcir func', str(e))
            return
    # Not finished
    def exec_cgh(self, user_id, redis_uuid):
        try:
            db_client = InitDBClient(**self.local_db_dict)
            db_client.curr.execute("""SELECT * FROM addcoin WHERE redis_uuid=%s""", redis_uuid)
            user_addcoin_df = pd.DataFrame(db_client.curr.fetchall())
            user_enter_upbit_uuid = user_addcoin_df['enter_upbit_uuid'].values[0]
            db_client.curr.execute("""SELECT * FROM trade_history WHERE upbit_uuid=%s""", user_enter_upbit_uuid)
            user_trade_history_df = pd.DataFrame(db_client.curr.fetchall())
            db_client.conn.close()
            user_symbol = user_addcoin_df['symbol'].values[0]

            if 'USDT' in user_symbol:
                usdt_flag = True
                user_targeted_value = user_trade_history_df['dollar'].values[0]*(1+user_trade_history_df['targeted_kimp'].values[0])
                user_executed_value = user_trade_history_df['dollar'].values[0]*(1+user_trade_history_df['executed_kimp'].values[0])
            else:
                usdt_flag = False
                user_targeted_value = user_trade_history_df['targeted_kimp'].values[0]*100
                user_executed_value = user_trade_history_df['executed_kimp'].values[0]*100
                
            user_low = user_addcoin_df['low'].values[0]
            user_high = user_addcoin_df['high'].values[0]
            user_low_high_gap = user_high - user_low
            new_high_value = float(round(user_executed_value + user_low_high_gap, 3))

            # Change low value according to the executed kimp
            db_client = InitDBClient(**self.local_db_dict)
            switch = 0
            auto_trade_switch = -1
            timestamp_now = datetime.datetime.now().timestamp()*10000000
            db_client.curr.execute("""UPDATE addcoin SET last_updated_timestamp=%s, switch=%s, auto_trade_switch=%s, low=%s WHERE redis_uuid=%s""", (timestamp_now, switch, auto_trade_switch, float(user_executed_value), redis_uuid))
            db_client.conn.commit()
            db_client.conn.close()

            if (user_targeted_value < user_executed_value) and (new_high_value > user_high):
                if usdt_flag == True:
                    body = f"실행 테더환산가가 타겟 테더환산가보다 높으므로 괴리값을 반영하여, 탈출 High 값을 자동 재조정 합니다.\n"
                else:
                    body = f"실행김프가 타겟김프보다 높으므로 괴리값을 반영하여, 탈출 High 값을 자동 재조정 합니다.\n"
                

                # # Change high value using the cgh function
                # class Object(object):
                #     pass
                # update = Object()
                # update.effective_chat = Object()
                # update.effective_chat.id = user_id
                # context = Object()
                # context.bot = self.telegram_bot.bot
                # context.args = [redis_uuid, ',', str(round(new_high_value,3))]
                # cgh(update, context)

                # update database
                db_client = InitDBClient(**self.local_db_dict)
                db_client.curr.execute("""SELECT high FROM addcoin WHERE redis_uuid=%s""", redis_uuid)
                before_high = db_client.curr.fetchall()[0]['high']
                db_client.curr.execute("""UPDATE addcoin SET last_updated_timestamp=%s, high=%s WHERE redis_uuid=%s""", (datetime.datetime.now().timestamp()*10000000, new_high_value, redis_uuid))
                db_client.conn.commit()
                
                # load addcoin from database
                db_client.curr.execute("""SELECT * FROM addcoin""")
                fetched_addcoin_df = pd.DataFrame(db_client.curr.fetchall())
                fetched_addcoin_df = fetched_addcoin_df.where(fetched_addcoin_df.notnull(), None)
                db_client.conn.close()

                body += f"거래ID:{redis_uuid_to_display_id(fetched_addcoin_df, redis_uuid)}({user_symbol.replace('USDT','')})의 탈출김프 혹은 탈출USDT환산가가\n"
                body += f"{before_high}에서 <b>{new_high_value}</b>로 변경되었습니다."
                self.telegram_bot.send_thread(user_id, body, parse_mode='html')
                self.register_trading_msg(user_id, "exec_cgh", "user_msg", 'normal', f'탈출김프 혹은 탈출USDT 환산가 변경', body)
                return
        except Exception as e:
            self.snatcher_logger.error(f"exec_cgh| user_id: {user_id}, addcoin redis_uuid: {redis_uuid}, {traceback.format_exc()}")
            body = f"Error occured in exec_cgh func\n"
            body += f"Error: {e}"
            self.telegram_bot.send_thread(self.admin_id, body)
            self.register_trading_msg(self.admin_id, "exec_cgh", "admin_msg", 'error', f'exec_cgh 에서 에러 발생', body)
            register(self.monitor_bot_token, self.monitor_bot_url, self.admin_id, self.node, 'error', 'Error occured in exec_cgh func', str(e))

    def cancel_addcoin(self, user_id, user_upbit_access_key, user_upbit_secret_key, user_okx_access_key, user_okx_secret_key, user_okx_passphrase):
        try:
            db_client = InitDBClient(**self.local_db_dict)
            db_client.curr.execute("""SELECT * FROM addcoin WHERE user_id=%s""", user_id)
            user_addcoin_df = pd.DataFrame(db_client.curr.fetchall())
            db_client.conn.close()
            if len(user_addcoin_df) == 0:
                return
            
            user_leverage = self.userinfo_df[self.userinfo_df['user_id']==user_id]['okx_leverage'].values[0]
            upbit_balance_df = self.upbit_adaptor.get_upbit_spot_balance(user_upbit_access_key, user_upbit_secret_key)
            upbit_krw_balance = upbit_balance_df[upbit_balance_df['currency']=='KRW']['balance'].iloc[0]
            okx_usdm_balance_df = self.okx_adaptor.get_okx_trade_balance(user_okx_access_key, user_okx_secret_key, user_okx_passphrase)
            okx_usdt_balance = okx_usdm_balance_df[okx_usdm_balance_df['ccy']=='USDT']['availBal'].iloc[0]
            okx_usdt_balance_krw = okx_usdt_balance * self.get_dollar_dict()['price'] # 잔고 계산시 김프적용은 어떻게?
            okx_usdt_balance_krw_leverage = okx_usdt_balance_krw * user_leverage

            for row_tup in user_addcoin_df.iterrows():
                row = row_tup[1]
                redis_uuid = row['redis_uuid']
                symbol = row['symbol']
                auto_trade_switch = row['auto_trade_switch']
                auto_trade_capital = row['auto_trade_capital']
                if auto_trade_capital == None or auto_trade_switch != 0:
                    continue
                if auto_trade_capital >= min(upbit_krw_balance, okx_usdt_balance_krw_leverage):
                    # cancel addcoin
                    body = f"잔고가 부족하여, 거래ID: {redis_uuid}({symbol})의 <b>/addcoin 거래설정을 삭제</b>합니다.\n"
                    self.telegram_bot.send_thread(user_id, body, parse_mode='html')
                    self.register_trading_msg(user_id, "cancel_addcoin", "user_msg", 'normal', f'잔고부족으로 인한 자동거래(/addcoin)설정 삭제', body)
                    db_client.conn.ping()
                    db_client.curr.execute("""DELETE FROM addcoin WHERE redis_uuid=%s""", redis_uuid)
                    self.deactivate_addcoin_addcir(user_id, redis_uuid, '/addcoin 김프거래 설정삭제(잔고 부족)')
                    db_client.conn.commit()
                    db_client.conn.close()
        except Exception as e:
            self.snatcher_logger.error(f"cancel_addcoin|{traceback.format_exc()}")
            body = "cancel_addcoin 에서 에러발생\n"
            body += f"user_id: {user_id}\n"
            body += f"Error: {e}"
            self.telegram_bot.send_thread(self.admin_id, body)
            self.register_trading_msg(self.admin_id, "cancel_addcoin", "admin_msg", 'error', f'cancel_addcoin 에서 에러 발생', body)
            register(self.monitor_bot_token, self.monitor_bot_url, self.admin_id, self.node, 'error', 'Error occured in cancel_addcoin func', str(e))

    def revert_position(self, side, user_id, redis_uuid, user_upbit_access_key, user_upbit_secret_key, user_okx_access_key, user_okx_secret_key, user_okx_passphrase, upbit_error_switch, okx_error_switch, upbit_res, okx_res, mgnMode):
        # If both are error, skip reverting
        if upbit_error_switch == True and okx_error_switch == True:
            return
        time.sleep(0.5)

        upbit_symbol = upbit_res['result']['market']
        okx_symbol = upbit_symbol.split('-')[1]+'-USDT-SWAP'

        # side -> enter, exit
        if side == 'enter':
            if upbit_error_switch == False:
                upbit_uuid = upbit_res['result']['uuid']
                upbit_order_info_dict = self.upbit_adaptor.upbit_order_info(user_upbit_access_key, user_upbit_secret_key, upbit_uuid)
                upbit_waiting_count = 0
                while float(upbit_order_info_dict['result']['executed_volume']) == 0:
                    if upbit_waiting_count == 10:
                        break
                    # body = f"enter_func 에서 float(upbit_order_info_dict['result']['executed_volume']) == 0 발생!\n"
                    # body += f"user_id: {user_id}, upbit_uuid: {upbit_uuid}"
                    # bot.send_message(chat_id=admin_id, text=body)
                    time.sleep(1)
                    upbit_order_info_dict = self.upbit_adaptor.upbit_order_info(user_upbit_access_key, user_upbit_secret_key, upbit_uuid)
                    upbit_waiting_count += 1
                upbit_enter_price = float(upbit_order_info_dict['result']['price']) / float(upbit_order_info_dict['result']['executed_volume'])
                upbit_qty = upbit_order_info_dict['result']['executed_volume']
                upbit_revert_res = self.upbit_adaptor.upbit_market_exit(user_upbit_access_key, user_upbit_secret_key, upbit_symbol, str(upbit_qty))
                if upbit_revert_res['response']['status_code'] == 201:
                    body = f"거래ID:{redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}의 김프거래 진입 시 역매매 안전장치가 작동하여, 업비트 매수포지션이 즉시 매도되었습니다.\n"
                    body += f"<b>역매매 내역</b>\n"
                    body += f"업비트 심볼: {upbit_symbol}\n"
                    body += f"매도 개수: {upbit_qty}개"
                    self.telegram_bot.send_thread(user_id, body, parse_mode='html')
                    self.register_trading_msg(user_id, "revert_position", "user_msg", 'normal', f'OKX 김프거래 진입 실패로 인한 업비트 역매매 실행', body)
                else:
                    body = f"거래ID:{redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}의 김프거래 진입 시, 업비트 역매매 과정에서 에러가 발생했습니다.\n"
                    body += f"Error: {upbit_revert_res['result']['error']['message']}"
                    self.snatcher_logger.error(f"revert_position|{body}")
                    self.telegram_bot.send_thread(user_id, body)
                    self.register_trading_msg(user_id, "revert_position", "user_msg", 'error', f'김프거래 진입 시, 업비트 역매매 안전장치 에러 발생', body)
                    register(self.monitor_bot_token, self.monitor_bot_url, user_id, self.node, 'error', f'김프거래 진입 시, 업비트 역매매 안전장치 에러 발생', body)
                    self.telegram_bot.send_thread(self.admin_id, body)
                    self.register_trading_msg(self.admin_id, "revert_position", "admin_msg", 'error', f'유저({user_id}) 김프거래 진입 시, 업비트 역매매 과정에서 에러 발생', body)
                    register(self.monitor_bot_token, self.monitor_bot_url, self.admin_id, self.node, 'error', f'유저({user_id}) 김프거래 진입 시, 업비트 역매매 과정에서 에러가 발생했습니다.', f"Error: {upbit_revert_res['result']['error']['message']}")
                return
            elif okx_error_switch == False:
                okx_orderId = okx_res['ordId']
                time.sleep(1)
                okx_order_info_dict = self.okx_adaptor.okx_order_info(user_okx_access_key, user_okx_secret_key, user_okx_passphrase, okx_symbol, okx_orderId)
                okx_qty = float(okx_order_info_dict['executedQty'])
                okx_revert_res = self.okx_adaptor.okx_market_exit(user_okx_access_key, user_okx_secret_key, okx_symbol, okx_qty, mgnMode)
                if okx_revert_res['sCode'] == "0":
                    body = f"거래ID:{redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}의 김프거래 진입 시 역매매 안전장치가 작동하여, OKX 숏포지션이 즉시 정리(롱) 되었습니다.\n"
                    body += f"<b>역매매 내역</b>\n"
                    body += f"OKX 심볼: {okx_symbol}\n"
                    body += f"롱 개수: {okx_qty}개"
                    self.telegram_bot.send_thread(user_id, body, parse_mode='html')
                    self.register_trading_msg(user_id, "revert_position", "user_msg", 'normal', f'업비트 김프거래 진입 실패로 인한 OKX 역매매 실행', body)
                else:
                    body = f"거래ID:{redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}의 김프거래 진입 시, OKX 역매매 안전정치에서 에러가 발생했습니다.\n"
                    body += f"Error: {e}"
                    self.snatcher_logger.error(f"revert_position|{body}, {traceback.format_exc()}")
                    self.telegram_bot.send_thread(user_id, body)
                    self.register_trading_msg(user_id, "revert_position", "user_msg", 'error', f'김프거래 진입 시, OKX 역매매 안전장치 에러 발생', body)
                    register(self.monitor_bot_token, self.monitor_bot_url, user_id, self.node, 'error', f'김프거래 진입 시, OKX 역매매 안전장치 에러 발생', body)
                    self.telegram_bot.send_thread(self.admin_id, body)
                    self.register_trading_msg(self.admin_id, "revert_position", "admin_msg", 'error', f'유저({user_id}) 김프거래 진입 시, OKX 역매매 과정에서 에러 발생', body)
                    register(self.monitor_bot_token, self.monitor_bot_url, self.admin_id, self.node, 'error', f'유저({user_id}) 김프거래 진입 시, OKX 역매매 안전정치에서 에러가 발생했습니다.', f"Error: {traceback.format_exc()}")
                return

        if side == 'exit':
            # 바이낸스는 청산이 날 경우, 정상적 임에도 binance_error_switch True 가 나는 경우가 있음.
            # 그 외에 바이낸스는 오류가 거의 없으므로 업비트가 오류나는 경우만 가정할 것.   --> Binance internal error 때문에 수정 중
            if okx_error_switch == False:
                okx_orderId = okx_res['ordId']
                time.sleep(1)
                okx_order_info_dict = self.okx_adaptor.okx_order_info(user_okx_access_key, user_okx_secret_key, user_okx_passphrase, okx_symbol, okx_orderId)
                okx_qty = float(okx_order_info_dict['executedQty'])
                okx_revert_res = self.okx_adaptor.okx_market_enter(user_okx_access_key, user_okx_secret_key, user_okx_passphrase, okx_symbol, okx_qty, mgnMode)
                if okx_revert_res['sCode'] == "0":
                    body = f"거래ID:{redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}의 김프거래 탈출 시 역매매 안전장치가 작동하여, OKX 숏포지션이 다시 복구되었습니다.\n"
                    body += f"<b>역매매 내역</b>"
                    body += f"OKX 심볼: {okx_symbol}\n"
                    body += f"숏 개수: {okx_qty}개"
                    self.telegram_bot.send_thread(user_id, body, parse_mode='html')
                    self.register_trading_msg(user_id, "revert_position", "user_msg", 'normal', f'업비트 김프거래 탈출 실패로 인한 OKX 역매매 실행', body)
                else:
                    body = f"거래ID:{redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}의 김프거래 탈출 시, OKX 역매매 안전정치에서 에러가 발생했습니다.\n"
                    body += f"Error: {e}"
                    self.snatcher_logger.error(f"revert_position|{body}, {traceback.format_exc()}")
                    self.telegram_bot.send_thread(user_id, body)
                    self.register_trading_msg(user_id, "revert_position", "user_msg", 'error', f'김프거래 탈출 시, OKX 역매매 과정에서 에러 발생', body)
                    register(self.monitor_bot_token, self.monitor_bot_url, user_id, self.node, 'error', f'김프거래 탈출 시, OKX 역매매 과정에서 에러 발생', body)
                    self.telegram_bot.send_thread(self.admin_id, body)
                    self.register_trading_msg(self.admin_id, "revert_position", "admin_msg", 'error', f'유저({user_id}) 김프거래 탈출 시, OKX 역매매 과정에서 에러 발생', body)
                    register(self.monitor_bot_token, self.monitor_bot_url, self.admin_id, self.node, 'error', f'유저({user_id}) 김프거래 탈출 시, OKX 역매매 안전정치에서 에러가 발생했습니다.', f"Error: {traceback.format_exc()}")
                return
            elif upbit_error_switch == False and okx_res['sCode'] != '0':
                # 업비트 역매매 하기 => 업비트에서 팔아버린 걸 다시 매수
                try: # Temporary Error check process
                    upbit_uuid = upbit_res['result']['uuid']
                    upbit_order_info_dict = self.upbit_adaptor.upbit_order_info(user_upbit_access_key, user_upbit_secret_key, upbit_uuid)
                    upbit_waiting_count = 0
                    while float(upbit_order_info_dict['result']['executed_volume']) == 0:
                        if upbit_waiting_count == 10:
                            break
                        # body = f"enter_func 에서 float(upbit_order_info_dict['result']['executed_volume']) == 0 발생!\n"
                        # body += f"user_id: {user_id}, upbit_uuid: {upbit_uuid}"
                        # bot.send_message(chat_id=admin_id, text=body)
                        time.sleep(1)
                        upbit_order_info_dict = self.upbit_adaptor.upbit_order_info(user_upbit_access_key, user_upbit_secret_key, upbit_uuid)
                        upbit_waiting_count += 1

                    upbit_exit_krw = int(sum([float(x['funds']) for x in upbit_order_info_dict['result']['trades']]))
                    upbit_revert_res = self.upbit_adaptor.upbit_market_enter(user_upbit_access_key, user_upbit_secret_key, upbit_symbol, str(upbit_exit_krw))
                    if upbit_revert_res['response']['status_code'] == 201:
                        body = f"거래ID:{redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}의 김프거래 탈출 시 역매매 안전장치가 작동하여, 업비트 매도포지션이 즉시 재매수되었습니다.\n"
                        body += f"<b>역매매 내역</b>\n"
                        body += f"업비트 심볼: {upbit_symbol}\n"
                        body += f"업비트 매수 금액: {upbit_exit_krw}원\n"
                        self.telegram_bot.send_thread(user_id, body, parse_mode='html')
                        self.register_trading_msg(user_id, "revert_position", "user_msg", 'normal', f'OKX 김프거래 탈출 실패로 인한 업비트 역매매 실행', body)
                    else:
                        body = f"거래ID:{redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}의 김프거래 탈출 시, 업비트 역매매 과정에서 에러가 발생했습니다.\n"
                        body += f"Error: {upbit_revert_res['result']['error']['message']}"
                        self.snatcher_logger.error(f"revert_position|{body}")
                        self.telegram_bot.send_thread(user_id, body)
                        self.register_trading_msg(user_id, "revert_position", "user_msg", 'error', f'김프거래 탈출 시, 업비트 역매매 안전장치 에러 발생', body)
                        register(self.monitor_bot_token, self.monitor_bot_url, user_id, self.node, 'error', f'김프거래 탈출 시, 업비트 역매매 안전장치 에러 발생', body)
                        self.telegram_bot.send_thread(self.admin_id, body)
                        self.register_trading_msg(self.admin_id, "revert_position", "admin_msg", 'error', f'유저({user_id}) 김프거래 탈출 시, 업비트 역매매 과정에서 에러 발생', body)
                        register(self.monitor_bot_token, self.monitor_bot_url, self.admin_id, self.node, 'error', f'유저({user_id}) 김프거래 탈출 시, 업비트 역매매 과정에서 에러가 발생했습니다.', f"Error: {upbit_revert_res['result']['error']['message']}")
                    return
                except Exception as e:
                    self.snatcher_logger.error(f"revert_position|{body}, {traceback.format_exc()}")
                    register(self.monitor_bot_token, self.monitor_bot_url, self.admin_id, self.node, 'error', f'유저({user_id}) 김프거래 탈출 시, 업비트 역매매 안전정치에서 에러가 발생했습니다.', f"Error: {traceback.format_exc()}")
