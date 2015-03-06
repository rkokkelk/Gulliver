# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import deluge.component as component
import deluge.scan.scanner as scanner
from deluge.ui.client import client
from deluge.ui.console.main import BaseCommand


class Command(BaseCommand):
    "Scan the scan directory"
    usage = "Usage: scan"

    def handle(self, *args, **options):
        self.console = component.get("ConsoleUI")

        def on_shutdown(result):
            self.console.write("{!success!} Scan has finished")

        def on_shutdown_fail(reason):
            self.console.write("{!error!}Scan has failed: %s" % reason)

        tmp_scanner = scanner()
        return tmp_scanner.test()
