# -*- coding: utf-8 -*
#
#  Copyright (C) 2009-2010 by Filip Brcic <brcha@gna.org>
#
#  This file is part of eRepublik IRC bot project
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

import sys
import os
import re
import time
import socket
import asyncore
import asynchat
import multiprocessing

def decode(bytes):
    """ helper function to decode unicode """
    try:
        text = bytes.decode('utf-8')
    except UnicodeDecodeError:
        try:
            text = bytes.decode('iso-8859-1')
        except UnicodeDecodeError:
            text = bytes.decode('cp1252')
    return text

class IRCMessageOrigin(object):
    """ Helper class for wrapping the origin of the IRC Message """
    source = re.compile(r'([^!]*)!?([^@]*)@?(.*)') # nick!user@host

    def __init__(self, bot, source, args):
        match = IRCMessageOrigin.source.match(source or '')
        self.nick, self.user, self.host = match.groups()

        if len(args) > 1:
            target = args[1]
        else:
            target = None

        mappings = {bot.nick: self.nick, None: None}
        self.sender = mappings.get(target, target)

class IRCBot(asynchat.async_chat, object):
    """ Main IRCBot class """
    def __init__(self, nick='IRCBot', name='IRCBot',
                 channels=None, serverpass=None, nickpass=None,
                 command_prefix='\.', verbose=True):
        asynchat.async_chat.__init__(self) # woa, doesn't support super???
        super(IRCBot, self).__init__()

        self.set_terminator('\n') # message terminator

        self.buffer = ''

        self.admins = []
        self.owner  = []

        self.nick = nick
        self.user = nick
        self.name = name
        self.serverpass = serverpass
        self.nickpass = nickpass
        self.command_prefix = command_prefix

        self.verbose = verbose
        self.channels = channels or []
        self.stack = []
        
        self.lck_send = multiprocessing.RLock()

    def __write(self, args, text=None):
        # low-level, unsafe write function
        try:
            if text is not None:
                print >> sys.stderr, (' '.join(args) + ' :' + text + '\r\n')
                self.push(' '.join(args) + ' :' + text + '\r\n')
            else:
                print >> sys.stderr, (' '.join(args) + '\r\n')
                self.push(' '.join(args) + '\r\n')
        except IndexError:
            pass

    def write(self, args, text=None):
        # safe write function
        def safe(input):
            # Remove new lines and encode in utf-8
            input = input.replace('\n', '')
            input = input.replace('\r', '')
            return input.encode('utf-8')
        try:
            args = [ safe(arg) for arg in args ]
            if text is not None:
                text = safe(text)
            self.lck_send.acquire()
            self.__write(args, text)
            self.lck_send.release()
        except Exception, e:
            pass

    def run(self, host, port=6667):
        """ Run the IRC client/bot """
        if self.verbose:
            print >> sys.stderr, ('Connecting to %s:%s ... ' % (host, port)),

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, port))

        try:
            asyncore.loop()
        except KeyboardInterrupt:
            sys.exit()

    def handle_connect(self):
        if self.verbose:
            print >> sys.stderr, '[ ok ]'
        if self.serverpass:
            self.write(('PASS', self.serverpass))
        self.write(('NICK', self.nick))
        self.write(('USER', self.user, '+iw', self.nick), self.name)

        # Initialize IRC Startup/Quit Modules
        IRCStartupModule(self)
        IRCQuitModule(self)
        IRCJoinModule(self)
        IRCPartModule(self)
        IRCDocModule(self)
        IRCCommandsModule(self)
        IRCHelpModule(self)
        IRCMsgModule(self)
        IRCMeModule(self)
        IRCCalcModule(self)
        IRCNoteModule(self)
        IRCSeenModule(self)

        self.after_connect()

    def after_connect(self):
        """ Redefine this to initialize the bot -- put your modules here """
        pass

    def handle_close(self):
        self.close()
        if self.verbose:
            print >> sys.stderr, 'Closed.'

    def collect_incoming_data(self, data):
        # Just append data to the buffer, will be handled when terminator is found
        self.buffer += data

    def found_terminator(self):
        # End of line found, handle buffer contents
        line = self.buffer
        if line.endswith('\r'):
            line = line[:-1]
        self.buffer = ''

        if self.verbose:
            print >> sys.stderr, '[DEBUG] ', line

        if line.startswith(':'):
            source, line = line[1:].split(' ', 1)
        else:
            source = None

        if ' :' in line:
            argstr, text = line.split(' :', 1)
        else:
            argstr, text = line, ''

        args = argstr.split()

        origin = IRCMessageOrigin(self, source, args)

        self.dispatch(origin, tuple([text] + args))

        if args[0] == 'PING':
            self.write(('PONG', text))

    def wrapped(self, origin, text, match):
        class BotWrapper(object):
            def __init__(self, bot):
                self.bot = bot

            def __getattr__(self, attr):
                sender = origin.sender or text
                if attr == 'reply':
                    return (lambda msg: self.bot.msg(sender, origin.nick + ': ' + msg))
                elif attr == 'say':
                    return (lambda msg: self.bot.msg(sender, msg))
                return getattr(self.bot, attr)

        return BotWrapper(self)

    def input(self, origin, text, bytes, match, event, args):
        # Return meta-string with request data
        class CommandInput(unicode):
            def __new__(cls, text, origin, bytes, match, event, args):
                s = unicode.__new__(cls, text)
                s.sender = origin.sender
                s.nick   = origin.nick
                s.event  = event
                s.bytes  = bytes
                s.match  = match
                s.group  = match.group
                s.groups = match.groups
                s.args   = args
                s.admin  = origin.nick in self.admins
                s.owner  = origin.nick in self.owner
                return s
        return CommandInput(text, origin, bytes, match, event, args)

    def dispatch(self, origin, args):
        """ Process messages here """
        bytes, event, args = args[0], args[1], args[2:]
        text = decode(bytes)

        for pri in ('high', 'medium', 'low'):
            for item in IRCModule.modules[pri]:
                if event != item.event:
                    continue

                match = item.match(text)
                if match:
                    input = self.input(origin, text, bytes, match, event, args)
                    bot   = self.wrapped(origin, text, match)
                    if item.threaded:
                        p = multiprocessing.Process(target=item.execute, args=(bot, input))
                        p.start()
                    else:
                        item.execute(bot, input)
                    
                    for source in [ origin.sender, origin.nick ]:
                        try:
                            item.stats[source] += 1
                        except KeyError:
                            item.stats[source]  = 1

    def msg(self, recipient, text):
        """ Send private message to IRC """
        self.lck_send.acquire()
        
        if isinstance(text, unicode):
            try:
                text = text.encode('utf-8')
            except UnicodeEncodeError, e:
                text = e.__class__ + ': ' + str(e)
        if isinstance(recipient, unicode):
            try:
                recipient = recipient.encode('utf-8')
            except UnicodeEncodeError, e:
                return

        # No messages within the last 3 seconds? Go ahead!
        # Otherwise, wait so it's been at least 0.8 seconds + penalty
        if self.stack:
            elapsed = time.time() - self.stack[-1][0]
            if elapsed < 3:
                penalty = float(max(0, len(text) - 50)) / 70
                wait = 0.8 + penalty
                if elapsed < wait:
                    time.sleep(wait - elapsed)
                    
        # Loop detection
        messages = [m[1] for m in self.stack[-8:]]
        if messages.count(text) >= 7:
            text = '...'
            if messages.count('...') >= 3:
                self.lck_send.release()
                return
            
        self.__write(('PRIVMSG', recipient), text)
        self.stack.append((time.time(), text))
        self.stack = self.stack[-10:]

        self.lck_send.release()

    def notice(self, dest, text):
        """ Send notice to IRC """
        self.write(('NOTICE', dest), text)

    def join(self, channel, key=None):
        """ Join the channel """
        if key is None:
            self.write(['JOIN', channel])
        else:
            self.write(['JOIN', channel, key])

    def part(self, channel):
        """ Part the channel """
        self.write(['PART'], channel)

    def identify(self, password, nickserv='NickServ'):
        """ Identify with nickserv """
        self.msg(nickserv, 'IDENTIFY %s' % password)
        time.sleep(5)

class IRCModule(object):
    """ Base class for all IRC modules """

    modules = { 'high': [], 'medium': [], 'low': [] }

    stats = {}

    docs = {}
    examples = {}
    acl = {}

    def __init__(self, bot, priority, rule=None, commands=None, event='PRIVMSG',
                 name=None, doc=None, example=None, acl=None,
                 threaded=False):
        super(IRCModule, self).__init__()

        self.priority = priority

        self.modules[self.priority].append(self)

        self.bot = bot

        self.event = event.upper()

        self.threaded = threaded

        if name is not None:
            name = name.lower() # use only lower case names
            self.name = name
            if doc is not None:
                self.docs[name] = doc.replace('$nickname', bot.nick)
            if example is not None:
                self.examples[name] = example.replace('$nickname', bot.nick)
            if acl is not None:
                self.acl[name] = acl

        def sub(pattern, bot=bot):
            # Replace variables in the rule
            pattern = pattern.replace('$nickname', bot.nick)
            return pattern.replace('$nick', r'%s[,:] +' % bot.nick)

        self.regexp = None
        
        if rule is not None:
            if type(rule) is str:
                pattern = sub(rule)
                self.regexp = re.compile(pattern)
            elif type(rule) is tuple:
                if len(rule) == 2 and type(rule[0]) is str:
                    # 1) ('$nick', '(regexp)') -- used for Domar: blablabla type of commands
                    prefix, pattern = rule
                    prefix = sub(prefix)
                    self.regexp = re.compile(prefix + pattern)
                    print 'Rule = %s' % (prefix + pattern)
                elif len(rule) == 2 and type(rule[0]) is list:
                    # 2) (['a', 'b'], '(regexp)') -- for privmsgs to Domar with commands
                    prefixes = bot.command_prefix
                    if type(bot.command_prefix) is not list:
                        prefixes = [ bot.command_prefix ]
                    for prefix in prefixes:
                        _commands, pattern = rule
                        self.regexp = []
                        for command in _commands:
                            command = r'(%s)\b(?: +(?:%s))?' % (command, pattern)
                            self.regexp.append(re.compile(prefix + command))
                elif len(rule) == 3:
                    # 3) ('$nick', ['a', 'b'], '(regexp)') -- for Domar: prefixed public commands
                    prefix, _commands, pattern = rule
                    prefix = sub(prefix)
                    self.regexp = []
                    for command in _commands:
                        command = r'(%s) +' % command
                        self.regexp.append(re.compile(prefix + command + pattern))
        if commands is not None:
            if self.regexp is not None:
                if type(self.regexp) is not list:
                    self.regexp = [ self.regexp ]
            else:
                self.regexp = []
            template = r'^%s(%s)(?: +(.*))?$'
            for command in commands:
                prefixes = bot.command_prefix
                if type(bot.command_prefix) is not list:
                    prefixes = [ bot.command_prefix ]
                for prefix in prefixes:
                    pattern = template % (prefix, command)
                    self.regexp.append(re.compile(pattern))
                    print 'Rule = %s' % pattern

    def match(self, text):
        if type(self.regexp) is list:
            for rx in self.regexp:
                match = rx.match(text)
                if match:
                    return match
            return None
        return self.regexp.match(text)

    def execute(self, bot, input):
        """ Implement the module here """
        pass

class IRCStartupModule(IRCModule):
    def __init__(self, bot):
        super(IRCStartupModule, self).__init__(
            bot=bot,
            priority='low',
            threaded=True,
            rule=r'(.*)',
            event='251')

    def execute(self, bot, input):
        if bot.nickpass is not None:
            bot.identify(bot.nickpass)

        for ch in bot.channels:
            bot.join(ch)
            time.sleep(1)

class IRCQuitModule(IRCModule):
    def __init__(self, bot):
        super(IRCQuitModule, self).__init__(
            bot=bot,
            priority='low',
            commands=['quit', 'umri', 'crkni', 'rikni', 'die'],
            name='quit',
            doc='Make the bot quit',
            example='.quit',
            )

    def execute(self, bot, input):
        if input.owner:
            bot.write(['QUIT'])
            os._exit(0)

class IRCJoinModule(IRCModule):
    def __init__(self, bot):
        super(IRCJoinModule, self).__init__(
            bot=bot,
            priority='low',
            rule=(['join', 'dodji', 'mars u', 'idi u', 'poseti'], '(#\S+)(?: *(\S+))?'),
            name='join',
            doc='Join the channel',
            example='.join #channel',
            acl='admin',
            )

    def execute(self, bot, input):
        try:
            channel = input.group(2)
        except:
            return
        if channel is None:
            return
        try:
            key = input.group(3)
        except IndexError:
            key = None
        if key is None:
            bot.join(channel)
        else:
            bot.join(channel, key)

class IRCPartModule(IRCModule):
    def __init__(self, bot):
        super(IRCPartModule, self).__init__(
            bot=bot,
            priority='low',
            commands=['part', 'izadji', 'mars iz', 'idi iz'],
            name='part',
            doc='Part the channel',
            example='.part #channel',
            acl='admin',
            )

    def execute(self, bot, input):
        channel = input.group(2)
        if channel is None:
            return
        bot.part(channel)

class IRCDocModule(IRCModule):
    def __init__(self, bot):
        super(IRCDocModule, self).__init__(
            bot=bot,
            priority='low',
            rule=('$nick', '(?i)(?:help|doc) +([A-Za-z_]+)(?:\?+)?$'),
            name='help',
            doc='Shows a command\'s documentation, and possibly an example.',
            example='$nickname: doc command?',
            )

    def execute(self, bot, input):
        name = input.group(1)
        if name is None:
            return
        name = name.lower()
        if self.acl.has_key(name):
            if (self.acl[name] == 'admin' and not input.admin) or \
                    (self.acl[name] == 'owner' and not input.owner):
                bot.reply('Sorry, you are not allowed to see that info')
                return
        if self.docs.has_key(name):
            bot.reply(self.docs[name])
            if self.examples.has_key(name):
                bot.say('ex. ' + self.examples[name])

class IRCCommandsModule(IRCModule):
    def __init__(self, bot):
        super(IRCCommandsModule, self).__init__(
            bot=bot,
            priority='low',
            commands=['commands', 'komande'],
            name='commands',
            doc='Show commands supported by the bot',
            )

    def execute(self, bot, input):
        names = ', '.join(sorted(self.docs.iterkeys()))
        bot.say('Recognized commands: ' + names + '.')
        bot.say('To find out more about individual commands, try "%s: help command?"' % bot.nick)

class IRCHelpModule(IRCModule):
    def __init__(self, bot):
        super(IRCHelpModule, self).__init__(
            bot=bot,
            priority='low',
            rule=('$nick', r'(?i)help(?:[?!]+)?$')
            )

    def execute(self, bot, input):
        resp = (
            'Hi, I\'m just a simple bot. If you want to know what I can do, '
            'then type ".commands" to get the list of supported commands, or '
            'if you are interested in seeing my source code, go and visit '
            'http://bitbucket.org/brcha/domar2/ for more info. My owner on '
            'this IRC server is %s so you can contact him too if you wish.'
            ) % bot.owner
        bot.reply(resp)

class IRCMsgModule(IRCModule):
    def __init__(self, bot):
        super(IRCMsgModule, self).__init__(
            bot=bot,
            priority='low',
            rule=(['msg'], r'(#?\S+) (.+)'),
            name='msg',
            doc='Send message to someone (accepted only in private message)',
            example='.msg #channel some message',
            acl='admin',
            )

    def execute(self, bot, input):
        if input.sender.startswith('#'):
            return
        try:
            target, message = input.group(2), input.group(3)
        except:
            return
        if target is None or message is None:
            return
        if input.admin:
            bot.msg(target, message)

class IRCMeModule(IRCModule):
    def __init__(self, bot):
        super(IRCMeModule, self).__init__(
            bot=bot,
            priority='low',
            rule=(['me'], r'(#?\S+) (.*)'),
            name='me',
            doc='Send /me action to some channel',
            example='.me #channel optional text',
            )

    def execute(self, bot, input):
        if input.sender.startswith('#'):
            return
        try:
            target = input.group(2)
            message = '\x01ACTION %s\x01' % input.group(3)
        except:
            return
        if target is None or message is None:
            return
        if input.admin:
            bot.msg(target, message)

import math
class IRCCalcModule(IRCModule):
    def __init__(self, bot):
        super(IRCCalcModule, self).__init__(
            bot=bot,
            priority='low',
            commands=['calc'],
            name='calc',
            doc='Calculate mathematical expressions',
            example='.calc 3 + 5*sin(13)',
            )

    def execute(self, bot, input):
        q = input.group(2)
        if not q:
            bot.say('0?')
            return

        try:
            # Allow math functions only
            try:
                res = eval(q, math.__dict__)
            except:
                bot.say('0?')
                return
            bot.say(str(res))
        except SyntaxError:
            bot.say('Syntax error in "%s"' % q)

class IRCNoteModule(IRCModule):
    def __init__(self, bot):
        super(IRCNoteModule, self).__init__(
            bot=bot,
            priority='low',
            rule=r'(.*)',
            )

    def execute(self, bot, input):
        if not hasattr(bot, 'db'):
            return
        if bot.db.has_key('seen'):
            seen = bot.db['seen']
        else:
            seen = dict()
        if input.sender.startswith('#'):
            seen[input.nick.lower()] = (input.sender, time.time())
            self.bot.db['seen'] = seen

class IRCSeenModule(IRCModule):
    def __init__(self, bot):
        super(IRCSeenModule, self).__init__(
            bot=bot,
            priority='low',
            rule=(['seen'], r'(\S+)'),
            name='seen',
            doc='Report if and when someone has been last seen ',
            example='.seen <nick>',
            )

    def execute(self, bot, input):
        nick = input.match.group(2)
        if nick is None:
            return
        nick = nick.lower()
        if not hasattr(bot, 'db'):
            return
        if not bot.db.has_key('seen'):
            bot.say('?')
            return
        if bot.db['seen'].has_key(nick):
            channel, t = bot.db['seen'][nick]
            t = time.ctime(t)
            msg = '%s was last seen at %s in %s' % (nick, t, channel)
            bot.say(msg)
        else:
            bot.say('Sorry, haven\'t seen %s around' % nick)
