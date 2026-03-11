#!/bin/bash
# Author: Gizelle Peras (gizelle@halo-soft.com)
# Description: Script to scrape announcements


main() {
    touch "$lock_file"

    echo "upbit"
    /usr/local/bin/scrapy crawl --nolog upbit
    echo

    echo "bithumb"
    /usr/local/bin/scrapy crawl --nolog bithumb
    echo

    echo "okx"
    /usr/local/bin/scrapy crawl --nolog okx
    echo

    echo "bybit"
    /usr/local/bin/scrapy crawl --nolog bybit
    echo

    echo "binance"
    /usr/local/bin/scrapy crawl --nolog binance
    echo

    rm "$lock_file"
}

lock_file="/home/scrapy/news_core/scripts/scrape_announcements.lock"

if [ -e "$lock_file" ] 
then
  echo "Lock file still exists..."
  echo 'Exiting...'
  exit 0
else
  main "${@}"
fi