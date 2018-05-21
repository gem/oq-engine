# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2018 GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import shapely.wkt
from openquake.baselib import sap, datastore


@sap.Script
def plot_assets(calc_id=-1):
    """
    Plot the sites and the assets
    """
    # NB: matplotlib is imported inside since it is a costly import
    import matplotlib.pyplot as p
    from openquake.hmtk.plotting.patch import PolygonPatch
    dstore = datastore.read(calc_id)
    oq = dstore['oqparam']
    sitecol = dstore['sitecol']
    assetcol = dstore['assetcol'].array
    fig = p.figure()
    ax = fig.add_subplot(111)
    if oq.region:
        pp = PolygonPatch(shapely.wkt.loads(oq.region), alpha=0.01)
        ax.add_patch(pp)
    else:
        ax.grid(True)
    p.scatter(sitecol.complete.lons, sitecol.complete.lats, marker='.',
              color='gray')
    p.scatter(assetcol['lon'], assetcol['lat'], marker='.', color='green')
    p.scatter(sitecol.lons, sitecol.lats, marker='o', color='black')
    p.show()

plot_assets.arg('calc_id', 'a computation id', type=int)
