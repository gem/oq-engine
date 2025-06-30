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
import shapely
import logging
from openquake.commonlib import datastore
from openquake.hazardlib.geo.utils import cross_idl  # , get_bbox
from openquake.calculators.getters import get_ebrupture
from openquake.calculators.postproc.plots import (
    get_assetcol, get_country_iso_codes, add_rupture_webmercator, adjust_limits,
    auto_limits, add_basemap)


def main(calc_id: int = -1, site_model=False,
         save_to=None, *, show=True, assets_only=False):
    """
    Plot the sites and the assets
    """

    # NB: matplotlib is imported inside since it is a costly import
    import matplotlib.pyplot as p
    from pyproj import Transformer
    from openquake.hmtk.plotting.patch import PolygonPatch

    dstore = datastore.read(calc_id)
    oq = dstore['oqparam']
    try:
        region = oq.region
    except KeyError:
        region = None
    sitecol = dstore['sitecol']
    assetcol = get_assetcol(calc_id)
    _fig, ax = p.subplots(figsize=(10, 10))
    transformer = Transformer.from_crs('EPSG:4326', 'EPSG:3857', always_xy=True)
    if region:
        region_geom = shapely.wkt.loads(region)
        region_proj_geom = shapely.ops.transform(transformer.transform, region_geom)
        pp = PolygonPatch(region_proj_geom, alpha=0.1)
        ax.add_patch(pp)
    ax.set_aspect('equal')
    # ax.grid(True)
    # markersize = 0.005
    # if assets_only:
    #     markersize_site_model = markersize_assets = 5
    # else:
    #     markersize_site_model = markersize_sitecol = markersize_assets = 18
    #     markersize_discarded = markersize_assets
    if site_model and 'site_model' in dstore:
        sm = dstore['site_model']
        sm_lons, sm_lats = sm['lon'], sm['lat']
        if len(sm_lons) > 1 and cross_idl(*sm_lons):
            sm_lons %= 360
        x_webmercator, y_webmercator = transformer.transform(sm_lons, sm_lats)
        p.scatter(x_webmercator, y_webmercator, marker='.', color='orange',
                  label='site model')  # , s=markersize_site_model)
    # p.scatter(sitecol.complete.lons, sitecol.complete.lats, marker='.',
    #           color='gray', label='grid')
    x_assetcol_wm, y_assetcol_wm = transformer.transform(
        assetcol['lon'], assetcol['lat'])
    p.scatter(x_assetcol_wm, y_assetcol_wm, marker='.', color='green',
              label='assets')  # , s=markersize_assets)
    if not assets_only:
        x_webmercator, y_webmercator = transformer.transform(
            sitecol.lons, sitecol.lats)
        p.scatter(x_webmercator, y_webmercator, marker='+', color='black',
                  label='sites')  # , s=markersize_sitecol)
        if 'discarded' in dstore:
            disc = numpy.unique(dstore['discarded']['lon', 'lat'])
            x_webmercator, y_webmercator = transformer.transform(
                disc['lon'], disc['lat'])
            p.scatter(x_webmercator, y_webmercator, marker='x', color='red',
                      label='discarded')  # , s=markersize_discarded)
    if oq.rupture_xml or oq.rupture_dict:
        rec = dstore['ruptures'][0]
        lon, lat, _dep = rec['hypo']
        xlon, xlat = [lon], [lat]
        x_webmercator, y_webmercator = transformer.transform(xlon, xlat)
        dist = sitecol.get_cdist(rec)
        print('rupture(%s, %s), dist=%s' % (lon, lat, dist))
        if os.environ.get('OQ_APPLICATION_MODE') == 'ARISTOTLE':
            # assuming there is only 1 rupture, so rup_id=0
            rup = get_ebrupture(dstore, rup_id=0)
            add_rupture_webmercator(
                ax, rup, hypo_alpha=0.8, hypo_markersize=8, surf_alpha=0.3,
                surf_linestyle='--')
        else:
            p.scatter(x_webmercator, y_webmercator, marker='*', color='orange',
                      label='hypocenter', alpha=.5)
    else:
        xlon, xlat = [], []

    if region:
        x_min, y_min, x_max, y_max = region_proj_geom.bounds
        xlim = (x_min, x_max)
        ylim = (y_min, y_max)
    else:
        xlim, ylim = auto_limits(ax)
        x_min, x_max = xlim
        y_min, y_max = ylim
    add_basemap(ax, x_min, y_min, x_max, y_max)
    adjust_limits(ax, xlim, ylim, padding=1E5)

    country_iso_codes = get_country_iso_codes(calc_id, assetcol)
    if country_iso_codes is not None:
        # NOTE: use following lines to add custom items without changing title
        # ax.plot([], [], ' ', label=country_iso_codes)
        # ax.legend()
        title = 'Countries: %s' % country_iso_codes
        ax.legend(title=title)
    else:
        ax.legend()

    if save_to:
        p.savefig(save_to, alpha=True, dpi=300)
        logging.info(f'Plot saved to {save_to}')
    if show:
        p.show()
    return p


main.calc_id = 'a computation id'
main.site_model = 'plot the site model too'
main.save_to = 'save the plot to this filename'
main.show = 'show the plot'
main.assets_only = 'display assets only (without sites and discarded)'
