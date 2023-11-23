import os
import json
import sys
import argparse
import time

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from info_core import InitCore
# from monitor_engine.kimp_core_monitor import InitKimpCoreMonitor
from etc.register_monitor_msg import RegisterMonitorMsg
# from kline_generator.kline_core import InitKlineCore

class Dummy:
    def __init__(self):
        pass
    def kline_fetcher_proc_status(self):
        integrity_flag = True
        status_str = 'This is not a Master node. So, there is no kline_fetcher_proc_status.'
        return integrity_flag, status_str

def get_arguments():
    """
    Parsing arguments
    """
    current_file_dir = os.path.realpath(__file__)
    current_folder_dir = os.path.abspath(os.path.join(current_file_dir, os.pardir))
    logging_dir = f"{current_folder_dir}/loggers/logs/"

    parser = argparse.ArgumentParser()
    # parser.add_argument('--node', '-n', required=True, nargs=1, help='Specify a node name. Configuration will be done based on the node name.', dest='node')
    parser.add_argument('--proc_n', '-p', nargs=1, help='Specify a number of processes to handle websockets.', default=[1], dest='proc_n')
    parser.add_argument('--log', '-l', nargs=1, help='Specify a directory to save log files.', default=[logging_dir], dest='logging_dir')
    parser.add_argument('--config', '-c', nargs=1, help='Specify a directory of a config json file.', default=[current_folder_dir+"/info_core_config.json"], dest='config_dir')

    # node = parser.parse_args().node[0]
    proc_n = int(parser.parse_args().proc_n[0])
    logging_dir = parser.parse_args().logging_dir[0]
    config_dir = parser.parse_args().config_dir[0]
    # return node, proc_n, logging_dir, input_update_common_info_flag, config_dir
    return proc_n, logging_dir, config_dir

if __name__ == '__main__':
    # node, proc_n, logging_dir, input_update_common_info_flag, config_dir = get_arguments()
    proc_n, logging_dir, config_dir = get_arguments()
    with open(config_dir) as f:
        config = json.load(f)
    if not os.path.exists(logging_dir):
        os.mkdir(logging_dir)
    # if node not in config['node_settings'].keys():
    #     raise Exception(f"Node name should be the one of {list(config['node_settings'].keys())}")
    node = config['node']
    monitor_bot_name = config['monitor_setting']['monitor_bot']
    monitor_bot_token = config['telegram_bot_setting'][monitor_bot_name]
    monitor_bot_api_url = config['monitor_setting']['monitor_bot_api_url']
    admin_id_list = []
    admin_id = config['telegram_admin_id']['charlie1155']
    admin_id_list.append(admin_id)
    register_monitor_msg = RegisterMonitorMsg(monitor_bot_token, monitor_bot_api_url, admin_id, logging_dir)
    # For Test
    register_monitor_msg.register(admin_id, node, 'info', f"info_core_main|node:{node} has started.", content=None, code=None, sent_switch=0, send_counts=1, remark=None)
    # Read api keys
    exchange_api_key_dict = config['exchange_api_key']
    # enabled kline market settings
    enabled_market_klines = config['node_settings'][node]['enabled_market_klines']
    # total enabled market settings
    total_enabled_market_klines = []
    for each_market_code_list in config['node_settings'].values():
        total_enabled_market_klines += each_market_code_list['enabled_market_klines']

    # idle

    from telegram_bot_plugin.telegram_bot import InitTelegramBot
    from etc.db_handler.postgres_client import InitDBClient
    telegram_bot_name = config['node_settings'][node]['telegram_bot_name']
    if telegram_bot_name:
        telegram_bot_token = config['telegram_bot_setting'][telegram_bot_name]
    else:
        telegram_bot_token = None
    master_flag = config['node_settings'][node]['MASTER']
    db_dict = config['database_setting'][config['node_settings'][node]['db_settings']]
    
    # Initiate Kimp core (Websocket engine)
    core = InitCore(logging_dir, master_flag, proc_n, node, admin_id, register_monitor_msg, exchange_api_key_dict, enabled_market_klines, total_enabled_market_klines, db_dict)

    time.sleep(5)

    # Initiate TelegramBot with Trigger engine
    if master_flag:
        admin_telegram_bot = InitTelegramBot(telegram_bot_token, logging_dir, node, db_dict, core, register_monitor_msg, admin_id_list)
        admin_telegram_bot.updater.idle()
    else:
        while True:
            time.sleep(1)

