from urllib.parse import quote_plus

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from api.config import postgres_db_dict

SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://{postgres_db_dict['user']}:{quote_plus(postgres_db_dict['passwd'])}@{postgres_db_dict['host']}:{postgres_db_dict['port']}/trade_core"

engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()