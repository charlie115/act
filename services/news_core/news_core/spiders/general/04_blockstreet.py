import re
import scrapy

from datetime import datetime
from icecream import ic as iceprint
from news_core.items import NewsItem


class BlockStreetSpider(scrapy.Spider):
    name = "blockstreet"
    start_urls = ["https://blockstreet.co.kr"]

    def parse(self, response):
        # iceprint(self.start_urls)

        urls = set()
        for url in response.css("a::attr(href)").getall():
            try:
                match = re.match(r"/news/view\?ud=[\d]+", url)

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

        article = response.css("div.content").css("article")

        header = article.css("div.view-header")

        title = header.css("h2.headline").css("::text").getall()
        title = " ".join(title).strip()

        date_time = header.css("div.datetime").css("span")[1].css("::text").get()
        date_time = date_time.replace("등록", "").strip()
        date_time = date_time + " +09:00"
        date_time = datetime.strptime(date_time, "%Y-%m-%d %H:%M %z")

        body = article.css("div.view-body")

        thumbnail = (
            body.css("div.photoOrg").xpath("//figure/img").css("::attr('src')").get()
        )

        content = body.css("::text").getall()
        content = [content.strip() for content in content]
        content = [content for content in content if content]

        news_item = NewsItem(
            url=url,
            title=title,
            datetime=date_time,
            thumbnail=thumbnail,
            content="\n".join(content),
            media="blockstreet",
        )

        yield news_item
