from etc.db_handler.postgres_client import InitDBClient as InitPostgresDBClient
from loggers.logger import KimpBotLogger
from threading import Thread
from multiprocessing import Process, Manager
from threading import Thread
from psycopg2 import extras
from etc.msg_api import MsgApi
import time

class InitTrigger:
    def __init__(self, admin_id, node, server_check_status_list, get_premium_df, enabled_markets, register_monitor_msg, remote_redis_client, db_dict, mongo_client, postgres_client, logging_dir):
        self.admin_id = admin_id
        self.node = node
        self.msg_api = MsgApi(prod=False)
        self.server_check_status_list = server_check_status_list
        self.get_premium_df = get_premium_df
        self.enabled_markets = enabled_markets
        self.register_monitor_msg = register_monitor_msg
        self.remote_redis_client = remote_redis_client
        self.db_dict = db_dict
        self.mongo_client = mongo_client
        self.postgres_client = postgres_client
        self.logging_dir = logging_dir
        self.logger = KimpBotLogger(logging_dir, "trigger").logger
        self.manager = Manager()
        self.user_info_dict = self.manager.dict()
        self.user_info_dict_initiated = False
        self.exchange_config_df_dict = self.manager.dict()
        self.exchange_config_df_dict_initiated = False
        self.trade_df_dict = self.manager.dict()
        self.load_user_info_thread = Thread(target=self.load_user_info, daemon=True)
        self.load_user_info_thread.start()
        self.load_exchange_config_thread = Thread(target=self.load_exchange_config, daemon=True)
        self.load_exchange_config_thread.start()
        for each_market_combi_code in self.enabled_markets:        
            self.start_trigger_loop_proc = Process(target=self.start_trigger_loop, args=(each_market_combi_code, self.trade_df_dict), daemon=True)
            self.start_trigger_loop_proc.start()
        # while self.user_info_dict_initiated is False or self.exchange_config_df_dict_initiated is False or [self.trade_df_dict.get(each_market_combi_code) for each_market_combi_code in self.enabled_markets].count(None) != 0:
        #     time.sleep(0.2)
        while self.user_info_dict_initiated is False:
            time.sleep(0.2)
        self.logger.info("user_info_df, exchange_config_df_dict, trade_df_dict have been initialized")
        time.sleep(20)

    def is_table_empty(self, conn, table_name):
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cur.fetchone()[0]
            return count == 0

    def get_column_names(self, conn, table_name):
        with conn.cursor() as cur:
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position;
            """, (table_name,))
            return [row[0] for row in cur.fetchall()]

    def load_user_info(self, table_name='user_info', loop_interval_secs=1):
        while True:
            try:
                conn = self.postgres_client.pool.getconn()
                curr = conn.cursor(cursor_factory=extras.RealDictCursor)
                curr.execute(f"SELECT * FROM {table_name}")
                fetched_dict_list = curr.fetchall()
                for fetched_dict in fetched_dict_list:
                    each_user_info_dict = {
                        "email": fetched_dict['email'],
                        "telegram_id": fetched_dict['telegram_id'],
                        "telegram_name": fetched_dict['telegram_name'],
                        "send_times": fetched_dict['send_times'],
                        "send_term": fetched_dict['send_term'],
                    }
                    self.user_info_dict[fetched_dict['user_uuid']] = each_user_info_dict
                self.postgres_client.pool.putconn(conn)
                if self.user_info_dict_initiated is False:
                    self.user_info_dict_initiated = True
                time.sleep(loop_interval_secs)
            except Exception as e:
                # rollback the transaction if any error while inserting
                self.postgres_client.pool.putconn(conn, close=True)
                self.logger.error(f"Error in load_user_info: {e}")
                self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"load_user_info", content=traceback.format_exc(), code=None, sent_switch=0, send_counts=1, remark=None)
                time.sleep(10)

    def load_exchange_config(self, table_name='exchange_config', loop_interval_secs=1):
        while True:
            try:
                # First check whether the table is empty
                conn = self.postgres_client.pool.getconn()
                curr = conn.cursor(cursor_factory=extras.RealDictCursor)
                if self.is_table_empty(conn, table_name):
                    # # Get the column names
                    # column_names = self.get_column_names(conn, table_name)
                    # # Create empty dataframe
                    # self.exchange_config_df = pd.DataFrame(columns=column_names)
                    pass
                else:
                    curr.execute(f"SELECT * FROM {table_name}")
                    exchange_config_df = pd.DataFrame(curr.fetchall())
                    target_market_code_unique = exchange_config_df['target_market_code'].unique()
                    origin_market_code_unique = exchange_config_df['origin_market_code'].unique()
                    for target_market_code in target_market_code_unique:
                        for origin_market_code in origin_market_code_unique:
                            market_combi_code = f"{target_market_code}:{origin_market_code}"
                            self.exchange_config_df_dict[market_combi_code] = exchange_config_df[(exchange_config_df['target_market_code'] == target_market_code) & (exchange_config_df['origin_market_code'] == origin_market_code)]
                self.postgres_client.pool.putconn(conn)
                if self.exchange_config_df_dict_initiated is False:
                    self.exchange_config_df_dict_initiated = True
                time.sleep(loop_interval_secs)
            except Exception as e:
                # rollback the transaction if any error while inserting
                self.postgres_client.pool.putconn(conn, close=True)
                self.logger.error(f"Error in load_exchange_config: {e}")
                self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"load_exchange_config", content=traceback.format_exc(), code=None, sent_switch=0, send_counts=1, remark=None)
                time.sleep(10)
        
    def start_trigger_loop(self, market_combi_code, trade_df_dict, table_name='trade', loop_interval_secs=5):
        # TEST
        target_market_code, origin_market_code = market_combi_code.split(':')
        self.logger.info(f"start_trigger_loop: {market_combi_code}")
        postgres_client = InitPostgresDBClient(**{**self.db_dict, 'database': 'trade_core'})
        self.logger.info(f"postgres client has been initiated for {market_combi_code}")
        while True:
            try:
                # First check whether the table is empty
                conn = postgres_client.pool.getconn()
                curr = conn.cursor(cursor_factory=extras.RealDictCursor)
                if self.is_table_empty(conn, table_name):
                    # Get the column names
                    column_names = self.get_column_names(conn, table_name)
                    # Create empty dataframe
                    trade_df_dict[market_combi_code] = pd.DataFrame(columns=column_names)
                else:
                    curr.execute(f"SELECT * FROM {table_name} WHERE target_market_code = %s AND origin_market_code = %s", (target_market_code, origin_market_code))
                    temp_trade_df = pd.DataFrame(curr.fetchall())
                    exchange_config_df = self.exchange_config_df_dict[market_combi_code][['user_uuid','service_datetime_end']]
                    valid_user_uuid_list = exchange_config_df[exchange_config_df['service_datetime_end']>=datetime.datetime.utcnow()]['user_uuid'].tolist()
                    trade_df_dict[market_combi_code] = temp_trade_df[temp_trade_df['user_uuid'].isin(valid_user_uuid_list)]
                    trade_df = trade_df_dict[market_combi_code]
                postgres_client.pool.putconn(conn)
                # Loading data done
                if len(trade_df) == 0:
                    time.sleep(loop_interval_secs)
                    continue

                trade_df = self.trade_df_dict[market_combi_code]
                premium_df = self.get_premium_df(*market_combi_code.split(':'))
                merged_df = trade_df.merge(premium_df, on='base_asset')
                merged_df['SL_premium_value'] = merged_df.apply(lambda x: x['SL_premium'] if x['usdt_conversion'] == False else x['SL_premium']*x['dollar'], axis=1)
                merged_df['LS_premium_value'] = merged_df.apply(lambda x: x['LS_premium'] if x['usdt_conversion'] == False else x['LS_premium']*x['dollar'], axis=1)

                # switch None: 최초, 0: 하향돌파 시, 1: 상향돌파 시
                # auto_trade_switch 0: 진입대기, -1: 탈출대기, 1:탈출완료, 2:탈출에러
                # case 1. switch None or False(0), High 돌파
                high_break_trade_df = (merged_df[((merged_df['trigger_switch'].isnull())|(merged_df['trigger_switch']==False))
                            &(merged_df['SL_premium']>=merged_df['high'])&(merged_df['trade_switch']!=3)])

                # case 2. switch None or True(1), Low 돌파
                low_break_trade_df = (merged_df[((merged_df['trigger_switch'].isnull())|(merged_df['trigger_switch']==True))
                            &(merged_df['LS_premium']<=merged_df['low'])&(merged_df['trade_switch']!=3)])

                # trade_swtich == 0: 진입대기, -1: 탈출대기, 1:탈출완료, 2:탈출에러, 3:거래 진행 중
                if len(high_break_trade_df) != 0:
                    high_break_trade_uuid_list = high_break_trade_df['uuid'].to_list()
                    # UPDATE database
                    conn = postgres_client.pool.getconn()
                    curr = conn.cursor()
                    curr.execute(f"UPDATE trade SET trigger_switch = 1 WHERE uuid IN %s", (tuple(high_break_trade_uuid_list),))
                    conn.commit()
                    postgres_client.pool.putconn(conn)
                    self.high_break(high_break_trade_df)

                if len(low_break_trade_df) != 0:
                    low_break_trade_uuid_list = low_break_trade_df['uuid'].to_list()
                    # UPDATE database
                    conn = postgres_client.pool.getconn()
                    curr = conn.cursor()
                    curr.execute(f"UPDATE trade SET trigger_switch = 0 WHERE uuid IN %s", (tuple(low_break_trade_uuid_list),))
                    conn.commit()
                    postgres_client.pool.putconn(conn)
                    self.low_break(low_break_trade_df)

                time.sleep(loop_interval_secs)
            except Exception as e:
                self.logger.error(f"Error in start_trigger_loop: {e}")
                # rollback the transaction if any error while inserting
                postgres_client.pool.putconn(conn, close=True)
                self.logger.error(f"Error in start_trigger_loop: {e}")
                self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"start_trigger_loop", content=traceback.format_exc(), code=None, sent_switch=0, send_counts=1, remark=None)
                time.sleep(10)

    def high_break(self, high_break_trade_df):
        for row_tup in high_break_trade_df.iterrows():
            def row_thread(row_tup):
                row = row_tup[1]
                user_uuid = row['user_uuid']
                telegram_id = self.user_info_dict[user_uuid]['telegram_id']
                telegram_name = self.user_info_dict[user_uuid]['telegram_name']
                send_times = self.user_info_dict[user_uuid]['send_times']
                send_term = self.user_info_dict[user_uuid]['send_term']
                trade_uuid = row['uuid']
                target_market_code = row['target_market_code']
                origin_market_code = row['origin_market_code']
                base_asset = row['base_asset']
                quote_asset = row['quote_asset']
                low = row['low']
                high = row['high']
                usdt_convertsion = row['usdt_conversion']
                

                ls_premium = row['LS_premium']
                ls_premium_value = row['LS_premium_value']
                sl_premium = row['SL_premium']
                sl_premium_value = row['SL_premium_value']

                msg_title = f"프리미엄 상향돌파"
                msg_content = f"{base_asset} {quote_asset} {sl_premium} {sl_premium_value}, 현재가격: {row['tp']}({round(row['scr'],2)}%)"
                msg_full = f"{msg_title}\n{msg_content}"
                print(f"{msg_full}")
                self.msg_api.create_message(self.admin_id, msg_title, self.node, 'info', msg_content)
            row_thread = Thread(target=row_thread, args=(row_tup,), daemon=True)
            row_thread.start()

    def low_break(self, low_break_trade_df):
        for row_tup in low_break_trade_df.iterrows():
            def row_thread(row_tup):
                row = row_tup[1]
                user_uuid = row['user_uuid']
                telegram_id = self.user_info_dict[user_uuid]['telegram_id']
                telegram_name = self.user_info_dict[user_uuid]['telegram_name']
                send_times = self.user_info_dict[user_uuid]['send_times']
                send_term = self.user_info_dict[user_uuid]['send_term']
                trade_uuid = row['uuid']
                target_market_code = row['target_market_code']
                origin_market_code = row['origin_market_code']
                base_asset = row['base_asset']
                quote_asset = row['quote_asset']
                low = row['low']
                high = row['high']
                usdt_convertsion = row['usdt_conversion']
                

                ls_premium = row['LS_premium']
                ls_premium_value = row['LS_premium_value']
                sl_premium = row['SL_premium']
                sl_premium_value = row['SL_premium_value']

                msg_title = f"프리미엄 하향돌파"
                msg_content = f"{base_asset} {quote_asset} {ls_premium} {ls_premium_value}, 현재가격: {row['tp']}({round(row['scr'],2)}%)"
                msg_full = f"{msg_title}\n{msg_content}"
                print(f"{msg_full}")
                self.msg_api.create_message(self.admin_id, msg_title, self.node, 'info', msg_content)
            row_thread = Thread(target=row_thread, args=(row_tup,), daemon=True)
            row_thread.start()