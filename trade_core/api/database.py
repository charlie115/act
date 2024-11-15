from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from config import postgres_db_dict

SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://{postgres_db_dict['user']}:{postgres_db_dict['passwd'].replace('!','%21')}@{postgres_db_dict['host']}/trade_core"

engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()