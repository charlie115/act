import os
import sys
import argparse
import time

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from trade_core import InitCore
from etc.command_handler import CommandHandler
from etc.acw_api import AcwApi
from dotenv import load_dotenv

def get_arguments():
    """
    Parsing arguments
    """
    current_file_dir = os.path.realpath(__file__)
    current_folder_dir = os.path.abspath(os.path.join(current_file_dir, os.pardir))
    logging_dir = f"{current_folder_dir}/loggers/logs/"

    parser = argparse.ArgumentParser()
    # parser.add_argument('--node', '-n', required=True, nargs=1, help='Specify a node name. Configuration will be done based on the node name.', dest='node')
    parser.add_argument('--proc_n', '-p', nargs=1, help='Specify a number of processes to handle websockets.', default=[None], dest='proc_n')
    parser.add_argument('--log', '-l', nargs=1, help='Specify a directory to save log files.', default=[logging_dir], dest='logging_dir')
    parser.add_argument('--config', '-c', nargs=1, help='Specify a directory of a config json file.', default=[current_folder_dir+"/.env"], dest='config_dir')

    proc_n = int(parser.parse_args().proc_n[0]) if parser.parse_args().proc_n[0] is not None else None
    logging_dir = parser.parse_args().logging_dir[0]
    config_dir = parser.parse_args().config_dir[0]
    return proc_n, logging_dir, config_dir

if __name__ == '__main__':
    proc_n, logging_dir, config_dir = get_arguments()
    # Load config
    load_dotenv(config_dir)
    if not os.path.exists(logging_dir):
        os.mkdir(logging_dir)
        
    PROD = os.getenv('PROD', 'False').lower() == 'true'
    NODE = os.getenv('NODE')
    PROC_N = int(os.getenv('PROC_N')) if proc_n is None else proc_n
    MONGODB_HOST = os.getenv('MONGODB_HOST')
    MONGODB_PORT = int(os.getenv('MONGODB_PORT', '27017'))  # Set default port if not provided
    MONGODB_USER = os.getenv('MONGODB_USER')
    MONGODB_PASS = os.getenv('MONGODB_PASS')
    REDIS_HOST = os.getenv('REDIS_HOST')
    REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_PASS = os.getenv('REDIS_PASS')
    POSTGRES_HOST = os.getenv('POSTGRES_HOST')
    POSTGRES_PORT = int(os.getenv('POSTGRES_PORT'))
    POSTGRES_USER = os.getenv('POSTGRES_USER')
    POSTGRES_PASS = os.getenv('POSTGRES_PASS')
    ADMIN_TELEGRAM_ID = int(os.getenv('ADMIN_TELEGRAM_ID'))
    STAFF_TELEGRAM_ID_LIST = [int(x.strip()) for x in os.getenv('STAFF_TELEGRAM_ID_LIST').split(',') if x != ""]
    TOTAL_ADMIN_TELEGRAM_ID_LIST = [ADMIN_TELEGRAM_ID] + STAFF_TELEGRAM_ID_LIST
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
    
    # Starting message
    acw_api = AcwApi(ACW_API_URL, NODE, PROD)
    acw_api.create_message_thread(
        ADMIN_TELEGRAM_ID,
        f"Node:{NODE} is starting with {PROC_N} processes..",
        f"Node:{NODE} is starting with {PROC_N} processes..",
    )
    
    # # enabled kline market settings
    # enabled_markets = config['node_settings'][node]['enabled_markets']

    # idle
    
    # Initiate Kimp core (Websocket engine)
    core = InitCore(logging_dir,
                    PROC_N,
                    NODE,
                    ADMIN_TELEGRAM_ID,
                    acw_api,
                    exchange_api_key_dict,
                    postgres_db_dict,
                    mongo_db_dict,
                    redis_dict)

    time.sleep(5)
    
    # Start command handler loop
    command_handler = CommandHandler(ACW_API_URL, NODE, PROD, ADMIN_TELEGRAM_ID, core, logging_dir)
    command_handler.fetch_command_loop()

