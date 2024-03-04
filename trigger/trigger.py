import time
import traceback
import pandas as pd
from etc.db_handler.postgres_client import InitDBClient as InitPostgresDBClient
from loggers.logger import KimpBotLogger
from threading import Thread
from multiprocessing import Process, Manager
from threading import Thread
from psycopg2 import extras
from etc.acw_api import AcwApi

class InitTrigger:
    def __init__(self, admin_telegram_id, node, server_check_status_list, get_premium_df, enabled_markets, register_monitor_msg, remote_redis_client, db_dict, mongo_client, postgres_client, logging_dir):
        self.admin_telegram_id = admin_telegram_id
        self.node = node
        self.acw_api = AcwApi(prod=False)
        self.server_check_status_list = server_check_status_list
        self.get_premium_df = get_premium_df
        self.enabled_markets = enabled_markets
        self.register_monitor_msg = register_monitor_msg
        self.remote_redis_client = remote_redis_client
        self.db_dict = db_dict
        self.mongo_client = mongo_client
        self.postgres_client = postgres_client
        self.logging_dir = logging_dir
        self.logger = KimpBotLogger("trigger", logging_dir).logger
        self.manager = Manager()
        self.exchange_config_df_dict = self.manager.dict()
        self.exchange_config_df_dict_initiated = False
        self.free_trade_df_dict = self.manager.dict()
        self.trade_df_dict = self.manager.dict()
        self.load_exchange_config_thread = Thread(target=self.load_exchange_config, daemon=True)
        self.load_exchange_config_thread.start()

        self.trade_proc_dict = {}
        self.alarm_proc_dict = {}
        for each_market_combi_code in self.enabled_markets:        
            self.trade_proc_dict[each_market_combi_code] = Process(target=self.start_trigger_loop, args=(each_market_combi_code, self.trade_df_dict, False, 'trade', 2), daemon=True)
            self.trade_proc_dict[each_market_combi_code].start()
            self.alarm_proc_dict[each_market_combi_code] = Process(target=self.start_trigger_loop, args=(each_market_combi_code, self.free_trade_df_dict, True, 'trade', 2), daemon=True)
            self.alarm_proc_dict[each_market_combi_code].start()
        # while self.user_info_dict_initiated is False or self.exchange_config_df_dict_initiated is False or [self.trade_df_dict.get(each_market_combi_code) for each_market_combi_code in self.enabled_markets].count(None) != 0:
        #     time.sleep(0.2)
        # while self.user_info_dict_initiated is False:
        #     time.sleep(0.2)
        self.logger.info("trade_config_df_dict, trade_df_dict have been initialized")
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

    def load_exchange_config(self, table_name='trade_config'):
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
        except Exception as e:
            # rollback the transaction if any error while inserting
            self.postgres_client.pool.putconn(conn, close=True)
            title = f"Error in load_exchange_config"
            full_content = f"{title}:\n{traceback.format_exc()}"
            self.logger.error(full_content)
            self.acw_api.create_message(self.admin_telegram_id, title, self.node, "monitor", full_content, code=None)
            time.sleep(5)

    def load_exchange_config_loop(self, table_name='trade_config', loop_interval_secs=1):
        while True:
            self.load_exchange_config(table_name)
            time.sleep(loop_interval_secs)

    def load_trade_df(self, conn, curr, market_combi_code, trade_df_dict, free_user, table_name='trade'):
        target_market_code, origin_market_code = market_combi_code.split(':')
        try:
            # First check whether the table is empty
            if self.is_table_empty(conn, table_name):
                # Get the column names
                column_names = self.get_column_names(conn, table_name)
                # Create empty dataframe
                trade_df_dict[market_combi_code] = pd.DataFrame(columns=column_names)
            else:
                if free_user:
                    sql = """
                    SELECT trade.*, trade_config, trade_config.service_datetime_end, trade_config.telegram_id, trade_config.target_market_code, trade_config.origin_market_code, trade_config.send_times, trade_config.send_term,
                    trade_config.target_market_cross, trade_config.target_market_leverage, trade_config.origin_market_cross, trade_config.origin_market_leverage, trade_config.target_market_margin_call, trade_config.origin_market_margin_call,
                    trade_config.target_market_safe_reverse, trade_config.origin_market_safe_reverse, trade_config.target_market_risk_threshold_p, trade_config.origin_market_risk_threshold_p, trade_config.repeat_limit_p,
                    trade_config.repeat_limit_direction, trade_config.repeat_num_limit
                    FROM trade
                    JOIN trade_config ON trade.trade_config_uuid = trade_config.uuid WHERE trade_config.target_market_code=%s AND trade_config.origin_market_code=%s AND trade_config.service_datetime_end <= %s"""
                else:
                    sql = """
                    SELECT trade.*, trade_config, trade_config.service_datetime_end, trade_config.telegram_id, trade_config.target_market_code, trade_config.origin_market_code, trade_config.send_times, trade_config.send_term,
                    trade_config.target_market_cross, trade_config.target_market_leverage, trade_config.origin_market_cross, trade_config.origin_market_leverage, trade_config.target_market_margin_call, trade_config.origin_market_margin_call,
                    trade_config.target_market_safe_reverse, trade_config.origin_market_safe_reverse, trade_config.target_market_risk_threshold_p, trade_config.origin_market_risk_threshold_p, trade_config.repeat_limit_p,
                    trade_config.repeat_limit_direction, trade_config.repeat_num_limit
                    FROM trade
                    JOIN trade_config ON trade.trade_config_uuid = trade_config.uuid WHERE trade_config.target_market_code=%s AND trade_config.origin_market_code=%s AND trade_config.service_datetime_end > %s"""
                val = (target_market_code, origin_market_code, pd.Timestamp.now())
                curr.execute(sql, val)
                trade_df = pd.DataFrame(curr.fetchall())
                trade_df_dict[market_combi_code] = trade_df
                return trade_df
        except Exception as e:
            title = f"Error in load_trade_df"
            full_content = f"Error in load_trade_df: {e}\n{traceback.format_exc()}"
            self.logger.error(full_content)
            self.acw_api.create_message(self.admin_telegram_id, title, self.node, "monitor", full_content, code=None)
        
    def start_trigger_loop(self, market_combi_code, trade_df_dict, free_user=True, table_name='trade', loop_interval_secs=5):
        self.logger.info(f"start_trigger_loop: {market_combi_code} | free_user: {free_user} | table_name: {table_name} | loop_interval_secs: {loop_interval_secs}")
        postgres_client = InitPostgresDBClient(**{**self.db_dict, 'database': 'trade_core'})
        conn = postgres_client.pool.getconn()
        curr = conn.cursor(cursor_factory=extras.RealDictCursor)
        self.logger.info(f"postgres client has been initiated for {market_combi_code}")
        while True:
            try:
                trade_df = self.load_trade_df(conn, curr, market_combi_code, trade_df_dict, free_user, table_name)
                # Loading data done
                if len(trade_df) == 0 or trade_df is None:
                    time.sleep(loop_interval_secs)
                    continue

                premium_df = self.get_premium_df(*market_combi_code.split(':'))
                merged_df = trade_df.merge(premium_df, on='base_asset')
                merged_df['SL_premium_value'] = merged_df.apply(lambda x: x['SL_premium'] if x['usdt_conversion'] == False else (1+x['SL_premium']/100)*x['dollar'], axis=1)
                merged_df['LS_premium_value'] = merged_df.apply(lambda x: x['LS_premium'] if x['usdt_conversion'] == False else (1+x['LS_premium']/100)*x['dollar'], axis=1)

                # switch None: 최초, 0: 하향돌파 시, 1: 상향돌파 시
                # auto_trade_switch 0: 진입대기, -1: 탈출대기, 1:탈출완료, 2:탈출에러
                # case 1. switch None or False(0), High 돌파
                high_break_trade_df = (merged_df[((merged_df['trigger_switch'].isnull())|(merged_df['trigger_switch']==False))
                            &(merged_df['SL_premium_value']>=merged_df['high'])&(merged_df['trade_switch']!=3)])

                # case 2. switch None or True(1), Low 돌파
                low_break_trade_df = (merged_df[((merged_df['trigger_switch'].isnull())|(merged_df['trigger_switch']==True))
                            &(merged_df['LS_premium_value']<=merged_df['low'])&(merged_df['trade_switch']!=3)])

                # trade_swtich == 0: 진입대기, -1: 탈출대기, 1:탈출완료, 2:탈출에러, 3:거래 진행 중
                if len(high_break_trade_df) != 0:
                    high_break_trigger_uuid_list = high_break_trade_df['uuid'].to_list()
                    # UPDATE database
                    # conn = postgres_client.pool.getconn()
                    # curr = conn.cursor()
                    curr.execute(f"UPDATE trade SET trigger_switch = 1 WHERE uuid IN %s", (tuple(high_break_trigger_uuid_list),))
                    conn.commit()

                    # postgres_client.pool.putconn(conn)
                    self.high_break(high_break_trade_df, free_user)

                if len(low_break_trade_df) != 0:
                    low_break_trigger_uuid_list = low_break_trade_df['uuid'].to_list()
                    # UPDATE database
                    # conn = postgres_client.pool.getconn()
                    # curr = conn.cursor()
                    curr.execute(f"UPDATE trade SET trigger_switch = 0 WHERE uuid IN %s", (tuple(low_break_trigger_uuid_list),))
                    conn.commit()
                    # postgres_client.pool.putconn(conn)
                    self.low_break(low_break_trade_df, free_user)

                time.sleep(loop_interval_secs)
            except Exception as e:
                title = f"Error in start_trigger_loop"
                full_content = f"{title}: {e}\n{traceback.format_exc()}"
                self.logger.error(full_content)
                # rollback the transaction if any error while inserting
                postgres_client.pool.putconn(conn, close=True)
                self.acw_api.create_message(self.admin_telegram_id, title, self.node, "monitor", full_content, code=None)
                time.sleep(10)

    def high_break(self, high_break_trade_df, free_user):
        for row_tup in high_break_trade_df.iterrows():
            def row_thread(row_tup):
                row = row_tup[1]

                ls_premium = row['LS_premium']
                ls_premium_value = row['LS_premium_value']
                sl_premium = row['SL_premium']
                sl_premium_value = row['SL_premium_value']

                msg_title = f"{row['base_asset']}/{row['quote_asset']} 프리미엄 상향돌파"
                msg_content = f"{row['target_market_code']}:{row['origin_market_code']}\n"
                msg_content += f"현재 SL:{round(sl_premium_value, 3)}, 설정된 탈출값: {row['high']}\n"
                if pd.isnull(row['tp']):
                    current_price = (row['ap'] + row['bp'])/2
                else:
                    current_price = row['tp']
                msg_content += f"현재가격: {current_price}({round(row['scr'],2)}%)"
                msg_full = f"{msg_title}\n{msg_content}"
                self.acw_api.create_message_thread(row['telegram_id'], msg_title, self.node, 'info', msg_full, send_times=row['send_times'], send_term=row['send_term'])
            row_thread = Thread(target=row_thread, args=(row_tup,), daemon=True)
            row_thread.start()

    def low_break(self, low_break_trade_df, free_user):
        for row_tup in low_break_trade_df.iterrows():
            def row_thread(row_tup):
                row = row_tup[1]
                base_asset = row['base_asset']
                quote_asset = row['quote_asset']                

                ls_premium = row['LS_premium']
                ls_premium_value = row['LS_premium_value']
                sl_premium = row['SL_premium']
                sl_premium_value = row['SL_premium_value']

                msg_title = f"{base_asset}/{quote_asset} 프리미엄 하향돌파"
                msg_content = f"{row['target_market_code']}:{row['origin_market_code']}\n"
                msg_content += f"현재 LS:{round(ls_premium_value, 3)}, 설정된 진입값: {row['low']}\n"
                if pd.isnull(row['tp']):
                    current_price = (row['ap'] + row['bp'])/2
                else:
                    current_price = row['tp']
                msg_content += f"현재가격: {current_price}({round(row['scr'],2)}%)"
                msg_full = f"{msg_title}\n{msg_content}"
                self.acw_api.create_message_thread(row['telegram_id'], msg_title, self.node, 'info', msg_full, send_times=row['send_times'], send_term=row['send_term'])
            row_thread = Thread(target=row_thread, args=(row_tup,), daemon=True)
            row_thread.start()