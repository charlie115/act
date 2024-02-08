from sqlalchemy import (
    create_engine,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine.base import Engine
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import relationship
from scrapy.utils.project import get_project_settings
from news_core import settings

Base = declarative_base()


def db_connect() -> Engine:
    """
    Creates database connection using database settings from settings.py.
    Returns sqlalchemy engine instance
    """
    return create_engine(settings.DATABASE, pool_size=10, max_overflow=20)


def create_items_table(engine: Engine):
    """
    Create the Items table
    """
    Base.metadata.create_all(engine)


class NewsModel(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True)
    title = Column("title", String(300))
    content = Column("content", Text())
    datetime = Column("datetime", DateTime)
    url = Column("url", String(500), unique=True)
    thumbnail = Column("thumbnail", String(500))
    media = Column("media", String(300))


class AnnouncementModel(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True)
    title = Column("title", String(300))
    content = Column("content", Text())
    datetime = Column("datetime", DateTime)
    url = Column("url", String(500), unique=True)
    category = Column("category", String(100))
    exchange = Column("exchange", String(300))


class PostModel(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    name = Column("name", String(100))
    username = Column("username", String(100))
    content = Column("content", Text())
    extra_data = Column("extra_data", JSONB)
    datetime = Column("datetime", DateTime)
    url = Column("url", String(500), unique=True)
    social_media = Column("social_media", String(100))
