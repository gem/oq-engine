# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2019 GEM Foundation
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
from openquake.baselib.general import git_suffix

# the version is managed by packager.sh with a sed
__version__ = '3.5.0'
__version__ += git_suffix(__file__)


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
    found = parser.read(os.path.normpath(os.path.expanduser(p)) for p in paths)
    if not found:
        raise IOError('No configuration file found in %s' % str(paths))
    config.found = found
    config.clear()
    for section in parser.sections():
        config[section] = sec = DotDict(parser.items(section))
        for k, v in sec.items():
            sec[k] = validators.get(k, lambda x: x)(v)


config.read = read


def boolean(flag):
    """
    Convert string in boolean
    """
    s = flag.lower()
    if s in ('1', 'yes', 'true'):
        return True
    elif s in ('0', 'no', 'false'):
        return False
    raise ValueError('Unknown flag %r' % s)


config.read(soft_mem_limit=int, hard_mem_limit=int, port=int,
            multi_user=boolean, multi_node=boolean, serialize_jobs=boolean)

if config.directory.custom_tmp:
    os.environ['TMPDIR'] = config.directory.custom_tmp

if 'OQ_DISTRIBUTE' not in os.environ:
    os.environ['OQ_DISTRIBUTE'] = config.distribution.oq_distribute

multi_node = config.distribution.get('multi_node', False)

if config.distribution.oq_distribute == 'celery' and not multi_node:
    sys.stderr.write(
        'oq_distribute is celery but you are not in a cluster? '
        'probably you forgot to set `multi_node=true` in openquake.cfg\n')
