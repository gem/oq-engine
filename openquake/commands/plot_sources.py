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


@sap.script
def plot_sources(calc_id=-1):
    """
    Plot the sources (except point sources)
    """
    # NB: matplotlib is imported inside since it is a costly import
    import matplotlib.pyplot as p
    from openquake.hmtk.plotting.patch import PolygonPatch
    dstore = util.read(calc_id)
    wkts = dstore['source_info']['wkt']
    fig, ax = p.subplots()
    ax.grid(True)
    minxs = []
    maxxs = []
    minys = []
    maxys = []
    for wkt in wkts:
        if wkt.startswith('POLYGON'):
            poly = shapely.wkt.loads(wkt)
            minx, miny, maxx, maxy = poly.bounds
            minxs.append(minx)
            maxxs.append(maxx)
            minys.append(miny)
            maxys.append(maxy)
            pp = PolygonPatch(poly, alpha=0.1)
            ax.add_patch(pp)
    ax.set_xlim(min(minxs), max(maxxs))
    ax.set_ylim(min(minys), max(maxys))
    p.show()


plot_sources.arg('calc_id', 'a computation id', type=int)
