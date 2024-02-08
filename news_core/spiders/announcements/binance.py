import json
import requests
import scrapy

from datetime import datetime, timezone
from icecream import ic as iceprint
from slugify import slugify

from news_core.items import AnnouncementItem
from news_core.lib.datetime import AM_KR, PM_KR
from news_core.spiders.announcements.constants import (
    BINANCE,
    NOTICE,
    MAINTENANCE,
    NEW_LISTING,
    DELISTING,
    CATEGORY_MAPPING,
)


class BinanceSpider(scrapy.Spider):
    name = "binance"
    start_urls = [
        "https://www.binance.com/en/support/announcement/latest-binance-news?c=49&navId=49"
    ]
    custom_settings = {
        "DOWNLOAD_DELAY": 3,
    }

    def parse(self, response):
        # iceprint(self.start_urls)

        data = json.loads(
            response.css("body").xpath("script[contains(.,'appState')]/text()").get()
        )["appState"]["loader"]["dataByRouteId"]

        catalogs = []
        for key, value in data.items():
            if "catalogs" in value:
                catalogs = value["catalogs"]

        for catalog in catalogs:
            if catalog["catalogName"] in [
                "Latest Binance News",
                "New Cryptocurrency Listing",
                "Delisting",
                "Wallet Maintenance Updates",
                "Crypto Airdrop",
            ]:
                category = CATEGORY_MAPPING.get(
                    catalog["catalogName"],
                    NOTICE,
                )
                for article in catalog["articles"]:
                    slug = f"{slugify(article['title'])}-{article['code']}"
                    url = response.urljoin(slug)
                    iceprint(url)

                    yield scrapy.Request(
                        url=url,
                        callback=self.parse_announcements,
                        cb_kwargs=dict(category=category),
                    )

    def parse_announcements(self, response, category):
        url = response.url

        data = json.loads(
            response.css("body").xpath("script[contains(.,'appState')]/text()").get()
        )["appState"]["loader"]["dataByRouteId"]

        article = None
        for key, value in data.items():
            if "articleDetail" in value:
                article = value["articleDetail"]

        title = article["title"]

        date_time = datetime.fromtimestamp(
            article["publishDate"] / 1000,
            tz=timezone.utc,
        )

        content = json.loads(article["body"])["child"]
        content = self.get_child(content)
        content = content.split("\n")
        content = [content.strip() for content in content]
        content = [content for content in content if content]

        announcement_item = AnnouncementItem(
            url=url,
            title=title,
            datetime=date_time,
            content="\n".join(content),
            category=category,
            exchange=BINANCE,
        )
        # iceprint(announcement_item)

        yield announcement_item

    def get_child(self, child):
        results = ""

        for c in child:
            if "child" in c:
                results += self.get_child(c["child"])
            elif "text" in c:
                results += f"{c['text']}\n"

        return results
