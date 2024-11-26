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

import io
import os
import base64
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


def add_borders(ax, read_df=readinput.read_countries_df, buffer=0, alpha=0.1):
    plt = import_plt()
    polys = read_df(buffer)['geom']
    cm = plt.get_cmap('RdBu')
    num_colours = len(polys)
    for idx, poly in enumerate(polys):
        colour = cm(1. * idx / num_colours)
        if isinstance(poly, MultiPolygon):
            for onepoly in poly.geoms:
                ax.add_patch(PolygonPatch(onepoly, fc=colour, alpha=alpha))
        else:
            ax.add_patch(PolygonPatch(poly, fc=colour, alpha=alpha))
    return ax


def add_populated_places(ax, xlim, ylim, read_df=readinput.read_populated_places_df,
                         lon_field='longitude', lat_field='latitude',
                         label_field='name'):
    data = read_df(lon_field, lat_field, label_field)
    if data is None:
        return ax
    data = data[(data[lon_field] >= xlim[0]) & (data[lon_field] <= xlim[1])
                & (data[lat_field] >= ylim[0]) & (data[lat_field] <= ylim[1])]
    if len(data) == 0:
        return ax
    ax.scatter(data[lon_field], data[lat_field], label="Populated places",
               s=2, color='black', alpha=0.5)
    for _, row in data.iterrows():
        ax.text(row[lon_field], row[lat_field], row[label_field], fontsize=7,
                ha='right', alpha=0.5)
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


def plt_to_base64(plt):
    """
    The base64 string can be passed to a Django template and embedded
    directly in HTML, without having to save the image to disk
    """
    bio = io.BytesIO()
    plt.savefig(bio, format='png', bbox_inches='tight')
    bio.seek(0)
    img_base64 = base64.b64encode(bio.getvalue()).decode('utf-8')
    return img_base64


def plot_shakemap(shakemap_array, imt, backend=None, figsize=(10, 10),
                  with_populated_places=False, return_base64=False,
                  rupture=None):
    plt = import_plt()
    if backend is not None:
        # we may need to use a non-interactive backend
        import matplotlib
        matplotlib.use(backend)
    _fig, ax = plt.subplots(figsize=figsize)
    ax.set_aspect('equal')
    ax.grid(True)
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    title = 'Avg GMF for %s' % imt
    ax.set_title(title)
    gmf = shakemap_array['val'][imt]
    markersize = 5
    coll = ax.scatter(shakemap_array['lon'], shakemap_array['lat'], c=gmf,
                      cmap='jet', s=markersize)
    plt.colorbar(coll)
    ax = add_borders(ax, alpha=0.2)
    BUF_ANGLE = 1
    min_x = shakemap_array['lon'].min()
    max_x = shakemap_array['lon'].max()
    min_y = shakemap_array['lat'].min()
    max_y = shakemap_array['lat'].max()
    if rupture is not None:
        ax, rup_min_x, rup_min_y, rup_max_x, rup_max_y = add_rupture(
            ax, rupture, hypo_alpha=0.8, hypo_markersize=8, surf_alpha=0.9,
            surf_facecolor='none', surf_linestyle='--')
        min_x = min(min_x, rup_min_x)
        max_x = max(max_x, rup_max_x)
        min_y = min(min_y, rup_min_y)
        max_y = max(max_y, rup_max_y)
    xlim = (min_x - BUF_ANGLE, max_x + BUF_ANGLE)
    ylim = (min_y - BUF_ANGLE, max_y + BUF_ANGLE)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    if with_populated_places:
        ax = add_populated_places(ax, xlim, ylim)
    if return_base64:
        return plt_to_base64(plt)
    else:
        return plt


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


def add_surface(ax, surface, label, alpha=0.5, facecolor=None, linestyle='-'):
    fill_params = {
        'alpha': alpha,
        'edgecolor': 'grey',
        'label': label
    }
    if facecolor is not None:
        fill_params['facecolor'] = facecolor
    ax.fill(*surface.get_surface_boundaries(), **fill_params)
    return surface.get_bounding_box()


def add_rupture(ax, rup, hypo_alpha=0.5, hypo_markersize=8, surf_alpha=0.5,
                surf_facecolor=None, surf_linestyle='-'):
    if hasattr(rup.surface, 'surfaces'):
        min_x = 180
        max_x = -180
        min_y = 90
        max_y = -90
        for surf_idx, surface in enumerate(rup.surface.surfaces):
            min_x_, max_x_, max_y_, min_y_ = add_surface(
                ax, surface, 'Surface %d' % surf_idx, alpha=surf_alpha,
                facecolor=surf_facecolor, linestyle=surf_linestyle)
            min_x = min(min_x, min_x_)
            max_x = max(max_x, max_x_)
            min_y = min(min_y, min_y_)
            max_y = max(max_y, max_y_)
    else:
        min_x, max_x, max_y, min_y = add_surface(
            ax, rup.surface, 'Surface', alpha=surf_alpha, facecolor=surf_facecolor,
            linestyle=surf_linestyle)
    ax.plot(rup.hypocenter.x, rup.hypocenter.y, marker='*',
            color='orange', label='Hypocenter', alpha=hypo_alpha,
            linestyle='', markersize=8)
    return ax, min_x, min_y, max_x, max_y


def plot_rupture(rup, backend=None, figsize=(10, 10),
                 with_populated_places=False, return_base64=False):
    # NB: matplotlib is imported inside since it is a costly import
    plt = import_plt()
    if backend is not None:
        # we may need to use a non-interactive backend
        import matplotlib
        matplotlib.use(backend)
    _fig, ax = plt.subplots(figsize=figsize)
    ax.set_aspect('equal')
    ax.grid(True)
    ax, min_x, min_y, max_x, max_y = add_rupture(ax, rup)
    ax = add_borders(ax)
    BUF_ANGLE = 1
    xlim = (min_x - BUF_ANGLE, max_x + BUF_ANGLE)
    ylim = (min_y - BUF_ANGLE, max_y + BUF_ANGLE)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    if with_populated_places:
        ax = add_populated_places(ax, xlim, ylim)
    ax.legend()
    if return_base64:
        return plt_to_base64(plt)
    else:
        return plt


def add_surface_3d(ax, surface, label):
    lon, lat, depth = surface.get_surface_boundaries_3d()
    lon_grid = numpy.array([[lon[0], lon[1]], [lon[3], lon[2]]])
    lat_grid = numpy.array([[lat[0], lat[1]], [lat[3], lat[2]]])
    depth_grid = numpy.array([[depth[0], depth[1]], [depth[3], depth[2]]])
    ax.plot_surface(lon_grid, lat_grid, depth_grid, alpha=0.5, label=label)


def plot_rupture_3d(rup):
    # NB: matplotlib is imported inside since it is a costly import
    plt = import_plt()
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
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
