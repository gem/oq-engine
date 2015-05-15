#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2015, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

from openquake.commonlib import sap, datastore
from openquake.baselib.general import humansize
from openquake.commonlib.commands.plot import combined_curves
from openquake.commonlib.util import rmsep


def show(calc_id, key=None, rlzs=None):
    """
    Show the content of a datastore.

    :param id: numeric calculation ID
    :param key: key of the datastore
    :param rlzs: flag; if given, print out the realizations in order
    """
    ds = datastore.DataStore(calc_id)
    if key:
        obj = ds[key]
        if key.startswith('/') and hasattr(obj, 'value'):
            print obj.value
        else:
            print obj
        return
    # print all keys
    print ds['oqparam'].calculation_mode, \
        'calculation saved in %s contains:' % ds.calc_dir
    for key in ds:
        print key, humansize(ds.getsize(key))
    if rlzs and 'curves_by_trt_gsim' in ds:
        min_value = 0.01  # used in rmsep
        curves_by_rlz, mean_curves = combined_curves(ds)
        dists = []
        for rlz in sorted(curves_by_rlz):
            curves = curves_by_rlz[rlz]
            dist = sum(rmsep(mean_curves[imt], curves[imt], min_value)
                       for imt in mean_curves.dtype.fields)
            dists.append((dist, rlz))
        for dist, rlz in sorted(dists):
            print 'rlz=%s, rmsep=%s' % (rlz, dist)


parser = sap.Parser(show)
parser.arg('calc_id', 'calculation ID', type=int)
parser.arg('key', 'key of the datastore')
parser.flg('rlzs', 'print out the realizations')
