""" Torrent-clean.py

This script searches the deluge state directory and checks if any iso file is no longer
available it will be removed."""

from optparse import OptionParser
from hashlib import sha1 as sha
import bencode
import ConfigParser
import logging.handlers
import logging
import subprocess
import threading
import thread
import Queue
import time
import shutil
import glob
import sys
import os
import re

# Default logging object
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

# Read all options from the configuration file
def readConfig(configFile):

    global stateDir, isoDir,Nice

    # Default values
    Nice = 20
    maxThreads = 5
    debugLimit = 0

    log.debug("Reading config from %s",configFile)
    parser = ConfigParser.SafeConfigParser()

    try:
        parser.read(configFile)

        isoDir = parser.get("directories","iso_directory")
        stateDir = parser.get("directories","state_directory")

        Nice = parser.getint("OS","nice_level")

    except ConfigParser.NoSectionError:
        log.error("Error reading config file")
        exit(1)

    dirExists(isoDir)
    dirExists(stateDir)

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
    sysFormatter = logging.Formatter('torrent.py['+str(pid)+': %(message)s')

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

    global pid
    pid = os.getpid()
    writeCounter = 0

    # Setup logging
    initLogging()

    # Read cli arguments
    readOptions()

    # Start application
    log.info("Torrent cleaner started")
    readConfig(configFile)

    # Set the script on the following nice level
    # Make it high, this script is not high prio
    os.nice(Nice)

    removed_counter = 0
    torrent_dict = dict()

    state_list = glob.glob(os.path.join(stateDir,"*.torrent"))
    for state_file in state_list:

        state_m_filedata = open(state_file, "rb").read()
        state_m_metadata = bencode.bdecode(state_m_filedata)
        try:
            state_iso_name = state_m_metadata["info"]["name"]

            # Store SHA1 identifier of torrent
            torrent_dict[state_iso_name] = sha(bencode.bencode(state_m_metadata["info"])).hexdigest()
            log.debug("State info, file[%s], name[%s]",state_file,state_iso_name)

        except KeyError:
            log.error("Cannot access info state file, %s",state_file)
            continue

    iso_list = glob.glob(os.path.join(isoDir,"*.iso"))
    for iso_fname in iso_list:

        if not os.path.isfile(iso_fname):

            iso_bname = os.path.basename(iso_fname)
            if iso_bname in torrent_dict:
                log.debug("Found old iso/torrent couple, %s",iso_fname)
                subprocess.call(["deluge-console","rm",torrent_dict[iso_bname]])
                os.remove(iso_fname)
                removed_counter = removed_counter + 1

    if removed_counter > 0:
        log.info("Result, torrents[%d], iso's[%d], removed couple [%d]",len(state_list),len(iso_list),removed_counter)
    else:
        log.info("No old torrents found")

if __name__ == "__main__":
    main(sys.argv)
