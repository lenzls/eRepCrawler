'''
Created on 03.04.2011

@author: simon
'''

import sys, os, time

class Logger(object):
    '''
    classdocs
    '''
    basepath = os.path.join(os.path.dirname(__file__), "..", "logs")
    initialized = False
    logfile = None

    @classmethod
    def initLogger(Logger):
        try:
            starttime = time.localtime()

            logName = "output_%s.log" %time.strftime("%Y-%m-%d--%H-%M-%S", starttime)
            logfilePath = os.path.join(Logger.basepath, logName)
        
            Logger.logfile = open(logfilePath, "w", 0)

            Logger.initialized = True
        except IOError, e:
            print "ERROR: While opening log-file"
            print "\t%s" %e

    @classmethod
    def log(Logger, line):
        if Logger.initialized:
            sys.stdout.write("%s: %s\n" %(time.strftime("%Y-%m-%d--%H-%M-%S", time.localtime()),str(line)))
            Logger.logfile.write("%s: %s\n" %(time.strftime("%Y-%m-%d--%H-%M-%S", time.localtime()),str(line)))
        else:
            print "logger not initalized!"
            sys.exit()
    
    @classmethod
    def log2File(Logger, line):
        if Logger.initialized:
            Logger.logfile.write("%s: %s\n" %(time.strftime("%Y-%m-%d--%H-%M-%S", time.localtime()),str(line)))
        else:
            print "logger not initalized!"
            sys.exit()

    @classmethod
    def close(Logger):
        Logger.logfile.close()

        
            