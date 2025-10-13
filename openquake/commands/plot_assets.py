# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2025 GEM Foundation
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
from openquake.hazardlib.geo.utils import cross_idl
from openquake.calculators.getters import get_ebrupture
from openquake.calculators.postproc.plots import (
    add_borders, get_assetcol, get_country_iso_codes, add_rupture,
    adjust_limits, auto_limits)


def main(calc_id: int = -1, site_model=False,
         save_to=None, *, show=True, assets_only=False):
    """
    Plot the sites, the assets and also rupture and stations if available
    """

    # NB: matplotlib is imported inside since it is a costly import
    import matplotlib.pyplot as p
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
    if region:
        region_geom = shapely.wkt.loads(region)
        pp = PolygonPatch(region_geom, alpha=0.1)
        ax.add_patch(pp)
    ax.set_aspect('equal')
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
    if 'station_data' in dstore:
        try:
            complete = dstore['complete']
        except KeyError:
            if dstore.parent:
                complete = dstore.parent['sitecol'].complete
            else:
                complete = dstore['sitecol'].complete
        station_ids = dstore['station_data/site_id'][:]
        station_sites = numpy.isin(complete.sids, station_ids)
        stations = complete[station_sites]
        if 'stations_considered' in dstore:  # not available in old jobs
            kw_params = dict(label='discarded stations', edgecolors='gray',
                             facecolors='none')
        else:
            kw_params = dict(label='all stations', c='brown')
        # NOTE: we might filter out the stations that were considered, and plot only
        # the discarded ones, but the output looks similar if we plot all stations
        # here, then overlap them with plotting the considered ones on top
        p.scatter(stations['lon'], stations['lat'], marker='D', s=markersize_site_model,
                  **kw_params)
        if 'stations_considered' in dstore:
            # NOTE: overlapping the used ones on top of the full set
            stations_considered = dstore['stations_considered']
            if len(stations_considered) > 0:
                p.scatter(stations_considered['lon'], stations_considered['lat'],
                          marker='D', c='brown', label='considered stations',
                          s=markersize_site_model)
    if oq.rupture_xml or oq.rupture_dict:
        use_shakemap = dstore['oqparam'].shakemap_uri
        if use_shakemap:
            lon, lat = oq.rupture_dict['lon'], oq.rupture_dict['lat']
        else:
            rec = dstore['ruptures'][0]
            lon, lat, _dep = rec['hypo']
            dist = sitecol.get_cdist(rec)
            print('rupture(%s, %s), dist=%s' % (lon, lat, dist))
        xlon, xlat = [lon], [lat]
        if (os.environ.get('OQ_APPLICATION_MODE') == 'ARISTOTLE'
                and not use_shakemap):
            # assuming there is only 1 rupture, so rup_id=0
            rup = get_ebrupture(dstore, rup_id=0).rupture
            ax, add_rupture(ax, rup)
        else:
            p.scatter(xlon, xlat, marker='*', color='orange',
                      label='hypocenter', alpha=.5)
    else:
        xlon, xlat = [], []

    if region:
        minx, miny, maxx, maxy = region_geom.bounds
        xlim = (minx, maxx)
        ylim = (miny, maxy)
    else:
        xlim, ylim = auto_limits(ax)

    add_borders(ax)
    adjust_limits(ax, xlim, ylim, padding=3)

    country_iso_codes = get_country_iso_codes(calc_id, assetcol)
    legend_params = dict(loc='upper left', bbox_to_anchor=(1.05, 1.0), borderaxespad=0.)
    if country_iso_codes is not None:
        # NOTE: use following lines to add custom items without changing title
        # ax.plot([], [], ' ', label=country_iso_codes)
        # ax.legend()
        title = 'Countries: %s' % country_iso_codes
        ax.legend(title=title, **legend_params)
    else:
        ax.legend(**legend_params)

    if save_to:
        p.savefig(save_to, alpha=True, dpi=300)
        logging.info(f'Plot saved to {save_to}')
    if show:
        p.tight_layout()  # adjust to prevent clipping
        p.show()
    return p


main.calc_id = 'a computation id'
main.site_model = 'plot the site model too'
main.save_to = 'save the plot to this filename'
main.show = 'show the plot'
main.assets_only = 'display assets only (without sites and discarded)'
