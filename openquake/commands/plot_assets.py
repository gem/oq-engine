# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2019 GEM Foundation
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
import numpy
import shapely.wkt
from openquake.baselib import sap
from openquake.hazardlib.geo.utils import cross_idl
from openquake.commonlib import util


@sap.script
def plot_assets(calc_id=-1, site_model=False):
    """
    Plot the sites and the assets
    """
    # NB: matplotlib is imported inside since it is a costly import
    import matplotlib.pyplot as p
    from openquake.hmtk.plotting.patch import PolygonPatch
    dstore = util.read(calc_id)
    try:
        region = dstore['oqparam'].region
    except KeyError:
        region = None
    sitecol = dstore['sitecol']
    try:
        assetcol = dstore['assetcol'].value
    except AttributeError:
        assetcol = dstore['assetcol'].array
    fig = p.figure()
    ax = fig.add_subplot(111)
    if region:
        pp = PolygonPatch(shapely.wkt.loads(region), alpha=0.1)
        ax.add_patch(pp)
    ax.grid(True)
    if site_model and 'site_model' in dstore:
        sm = dstore['site_model']
        sm_lons, sm_lats = sm['lon'], sm['lat']
        if len(sm_lons) > 1 and cross_idl(*sm_lons):
            sm_lons %= 360
        p.scatter(sm_lons, sm_lats, marker='.', color='orange')
    p.scatter(sitecol.complete.lons, sitecol.complete.lats, marker='.',
              color='gray')
    p.scatter(assetcol['lon'], assetcol['lat'], marker='.', color='green')
    p.scatter(sitecol.lons, sitecol.lats, marker='+', color='black')
    if 'discarded' in dstore:
        disc = numpy.unique(dstore['discarded'].value[['lon', 'lat']])
        p.scatter(disc['lon'], disc['lat'], marker='x', color='red')
    p.show()


plot_assets.arg('calc_id', 'a computation id', type=int)
plot_assets.flg('site_model', 'plot the site model too')
