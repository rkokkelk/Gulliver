# -*- coding: utf-8 -*-
#
#  Roy Kokkelkoren  <roy.kokkelkoren@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import os
from optparse import make_option

import deluge.component as component
from deluge.ui.client import client
from deluge.ui.console.main import BaseCommand


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('-d', '--scan-dir', dest='scan_dir', help='Folder which will be scanned'),
    )
    usage = "Usage: scan -d <scan-folder>"

    def handle(self, *args, **options):
        console = component.get("ConsoleUI")

        t_options = {}
        if options["scan_dir"]:
            t_options["scan_dir"] = os.path.expanduser(options["scan_dir"])
            console.write("{!info!} Scanning directory: "+t_options["scan_dir"])
        else:
            t_options["scan_dir"] = None
            console.write("{!info!} No scan directory set, using default.")

        def on_scan_success(result):

            if any(result):
                for torrent_name in result.iterkeys():
                    console.write("{!success!} Torrent found "+torrent_name)
            else:
                console.write("{!success!} No torrents found")

        def on_scan_fail(reason):
            console.write("{!error!}Scan has failed: %s" % reason)

        d = client.core.start_scan(t_options["scan_dir"])
        d.addCallback(on_scan_success)
        d.addErrback(on_scan_fail)

        return d
