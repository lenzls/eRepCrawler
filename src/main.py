#!/usr/bin/python
'''
Created on 23.03.2011

@author: simon
'''

from eRepCrawler import ERepCrawler
from eRepDBInterface import ERepDBInterface
from logger import Logger
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
    Logger.initLogger()
    optparser = optparse.OptionParser()
    optparser.add_option("-t", "--type", dest="type", help="clarify what sort of crawling should be done\t[standard,extended,query]")
    optparser.add_option("-q", "--query", dest="query", help="sql query as string")
    (options, args) = optparser.parse_args()
    starttime = time.time()
    
    Logger.log("|eRepublik Crawler|")
    Logger.log("---Started logging---")
    Logger.log("Script started at: %s" %time.strftime("%Y-%m-%d [%H-%M-%S]", time.localtime()))
    try:
        if options.type not in ["standard", "extended", "query"]:
            Logger.log("Error: Wrong TYPE value")
        else:
            if options.type == "standard":
                Logger.log("executing standard task")
                crawler = ERepCrawler()
                standardCrawlTask(crawler)
                crawler.printStats()
            elif options.type == "extended":
                Logger.log("executing extended task")
                crawler = ERepCrawler()
                #extendedCrawlTask(crawler)
                #germanyAslovenia(crawler)
                crawler.addCitizensOfRegion(258)
                crawler.printStats()
            elif options.type == "query":
                Logger.log("executing query task")
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
        Logger.log("An error encountered:%s \n\t" %e)

    endtime = time.time()
    Logger.log("The script runned %f seconds = %f minutes = %f hours" %(endtime-starttime, (endtime-starttime)/60, (endtime-starttime)/60/24))
    Logger.log("Script ended at: %s" %time.strftime("%Y-%m-%d [%H-%M-%S]", time.localtime()))
    
    Logger.log("---Stopped logging---")

    print "script finished"
