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
NODE = os.getenv('NODE', 'default') + '_api'
ADMIN_TELEGRAM_ID = int(os.getenv('ADMIN_TELEGRAM_ID', '0'))
USER_UUID_FOR_WALLET = os.getenv('USER_UUID_FOR_WALLET', '')
ACW_API_URL = os.getenv('ACW_API_URL', 'http://localhost:8000')
MONGODB_HOST = os.getenv('MONGODB_HOST', 'localhost')
MONGODB_PORT = int(os.getenv('MONGODB_PORT', '27017'))  # Set default port if not provided
MONGODB_USER = os.getenv('MONGODB_USER', '')
MONGODB_PASS = os.getenv('MONGODB_PASS', '')
API_REDIS_HOST = os.getenv('API_REDIS_HOST', 'localhost')
API_REDIS_PORT = int(os.getenv('API_REDIS_PORT', '6379'))
API_REDIS_PASS = os.getenv('API_REDIS_PASS', None)
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASS = os.getenv('POSTGRES_PASS', '')
_encryption_key = os.getenv('ENCRYPTION_KEY', '')
if not _encryption_key:
    raise ValueError("ENCRYPTION_KEY environment variable must be set")
ENCRYPTION_KEY = _encryption_key.encode()

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
