# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2019 GEM Foundation
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
from openquake.baselib import sap
from openquake.hazardlib.geo.utils import cross_idl
from openquake.commonlib import util


@sap.script
def plot_sites(calc_id=-1):
    """
    Plot the sites
    """
    # NB: matplotlib is imported inside since it is a costly import
    import matplotlib.pyplot as p
    dstore = util.read(calc_id)
    sitecol = dstore['sitecol']
    lons, lats = sitecol.lons, sitecol.lats
    if len(lons) > 1 and cross_idl(*lons):
        lons %= 360

    fig, ax = p.subplots()
    ax.grid(True)
    if 'site_model' in dstore:
        sm = dstore['site_model']
        sm_lons, sm_lats = sm['lon'], sm['lat']
        if len(sm_lons) > 1 and cross_idl(*sm_lons):
            sm_lons %= 360
        p.scatter(sm_lons, sm_lats, marker='.', color='orange')
    p.scatter(lons, lats, marker='+')
    p.show()


plot_sites.arg('calc_id', 'a computation id', type=int)
