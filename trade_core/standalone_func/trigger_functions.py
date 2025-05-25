import time
import json
import traceback
import datetime
import pandas as pd
import aiohttp
import asyncio
from etc.db_handler.mongodb_client import InitDBClient as InitMongoDBClient
from etc.db_handler.postgres_client import InitDBClient as InitPostgresDBClient
from exchange_plugin.integrated_plug import UserExchangeAdaptor
from etc.utils import get_trade_config_df, get_trade_df, get_users_with_negative_balance
from loggers.logger import TradeCoreLogger
from psycopg2 import extras
from threading import Thread
from standalone_func.premium_data_generator import get_premium_df
from standalone_func.uuid_converter import trade_uuid_to_display_id
from standalone_func.data_process import get_pboundary
from standalone_func.store_exchange_status import fetch_market_servercheck
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
    logger.info(f"postgres client has been initiated for {market_code_combination} | trade_support: {trade_support}")
    
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
        
    # Initialize convert_rate_dict
    while True:
        fetched_convert_rate_dict = local_redis.hgetall_dict('convert_rate_dict')
        if fetched_convert_rate_dict:
            fetched_convert_rate_dict = {key.decode('utf-8'): float(value) for key, value in fetched_convert_rate_dict.items()}
            break
        logger.info("convert_rate_dict is not ready yet. Waiting for 1 second...")
        time.sleep(1)
        
    # Loop Thread for saving servercheck status
    target_market_code, origin_market_code = market_code_combination.split(':')
    between_futures = True if 'SPOT' not in target_market_code and 'SPOT' not in origin_market_code else False
    target_market_servercheck = False
    origin_market_servercheck = False
    def save_servercheck_status():
        logger.info(f"start_trigger_loop|trade_support: {trade_support}|target_market_code:{target_market_code}, origin_market_code:{origin_market_code}, save_servercheck_status thread has started.")
        nonlocal target_market_servercheck, origin_market_servercheck
        while True:
            try:
                target_market_servercheck = fetch_market_servercheck(target_market_code)
                origin_market_servercheck = fetch_market_servercheck(origin_market_code)
                time.sleep(1)
            except Exception as e:
                logger.error(f"start_trigger_loop|trade_support: {trade_support}|target_market_code:{target_market_code}, origin_market_code:{origin_market_code}, Error in save_servercheck_status: {traceback.format_exc()}")
                time.sleep(3)
    save_servercheck_status_thread = Thread(target=save_servercheck_status, daemon=True)
    save_servercheck_status_thread.start()
    
    while True:
        try:
            if target_market_servercheck or origin_market_servercheck:
                logger.info(f"start_trigger_loop|trade_support: {trade_support}|target_market_code:{target_market_code}, origin_market_code:{origin_market_code}, has been skipped due to server check.")
                time.sleep(60)
                continue
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
            
            premium_df = get_premium_df(local_redis, fetched_convert_rate_dict, target_market_code, origin_market_code, logger)
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
                    if between_futures:
                        sql = f"""
                            UPDATE {table_name}
                            SET trigger_switch = 1,
                                trade_switch = CASE
                                    WHEN trade_switch IN (-1, 0) THEN 3
                                    ELSE trade_switch
                                END
                            WHERE uuid IN ({high_break_placeholders});
                            """
                    else:
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
                high_break(high_break_trade_df, user_exchange_adaptor, market_code_combination, trade_support, admin_id, acw_api, between_futures, logger)

            if not low_break_trade_df.empty:
                low_break_trigger_uuid_list = low_break_trade_df['uuid'].to_list()
                low_break_placeholders = ', '.join(['%s'] * len(low_break_trigger_uuid_list))
                low_break_params = tuple(low_break_trigger_uuid_list)
                # UPDATE database
                if trade_support:
                    if between_futures:
                        sql = f"""
                            UPDATE {table_name}
                            SET trigger_switch = 0,
                                trade_switch = CASE
                                    WHEN trade_switch IN (-1, 0) THEN 3
                                    ELSE trade_switch
                                END
                            WHERE uuid IN ({low_break_placeholders});
                            """
                    else:
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
                low_break(low_break_trade_df, user_exchange_adaptor, market_code_combination, trade_support, admin_id, acw_api, between_futures, logger)
            # Reload convert_rate_dict
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
            
def high_break(high_break_trade_df, user_exchange_adaptor, market_code_combination, trade_support, admin_id, acw_api, between_futures=False, logger=None):
    high_str = '상방' if between_futures else '탈출'
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
                msg_content += f"현재 SL:{round(row['SL_premium_value'], 3)}, 설정된 {high_str}값: {row['high']}\n"
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
        
def low_break(low_break_trade_df, user_exchange_adaptor, market_code_combination, trade_support, admin_id, acw_api, between_futures=False, logger=None):
    low_str = '하방' if between_futures else '진입'
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
                msg_content += f"현재 LS:{round(row['LS_premium_value'], 3)}, 설정된 {low_str}값: {row['low']}\n"
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
    
    # Initialize convert_rate_dict
    while True:
        fetched_convert_rate_dict = local_redis.hgetall_dict('convert_rate_dict')
        if fetched_convert_rate_dict:
            fetched_convert_rate_dict = {key.decode('utf-8'): float(value) for key, value in fetched_convert_rate_dict.items()}
            break
        logger.info("convert_rate_dict is not ready yet. Waiting for 1 second...")
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
            premium_df = get_premium_df(local_redis, fetched_convert_rate_dict, target_market_code, origin_market_code, logger)
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
            # Reload convert_rate_dict
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
        target_market_code, origin_market_code = market_code_combination.split(':')
        between_futures = True if 'SPOT' not in target_market_code and 'SPOT' not in origin_market_code else False
        conn = postgres_client.pool.getconn()
        curr = conn.cursor(cursor_factory=extras.RealDictCursor)
        merged_df = merged_repeat_df.merge(simple_premium_df, on='base_asset')
        # merged_df = merged_df[merged_df['trade_switch'].isin([0, 1])]
        # df to deactivate
        if between_futures:
            repeat_limit_violated_repeat_uuid_list = []
        else:
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
                if pd.isnull(row['pauto_num']) or between_futures:
                    continue
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
                    
                    # apply it to the trade_log table
                    sql = "UPDATE trade_log SET last_updated_datetime = %s, low = %s, high = %s WHERE trade_uuid = %s"
                    val = (datetime.datetime.utcnow(), low_to_apply, high_to_apply, row['uuid_x'])
                    curr.execute(sql, val)
                    conn.commit()
                    
                    if print_update:
                        title = f"거래ID:{trade_uuid_to_display_id(local_redis, market_code_combination, row['uuid_x'], logger)} 진입값 탈출값 업데이트"
                        full_content = title
                        full_content += f"\n{row['base_asset']}/{row['quote_asset']} 진입값과 탈출값이 업데이트되었습니다."
                        full_content += f"\n진입값: {low_to_apply}, 탈출값: {high_to_apply}"
                        acw_api.create_message_thread(row['telegram_id'], title, full_content, 'INFO')
                
            elif row['trade_switch'] == 1: # 탈출완료
                if pd.isnull(row['pauto_num']) or between_futures:
                    # read the trade log based on the uuid_x from trade_log table
                    sql = "SELECT * FROM trade_log WHERE trade_uuid = %s"
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
                    val = (datetime.datetime.utcnow(), low_to_apply, high_to_apply, None if between_futures else 1, 0, None, row['uuid_x'])
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
    
async def async_create_trade(row, admin_id, acw_api, logger):
    try:
        api_url = "http://trade-core-api:8000/trades/"
        trade_data = {
            "trade_config_uuid": str(row['trade_config_uuid']),
            "base_asset": row['base_asset'],
            "usdt_conversion": False,  # Default value, modify based on your requirements
            "low": float(row['low']),
            "high": float(row['high']),
            "trade_capital": float(row['trade_capital']),
            "trade_switch": 0,
            "trigger_scanner_uuid": str(row['uuid'])
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=trade_data) as response:
                if response.status == 201:
                    response_data = await response.json()
                    logger.info(f"Successfully created trade from trigger scanner: {response_data['uuid']}")
                    return response_data
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to create trade: {error_text}")
                    title = f"Error in async_create_trade"
                    full_content = f"{title}: {error_text}"
                    acw_api.create_message_thread(admin_id, title, full_content, 'ERROR')
                    return None
    except Exception as e:
        logger.error(f"Error in async_create_trade: {e}\n{traceback.format_exc()}")
        title = f"Error in async_create_trade"
        full_content = f"{title}: {e}\n{traceback.format_exc()}"
        acw_api.create_message_thread(admin_id, title, full_content, 'ERROR')
        return None

def start_trigger_scanner_loop(
    market_code_combination,
    postgres_db_dict,
    admin_id,
    acw_api,
    logging_dir,
    table_name='trigger_scanner',
    users_with_negative_banace_redis_key_name='negative_balance_users',
    loop_interval_secs=5
):
    logger = TradeCoreLogger("start_trigger_scanner_loop", logging_dir).logger
    logger.info(f"start_trigger_scanner_loop started for {market_code_combination} | | table_name: {table_name} | loop_interval_secs: {loop_interval_secs}")
    target_market_code, origin_market_code = market_code_combination.split(':')
    postgres_client = InitPostgresDBClient(**{**postgres_db_dict, 'database': 'trade_core'})
    conn = postgres_client.pool.getconn()
    curr = conn.cursor(cursor_factory=extras.RealDictCursor)
    logger.info(f"postgres client for start_trigger_scanner_loop has been initiated for {market_code_combination}")
    
     # Loop Thread for saving servercheck status
    target_market_servercheck = False
    origin_market_servercheck = False
    def save_servercheck_status():
        logger.info(f"start_trigger_scanner_loop|target_market_code:{target_market_code}, origin_market_code:{origin_market_code}, save_servercheck_status thread has started.")
        nonlocal target_market_servercheck, origin_market_servercheck
        while True:
            try:
                target_market_servercheck = fetch_market_servercheck(target_market_code)
                origin_market_servercheck = fetch_market_servercheck(origin_market_code)
                time.sleep(1)
            except Exception as e:
                logger.error(f"start_trigger_scanner_loop|target_market_code:{target_market_code}, origin_market_code:{origin_market_code}, Error in save_servercheck_status: {traceback.format_exc()}")
                time.sleep(3)
    save_servercheck_status_thread = Thread(target=save_servercheck_status, daemon=True)
    save_servercheck_status_thread.start()
    
    while True:
        time.sleep(loop_interval_secs)
        try:
        
            if target_market_servercheck or origin_market_servercheck:
                logger.info(f"start_trigger_scanner_loop|target_market_code:{target_market_code}, origin_market_code:{origin_market_code}, has been skipped due to server check.")
                time.sleep(60)
                continue
            
            # Initialize convert_rate_dict
            while True:
                fetched_convert_rate_dict = local_redis.hgetall_dict('convert_rate_dict')
                if fetched_convert_rate_dict:
                    fetched_convert_rate_dict = {key.decode('utf-8'): float(value) for key, value in fetched_convert_rate_dict.items()}
                    break
                logger.info("convert_rate_dict is not ready yet. Waiting for 1 second...")
                time.sleep(1)
            
            # Initialize fundingrate_df
            while True:
                fundingrate_df = local_redis.get_fundingrate_df(market_code_combination, origin_market_code)
                if not fundingrate_df.empty:
                    break
                logger.info("fundingrate_df is not ready yet. Waiting for 1 second...")
                time.sleep(1)
                
            users_with_negative_balance = get_users_with_negative_balance(users_with_negative_banace_redis_key_name)
            # Load trigger_scanner table
            if not users_with_negative_balance:
                sql = """
                SELECT trigger_scanner.*, trade_config.telegram_id, trade_config.target_market_code, trade_config.origin_market_code
                FROM trigger_scanner
                JOIN trade_config ON trigger_scanner.trade_config_uuid = trade_config.uuid
                WHERE trade_config.target_market_code=%s AND trade_config.origin_market_code=%s
                AND (trigger_scanner.max_repeat_num IS NULL OR trigger_scanner.curr_repeat_num < trigger_scanner.max_repeat_num)
                """
                val = (target_market_code, origin_market_code)
            else:
                sql = """
                SELECT trigger_scanner.*, trade_config.telegram_id, trade_config.target_market_code, trade_config.origin_market_code
                FROM trigger_scanner
                JOIN trade_config ON trigger_scanner.trade_config_uuid = trade_config.uuid
                WHERE trade_config.target_market_code=%s AND trade_config.origin_market_code=%s AND trade_config.user NOT IN %s
                AND (trigger_scanner.max_repeat_num IS NULL OR trigger_scanner.curr_repeat_num < trigger_scanner.max_repeat_num)
                """
                val = (target_market_code, origin_market_code, tuple(users_with_negative_balance))
                
            curr.execute(sql, val)
            trigger_scanner_df = pd.DataFrame(curr.fetchall())
            if not trigger_scanner_df.empty:
                # Ensure 'last_updated_datetime' is in datetime format
                trigger_scanner_df['last_updated_datetime'] = pd.to_datetime(trigger_scanner_df['last_updated_datetime'])
                
                # Get current datetime - always use UTC for consistency
                now = pd.Timestamp.now(tz='UTC')
                
                # Check if datetime has timezone info
                has_tz = False
                if not trigger_scanner_df['last_updated_datetime'].isna().all():
                    sample_dt = trigger_scanner_df['last_updated_datetime'].iloc[0]
                    has_tz = hasattr(sample_dt, 'tz') and sample_dt.tz is not None
                
                if has_tz:
                    # If timestamps have timezone, normalize to UTC
                    last_updated_utc = trigger_scanner_df['last_updated_datetime'].dt.tz_convert('UTC')
                else:
                    # If naive timestamps, assume they're in UTC
                    last_updated_utc = trigger_scanner_df['last_updated_datetime'].dt.tz_localize('UTC')
                
                # Calculate next update times
                next_update_times = last_updated_utc + pd.to_timedelta(trigger_scanner_df['repeat_term_secs'], unit='s')
                
                # Filter records where next update time is before current time OR curr_repeat_num is 0 (first execution)
                time_condition = next_update_times < now
                first_execution_condition = trigger_scanner_df['curr_repeat_num'] == 0
                logger.info(f"first_execution_condition: {first_execution_condition}")
                logger.info(f"time_condition: {time_condition}")
                logger.info(f"trigger_scanner_df before filtering: {trigger_scanner_df}")
                trigger_scanner_df = trigger_scanner_df[time_condition | first_execution_condition]
                logger.info(f"trigger_scanner_df after filtering: {trigger_scanner_df}")
            if not trigger_scanner_df.empty:
                premium_df = get_premium_df(local_redis, fetched_convert_rate_dict, target_market_code, origin_market_code, logger)
                merged_premium_df = premium_df.merge(fundingrate_df[['base_asset','funding_rate','funding_time']], on='base_asset')
                cross_merged_df = pd.merge(merged_premium_df, trigger_scanner_df, how='cross')
                
                # 컬럼을 숫자형으로 변환 (None -> np.nan, 변환 불가 시 np.nan)
                cross_merged_df['min_origin_funding_rate'] = pd.to_numeric(cross_merged_df['min_origin_funding_rate'], errors='coerce')

                # atp 관련 컬럼도 동일하게 처리 (필요한 경우)
                cross_merged_df['min_target_atp'] = pd.to_numeric(cross_merged_df['min_target_atp'], errors='coerce')

                # 1. 기본 LS_premium 조건
                condition_ls_premium = cross_merged_df['LS_premium'] < cross_merged_df['low']
                # 2. Funding Rate 조건
                condition_funding_rate = (
                    cross_merged_df['min_origin_funding_rate'].isnull() |
                    (cross_merged_df['funding_rate'] >= cross_merged_df['min_origin_funding_rate'])
                )
                # 3. ATP 조건
                condition_atp = (
                    cross_merged_df['min_target_atp'].isnull() |
                    (cross_merged_df['atp24h'] > cross_merged_df['min_target_atp'])
                )
                # 모든 조건을 결합 (AND 연산)
                final_condition = condition_ls_premium & condition_funding_rate & condition_atp
                filtered_df = cross_merged_df[final_condition].copy()
                
                if not filtered_df.empty:
                    # uuid로 그룹화한 후, 각 그룹에서 LS_premium이 최소값인 행의 인덱스를 찾음
                    idx_min_ls_premium = filtered_df.groupby('uuid')['LS_premium'].idxmin()

                    # 찾은 인덱스를 사용하여 해당 행들을 원래 DataFrame에서 추출
                    result_df = filtered_df.loc[idx_min_ls_premium]
                else:
                    result_df = pd.DataFrame(columns=filtered_df.columns) # 빈 DataFrame 처리
                    
                if not result_df.empty:
                    # Update last_updated_datetime and curr_repeat_num for multiple rows
                    uuid_list = result_df['uuid'].tolist()
                    sql = "UPDATE trigger_scanner SET last_updated_datetime = %s, curr_repeat_num = curr_repeat_num + 1 WHERE uuid IN %s"
                    val = (datetime.datetime.utcnow(), tuple(uuid_list))
                    curr.execute(sql, val)
                    conn.commit()

                    # Create trades asynchronously for rows in result_df
                    async def process_trades():
                        tasks = []
                        for _, row in result_df.iterrows():
                            task = asyncio.create_task(async_create_trade(row, admin_id, acw_api, logger))
                            tasks.append(task)
                        
                        # Wait for all API calls to complete
                        results = await asyncio.gather(*tasks, return_exceptions=True)
                        return results
                    
                    # Run the async function in a synchronous context
                    loop = asyncio.get_event_loop()
                    try:
                        trade_results = loop.run_until_complete(process_trades())
                        logger.info(f"Created {len([r for r in trade_results if r is not None])} trades from trigger scanner")
                    except Exception as e:
                        logger.error(f"Error processing trades: {e}\n{traceback.format_exc()}")
                    
                # Send message to telegram for testing
                for row_tup in result_df.iterrows():
                    row = row_tup[1]
                    title = f"Trigger Scanner Loop"
                    full_content = f"{market_code_combination}의 {row['base_asset']} 프리미엄 하향돌파"
                    full_content += f"\n현재프리미엄: {row['LS_premium']}, Low값: {row['low']}, High값: {row['high']}"
                    full_content += f"\n진입자산: {row['trade_capital']}"
                    full_content += f"\n설정오리진최소펀딩률: {round(row['min_origin_funding_rate']*100, 4)}%"
                    full_content += f"\n현재펀딩률: {round(row['funding_rate']*100, 4)}%"
                    full_content += f"\n설정최소타겟거래량: {round(row['min_target_atp']/1000000000, 3)} 억"
                    full_content += f"\n현재타겟거래량: {round(row['atp24h']/1000000000, 3)} 억"
                    full_content += f"\n현재반복횟수: {row['curr_repeat_num'] + 1}회"
                    full_content += f"\n최대반복횟수: {row['max_repeat_num']}회"
                    full_content += f"\n반복주기: {row['repeat_term_secs']}초"
                    full_content += f"\n마지막 업데이트: {row['last_updated_datetime']}"
                    acw_api.create_message_thread(row['telegram_id'], title, full_content, 'INFO')
        
        except Exception as e:
            title = f"Error in start_trigger_scanner_loop"
            full_content = f"Error in start_trigger_scanner_loop: {e}\n{traceback.format_exc()}"
            logger.error(f"Error in start_trigger_scanner_loop: {e}\n{traceback.format_exc()}")
            acw_api.create_message_thread(admin_id, title, full_content, 'ERROR')
            time.sleep(10)

    
def fetch_fundingrate_loop(admin_id, acw_api, mongo_db_dict, market_code_combination, market_code, logging_dir):
    logger = TradeCoreLogger("fetch_fundingrate_loop", logging_dir).logger
    logger.info(f"fetch_fundingrate_loop started for {market_code_combination}|{market_code}")
    target_market_code, origin_market_code = market_code_combination.split(':')
    if 'SPOT' in target_market_code and 'SPOT' in origin_market_code:
        raise Exception("Between SPOT markets is not supported for fundingrate")
    elif 'SPOT' not in target_market_code and 'SPOT' not in origin_market_code:
        raise Exception("Between futures markets is not supported for fundingrate")        
        # Initialize convert_rate_dict
    while True:
        fetched_convert_rate_dict = local_redis.hgetall_dict('convert_rate_dict')
        if fetched_convert_rate_dict:
            fetched_convert_rate_dict = {key.decode('utf-8'): float(value) for key, value in fetched_convert_rate_dict.items()}
            break
        logger.info("convert_rate_dict is not ready yet. Waiting for 1 second...")
        time.sleep(1)
    while True:
        try:
            # Reload convert_rate_dict
            fetched_convert_rate_dict = {key.decode('utf-8'): float(value) for key, value in local_redis.hgetall_dict('convert_rate_dict').items()}
            fetch_fundingrate_and_save_to_redis(mongo_db_dict, market_code_combination, market_code, fetched_convert_rate_dict, logger)
            time.sleep(60)
        except Exception as e:
            logger.error(f"Error in fetch_fundingrate_loop: {e}\n{traceback.format_exc()}")
            title = f"Error in fetch_fundingrate_loop"
            full_content = f"Error in fetch_fundingrate_loop: {e}\n{traceback.format_exc()}"
            acw_api.create_message_thread(admin_id, title, full_content, 'ERROR')
            time.sleep(60)

def fetch_fundingrate_and_save_to_redis(mongo_db_dict, market_code_combination, market_code, convert_rate_dict, logger, ex=180):
    client = InitMongoDBClient(**mongo_db_dict)
    conn = client.get_conn()
    target_market_code, origin_market_code = market_code_combination.split(':')
    premium_df = get_premium_df(local_redis, convert_rate_dict, target_market_code, origin_market_code, logger)
    
    base_asset_list_to_fetch = premium_df['base_asset'].unique().tolist()
        
    redis_key_name = f'fundingrate|{market_code_combination}|{market_code}'
    market_code_without_quote_asset, quote_asset = market_code.split('/')
    exchange = market_code_without_quote_asset.split('_')[0]
    market_type = market_code_without_quote_asset.replace(exchange + '_', '')

    fundingrate_db_name = f'{exchange}_fundingrate'
    fundingrate_collection_name = market_type
    # Fetch all
    db = conn[fundingrate_db_name]
    collection = db[fundingrate_collection_name]
    cursor = collection.aggregate([
        {
            '$match': {
                'base_asset': {'$in': base_asset_list_to_fetch},
                'quote_asset': quote_asset,
                'perpetual': True
            }
        },
        {
            '$sort': {'funding_time': -1}
        },
        {
            '$group': {
                '_id': '$base_asset',
                'doc': {'$first': '$$ROOT'}
            }
        },
        {
            '$replaceRoot': {'newRoot': '$doc'}
        },
        {
            '$project': {'_id': 0}
        }
    ])
    fundingrate_df = pd.DataFrame(list(cursor))
    conn.close()
    local_redis.set_data(redis_key_name, pickle.dumps(fundingrate_df), ex=ex)
    return fundingrate_df