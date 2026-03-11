import re
import scrapy

from datetime import datetime
from icecream import ic as iceprint
from news_core.items import NewsItem


class CoinReadersSpider(scrapy.Spider):
    name = "coinreaders"
    start_urls = ["https://coinreaders.com"]

    def parse(self, response):
        # iceprint(self.start_urls)

        urls = set()
        for url in response.css("a::attr(href)").getall():
            try:
                match = re.match(r"/[\d]+", url)

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

        article_head = response.css("div.article_head")[0]

        title = article_head.css("h1.read_title::text").get()

        date_time = (
            article_head.css("div.read_option_top")
            .css("div.writer_time::text")
            .getall()
        )
        date_time = "".join(date_time).replace("기사입력", "").strip()
        date_time = date_time + " +09:00"
        date_time = datetime.strptime(date_time, "%Y/%m/%d [%H:%M] %z")

        table_sub_read = (
            response.css("table.table_sub_read")
            .css("td.td_sub_read_contents")
            .css("div[id=textinput]")
        )

        thumbnail = (
            table_sub_read.css("table.body_img_table")
            .css("img[id=img_pop_view]::attr('src')")
            .get()
        )
        thumbnail = response.urljoin(thumbnail)

        content = table_sub_read.css("::text").getall()
        content = [content.strip() for content in content]
        content = [content for content in content if content]

        news_item = NewsItem(
            url=url,
            title=title,
            datetime=date_time,
            thumbnail=thumbnail,
            content="\n".join(content),
            media="coinreaders",
        )

        yield news_item
