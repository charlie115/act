import re
import scrapy

from datetime import datetime
from icecream import ic as iceprint
from time import time

from news_core.items import NewsItem


class ETodaySpider(scrapy.Spider):
    """General news media"""

    name = "etoday"
    start_urls = [
        # Global economy > Market conditions
        "https://www.etoday.co.kr/news/section/subsection?MID=1603",
        # Enterprise > Electronics/Communication/IT
        "https://www.etoday.co.kr/news/section/subsection?MID=1302",
        # "zdnet.co.kr",
    ]

    def parse(self, response):
        # iceprint(self.start_urls)

        urls = set()
        for url in response.css("a::attr(href)").getall():
            try:
                match = re.match(r"/news/view/[\d]+", url)

                if url and bool(match):
                    # To get unique urls that have extra endpoints/parameters
                    # https://www.etoday.co.kr/news/view/2299082
                    # https://www.etoday.co.kr/news/view/2299082?trc=right_categori_news
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

        top_wrap = response.css("section.news_dtail_view_top_wrap")

        title = top_wrap.css("h1.main_title::text").get().strip()

        date_time = top_wrap.css("div.newsinfo").css("span::text").get()
        date_time = date_time.replace("입력", "").strip() + " +09:00"
        date_time = datetime.strptime(date_time, "%Y-%m-%d %H:%M %z")

        body_wrap = (
            response.css("section.view_body_moduleWrap")
            .css("div.l_content_module")
            .css("div.articleView")
        )

        thumbnail = body_wrap.css("img::attr('src')").get()

        content = body_wrap.css("::text").getall()
        content = [content.strip() for content in content]
        content = [content for content in content if content]

        news_item = NewsItem(
            url=url,
            title=title,
            datetime=date_time,
            thumbnail=thumbnail,
            content="\n".join(content),
            media="etoday",
        )

        yield news_item
