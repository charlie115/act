import scrapy
import urllib.parse

from datetime import datetime
from icecream import ic as iceprint

from news_core.items import PostItem


class XSpider(scrapy.Spider):
    name = "x"
    start_urls = [
        "https://nitter.net/elonmusk",
        "https://nitter.net/MMCrypto",
        "https://nitter.net/100trillionUSD",
        "https://nitter.net/TheCryptoLark",
        "https://nitter.net/APompliano",
        "https://nitter.net/scottmelker",
        "https://nitter.net/3orovik",
        "https://nitter.net/notsofast",
        "https://nitter.net/altcoingordon",
        "https://nitter.net/Nicholas_Merten",
        "https://nitter.net/AltCryptoGems",
    ]
    custom_settings = {
        "DOWNLOAD_DELAY": 5,
    }

    def parse(self, response):
        # iceprint(self.start_urls)

        timeline = response.css("div.timeline").css("div.timeline-item")

        for item in timeline:
            tweet_link = item.css("a.tweet-link::attr(href)").get()
            url = urllib.parse.urljoin("https://x.com", tweet_link.split("#")[0])
            iceprint(url)

            tweet_body = item.css("div.tweet-body")

            retweet_header = tweet_body.xpath("div").css("div.retweet-header").get()
            if retweet_header:
                iceprint("RETWEET!!!")
                continue

            tweet_header = tweet_body.css("div.tweet-header")

            tweet_avatar = (
                tweet_header.css("a.tweet-avatar").css("img::attr(src)").get()
            )
            avatar = response.urljoin(tweet_avatar)

            tweet_name = tweet_header.css("div.tweet-name-row")
            tweet_fullname = tweet_name.css("a.fullname")
            name = tweet_fullname.css("::text").get()
            verified = (
                tweet_fullname.css("span.verified-icon::attr(title)").get()
                == "Verified account"
            )
            username = tweet_name.css("a.username::text").get()
            date_time = tweet_name.css("span.tweet-date").css("a::attr(title)").get()
            date_time = datetime.strptime(date_time, "%b %d, %Y · %I:%M %p %Z")

            content = tweet_body.css("div.tweet-content").css("*::text").getall()
            content = "".join(content)

            quote = {}
            tweet_quote = tweet_body.css("div.quote")
            if tweet_quote:
                quote_link = tweet_quote.css("a.quote-link::attr(href)").get()
                quote["url"] = urllib.parse.urljoin(
                    "https://x.com",
                    quote_link.split("#")[0],
                )

            attachments = {}
            tweet_attachments = tweet_body.css("div.attachments")
            if tweet_attachments:
                tweet_gallery = tweet_attachments.css("div.gallery-row")
                if tweet_gallery:
                    gallery_list = tweet_gallery.css(
                        "a.still-image::attr(href)"
                    ).getall()
                    attachments["gallery"] = [
                        response.urljoin(href) for href in gallery_list
                    ]

                tweet_video = tweet_attachments.css("div.gallery-video")
                if tweet_video:
                    video_list = tweet_video.css("img::attr(src)").getall()
                    attachments["video"] = [response.urljoin(src) for src in video_list]

            stats = {
                "comment_count": 0,
                "retweet_count": 0,
                "quote_count": 0,
                "heart_count": 0,
            }
            tweet_stats = (
                tweet_body.css("div.tweet-stats")
                .css("span.tweet-stat")
                .css("div.icon-container")
            )
            for tweet_stat in tweet_stats:
                stat = tweet_stat.css("::text").get()
                if stat:
                    stat = stat.replace(",", "").strip()

                    # Move typecasting inside since there are other stats
                    # like GIF/video plays
                    if tweet_stat.css("span.icon-comment"):
                        stats["comment_count"] = int(stat)
                    elif tweet_stat.css("span.icon-retweet"):
                        stats["retweet_count"] = int(stat)
                    elif tweet_stat.css("span.icon-quote"):
                        stats["quote_count"] = int(stat)
                    elif tweet_stat.css("span.icon-heart"):
                        stats["heart_count"] = int(stat)

            extra_data = {
                "avatar": avatar,
                "verified": verified,
                "stats": stats,
                "quote": quote,
                "attachments": attachments,
            }

            post_item = PostItem(
                name=name,
                username=username,
                content=content,
                extra_data=extra_data,
                datetime=date_time,
                url=url,
                social_media="x",
            )

            # iceprint(post_item)

            yield post_item
