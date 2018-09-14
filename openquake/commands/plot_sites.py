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
import numpy
from openquake.baselib import sap, datastore
from openquake.hazardlib.geo.utils import cross_idl, fix_lon


def cross(lonlat, width, height):
    return cross_idl(lonlat[0], lonlat[0] + width)


def fix_polygon(poly, idl):
    # manage the international date line and add the first point as last point
    # to close the polygon
    lons = poly.lons % 360 if idl else poly.lons
    return (numpy.append(lons, lons[0]),
            numpy.append(poly.lats, poly.lats[0]))


def get_rectangle(src, geom):
    """
    :param src: a source record
    :param geom: an array of shape (N, 3)
    :returns: ((min_lon, min_lat), width, height), useful for plotting
    """
    lons, lats, deps = geom.T
    min_lon, min_lat, max_lon, max_lat = (
        lons.min(), lats.min(), lons.max(), lats.max())
    return (min_lon, min_lat), (max_lon - min_lon) % 360, max_lat - min_lat


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
    sitecol = dstore['sitecol']
    lons, lats = sitecol.lons, sitecol.lats
    sources = dstore['sources'].value
    srcgeoms = dstore['srcgeoms'].value
    fig, ax = p.subplots()
    ax.grid(True)
    rects = [get_rectangle(src, srcgeoms[src['gidx1']:src['gidx2']])
             for src in sources]
    lonset = set(lons)
    for ((lon, lat), width, height) in rects:
        lonset.add(lon)
        lonset.add(fix_lon(lon + width))
    idl = cross_idl(min(lonset), max(lonset))
    if idl:
        lons = lons % 360
    for ((lon, lat), width, height) in rects:
        lonlat = (lon % 360 if idl else lon, lat)
        ax.add_patch(Rectangle(lonlat, width, height, fill=False))
        # if hasattr(src.__class__, 'polygon'):
        #    xs, ys = fix_polygon(src.polygon, idl)
        #    p.plot(xs, ys, marker='.')

    p.scatter(lons, lats, marker='+')
    p.show()


plot_sites.arg('calc_id', 'a computation id', type=int)
