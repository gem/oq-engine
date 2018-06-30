#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2018, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import numpy
from openquake.baselib import sap, datastore
from openquake.calculators.getters import PmapGetter


@sap.Script
def compare_mean_curves(calc_ref, calc, rtol=.01, atol=1E-5):
    """
    Compare the hazard curves coming from two different calculations.
    """
    dstore_ref = datastore.read(calc_ref)
    dstore = datastore.read(calc)
    sitecol_ref = dstore_ref['sitecol']
    sitecol = dstore['sitecol']
    site_id_ref = {(lon, lat): sid for sid, lon, lat in zip(
        sitecol_ref.sids, sitecol_ref.lons, sitecol_ref.lats)}
    site_id = {(lon, lat): sid for sid, lon, lat in zip(
        sitecol.sids, sitecol.lons, sitecol.lats)}
    common = set(site_id_ref) & set(site_id)
    if not common:
        raise RuntimeError('There are no common sites between calculation '
                           '%d and %d' % (calc_ref, calc))
    pmap_ref = PmapGetter(dstore_ref, sids=[site_id_ref[lonlat]
                                            for lonlat in common]).get_mean()
    pmap = PmapGetter(dstore, sids=[site_id[lonlat]
                                    for lonlat in common]).get_mean()
    for sid in pmap:
        ok = numpy.allclose(pmap[sid].array, pmap_ref[sid].array,
                            rtol=rtol, atol=atol)
        print(sid, ok)
        if not ok:
            print(numpy.hstack([pmap[sid].array, pmap_ref[sid].array]))


compare_mean_curves.arg('calc_ref', 'first calculation', type=int)
compare_mean_curves.arg('calc', 'second calculation', type=int)
compare_mean_curves.arg('rtol', 'relative tolerance', type=float)
compare_mean_curves.arg('atol', 'absolute tolerance', type=float)


if __name__ == '__main__':
    compare_mean_curves.callfunc()
