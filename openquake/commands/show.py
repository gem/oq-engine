# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2018 GEM Foundation
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
import io
import os
import logging
import numpy

from openquake.baselib import sap, config
from openquake.hazardlib import stats
from openquake.baselib import datastore
from openquake.commonlib.writers import write_csv
from openquake.commonlib.util import rmsep
from openquake.commonlib import logs
from openquake.calculators import getters
from openquake.calculators.views import view
from openquake.calculators.extract import extract

if config.dbserver.multi_user:
    def read(calc_id):
        job = logs.dbcmd('get_job', calc_id)
        if job:
            return datastore.read(job.ds_calc_dir + '.hdf5')
        # calc_id can be present in the datastore and not in the database:
        # this happens if the calculation was run with `oq run`
        return datastore.read(calc_id)
else:  # get the datastore of the current user
    read = datastore.read


def get_hcurves_and_means(dstore):
    """
    Extract hcurves from the datastore and compute their means.

    :returns: curves_by_rlz, mean_curves
    """
    rlzs_assoc = dstore['csm_info'].get_rlzs_assoc()
    getter = getters.PmapGetter(dstore, rlzs_assoc)
    sitecol = dstore['sitecol']
    pmaps = getter.get_pmaps(sitecol.sids)
    return dict(zip(getter.rlzs, pmaps)), dstore['hcurves/mean']


@sap.Script
def show(what='contents', calc_id=-1, extra=()):
    """
    Show the content of a datastore (by default the last one).
    """
    datadir = datastore.get_datadir()
    if what == 'all':  # show all
        if not os.path.exists(datadir):
            return
        rows = []
        for calc_id in datastore.get_calc_ids(datadir):
            try:
                ds = read(calc_id)
                oq = ds['oqparam']
                cmode, descr = oq.calculation_mode, oq.description
            except:
                # invalid datastore file, or missing calculation_mode
                # and description attributes, perhaps due to a manual kill
                f = os.path.join(datadir, 'calc_%s.hdf5' % calc_id)
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
        getter = getters.PmapGetter(ds)
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
    elif what.split('/', 1)[0] in extract:
        print(extract(ds, what, *extra))
    elif what in ds:
        obj = ds[what]
        if hasattr(obj, 'value'):  # an array
            print(write_csv(io.BytesIO(), obj.value).decode('utf8'))
        else:
            print(obj)
    else:
        print('%s not found' % what)

    ds.close()

show.arg('what', 'key or view of the datastore')
show.arg('calc_id', 'calculation ID', type=int)
show.arg('extra', 'extra arguments', nargs='*')
