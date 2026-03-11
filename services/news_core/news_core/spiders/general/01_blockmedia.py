import re
import scrapy

from datetime import datetime
from icecream import ic as iceprint
from news_core.lib.datetime import AM_KR, PM_KR
from news_core.items import NewsItem


class BlockMediaSpider(scrapy.Spider):
    name = "blockmedia"
    start_urls = ["https://www.blockmedia.co.kr"]

    def parse(self, response):
        # iceprint(self.start_urls)

        urls = set()
        for url in response.css("a::attr(href)").getall():
            try:
                match = re.match(r"https://www.blockmedia.co.kr/archives/[\d]+", url)

                if url and bool(match) and url not in urls:
                    urls.add(url)
                    iceprint(url)

                    yield scrapy.Request(
                        url=response.urljoin(url),
                        callback=self.parse_articles,
                    )

            except TypeError as err:
                print(err)

    def parse_articles(self, response):
        url = response.url

        post_header = response.css("div.post-header")

        title = post_header.css("h1.entry-title::text").getall()
        title = " ".join(title)

        date_time = post_header.css("div.post-meta").css("span.updated::text").get()
        date_time = date_time.replace(AM_KR, "AM") if AM_KR in date_time else date_time
        date_time = date_time.replace(PM_KR, "PM") if PM_KR in date_time else date_time
        date_time = date_time.replace(" ", "") + "+09:00"
        date_time = datetime.strptime(date_time, "%Y년%m월%d일%p%I:%M%z")

        thumbnail = response.css("div.post-thumbnail").css("img::attr(src)").get()

        post_content = (
            response.css("div.post-wrap")
            .css("div.post-content")
            .css("div[id=pavo_contents]")
            .css("*::text")
            .getall()
        )

        content = [content.strip() for content in post_content]
        content = [content for content in content if content]

        news_item = NewsItem(
            url=url,
            title=title,
            datetime=date_time,
            thumbnail=thumbnail,
            content="\n".join(content),
            media="blockmedia",
        )

        yield news_item
