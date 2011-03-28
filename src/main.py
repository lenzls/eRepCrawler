'''
Created on 23.03.2011

@author: simon
'''

from eRepCrawler import ERepCrawler
from eRepDBInterface import ERepDBInterface
import time, sys

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
    starttime = time.time()
    try:
        crawler = ERepCrawler()
        dbInterface = ERepDBInterface()

        if len(sys.argv) > 1 and sys.argv[1] == "standard":
            standardCrawlTask(crawler)
        else:
            #extendedCrawlTask(crawler)

            crawler.printStats()
            #--------------------------------

            #query = """SELECT citLevel, COUNT(citLevel) AS anzahl FROM citizens WHERE citCitshipCounID == 12 GROUP BY citLevel"""
            #query = """SELECT citCitshipCounName, COUNT(citCitshipCounID) as anzahl FROM citizens WHERE citResidenceCounID in (12) GROUP BY citCitshipCounID ORDER BY anzahl DESC"""

            #dbInterface.executeQuery(query)
            #dbInterface.printCurQueryResult()
            #dbInterface.writeCurQueryResult2CSV()
    except Exception, e:
        print "An error encountered: \n\t", e

    endtime = time.time()
    print "The script runned %f seconds" %(endtime-starttime)
