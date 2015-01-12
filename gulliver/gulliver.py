""" Gulliver.py

This scripts traverses the specific directory and gathers all torrent files 
and properly categorise them."""

from optparse import OptionParser
import ConfigParser
import logging.handlers
import logging
import threading
import thread
import Queue
import time
import shutil
import glob
import sys
import os
import re

from torrent.session import Session
from ui.console import consoleUI, consoleInput
from ui.console_handler import ProgressConsoleHandler

version = '0.0.1'
name = 'Gulliver'
input_run = True

# Default logging object
log = logging.getLogger('gulliver')
log.setLevel(logging.DEBUG)

# Read all options from the configuration file
def readConfig(configFile):

    global scanDir, isoDir, torrentDir,Nice,maxThreads, debug_limit

    # Default values
    Nice = 20
    maxThreads = 5
    debug_limit = 0

    log.debug("Reading config from %s",configFile)
    parser = ConfigParser.SafeConfigParser()

    try:
        parser.read(configFile)

        isoDir = parser.get("directories","iso_directory")
        scanDir = parser.get("directories","scan_directory")
        torrentDir = parser.get("directories","torrent_directory")

        Nice = parser.getint("OS","nice_level")
        maxThreads = parser.getint("OS","max_threads")
        debug_limit = parser.getint("debug","limit")

        # DebugLimit set to 0, means no limit
        if debug_limit > 0:
            log.debug("Debug limit set to %d",debug_limit)

    except ConfigParser.NoSectionError:
        log.error("Error reading config file")
        exit(1)

    dirExists(isoDir)
    dirExists(scanDir)
    dirExists(torrentDir)

# Check if given dir exists
def dirExists(tmpDir):
    if not os.path.isdir(tmpDir):
        log.error("%s does not exists",tmpDir)
        exit(5)

# Read command line arguments
def readOptions():

    global debugMode, configFile, logFile

    parser = OptionParser()
    parser.add_option("-c", "--config", dest="config", default="torrent.ini",help="Config file location, default=torrent.ini")
    parser.add_option("-d", "--debug", dest="debug",action="store_true",default=False, help="Print out debug statements")
    parser.add_option("-l", "--log", dest="log",default="", help="Log file location")

    options, args = parser.parse_args()

    logFile = options.log
    configFile = options.config
    debugMode = options.debug

    if debugMode:
        stdoutHandler.setLevel(logging.DEBUG)
        log.setLevel(logging.DEBUG)

    if logFile:
        initFileLogging()

# Setup file logging
def initFileLogging():

    formatter = logging.Formatter('%(asctime)s (%(levelname)s) - %(message)s')

    # Setup rotating file, limit is set to 1Mb
    fh = logging.handlers.RotatingFileHandler(logFile,maxBytes=(1024 * 1024),backupCount=3)
    fh.setFormatter(formatter)

    # Check if debug mode is enabled, and configure the FileHandler
    if debugMode:
        fh.setLevel(logging.DEBUG)
    else:
        fh.setLevel(logging.INFO)

    log.addHandler(fh)

# Set up logging mechanism
def initLogging():

    global stdoutHandler

    formatter = logging.Formatter('%(asctime)s (%(levelname)s) - %(message)s')
    sysFormatter = logging.Formatter(name+'['+str(pid)+']: %(message)s')

    # Set up syslog handler
    sh = logging.handlers.SysLogHandler(address='/dev/log')
    sh.setLevel(logging.INFO)
    sh.setFormatter(sysFormatter)
    log.addHandler(sh)

    # Enable logging
    stdoutHandler = logging.StreamHandler(sys.stdout)
    stdoutHandler.setLevel(logging.INFO)
    stdoutHandler.setFormatter(formatter)
    log.addHandler(stdoutHandler)

# Main method
def main(argv):

    global pid, debug_limit, input_run 
    pid = os.getpid()
    input_run = True

    # Setup logging
    initLogging()

    # Read cli arguments
    readOptions()

    # Start application
    log.info("%s (%s) started", name, version)
    readConfig(configFile)

    # Set the script on the following nice level
    # Make it high, this script is not high prio
    os.nice(Nice)

    lt_session = Session()
    console = consoleUI(lt_session)

    input_thread = consoleInput(console)
    input_thread.start()

    consoleHandler = ProgressConsoleHandler(console)
    consoleHandler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s (%(levelname)s) - %(message)s')
    consoleHandler.setFormatter(formatter)

    log.addHandler(consoleHandler)

    while input_thread.isAlive():

        console.update_status(lt_session.session_status())
        time.sleep(1)


if __name__ == "__main__":
    main(sys.argv)
