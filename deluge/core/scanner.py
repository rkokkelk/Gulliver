""" Torrent.py

This scripts traverses the specific directory and gathers all torrent files 
and properly categorise them."""

import base64
import logging
import threading
import thread

from twisted.internet import reactor, defer

import Queue
import glob
import re
import os

import deluge.component as component
from deluge.scan.scan_thread import Scan_Thread

log = logging.getLogger(__name__+"scanner")


class Scanner(component.Component):

    def __init__(self):
        component.Component.__init__(self, "Scanner", interval=1)

        # Verify if threads should run
        self.running = True
        self.timer = None

        self.start_timer()

    # Scan method
    def scan(self, scan_dir=None, timer=True):

        results = []
        lock = threading.Lock()
        core = component.get("Core")
        config = core.config.config

        if lock.acquire(False):

            # If no scan dir is set, use default
            if not scan_dir:
                scan_dir = config["scan_directory"]

            scan_queue = Queue.Queue()
            result_queue = Queue.Queue()

            dir_list = [dir_name for dir_name in os.listdir(scan_dir)
                        if os.path.isdir(os.path.join(scan_dir, dir_name))]
            log.debug("Scan directory size: %d", len(dir_list))

            # Load all the subdirectories of scan_dir in scan_queue
            for dir_name in dir_list:
                scan_queue.put(os.path.join(scan_dir, dir_name))

            for i in range(5):
                thread = Scan_Thread(scan_queue, result_queue)
                thread.start()

            scan_queue.join()

            while not result_queue.empty():
                result = result_queue.get()
                self.add_torrent_seed(result[0], result[1])
                results.append({result[0], result[1]})
                result_queue.task_done()

            if timer and self.running:

                sequence = config["scan_frequency"]
                self.timer = threading.Timer(sequence, self.scan)
                self.timer.start()

            lock.release()

        else:
            raise Exception("Already scan running")

        return results

    def add_torrent_seed(self, torrent_location, seed_location):

        core = component.get("Core")

        t_options = {}
        filename = os.path.basename(torrent_location)
        filedump = base64.encodestring(open(torrent_location).read())
        seeddir, seedname = os.path.split(seed_location)
        core.add_torrent_seed(filename, filedump, seeddir, t_options)

    def start_timer(self):

        core = component.get("Core")
        config = core.config.config

        timer = config["scan_frequency"]
        self.timer = threading.Timer(timer, self.scan)
        self.timer.start()

    def stop(self):

        log.debug("Scanner shutting down")
        self.running = False
        self.timer.cancel()


class Scan_Thread(threading.Thread):

    prog_iso = re.compile("\w*\.iso$")

    # Constructor
    def __init__(self, scanQueue, resultQueue):
        threading.Thread.__init__(self)
        self.scanQueue = scanQueue
        self.resultQueue = resultQueue
        self.ID = thread.get_ident()

    # Scan method
    def scan(self, scanDir):

        index = -1
        isoList = list()
        torList = list()

        # Walk through all subdirectories of the top directory
        for root, dirs, files in os.walk(scanDir):

            tmp_torrent_list = glob.glob(os.path.join(root, "*.torrent"))
            tmp_torrent_list.extend(glob.glob(os.path.join(root, "*.torrents")))
            tmp_iso_list = glob.glob(os.path.join(root, "*.iso"))

            torList.extend(tmp_torrent_list)
            isoList.extend(tmp_iso_list)

        log.debug("Result %s: (%d) torrents, (%d) iso", scanDir, len(torList), len(isoList))

        # Matching .torrent files with the corret .iso
        for tor_file in torList:
            tor_base_name = os.path.basename(tor_file)
            rmTor = re.sub(".torrent(s)?$", '', tor_base_name)

            # Some torrents are stored as following abc.1.2.torrent --> abc.1.2.iso
            # so in order to fix this, .iso is appended if there is no file extension
            if self.prog_iso.search(rmTor) is None:
                rmTor = rmTor + ".iso"

            for iso_file in isoList:
                iso_base_name = os.path.basename(iso_file)
                if iso_base_name == rmTor:
                    result = (tor_file, iso_file)
                    self.resultQueue.put(result)

    # Thread run method
    def run(self):

        # Loop through directories until queue is empty
        while not self.scanQueue.empty():
            scanDir = self.scanQueue.get()
            self.scan(scanDir)
            self.scanQueue.task_done()