import re
import scrapy

from datetime import datetime
from icecream import ic as iceprint
from news_core.items import NewsItem


class DecenterSpider(scrapy.Spider):
    name = "decenter"
    start_urls = ["https://decenter.kr"]

    def parse(self, response):
        # iceprint(self.start_urls)

        urls = set()
        for url in response.css("a::attr(href)").getall():
            try:
                match = re.match(r"/NewsView/\w+", url)

                if url and bool(match):
                    # To get unique urls that have extra endpoints/parameters
                    # https://decenter.kr/NewsView/29X4Q4H6WB
                    # https://decenter.kr/NewsView/29X4Q4H6WB/GZ01
                    url = match.group()
                    if url not in urls:
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

        article = response.css("div[id=contents-article-view]").css("div[id=v-left]")

        article_head = response.css("div.article_head")[0]

        title = article_head.css("h2::text").get()

        date_time = (
            article_head.css("div.article_info").css("span.url_txt::text")[0].get()
        )
        date_time = date_time.strip() + " +09:00"
        date_time = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S %z")

        view_content = article.css("div.view_con")

        thumbnail = view_content.css("figure.art_photo").css("::attr('src')").get()

        content = view_content.css("::text").getall()
        content = [content.strip() for content in content]
        content = [content for content in content if content]

        news_item = NewsItem(
            url=url,
            title=title,
            datetime=date_time,
            thumbnail=thumbnail,
            content="\n".join(content),
            media="decenter",
        )

        yield news_item
