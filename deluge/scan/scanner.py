""" Torrent.py

This scripts traverses the specific directory and gathers all torrent files 
and properly categorise them."""

import base64
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

from deluge.ui.client import client
from deluge.scan.scan_thread import Scan_Thread

log = logging.getLogger(__name__+"scanner")

class Scanner(object):
    """
    Scanner
    """

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

        if result_queue.empty():
            self.console.write("{!info!} No torrents found")
        else:
            while not result_queue.empty():
                result = result_queue.get()
                self.add_torrent_seed(result[0],result[1])
                result_queue.task_done()

        self.console.write("{!success!} Scan finished")

    def add_torrent_seed(self,torrent_location,seed_location):

        def fail_cb(msg,t_file):
            log.debug("failed to add torrent: %s: %s" % (t_file,msg))

        def success_cb(msg,t_file):
            log.debug("Added torrent: %s: %s" % (t_file,msg))

        self.console.write("{!info!} Torrent found "+torrent_location+" "+seed_location)

        t_options = {}
        filename = os.path.basename(torrent_location)
        filedump = base64.encodestring(open(torrent_location).read())
        seeddir, seedname = os.path.split(seed_location)
        d = client.core.add_torrent_seed(filename,filedump,seeddir,t_options)
        d.addCallback(success_cb,torrent_location)
        d.addErrback(fail_cb,torrent_location)

