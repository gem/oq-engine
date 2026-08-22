# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2026 GEM Foundation
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

import os
import sys
import configparser
import logging
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import FrozenSet


# use utf8 as default encodings on all platforms (i.e. Windows)
# TODO: to remove in Python 3.15 when this will become the default
os.environ['PYTHONUTF8'] = '1'

# disable OpenBLAS threads before the first numpy import
# see https://github.com/numpy/numpy/issues/11826
os.environ['OPENBLAS_NUM_THREADS'] = '1'


class InvalidFile(Exception):
    """Raised from custom file validators"""


class DotDict(dict):
    """
    A string-valued dictionary that can be accessed with the "." notation
    """
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)


def positiveint(flag):
    """
    Convert string into integer
    """
    s = flag.lower()
    if s in ('1', 'yes', 'true'):
        return 1
    elif s in ('0', 'no', 'false'):
        return 0
    i = int(s)
    if i < 0:
        raise ValueError('Invalid %r' % s)
    return i


config = DotDict()  # global configuration
d = os.path.dirname
base = os.path.join(d(d(__file__)), 'engine', 'openquake.cfg')
home = os.path.expanduser('~/openquake.cfg')
if sys.prefix != sys.base_prefix:
    # installation in the venv identified by sys.prefix
    config.paths = [base, os.path.join(sys.prefix, 'openquake.cfg'), home]
else:  # other kind of installation
    config.paths = [base, '/etc/openquake/openquake.cfg', home]
cfgfile = os.environ.get('OQ_CONFIG_FILE')
if cfgfile:
    config.paths.append(cfgfile)
# NB: the last file wins, since the parameters are overridden in order


def read(*paths, **validators):
    """
    Load the configuration, make each section available in a separate dict.

    The configuration location can specified via an environment variable:
       - OQ_CONFIG_FILE

    In the absence of this environment variable the following paths will be
    used:
       - sys.prefix + /openquake.cfg when in a virtualenv
       - /etc/openquake/openquake.cfg outside of a virtualenv

    If those files are missing, the fallback is the source code:
       - openquake/engine/openquake.cfg

    Please note: settings in the site configuration file are overridden
    by settings with the same key names in the OQ_CONFIG_FILE openquake.cfg.
    """
    paths = config.paths + list(paths)
    parser = configparser.ConfigParser(interpolation=None)
    found = parser.read(
        [os.path.normpath(os.path.expanduser(p)) for p in paths],
        encoding='utf8')
    if not found:
        raise IOError('No configuration file found in %s' % str(paths))
    config.found = found
    config.clear()
    for section in parser.sections():
        config[section] = sec = DotDict(parser.items(section))
        for k, v in sec.items():
            try:
                sec[k] = validators.get(k, lambda x: x)(v)
            except ValueError as err:
                raise ValueError('%s for %s in %s' % (err, k, found[-1]))


# NB: duplicated in commands/engine.py!!
config.read = read
config.read(limit=int, soft_mem_limit=int, hard_mem_limit=int, port=int,
            serialize_jobs=positiveint, strict=positiveint, code=exec)

if config.directory.custom_tmp:
    os.environ['TMPDIR'] = config.directory.custom_tmp
    # NUMBA_CACHE_DIR is useless since numba is saving on .cache/numba anyway
    # os.environ['NUMBA_CACHE_DIR'] = config.directory.custom_tmp

if 'OQ_DISTRIBUTE' not in os.environ:
    os.environ['OQ_DISTRIBUTE'] = config.distribution.oq_distribute

# wether the engine was installed as multi_user (linux root) or not
if sys.platform in 'win32 darwin':
    config.multi_user = False
else:  # linux
    import pwd
    try:
        install_user = pwd.getpwuid(os.stat(__file__).st_uid).pw_name
    except KeyError:  # on the IUSS cluster
        install_user = None
    config.multi_user = install_user in ('root', 'openquake')


# FIXME: we could have a standard mode with a set of capabilities and
# subclasses for specialized modes that differ just for a few capabilities

class Mode(str, Enum):
    # TODO: we probably need better names. For instance:
    #   - PUBLIC     -> SINGLE_USER,
    #   - RESTRICTED -> MULTI_USER

    PUBLIC = 'PUBLIC'
    RESTRICTED = 'RESTRICTED'
    AELO = 'AELO'
    IMPACT = 'IMPACT'
    READ_ONLY = 'READ_ONLY'
    TOOLS_ONLY = 'TOOLS_ONLY'

    @property
    def description(self) -> str:
        return {
            Mode.PUBLIC: "Single user application without authentication",
            Mode.RESTRICTED: "Multi-user application with authentication",
            Mode.AELO: "AELO assessment mode",
            Mode.IMPACT: "Impact assessment mode",
            Mode.READ_ONLY: "Inhibits the possibility to run calculations",
            Mode.TOOLS_ONLY: "Provides standalone tools only",
        }[self]

    def __repr__(self) -> str:
        return f"{self.name}: {self.description}"

    def __str__(self) -> str:
        return self.__repr__()


class Capability(Enum):
    # auto assigns incremental integers
    AUTHENTICATION = auto()

    # Job-related capabilities
    JOB_ABORTING = auto()
    JOB_REMOVING = auto()
    JOB_SHARING = auto()
    JOB_TAGGING = auto()
    JOB_CONTINUING = auto()
    STANDARD_JOB_LAUNCHING = auto()
    AELO_JOB_LAUNCHING = auto()
    IMPACT_JOB_LAUNCHING = auto()

    STANDALONE_TOOLS = auto()
    MOSAIC_DIR_REQUIRED = auto()
    VISIBLE_SERVER_NAME = auto()
    PLOT_ASSETS_POST_RISK = auto()
    GLOSSARY = auto()  # FIXME: check logic

    def __repr__(self) -> str:
        return self.name


# Mapping modes to active capabilities
MODE_CAPABILITIES: dict[Mode, FrozenSet[Capability]] = {
    Mode.PUBLIC: frozenset(
        {
         Capability.STANDARD_JOB_LAUNCHING,
         Capability.JOB_CONTINUING,
         Capability.JOB_ABORTING,
         Capability.JOB_REMOVING,
         Capability.VISIBLE_SERVER_NAME,
         Capability.GLOSSARY,
         }
    ),
    Mode.RESTRICTED: frozenset(
        {
         Capability.AUTHENTICATION,
         Capability.STANDARD_JOB_LAUNCHING,
         Capability.JOB_CONTINUING,
         Capability.JOB_ABORTING,
         Capability.JOB_REMOVING,
         Capability.JOB_SHARING,
         Capability.JOB_TAGGING,
         Capability.VISIBLE_SERVER_NAME,
         Capability.GLOSSARY,
         }
    ),
    Mode.IMPACT: frozenset(
        {
         Capability.AUTHENTICATION,
         Capability.IMPACT_JOB_LAUNCHING,
         Capability.JOB_ABORTING,
         Capability.JOB_REMOVING,
         Capability.JOB_SHARING,
         Capability.JOB_TAGGING,
         Capability.MOSAIC_DIR_REQUIRED,
         Capability.VISIBLE_SERVER_NAME,
         Capability.PLOT_ASSETS_POST_RISK,
         Capability.GLOSSARY,
         }
    ),
    Mode.AELO: frozenset(
        {
         Capability.AUTHENTICATION,
         Capability.AELO_JOB_LAUNCHING,
         Capability.JOB_ABORTING,
         Capability.JOB_REMOVING,
         Capability.MOSAIC_DIR_REQUIRED,
         Capability.GLOSSARY,
         }
    ),
    Mode.READ_ONLY: frozenset(
        {
         Capability.AUTHENTICATION,
         Capability.VISIBLE_SERVER_NAME,
         }
    ),
    Mode.TOOLS_ONLY: frozenset(
        {
         Capability.AUTHENTICATION,
         Capability.STANDALONE_TOOLS,
         Capability.VISIBLE_SERVER_NAME,
         Capability.GLOSSARY,
         }
    ),
}


def generate_capability_checkers(cls):
    for cap in Capability:
        method_name = f"has_{cap.name.lower()}_enabled"

        # Helper function creates a proper closure over 'cap'
        def make_method(capability):
            return lambda self: self.has(capability)

        setattr(cls, method_name, make_method(cap))
    return cls


@generate_capability_checkers
@dataclass(frozen=True)
class Application:
    mode: Mode
    capabilities: FrozenSet[Capability] = field(init=False)

    def __init__(self, mode: str):
        target_mode: Mode

        # Normalize input string (case-insensitive)
        raw_str = str(mode).upper()
        try:
            target_mode = Mode[raw_str]
        except KeyError:
            available_modes = [m.name for m in Mode]
            logging.warning(
                "Application mode '%s' is not recognized. "
                "Falling back to default 'PUBLIC' mode. "
                "Available modes are: %s",
                mode,
                ", ".join(available_modes),
            )
            target_mode = Mode.PUBLIC

        # Set immutable fields on frozen dataclass
        object.__setattr__(self, "mode", target_mode)
        object.__setattr__(
            self, "capabilities", MODE_CAPABILITIES.get(
                target_mode, frozenset())
        )

    def has(self, cap: Capability) -> bool:
        return cap in self.capabilities

    def __repr__(self) -> str:
        caps_formatted = ("{" + ", ".join(cap.name for cap in
                                          self.capabilities) + "}")
        return f"Application(mode={self.mode}, capabilities={caps_formatted})"

    # def get_additioanl_attrs(self):
    #     return {}


# class AeloApplication(Application):


def get_application() -> Application:
    """
    Reads the raw mode from config/env and returns an Application instance.
    """
    raw_mode = os.environ.get("OQ_APPLICATION_MODE",
                              config.webapi.application_mode)
    return Application(mode=raw_mode)


# Singleton initialized on import
APPLICATION = get_application()


# the version is managed by the universal installer
__version__ = '3.27.0'
