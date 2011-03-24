#! /usr/bin/env python
# -*- coding: utf-8 -*
#
#  Copyright (C) 2009-2010 by Filip Brcic <brcha@gna.org>
#
#  eRepublik bot using python irc library
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

import random
import time
import multiprocessing
from optparse import OptionParser

import feedparser

from irc import IRCBot, IRCModule
from db import DB, DBManagerProcess
from eRepublik import Citizen

import army_modules

class HelloModule(IRCModule):
    def __init__(self, bot):
        super(HelloModule, self).__init__(
            bot=bot,
            priority='low',
            rule=r'(?i)(hi|hello|hey|bok|poz|zdravo|pozz|ave|cao|juhu) $nickname\b'
            )

    def execute(self, bot, input):
        greeting = random.choice(('Hi', 'Hey', 'Hello', 'Bok', 'Poz', 'Pozz', 'Cao',
                                  'Ave', 'Juhu',))
        punctuation = random.choice(('', '!'))
        bot.say(greeting + ' ' + input.nick + punctuation)

class CurseModule(IRCModule):
    def __init__(self, bot):
        super(CurseModule, self).__init__(
            bot=bot,
            priority='low',
            rule=r'(?i)(pusi.*|jedi.*|mars|pederu) $nickname\b'
            )

    def execute(self, bot, input):
        greeting = random.choice(('Mars bre', 'Odbi', 'I ja tebi,', 'Ha ha,', 'Pederu',))
        punctuation = random.choice(('', '!'))
        bot.say(greeting + ' ' + input.nick + punctuation)

class CitizenInfoModule(IRCModule):
    def __init__(self, bot):
        super(CitizenInfoModule, self).__init__(
            bot=bot,
            priority='low',
            threaded=True,
            commands=['info', 'opisi', 'ko je'],
            name='info',
            doc='Show info on eRepublik citizen',
            example='.info admin',
            )

    def execute(self, bot, input):
        try:
            cit_name = int(input.group(2))
        except ValueError:
            cit_name = input.group(2)
        cit = Citizen(cit_name)
        bot.say(cit.toString())
        # Store citizen for future use
        ctzns = bot.db['citizens']
        if ctzns is None:
            ctzns = []
        if cit not in ctzns:
            ctzns.append(cit)
            bot.db['citizens'] = ctzns

class CitizenLinkModule(IRCModule):
    def __init__(self, bot):
        super(CitizenLinkModule, self).__init__(
            bot=bot,
            priority='low',
            threaded=True,
            commands=['link'],
            name='link',
            doc='Show the link to eRepublik citizen\'s profile',
            example='.link admin',
            )

    def execute(self, bot, input):
        try:
            cit_name = int(input.group(2))
        except ValueError:
            cit_name = input.group(2)
        if cit_name in bot.db.get('citizens', []):
            ndx = bot.db['citizens'].index(cit_name)
            cit = bot.db['citizens'][ndx]
        else:
            cit = Citizen(cit_name)
            cit.load()
            ctzns = bot.db.get('citizens', [])
            if cit not in ctzns:
                ctzns.append(cit)
                bot.db['citizens'] = ctzns
        bot.say('http://www.erepublik.com/en/citizen/profile/%s' % cit.id)

class CitizenDonateModule(IRCModule):
    def __init__(self, bot):
        super(CitizenDonateModule, self).__init__(
            bot=bot,
            priority='low',
            threaded=True,
            commands=['donate', 'daj'],
            name='donate',
            doc='Show the donation link of an eRepublik citizen',
            example='.donate admin',
            )

    def execute(self, bot, input):
        try:
            cit_name = int(input.group(2))
        except ValueError:
            cit_name = input.group(2)
        if cit_name in bot.db.get('citizens', []):
            ndx = bot.db['citizens'].index(cit_name)
            cit = bot.db['citizens'][ndx]
        else:
            cit = Citizen(cit_name)
            cit.load()
            ctzns = bot.db.get('citizens', [])
            if cit not in ctzns:
                ctzns.append(cit)
                bot.db['citizens'] = ctzns
        bot.say('http://economy.erepublik.com/en/citizen/donate/%s' % cit.id)

class CitizenHealthIncreaseModule(IRCModule):
    def __init__(self, bot):
        super(CitizenHealthIncreaseModule, self).__init__(
            bot=bot,
            priority='low',
            threaded=True,
            rule=(['health'], r'([^:]*)(?:\: *(\S+)(?: *(\S+))?)?'),
            name='health',
            doc='Show health increase of the citizen',
            example='.health citizen: food [house]',
            )

    def execute(self, bot, input):
        try:
            cit_name = int(input.group(2))
        except ValueError:
            cit_name = input.group(2)
        cit = Citizen(cit_name)
        cit.load()
        ctzns = bot.db.get('citizens', [])
        if cit not in ctzns:
            ctzns.append(cit)
            bot.db['citizens'] = ctzns
        try:
            food = float(input.group(3))
        except IndexError:
            # No food => assume 1
            food = 1
        except TypeError:
            # No food => assume 1
            food = 1
        except ValueError:
            bot.reply('Food increase "%s" is not parsable...' % input.group(3))
        try:
            house = float(input.group(4))
        except IndexError:
            # No house => assume no house (0)
            house = 0
        except TypeError:
            # No house => assume no house (0)
            house = 0
        except ValueError:
            bot.reply('House increase "%s" is not parsable...' % input.group(4))
        health_increase = (1.5 - (cit.wellness / 100.0)) * (food + house)
        health_tomorrow = cit.wellness + health_increase
        if health_tomorrow > 100:
            health_tomorrow = 100
        bot.reply('%s\'s wellness tomorrow will be %s (+%s)' % (cit.name,
                                                                health_tomorrow,
                                                                health_increase))
            
class CitizenHappinessIncreaseModule(IRCModule):
    def __init__(self, bot):
        super(CitizenHappinessIncreaseModule, self).__init__(
            bot=bot,
            priority='low',
            threaded=True,
            rule=(['happiness', 'happy'], r'([^:]*)(?:\: *(\S+)(?: *(\S+))?)?'),
            name='happiness',
            doc='Show happiness increase of the citizen',
            example='.happiness citizen: food [house]',
            )

    def execute(self, bot, input):
        try:
            cit_name = int(input.group(2))
        except ValueError:
            cit_name = input.group(2)
        cit = Citizen(cit_name)
        cit.load()
        ctzns = bot.db.get('citizens', [])
        if cit not in ctzns:
            ctzns.append(cit)
            bot.db['citizens'] = ctzns
        try:
            food = float(input.group(3))
        except IndexError:
            # No food => assume 1
            food = 1
        except TypeError:
            # No food => assume 1
            food = 1
        except ValueError:
            bot.reply('Food increase "%s" is not parsable...' % input.group(3))
        try:
            house = float(input.group(4))
        except IndexError:
            # No house => assume no house (0)
            house = 0
        except TypeError:
            # No house => assume no house (0)
            house = 0
        except ValueError:
            bot.reply('House increase "%s" is not parsable...' % input.group(4))
        happiness_increase = (1.5 - (cit.happiness / 100.0)) * (food + house)
        happiness_tomorrow = cit.happiness + happiness_increase
        if happiness_tomorrow > 100:
            happiness_tomorrow = 100
        bot.reply('%s\'s happiness tomorrow will be %s (+%s)' % (cit.name,
                                                                 happiness_tomorrow,
                                                                 happiness_increase))

class CitizenFightModule(IRCModule):
    def __init__(self, bot):
        super(CitizenFightModule, self).__init__(
            bot=bot,
            priority='low',
            threaded=True,
            commands=['fight', 'borba', 'fc', 'fight_calc', ],
            name='fight',
            doc='Show info on eRepublik citizen''s fight capabilities',
            example='.fight admin',
            )

    def execute(self, bot, input):
        try:
            cit_name = int(input.group(2))
        except ValueError:
            cit_name = input.group(2)
        cit = Citizen(cit_name)
        cit.load()
        bot.say(cit.name + ': ' + cit.fightCalcStr())
        # Store citizen for future use
        ctzns = bot.db['citizens']
        if ctzns is None:
            ctzns = []
        if cit not in ctzns:
            ctzns.append(cit)
            bot.db['citizens'] = ctzns

class eRepublikRSSFeeder(multiprocessing.Process):
    urls = [
        ('military', 'http://www.erepublik.com/rss/allMilitaryEvents'),
#        ('wars', 'http://www.erepublik.com/rss/allWars'),
#        ('mpp', 'http://www.erepublik.com/rss/mpp'),
        ]

    def __init__(self, bot, delay, initialdelay=240):
        super(eRepublikRSSFeeder, self).__init__()
        self.bot = bot
        self.delay = delay
        self.initialdelay = initialdelay
        self.firstrun = True

        self.last_updated = dict()

        self.die = False

    def run(self):
        time.sleep(self.initialdelay)

        while not self.die:
            time.sleep(self.delay)

            if not self.bot.db.has_key('rss_channels'):
                continue
            if len(self.bot.db.get('rss_channels', [])) == 0:
                continue

            entries_to_show = []

            for (feed_name, feed_url) in eRepublikRSSFeeder.urls:
                f = feedparser.parse(feed_url)
                feed_time = time.mktime(f.feed.updated_parsed)
                if not self.last_updated.has_key(feed_name):
                    self.last_updated[feed_name] = time.time() - 60*60*24 # juce
                if self.last_updated[feed_name] < feed_time:
                    # Feed has new data
                    if not self.firstrun:
                        for i in range(0, len(f.entries)):
                            entry_time = time.mktime(f.entries[i].updated_parsed)
                            if self.last_updated[feed_name] < entry_time:
                                # New entry
                                entries_to_show.append(feed_name + ' event: ' + f.entries[i].title)
                    self.last_updated[feed_name] = feed_time
            self.firstrun = False
            entries_to_show.reverse()
            for chan in self.bot.db.get('rss_channels', []):
                if chan not in self.bot.db.get('channels', []):
                    continue
                for entry in entries_to_show:
                    self.bot.msg(chan, entry)

class RSSEnableModule(IRCModule):
    def __init__(self, bot):
        super(RSSEnableModule, self).__init__(
            bot=bot,
            priority='low',
            threaded=True,
            commands=['rss_enable', 'enable rss', 'ukljuci rss',],
            name='rss_enable',
            doc='Enable eRepublik RSS in the chanel',
            example='.rss_enable #channel',
            )

    def execute(self, bot, input):
        chan = input.group(2)
        if not chan.startswith('#'):
            bot.reply('Invalid channel format "%s"' % chan)
            return
        if chan not in bot.db.get('rss_channels', []):
            rssc = bot.db.get('rss_channels', [])
            rssc.append(chan)
            bot.db['rss_channels'] = rssc
            bot.say('RSS enabled')

class RSSDisableModule(IRCModule):
    def __init__(self, bot):
        super(RSSDisableModule, self).__init__(
            bot=bot,
            priority='low',
            threaded=True,
            commands=['rss_disable', 'disable rss', 'iskljuci rss',],
            name='rss_disable',
            doc='Disable eRepublik RSS in the chanel',
            example='.rss_disable #channel',
            )

    def execute(self, bot, input):
        chan = input.group(2)
        if not chan.startswith('#'):
            bot.reply('Invalid channel format "%s"' % chan)
            return
        if chan in bot.db.get('rss_channels', []):
            rssc = bot.db.get('rss_channels', [])
            rssc.remove(chan)
            bot.db['rss_channels'] = rssc
            bot.say('RSS disabled')

class CondorsPlataModule(IRCModule):
    def __init__(self, bot):
        super(CondorsPlataModule, self).__init__(
            bot=bot,
            priority='low',
            threaded=True,
            rule=(['condors_plata'], r'(\S+) *(\S+) *(\S+) *(\S+)'),
            )

    def execute(self, bot, input):
        if input.sender != '#condorsu':
            return
        try:
            prod, hleb, raw, sati = map(lambda x: float(input.match.group(x)), [2,3,4,5])
        except:
            return
        if prod is None or hleb is None or raw is None or sati is None:
            return
        zarada_sa_minimalcem = (hleb/45.0 - raw)*prod*0.7
        zarada_bez_minimalca = zarada_sa_minimalcem - 0.25*sati # 0.25 je minimalac
        bot.reply('Zarada sa minimalcem je %5.4s, a bez minimalca je %5.4s' %
                  (zarada_sa_minimalcem, zarada_bez_minimalca)
                  )

class Domar(IRCBot):
    def __init__(self,
                 nick='Domar',
                 nickpass='qwerty',
                 server='irc.mibbit.com',
                 port=6667,
                 channel='#domar'):
        super(Domar, self).__init__(nick=nick,
                                    name='Domar bot, http://bitbucket.org/brcha/domar2',
                                    channels=[ channel, ],
                                    nickpass=nickpass,
                                    command_prefix=['!', '\.'],
				    verbose=False)

        self.server = server
        self.port = port

        self.db = DBManagerProcess(DB('erep.db'))
        self.db.start()
        self.admins   = self.db.get('admins', ['Hostilian', 'Rx_Queen'])
        self.owner    = self.db.get('owner',  ['Hostilian'])
        self.channels = self.db.get('channels', self.channels)
        self.db['admins']   = self.admins
        self.db['owner']    = self.owner
        self.db['channels'] = self.channels

        # Initialize citizens cache array
        citizens = self.db.get('citizens', [])
        self.db['citizens'] = citizens

        # Initialize RSS channels array
        rss_channels = self.db.get('rss_channels', [])
        self.db['rss_channels'] = rss_channels

        self.rssFeeder = eRepublikRSSFeeder(self, 60) # get RSS every 60 seconds
        
    def run(self):
        super(Domar, self).run(host=self.server, port=self.port)

    def after_connect(self):
        # Initialize modules
        HelloModule(self)
        CurseModule(self)
        CitizenInfoModule(self)
        CitizenLinkModule(self)
        CitizenDonateModule(self)
        CitizenFightModule(self)
        RSSEnableModule(self)
        RSSDisableModule(self)
        CitizenHealthIncreaseModule(self)
        CitizenHappinessIncreaseModule(self)
        CondorsPlataModule(self)
        # Army modules
        army_modules.Define(self)
        army_modules.AddGeneral(self)
        army_modules.RemoveGeneral(self)
        army_modules.BindChannel(self)
        army_modules.UnbindChannel(self)
        army_modules.AddMember(self)
        army_modules.RemoveMember(self)
        army_modules.ListMembers(self)
        army_modules.ListGenerals(self)
        army_modules.SetOrder(self)
        army_modules.Order(self)

        # Start RSS feeder
        self.rssFeeder.start()

    def join(self, channel, key=None):
        # Keep track of channels to make them persistent
        if not channel.startswith('#'):
            return
        super(Domar, self).join(channel, key)
        if not channel in self.db['channels']:
            channels = self.db['channels']
            channels.append(channel)
            self.db['channels'] = channels

    def part(self, channel):
        # Keep track of channels to make them persistent
        if not channel.startswith('#'):
            return
        super(Domar, self).part(channel)
        if channel in self.db['channels']:
            channels = self.db['channels']
            channels.remove(channel)
            self.db['channels'] = channels

    def handle_close(self):
        self.rssFeeder.die = True
        self.rssFeeder.join(65)
        self.rssFeeder.terminate()
        self.db.die()
        super(Domar, self).__del__()

    def __del__(self):
        self.rssFeeder.terminate()
        super(Domar, self).__del__()

if __name__ == '__main__':
    options = OptionParser()
    options.add_option('-n', '--nick', dest='nick', default='Domar',
                       help='Use NICK as IRC nickname', metavar='NICK')
    options.add_option('', '--password', dest='password',
                       help='Set NickServ password', metavar='PASS')
    options.add_option('-s', '--server', dest='server', default='irc.mibbit.com',
                       help='Use SERVER as IRC server', metavar='SERVER')
    options.add_option('-p', '--port', dest='port', default=6667, type='int',
                       help='Specify PORT for connecting to IRC server', metavar='PORT')
    options.add_option('-c', '--channel', dest='channel', default='#domar',
                       help='Join CHANNEL as an initial channel', metavar='CHANNEL')

    (options, args) = options.parse_args()

    domar = Domar(
        nick=options.nick,
        nickpass=options.password,
        server=options.server,
        port=options.port,
        channel=options.channel,
        )
    domar.run()
