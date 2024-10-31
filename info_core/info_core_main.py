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
from etc.command_handler import CommandHandler
from dotenv import load_dotenv

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
    parser.add_argument('--config', '-c', nargs=1, help='Specify a directory of a config json file.', default=[current_folder_dir+"/.env"], dest='config_dir')

    # node = parser.parse_args().node[0]
    proc_n = int(parser.parse_args().proc_n[0])
    logging_dir = parser.parse_args().logging_dir[0]
    config_dir = parser.parse_args().config_dir[0]
    # return node, proc_n, logging_dir, input_update_common_info_flag, config_dir
    return proc_n, logging_dir, config_dir

if __name__ == '__main__':
    # node, proc_n, logging_dir, input_update_common_info_flag, config_dir = get_arguments()
    proc_n, logging_dir, config_dir = get_arguments()
    # Load config
    load_dotenv(config_dir)
    if not os.path.exists(logging_dir):
        os.mkdir(logging_dir)
    # if node not in config['node_settings'].keys():
    #     raise Exception(f"Node name should be the one of {list(config['node_settings'].keys())}")
    
    # Access environment variables
    PROD = os.getenv('PROD', 'False').lower() == 'true'
    NODE = os.getenv('NODE')
    MASTER = os.getenv('MASTER').lower() == 'true'
    MONGODB_HOST = os.getenv('MONGODB_HOST')
    MONGODB_PORT = int(os.getenv('MONGODB_PORT', '27017'))  # Set default port if not provided
    MONGODB_USER = os.getenv('MONGODB_USER')
    MONGODB_PASS = os.getenv('MONGODB_PASS')
    REDIS_HOST = os.getenv('REDIS_HOST')
    REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_PASS = os.getenv('REDIS_PASS')
    POSTGRES_HOST = os.getenv('POSTGRES_HOST')
    POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
    POSTGRES_USER = os.getenv('POSTGRES_USER')
    POSTGRES_PASS = os.getenv('POSTGRES_PASS')
    ADMIN_TELEGRAM_ID = int(os.getenv('ADMIN_TELEGRAM_ID'))
    STAFF_TELEGRAM_ID_LIST = [int(x.strip()) for x in os.getenv('STAFF_TELEGRAM_ID_LIST').split(',') if x != ""]
    TOTAL_ADMIN_TELEGRAM_ID_LIST = [ADMIN_TELEGRAM_ID] + STAFF_TELEGRAM_ID_LIST
    MONITOR_BOT_TOKEN = os.getenv('MONITOR_BOT_TOKEN')
    MONITOR_BOT_API_URL = os.getenv('MONITOR_BOT_API_URL')
    ACW_API_URL = os.getenv('ACW_API_URL')
    BINANCE_ACCESS_KEY = os.getenv('BINANCE_ACCESS_KEY')
    BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')
    OKX_ACCESS_KEY = os.getenv('OKX_ACCESS_KEY')
    OKX_SECRET_KEY = os.getenv('OKX_SECRET_KEY')
    OKX_PASSPHRASE = os.getenv('OKX_PASSPHRASE')
    UPBIT_ACCESS_KEY = os.getenv('UPBIT_ACCESS_KEY')
    UPBIT_SECRET_KEY = os.getenv('UPBIT_SECRET_KEY')
    BITHUMB_ACCESS_KEY = os.getenv('BITHUMB_ACCESS_KEY')
    BITHUMB_SECRET_KEY = os.getenv('BITHUMB_SECRET_KEY')
    BYBIT_ACCESS_KEY = os.getenv('BYBIT_ACCESS_KEY')
    BYBIT_SECRET_KEY = os.getenv('BYBIT_SECRET_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    ENABLED_MARKET_KLINES = [x for x in [x.strip() for x in os.getenv('ENABLED_MARKET_KLINES').split(',')] if x != ""]
    ENALBED_ARBITRAGE_MARKETS = [x for x in [x.strip() for x in os.getenv('ENALBED_ARBITRAGE_MARKETS').split(',')] if x != ""]

    # make api key dict
    exchange_api_key_dict = {
        "binance_read_only": {
            "api_key": BINANCE_ACCESS_KEY,
            "secret_key": BINANCE_SECRET_KEY
        },
        "okx_read_only": {
            "api_key": OKX_ACCESS_KEY,
            "secret_key": OKX_SECRET_KEY,
            "passphrase": OKX_PASSPHRASE
        },
        "upbit_read_only": {
            "api_key": UPBIT_ACCESS_KEY,
            "secret_key": UPBIT_SECRET_KEY
        },
        "bithumb_read_only": {
            "api_key": BITHUMB_ACCESS_KEY,
            "secret_key": BITHUMB_SECRET_KEY,
        },
        "bybit_read_only": {
            "api_key": BYBIT_ACCESS_KEY,
            "secret_key": BYBIT_SECRET_KEY,
        },
    }

    # make db info dict
    mongo_db_dict = {
        "host": MONGODB_HOST,
        "port": MONGODB_PORT,
        "user": MONGODB_USER,
        "passwd": MONGODB_PASS
    }

    redis_dict = {
        "host": REDIS_HOST,
        "port": REDIS_PORT,
        "passwd": REDIS_PASS
    }

    postgres_db_dict = {
        "host": POSTGRES_HOST,
        "port": POSTGRES_PORT,
        "user": POSTGRES_USER,
        "passwd": POSTGRES_PASS
    }
    
    register_monitor_msg = RegisterMonitorMsg(MONITOR_BOT_TOKEN, MONITOR_BOT_API_URL, ADMIN_TELEGRAM_ID, logging_dir)
    # For Test
    register_monitor_msg.register(ADMIN_TELEGRAM_ID, NODE, 'info', f"info_core_main|NODE:{NODE} has started.", content=None, code=None, sent_switch=0, send_counts=1, remark=None)

    # idle
    from telegram_bot_plugin.telegram_bot import InitTelegramBot
    
    # Initiate Kimp core (Websocket engine)
    core = InitCore(logging_dir,
                    MASTER,
                    proc_n,
                    NODE,
                    ADMIN_TELEGRAM_ID,
                    register_monitor_msg,
                    exchange_api_key_dict,
                    ENABLED_MARKET_KLINES,
                    ENALBED_ARBITRAGE_MARKETS,
                    mongo_db_dict,
                    redis_dict)

    time.sleep(5)

    # Initiate TelegramBot with Trigger engine
    if MASTER:
        telegram_bot_token = "6661285565:AAGjGdZKYhwgQ5CcuDMZumEwaEGbzdTWAHE" # Temporary. Later it will use acw's message system to communicate with info_core
        admin_telegram_bot = InitTelegramBot(telegram_bot_token,
                                             logging_dir,
                                             NODE,
                                             redis_dict,
                                             mongo_db_dict,
                                             core,
                                             register_monitor_msg,
                                             TOTAL_ADMIN_TELEGRAM_ID_LIST,
                                             ENALBED_ARBITRAGE_MARKETS)

    # Start command handler loop
    command_handler = CommandHandler(NODE, ADMIN_TELEGRAM_ID, core, logging_dir)
    command_handler.fetch_command_loop()

