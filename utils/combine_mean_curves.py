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
def combine_mean_curves(calc1, calc2):
    """
    Combine the hazard curves coming from two different calculations.
    The result will be the hazard curves of calc1, updated on the sites
    in common with calc2 with the PoEs of calc2.
    """
    dstore1 = datastore.read(calc1)
    dstore2 = datastore.read(calc2)
    sitecol1 = dstore1['sitecol']
    sitecol2 = dstore2['sitecol']
    site_id1 = {(lon, lat): sid for sid, lon, lat in zip(
        sitecol1.sids, sitecol1.lons, sitecol1.lats)}
    site_id2 = {(lon, lat): sid for sid, lon, lat in zip(
        sitecol2.sids, sitecol2.lons, sitecol2.lats)}
    common = set(site_id1) & set(site_id2)
    if not common:
        raise RuntimeError('There are no common sites between calculation '
                           '%d and %d' % (calc1, calc2))
    sids2 = [site_id2[lonlat] for lonlat in common]
    pmap = PmapGetter(dstore1).get_mean()
    pmap2 = PmapGetter(dstore1, sids=sids2).get_mean()
    for lonlat in common:
        pmap[site_id1[lonlat]] |= pmap2[site_id2[lonlat]]
    out = 'combine_%d_%d.hdf5' % (calc1, calc2)
    with hdf5.File(out, 'w') as h5:
        h5['hcurves/mean'] = pmap
        h5['oqparam'] = dstore1['oqparam']
        h5['sitecol'] = dstore1['sitecol']
    print('Generated %s' % out)


combine_mean_curves.arg('calc1', 'first calculation', type=int)
combine_mean_curves.arg('calc2', 'second calculation', type=int)

if __name__ == '__main__':
    combine_mean_curves.callfunc()
