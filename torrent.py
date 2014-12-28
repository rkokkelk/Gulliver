""" Torrent.py

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

# Default logging object
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class Scanner(threading.Thread):
    """
    Scan Thread, this class scans for a sets of .torrent/.iso files.

    Only direct sets are currently possible so 

    test_db-4.1.2.iso / test_db-4.1.2.iso.torrent --> work
    test_db-4.1.2.iso / test_db-4.1_2.iso.torrent --> does not work
    """

    # Regex, precompiled to increase speed
    prog_iso = re.compile("\w*\.iso$")

    # create log
    log = logging.getLogger("torrent_scanner")
    log.setLevel(logging.DEBUG)

    # Constructor
    def __init__(self, scanQueue, resultQueue):
        threading.Thread.__init__(self)
        self.scanQueue = scanQueue
        self.resultQueue = resultQueue
        self.ID = thread.get_ident()

    # Scan method
    def scan(self,scanDir):

        index = -1
        isoList = list()
        torList = list()

        # Walk through all subdirectories of the top directory
        for root, dirs, files in os.walk(scanDir):

            tmp_torrent_list = glob.glob(os.path.join(root,"*.torrent"))
            tmp_torrent_list.extend(glob.glob(os.path.join(root,"*.torrents")))
            tmp_iso_list = glob.glob(os.path.join(root,"*.iso"))

            torList.extend(tmp_torrent_list)
            isoList.extend(tmp_iso_list)

        log.debug("Result %s: (%d) torrents, (%d) iso",scanDir,len(torList),len(isoList))

        # Matching .torrent files with the corret .iso
        for tor_file in torList:
            tor_base_name = os.path.basename(tor_file)
            rmTor = re.sub(".torrent(s)?$",'',tor_base_name)

            # Some torrents are stored as following abc.1.2.torrent --> abc.1.2.iso
            # so in order to fix this, .iso is appended if there is no file extension
            if self.prog_iso.search(rmTor) is None:
                rmTor = rmTor + ".iso"

            for iso_file in isoList:
                iso_base_name = os.path.basename(iso_file)
                if iso_base_name == rmTor:
                    result = (tor_file,iso_file)
                    self.resultQueue.put(result)

    # Thread run method
    def run(self):

        # Loop through directories until queue is empty
        while not self.scanQueue.empty():
            scanDir = self.scanQueue.get()
            self.scan(scanDir)
            self.scanQueue.task_done()

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
    sysFormatter = logging.Formatter('torrent.py['+str(pid)+']: %(message)s')

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

    global pid, debug_limit
    pid = os.getpid()
    writeCounter = 0

    # Setup logging
    initLogging()

    # Read cli arguments
    readOptions()

    # Start application
    log.info("Torrent scan started")
    readConfig(configFile)

    # Set the script on the following nice level
    # Make it high, this script is not high prio
    os.nice(Nice)

    # Queues
    scanQueue = Queue.Queue()
    resultQueue = Queue.Queue()

    # Retrieve number of iso already seeding
    seed_num = len([seed for seed in os.listdir(isoDir) if os.path.islink(os.path.join(isoDir,seed))])

    # Check if debugLimit is already triggered, if not only allow the rest number
    # of seeds to be written
    if debug_limit > 0 and seed_num >= debug_limit:
        log.warn("Debug seed limit hit! %d",debug_limit)
        exit(seed_num)
    elif debug_limit > 0 and True:
        debug_limit -= seed_num
        log.debug("%d seed(s) available",debug_limit)

    # Retrieve all 1 level subdirectories, used for thread for each Arc, Ubuntu repo
    dir_list = [ name for name in os.listdir(scanDir) if os.path.isdir(os.path.join(scanDir, name)) ]
    log.info("Scan directory size: %d",len(dir_list))

    # Enter every subdir in the queue
    for subDir in dir_list:
        scanQueue.put(os.path.join(scanDir,subDir))

    # Start the threads
    for i in range(maxThreads):
        thread = Scanner(scanQueue,resultQueue)
        thread.setDaemon(True)
        thread.start()

    # Wait for threads to finish
    scanQueue.join()
    log.info("%d torrent/iso sets found",resultQueue.qsize())

    # Process results
    while not resultQueue.empty():

        # Limit to write iso/tor, used for debug
        if debug_limit > 0 and writeCounter >= debug_limit:
            log.warn("Debug seed limit hit!")
            break

        # Get result tuple
        result = resultQueue.get()
        tor_file = result[0]
        iso_file = result[1]

        tor_base_name = os.path.basename(tor_file)
        iso_base_name = os.path.basename(iso_file)
        isoDestName = os.path.join(isoDir,iso_base_name)
        torDestName = os.path.join(torrentDir,tor_base_name)

        # The file does not already exists, so create symbolic link and copy torrent file
        if not os.path.exists(isoDestName) and not os.path.exists(torDestName):
            os.symlink(iso_file,isoDestName)
            shutil.copy2(tor_file,torDestName)
            writeCounter = writeCounter +1

        resultQueue.task_done()

    log.info("%d torrent/iso sets written",writeCounter)

if __name__ == "__main__":
    main(sys.argv)
