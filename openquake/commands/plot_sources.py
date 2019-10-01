# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2019 GEM Foundation
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
from openquake.baselib import sap
from openquake.commonlib import util
from openquake.hazardlib.geo.utils import cross_idl


@sap.script
def plot_sources(calc_id=-1):
    """
    Plot the sources (except point sources)
    """
    # NB: matplotlib is imported inside since it is a costly import
    import matplotlib.pyplot as p
    from openquake.hmtk.plotting.patch import PolygonPatch
    dstore = util.read(calc_id)
    info = dstore['source_info'][()]
    sitecol = dstore['sitecol']
    lons, lats = sitecol.lons, sitecol.lats
    if len(lons) > 1 and cross_idl(*lons):
        lons %= 360
    fig, ax = p.subplots()
    ax.grid(True)
    minxs = []
    maxxs = []
    minys = []
    maxys = []
    n = 0
    tot = 0
    for rec in info:
        if rec['wkt'].startswith('POLYGON'):
            poly = shapely.wkt.loads(rec['wkt'])
            minx, miny, maxx, maxy = poly.bounds
            minxs.append(minx)
            maxxs.append(maxx)
            minys.append(miny)
            maxys.append(maxy)
            if rec['num_sites']:  # not filtered out
                alpha = .3
                n += 1
            else:
                alpha = .1
            pp = PolygonPatch(poly, alpha=alpha)
            ax.add_patch(pp)
            tot += 1
    ax.scatter(lons, lats, marker='o', color='red')
    ax.set_xlim(min(minxs), max(maxxs))
    ax.set_ylim(min(minys), max(maxys))
    ax.set_title('%d/%d sources' % (n, tot))
    p.show()


plot_sources.arg('calc_id', 'a computation id', type=int)
