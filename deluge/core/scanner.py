# -*- coding: utf-8 -*-
#
#  Roy Kokkelkoren  <roy.kokkelkoren@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import base64
import logging
import threading
import thread
import Queue
import re
import os

from deluge._libtorrent import lt
import deluge.component as component

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

        results = {}
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

            # Divide search for torrent by threads
            for i in range(scan_queue.qsize()):
                scan_thread = Scan_Thread(scan_queue, result_queue)
                scan_thread.start()

            # Wait for all torrent_scan to finish
            scan_queue.join()

            # Add results in new dict for easy searching
            while not result_queue.empty():
                torrent_result = result_queue.get()
                results[torrent_result["name"]] = torrent_result
                result_queue.task_done()

            self.scan_for_files(results, scan_dir, core)

            if timer and self.running:

                sequence = config["scan_frequency"]
                self.timer = threading.Timer(sequence, self.scan)
                self.timer.start()

            lock.release()

        else:
            raise Exception("Already scan running")

        return results

    def scan_for_files(self, torrent_list, scan_dir, core):

        # Walk through all subdirectories of the top directory
        for root, dirs, files in os.walk(scan_dir):

            for dir_walk in dirs:
                if dir_walk in torrent_list:
                    print("Found dir, do nothing, yet!")
                    pass

            for file_walk in files:
                if file_walk in torrent_list:

                    file_root = os.path.join(root, file_walk)
                    file_size = os.path.getsize(file_root)
                    with open(torrent_list[file_walk]["path"], "r") as f:
                        metadata = lt.bdecode(f.read())

                    # Verify if correct file by comparing file size
                    if file_size == metadata["info"]["length"]:
                        self.add_torrent_seed(torrent_list[file_walk]["path"], file_root, core)

    def add_torrent_seed(self, torrent_location, seed_location, core):

        t_options = {}
        filename = os.path.basename(torrent_location)
        file_dump = base64.encodestring(open(torrent_location).read())
        seed_dir, seed_name = os.path.split(seed_location)
        core.add_torrent_seed(filename, file_dump, seed_dir, t_options)

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

    re_torrents = re.compile(".*\.torrent(s)?$")

    # Constructor
    def __init__(self, scan_queue, result_queue):
        threading.Thread.__init__(self)
        self.scan_queue = scan_queue
        self.result_queue = result_queue
        self.ID = thread.get_ident()

    # Scan method
    def scan_for_torrent(self, scan_dir):

        # Walk through all subdirectories of the top directory
        for root, dirs, files in os.walk(scan_dir):

            for walk_file in files:

                # Verify if is torrent file by checking extension
                if self.re_torrents.match(walk_file):

                    is_dir = False
                    file_root = os.path.join(root, walk_file)
                    with open(file_root, "r") as f:
                        metadata = lt.bdecode(f.read())

                    if metadata is None:
                        log.warning("Corrupt torrent file found: %s"+walk_file)
                        continue

                    name = metadata["info"]["name"]
                    if "files" in metadata["info"]:
                        is_dir = True

                    file_dict = {"name": name, "is_dir": is_dir, "path": file_root}
                    self.result_queue.put(file_dict)

    # Thread run method
    def run(self):

        # Loop through directories until queue is empty
        while not self.scan_queue.empty():
            scan_dir = self.scan_queue.get()
            self.scan_for_torrent(scan_dir)
            self.scan_queue.task_done()