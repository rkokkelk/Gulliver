#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import glob
import os
import platform
import sys
from distutils import cmd
from distutils.command.build import build as _build
from distutils.command.clean import clean as _clean

from setuptools import find_packages, setup
from setuptools.command.test import test as _test

from version import get_version

try:
    from sphinx.setup_command import BuildDoc
except ImportError:
    class BuildDoc(object):
        pass

class Build(_build):
    sub_commands = [('build_trans', None), ('build_plugins', None)] + _build.sub_commands

    def run(self):
        # Run all sub-commands (at least those that need to be run)
        _build.run(self)
        try:
            from deluge._libtorrent import lt
            print "Found libtorrent version: %s" % lt.version
        except ImportError, e:
            print "Warning libtorrent not found: %s" % e

class Clean(_clean):
    sub_commands = _clean.sub_commands + [('clean_plugins', None)]

    def run(self):
        # Run all sub-commands (at least those that need to be run)
        for cmd_name in self.get_sub_commands():
            self.run_command(cmd_name)
        _clean.run(self)

cmdclass = {
    'build': Build,
    'build_docs': BuildDoc,
    'clean': Clean,
}

# Data files to be installed to the system
_data_files = [
    ('share/man/man1', [
        'docs/man/deluge.1',
        'docs/man/deluged.1',
        'docs/man/deluge-console.1'])
]

entry_points = {
    "console_scripts": [
        "deluge-console = deluge.ui.console:start"
    ],
    "gui_scripts": [
        #"deluge = deluge.main:start_ui",
        #"deluge-gtk = deluge.ui.gtkui:start",
        #"deluge-web = deluge.ui.web:start",
        "deluged = deluge.main:start_daemon"
    ]
}

# Main setup
setup(
    name="deluge",
    version=get_version(prefix='deluge-', suffix='.dev0'),
    fullname="Deluge Bittorrent Client",
    description="Bittorrent Client",
    author="Andrew Resch, Damien Churchill",
    author_email="andrewresch@gmail.com, damoxc@gmail.com",
    keywords="torrent bittorrent p2p fileshare filesharing",
    long_description="""Deluge is a bittorrent client that utilizes a
        daemon/client model. There are various user interfaces available for
        Deluge such as the GTKui, the webui and a console ui. Deluge uses
        libtorrent in it's backend to handle the bittorrent protocol.""",
    url="http://deluge-torrent.org",
    license="GPLv3",
    cmdclass=cmdclass,
    tests_require=['pytest'],
    data_files=_data_files,
    packages=find_packages(exclude=["plugins", "docs", "tests"]),
    namespace_packages=["deluge"],
    entry_points=entry_points
)
