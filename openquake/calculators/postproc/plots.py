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
from openquake.calculators.getters import get_ebrupture


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
    _fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_aspect('equal')
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


def add_surface(ax, surface, label):
    ax.fill(*surface.get_surface_boundaries(), alpha=.5, edgecolor='grey',
            label=label)
    return surface.get_bounding_box()


def add_rupture(ax, dstore, rup_id=0):
    ebr = get_ebrupture(dstore, rup_id)
    rup = ebr.rupture
    if hasattr(rup.surface, 'surfaces'):
        min_x = 180
        max_x = -180
        min_y = 90
        max_y = -90
        for surf_idx, surface in enumerate(rup.surface.surfaces):
            min_x_, max_x_, max_y_, min_y_ = add_surface(
                ax, surface, 'Surface %d' % surf_idx)
            min_x = min(min_x, min_x_)
            max_x = max(max_x, max_x_)
            min_y = min(min_y, min_y_)
            max_y = max(max_y, max_y_)
    else:
        min_x, max_x, max_y, min_y = add_surface(ax, rup.surface, 'Surface')
    ax.plot(rup.hypocenter.x, rup.hypocenter.y, marker='*',
            color='orange', label='Hypocenter', alpha=.5,
            linestyle='', markersize=8)
    return ax, min_x, min_y, max_x, max_y


def plot_rupture(dstore):
    # NB: matplotlib is imported inside since it is a costly import
    plt = import_plt()
    _fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_aspect('equal')
    ax.grid(True)
    # assuming there is only 1 rupture, so rup_id=0
    ax, min_x, min_y, max_x, max_y = add_rupture(ax, dstore, rup_id=0)
    ax = add_borders(ax)
    BUF_ANGLE = 4
    ax.set_xlim(min_x - BUF_ANGLE, max_x + BUF_ANGLE)
    ax.set_ylim(min_y - BUF_ANGLE, max_y + BUF_ANGLE)
    ax.legend()
    return plt


def add_surface_3d(ax, surface, label):
    lon, lat, depth = surface.get_surface_boundaries_3d()
    lon_grid = numpy.array([[lon[0], lon[1]], [lon[3], lon[2]]])
    lat_grid = numpy.array([[lat[0], lat[1]], [lat[3], lat[2]]])
    depth_grid = numpy.array([[depth[0], depth[1]], [depth[3], depth[2]]])
    ax.plot_surface(lon_grid, lat_grid, depth_grid, alpha=0.5, label=label)


def plot_rupture_3d(dstore):
    # NB: matplotlib is imported inside since it is a costly import
    plt = import_plt()
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ebr = get_ebrupture(dstore, rup_id=0)
    rup = ebr.rupture
    if hasattr(rup.surface, 'surfaces'):
        for surf_idx, surface in enumerate(rup.surface.surfaces):
            add_surface_3d(ax, surface, 'Surface %d' % surf_idx)
    else:
        add_surface_3d(ax, rup.surface, 'Surface')
    ax.plot(rup.hypocenter.x, rup.hypocenter.y, rup.hypocenter.z, marker='*',
            color='orange', label='Hypocenter', alpha=.5,
            linestyle='', markersize=8)
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_zlabel('Depth')
    ax.legend()
    plt.show()
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
