import re
import scrapy

from datetime import datetime
from icecream import ic as iceprint

from news_core.items import AnnouncementItem
from news_core.lib.datetime import AM_KR, PM_KR
from news_core.spiders.announcements.constants import BITHUMB, NOTICE, CATEGORY_MAPPING


class BithumbSpider(scrapy.Spider):
    name = "bithumb"
    start_urls = ["https://cafe.bithumb.com/view/boards/43"]

    def parse(self, response):
        # iceprint(self.start_urls)

        urls = (
            response.css("div.container")
            .css("table")
            .css("tbody")
            .css("a::attr(onclick)")
            .getall()
        )
        for url in urls:
            article_id = url.replace("'", "").split(",")[1].strip()
            url = f"https://cafe.bithumb.com/view/board-contents/{article_id}"
            iceprint(url)

            yield scrapy.Request(
                url=response.urljoin(url),
                callback=self.parse_announcements,
            )

    def parse_announcements(self, response):
        url = response.url

        container = response.css("div.container").css("div.content")

        contents_title = container.css("div.contents-title")

        title = contents_title.css("div.title::text").get()

        date_time = contents_title.css("div.date::text").get()
        date_time = date_time.replace("카페 관리자", "").replace("\xa0", "")
        date_time = date_time + " +09:00"
        date_time = datetime.strptime(date_time, "%Y.%m.%d %H:%M:%S %z")

        board_content = container.css("div.board-content").css("*::text").getall()

        content = [content.strip() for content in board_content]
        content = [content for content in content if content]

        category = title.split(" ")[0]
        if "[" in category and "]" in category:
            category = category.strip("[]")
            category = CATEGORY_MAPPING.get(category, NOTICE)
        else:
            category = NOTICE

        announcement_item = AnnouncementItem(
            url=url,
            title=title,
            datetime=date_time,
            content="\n".join(content),
            category=category,
            exchange=BITHUMB,
        )
        # iceprint(announcement_item)

        yield announcement_item
