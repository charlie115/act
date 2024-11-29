import time
import json
import traceback
import datetime
import pandas as pd
from etc.db_handler.postgres_client import InitDBClient as InitPostgresDBClient
from exchange_plugin.integrated_plug import UserExchangeAdaptor
from etc.utils import get_trade_config_df, get_trade_df, get_users_with_negative_balance
from loggers.logger import TradeCoreLogger
from psycopg2 import extras
from threading import Thread
from standalone_func.premium_data_generator import get_premium_df
from standalone_func.uuid_converter import trade_uuid_to_display_id
from standalone_func.data_process import get_pboundary
from etc.redis_connector.redis_helper import RedisHelper
import _pickle as pickle

local_redis = RedisHelper()

def fetch_users_with_negative_balance(acw_api):
    balance_df = acw_api.get_deposit_balance()
    if balance_df.empty:
        return []
    negative_balance_df = balance_df[balance_df['balance'].astype(float) <= 0]
    return negative_balance_df['user'].tolist()
    
def fetch_users_with_negative_balance_loop(admin_id,
                                           acw_api,
                                           logging_dir,
                                           redis_key_name='negative_balance_users',
                                           ex=30,
                                           loop_interval_secs=15):
    logger = TradeCoreLogger("fetch_users_with_negative_balance", logging_dir).logger
    logger.info("fetch_users_with_negative_balance_loop has been started")
    while True:
        try:
            negative_balance_users = fetch_users_with_negative_balance(acw_api)
            local_redis.set_data(redis_key_name, json.dumps(negative_balance_users), ex=ex)
        except Exception as e:
            local_redis.set_data(redis_key_name, json.dumps([]), ex=ex)
            title = f"Error in fetch_users_with_negative_balance"
            full_content = f"{title}:\n{traceback.format_exc()}"
            logger.error(full_content)
            acw_api.create_message_thread(admin_id, title, full_content)
            time.sleep(5)
        time.sleep(loop_interval_secs)
        
def load_trade_config(postgres_client, admin_id, acw_api, logger, ex, table_name='trade_config'):
    try:
        conn = postgres_client.pool.getconn()
        curr = conn.cursor(cursor_factory=extras.RealDictCursor)
        # First check whether the table is empty
        if postgres_client.is_table_empty(table_name):
            # # Get the column names
            # column_names = self.postgres_client.get_column_names(table_name)
            # # Create empty dataframe
            # self.trade_config_df = pd.DataFrame(columns=column_names)
            pass
        else:
            curr.execute(f"SELECT * FROM {table_name}")
            trade_config_df = pd.DataFrame(curr.fetchall())
            target_market_code_unique = trade_config_df['target_market_code'].unique()
            origin_market_code_unique = trade_config_df['origin_market_code'].unique()
            for target_market_code in target_market_code_unique:
                for origin_market_code in origin_market_code_unique:
                    market_code_combination = f"{target_market_code}:{origin_market_code}"
                    local_redis.set_data(f"{table_name}|{market_code_combination}",
                                         pickle.dumps(trade_config_df[(trade_config_df['target_market_code'] == target_market_code) & (trade_config_df['origin_market_code'] == origin_market_code)]),
                                         ex=ex)
        postgres_client.pool.putconn(conn)
    except Exception as e:
        # rollback the transaction if any error while inserting
        postgres_client.pool.putconn(conn, close=True)
        title = f"Error in load_trade_config"
        full_content = f"{title}:\n{traceback.format_exc()}"
        logger.error(full_content)
        acw_api.create_message_thread(admin_id, title, full_content)
        time.sleep(5)
        
        
def load_trade_config_loop(postgres_db_dict, admin_id, acw_api, logging_dir, ex=30, table_name='trade_config', loop_interval_secs=1):
    logger = TradeCoreLogger("load_trade_config", logging_dir).logger
    logger.info(f"load_trade_config_loop has been started")
    postgres_client = InitPostgresDBClient(**{**postgres_db_dict, 'database': 'trade_core'})
    while True:
        load_trade_config(postgres_client, admin_id, acw_api, logger, ex, table_name)
        time.sleep(loop_interval_secs)

def load_trade_df(curr,
                  postgres_client,
                  market_code_combination,
                  trade_support,
                  admin_id,
                  acw_api,
                  logger,
                  table_name='trade',
                  users_with_negative_banace_redis_key_name='negative_balance_users'):
    target_market_code, origin_market_code = market_code_combination.split(':')

    try:
        if not trade_support:
            # alarm trigger only!
            sql = """
            SELECT trade.*, trade_config.telegram_id, trade_config.target_market_code, trade_config.origin_market_code,
            trade_config.send_times, trade_config.send_term,
            trade_config.target_market_cross, trade_config.target_market_leverage, trade_config.origin_market_cross,
            trade_config.origin_market_leverage, trade_config.target_market_margin_call, trade_config.origin_market_margin_call,
            trade_config.safe_reverse,
            trade_config.target_market_risk_threshold_p, trade_config.origin_market_risk_threshold_p, trade_config.repeat_limit_p,
            trade_config.repeat_limit_direction, trade_config.repeat_num_limit
            FROM trade
            JOIN trade_config ON trade.trade_config_uuid = trade_config.uuid
            WHERE trade_config.target_market_code=%s AND trade_config.origin_market_code=%s AND trade.trade_switch IS NULL
            """
            val = (target_market_code, origin_market_code)
        else:
            # trade trigger only!
            users_with_negative_balance = get_users_with_negative_balance(users_with_negative_banace_redis_key_name)
            if not users_with_negative_balance:
                sql = """
                SELECT trade.*, trade_config.user, trade_config.telegram_id, trade_config.target_market_code, trade_config.origin_market_code,
                trade_config.send_times, trade_config.send_term,
                trade_config.target_market_cross, trade_config.target_market_leverage, trade_config.origin_market_cross,
                trade_config.origin_market_leverage, trade_config.target_market_margin_call, trade_config.origin_market_margin_call,
                trade_config.safe_reverse,
                trade_config.target_market_risk_threshold_p, trade_config.origin_market_risk_threshold_p, trade_config.repeat_limit_p,
                trade_config.repeat_limit_direction, trade_config.repeat_num_limit
                FROM trade
                JOIN trade_config ON trade.trade_config_uuid = trade_config.uuid
                WHERE trade_config.target_market_code=%s AND trade_config.origin_market_code=%s AND trade.trade_switch IS NOT NULL
                """
                val = (target_market_code, origin_market_code)
            else:
                sql = """
                SELECT trade.*, trade_config.user, trade_config.telegram_id, trade_config.target_market_code, trade_config.origin_market_code,
                trade_config.send_times, trade_config.send_term,
                trade_config.target_market_cross, trade_config.target_market_leverage, trade_config.origin_market_cross,
                trade_config.origin_market_leverage, trade_config.target_market_margin_call, trade_config.origin_market_margin_call,
                trade_config.safe_reverse,
                trade_config.target_market_risk_threshold_p, trade_config.origin_market_risk_threshold_p, trade_config.repeat_limit_p,
                trade_config.repeat_limit_direction, trade_config.repeat_num_limit
                FROM trade
                JOIN trade_config ON trade.trade_config_uuid = trade_config.uuid
                WHERE trade_config.target_market_code=%s AND trade_config.origin_market_code=%s AND trade_config.user NOT IN %s AND trade.trade_switch IS NOT NULL
                """
                val = (target_market_code, origin_market_code, tuple(users_with_negative_balance))

        curr.execute(sql, val)
        trade_records = curr.fetchall()
        trade_df = pd.DataFrame(trade_records)
        # check whetheer the table is empty
        if trade_df.empty:
            # Get the column names
            column_names = postgres_client.get_column_names(table_name)
            # Create empty dataframe
            trade_df = pd.DataFrame(columns=column_names)
        # Set trade_df to the redis
        if trade_support:
            local_redis.set_data(f"{table_name}|trade|{market_code_combination}", pickle.dumps(trade_df), ex=30)
        else:
            local_redis.set_data(f"{table_name}|alarm|{market_code_combination}", pickle.dumps(trade_df), ex=30)
        return trade_df
    except Exception as e:
        title = f"Error in load_trade_df"
        full_content = f"Error in load_trade_df: {e}\n{traceback.format_exc()}"
        logger.error(full_content)
        acw_api.create_message_thread(admin_id, title, full_content)
        return

def start_trigger_loop(
    market_code_combination,
    trade_support,
    postgres_db_dict,
    mongo_db_dict,
    admin_id,
    acw_api,
    logging_dir,
    table_name='trade',
    loop_interval_secs=5
):
    logger = TradeCoreLogger("trigger", logging_dir).logger
    logger.info(f"start_trigger_loop: {market_code_combination} | trade_support: {trade_support} | table_name: {table_name} | loop_interval_secs: {loop_interval_secs}")
    
    postgres_client = InitPostgresDBClient(**{**postgres_db_dict, 'database': 'trade_core'})
    conn = postgres_client.pool.getconn()
    curr = conn.cursor(cursor_factory=extras.RealDictCursor)
    logger.info(f"postgres client has been initiated for {market_code_combination}")
    
    if not trade_support:
        user_exchange_adaptor = None
    else:
        # Initialize UserExchangeAdaptor
        user_exchange_adaptor = UserExchangeAdaptor(
            admin_id=admin_id,
            acw_api=acw_api,
            redis_db_dict=None,
            postgres_db_dict=postgres_db_dict,
            market_code_combination=market_code_combination,
            api_server=False,
            logging_dir=logging_dir
        )
        # Start handle_repeat_trade_loop in a separate thread
        handle_repeat_trade_loop_thread = Thread(
            target=handle_repeat_trade_loop,
            args=(postgres_db_dict, mongo_db_dict, market_code_combination, admin_id, acw_api, logging_dir),
            daemon=True
        )
        handle_repeat_trade_loop_thread.start()
        
    # Initialize info_dict and convert_rate_dict
    while True:
        fetched_info_dict = local_redis.get_data('info_dict')
        fetched_convert_rate_dict = local_redis.hgetall_dict('convert_rate_dict')
        if fetched_info_dict and fetched_convert_rate_dict:
            fetched_info_dict = pickle.loads(fetched_info_dict)
            fetched_convert_rate_dict = {key.decode('utf-8'): float(value) for key, value in fetched_convert_rate_dict.items()}
            break
        logger.info("info_dict and convert_rate_dict are not ready yet. Waiting for 1 second...")
        time.sleep(1)
    
    while True:
        try:
            trade_df = load_trade_df(curr,
                                    postgres_client,
                                    market_code_combination,
                                    trade_support,
                                    admin_id,
                                    acw_api,
                                    logger,
                                    table_name,)
            if trade_df is None or trade_df.empty:
                time.sleep(loop_interval_secs)
                continue
            
            target_market_code, origin_market_code = market_code_combination.split(':')
            premium_df = get_premium_df(local_redis, fetched_info_dict, fetched_convert_rate_dict, target_market_code, origin_market_code, logger)
            merged_df = trade_df.merge(premium_df, on='base_asset')
            merged_df['SL_premium_value'] = merged_df.apply(
                lambda x: x['SL_premium'] if not x['usdt_conversion'] else (1 + x['SL_premium'] / 100) * x['dollar'], axis=1)
            merged_df['LS_premium_value'] = merged_df.apply(
                lambda x: x['LS_premium'] if not x['usdt_conversion'] else (1 + x['LS_premium'] / 100) * x['dollar'], axis=1)

            # Define high_break and low_break dataframes
            # switch None: 최초, 0: 하향돌파 시, 1: 상향돌파 시
            # trade_switch 0: 진입대기, -1: 탈출대기, -2: 진입에러, 1:탈출완료, 2:탈출에러, 3: 거래 진행 중
            # case 1. switch None or False(0), High 돌파
            high_break_trade_df = merged_df[
                ((merged_df['trigger_switch'].isnull()) | (merged_df['trigger_switch'] == False)) &
                (merged_df['SL_premium_value'] >= merged_df['high']) &
                (merged_df['trade_switch'] != 3)
            ]
            # case 2. switch None or True(1), Low 돌파
            low_break_trade_df = merged_df[
                ((merged_df['trigger_switch'].isnull()) | (merged_df['trigger_switch'] == True)) &
                (merged_df['LS_premium_value'] <= merged_df['low']) &
                (merged_df['trade_switch'] != 3)
            ]

            if not high_break_trade_df.empty:
                high_break_trigger_uuid_list = high_break_trade_df['uuid'].to_list()
                high_break_placeholders = ', '.join(['%s'] * len(high_break_trigger_uuid_list))
                high_break_params = tuple(high_break_trigger_uuid_list)
                # UPDATE database
                if trade_support: # trade triggers only
                    # sql = f"""
                    #         UPDATE {table_name}
                    #         SET trigger_switch = 1,
                    #             trade_switch = CASE
                    #                 WHEN trade_switch = -1 THEN 3
                    #                 WHEN trade_switch = 0 THEN trade_switch
                    #                 ELSE trade_switch
                    #             END
                    #         WHERE uuid IN ({high_break_placeholders})
                    #         AND (trade_switch = -1 OR trade_switch = 0);
                    #         """
                    sql = f"""
                            UPDATE {table_name}
                            SET trigger_switch = 1,
                                trade_switch = CASE
                                    WHEN trade_switch = -1 THEN 3
                                    ELSE trade_switch
                                END
                            WHERE uuid IN ({high_break_placeholders});
                            """
                else:
                    sql = f"UPDATE {table_name} SET trigger_switch = 1 WHERE uuid IN ({high_break_placeholders})"
                curr.execute(sql, high_break_params)
                conn.commit()
                if curr.rowcount == 0:
                    logger.error(f"No row has been updated for high_break_trade_df even though there are {len(high_break_trade_df)} rows")
                high_break(high_break_trade_df, user_exchange_adaptor, market_code_combination, trade_support, admin_id, acw_api, logger)

            if not low_break_trade_df.empty:
                low_break_trigger_uuid_list = low_break_trade_df['uuid'].to_list()
                low_break_placeholders = ', '.join(['%s'] * len(low_break_trigger_uuid_list))
                low_break_params = tuple(low_break_trigger_uuid_list)
                # UPDATE database
                if trade_support:
                    # sql = f"""
                    #         UPDATE {table_name}
                    #         SET trigger_switch = 0,
                    #             trade_switch = CASE
                    #                 WHEN trade_switch = 0 THEN 3
                    #                 ELSE trade_switch
                    #             END
                    #         WHERE uuid IN ({low_break_placeholders})
                    #         AND (trade_switch = 1 OR trade_switch = 0);
                    #         """
                    sql = f"""
                            UPDATE {table_name}
                            SET trigger_switch = 0,
                                trade_switch = CASE
                                    WHEN trade_switch = 0 THEN 3
                                    ELSE trade_switch
                                END
                            WHERE uuid IN ({low_break_placeholders});
                            """
                else:
                    sql = f"UPDATE {table_name} SET trigger_switch = 0 WHERE uuid IN ({low_break_placeholders})"
                curr.execute(sql, low_break_params)
                conn.commit()
                if curr.rowcount == 0:
                    logger.error(f"No row has been updated for low_break_trade_df even though there are {len(low_break_trade_df)} rows")
                low_break(low_break_trade_df, user_exchange_adaptor, market_code_combination, trade_support, admin_id, acw_api, logger)
            # Reload the info_dict and convert_rate_dict
            fetched_info_dict = pickle.loads(local_redis.get_data('info_dict'))
            fetched_convert_rate_dict = {key.decode('utf-8'): float(value) for key, value in local_redis.hgetall_dict('convert_rate_dict').items()}
            time.sleep(loop_interval_secs)
        except Exception as e:
            title = f"Error in start_trigger_loop"
            full_content = f"{title}: {e}\n{traceback.format_exc()}"
            logger.error(full_content)
            # Reinitialize the connection and cursor
            postgres_client.pool.putconn(conn, close=True)
            # re-initiate the connection and cursor
            conn = postgres_client.pool.getconn()
            curr = conn.cursor(cursor_factory=extras.RealDictCursor)
            acw_api.create_message_thread(admin_id, title, full_content)
            time.sleep(10)
            
def high_break(high_break_trade_df, user_exchange_adaptor, market_code_combination, trade_support, admin_id, acw_api, logger):
    for row_tup in high_break_trade_df.iterrows():
        def row_thread(row_tup):
            try:
                row = row_tup[1]
                # ls_premium = row['LS_premium']
                # ls_premium_value = row['LS_premium_value']
                # sl_premium = row['SL_premium']
                # sl_premium_value = row['SL_premium_value']
                
                if trade_support: # trade triggers only
                    user_exchange_adaptor.short_long_trade(row)

                msg_title = f"거래ID: {trade_uuid_to_display_id(local_redis, market_code_combination, row['uuid'], logger)}({row['base_asset']}/{row['quote_asset']}) 프리미엄 상향돌파"
                msg_content = f"{row['target_market_code']}:{row['origin_market_code']}\n"
                msg_content += f"현재 SL:{round(row['SL_premium_value'], 3)}, 설정된 탈출값: {row['high']}\n"
                if pd.isnull(row['tp']):
                    current_price = (row['ap'] + row['bp'])/2
                else:
                    current_price = row['tp']
                msg_content += f"현재가격: {current_price}({round(row['scr'],2)}%)"
                msg_full = f"{msg_title}\n{msg_content}"
                acw_api.create_message_thread(row['telegram_id'], msg_title, msg_full, 'INFO', send_times=row['send_times'], send_term=row['send_term'])
            except Exception as e:
                title = f"Error in high_break"
                full_content = f"{title}: {e}\n{traceback.format_exc()}"
                logger.error(full_content)
                acw_api.create_message_thread(admin_id, title, full_content)
        row_thread = Thread(target=row_thread, args=(row_tup,), daemon=True)
        row_thread.start()
        
def low_break(low_break_trade_df, user_exchange_adaptor, market_code_combination, trade_support, admin_id, acw_api, logger):
    for row_tup in low_break_trade_df.iterrows():
        def row_thread(row_tup):
            try:
                row = row_tup[1]
                # base_asset = row['base_asset']
                # quote_asset = row['quote_asset']

                # ls_premium = row['LS_premium']
                # ls_premium_value = row['LS_premium_value']
                # sl_premium = row['SL_premium']
                # sl_premium_value = row['SL_premium_value']
                if trade_support: # trade triggers only
                    user_exchange_adaptor.long_short_trade(row)
                
                msg_title = f"거래ID: {trade_uuid_to_display_id(local_redis, market_code_combination, row['uuid'], logger)}({row['base_asset']}/{row['quote_asset']}) 프리미엄 하향돌파"
                msg_content = f"{row['target_market_code']}:{row['origin_market_code']}\n"
                msg_content += f"현재 LS:{round(row['LS_premium_value'], 3)}, 설정된 진입값: {row['low']}\n"
                if pd.isnull(row['tp']):
                    current_price = (row['ap'] + row['bp'])/2
                else:
                    current_price = row['tp']
                msg_content += f"현재가격: {current_price}({round(row['scr'],2)}%)"
                msg_full = f"{msg_title}\n{msg_content}"
                acw_api.create_message_thread(row['telegram_id'], msg_title, msg_full, 'INFO', send_times=row['send_times'], send_term=row['send_term'])
            except Exception as e:
                title = f"Error in low_break"
                full_content = f"{title}: {e}\n{traceback.format_exc()}"
                logger.error(full_content)
                acw_api.create_message_thread(admin_id, title, full_content)
        row_thread = Thread(target=row_thread, args=(row_tup,), daemon=True)
        row_thread.start()
        
def load_merged_repeat_df(postgres_client,
                          market_code_combination,
                          admin_id,
                          acw_api,
                          logger,
                          table_name='repeat_trade'):
    try:
        conn = postgres_client.pool.getconn()
        curr = conn.cursor(cursor_factory=extras.RealDictCursor)
        # First check whether the table is empty
        if postgres_client.is_table_empty(table_name):
            # Get the column names
            column_names = postgres_client.get_column_names(table_name)
            # Create empty dataframe
            repeat_df = pd.DataFrame(columns=column_names)
            # save the repeat_df to the redis
            local_redis.set_data(f"{table_name}|{market_code_combination}", pickle.dumps(repeat_df), ex=30)
            merged_repeat_df = repeat_df
        else:
            # only valid user's repeat settings are loaded!
            sql = f"""SELECT * FROM {table_name}"""
            curr.execute(sql)
            repeat_df = pd.DataFrame(curr.fetchall())
            # save the repeat_df to the redis
            local_redis.set_data(f"{table_name}|{market_code_combination}", pickle.dumps(repeat_df), ex=30)
            merged_repeat_df = repeat_df
        if len(repeat_df) != 0:
            # intersect with trade_df                
            trade_df = get_trade_df(market_code_combination, trade_support=True)
            merged_repeat_df = trade_df.merge(repeat_df, left_on='uuid', right_on='trade_uuid')
            # save the merged_repeat_df to the redis
            local_redis.set_data(f"{table_name}|{market_code_combination}", pickle.dumps(merged_repeat_df), ex=30)
        postgres_client.pool.putconn(conn, close=True)
        return merged_repeat_df
    except Exception as e:
        title = f"Error in load_repeat_df"
        full_content = f"Error in load_repeat_df: {e}\n{traceback.format_exc()}"
        logger.error(full_content)
        # put the connection back to the pool
        postgres_client.pool.putconn(conn, close=True)
        acw_api.create_message_thread(admin_id, title, full_content)
        
def handle_repeat_trade_loop(postgres_db_dict, mongo_db_dict, market_code_combination, admin_id, acw_api, logging_dir, loop_interval_secs=1):
    logger = TradeCoreLogger("handle_repeat_trade", logging_dir).logger
    logger.info(f"handle_repeat_trade_loop started for {market_code_combination}")
    postgres_client = InitPostgresDBClient(**{**postgres_db_dict, 'database': 'trade_core'})
    
    # Initialize info_dict and convert_rate_dict
    while True:
        fetched_info_dict = local_redis.get_data('info_dict')
        fetched_convert_rate_dict = local_redis.hgetall_dict('convert_rate_dict')
        if fetched_info_dict and fetched_convert_rate_dict:
            fetched_info_dict = pickle.loads(fetched_info_dict)
            fetched_convert_rate_dict = {key.decode('utf-8'): float(value) for key, value in fetched_convert_rate_dict.items()}
            break
        logger.info("info_dict and convert_rate_dict are not ready yet. Waiting for 1 second...")
        time.sleep(1)
    
    while True:
        try:
            # Check whether trade_df_dict for that market_combination exists
            if get_trade_df(market_code_combination, trade_support=True).empty:
                time.sleep(loop_interval_secs)
                continue
            merged_repeat_df = load_merged_repeat_df(postgres_client,
                                                     market_code_combination,
                                                     admin_id,
                                                     acw_api,
                                                     logger,
                                                     table_name='repeat_trade')
            if len(merged_repeat_df) == 0:
                continue
            target_market_code, origin_market_code = market_code_combination.split(':')
            premium_df = get_premium_df(local_redis, fetched_info_dict, fetched_convert_rate_dict, target_market_code, origin_market_code, logger)
            if len(premium_df) == 0:
                time.sleep(loop_interval_secs)
                continue
            # check whether 'Tp_premium' values are all NaN or None
            if premium_df['tp_premium'].isnull().all():
                premium_df.loc[:, 'tp_premium'] = (premium_df['LS_premium'] + premium_df['SL_premium']) / 2
            
            simple_premium_df = premium_df[['base_asset','quote_asset','tp_premium']]
            handle_repeat_trade(postgres_client,
                                mongo_db_dict,
                                acw_api,
                                market_code_combination,
                                merged_repeat_df,
                                simple_premium_df,
                                logger,
                                logging_dir)
            # Reload the info_dict and convert_rate_dict
            fetched_info_dict = pickle.loads(local_redis.get_data('info_dict'))
            fetched_convert_rate_dict = {key.decode('utf-8'): float(value) for key, value in local_redis.hgetall_dict('convert_rate_dict').items()}
            time.sleep(loop_interval_secs)
        except Exception as e:
            title = f"Error in handle_repeat_trade_loop"
            full_content = f"Error in handle_repeat_trade_loop: {e}\n{traceback.format_exc()}"
            logger.error(full_content)
            acw_api.create_message_thread(admin_id, title, full_content)
            time.sleep(10)
            
def handle_repeat_trade(postgres_client,
                        mongo_db_dict,
                        acw_api,
                        market_code_combination,
                        merged_repeat_df,
                        simple_premium_df,
                        logger,
                        logging_dir,
                        print_update=False,
                        update_low_high_interval_secs=180):
    try:
        conn = postgres_client.pool.getconn()
        curr = conn.cursor(cursor_factory=extras.RealDictCursor)
        merged_df = merged_repeat_df.merge(simple_premium_df, on='base_asset')
        # merged_df = merged_df[merged_df['trade_switch'].isin([0, 1])]
        # df to deactivate
        repeat_limit_violated_df = merged_df[merged_df['repeat_limit_p']<=merged_df['tp_premium']]
        repeat_limit_violated_repeat_uuid_list = repeat_limit_violated_df['uuid_y'].to_list()
        repeat_num_limit_violated_df = merged_df[merged_df['repeat_num_limit']<=merged_df['auto_repeat_num']]
        repeat_num_limit_violated_repeat_uuid_list = repeat_num_limit_violated_df['uuid_y'].to_list()
        # Find users whose deposit balance is below 0
        # Fetch trade_config_df from redis
        trade_config_df = get_trade_config_df(market_code_combination)
        # Fetch balance df from ACW
        # user_balance_df = self.acw_api.get_deposit_balance()
        # user_balance_df.loc[:,'balance'] = user_balance_df['balance'].astype(float)
        # deposit_violated_user_balance_df = user_balance_df[user_balance_df['balance']<=0]
        # deposit_violated_user_uuid_list = deposit_violated_user_balance_df['user'].to_list()
        # Fetch users with negative balance from redis
        deposit_violated_user_uuid_list = get_users_with_negative_balance('negative_balance_users')
        
        deposit_violated_repeat_uuid_list = []
        for deposit_violated_user_uuid in deposit_violated_user_uuid_list:
            for trade_config_uuid in trade_config_df[trade_config_df['user']==deposit_violated_user_uuid]:
                deposit_violated_repeat_uuid_list += merged_df[merged_df['trade_config_uuid']==trade_config_uuid]['uuid_y'].to_list()
        
        violated_repeat_uuid_list = list(set(repeat_limit_violated_repeat_uuid_list + repeat_num_limit_violated_repeat_uuid_list + deposit_violated_repeat_uuid_list))
        validated_merged_df = merged_df[~merged_df['uuid_y'].isin(violated_repeat_uuid_list)]
        
        for violated_repeat_uuid in violated_repeat_uuid_list:
            status_str = ""
            if violated_repeat_uuid in repeat_limit_violated_repeat_uuid_list:
                if status_str == "":
                    status_str += "반복제한 프리미엄값 설정으로인한 꺼짐"
                else:
                    status_str += ", 반복제한 프리미엄값 설정으로인한 꺼짐"
            if violated_repeat_uuid in repeat_num_limit_violated_repeat_uuid_list:
                if status_str == "":
                    status_str += "반복제한횟수 설정으로인한 꺼짐"
                else:
                    status_str += ", 반복제한횟수 설정으로인한 꺼짐"
            if violated_repeat_uuid in deposit_violated_repeat_uuid_list:
                if status_str == "":
                    status_str += "잔액부족으로인한 꺼짐"
                else:
                    status_str += ", 잔액부족으로인한 꺼짐"
            # deactivate violated repeat_trade
            sql = "UPDATE repeat_trade SET last_updated_datetime = %s, auto_repeat_switch = 0, status = %s WHERE uuid = %s"
            val = (datetime.datetime.utcnow(), status_str, violated_repeat_uuid)
            curr.execute(sql, val)
            conn.commit()
            
        for row_tup in validated_merged_df.iterrows():
            # First check whether the record has pauto_num value
            row = row_tup[1]
            sql = "UPDATE repeat_trade SET last_updated_datetime = %s, auto_repeat_switch = 1, status=%s WHERE uuid = %s"
            val = (datetime.datetime.utcnow(), None, row['uuid_y'])
            curr.execute(sql, val)
            conn.commit()
            if row['trade_switch'] == 0: # 진입대기
                if pd.isnull(row['pauto_num']):
                    pass
                else:
                    if (datetime.datetime.utcnow() - row['last_updated_datetime_x'] < datetime.timedelta(seconds=update_low_high_interval_secs)):
                        continue
                    output_dict = get_pboundary(mongo_db_dict,
                                                market_code_combination,
                                                row['base_asset'],
                                                row['usdt_conversion'],
                                                row['kline_interval'],
                                                row['kline_num'],
                                                row['pauto_num'],
                                                logging_dir,
                                                draw_plot=False,
                                                return_dict=None)
                    low_to_apply, high_to_apply = output_dict['predicted_points']['y']
                    # apply it to the trade table
                    sql = "UPDATE trade SET last_updated_datetime = %s, low = %s, high = %s, trigger_switch = %s, trade_switch = %s WHERE uuid = %s"
                    val = (datetime.datetime.utcnow(), low_to_apply, high_to_apply, 1, 0, row['uuid_x'])
                    curr.execute(sql, val)
                    conn.commit()
                    
                    if print_update:
                        title = f"거래ID:{trade_uuid_to_display_id(local_redis, market_code_combination, row['uuid_x'], logger)} 진입값 탈출값 업데이트"
                        full_content = title
                        full_content += f"\n{row['base_asset']}/{row['quote_asset']} 진입값과 탈출값이 업데이트되었습니다."
                        full_content += f"\n진입값: {low_to_apply}, 탈출값: {high_to_apply}"
                        acw_api.create_message_thread(row['telegram_id'], title, full_content, 'INFO')
                
            elif row['trade_switch'] == 1: # 탈출완료
                if pd.isnull(row['pauto_num']):
                    # read the trade log based on the uuid_x from trade_log table
                    sql = "SELECT * FROM trade_log WHERE uuid = %s"
                    val = (row['uuid_x'],)
                    curr.execute(sql, val)
                    trade_log_df = pd.DataFrame(curr.fetchall())
                    if len(trade_log_df) == 0:
                        # raise error
                        postgres_client.pool.putconn(conn, close=True)
                        raise Exception(f"trade_log_df is empty for trade uuid: {row['uuid_x']}")
                    low_to_apply = trade_log_df['low'].iloc[0]
                    high_to_apply = trade_log_df['high'].iloc[0]
                    # apply it to the trade table
                    sql = "UPDATE trade SET last_updated_datetime = %s, low = %s, high = %s, trigger_switch = %s, trade_switch = %s, status = %s WHERE uuid = %s"
                    val = (datetime.datetime.utcnow(), low_to_apply, high_to_apply, 1, 0, None, row['uuid_x'])
                    curr.execute(sql, val)
                    conn.commit()
                else:
                    output_dict = get_pboundary(mongo_db_dict,
                                                market_code_combination,
                                                row['base_asset'],
                                                row['usdt_conversion'],
                                                row['kline_interval'],
                                                row['kline_num'],
                                                row['pauto_num'],
                                                logging_dir,
                                                draw_plot=False,
                                                return_dict=None)
                    low_to_apply, high_to_apply = output_dict['predicted_points']['y']
                    # apply it to the trade table
                    sql = "UPDATE trade SET last_updated_datetime = %s, low = %s, high = %s, trigger_switch = %s, trade_switch = %s, status = %s WHERE uuid = %s"
                    val = (datetime.datetime.utcnow(), low_to_apply, high_to_apply, 1, 0, None, row['uuid_x'])
                    curr.execute(sql, val)
                    conn.commit()
                
                title = f"거래ID:{trade_uuid_to_display_id(local_redis, market_code_combination, row['uuid_x'], logger)} 자동거래 재등록"
                full_content = title
                full_content += f"\n{row['base_asset']}/{row['quote_asset']} 자동거래가 탈출완료되어 자동거래를 재등록합니다."
                acw_api.create_message_thread(row['telegram_id'], title, full_content, 'INFO')
        postgres_client.pool.putconn(conn, close=True)
    except Exception as e:
        logger.error(f"Error in handle_repeat_trade: {e}\n{traceback.format_exc()}")
        # put the connection back to the pool
        postgres_client.pool.putconn(conn, close=True)
        raise e