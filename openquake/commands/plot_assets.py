#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2017, GEM Foundation

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
from __future__ import division
from openquake.baselib import sap, datastore


@sap.Script
def plot_assets(calc_id=-1):
    """
    Plot the sites and the assets
    """
    # NB: matplotlib is imported inside since it is a costly import
    import matplotlib.pyplot as p
    dstore = datastore.read(calc_id)
    sitecol = dstore['sitecol']
    assetcol = dstore['assetcol'].array
    fig = p.figure()
    ax = fig.add_subplot(111)
    ax.grid(True)
    p.scatter(sitecol.lons, sitecol.lats, marker='+')
    p.scatter(assetcol['lon'], assetcol['lat'], marker='.')
    p.show()

plot_assets.arg('calc_id', 'a computation id', type=int)
