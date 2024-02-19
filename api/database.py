from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
import os
import json
import sys

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
config_dir = f"{upper_dir}/trade_core_config.json"
with open(config_dir) as f:
    config = json.load(f)

node = config['node']
db_dict = config['database_setting'][config['node_settings'][node]['db_settings']]

SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://{db_dict['user']}:{db_dict['passwd'].replace('!','%21')}@postgres/trade_core"

engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()