#
#  Copyright (C) 2009-2011 by Filip Brcic <brcha@gna.org>
#
#  eRepublik eAPI python access library
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from math import ceil, floor

from datetime import tzinfo, timedelta, datetime

try:
    from xml.etree.cElementTree import *
except ImportError:
    from xml.etree.ElementTree import *

try:
    from cStringIO import *
except ImportError:
    from StringIO import *

from urllib import urlopen

class eRepublikXMLProcessor(object):
    " eRepublik XML Processing helper functions "
    def __init__(self):
        super(eRepublikXMLProcessor, self).__init__()

    def checkError(self, elem):
        return elem.tag == 'error'

    def getErrorMessage(self, elem):
        if self.checkError(elem):
            return self.findString(elem, 'message')
        return None

    def findString(self, elem, path):
        " Returns string or None from ElementTree Element "
        return elem.findtext(path) or "undefined"

    def findInt(self, elem, path):
        " Returns int or None from ElementTree Element "
        try:
            return int(float(elem.findtext(path))) or -1
        except TypeError:
            return -1
        except:
            return -1

    def findFloat(self, elem, path):
        " Returns float or None from ElementTree Element "
        try:
            return float(elem.findtext(path)) or -1.0
        except TypeError:
            return -1.0
        except:
            return -1.0

    def findBool(self, elem, path):
        " Returns bool or None from ElementTree Element "
        try:
            return (elem.findtext(path) == 'true') or False
        except TypeError:
            return False
        except:
            return False

# Useful time variables
ZERO = timedelta(0)
HOUR = timedelta(hours=1)

# A complete implementation of current DST rules for major US time zones.
def first_sunday_on_or_after(dt):
    days_to_go = 6 - dt.weekday()
    if days_to_go:
        dt += timedelta(days_to_go)
    return dt

# US DST Rules
DSTSTART_2007 = datetime(1, 3, 8, 2)
DSTEND_2007 = datetime(1, 11, 1, 1)
DSTSTART_1987_2006 = datetime(1, 4, 1, 2)
DSTEND_1987_2006 = datetime(1, 10, 25, 1)
DSTSTART_1967_1986 = datetime(1, 4, 24, 2)
DSTEND_1967_1986 = DSTEND_1987_2006

class USTimeZone(tzinfo):
    " US Time Zones tzinfo class "
    def __init__(self, hours=0, reprname=None, stdname=None, dstname=None):
        super(USTimeZone, self).__init__()
        self.stdoffset = timedelta(hours=hours)
        self.reprname = reprname
        self.stdname = stdname
        self.dstname = dstname

    def __repr__(self):
        return self.reprname

    def tzname(self, dt):
        if self.dst(dt):
            return self.dstname
        else:
            return self.stdname

    def utcoffset(self, dt):
        return self.stdoffset + self.dst(dt)

    def dst(self, dt):
        if dt is None or dt.tzinfo is None:
            # An exception may be sensible here, in one or both cases.
            # It depends on how you want to treat them.  The default
            # fromutc() implementation (called by the default astimezone()
            # implementation) passes a datetime with dt.tzinfo is self.
            return ZERO
        assert dt.tzinfo is self

        # Find start and end times for US DST. For years before 1967, return
        # ZERO for no DST.
        if 2006 < dt.year:
            dststart, dstend = DSTSTART_2007, DSTEND_2007
        elif 1986 < dt.year < 2007:
            dststart, dstend = DSTSTART_1987_2006, DSTEND_1987_2006
        elif 1966 < dt.year < 1987:
            dststart, dstend = DSTSTART_1967_1986, DSTEND_1967_1986
        else:
            return ZERO

        start = first_sunday_on_or_after(dststart.replace(year=dt.year))
        end = first_sunday_on_or_after(dstend.replace(year=dt.year))

        # Can't compare naive to aware objects, so strip the timezone from
        # dt first.
        if start <= dt.replace(tzinfo=None) < end:
            return HOUR
        else:
            return ZERO

    def __getstate__(self):
        return self.__dict__.copy()

    def __setstate__(self, dict):
        self.__dict__.update(dict)

Eastern  = USTimeZone(-5, "Eastern",  "EST", "EDT")
Central  = USTimeZone(-6, "Central",  "CST", "CDT")
Mountain = USTimeZone(-7, "Mountain", "MST", "MDT")
Pacific  = USTimeZone(-8, "Pacific",  "PST", "PDT")

eRepTZ   = USTimeZone(-8, 'eRepublik', 'eST', 'eDT') # Actually Pacific time, but this is better

# Helper lambda functions
add = lambda x, y: x + y
mul = lambda x, y: x * y

class Citizen(eRepublikXMLProcessor):
    " eRepublik Citizen class "
    url = 'http://api.erepublik.com/v2/feeds/citizens/%s'
    url_name = 'http://api.erepublik.com/v2/feeds/citizen_by_name/xml/%s'

    def __init__(self, arg=None):
        super(Citizen, self).__init__()

        self.id = arg
        self.loaded = False

    def load(self):
        if hasattr(self, 'error'):
            return False
        if self.id == None:
            return False
        if self.loaded:
            return True

        try:
            self.id = int(self.id)
        except ValueError:
            pass

        if type(self.id) is int:
            arg = Citizen.url % str(self.id)
        elif type(self.id) is str or type(self.id) is unicode:
            arg = Citizen.url_name % self.id
        else:
            return False
        xml = ''.join(urlopen(arg))
        cit = XML(xml)

        if self.checkError(cit):
            self.error = self.getErrorMessage(cit)
            self.loaded = True
            return False

        # Process data
        self.isOrganization = self.findBool(cit, 'is-organization')

        self.residenceRegion = self.findString(cit, 'residence/region/name')
        self.residenceRegionId = self.findInt(cit, 'residence/region/id')
        self.residenceCountry = self.findString(cit, 'residence/country/name')
        self.residenceCountryCode = self.findString(cit, 'residence/country/code')
        self.residenceCountryId = self.findInt(cit, 'residence/country/id')

        self.avatarLink = self.findString(cit, 'avatar-link')

        self.dateOfBirth = self.findString(cit, 'date-of-birth')

        self.name = self.findString(cit, 'name')

        self.isGeneralManager = self.findBool(cit, 'is-general-manager')

        self.id = self.findInt(cit, 'id')

        if not self.isOrganization:
            self.citizenshipRegion = self.findString(cit, 'citizenship/region/name')
            self.citizenshipRegionId = self.findString(cit, 'citizenship/region/id')
            self.citizenship = self.findString(cit, 'citizenship/country/name')
            self.citizenshipCode = self.findString(cit, 'citizenship/country/code')
            self.citizenshipId = self.findInt(cit, 'citizenship/country/id')

            self.wellness = self.findInt(cit, 'wellness')

            self.isCongressman = self.findBool(cit, 'is-congressman')

            self.level = self.findInt(cit, 'level')
            
            self.sex = self.findString(cit, 'sex')

            # Process skills
            self.workSkillPoints = self.findInt(cit, 'work-skill-points')

            # Process medals
            medalRoot = cit.find('medals')
            self.medals = dict()
            if medalRoot != None:
                for m in medalRoot:
                    self.medals[self.findString(m, 'type')] = self.findInt(m, 'amount')

            self.employer = self.findString(cit,'employer/name')
            self.employerId = self.findInt(cit, 'employer/id')

            self.fightCount = self.findInt(cit, 'military/fight-count')
            self.stars = self.findInt(cit, 'military/stars')
            self.rank = self.findString(cit, 'military/rank')
            self.rankPoints = self.findInt(cit, 'military/rank-points')
            self.damage = self.findInt(cit, 'military/total-damage')

            # Process military skills
            self.militaryLevel = self.findString(cit, 'military-skills/military-skill/level')
            self.militaryName = self.findString(cit, 'military-skills/military-skill/name')
            self.militaryPoints = self.findInt(cit, 'military-skills/military-skill/points')

            self.party = self.findString(cit, 'party/name')
            self.partyId = self.findInt(cit, 'party/id')
            self.partyPresident = self.findBool(cit, 'party/president')

            self.experiencePoints = self.findInt(cit, 'experience-points')
            self.isPresident = self.findBool(cit, 'is-president')

        self.updateTime = datetime.now(eRepTZ)

        if type(self.id) == int:
            self.loaded = True

        return self.loaded

    def rankString(self):
        rankStr = self.rank
        stars = self.stars
        while stars > 0:
            rankStr += '*'
            stars = stars - 1
        return rankStr

    def rankAsNumber(self):
        self.load()
        ranks = [
            'recruit',
            'private',
            'private*',
            'private**',
            'private***',
            'corporal',
            'corporal*',
            'corporal**',
            'corporal***',
            'sergeant',
            'sergeant*',
            'sergeant**',
            'sergeant***',
            'lieutenant',
            'lieutenant*',
            'lieutenant**',
            'lieutenant***',
            'captain',
            'captain*',
            'captain**',
            'captain***',
            'major',
            'major*',
            'major**',
            'major***',
            'commander',
            'commander*',
            'commander**',
            'commander***',
            'lt colonel',
            'lt colonel*',
            'lt colonel**',
            'lt colonel***',
            'colonel',
            'colonel*',
            'colonel**',
            'colonel***',
            'general',
            'general*',
            'general**',
            'general***',
            'field marshal',
            'field marshal*',
            'field marshal**',
            'field marshal***',
            'supreme marshal',
            'supreme marshal*',
            'supreme marshal**',
            'supreme marshal***',
            'national force',
            'national force*',
            'national force**',
            'national force***',
            'world class force',
            'world class force*',
            'world class force**',
            'world class force***',
            'legendary force',
            'legendary force*',
            'legendary force**',
            'legendary force***',
            'god of war',
            ]
        return ranks.index(self.rankString().lower()) + 1

    def fightCalc(self):
        ran = self.rankAsNumber()

        dmg = ((ran - 1)/20.0 + 0.3) * (self.militaryPoints/10.0 + 40.0)

        return [ int(floor(dmg * (1 + x/100.0))) for x in (0, 20, 40, 60, 80, 100) ]

    def fightCalcStr(self):
        fc = self.fightCalc()
        return ', '.join([ 'Q%s: %s' % (str(i), str(fc[i])) for i in range(0,6) ])

    def toString(self):
        if not self.load():
            if hasattr(self, 'error'):
                return self.error
            else:
                return 'Citizen/organization doesn\'t exist'

        if self.isOrganization:
            ret = self.name + '(org)'
        else:
            ret = self.name
        ret += ': Location: ' + self.residenceCountry + ', ' + self.residenceRegion

        if not self.isOrganization:
            ret += '; Skill: ' + str(self.workSkillPoints)

            ret += '; Strength: ' + str(self.militaryPoints)

            ret += (
                '; Rank: ' + self.rankString() +
                ' (' + str(self.damage or 0) + ' dmg)' +
                '; Wellness: ' + str(self.wellness or 0) +
                '; Level: ' + str(self.level or 0) +
                ' (' + str(self.experiencePoints or 0) + ')' +
                '; '
            )

            if self.party is not None:
                ret += 'Party: ' + self.party
                if self.partyPresident:
                    ret += '(pres)'
                ret += '; '

            if self.employer is not None:
                ret += 'Employed at: ' + self.employer
            else:
                ret += 'unemployed' 

            ret += (
                '; Citizenship: ' + self.citizenship + ', ' +
                self.citizenshipRegion
                )

        return ret

    def __eq__(self, other):
        " Two Citizens are equal if their ID is the same "
        if not self.loaded:
            return False
        if type(other) is Citizen or type(other) is CitizenWithHistory:
            if other.loaded:
                return self.id == other.id
        elif type(other) is int:
            if self.id == other:
                return True
        elif type(other) is str or type(other) is unicode:
            if hasattr(self, 'name') and self.name.lower() == other.lower(): # case doesn't matter
                return True
        return False

    def __hash__(self):
        " Return citizen's id "
        self.load()
        return self.id

    def __getstate__(self):
        self.load()
        return self.__dict__.copy()

    def __setstate__(self, dict):
        self.__dict__.update(dict)

class CitizenWithHistory(object):
    " Citizen that saves citizen history "
    def __init__(self, arg=None):
        self.history = []

        if type(arg) == Citizen:
            self.history.append(arg)
        else:
            cit = Citizen(arg)
            if not cit.load():
                raise Exception('Citizen "%s" doesn\'t exist!' % arg)
            self.history.append(cit)

    def update(self):
        " Get another update of the citizen "
        cit = Citizen(self.history[-1].id)
        cit.load()
        self.history.append(cit)

    def __getattribute__(self, name):
        " Proxy attributes to last updated history item "
        try:
            return super(CitizenWithHistory, self).__getattribute__(name)
        except:
            return self.history[-1].__getattribute__(name)

    def __eq__(self, other):
        " Two Citizens are equal if their ID is the same "
        if not self.loaded:
            return False
        if type(other) is Citizen or type(other) is CitizenWithHistory:
            if other.loaded:
                return self.id == other.id
        elif type(other) is int:
            if self.id == other:
                return True
        elif type(other) is str or type(other) is unicode:
            if hasattr(self, 'name') and self.name.lower() == other.lower(): # case doesn't matter
                return True
        return False

    def __hash__(self):
        " Return citizen's id "
        self.load()
        return self.id

    def __getstate__(self):
        return self.__dict__.copy()

    def __setstate__(self, dict):
        self.__dict__.update(dict)

class Army(object):
    " eRepublik Army class "
    def __init__(self, name=None, logo=None):
        super(Army, self).__init__()
        self.name = name
        self.logo = logo
        self.members = []

    def add(self, member):
        if type(member) != CitizenWithHistory:
            cit = CitizenWithHistory(member)
        else:
            cit = member
        if cit not in self.members:
            self.members.append(cit)

    def remove(self, member):
        if member in self.members:
            self.members.remove(member)

    def update(self):
        map(lambda x : x.update(), self.members)

    def fightCalc(self, wellness=None):
        res = [ 0 for x in range(6) ]
        for member in self.members:
            res = map(add, res, member.fightCalc(wellness))
        return res

    def __contains__(self, what):
        return what in self.members

    def __getstate__(self):
        return self.__dict__.copy()

    def __setstate__(self, dict):
        self.__dict__.update(dict)        

class BattleFeed(eRepublikXMLProcessor):
    " eRepublik battle feed class "
    url = 'http://api.erepublik.com/v1/feeds/battle_logs/%s/%s'

    def __init__(self, arg=None):
        super(BattleFeed, self).__init__()

        self.id = arg
        self.curPage = -1
        self.maxPages = -1
        self.attacker = None
        self.attackerId = None
        self.defender = None
        self.defenderId = None
        self.raw_battles = None
        self.battles = None
        self.loaded = False
        self.processed = False

    def load(self):
        if self.id == None:
            raise Exception('id=None and BattleFeed.load was called')
        if self.loaded or self.processed:
            return
        while self._loadNextPage():
            print 'Loaded page ' + str(self.curPage)
        self.loaded = True

    def process(self):
        self.load()
        if self.processed:
            return
        battles = Element('battles')
        battles.attrib['id'] = str(self.id)
        battles.attrib['attacker'] = self.attacker
        battles.attrib['attacker-id'] = str(self.attackerId)
        battles.attrib['defender'] = self.defender
        battles.attrib['defender-id'] = str(self.defenderId)
        for b in self.raw_battles.findall('battle'):
            battle = Element('battle')
            battle.attrib['time'] = b.find('time').text
            battle.attrib['damage'] = b.find('damage').text
            battle.attrib['citizen'] = b.find('citizen').text
            battle.attrib['citizen-id'] = b.find('citizen-id').text
            battles.append(battle)
        self.battles = ElementTree(battles)
        del self.raw_battles # free some memory
        self.processed = True

    def _loadNextPage(self):
        if not self._getNextPage():
            return False
        
        xml = ''.join(urlopen(BattleFeed.url % (str(self.id), str(self.curPage))).readlines())
        bl = XML(xml)
        battleInfo = bl.find('battle-info')
        self.maxPages = self.findInt(battleInfo, 'max-pages')
        if not self.attacker:
            self.attacker = self.findString(battleInfo, 'attacker')
            self.attackerId = self.findInt(battleInfo, 'attacker-id')
            self.defender = self.findString(battleInfo, 'defender')
            self.defenderId = self.findInt(battleInfo, 'defender-id')

        if not self.raw_battles:
            self.raw_battles = ElementTree(bl.find('battles'))
        else:
            for b in bl.findall('battles/battle'):
                self.raw_battles.getroot().append(b)
        return True

    def _getNextPage(self):
        """ Sets curPage to next available page and returns true or
            returns false if there are no more pages available.
            """
        if self.curPage == -1:
            self.curPage = 0
            return True
        if self.maxPages > self.curPage:
            self.curPage = self.curPage + 1
            return True
        return False

    def _findBattlesByCitizenId(self, citizenId):
        """
        returns list of damages done by citizen(by citizenId)
        """
        self.process()

        damage = []
        for b in self.battles.findall('battle'):
            if int(b.attrib['citizen-id']) == citizenId:
                # Found
                damage.append(int(b.attrib['damage']))
        return damage

    def findBattles(self, arg):
        self.process()

        if type(arg) == int:
            return self._findBattlesByCitizenId(arg)
        elif type(arg) == Citizen or type(arg) == CitizenWithHistory:
            return self._findBattlesByCitizenId(arg.id)
        elif type(arg) == Army:
            damage = dict()
            for m in arg.members:
                damage[m.name] = self._findBattlesByCitizenId(m.id)
            return damage

    def __str__(self):
        self.process()

        f = StringIO()
        self.battles.write(f)
        f.reset()
        return ''.join(f.readlines())

    def __getstate__(self):
        odict = dict()
        odict['battles'] = str(self)
        return odict

    def __setstate__(self, dict):
        self.battles = ElementTree(XML(dict['battles']))
        self.processed = True
        self.loaded = True
        root = self.battles.getroot()
        self.id = root.attrib['id']
        self.attacker = root.attrib['attacker']
        self.attackerId = int(root.attrib['attacker-id'])
        self.defender = root.attrib['defender']
        self.defenderId = int(root.attrib['defender-id'])

class Region(eRepublikXMLProcessor):
    " eRepublik region class "
    url = 'http://api.erepublik.com/v2/feeds/regions/%s'
    url_citizens = 'http://api.erepublik.com/v2/feeds/regions/%s/citizens/%s'

    def __init__(self, arg=None):
        super(Region, self).__init__()

        self.id = arg
        self.loaded = False

    def load(self):
        if self.id == None:
            raise Exception('id=None and Region.load was called')
        if self.loaded:
            return
        
        if type(self.id) != int:
            raise Exception('Invalid id, id should be int')

        xml = ''.join(urlopen(Region.url % str(self.id)))
        reg = XML(xml)

        # Process data
        # ...

        # Process citizens
        self.citizen_ids = []
        pageId = 0
        pageCount = 1
        while pageId < pageCount:
            xml = ''.join(urlopen(Region.url_citizens % (str(self.id), str(pageId))))
            reg_cit = XML(xml)

            pageCount = self.findInt(reg_cit, 'page-count')
            cits = reg_cit.find('citizens')
            for id_el in cits.findall('citizen/id'):
                self.citizen_ids.append(int(id_el.text))
            pageId = pageId + 1            

class Country(eRepublikXMLProcessor):
    " eRepublik country class "
    url = 'http://api.erepublik.com/v2/feeds/countries/%s'

    def __init__(self, arg=None):
        super(Country, self).__init__()

        self.id = arg
        self.loaded = False

    def load(self):
        if self.id == None:
            raise Exception('id=None and Country.load was called')
        if self.loaded:
            return
        
        if type(self.id) != int:
            raise Exception('Invalid id, id should be int')

        xml = ''.join(urlopen(Country.url % str(self.id)))

        self.regionDict = {}

        country = XML(xml)

        self.id = self.findInt(country, 'id')
        self.name = self.findString(country, 'name')
        self.citizenFee = self.findInt(country, 'citizen-fee')
        self.currency = self.findString(country, 'currency')
        self.continent = self.findString(country, 'continent')
        self.code = self.findString(country, 'code')
        self.avCitLvl = self.findInt(country, 'average-citizen-level')
        self.citCount = self.findInt(country, 'citizen-count')
        self.regCount = self.findInt(country, 'region-count')
        regions = country.find('regions')
        for region in regions.findall('region'):
            self.regionDict[self.findInt(region, 'id')] = self.findString(region, 'name')
        
        self.updateTime = datetime.now(eRepTZ)

        if type(self.id) == int:
            self.loaded = True

        return self.loaded

    def __getstate__(self):
        return self.__dict__.copy()

class World(eRepublikXMLProcessor):
    """world class  stores a dict of countries"""
    
    url = 'http://api.erepublik.com/v2/feeds/countries'

    def __init__(self):
        super(World, self).__init__()

        self.loaded = False

    def load(self):

        if self.loaded:
            return

        xml = ''.join(urlopen(World.url))

        countries = XML(xml)
        
        self.countryDict = {}

        for country in countries.findall('country'):
            self.countryDict[int(country.find('id').text)] = country.find('name').text
