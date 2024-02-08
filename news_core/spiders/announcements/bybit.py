import json
import re
import scrapy

from datetime import datetime
from icecream import ic as iceprint

from news_core.items import AnnouncementItem
from news_core.lib.datetime import AM_KR, PM_KR
from news_core.spiders.announcements.constants import (
    BYBIT,
    NOTICE,
    MAINTENANCE,
    NEW_LISTING,
    DELISTING,
    CATEGORY_MAPPING,
)


class BybitSpider(scrapy.Spider):
    name = "bybit"
    start_urls = [
        "https://announcements.bybit.com/en/?category=latest_bybit_news&page=1"
        "https://announcements.bybit.com/en/?category=new_crypto&page=1",
        "https://announcements.bybit.com/en/?category=maintenance_updates&page=1",
        "https://announcements.bybit.com/en/?category=delistings&page=1",
    ]

    def parse(self, response):
        # iceprint(self.start_urls)

        urls = response.css("div.article-list").css("a::attr(href)").getall()
        for url in urls:
            url = response.urljoin(url)
            iceprint(url)

            yield scrapy.Request(
                url=url,
                callback=self.parse_announcements,
            )

    def parse_announcements(self, response):
        url = response.url

        # Change to __NEXT_DATA__
        article = json.loads(
            response.css("body")
            .xpath("script[contains(.,'articleDetail')]/text()")
            .get()
        )["props"]["pageProps"]["articleDetail"]

        title = article["title"]

        date_time = article["date"].split(".")[0] + "+00:00"
        date_time = datetime.strptime(date_time, "%Y-%m-%dT%H:%M:%S%z")

        content = article["content"]["json"]["children"]
        content = self.get_children(content)
        content = content.split("\n")
        content = [content.strip() for content in content]
        content = [content for content in content if content]

        if "category=latest_bybit_news" in url:
            category = NOTICE
        elif "category=new_crypto" in url:
            category = NEW_LISTING
        elif "category=maintenance_updates" in url:
            category = MAINTENANCE
        elif "category=delistings" in url:
            category = DELISTING
        else:
            category = NOTICE

        announcement_item = AnnouncementItem(
            url=url,
            title=title,
            datetime=date_time,
            content="\n".join(content),
            category=category,
            exchange=BYBIT,
        )
        # iceprint(announcement_item)

        yield announcement_item

    def get_children(self, children):
        results = ""

        for child in children:
            if "children" in child:
                results += self.get_children(child["children"])
            else:
                results += f"{child['text']}\n"

        return results
