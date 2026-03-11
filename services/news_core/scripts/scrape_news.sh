#!/bin/bash
# Author: Gizelle Peras (gizelle@halo-soft.com)
# Description: Script to scrape news


main() {
    touch "$lock_file"

    echo "zdnet"
    /usr/local/bin/scrapy crawl --nolog zdnet
    echo

    echo "etoday"
    /usr/local/bin/scrapy crawl --nolog etoday
    echo

    echo "einfomax"
    /usr/local/bin/scrapy crawl --nolog einfomax
    echo

    echo "bonmedia"
    /usr/local/bin/scrapy crawl --nolog bonmedia
    echo

    echo "fnnews"
    /usr/local/bin/scrapy crawl --nolog fnnews
    echo

    echo "decenter"
    /usr/local/bin/scrapy crawl --nolog decenter
    echo

    echo "blockstreet"
    /usr/local/bin/scrapy crawl --nolog blockstreet
    echo

    echo "coindeskkorea"
    /usr/local/bin/scrapy crawl --nolog coindeskkorea
    echo

    echo "coinreaders"
    /usr/local/bin/scrapy crawl --nolog coinreaders
    echo

    echo "blockmedia"
    /usr/local/bin/scrapy crawl --nolog blockmedia
    echo

    rm "$lock_file"
}

lock_file="/home/scrapy/news_core/scripts/scrape_news.lock"

if [ -e "$lock_file" ] 
then
  echo "Lock file still exists..."
  echo 'Exiting...'
  exit 0
else
  main "${@}"
fi