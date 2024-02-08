import re
import scrapy

from datetime import datetime
from icecream import ic as iceprint
from time import time

from news_core.items import NewsItem


class ZDNetSpider(scrapy.Spider):
    """General news media"""

    name = "zdnet"
    start_urls = [
        # Computing
        "https://zdnet.co.kr/news/?lstcode=0020",
    ]

    def parse(self, response):
        # iceprint(self.start_urls)

        urls = set()
        for url in response.css("div.news_box")[1].css("a::attr(href)").getall():
            try:
                match = re.match(r"/view/\?no=[\d]+", url)

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

        article_feed = response.css("div.article-feed")

        news_head = article_feed.css("div.news_head")

        title = news_head.css("h1::text").get().strip()

        date_time = news_head.css("span::text").get()
        date_time = date_time.replace("입력 :", "").strip() + " +09:00"
        date_time = datetime.strptime(date_time, "%Y/%m/%d %H:%M %z")

        view_cont = response.css("div.view_cont")

        thumbnail = view_cont.css("figure").css("img::attr('src')").get()

        content = view_cont.css("::text").getall()
        content = [content.strip() for content in content]
        content = [content for content in content if content]

        news_item = NewsItem(
            url=url,
            title=title,
            datetime=date_time,
            thumbnail=thumbnail,
            content="\n".join(content),
            media="zdnet",
        )

        yield news_item
