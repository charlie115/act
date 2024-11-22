from dotenv import load_dotenv
import os
from etc.db_handler.postgres_client import InitDBClient as InitPostgresDBClient
from etc.acw_api import AcwApi

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logging_dir = f"{upper_dir}/loggers/logs/"
# Read config
config_dir = f"{upper_dir}/.env"
load_dotenv(config_dir)

logging_dir = f"{upper_dir}/loggers/logs/"
PROD = os.getenv('PROD', 'False').lower() == 'true'
NODE = os.getenv('NODE') + '_api'
ADMIN_TELEGRAM_ID = int(os.getenv('ADMIN_TELEGRAM_ID'))
USER_UUID_FOR_WALLET = os.getenv('USER_UUID_FOR_WALLET')
ACW_API_URL = os.getenv('ACW_API_URL')
MONGODB_HOST = os.getenv('MONGODB_HOST')
MONGODB_PORT = int(os.getenv('MONGODB_PORT', '27017'))  # Set default port if not provided
MONGODB_USER = os.getenv('MONGODB_USER')
MONGODB_PASS = os.getenv('MONGODB_PASS')
API_REDIS_HOST = os.getenv('API_REDIS_HOST')
API_REDIS_PORT = int(os.getenv('API_REDIS_PORT', '6379'))
API_REDIS_PASS = os.getenv('API_REDIS_PASS')
POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_PORT = int(os.getenv('POSTGRES_PORT'))
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASS = os.getenv('POSTGRES_PASS')
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY').encode()

mongo_db_dict = {
    "host": MONGODB_HOST,
    "port": MONGODB_PORT,
    "user": MONGODB_USER,
    "passwd": MONGODB_PASS
}

redis_dict = {
    "host": API_REDIS_HOST,
    "port": API_REDIS_PORT,
    "passwd": API_REDIS_PASS
}

postgres_db_dict = {
    "host": POSTGRES_HOST,
    "port": POSTGRES_PORT,
    "user": POSTGRES_USER,
    "passwd": POSTGRES_PASS
}

# Create postgres db and tables
postgres_client = InitPostgresDBClient(**{**postgres_db_dict, 'database': 'trade_core'})
postgres_client.create_all_tables()

acw_api = AcwApi(ACW_API_URL, NODE, PROD)
