# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2025 GEM Foundation
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

# the version is managed by the universal installer
__version__ = '3.23.1'
