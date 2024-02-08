# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import psycopg2

from icecream import ic as iceprint
from itemadapter import ItemAdapter
from sqlalchemy.orm import sessionmaker

from news_core.settings import env
from news_core.items import AnnouncementItem, NewsItem, PostItem
from news_core.models import (
    AnnouncementModel,
    NewsModel,
    PostModel,
    create_items_table,
    db_connect,
)


class NewsCorePipeline(object):
    item_model_mapping = {
        AnnouncementItem: AnnouncementModel,
        NewsItem: NewsModel,
        PostItem: PostModel,
    }

    def __init__(self):
        """
        Initializes database connection and sessionmaker.
        Creates items table.
        """
        engine = db_connect()
        create_items_table(engine)
        self.Session = sessionmaker(bind=engine)

    def process_item(self, item, spider):
        """
        Process the item and store to database.
        """
        model = self.item_model_mapping[type(item)]

        session = self.Session()

        instance = session.query(model).filter_by(url=item["url"]).one_or_none()
        if instance:
            return instance

        model_item = model(**item)

        try:
            session.add(model_item)
            session.commit()
        except Exception as err:
            iceprint(err)
            session.rollback()
            raise
        finally:
            session.close()

        return item
