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

log = logging.getLogger(__name__+"scan_thread")

class Scan_Thread(threading.Thread):
    """
    Scan Thread, this class scans for a sets of .torrent/.iso files.

    Only direct sets are currently possible so 

    test_db-4.1.2.iso / test_db-4.1.2.iso.torrent --> work
    test_db-4.1.2.iso / test_db-4.1_2.iso.torrent --> does not work
    """

    # Regex, precompiled to increase speed
    prog_iso = re.compile("\w*\.iso$")

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
