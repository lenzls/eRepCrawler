'''
Created on 24.03.2011

@author: simon
'''

from csv import CSV 
from database.eRepDB import eRepLokalDBManager

class ERepDBInterface(object):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.csv = CSV()
        self.eRepDB = eRepLokalDBManager()
        self.currentQuery = None
        self.currentQueryResult = None
    
    def executeQuery(self, query):
        self.currentQuery = query
        self.currentQueryResult = self.eRepDB.selectorQuery(self.currentQuery)
    
    def printCurQueryResult(self):
        print "++++++++++++++++++++++"
        print "executing query:\n %s" %self.currentQuery
        print "----------------------"
        print self.currentQueryResult
        
        
    def writeCurQueryResult2CSV(self):
        self.csv.writeCSVfromSQLResult(self.currentQueryResult)
