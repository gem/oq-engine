# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2021 GEM Foundation
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
import numpy
import scipy
import pandas
import configparser

# disable OpenBLAS threads before the first numpy import
# see https://github.com/numpy/numpy/issues/11826
os.environ['OPENBLAS_NUM_THREADS'] = '1'
from openquake.baselib.general import git_suffix  # noqa: E402

# the version is managed by packager.sh with a sed
__version__ = '3.11.2'
__version__ += git_suffix(__file__)

version = dict(engine=__version__,
               python='%d.%d' % sys.version_info[:2],
               numpy=numpy.__version__,
               scipy=scipy.__version__,
               pandas=pandas.__version__)


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


config = DotDict()  # global configuration
d = os.path.dirname
base = os.path.join(d(d(__file__)), 'engine', 'openquake.cfg')
# 'virtualenv' still uses 'real_prefix' also on Python 3
# removal of this breaks Travis
if (hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix')
                                    and sys.base_prefix != sys.prefix)):
    config.paths = [base, os.path.join(sys.prefix, 'openquake.cfg')]
else:  # installation from sources or packages, search in $HOME or /etc
    config.paths = [base, '/etc/openquake/openquake.cfg', '~/openquake.cfg']
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
    parser = configparser.ConfigParser()
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


config.read = read


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


config.read(limit=int, soft_mem_limit=int, hard_mem_limit=int, port=int,
            multi_user=positiveint, serialize_jobs=positiveint,
            strict=positiveint, code=exec)

if config.directory.custom_tmp:
    os.environ['TMPDIR'] = config.directory.custom_tmp

if 'OQ_DISTRIBUTE' not in os.environ:
    os.environ['OQ_DISTRIBUTE'] = config.distribution.oq_distribute
