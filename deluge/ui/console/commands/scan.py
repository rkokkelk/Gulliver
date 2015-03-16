# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import os
from optparse import make_option


import deluge.component as component
import deluge.scan.scanner as scanner
from deluge.ui.client import client
from deluge.ui.console.main import BaseCommand

class Command(BaseCommand):
    "Scan the scan directory"

    option_list = BaseCommand.option_list + (
        make_option('-d','--scan-dir',dest='scan_dir',help='Folder which will be scanned'),
    )
    usage = "Usage: scan -d <scan-folder>"

    def handle(self, *args, **options):
        self.console = component.get("ConsoleUI")

        t_options = {}
        if options["scan_dir"]:
            t_options["scan_dir"] = os.path.expanduser(options["scan_dir"])

        self.console.write("{!success!} Input is "+t_options["scan_dir"])

        def on_scan(result):
            self.console.write("{!success!} Scan has finished")

        def on_scan_fail(reason):
            self.console.write("{!error!}Scan has failed: %s" % reason)

        scan = scanner.Scanner(self.console)
        return scan.scan(t_options["scan_dir"]).addCallback(on_scan).addErrback(on_scan_fail)
