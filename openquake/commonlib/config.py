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

from openquake.baselib.python3compat import configparser, encode
import os
import sys
from shutil import copy
from contextlib import contextmanager

OQDIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
#: Environment variable name for specifying a custom openquake.cfg.
#: The file name doesn't matter.
OQ_CONFIG_FILE_VAR = "OQ_CONFIG_FILE"


# singleton
class _Config(object):
    """
    Load the configuration, make each section available in a separate
    dict.

    The configuration location can be specified via the 'OQ_CONFIG_FILE'
    environment variable.

    In the absence of this environment variable the configuration is located
    in the following way:

        - in the 'oq-engine' GIT source code repo (when using it)
        - inside a platform specific, standard, location
            - XDG_CONFIG_HOME or ~/.config for Linux
            - ~/Library/Preferences for macOS
            - %APPDATA% for Windows
        - in /etc, with higher prority, if code is running outside
          a virtualenvironment

    Please note: settings in the site configuration file are overridden
    by settings with the same key names in the local configuration.
    """
    SYS_PREFIX = "/etc"
    CFG_PREFIX = "openquake"
    CFG_FILE = "openquake.cfg"
    CFG_TEMPLATE = (os.path.join(os.path.dirname(__file__),
                    'cfg_samples', CFG_FILE))
    cfg = dict()

    def __init__(self):
        self._file_init()
        self._load_from_file()
        self.job_id = -1

    def get(self, name):
        """A dict with key/value pairs for the given `section` or `None`."""
        return self.cfg.get(name)

    def set(self, name, dic):
        """Set the dictionary for given section"""
        self.cfg[name] = dic

    def _get_paths(self):
        """Return the paths for the global/local configuration files."""
        if sys.platform == 'win32':
            local_prefix = os.environ['APPDATA']
        elif sys.platform == 'darwin':
            local_prefix = '~/Library/Preferences'
        else:
            local_prefix = os.environ.get('XDG_CONFIG_HOME', '~/.config')

        local_path = os.path.join(local_prefix, self.CFG_PREFIX,
                                  self.CFG_FILE)

        paths = [local_path]

        # when not running in a virtualenv system config
        # has the highest priority
        if not hasattr(sys, 'real_prefix'):
            paths.append(os.path.join(self.SYS_PREFIX, self.CFG_PREFIX,
                                      self.CFG_FILE))

        # keep the old behaviour when git sources are used
        if os.path.exists(os.path.join(OQDIR, self.CFG_FILE)):
            paths.append(os.path.join(OQDIR, self.CFG_FILE))

        env_path = os.environ.get(OQ_CONFIG_FILE_VAR)
        if env_path is not None:
            paths.append(os.path.normpath(os.environ[OQ_CONFIG_FILE_VAR]))

        # normalize all paths and resolve '~' in a single pass
        paths = [os.path.normpath(os.path.expanduser(p)) for p in paths]

        return paths

    def _file_init(self):
        """Initialize a new config file if it does not exist yet."""
        paths = self._get_paths()
        if not os.path.exists(paths[-1]):
            try:
                if not os.path.exists(os.path.dirname(paths[-1])):
                    os.makedirs(os.path.dirname(paths[-1]))
                copy(self.CFG_TEMPLATE, paths[-1])
            finally:
                print('Could not find a configuration file in %s and '
                      'could not create if from template.\n'
                      % paths)

    def _load_from_file(self):
        """Load the config files, set up the section dictionaries."""
        config = configparser.SafeConfigParser()
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


cfg = _Config()  # the only instance of _Config


@contextmanager
def context(section, **kw):
    """
    Context manager used to change the parameters of a configuration
    section on the fly. For use in the tests.
    """
    section_dict = cfg.get(section)
    orig = section_dict.copy()
    try:
        section_dict.update(kw)
        yield
    finally:
        cfg.set(section, orig)


def get_section(section):
    """A dictionary of key/value pairs for the given `section` or `None`."""
    abort_if_no_config_readable()
    return cfg.get(section)


def get(section, key):
    """The configuration value for the given `section` and `key` or `None`."""
    data = get_section(section)
    return data.get(key) if data else None


def abort_if_no_config_readable():
    """Call sys.exit() if no openquake configuration file is readable."""
    if not cfg.is_readable():
        msg = (
            "\nYou are not authorized to read any of the OpenQuake "
            "configuration files.\n"
            "Please check permissions on the configuration files in %s."
            % cfg._get_paths())
        print(msg)
        sys.exit(2)


def flag_set(section, setting):
    """True if the given boolean setting is enabled in openquake.cfg

    :param string section: name of the configuration file section
    :param string setting: name of the configuration file setting

    :returns: True if the setting is enabled in openquake.cfg, False otherwise
    """
    setting = get(section, setting)
    if setting is None:
        return False
    return setting.lower() in ("true", "yes", "t", "1")


def refresh():
    """
    Re-parse config files and refresh the cached configuration.

    NOTE: Use with caution. Calling this during some phases of a calculation
    could cause undesirable side-effects.
    """
    cfg._load_from_file()


port = int(get('dbserver', 'port'))
DBS_ADDRESS = (get('dbserver', 'host'), port)
DBS_AUTHKEY = encode(get('dbserver', 'authkey'))
