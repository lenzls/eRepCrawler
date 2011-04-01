#!/bin/sh
echo "starting erep Crawler"
python ./src/main.py -t standard |  mutt -s "eRepCrawler Status-Bericht" lenz.simon@googlemail.com