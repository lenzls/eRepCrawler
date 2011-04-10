'''
Created on 24.03.2011

@author: simon
'''

from database.eRepDB import eRepLokalDBManager
import domarIRCbot.eRepublik as eRepublikApi
from logger import Logger

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
        Logger.log("\t\tprocessing %i persons of region %i" %(len(region.citizen_ids), regionID))
        i = 0
        for citID in region.citizen_ids:
            i += 1
            Logger.log2File("\t\t\tperson nr %i / %i in region %i" %(i, len(region.citizen_ids), regionID))    #commented because of too much output
            self.addCitizen(citID)
        Logger.log("\t\tprocessed %i persons in region %i" %(len(region.citizen_ids), regionID))
        self.addedRegionsCitsC += 1
        
    def addCitizensOfCountry(self, countryID):
        country = eRepublikApi.Country(countryID)
        country.load()
        Logger.log("processing %i regions of country nr %i" %(len(country.regionDict),countryID))
        for regionID in country.regionDict:
            Logger.log("\tprocessing region  %s (%i)" %(country.regionDict[regionID], regionID))
            self.addCitizensOfRegion(regionID)
        self.addedCountriesCitsC += 1
    
    def addGeneralDataOfCountry(self, countryID):
        self.eRepDB.addGeneralDataOfCountry(countryID)
        self.addedGeneralDataCountriesC += 1
    
    def addGeneralDataOfWorld(self):
        countries = eRepublikApi.World()
        countries.load()
        Logger.log("processing %i countries" %len(countries.countryDict))
        for countryID in countries.countryDict:
            Logger.log("\tprocessing country %s (%i)" %(countries.countryDict[countryID], countryID))
            self.addGeneralDataOfCountry(countryID)
    
    def addCitizensOfBundesgebiet(self):
        Logger.log("#########################")
        Logger.log("processing good ol' germany")
        Logger.log("-------------------------")
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
        Logger.log("processing %i regions of good ol' germany" %(len(bundesgebietRegions)))
        for regionID in bundesgebietRegions:
            Logger.log("\tprocessing region %s (%i)" %(bundesgebietRegions[regionID], regionID))
            self.addCitizensOfRegion(regionID)
        self.addedCountriesCitsC += 1
    
    def addCitizensOfOriginalRomania(self):
        Logger.log("#########################")
        Logger.log("processing good ol' romania")
        Logger.log("-------------------------")
        romanianRegions = {
                    38:"Maramures",
                    11:"Banat",
                    3:"Dobrogea",
                    5:"Muntenia",
                    9:"Oltenia",
                    35:"Transilvania",
                    36:"Crisana",
                    37:"Moldova",
                    39:"Bucovina"
                    }
        Logger.log("processing %i regions of good ol' romania" %(len(romanianRegions)))
        for regionID in romanianRegions:
            Logger.log("\tprocessing region %s (%i)" %(romanianRegions[regionID], regionID))
            self.addCitizensOfRegion(regionID)
        self.addedCountriesCitsC += 1

    def printStats(self):
        Logger.log("+++++++++++++++++++++++++++++++++++")
        Logger.log("successfully processed citizens of:\n - %i countries \n - %i regions \n - %i citizens \n and country data of %i countries" %(self.addedCountriesCitsC,self.addedRegionsCitsC,self.addedPersonsC, self.addedGeneralDataCountriesC))
        Logger.log("+++++++++++++++++++++++++++++++++++")
        
