import json
import requests
import scrapy

from datetime import datetime
from icecream import ic as iceprint

from news_core.items import AnnouncementItem
from news_core.lib.datetime import AM_KR, PM_KR
from news_core.spiders.announcements.constants import UPBIT, NOTICE, CATEGORY_MAPPING


class UpbitSpider(scrapy.Spider):
    name = "upbit"
    start_urls = ["https://api-manager.upbit.com/api/v1/notices"]

    def parse(self, response):
        # iceprint(self.start_urls)

        response_data = json.loads(response.body)["data"]["list"]
        for data in response_data:
            url = f"{response.url}/{data['id']}"
            iceprint(url)

            yield scrapy.Request(
                url=url,
                headers={"Accept-Language": "ko-KR, ko;q=1, en-US;q=0.1"},
                callback=self.parse_announcements,
            )

    def parse_announcements(self, response):
        data = json.loads(response.body)["data"]

        url = f"https://upbit.com/service_center/notice?id={data['id']}"

        date_time = datetime.strptime(
            data["created_at"],
            "%Y-%m-%dT%H:%M:%S%z",
        )

        category = data["title"].split(" ")[0]
        if "[" in category and "]" in category:
            category = category.strip("[]")
            category = CATEGORY_MAPPING.get(category, NOTICE)
        else:
            category = NOTICE

        announcement_item = AnnouncementItem(
            url=url,
            title=data["title"],
            datetime=date_time,
            content=data["body"],
            category=category,
            exchange=UPBIT,
        )
        # iceprint(announcement_item)

        yield announcement_item
