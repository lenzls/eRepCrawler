# -*- coding: utf-8 -*
#
#  Copyright (C) 2010 by Filip Brcic <brcha@gna.org>
#
#  eRepublik bot using python irc library (Army module)
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

from irc import IRCModule

from eRepublik import Army

from multiprocessing import RLock

class Define(IRCModule):
    def __init__(self, bot):
        super(Define, self).__init__(
            bot=bot,
            priority='low',
            rule=(['define_army', 'definisi armiju',], r'(\S+)'),
            name='define_army',
            doc='Define the army (no spaces in name)',
            example='.define_army zdrug',
            )
        if not hasattr(bot, 'armies_lock'):
            bot.armies_lock = RLock()

    def execute(self, bot, input):
        bot.armies_lock.acquire()
        try:
            name = input.group(2).lower()
        except:
            return

        if name.find(' ') != -1:
            bot.reply('Army cannot contain white spaces.')
            return

        if bot.db.has_key('armies') and name in bot.db['armies']:
            bot.reply('Army "%s" is already defined.')
            bot.armies_lock.release()
            return
        army = Army(name)
        armies = bot.db['armies']
        if armies is None:
            armies = dict()
        armies[name] = army
        bot.db['armies'] = armies
        bot.say('Army "%s" successfully defined.' % name)
        bot.armies_lock.release()

class ArmyACL(object):
    """ ACL management of the army """

    CHANNEL = 1 << 0
    GENERAL = 1 << 1
    
    def __init__(self):
        super(ArmyACL, self).__init__()

        self.channels = []
        self.generals = []

    def bind_channel(self, channel):
        channel = channel.lower()
        if not channel.startswith('#'):
            return
        if channel not in self.channels:
            self.channels.append(channel)

    def unbind_channel(self, channel):
        channel = channel.lower()
        if not channel.startswith('#'):
            return
        if channel in self.channels:
            self.channels.remove(channel)

    def is_bound(self, channel):
        return channel.lower() in self.channels

    def add_general(self, general):
        general = general.lower()
        if general not in self.generals:
            self.generals.append(general)

    def remove_general(self, general):
        general = general.lower()
        if general in self.generals:
            self.generals.remove(general)

    def is_general(self, general):
        return general.lower() in self.generals

    def check(self, input, level):
        ret = False
        if level & ArmyACL.CHANNEL:
            if len(self.channels) > 0:
                if self.is_bound(input.sender):
                    ret = True
            else:
                ret = True # No Channels defined => allow
        if level & ArmyACL.GENERAL:
            if len(self.generals) > 0:
                if self.is_general(input.nick):
                    ret = True
            else:
                ret = True # No Generals defined => allow
        return ret

    def __getstate__(self):
        return self.__dict__.copy()

    def __setstate__(self, dict):
        self.__dict__.update(dict)

class AddGeneral(IRCModule):
    def __init__(self, bot):
        super(AddGeneral, self).__init__(
            bot=bot,
            priority='low',
            threaded=True,
            rule=(['add_general', 'dodaj generala',], r'(\S+) +(\S+)'),
            name='add_general',
            doc='Add general of the army (by IRC name)',
            example='.add_general zdrug Hostilian',
            )
        if not hasattr(bot, 'armies_lock'):
            bot.armies_lock = RLock()

    def execute(self, bot, input):
        bot.armies_lock.acquire()
        try:
            name = input.group(2).lower()
        except:
            return

        general = input.group(3)
        if bot.db.has_key('armies') and name not in bot.db['armies']:
            bot.reply('Army "%s" is not defined.' % name)
            bot.armies_lock.release()
            return
        armies = bot.db['armies']
        army = armies[name]
        if not hasattr(army, 'acl'):
            army.acl = ArmyACL()
        if not army.acl.check(input, ArmyACL.GENERAL):
            bot.reply('You are not authorized to change anything in %s' % name)
            bot.armies_lock.release()
            return
        if army.acl.is_general(general):
            bot.reply('%s is already general of %s.' % (general, name))
            bot.armies_lock.release()
            return
        army.acl.add_general(general)
        armies[name] = army
        bot.db['armies'] = armies
        bot.say('%s added to %s generals' % (general, name))
        bot.armies_lock.release()

class RemoveGeneral(IRCModule):
    def __init__(self, bot):
        super(RemoveGeneral, self).__init__(
            bot=bot,
            priority='low',
            threaded=True,
            rule=(['remove_general', 'izbaci generala',], r'(\S+) +(\S+)'),
            name='remove_general',
            doc='Remove general of the army (by IRC name)',
            example='.remove_general zdrug Hostilian',
            )
        if not hasattr(bot, 'armies_lock'):
            bot.armies_lock = RLock()

    def execute(self, bot, input):
        bot.armies_lock.acquire()
        try:
            name = input.group(2).lower()
        except:
            return

        general = input.group(3)
        if bot.db.has_key('armies') and name not in bot.db['armies']:
            bot.reply('Army "%s" is not defined.' % name)
            bot.armies_lock.release()
            return
        armies = bot.db['armies']
        army = armies[name]
        if not hasattr(army, 'acl'):
            bot.reply('%s has no generals at the moment.' %name)   #fixed by SimonLenz 2011-03-23: bot.reply('%s has no generals at the moment.' %s)
            bot.armies_lock.release()
            return
        if not army.acl.check(input, ArmyACL.GENERAL):
            bot.reply('You are not authorized to change anything in %s' % name)
            bot.armies_lock.release()
            return
        if not army.acl.is_general(general):
            bot.reply('%s is not the general of %s.' % (general, name))
            bot.armies_lock.release()
            return
        army.acl.remove_general(general)
        armies[name] = army
        bot.db['armies'] = armies
        bot.say('%s removed from %s generals' % (general, name))
        bot.armies_lock.release()

class BindChannel(IRCModule):
    def __init__(self, bot):
        super(BindChannel, self).__init__(
            bot=bot,
            priority='low',
            threaded=True,
            rule=(['bind_channel', 'povezi kanal',], r'(\S+) +(\S+)'),
            name='bind_channel',
            doc='Bind the channel with the the army',
            example='.bind_channel zdrug #zdrug',
            )
        if not hasattr(bot, 'armies_lock'):
            bot.armies_lock = RLock()

    def execute(self, bot, input):
        bot.armies_lock.acquire()
        try:
            name = input.group(2).lower()
        except:
            return

        channel = input.group(3)
        if not channel.startswith('#'):
            bot.reply('Channel name should start with #.')
            bot.armies_lock.release()
            return
        if bot.db.has_key('armies') and name not in bot.db['armies']:
            bot.reply('Army "%s" is not defined.' % name)
            bot.armies_lock.release()
            return
        armies = bot.db['armies']
        army = armies[name]
        if not hasattr(army, 'acl'):
            army.acl = ArmyACL()
        if not army.acl.check(input, ArmyACL.GENERAL):
            bot.reply('You are not authorized to change anything in %s' % name)
            bot.armies_lock.release()
            return
        if army.acl.is_bound(channel):
            bot.reply('%s is already bound to %s.' % (channel, name))
            bot.armies_lock.release()
            return
        army.acl.bind_channel(channel)
        armies[name] = army
        bot.db['armies'] = armies
        bot.say('Channel %s bound to %s.' % (channel, name))
        bot.armies_lock.release()

class UnbindChannel(IRCModule):
    def __init__(self, bot):
        super(UnbindChannel, self).__init__(
            bot=bot,
            priority='low',
            threaded=True,
            rule=(['unbind_channel', 'odvezi kanal',], r'(\S+) +(\S+)'),
            name='unbind_channel',
            doc='Unbind the channel from the the army',
            example='.unbind_channel zdrug #zdrug',
            )
        if not hasattr(bot, 'armies_lock'):
            bot.armies_lock = RLock()

    def execute(self, bot, input):
        bot.armies_lock.acquire()
        try:
            name = input.group(2).lower()
        except:
            return

        channel = input.group(3)
        if not channel.startswith('#'):
            bot.reply('Channel name should start with #.')
            bot.armies_lock.release()
            return
        if bot.db.has_key('armies') and name not in bot.db['armies']:
            bot.reply('Army "%s" is not defined.' % name)
            bot.armies_lock.release()
            return
        armies = bot.db['armies']
        army = armies[name]
        if not hasattr(army, 'acl'):
            army.acl = ArmyACL()
        if not army.acl.check(input, ArmyACL.GENERAL):
            bot.reply('You are not authorized to change anything in %s' % name)
            bot.armies_lock.release()
            return
        if not army.acl.is_bound(channel):
            bot.reply('%s is not bound to %s.' % (channel, name))
            bot.armies_lock.release()
            return
        army.acl.unbind_channel(channel)
        armies[name] = army
        bot.db['armies'] = armies
        bot.say('Channel %s unbound from %s.' % (channel, name))
        bot.armies_lock.release()

class AddMember(IRCModule):
    def __init__(self, bot):
        super(AddMember, self).__init__(
            bot=bot,
            priority='low',
            threaded=True,
            rule=(['add_member', 'dodaj clana',], r'(\S+) +(.+)'),
            name='add_member',
            doc='Add member to the army',
            example='.add_member zdrug Hostilian',
            )
        if not hasattr(bot, 'armies_lock'):
            bot.armies_lock = RLock()

    def execute(self, bot, input):
        bot.armies_lock.acquire()
        try:
            name = input.group(2).lower()
        except:
            return

        member = input.group(3)
        if bot.db.has_key('armies') and name not in bot.db['armies']:
            bot.reply('Army "%s" is not defined.' % name)
            bot.armies_lock.release()
            return
        armies = bot.db['armies']
        army = armies[name]
        if hasattr(army, 'acl'):
            if not army.acl.check(input, ArmyACL.GENERAL):
                bot.reply('You are not authorized to change anything in %s' % name)
                bot.armies_lock.release()
                return
        if member in army:
            bot.reply('%s is already member of %s.' % (member, name))
        try:
            army.add(member)
        except Exception, e:
            bot.reply(e.message)
            bot.armies_lock.release()
            return
        armies[name] = army
        bot.db['armies'] = armies
        bot.say('%s added to %s members.' % (member, name))
        bot.armies_lock.release()

class RemoveMember(IRCModule):
    def __init__(self, bot):
        super(RemoveMember, self).__init__(
            bot=bot,
            priority='low',
            threaded=True,
            rule=(['remove_member', 'izbaci clana',], r'(\S+) +(.+)'),
            name='remove_member',
            doc='Remove member from the army',
            example='.remove_member zdrug Hostilian',
            )
        if not hasattr(bot, 'armies_lock'):
            bot.armies_lock = RLock()

    def execute(self, bot, input):
        bot.armies_lock.acquire()
        try:
            name = input.group(2).lower()
        except:
            return

        member = input.group(3)
        if bot.db.has_key('armies') and name not in bot.db['armies']:
            bot.reply('Army "%s" is not defined.' % name)
            bot.armies_lock.release()
            return
        armies = bot.db['armies']
        army = armies[name]
        if hasattr(army, 'acl'):
            if not army.acl.check(input, ArmyACL.GENERAL):
                bot.reply('You are not authorized to change anything in %s' % name)
                bot.armies_lock.release()
                return
        if member not in army:
            bot.reply('%s is not member of %s.' % (member, name))
            bot.armies_lock.release()
        try:
            army.remove(member)
        except Exception, e:
            bot.reply(e.message)
            bot.armies_lock.release()
            return
        armies[name] = army
        bot.db['armies'] = armies
        bot.say('%s removed from %s members.' % (member, name))
        bot.armies_lock.release()

class ListMembers(IRCModule):
    def __init__(self, bot):
        super(ListMembers, self).__init__(
            bot=bot,
            priority='low',
            threaded=True,
            commands=['list_members', 'ls', 'izlistaj clanove',],
            name='list_members',
            doc='List members of the army',
            example='.list_members',
            )
        if not hasattr(bot, 'armies_lock'):
            bot.armies_lock = RLock()

    def execute(self, bot, input):
        name = None
        if bot.db.has_key('armies'):
            for army in bot.db['armies'].values():
                if hasattr(army, 'acl'):
                    if army.acl.is_bound(input.sender):
                        name = army.name
                        break

        if name is None:
            bot.reply('No army is defined for this channel.')
            bot.armies_lock.release()
            return

        if bot.db.has_key('armies') and name not in bot.db['armies']:
            bot.reply('Army "%s" is not defined.' % name)
            return
        armies = bot.db['armies']
        army = armies[name]
        if hasattr(army, 'acl'):
            if not army.acl.check(input, ArmyACL.CHANNEL | ArmyACL.GENERAL):
                bot.reply('You are not authorized to read anything in %s' % name)
                bot.armies_lock.release()
                return
        members = map(lambda x: x.name, army.members)
        line = name + ' are: ' + ', '.join(members)
        lines = [line]
        if len(line) > 60:
            # Eyecandy: limit line length to 60
            line = name + ' are: '
            lines = []
            members.reverse()
            while len(members) > 0:
                while len(line) <= 60 and len(members) > 0:
                    line += members.pop()
                    line += ', '
                if len(members) > 0:
                    lines.append(line[:-1])
                    line = ''
                else:
                    lines.append(line[:-2])
        for line in lines:
            bot.say(line)

class ListGenerals(IRCModule):
    def __init__(self, bot):
        super(ListGenerals, self).__init__(
            bot=bot,
            priority='low',
            threaded=True,
            commands=['list_generals', 'generals', 'lsg', 'izlistaj generale', 'lopovi',],
            name='list_generals',
            doc='List generals of the army',
            example='.list_generals',
            )
        if not hasattr(bot, 'armies_lock'):
            bot.armies_lock = RLock()

    def execute(self, bot, input):
        name = None
        if bot.db.has_key('armies'):
            for army in bot.db['armies'].values():
                if hasattr(army, 'acl'):
                    if army.acl.is_bound(input.sender):
                        name = army.name
                        break

        if name is None:
            bot.reply('No army is defined for this channel.')
            bot.armies_lock.release()
            return

        if bot.db.has_key('armies') and name not in bot.db['armies']:
            bot.reply('Army "%s" is not defined.' % name)
            return
        armies = bot.db['armies']
        army = armies[name]
        if hasattr(army, 'acl'):
            if not army.acl.check(input, ArmyACL.CHANNEL | ArmyACL.GENERAL):
                bot.reply('You are not authorized to read anything in %s' % name)
                bot.armies_lock.release()
                return
        if not hasattr(army, 'acl'):
            bot.reply('%s has no generals.' % name)
            bot.armies_lock.release()
            return
        members = army.acl.generals
        line = 'Generals of ' + name + ' are: ' + ', '.join(members)
        lines = [line]
        if len(line) > 60:
            # Eyecandy: limit line length to 60
            line = 'Generals of ' + name + ' are: '
            lines = []
            members.reverse()
            while len(members) > 0:
                while len(line) <= 60 and len(members) > 0:
                    line += members.pop()
                    line += ', '
                if len(members) > 0:
                    lines.append(line[:-1])
                    line = ''
                else:
                    lines.append(line[:-2])
        for line in lines:
            bot.say(line)

class SetOrder(IRCModule):
    def __init__(self, bot):
        super(SetOrder, self).__init__(
            bot=bot,
            priority='low',
            threaded=True,
            rule=(['set_order', 'postavi naredjenje',], r'(\S+) +(.+)'),
            name='set_order',
            doc='Set the order for the army',
            example='.set_order zdrug Shoot for eSerbia in ...',
            )
        if not hasattr(bot, 'armies_lock'):
            bot.armies_lock = RLock()

    def execute(self, bot, input):
        bot.armies_lock.acquire()
        try:
            name = input.group(2).lower()
        except:
            return

        order = input.group(3)
        if bot.db.has_key('armies') and name not in bot.db['armies']:
            bot.reply('Army "%s" is not defined.' % name)
            bot.armies_lock.release()
            return
        armies = bot.db['armies']
        army = armies[name]
        if hasattr(army, 'acl'):
            if not army.acl.check(input, ArmyACL.GENERAL):
                bot.reply('You are not authorized to change anything in %s' % name)
                bot.armies_lock.release()
                return
        army.order = order
        armies[name] = army
        bot.db['armies'] = armies
        bot.say('Orders for %s set to %s' % (name, order))
        bot.armies_lock.release()

class Order(IRCModule):
    def __init__(self, bot):
        super(Order, self).__init__(
            bot=bot,
            priority='low',
            threaded=True,
            commands=['order', 'naredjenje',],
            name='order',
            doc='Get the order for the army',
            example='.order',
            )
        if not hasattr(bot, 'armies_lock'):
            bot.armies_lock = RLock()

    def execute(self, bot, input):
        name = None
        if bot.db.has_key('armies'):
            for army in bot.db['armies'].values():
                if hasattr(army, 'acl'):
                    if army.acl.is_bound(input.sender):
                        name = army.name
                        break

        if name is None:
            bot.reply('No army is defined for this channel.')
            bot.armies_lock.release()
            return

        if bot.db.has_key('armies') and name not in bot.db['armies']:
            bot.reply('Army "%s" is not defined.' % name)
            bot.armies_lock.release()
            return

        armies = bot.db['armies']
        army = armies[name]
        if hasattr(army, 'acl'):
            if not army.acl.check(input, ArmyACL.CHANNEL | ArmyACL.GENERAL):
                bot.reply('You are not authorized to read anything in %s' % name)
                bot.armies_lock.release()
                return
        if not hasattr(army, 'order'):
            bot.say('%s has no order' % name)
        else:
            bot.say('Order is: %s' % army.order)

