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

        client.register_event_handler("TorrentStateChangedEvent", self.on_torrent_state_changed_event)

    def start(self):
        def on_get_config(config):
            self.config = config
            self._clean_config()
            return config

        return client.core.get_torrent_config().addCallback(on_get_config)

    def stop(self):
        self.config = {}

    def on_torrent_state_changed_event(self, torrent_id, state):
        # We only want to seed, so if file has been removed on disk then remove
        # file from seeding to prevent downloading
        if "Downloading" == state:
            log.debug("State changed to downloading, removed: %s (%s)", str(torrent_id), str(state))
            client.core.remove_torrent(torrent_id, True)

    def _clean_config(self):

        for key in self.config.keys():
            value = self.config[key]
            if isinstance(value, unicode) and '\0' in value and len(value) == 1:
                """
                Not ideal setup but encode functions, replace functions
                and other functions does not remove null byte from value.

                Only peer_tos key contains a null byte
                """
                # TODO: create cleaner implementation
                self.config[key] = ""
            elif isinstance(value, unicode) and '\0' in value:
                log.warning("Found another null byte in (%s)", key)

    def set_high_performance_seed(self):
        deferred = defer.Deferred()
        client.core.set_torrent_high_speed_seed()

        def on_get_config(config):
            self.config = config
            self._clean_config()
            deferred.callback(True)

        client.core.get_torrent_config().addCallback(on_get_config)
        return deferred

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
