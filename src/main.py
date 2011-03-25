'''
Created on 23.03.2011

@author: simon
'''

from eRepCrawler import ERepCrawler
from eRepDBInterface import ERepDBInterface

def standardCrawlTask(crawler):
    crawler.addCitizensOfBundesgebiet()
    crawler.addGeneralDataOfWorld()
    crawler.printStats()

if __name__ == '__main__':

    crawler = ERepCrawler()

    standardCrawlTask(crawler)
    #crawler.addCitizensOfBundesgebiet()
    #crawler.addCitizen(3051253)
    #crawler.addGeneralDataOfWorld()
    #crawler.printStats()
    
    

    #query = """SELECT citLevel, COUNT(citLevel) AS anzahl FROM citizens WHERE citCitshipCounID == 12 GROUP BY citLevel"""
    #query = """SELECT citMilitaryRank, COUNT(citMilitaryRank) AS anzahl FROM citizens WHERE citCitshipCounID == 12 GROUP BY citMilitaryRank"""

    dbInterface = ERepDBInterface()
    #dbInterface.executeQuery(query)
    #dbInterface.printCurQueryResult()
    #dbInterface.writeCurQueryResult2CSV()
    
    
    
    