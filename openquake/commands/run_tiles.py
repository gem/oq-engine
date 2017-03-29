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
import time
import logging
from openquake.baselib import sap, general, parallel
from openquake.hazardlib import valid
from openquake.commonlib import readinput, datastore, logs
from openquake.commands import engine


@sap.Script
def run_tiles(num_tiles, job_ini, poolsize=0):
    """
    Run a hazard calculation by splitting the sites into tiles.
    WARNING: this is experimental and meant only for internal users
    """
    t0 = time.time()
    oq = readinput.get_oqparam(job_ini)
    num_sites = len(readinput.get_mesh(oq))
    task_args = [(job_ini, slc)
                 for slc in general.split_in_slices(num_sites, num_tiles)]
    if poolsize == 0:  # no pool
        Starmap = parallel.Sequential
    elif os.environ.get('OQ_DISTRIBUTE') == 'celery':
        Starmap = parallel.Processmap  # celery plays only with processes
    else:  # multiprocessing plays only with threads
        Starmap = parallel.Threadmap
    parent_child = [None, None]

    def agg(calc_ids, calc_id):
        if not calc_ids:  # first calculation
            parent_child[0] = calc_id
        parent_child[1] = calc_id
        logs.dbcmd('update_parent_child', parent_child)
        logging.warn('Finished calculation %d of %d',
                     len(calc_ids) + 1, num_tiles)
        return calc_ids + [calc_id]
    calc_ids = Starmap(engine.run_tile, task_args, poolsize).reduce(agg, [])
    for calc_id in calc_ids:
        print(os.path.join(datastore.DATADIR, 'calc_%d.hdf5' % calc_id))
    print('Total calculation time: %.1f h' % ((time.time() - t0) / 3600.))

run_tiles.arg('num_tiles', 'number of tiles to generate',
              type=valid.positiveint)
run_tiles.arg('job_ini', 'calculation configuration file '
              '(or files, comma-separated)')
run_tiles.opt('poolsize', 'size of the pool (default 0, no pool)',
              type=valid.positiveint)
