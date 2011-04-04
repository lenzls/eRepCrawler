#!/bin/sh
echo "starting erep Crawler"
python /root/eRepCrawler/src/main.py -t extended |  mutt -s "eRepCrawler Status-Bericht" lenz.simon@googlemail.com
#python /home/simon/dev/erepCrawler/src/main.py -t extended
echo "finished crawler"