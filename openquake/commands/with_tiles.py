# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017 GEM Foundation
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
from __future__ import division
import os
from openquake.baselib import sap, general, parallel
from openquake.hazardlib import valid
from openquake.commonlib import readinput
from openquake.commands import engine


@sap.Script
def with_tiles(num_tiles, job_ini):
    """
    Run a calculation by splitting the sites into tiles.
    WARNING: this is experimental and meant only for GEM users
    """
    oq = readinput.get_oqparam(job_ini)
    num_sites = len(readinput.get_mesh(oq))
    task_args = [(job_ini, slc)
                 for slc in general.split_in_slices(num_sites, num_tiles)]
    if os.environ.get('OQ_DISTRIBUTE') == 'celery':
        Starmap = parallel.Processmap  # celery plays only with processes
    else:  # multiprocessing plays only with threads
        Starmap = parallel.Threadmap
    Starmap(engine.run_tile, task_args).reduce()

with_tiles.arg('num_tiles', 'number of tiles to generate',
               type=valid.positiveint)
with_tiles.arg('job_ini', 'calculation configuration file '
               '(or files, comma-separated)')
