#!/usr/bin/python

import sys
import re
import argparse

# Parsing arguments
parser = argparse.ArgumentParser(
    description= 'Mail log parser', 
    epilog='Created by Robert Vojcik <robert@vojcik.net>')

# Example of sample arguments
parser.add_argument('-l', dest='logfile', default='/var/log/mail.log', help='Maillog file (default: /var/log/mail.log)') 
parser.add_argument('-f', dest='email_from', default='.*', help='From address') 
parser.add_argument('-t', dest='email_to', default='.*', help='To address') 
parser.add_argument('-q', dest='queue_id', default='\w+', help='Email queue ID') 
parser.add_argument('-v', dest='verbose', default=False, action="store_true", help='Verbose mode') 

args = parser.parse_args()

fh = open(args.logfile, 'r')

email_from_re = '(?P<email_from>'+args.email_from+')'
email_to_re = '(?P<email_to>'+args.email_to+')'

syslog_timestamp_re = '[A-Z][a-z]{2}\s[0-9]{1,2}\s{1,2}[0-9]{1,2}:[0-9]{1,2}:[0-9]{1,2}'

message_id = False

# Classes definition {{{
class colors:
    NOC     = '\033[0m'
    GREEN   = '\033[32m'
    HGREEN   = '\033[92m'
    HRED     = '\033[91m'
    RED     = '\033[31m'
    HBLUE    = '\033[94m'
    BLUE    = '\033[34m'
    AZURE    = '\033[36m'
    HAZURE    = '\033[96m'
    YELOW    = '\033[33m'
    HYELOW    = '\033[93m'
    WHITE    = NOC+'\033[1m'

class storage:
    MESSAGE_ID = False

#}}} Classes definition

# Functions definition {{{
def exit_script(msg,returncode):
    """Exist script"""
    if returncode == 0:
        msg_output = colors.GREEN + msg + colors.NOC
    else:
        msg_output = colors.RED + "ERROR: " + msg + colors.NOC

    print msg_output
    sys.exit(returncode)

def analyze_postfix_noqueue(line):
    # Postfix NOQUEUE
    re_compiled = re.compile('^(?P<timestamp>'+syslog_timestamp_re+')\s\w+\s(?P<daemon>.*)\[[0-9]+\]: (?P<queue>NOQUEUE): (?P<resolution>\w+): (?P<message>.*); from=<'+email_from_re+'> to=<'+email_to_re+'>.*$')
    match = re_compiled.match(line)
    if match != None:
        print '\nDaemon ('+match.group('daemon')+')'
        print '-------'
        print colors.WHITE+'Time: '+colors.AZURE+match.group('timestamp')
        print colors.WHITE+'From: '+colors.HBLUE+match.group('email_from')
        print colors.WHITE+'To: '+colors.HBLUE+match.group('email_to')
        print colors.WHITE+'Resolution: '+colors.RED+match.group('resolution')
        print colors.WHITE+'Message: '+colors.YELOW+match.group('message')+colors.NOC
        if args.verbose:
            print line

def analyze_cbpolicy(line):
    # CB Policyd
    re_compiled = re.compile('^(?P<timestamp>'+syslog_timestamp_re+')\s\w+\s(?P<daemon>.*)\[[0-9]+\]: module=(?P<module>.*), action=(?P<action>\w+), host=(?P<host>.*), helo=(?P<helo>.*), from='+email_from_re+', to='+email_to_re+', reason=(?P<reason>.*)$')
    match = re_compiled.match(line)
    if match != None:
        print '\nDaemon ('+match.group('daemon')+')'
        print '-------'
        print colors.WHITE+'Time: '+colors.AZURE+match.group('timestamp')
        print colors.WHITE+'From: '+colors.HBLUE+match.group('email_from')
        print colors.WHITE+'To: '+colors.HBLUE+match.group('email_to')
        print colors.WHITE+'Module: '+colors.YELOW+match.group('module')
        if match.group('action') == 'pass':
            col = colors.GREEN
        else:
            col = colors.RED
        print colors.WHITE+'Action: '+col+match.group('action')+colors.NOC 
        print colors.WHITE+'Host: '+colors.YELOW+match.group('host')+colors.NOC 
        print colors.WHITE+'HELO: '+colors.YELOW+match.group('helo')+colors.NOC 
        print colors.WHITE+'Reason: '+colors.YELOW+match.group('reason')+colors.NOC 
        if args.verbose:
            print line

def analyze_amavis_first(line, message_id='\w+'):

    # AMAVIS1
    re_compiled = re.compile('^(?P<timestamp>'+syslog_timestamp_re+')\s\w+\s(?P<daemon>.*)\[[0-9]+\]: \(.*\) (?P<resolution>\w+) (?P<filter_status>\w+) .* <'+email_from_re+'> -> <'+email_to_re+'>, Queue-ID: (?P<message_id>'+message_id+'),.* Hits: (?P<hits>[0-9.\-]+),.*queued_as: (?P<queue_id>\w+),.*$')
    match = re_compiled.match(line)
    if match != None:
        print '\nDaemon ('+match.group('daemon')+')'
        print '-------'
        print colors.WHITE+'Time: '+colors.AZURE+match.group('timestamp')
        print colors.WHITE+'From: '+colors.HBLUE+match.group('email_from')
        print colors.WHITE+'To: '+colors.HBLUE+match.group('email_to')
        if match.group('resolution') == 'Passed':
            col = colors.GREEN
        else:
            col = colors.RED
        print colors.WHITE+'Resolution: '+col+match.group('resolution')
        if match.group('filter_status') == 'CLEAN':
            col = colors.GREEN
        else:
            col = colors.RED
        print colors.WHITE+'State: '+col+match.group('filter_status')
        print colors.WHITE+'Message ID: '+colors.YELOW+match.group('message_id')
        print colors.WHITE+'Queue ID: '+colors.YELOW+match.group('queue_id')
        print colors.WHITE+'Hits: '+colors.YELOW+match.group('hits')+colors.NOC
        storage.MESSAGE_ID = match.group('queue_id')
        if args.verbose:
            print line

def analyze_postfix_queued(line, message_id='\w+'):
    re_compiled = re.compile('^(?P<timestamp>'+syslog_timestamp_re+')\s\w+\s(?P<daemon>.*)\[[0-9]+\]: \w+: to=<'+email_to_re+'>, relay=(?P<relay>.*), .*, status=(?P<status>\w+) .* queued as '+message_id+'\)$')
    match = re_compiled.match(line)
    if match != None:
        print '\nDaemon ('+match.group('daemon')+')'
        print '-------'
        print colors.WHITE+'Time: '+colors.AZURE+match.group('timestamp')
        print colors.WHITE+'To: '+colors.HBLUE+match.group('email_to')
        print colors.WHITE+'Relay: '+colors.AZURE+match.group('relay')
        if match.group('status') == 'sent':
            col = colors.GREEN
        else:
            col = colors.RED
        print colors.WHITE+'Status: '+col+match.group('status')+colors.NOC
        if args.verbose:
            print line

def analyze_postfix_queueactive(line, message_id='\w+'):

    # Postfix QUEUED
    re_compiled = re.compile('^(?P<timestamp>'+syslog_timestamp_re+')\s\w+\s(?P<daemon>postfix/qmgr)\[[0-9]+\]: (?P<message_id>'+message_id+'): from=<'+email_from_re+'>,.*\(queue active\).*$')
    match = re_compiled.match(line)
    if match != None:
        print '\nDaemon ('+match.group('daemon')+')'
        print '-------'
        print colors.WHITE+'Time: '+colors.AZURE+match.group('timestamp')
        print colors.WHITE+'From: '+colors.HBLUE+match.group('email_from')+colors.NOC
        print colors.WHITE+'Message ID: '+colors.HBLUE+match.group('message_id')+colors.NOC
        print colors.WHITE+'State: '+colors.HBLUE+'Queue active'+colors.NOC
        if args.verbose:
            print line
        storage.MESSAGE_ID = match.group('message_id')

def analyze_postfix_generic(line, message_id='\w+'):

    re_compiled = re.compile('^(?P<timestamp>'+syslog_timestamp_re+')\s\w+\s(?P<daemon>.*)\[[0-9]+\]: '+message_id+': to=<'+email_to_re+'>, relay=(?P<relay>.*), .*, status=(?P<status>\w+) (?P<message>.*)$')
    match = re_compiled.match(line)
    if match != None:
        print '\nDaemon ('+match.group('daemon')+')'
        print '-------'
        print colors.WHITE+'Time: '+colors.AZURE+match.group('timestamp')
        print colors.WHITE+'To: '+colors.HBLUE+match.group('email_to')
        print colors.WHITE+'Relay: '+colors.AZURE+match.group('relay')
        if match.group('status') == 'sent':
            col = colors.GREEN
        else:
            col = colors.RED
        print colors.WHITE+'Status: '+col+match.group('status')
        print colors.WHITE+'Message: '+colors.AZURE+match.group('message')+colors.NOC
        if args.verbose:
            print line
        storage.MESSAGE_ID = False


#}}}

# Default behaviour
for line in fh:
    if args.queue_id == '\w+':
        # Postfix NOQUEUE
        analyze_postfix_noqueue(line)
        # CB Policyd
        analyze_cbpolicy(line)
        # Find in amavis from->to email, get message_id
        analyze_amavis_first(line)
    else:
    # Find in amavis from->to email, get message_id
        analyze_postfix_queueactive(line, args.queue_id)
        analyze_amavis_first(line, args.queue_id)

    # Postfix2: find postfix  messages based on amavis message_id
    if storage.MESSAGE_ID != False:
        analyze_postfix_queued(line, storage.MESSAGE_ID)
        analyze_postfix_generic(line, storage.MESSAGE_ID)


fh.close()
exit_script("\nDone", 0)
