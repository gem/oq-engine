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

from __future__ import print_function
import io
import os
import getpass
import logging
import numpy

from openquake.baselib import sap
from openquake.hazardlib import valid, stats
from openquake.commonlib import datastore, calc
from openquake.commonlib.writers import write_csv
from openquake.commonlib.util import rmsep
from openquake.commonlib import config
from openquake.commonlib import logs
from openquake.calculators.views import view

MULTI_USER = valid.boolean(config.get('dbserver', 'multi_user') or 'false')
if MULTI_USER:
    # get the datastore of the user who ran the job
    def read(calc_id):
        job = logs.dbcmd('get_job', calc_id, getpass.getuser())
        datadir = os.path.dirname(job.ds_calc_dir)
        return datastore.read(job.id, datadir=datadir)
else:  # get the datastore of the current user
    read = datastore.read


def get_hcurves_and_means(dstore):
    """
    Extract hcurves from the datastore and compute their means.

    :returns: curves_by_rlz, mean_curves
    """
    getter = calc.PmapGetter(dstore)
    sitecol = dstore['sitecol']
    pmaps = getter.get_pmaps(sitecol.sids)
    return dict(zip(getter.rlzs, pmaps)), dstore['hcurves/mean']


@sap.Script
def show(what, calc_id=-1):
    """
    Show the content of a datastore (by default the last one).
    """
    if what == 'all':  # show all
        if not os.path.exists(datastore.DATADIR):
            return
        rows = []
        for calc_id in datastore.get_calc_ids(datastore.DATADIR):
            try:
                ds = datastore.read(calc_id)
                oq = ds['oqparam']
                cmode, descr = oq.calculation_mode, oq.description
            except:
                # invalid datastore file, or missing calculation_mode
                # and description attributes, perhaps due to a manual kill
                f = os.path.join(datastore.DATADIR, 'calc_%s.hdf5' % calc_id)
                logging.warn('Unreadable datastore %s', f)
                continue
            else:
                rows.append((calc_id, cmode, descr.encode('utf-8')))
        for row in sorted(rows, key=lambda row: row[0]):  # by calc_id
            print('#%d %s: %s' % row)
        return

    ds = read(calc_id)

    # this part is experimental
    if what == 'rlzs' and 'poes' in ds:
        min_value = 0.01  # used in rmsep
        getter = calc.PmapGetter(ds)
        sitecol = ds['sitecol']
        pmaps = getter.get_pmaps(sitecol.sids)
        weights = [rlz.weight for rlz in getter.rlzs]
        mean = stats.compute_pmap_stats(pmaps, [numpy.mean], weights)
        dists = []
        for rlz, pmap in zip(getter.rlzs, pmaps):
            dist = rmsep(mean.array, pmap.array, min_value)
            dists.append((dist, rlz))
        print('Realizations in order of distance from the mean curves')
        for dist, rlz in sorted(dists):
            print('%s: rmsep=%s' % (rlz, dist))
    elif view.keyfunc(what) in view:
        print(view(what, ds))
    elif what in ds:
        obj = ds[what]
        if hasattr(obj, 'value'):  # an array
            print(write_csv(io.StringIO(), obj.value))
        else:
            print(obj)
    else:
        print('%s not found' % what)

    ds.close()

show.arg('what', 'key or view of the datastore')
show.arg('calc_id', 'calculation ID', type=int)
