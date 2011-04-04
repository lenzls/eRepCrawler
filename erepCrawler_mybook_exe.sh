#!/bin/sh
echo "starting erep Crawler"
python /root/eRepCrawler/src/main.py -t standard |  mutt -s "eRepCrawler Status-Bericht" lenz.simon@googlemail.com
echo "finished crawler"
