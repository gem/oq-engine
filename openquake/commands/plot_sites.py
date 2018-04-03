# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2018 GEM Foundation
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

from __future__ import division
import logging
from openquake.baselib import sap, datastore
from openquake.hazardlib.calc.filters import SourceFilter
from openquake.commonlib import readinput


@sap.Script
def plot_sites(calc_id=-1):
    """
    Plot the sites and the bounding boxes of the sources, enlarged by
    the maximum distance
    """
    # NB: matplotlib is imported inside since it is a costly import
    import matplotlib.pyplot as p
    from matplotlib.patches import Rectangle
    logging.basicConfig(level=logging.INFO)
    dstore = datastore.read(calc_id)
    oq = dstore['oqparam']
    sitecol = dstore['sitecol']
    srcfilter = SourceFilter(sitecol, oq.maximum_distance)
    csm = readinput.get_composite_source_model(oq).filter(srcfilter)
    fig = p.figure()
    ax = fig.add_subplot(111)
    ax.grid(True)
    for src in csm.get_sources():
        llcorner, width, height = srcfilter.get_rectangle(src)
        ax.add_patch(Rectangle(llcorner, width, height, fill=False))
    p.scatter(sitecol.lons, sitecol.lats, marker='+')
    p.show()


plot_sites.arg('calc_id', 'a computation id', type=int)
