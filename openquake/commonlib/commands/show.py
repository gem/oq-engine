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
from openquake.baselib.general import ArrayDict
from openquake.commonlib.commands.plot import combined_curves
from openquake.commonlib.util import rmsep


def human(nbytes, suffixes=('B', 'KB', 'MB', 'GB', 'TB', 'PB')):
    """
    Return file size in a human-friendly format
    """
    if nbytes == 0:
        return '0 B'
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[i])


def show(calc_id, key=None, rlzs=None):
    """
    Show the content of a datastore
    """
    ds = datastore.DataStore(calc_id)
    if key:
        print ds[key.split('-')]
        return
    # print all keys
    print ds['oqparam'].calculation_mode, ds, 'saved in %s contains:' % (
        ds.calc_dir)
    for key in ds:
        print key, human(ds.getsize(*key))
    if rlzs and 'curves_by_trt_gsim' in ds:
        min_value = 0.01  # used in rmsep
        curves_by_rlz, mean_curves = combined_curves(ds)
        dists = []
        for rlz in sorted(curves_by_rlz):
            mean = ArrayDict(mean_curves)
            arr = ArrayDict(curves_by_rlz[rlz])
            dists.append((rmsep(mean, arr, min_value), rlz))
        for dist, rlz in sorted(dists):
            print 'rlz=%s, rmsep=%s' % (rlz, dist)


parser = sap.Parser(show)
parser.arg('calc_id', 'calculation ID', type=int)
parser.arg('key', 'key of the datastore')
parser.flg('rlzs', 'print out the realizations')
