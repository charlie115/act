#!/bin/bash
# Author: Gizelle Peras (gizelle@halo-soft.com)
# Description: Script to scrape sns posts


main() {
    touch "$lock_file"

    echo "x"
    /usr/local/bin/scrapy crawl --nolog x
    echo

    rm "$lock_file"
}

lock_file="/home/scrapy/news_core/scripts/scrape_sns.lock"

if [ -e "$lock_file" ] 
then
  echo "Lock file still exists..."
  echo 'Exiting...'
  exit 0
else
  main "${@}"
fi