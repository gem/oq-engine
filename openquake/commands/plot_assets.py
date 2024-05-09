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

import numpy
import shapely
import logging
from openquake.commonlib import datastore
from openquake.hazardlib.geo.utils import cross_idl
from openquake.commands.plot import (
    add_borders, get_assetcol, get_country_iso_codes)


def main(calc_id: int = -1, site_model=False,
         save_to=None, *, show=True, assets_only=False):
    """
    Plot the sites and the assets
    """

    # NB: matplotlib is imported inside since it is a costly import
    import matplotlib.pyplot as p
    from openquake.hmtk.plotting.patch import PolygonPatch

    dstore = datastore.read(calc_id)
    try:
        region = dstore['oqparam'].region
    except KeyError:
        region = None
    sitecol = dstore['sitecol']
    assetcol = get_assetcol(calc_id)
    fig = p.figure()
    ax = fig.add_subplot(111)
    if region:
        region_geom = shapely.wkt.loads(region)
        pp = PolygonPatch(region_geom, alpha=0.1)
        ax.add_patch(pp)
    ax.grid(True)
    if assets_only:
        markersize_site_model = markersize_assets = 5
    else:
        markersize_site_model = markersize_sitecol = markersize_assets = 18
        markersize_discarded = markersize_assets
    if site_model and 'site_model' in dstore:
        sm = dstore['site_model']
        sm_lons, sm_lats = sm['lon'], sm['lat']
        if len(sm_lons) > 1 and cross_idl(*sm_lons):
            sm_lons %= 360
        p.scatter(sm_lons, sm_lats, marker='.', color='orange',
                  label='site model', s=markersize_site_model)
    # p.scatter(sitecol.complete.lons, sitecol.complete.lats, marker='.',
    #           color='gray', label='grid')
    p.scatter(assetcol['lon'], assetcol['lat'], marker='.', color='green',
              label='assets', s=markersize_assets)
    if not assets_only:
        p.scatter(sitecol.lons, sitecol.lats, marker='+', color='black',
                  label='sites', s=markersize_sitecol)
        if 'discarded' in dstore:
            disc = numpy.unique(dstore['discarded']['lon', 'lat'])
            p.scatter(disc['lon'], disc['lat'], marker='x', color='red',
                      label='discarded', s=markersize_discarded)

    ax = add_borders(ax)

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
