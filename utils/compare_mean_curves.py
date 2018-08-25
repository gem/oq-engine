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

import numpy
import matplotlib.pyplot as plt
from openquake.baselib import sap, datastore
from openquake.calculators.getters import PmapGetter


@sap.Script
def compare_mean_curves(calc_ref, calc, nsigma=3):
    """
    Compare the hazard curves coming from two different calculations.
    """
    dstore_ref = datastore.read(calc_ref)
    dstore = datastore.read(calc)
    imtls = dstore_ref['oqparam'].imtls
    if dstore['oqparam'].imtls != imtls:
        raise RuntimeError('The IMTs and levels are different between '
                           'calculation %d and %d' % (calc_ref, calc))
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
    for lonlat in common:
        mean, std = pmap[site_id[lonlat]].array.T  # shape (2, N)
        mean_ref, std_ref = pmap_ref[site_id_ref[lonlat]].array.T
        err = numpy.sqrt(std**2 + std_ref**2)
        for imt in imtls:
            sl = imtls(imt)
            ok = (numpy.abs(mean[sl] - mean_ref[sl]) < nsigma * err[sl]).all()
            if not ok:
                md = (numpy.abs(mean[sl] - mean_ref[sl])).max()
                plt.title('point=%s, imt=%s, maxdiff=%.2e' % (lonlat, imt, md))
                plt.loglog(imtls[imt], mean_ref[sl] + std_ref[sl],
                           label=str(calc_ref), color='black')
                plt.loglog(imtls[imt], mean_ref[sl] - std_ref[sl],
                           color='black')
                plt.loglog(imtls[imt], mean[sl] + std[sl], label=str(calc),
                           color='red')
                plt.loglog(imtls[imt], mean[sl] - std[sl], color='red')
                plt.legend()
                plt.show()


compare_mean_curves.arg('calc_ref', 'first calculation', type=int)
compare_mean_curves.arg('calc', 'second calculation', type=int)
compare_mean_curves.opt('nsigma', 'tolerance as number of sigma', type=float)

if __name__ == '__main__':
    compare_mean_curves.callfunc()
