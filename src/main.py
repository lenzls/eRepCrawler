#!/usr/bin/python
#!/opt/bin/python
'''
Created on 23.03.2011

@author: simon
'''

from eRepCrawler import ERepCrawler
from eRepDBInterface import ERepDBInterface
import time, sys
import optparse

def standardCrawlTask(crawler):
    crawler.addCitizensOfBundesgebiet()
    crawler.addGeneralDataOfWorld()

def extendedCrawlTask(crawler):
    """Germany & Poland"""

    crawler.addCitizensOfBundesgebiet()
    crawler.addCitizensOfCountry(35)
    crawler.addGeneralDataOfWorld()

def germanyAslovenia(crawler):
    """Germany & Slovenia"""
    
    crawler.addCitizensOfBundesgebiet()
    crawler.addCitizensOfCountry(61)
    crawler.addGeneralDataOfWorld()
    

if __name__ == '__main__':
    optparser = optparse.OptionParser()
    optparser.add_option("-t", "--type", dest="type", help="clarify what sort of crawling should be done\t[standard,extended,query]")
    (options, args) = optparser.parse_args()
    starttime = time.time()
    try:
        if options.type not in ["standard", "extended", "query"]:
            print "Wrong TYPE value"
            sys.exit()
        else:
            if options.type == "standard":
                crawler = ERepCrawler()
                #standardCrawlTask(crawler)
                crawler.printStats()
                print "executing standard task"
            elif options.type == "extended":
                crawler = ERepCrawler()
                #extendedCrawlTask(crawler)
                #germanyAslovenia(crawler)
                #crawler.addCitizensOfRegion(255)
                print "executing extended task"
                crawler.printStats()
            elif options.type == "query":
                dbInterface = ERepDBInterface()
                print "executing query task"
                #query = """SELECT citLevel, COUNT(citLevel) AS anzahl FROM citizens WHERE citCitshipCounID == 12 GROUP BY citLevel"""
                #query = """SELECT citCitshipCounName, COUNT(citCitshipCounID) as anzahl FROM citizens WHERE citResidenceCounID in (12) GROUP BY citCitshipCounID ORDER BY anzahl DESC"""

                #dbInterface.executeQuery(query)
                #dbInterface.printCurQueryResult()
                #dbInterface.writeCurQueryResult2CSV()
    except Exception, e:
        print "An error encountered: \n\t", e

    endtime = time.time()
    print "The script runned %f seconds" %(endtime-starttime)
