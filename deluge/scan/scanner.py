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

from deluge.scan.scan_thread import Scan_Thread

log = logging.getLogger(__name__+"scanner")

class Scanner(object):
    """
    Scanner
    """

    log = logging.getLogger(__name__+"scanner")

    # Regex, precompiled to increase speed
    prog_iso = re.compile("\w*\.iso$")

    # Constructor
    def __init__(self, console):
        self.console = console

    # Scan method
    def scan(self,scan_dir):

        scan_queue = Queue.Queue()
        result_queue = Queue.Queue()

        self.console.write("{!info!} Starting scan")

        dir_list = [ dir_name for dir_name in os.listdir(scan_dir) if os.path.isdir(os.path.join(scan_dir,dir_name)) ]
        log.debug("Scan directory size: %d",len(dir_list))

        # Load all the subdirectories of scan_dir in scan_queue
        for dir_name in dir_list:
            scan_queue.put(os.path.join(scan_dir,dir_name))

        for i in range(5):
            thread = Scan_Thread(scan_queue,result_queue)
            thread.start()

        scan_queue.join()
        self.console.write("{!info!} Scan finished")
