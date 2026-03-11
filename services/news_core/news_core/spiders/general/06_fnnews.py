import re
import scrapy

from datetime import datetime
from icecream import ic as iceprint
from time import time

from news_core.items import NewsItem


class FNNewsSpider(scrapy.Spider):
    name = "fnnews"
    start_urls = [
        f"https://www.fnnews.com/load/category/002010000?page=0&_={int(time()*1000)}"
    ]

    def parse(self, response):
        # iceprint(self.start_urls)

        urls = set()
        for url in response.css("a::attr(href)").getall():
            try:
                match = re.match(r"https://www.fnnews.com/news/[\d]+", url)

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

        view_hd = response.css("div.view_hd")

        title = view_hd.css("h1.tit_view::text").get().strip()

        date_time = view_hd.css("div.byline").css("em")[1].css("::text").get()
        date_time = date_time.replace("입력", "").strip() + " +09:00"
        date_time = datetime.strptime(date_time, "%Y.%m.%d %H:%M %z")

        contents = response.css("div.contents")

        thumbnail = contents.css("div.box_img").css("::attr('src')").get()

        content = contents.css("div.cont_art::text").getall()
        content = [content.strip() for content in content]
        content = [content for content in content if content]

        news_item = NewsItem(
            url=url,
            title=title,
            datetime=date_time,
            thumbnail=thumbnail,
            content="\n".join(content),
            media="fnnews",
        )

        yield news_item
