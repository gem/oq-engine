# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2014, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.


"""
Various utility functions concerned with configuration.
"""

import ConfigParser
import os
import pwd
import sys
from contextlib import contextmanager

import openquake.engine

OQDIR = os.path.dirname(os.path.dirname(openquake.engine.__path__[0]))
#: Environment variable name for specifying a custom openquake.cfg.
#: The file name doesn't matter.
OQ_CONFIG_FILE_VAR = "OQ_CONFIG_FILE"


# singleton
class _Config(object):
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
    LOCAL_PATH = os.path.join(OQDIR, "openquake.cfg")
    cfg = dict()

    def __init__(self):
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
        global_path = os.environ.get("OQ_SITE_CFG_PATH", self.GLOBAL_PATH)
        local_path = os.environ.get(
            "OQ_LOCAL_CFG_PATH", os.path.abspath(self.LOCAL_PATH))
        paths = [global_path, local_path]

        # User specified
        user_path = os.environ.get(OQ_CONFIG_FILE_VAR)
        if user_path is not None:
            paths.append(user_path)
        return paths

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

    def exists(self):
        """Return `True` if at least one config file exists."""
        return any(os.path.exists(path) for path in self._get_paths())


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
               % cfg._get_paths())
        print msg
        sys.exit(2)
    if not cfg.is_readable():
        msg = (
            "\nYou are not authorized to read any of the OpenQuake "
            "configuration files.\n"
            "Please contact a system administrator or run the following "
            "command:\n\n"
            "   sudo gpasswd --add %s openquake"
            % pwd.getpwuid(os.geteuid()).pw_name)
        print msg
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
