# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class NewsItem(scrapy.Item):
    title = scrapy.Field()
    content = scrapy.Field()
    datetime = scrapy.Field()
    url = scrapy.Field()
    thumbnail = scrapy.Field()
    media = scrapy.Field()


class AnnouncementItem(scrapy.Item):
    title = scrapy.Field()
    content = scrapy.Field()
    datetime = scrapy.Field()
    url = scrapy.Field()
    category = scrapy.Field()
    exchange = scrapy.Field()


class PostItem(scrapy.Item):
    name = scrapy.Field()
    username = scrapy.Field()
    content = scrapy.Field()
    extra_data = scrapy.Field()
    datetime = scrapy.Field()
    url = scrapy.Field()
    social_media = scrapy.Field()
