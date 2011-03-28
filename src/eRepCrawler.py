'''
Created on 24.03.2011

@author: simon
'''

from database.eRepDB import eRepLokalDBManager
import domarIRCbot.eRepublik as eRepublikApi

class ERepCrawler(object):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.eRepDB = eRepLokalDBManager()
        self.eRepDB.initializeNew()
        
        self.addedPersonsC = 0
        self.addedRegionsCitsC = 0
        self.addedCountriesCitsC = 0

        self.addedGeneralDataCountriesC = 0
        
    def addCitizen(self, citID):
        self.eRepDB.addCitizen(citID)
        self.addedPersonsC += 1

    def addCitizensOfRegion(self, regionID):
        region = eRepublikApi.Region(regionID)
        region.load()
        print "processing %i persons of region %i" %(len(region.citizen_ids), regionID)
        i = 0
        for citID in region.citizen_ids:
            i += 1
            #print "\tperson nr %i / %i in region %i" %(i, len(region.citizen_ids), regionID)    #commented because of too much output
            self.addCitizen(citID)
        print "\tprocessed %i persons in region %i" %(len(region.citizen_ids), regionID)
        self.addedRegionsCitsC += 1
        
    def addCitizensOfCountry(self, countryID):
        country = eRepublikApi.Country(countryID)
        country.load()
        print "processing %i regions of country nr %i" %(len(country.regionDict),countryID)
        for regionID in country.regionDict:
            print "processing region  %s (%i)" %(country.regionDict[regionID], regionID)
            self.addCitizensOfRegion(regionID)
        self.addedCountriesCitsC += 1
    
    def addGeneralDataOfCountry(self, countryID):
        self.eRepDB.addGeneralDataOfCountry(countryID)
        self.addedGeneralDataCountriesC += 1
    
    def addGeneralDataOfWorld(self):
        countries = eRepublikApi.World()
        countries.load()
        print "processing %i countries" %len(countries.countryDict)
        for countryID in countries.countryDict:
            print "processing country %s (%i)" %(countries.countryDict[countryID], countryID)
            self.addGeneralDataOfCountry(countryID)
    
    def addCitizensOfBundesgebiet(self):
        print "#########################"
        print "processing good ol' germany"
        print "-------------------------"
        bundesgebietRegions = {
                    243:"Baden-Wurttemberg",
                    244:"Bavaria",
                    246:"Brandenburg and Berlin",
                    249:"Hesse",
                    250:"Mecklenburg-Western Pomerania",
                    251:"Lower Saxony and Bremen",
                    252:"North Rhine-Westphalia",
                    253:"Rhineland-Palatinate",
                    254:"Saarland",
                    255:"Saxony",
                    256:"Saxony-Anhalt",
                    257:"Schleswig-Holstein and Hamburg",
                    258:"Thuringia"
                    }
        print "processing %i regions of good ol' germany" %(len(bundesgebietRegions))
        for regionID in bundesgebietRegions:
            print "processing region %s (%i)" %(bundesgebietRegions[regionID], regionID)
            self.addCitizensOfRegion(regionID)
        self.addedCountriesCitsC += 1
    
    def printStats(self):
        print "+++++++++++++++++++++++++++++++++++"
        print "successfully processed citizens of:\n - %i countries \n - %i regions \n - %i citizens \n and country data of %i countries" %(self.addedCountriesCitsC,self.addedRegionsCitsC,self.addedPersonsC, self.addedGeneralDataCountriesC)
        print "+++++++++++++++++++++++++++++++++++"
        
