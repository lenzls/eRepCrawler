'''
Created on 23.03.2011

@author: simon
'''

import sqlite3
import os
import domarIRCbot.eRepublik as eRepTools
from logger import Logger


class eRepLokalDBManager():
    basepath = os.path.join(os.path.dirname(__file__), "..", "..")

    def __init__(self):
        self.connection = sqlite3.connect(os.path.join(eRepLokalDBManager.basepath,"eRepLokal.db"))
        self.connection.text_factory = str
        self.cursor = self.connection.cursor()
    
    def initializeNew(self):
        """creates and initializes a new local erep database
            if the database is already existing -> automatically skiped
        """

        Logger.log("try: creating citizens TABLE")
        try:
            self.cursor.execute("""CREATE TABLE citizens( 
                updateTime TEXT,
                updateTimeDay TEXT,
                citID INTEGER,
                citIsOrganisation BOOLEAN, 
                citNAME TEXT,
                citLevel INTEGER,
                citEXP INTEGER,
                citSex TEXT,
                citWellness INTEGER,
                citDateOfBirth TEXT,
                citWorkSkillPoints INTEGER,
                citIsGeneralManager BOOLEAN,
                citIsPresident BOOLEAN,
                citIsCongressman BOOLEAN,
                citIsPartyPresident BOOLEAN,
                citPartyName TEXT,
                citPartyID INTEGER,
                citMilitarySkillLevel TEXT,
                citMilitarySkillPoints INTEGER,
                citMilitaryRankPoints INTEGER,
                citMilitaryRank TEXT,
                citMilitaryStars INTEGER,
                citMilitaryTotalDamage INTEGER,
                citMilitaryFightCount INTEGER,
                citCompanyName TEXT,
                citCompanyID INTEGER,
                citCitshipRegName TEXT,
                citCitshipRegID INTEGER,
                citCitshipCounCode TEXT,
                citCitshipCounName TEXT,
                citCitshipCounID INTEGER,
                citResidenceRegName TEXT,
                citResidenceRegID INTEGER,
                citResidenceCounCode TEXT,
                citResidenceCounName TEXT,
                citResidenceCounID INTEGER,
                citMedals TEXT,
                citAvatarLink TEXT
                )""")
            
            Logger.log("created citizens TABLE")
        except sqlite3.OperationalError,  e:
            Logger.log("Error: %s" %e)

        print "try: creating countries TABLE"
        try:
            self.cursor.execute("""CREATE TABLE countries( 
                updateTime TEXT,
                updateTimeDay TEXT,
                countryID INTEGER,
                countryNAME TEXT,
                countryCitizenFee INTEGER,
                countryCurrency TEXT,
                countryContinent TEXT,
                countryCode TEXT,
                countryAvCitLvl INTEGER,
                countryCitCount INTEGER,
                countryRegCount INTEGER,
                countryRegions TEXT
                )""")
            
            Logger.log("created countries TABLE")
        except sqlite3.OperationalError,  e:
            Logger.log("Error: %s" %e)

    def addCitizen(self, id):
        """adds a row to the citizens table of the database"""

        cit = eRepTools.Citizen(id)
        cit.load()
        values = cit.__getstate__()
        values["medals"] = str(values["medals"]).replace(",", ";")
        values["updateTimeDay"] = values["updateTime"].strftime("%Y-%m-%d")
        query = """INSERT INTO citizens VALUES (
            :updateTime,
            :updateTimeDay,
            :id,
            :isOrganization,
            :name,
            :level,
            :experiencePoints,
            :sex,
            :wellness,
            :dateOfBirth,
            :workSkillPoints,
            :isGeneralManager,
            :isPresident,
            :isCongressman,
            :partyPresident,
            :party,
            :partyId,
            :militaryLevel,
            :militaryPoints,
            :rankPoints,
            :rank,
            :stars,
            :damage,
            :fightCount,
            :employer,
            :employerId,
            :citizenshipRegion,
            :citizenshipRegionId,
            :citizenshipCode,
            :citizenship,
            :citizenshipId,
            :residenceRegion,
            :residenceRegionId,
            :residenceCountryCode,
            :residenceCountry,
            :residenceCountryId,
            :medals,
            :avatarLink)"""
        self.cursor.execute(query, values)
        self.connection.commit()
        
        try:
            Logger.log("\t\t\tadded: %s (%i)" %(values["name"], values["id"]))    #commented because of too much output
            pass
        except UnicodeEncodeError:
            Logger.log("\tadded kyrillic name")
    
    def addGeneralDataOfCountry(self, id):
        """adds a row to the countries table of the database"""

        country = eRepTools.Country(id)
        country.load()
        values = country.__getstate__()
        
        values["regionDict"] = str(values["regionDict"]).replace(",",";")
        values["updateTimeDay"] = values["updateTime"].strftime("%Y-%m-%d")
        query = """INSERT INTO countries VALUES (
            :updateTime,
            :updateTimeDay,
            :id,
            :name,
            :citizenFee,
            :currency,
            :continent,
            :code,
            :avCitLvl,
            :citCount,
            :regCount,
            :regionDict
            )"""
        self.cursor.execute(query, values)
        self.connection.commit()

        try:
            Logger.log("\t\tadded: %s (%i)" %(values["name"], values["id"]))
        except UnicodeEncodeError:
            Logger.log("\tadded kyrillic name")
    
    def selectorQuery(self, query):
        """expects a sql selector query and returns the result of it"""

        self.cursor.execute(query)
        return self.cursor.fetchall()
