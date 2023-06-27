import sys
import os
import pandas as pd
from threading import Thread
import datetime
import time
import traceback
import pymysql

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from etc.register_msg import register
from loggers.logger import KimpBotLogger

# Connect to DB
def connect_db(database, host, port, user, passwd):
    conn = pymysql.connect(
        host = host,
        port = port,
        user = user,
        passwd = passwd,
        database = database
    )
    curr = conn.cursor(pymysql.cursors.DictCursor)
    return conn,curr

class InitKimpCoreMonitor:
    def __init__(self, logging_dir, node, admin_id, prod_n, remote_db_dict, get_kimp_df_func, get_dollar_dict_func, monitor_bot_token, monitor_bot_url):
        self.node = node
        self.admin_id = admin_id
        # self.helper_id_list = [1007931055, 1976936977, 1100166438] # 영익, 준우, 홍갑
        self.helper_id_list = [1007931055]
        self.prod_n = prod_n
        self.logging_dir = logging_dir
        self.remote_db_dict = remote_db_dict
        self.monitor_bot_token = monitor_bot_token
        self.monitor_bot_url = monitor_bot_url
        self.kimp_core_monitor_logger = KimpBotLogger("kimp_core_monitor", logging_dir).logger
        self.get_kimp_df_func = get_kimp_df_func
        self.get_dollar_dict_func = get_dollar_dict_func
        self.websocket_time_error_counter = 0
        self.dollar_time_error_counter = 0 # For Master node
        self.kline_date_error_counter = 0 # For Master node # Monitoring only 1min kline

    def loop_monitor_websocket_time(self, threshold_minutes, loop_secs=3):
        self.kimp_core_monitor_logger.info(f"loop_monitor_websocket_time started.")
        title = '웹소켓 거래가격 수신이 느립니다.. loop_monitor_websocket_time.. timestamp slow detected..'
        while True:
            try:
                if self.websocket_time_error_counter >= 10:
                    register(self.monitor_bot_token, self.monitor_bot_url, [self.admin_id]+self.helper_id_list, self.node, 'error', title, f'Restarting kimp_bot.. websocket_time_error_counter: {self.websocket_time_error_counter}')
                    os.system(os.getcwd() + '/restart.sh')
                kimp_time_df = self.get_kimp_df_func()[['symbol','upbit_timestamp', 'binance_event_time']]
                total_coin_num = len(kimp_time_df)
                kimp_time_df.loc[:, 'upbit_timestamp'] = pd.to_datetime(kimp_time_df['upbit_timestamp'], unit='ms')
                kimp_time_df.loc[:, 'binance_event_time'] = pd.to_datetime(kimp_time_df['binance_event_time'], unit='ms')
                upbit_slow_df = kimp_time_df[kimp_time_df['upbit_timestamp'] <= (datetime.datetime.now()-datetime.timedelta(hours=9)-datetime.timedelta(minutes=threshold_minutes))]
                upbit_slow_num = len(upbit_slow_df)
                upbit_slow_symbols = upbit_slow_df['symbol'].to_list()

                binance_slow_df = kimp_time_df[kimp_time_df['binance_event_time'] <= (datetime.datetime.now()-datetime.timedelta(hours=9)-datetime.timedelta(minutes=threshold_minutes))]
                binance_slow_num = len(binance_slow_df)
                binance_slow_symbols = binance_slow_df['symbol'].to_list()

                if upbit_slow_num >= total_coin_num // self.prod_n or binance_slow_num >= total_coin_num // self.prod_n:
                    content = f"Slow min threashold: {threshold_minutes}\n"
                    content += f"upbit_slow_num: {upbit_slow_num}\n"
                    content += f"binance_slow_num: {binance_slow_num}\n"
                    content += f"upbit_slow_symbols: {upbit_slow_symbols}\n"
                    content += f"binance_slow_symbols: {binance_slow_symbols}"
                    if len(content) > 1000:
                        content = content[:1000]
                    register(self.monitor_bot_token, self.monitor_bot_url, [self.admin_id]+self.helper_id_list, self.node, 'monitor', title, content)
                    self.websocket_time_error_counter += 1
                else:
                    self.websocket_time_error_counter = 0
                time.sleep(loop_secs)
            except:
                self.websocket_time_error_counter += 1
                self.kimp_core_monitor_logger.error(f"loop_monitor_websocket_time|{traceback.format_exc()}")
                register(self.monitor_bot_token, self.monitor_bot_url, self.admin_id, self.node, 'error', 'Error occured in loop_monitor_websocket_time', str(traceback.format_exc())[:500])
                time.sleep(loop_secs)

    def loop_monitor_dollar_time(self, threshold_minutes, loop_secs=3):
        self.kimp_core_monitor_logger.info(f"loop_monitor_dollar_time started.")
        title = '달러가격 수신이 딜레이 되고 있습니다.. loop_minitor_dollar_time.. timestamp slow detected..'
        while True:
            try:
                if self.dollar_time_error_counter >= 10 and 'master' in self.node:
                    register(self.monitor_bot_token, self.monitor_bot_url, [self.admin_id]+self.helper_id_list, self.node, 'error', title, f'Restarting kimp_bot.. dollar_time_error_counter: {self.dollar_time_error_counter}')
                    os.system(os.getcwd() + '/restart.sh')
                dollar_dict = self.get_dollar_dict_func()
                dollar_last_updated_datetime = dollar_dict['last_updated_time']
                if dollar_last_updated_datetime <= datetime.datetime.now() - datetime.timedelta(minutes=threshold_minutes):
                    content = f"Dollar update stopped..\n"
                    content += f"Dollar Last Updated time: {dollar_last_updated_datetime}\n"
                    content += f"Now Server time: {datetime.datetime.now()}"
                    # TEST
                    content += f"self.dollar_time_error_counter: {self.dollar_time_error_counter}"
                    content += f"self.dollar_time_error_counter >= 10 and 'master' in self.node: {self.dollar_time_error_counter >= 10 and 'master' in self.node}"
                    content += f"self.node: {self.node}"
                    register(self.monitor_bot_token, self.monitor_bot_url, [self.admin_id]+self.helper_id_list, self.node, 'monitor', title, content)
                    self.dollar_time_error_counter += 1
                else:
                    self.dollar_time_error_counter = 0
                time.sleep(loop_secs)
            except:
                self.kimp_core_monitor_logger.error(f"loop_monitor_dollar_time|{traceback.format_exc()}")
                register(self.monitor_bot_token, self.monitor_bot_url, self.admin_id, self.node, 'error', 'Error occured in loop_monitor_dollar_time', str(traceback.format_exc())[:500])
                time.sleep(loop_secs)

    def loop_monitor_kline_data(self, threshold_minutes, loop_secs=2.5):
        time.sleep(90)
        self.kimp_core_monitor_logger.info(f"loop_monitor_kline_data started.")
        title = "차트가 업데이트되고 있지 않습니다. kline data is not being updated."
        while True:
            try:
                if self.kline_date_error_counter >= 20 and 'master' in self.node:
                    register(self.monitor_bot_token, self.monitor_bot_url, [self.admin_id]+self.helper_id_list, self.node, 'error', title, f'Restarting kimp_bot.. kline_date_error_counter: {self.kline_date_error_counter}')
                    os.system(os.getcwd() + '/restart.sh')
                time.sleep(loop_secs)
                # 1min
                conn, curr = connect_db('coin_kimp_kline', self.remote_db_dict['host'], self.remote_db_dict['port'], self.remote_db_dict['user'], self.remote_db_dict['passwd'])
                curr.execute("""SELECT datetime_kst FROM upbit_binancef_BTC WHERE period=1 ORDER BY id DESC LIMIT 1""")
                fetched = curr.fetchall()
                conn.close()
                kline_1m_last_updated_datetime = fetched[0]['datetime_kst']
                if kline_1m_last_updated_datetime < datetime.datetime.now() - datetime.timedelta(minutes=threshold_minutes):
                    content = f"1분봉 차트 마지막 업데이트 시각 kline_1m_last_updated_datetime: {kline_1m_last_updated_datetime}\n"
                    content += f"datetime.datetime.now(): {datetime.datetime.now()}\n"
                    content += f"threshold_minutes: {threshold_minutes}"
                    # TEST
                    content += f"self.kline_data_error_counter: {self.kline_date_error_counter}"
                    content += f"self.kline_date_error_counter >= 20 and 'master' in self.node: {self.kline_date_error_counter >= 20 and 'master' in self.node}"
                    content += f"self.node: {self.node}"
                    register(self.monitor_bot_token, self.monitor_bot_url, [self.admin_id]+self.helper_id_list, self.node, 'monitor', title, content)
                    self.kline_date_error_counter += 1
                else:
                    self.kline_date_error_counter = 0
                # 5min
                conn, curr = connect_db('coin_kimp_kline', self.remote_db_dict['host'], self.remote_db_dict['port'], self.remote_db_dict['user'], self.remote_db_dict['passwd'])
                curr.execute("""SELECT datetime_kst FROM upbit_binancef_BTC WHERE period=5 ORDER BY id DESC LIMIT 1""")
                fetched = curr.fetchall()
                conn.close()
                kline_5m_last_updated_datetime = fetched[0]['datetime_kst']
                if kline_5m_last_updated_datetime < datetime.datetime.now() - datetime.timedelta(minutes=threshold_minutes) - datetime.timedelta(minutes=5*3):
                    content = f"5분봉 차트 마지막 업데이트 시각 kline_5m_last_updated_datetime: {kline_5m_last_updated_datetime}\n"
                    content += f"datetime.datetime.now(): {datetime.datetime.now()}\n"
                    content += f"threshold_minutes: {threshold_minutes}"
                    register(self.monitor_bot_token, self.monitor_bot_url, [self.admin_id]+self.helper_id_list, self.node, 'monitor', title, content)
                # 30min
                conn, curr = connect_db('coin_kimp_kline', self.remote_db_dict['host'], self.remote_db_dict['port'], self.remote_db_dict['user'], self.remote_db_dict['passwd'])
                curr.execute("""SELECT datetime_kst FROM upbit_binancef_BTC WHERE period=30 ORDER BY id DESC LIMIT 1""")
                fetched = curr.fetchall()
                conn.close()
                kline_30m_last_updated_datetime = fetched[0]['datetime_kst']
                if kline_30m_last_updated_datetime < datetime.datetime.now() - datetime.timedelta(minutes=threshold_minutes) - datetime.timedelta(minutes=30*2):
                    content = f"30분봉 차트 마지막 업데이트 시각 kline_30m_last_updated_datetime: {kline_30m_last_updated_datetime}\n"
                    content += f"datetime.datetime.now(): {datetime.datetime.now()}\n"
                    content += f"threshold_minutes: {threshold_minutes}"
                    register(self.monitor_bot_token, self.monitor_bot_url, [self.admin_id]+self.helper_id_list, self.node, 'monitor', title, content)
                # 60min
                conn, curr = connect_db('coin_kimp_kline', self.remote_db_dict['host'], self.remote_db_dict['port'], self.remote_db_dict['user'], self.remote_db_dict['passwd'])
                curr.execute("""SELECT datetime_kst FROM upbit_binancef_BTC WHERE period=60 ORDER BY id DESC LIMIT 1""")
                fetched = curr.fetchall()
                conn.close()
                kline_60m_last_updated_datetime = fetched[0]['datetime_kst']
                if kline_60m_last_updated_datetime < datetime.datetime.now() - datetime.timedelta(minutes=threshold_minutes) - datetime.timedelta(minutes=60*3):
                    content = f"60분봉 차트 마지막 업데이트 시각 kline_60m_last_updated_datetime: {kline_60m_last_updated_datetime}\n"
                    content += f"datetime.datetime.now(): {datetime.datetime.now()}\n"
                    content += f"threshold_minutes: {threshold_minutes}"
                    register(self.monitor_bot_token, self.monitor_bot_url, [self.admin_id]+self.helper_id_list, self.node, 'monitor', title, content)
                # 240min
                conn, curr = connect_db('coin_kimp_kline', self.remote_db_dict['host'], self.remote_db_dict['port'], self.remote_db_dict['user'], self.remote_db_dict['passwd'])
                curr.execute("""SELECT datetime_kst FROM upbit_binancef_BTC WHERE period=240 ORDER BY id DESC LIMIT 1""")
                fetched = curr.fetchall()
                conn.close()
                kline_240m_last_updated_datetime = fetched[0]['datetime_kst']
                if kline_240m_last_updated_datetime < datetime.datetime.now() - datetime.timedelta(minutes=threshold_minutes) - datetime.timedelta(minutes=240*3):
                    content = f"240분봉 차트 마지막 업데이트 시각 kline_240m_last_updated_datetime: {kline_240m_last_updated_datetime}\n"
                    content += f"datetime.datetime.now(): {datetime.datetime.now()}\n"
                    content += f"threshold_minutes: {threshold_minutes}"
                    register(self.monitor_bot_token, self.monitor_bot_url, [self.admin_id]+self.helper_id_list, self.node, 'monitor', title, content)

            except:
                try:
                    conn.close()
                except:
                    pass
                self.kimp_core_monitor_logger.error(f"loop_monitor_kline_data|{traceback.format_exc()}")
                register(self.monitor_bot_token, self.monitor_bot_url, self.admin_id, self.node, 'error', 'Error occured in loop_monitor_kline_data', str(traceback.format_exc())[:500])
                time.sleep(loop_secs)

    def start_loop_monitor_websocket_time(self, threshold_minutes=3):
        self.loop_monitor_websocket_time_thread = Thread(target=self.loop_monitor_websocket_time, args=(threshold_minutes,), daemon=True)
        self.loop_monitor_websocket_time_thread.start()

    def start_loop_monitor_dollar_time(self, threshold_minutes=2):
        self.loop_monitor_dollar_time_thread = Thread(target=self.loop_monitor_dollar_time, args=(threshold_minutes,), daemon=True)
        self.loop_monitor_dollar_time_thread.start()                

    def start_loop_monitor_kline_data(self, threshold_minutes=2):
        self.loop_monitor_kline_data_thread = Thread(target=self.loop_monitor_kline_data, args=(threshold_minutes,), daemon=True)
        self.loop_monitor_kline_data_thread.start()
