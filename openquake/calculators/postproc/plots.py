# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# 
# Copyright (C) 2024, GEM Foundation
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
from shapely.geometry import MultiPolygon
from openquake.commonlib import readinput, datastore
from openquake.hmtk.plotting.patch import PolygonPatch


def import_plt():
    if os.environ.get('TEXT'):
        import plotext as plt
    else:
        import matplotlib.pyplot as plt
    return plt


def add_borders(ax, read_df=readinput.read_countries_df, buffer=0):
    plt = import_plt()
    polys = read_df(buffer)['geom']
    cm = plt.get_cmap('RdBu')
    num_colours = len(polys)
    for idx, poly in enumerate(polys):
        colour = cm(1. * idx / num_colours)
        if isinstance(poly, MultiPolygon):
            for onepoly in poly.geoms:
                ax.add_patch(PolygonPatch(onepoly, fc=colour, alpha=0.1))
        else:
            ax.add_patch(PolygonPatch(poly, fc=colour, alpha=0.1))
    return ax


def get_country_iso_codes(calc_id, assetcol):
    dstore = datastore.read(calc_id)
    try:
        ALL_ID_0 = dstore['assetcol/tagcol/ID_0'][:]
        ID_0 = ALL_ID_0[numpy.unique(assetcol['ID_0'])]
    except KeyError:  # ID_0 might be missing
        id_0_str = None
    else:
        id_0_str = ', '.join(id_0.decode('utf8') for id_0 in ID_0)
    return id_0_str


def plot_avg_gmf(ex, imt):
    plt = import_plt()
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.grid(True)
    ax.set_xlabel('Lon')
    ax.set_ylabel('Lat')

    title = 'Avg GMF for %s' % imt
    assetcol = get_assetcol(ex.calc_id)
    if assetcol is not None:
        country_iso_codes = get_country_iso_codes(ex.calc_id, assetcol)
        if country_iso_codes is not None:
            title += ' (Countries: %s)' % country_iso_codes
    ax.set_title(title)

    avg_gmf = ex.get('avg_gmf?imt=%s' % imt)
    gmf = avg_gmf[imt]
    markersize = 5
    coll = ax.scatter(avg_gmf['lons'], avg_gmf['lats'], c=gmf, cmap='jet',
                      s=markersize)
    plt.colorbar(coll)

    ax = add_borders(ax)

    minx = avg_gmf['lons'].min()
    maxx = avg_gmf['lons'].max()
    miny = avg_gmf['lats'].min()
    maxy = avg_gmf['lats'].max()
    w, h = maxx - minx, maxy - miny
    ax.set_xlim(minx - 0.2 * w, maxx + 0.2 * w)
    ax.set_ylim(miny - 0.2 * h, maxy + 0.2 * h)
    return plt


def get_assetcol(calc_id):
    try:
        dstore = datastore.read(calc_id)
    except OSError:
        return
    if 'assetcol' in dstore:
        try:
            assetcol = dstore['assetcol'][()]
        except AttributeError:
            assetcol = dstore['assetcol'].array
        return assetcol
