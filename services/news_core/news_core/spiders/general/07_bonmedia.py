import re
import scrapy

from datetime import datetime
from icecream import ic as iceprint
from time import time

from news_core.items import NewsItem


class BonMediaSpider(scrapy.Spider):
    name = "bonmedia"
    start_urls = ["https://www.bonmedia.kr"]

    def parse(self, response):
        # iceprint(self.start_urls)

        urls = set()
        for url in response.css("a::attr(href)").getall():
            try:
                match = re.match(r"/news/articleView.html\?idxno=[\d]+", url)

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

        article_view = response.css("div[id=article-view]")

        header = article_view.css("header.article-view-header")

        title = header.css("h3.heading::text").get()

        date_time = header.css("nav.rooted").css("ul.dated").css("li::text")[0].get()
        date_time = "".join(date_time).replace("입력", "").strip()
        date_time = date_time + " +09:00"
        date_time = datetime.strptime(date_time, "%Y.%m.%d %H:%M %z")

        article_view_content = article_view.css("article[id=article-view-content-div]")

        thumbnail = (
            article_view_content.css("figure.photo-layout")
            .css("img::attr('src')")
            .get()
        )

        content = article_view_content.css("::text").getall()
        content = [content.strip() for content in content]
        content = [content for content in content if content]

        news_item = NewsItem(
            url=url,
            title=title,
            datetime=date_time,
            thumbnail=thumbnail,
            content="\n".join(content),
            media="bonmedia",
        )

        yield news_item
