# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2017 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Various utility functions concerned with configuration.
"""

import os
import sys

from openquake.baselib.python3compat import configparser, encode
from openquake.hazardlib import valid

OQ_PATH = os.path.dirname(os.path.dirname(__file__))
#: Environment variable name for specifying a custom openquake.cfg.
#: The file name doesn't matter.
OQ_CONFIG_FILE_VAR = "OQ_CONFIG_FILE"


# singleton
class _Config(object):
    """
    Load the configuration, make each section available in a separate
    dict.

    The configuration location can specified via an environment variables:
        - OQ_CONFIG_FILE

    In the absence of this environment variable the following paths will be
    used in order:
        - /etc/openquake/openquake.cfg (only when running outside a venv)
        - openquake/engine/openquake.cfg (from the python package)

    Please note: settings in the site configuration file are overridden
    by settings with the same key names in the OQ_CONFIG_FILE openquake.cfg.
    """
    CFG_FILE = "openquake.cfg"
    ETC_PATH = os.path.join("/etc/openquake", CFG_FILE)
    PKG_PATH = os.path.join(OQ_PATH, "engine", CFG_FILE)
    cfg = dict()

    def __init__(self):
        """
        Determine the paths to search and load the config file.
        """
        paths = []

        # path from python package
        paths.append(os.path.join(OQ_PATH, "engine", self.CFG_FILE))

        # path from system etc dir, only if a venv is not active
        venv = 'VIRTUAL_ENV' in os.environ or hasattr(sys, 'real_prefix')
        if not venv and os.path.exists(self.ETC_PATH):
            paths.append(self.ETC_PATH)

        # path from env variable
        if OQ_CONFIG_FILE_VAR in os.environ:
            paths.append(os.path.normpath(os.environ[OQ_CONFIG_FILE_VAR]))

        # normalize all paths and resolve '~' in a single pass
        self._paths = [os.path.normpath(os.path.expanduser(p)) for p in paths]
        self._load_from_file()

    def get(self, name):
        """A dict with key/value pairs for the given `section` or `None`."""
        return self.cfg.get(name)

    def set(self, name, dic):
        """Set the dictionary for given section"""
        self.cfg[name] = dic

    def _load_from_file(self):
        """Load the config files, set up the section dictionaries."""
        config = configparser.SafeConfigParser()
        config.read(self._paths)
        for section in config.sections():
            self.cfg[section] = dict(config.items(section))

    def is_readable(self):
        """Return `True` if at least one config file is readable."""
        for path in self._paths:
            if os.access(path, os.R_OK):
                return True
        else:
            return False

    def exists(self):
        """Return `True` if at least one config file exists."""
        return any(os.path.exists(path) for path in self._paths)


cfg = _Config()  # the only instance of _Config


def get_section(section):
    """A dictionary of key/value pairs for the given `section` or `None`."""
    abort_if_no_config_available()
    return cfg.get(section)


def get(section, key):
    """The configuration value for the given `section` and `key` or `None`."""
    data = get_section(section)
    return data.get(key) if data else None


def abort_if_no_config_available():
    """Call sys.exit() if no openquake configuration file is readable."""
    if not cfg.exists():
        msg = ('Could not find a configuration file in %s. '
               'Probably your are not in the right directory'
               % cfg._paths)
        sys.exit(msg)
    if not cfg.is_readable():
        msg = (
            "\nYou are not authorized to read any of the OpenQuake "
            "configuration files.\n"
            "Please check permissions on the configuration files in %s."
            % cfg._paths)
        sys.exit(msg)


def flag_set(section, setting):
    """True if the given boolean setting is enabled in openquake.cfg

    :param string section: name of the configuration file section
    :param string setting: name of the configuration file setting

    :returns: True if the setting is enabled in openquake.cfg, False otherwise
    """
    return valid.boolean(get(section, setting) or '')


port = int(get('dbserver', 'port'))
DBS_ADDRESS = (get('dbserver', 'host'), port)
DBS_AUTHKEY = encode(get('dbserver', 'authkey'))
SHARED_DIR_ON = bool(get('directory', 'shared_dir'))
