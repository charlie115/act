import json
import re
import scrapy

from datetime import datetime
from icecream import ic as iceprint

from news_core.items import AnnouncementItem
from news_core.lib.datetime import AM_KR, PM_KR
from news_core.spiders.announcements.constants import (
    OKX,
    NOTICE,
    NEW_LISTING,
    DELISTING,
    CATEGORY_MAPPING,
)


class OKXSpider(scrapy.Spider):
    name = "okx"
    start_urls = ["https://www.okx.com/v2/support/home/web"]

    def parse(self, response):
        # iceprint(self.start_urls)

        response_data = json.loads(response.body)["data"]["notices"]
        for data in response_data:
            url = response.urljoin(data["link"])
            iceprint(url)

            yield scrapy.Request(
                url=url,
                callback=self.parse_announcements,
            )

    def parse_announcements(self, response):
        url = response.url

        article_container = response.css("div[id=article-container]")

        header = article_container.css("div")[0].css("div")

        title = header.css("h1::text").get()

        date_time = header.css("span::text").get()
        date_time = date_time.replace("Published", "").strip()
        date_time = date_time + " +09:00"
        date_time = datetime.strptime(date_time, "%b %d, %Y %z")

        article_content = (
            response.css("div.article-content-wrap").css("p::text").getall()
        )

        content = [content.strip() for content in article_content]
        content = [content for content in content if content]

        if "list" in title:
            category = NEW_LISTING
        elif "delist" in title:
            category = DELISTING
        else:
            category = NOTICE

        announcement_item = AnnouncementItem(
            url=url,
            title=title,
            datetime=date_time,
            content="\n".join(content),
            category=category,
            exchange=OKX,
        )
        # iceprint(announcement_item)

        yield announcement_item
