# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import logging

from twisted.internet import defer

import deluge.component as component
from deluge.ui.client import client

log = logging.getLogger(__name__)


class TorrentConfig(component.Component):
    def __init__(self):
        log.debug("TorrentConfig init..")
        component.Component.__init__(self, "TorrentConfig")
        self.config = {}

        #def on_configvaluechanged_event(key, value):
        #    self.config[key] = value
        #client.register_event_handler("ConfigValueChangedEvent", on_configvaluechanged_event)

    def start(self):
        def on_get_config(config):
            self.config = config
            self._clean_config()
            return config

        return client.core.get_torrent_config().addCallback(on_get_config)

    def stop(self):
        self.config = {}

    def _clean_config(self):

        for key in self.config.keys():
            value = self.config[key]
            if isinstance(value, unicode):
                if '\0' in value:
                    value = value.encode('utf-8', 'ignore')
                    self.config[key] = value


    def __getitem__(self, key):
        return self.config[key]

    def __setitem__(self, key, value):
        client.core.set_torrent_config({key: value})

    def set_item(self, key, value):
        deferred = defer.Deferred()
        client.core.set_torrent_config({key: value})

        def on_get_config(config):
            self.config = config
            self._clean_config()
            deferred.callback(True)

        client.core.get_torrent_config().addCallback(on_get_config)

        return deferred

    def __getattr__(self, attr):
        # We treat this directly interacting with the dictionary
        return getattr(self.config, attr)
