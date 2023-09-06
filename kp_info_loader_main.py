import os
import json
import sys
import argparse

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from kimp_bot_core import InitKimpCore
from monitor_engine.kimp_core_monitor import InitKimpCoreMonitor
from etc.register_monitor_msg import RegisterMonitorMsg

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
    parser.add_argument('--update_common_info', '-u', nargs=1, help='Whether to update common info data to the remote DB', default=[True], dest='update_common_info_flag')
    parser.add_argument('--redis_mode', '-r', nargs=1, help='Switch for redis mode used for Django', default=[False], dest='redis_mode')
    parser.add_argument('--log', '-l', nargs=1, help='Specify a directory to save log files.', default=[logging_dir], dest='logging_dir')
    parser.add_argument('--config', '-c', nargs=1, help='Specigy a directory of a config json file.', default=[current_folder_dir+"/kimp_bot_config.json"], dest='config_dir')

    # node = parser.parse_args().node[0]
    proc_n = int(parser.parse_args().proc_n[0])
    logging_dir = parser.parse_args().logging_dir[0]
    redis_mode = parser.parse_args().redis_mode[0]
    if type(redis_mode) == str:
        if redis_mode in ['true', 'True']:
            redis_mode = True
        elif redis_mode in ['false', 'False']:
            redis_mode = False
        else:
            raise Exception('redis_mode Error!. redis_mode must be either true or false.')
    input_update_common_info_flag = parser.parse_args().update_common_info_flag[0]
    if type(input_update_common_info_flag) == str:
        if input_update_common_info_flag in ['true', 'True']:
            input_update_common_info_flag = True
        elif input_update_common_info_flag in ['false', 'False']:
            input_update_common_info_flag = False
        else:
            raise Exception('update_common_info_flag Error!. update_common_info_flag must be either true or false.')
    config_dir = parser.parse_args().config_dir[0]
    # return node, proc_n, logging_dir, input_update_common_info_flag, config_dir
    return proc_n, logging_dir, redis_mode, input_update_common_info_flag, config_dir

if __name__ == '__main__':
    # node, proc_n, logging_dir, input_update_common_info_flag, config_dir = get_arguments()
    proc_n, logging_dir, redis_mode, input_update_common_info_flag, config_dir = get_arguments()
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
    admin_id = config['telegram_admin_id']['charlie1155']
    register_monitor_msg = RegisterMonitorMsg(monitor_bot_token, monitor_bot_api_url, admin_id)
    # Read api keys
    exchange_api_key_dict = config['exchange_api_key']
    # Exchange market settings
    enabled_markets_dict = config['enabled_markets']

    # idle
    # kimp_core.update_kimp_to_redis_thread.join()

    from telegram_bot_plugin.telegram_bot import InitTelegramBot
    from etc.db_handler.create_schema_tables import InitDBClient
    from exchange_plugin.common_info import InitCommonInfo
    telegram_bot_name = config['node_settings'][node]['telegram_bot_name']
    telegram_bot_token = config['telegram_bot_setting'][telegram_bot_name]
    master_flag = config['node_settings'][node]['MASTER']
    db_dict = config['database_setting'][config['node_settings'][node]['db_settings']]
    db_dict['database'] = node

    # Create database and tables if not exists
    temp_db_dict = db_dict.copy()
    temp_db_dict['create_database'] = True
    temp_db_dict['logging_dir'] = logging_dir
    temp_db_client = InitDBClient(**temp_db_dict)
    temp_db_client.create_all_table(master_node=master_flag)
    temp_db_client.curr.close()
    temp_db_client.conn.close()

    # kline_schema_name = 'test_coin_kimp_kline' # Original
    kline_schema_name = 'coin_kimp_kline'
    
    # Initiate Kimp core (Websocket engine)
    kimp_core = InitKimpCore(logging_dir, proc_n, node, admin_id, register_monitor_msg, exchange_api_key_dict, enabled_markets_dict)
    # kimp_core.monitor_websocket()
    kimp_core.start_monitor_update_kimp_to_redis()
    kimp_core.start_monitor_update_wa_kimp_to_redis()
    kimp_core.start_monitor_update_dollar_to_redis()

    # Initiate Kimp core monitor
    kimp_core_monitor = InitKimpCoreMonitor(logging_dir, node, admin_id, proc_n, db_dict, kimp_core.get_kimp_df, kimp_core.get_dollar_dict, register_monitor_msg)
    kimp_core_monitor.start_loop_monitor_websocket_time(threshold_minutes=3)
    kimp_core_monitor.start_loop_monitor_dollar_time(threshold_minutes=2)
    kimp_core_monitor.start_loop_monitor_kline_data(threshold_minutes=3)
    
    if master_flag and input_update_common_info_flag:
        # Updating fund info & Kline
        common_info = InitCommonInfo(logging_dir, node, admin_id, db_dict, register_monitor_msg, kimp_core, kline_schema_name, MASTER=True)
    else:
        common_info = Dummy()
                                    
    # Initiate TelegramBot with Trigger engine
    telegram_bot = InitTelegramBot(logging_dir, node, db_dict, kimp_core, common_info.kline_fetcher_proc_status, register_monitor_msg, telegram_bot_token, kline_schema_name, admin_id) # LATER
    # Start High Low trigger engine
    telegram_bot.snatcher.start_monitor_high_low_loop()

    telegram_bot.updater.idle()

