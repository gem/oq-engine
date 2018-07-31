#!/usr/bin/env python3
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

from openquake.baselib import sap, hdf5, datastore
from openquake.calculators.getters import PmapGetter


@sap.Script
def combine_mean_curves(calc_big, calc_small):
    """
    Combine the hazard curves coming from two different calculations.
    The result will be the hazard curves of calc_big, updated on the sites
    in common with calc_small with the PoEs of calc_small. For instance:
    calc_big = USA, calc_small = California
    """
    dstore_big = datastore.read(calc_big)
    dstore_small = datastore.read(calc_small)
    sitecol_big = dstore_big['sitecol']
    sitecol_small = dstore_small['sitecol']
    site_id_big = {(lon, lat): sid for sid, lon, lat in zip(
        sitecol_big.sids, sitecol_big.lons, sitecol_big.lats)}
    site_id_small = {(lon, lat): sid for sid, lon, lat in zip(
        sitecol_small.sids, sitecol_small.lons, sitecol_small.lats)}
    common = set(site_id_big) & set(site_id_small)
    if not common:
        raise RuntimeError('There are no common sites between calculation '
                           '%d and %d' % (calc_big, calc_small))
    sids_small = [site_id_small[lonlat] for lonlat in common]
    pmap_big = PmapGetter(dstore_big).get_mean()  # USA
    pmap_small = PmapGetter(dstore_big, sids=sids_small).get_mean()  # Cal
    for lonlat in common:
        pmap_big[site_id_big[lonlat]] |= pmap_small.get(
            site_id_small[lonlat], 0)
    out = 'combine_%d_%d.hdf5' % (calc_big, calc_small)
    with hdf5.File(out, 'w') as h5:
        h5['hcurves/mean'] = pmap_big
        h5['oqparam'] = dstore_big['oqparam']
        h5['sitecol'] = dstore_big['sitecol']
    print('Generated %s' % out)


combine_mean_curves.arg('calc_big', 'first calculation', type=int)
combine_mean_curves.arg('calc_small', 'second calculation', type=int)

if __name__ == '__main__':
    combine_mean_curves.callfunc()
