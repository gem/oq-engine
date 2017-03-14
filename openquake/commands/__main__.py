#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2017 GEM Foundation
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
import importlib

from openquake.baselib import sap
from openquake.commonlib import __version__
from openquake import commands
from openquake.commonlib import config

USE_CELERY = config.get('distribution', 'oq_distribute') == 'celery'

# the environment variable has the precedence over the configuration file
if 'OQ_DISTRIBUTE' not in os.environ and USE_CELERY:
    os.environ['OQ_DISTRIBUTE'] = 'celery'

# force cluster users to use `oq engine` so that we have centralized logs
if USE_CELERY and 'run' in sys.argv:
    sys.exit('You are on a cluster and you are using oq run?? '
             'Use oq engine --run instead!')


def oq():
    modnames = ['openquake.commands.%s' % mod[:-3]
                for mod in os.listdir(commands.__path__[0])
                if mod.endswith('.py') and not mod.startswith('_')]
    for modname in modnames:
        importlib.import_module(modname)
    parser = sap.compose(sap.Script.registry.values(),
                         prog='oq', version=__version__)
    parser.callfunc()

if __name__ == '__main__':
    oq()
