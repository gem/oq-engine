# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.


"""
Various utility functions concerned with configuration.
"""

import ConfigParser
import os
import pwd
import sys

from openquake.utils import general


@general.singleton
class Config(object):
    """
    Load the configuration, make each section available in a separate
    dict.

    The configuration locations are specified via environment variables:
        - OQ_SITE_CFG_PATH
        - OQ_LOCAL_CFG_PATH

    In the absence of these environment variables the following hard-coded
    paths will be used in order:
        - /etc/openquake/openquake.cfg
        - ./openquake.cfg

    Please note: settings in the site configuration file are overridden
    by settings with the same key names in the local configuration.
    """
    GLOBAL_PATH = "/etc/openquake/openquake.cfg"
    LOCAL_PATH = "./openquake.cfg"
    cfg = dict()

    def __init__(self):
        self._load_from_file()

    def get(self, name):
        """A dict with key/value pairs for the given `section` or `None`."""
        return self.cfg.get(name)

    def _get_paths(self):
        """Return the paths for the global/local configuration files."""
        global_path = os.environ.get("OQ_SITE_CFG_PATH", self.GLOBAL_PATH)
        local_path = os.environ.get(
            "OQ_LOCAL_CFG_PATH", os.path.abspath(self.LOCAL_PATH))
        return [global_path, local_path]

    def _load_from_file(self):
        """Load the config files, set up the section dictionaries."""
        config = ConfigParser.SafeConfigParser()
        config.read(self._get_paths())
        for section in config.sections():
            self.cfg[section] = dict(config.items(section))

    def is_readable(self):
        """Return `True` if at least one config file is readable."""
        for path in self._get_paths():
            if os.access(path, os.R_OK):
                return True
        else:
            return False


def get_section(section):
    """A dictionary of key/value pairs for the given `section` or `None`."""
    return Config().get(section)


def get(section, key):
    """The configuration value for the given `section` and `key` or `None`."""
    data = get_section(section)
    return data.get(key) if data else None


def abort_if_no_config_available():
    """Call sys.exit() if no openquake configuration file is readable."""
    if not Config().is_readable():
        msg = (
            "\nYou are not authorized to read any of the OpenQuake "
            "configuration files.\n"
            "Please contact a system administrator or run the following "
            "command:\n\n"
            "   sudo gpasswd --add %s openquake"
            % pwd.getpwuid(os.geteuid()).pw_name)
        print msg
        sys.exit(2)
