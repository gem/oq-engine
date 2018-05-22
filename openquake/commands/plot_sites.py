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
import logging
import random
import numpy
from openquake.baselib import sap, datastore
from openquake.hazardlib.geo.utils import cross_idl, fix_lon
from openquake.hazardlib.calc.filters import SourceFilter
from openquake.commonlib import readinput


def cross(lonlat, width, height):
    return cross_idl(lonlat[0], lonlat[0] + width)


def fix_polygon(poly, idl):
    # manage the international date line and add the first point as last point
    # to close the polygon
    lons = poly.lons % 360 if idl else poly.lons
    return (numpy.append(lons, lons[0]),
            numpy.append(poly.lats, poly.lats[0]))


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
    lons, lats = sitecol.lons, sitecol.lats
    srcfilter = SourceFilter(sitecol.complete, oq.maximum_distance)
    csm = readinput.get_composite_source_model(oq).filter(srcfilter)
    sources = csm.get_sources()
    if len(sources) > 100:
        logging.info('Sampling 100 sources of %d', len(sources))
        sources = random.Random(42).sample(sources, 100)
    fig, ax = p.subplots()
    ax.grid(True)
    rects = [srcfilter.get_rectangle(src) for src in sources]
    lonset = set(lons)
    for ((lon, lat), width, height) in rects:
        lonset.add(lon)
        lonset.add(fix_lon(lon + width))
    idl = cross_idl(min(lonset), max(lonset))
    if idl:
        lons = lons % 360
    for src, ((lon, lat), width, height) in zip(sources, rects):
        lonlat = (lon % 360 if idl else lon, lat)
        ax.add_patch(Rectangle(lonlat, width, height, fill=False))
        if hasattr(src.__class__, 'polygon'):
            xs, ys = fix_polygon(src.polygon, idl)
            p.plot(xs, ys, marker='.')

    p.scatter(lons, lats, marker='+')
    p.show()


plot_sites.arg('calc_id', 'a computation id', type=int)
