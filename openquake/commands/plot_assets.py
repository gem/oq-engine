# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2023 GEM Foundation
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

import os
import numpy
import fiona
import shapely
import logging
from shapely.geometry import MultiPolygon, shape
from openquake.commonlib import datastore
from openquake.hazardlib.geo.utils import cross_idl
from openquake.qa_tests_data import global_risk


def main(calc_id: int = -1, site_model=False, shapefile_path=None,
         save_to=None):
    """
    Plot the sites and the assets
    """

    # NB: matplotlib is imported inside since it is a costly import
    import matplotlib.pyplot as p
    from openquake.hmtk.plotting.patch import PolygonPatch

    if shapefile_path is None:
        shapefile_dir = os.path.dirname(global_risk.__file__)
        shapefile_path = os.path.join(
            shapefile_dir, 'geoBoundariesCGAZ_ADM0.shp')
    polys = [shape(pol['geometry']) for pol in fiona.open(shapefile_path)]
    cm = p.get_cmap('RdBu')
    num_colours = len(polys)

    dstore = datastore.read(calc_id)
    try:
        region = dstore['oqparam'].region
    except KeyError:
        region = None
    sitecol = dstore['sitecol']
    try:
        assetcol = dstore['assetcol'][()]
    except AttributeError:
        assetcol = dstore['assetcol'].array
    fig = p.figure()
    ax = fig.add_subplot(111)
    if region:
        region_geom = shapely.wkt.loads(region)
        pp = PolygonPatch(region_geom, alpha=0.1)
        ax.add_patch(pp)
    ax.grid(True)
    if site_model and 'site_model' in dstore:
        sm = dstore['site_model']
        sm_lons, sm_lats = sm['lon'], sm['lat']
        if len(sm_lons) > 1 and cross_idl(*sm_lons):
            sm_lons %= 360
        p.scatter(sm_lons, sm_lats, marker='.', color='orange',
                  label='site model')
    # p.scatter(sitecol.complete.lons, sitecol.complete.lats, marker='.',
    #           color='gray', label='grid')
    p.scatter(assetcol['lon'], assetcol['lat'], marker='.', color='green',
              label='assets')
    p.scatter(sitecol.lons, sitecol.lats, marker='+', color='black',
              label='sites')
    if 'discarded' in dstore:
        disc = numpy.unique(dstore['discarded']['lon', 'lat'])
        p.scatter(disc['lon'], disc['lat'], marker='x', color='red',
                  label='discarded')

    for idx, poly in enumerate(polys):
        colour = cm(1. * idx / num_colours)
        if isinstance(poly, MultiPolygon):
            for onepoly in poly.geoms:
                ax.add_patch(PolygonPatch(onepoly, fc=colour, alpha=0.1))
        else:
            ax.add_patch(PolygonPatch(poly, fc=colour, alpha=0.1))

    if region:
        minx, miny, maxx, maxy = region_geom.bounds
    else:
        minx = assetcol['lon'].min()
        maxx = assetcol['lon'].max()
        miny = assetcol['lat'].min()
        maxy = assetcol['lat'].max()
    w, h = maxx - minx, maxy - miny
    ax.set_xlim(minx - 0.2 * w, maxx + 0.2 * w)
    ax.set_ylim(miny - 0.2 * h, maxy + 0.2 * h)
    ax.legend()
    if save_to:
        p.savefig(save_to, alpha=True, dpi=300)
        logging.info(f'Plot saved to {save_to}')
    p.show()


main.calc_id = 'a computation id'
main.site_model = 'plot the site model too'
main.shapefile_path = 'a shapefile with country/region borders'
main.save_to = 'save the plot to this filename'
