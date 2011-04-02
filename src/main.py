#!/usr/bin/python
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
    optparser.add_option("-q", "--query", dest="query", help="sql query as string")
    (options, args) = optparser.parse_args()
    starttime = time.time()
    print "Script started at: %s" %time.strftime("%Y-%m-%d [%H-%M-%S]", time.gmtime())
    try:
        if options.type not in ["standard", "extended", "query"]:
            print "Wrong TYPE value"
            sys.exit()
        else:
            if options.type == "standard":
                print "executing standard task"
                crawler = ERepCrawler()
                #standardCrawlTask(crawler)
                crawler.printStats()
            elif options.type == "extended":
                print "executing extended task"
                crawler = ERepCrawler()
                extendedCrawlTask(crawler)
                #germanyAslovenia(crawler)
                ##crawler.addCitizensOfRegion(255)
                crawler.printStats()
            elif options.type == "query":
                print "executing query task"
                dbInterface = ERepDBInterface()
                query = ""
                if None != options.query:
                    query = options.query
                #query = """SELECT citLevel, COUNT(citLevel) AS anzahl FROM citizens WHERE citCitshipCounID == 12 GROUP BY citLevel"""
                #query = """SELECT citWorkSkillPoints/20000*20000 as minValue, (citWorkSkillPoints/20000+1)*20000-1 as maxValue, COUNT(*) FROM citizens WHERE citCitshipCounID = 61 AND updateTimeDay == '2011-03-28' GROUP BY citWorkSkillPoints/20000"""
                
                dbInterface.executeQuery(query)
                dbInterface.printCurQueryResult()
                dbInterface.writeCurQueryResult2CSV()
    except Exception, e:
        print "An error encountered: \n\t", e

    endtime = time.time()
    print "The script runned %f seconds" %(endtime-starttime)
    print "Script ended at: %s" %time.strftime("%Y-%m-%d [%H-%M-%S]", time.gmtime())
