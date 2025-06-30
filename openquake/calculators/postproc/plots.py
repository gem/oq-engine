# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024-2025, GEM Foundation
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
import contextily
from pyproj import Transformer
from shapely.geometry import MultiPolygon
from openquake.commonlib import readinput, datastore
from openquake.hmtk.plotting.patch import PolygonPatch


def import_plt():
    if os.environ.get('TEXT'):
        import plotext as plt
    else:
        import matplotlib.pyplot as plt
    return plt


def add_basemap(ax, x_min, y_min, x_max, y_max,
                source=contextily.providers.CartoDB.Positron):
    # NOTE: another interesting option:
    # source = contextily.providers.TopPlusOpen.Grey
    img, extent = contextily.bounds2img(x_min, y_min, x_max, y_max, source=source)
    ax.imshow(img, extent=extent, interpolation='bilinear', alpha=1)
    ax.text(
        0.01, 0.01,  # Position: Bottom-left corner (normalized coordinates)
        source['attribution'],
        transform=ax.transAxes,  # Place text relative to axes
        fontsize=8, color="black", alpha=0.5,
        ha="left",  # Horizontal alignment
        va="bottom",  # Vertical alignment
    )


def auto_limits(ax):
    # Set the plot to display all contents and return the limits determined
    # automatically
    ax.set_xlim(auto=True)
    ax.set_ylim(auto=True)
    ax.relim()
    ax.autoscale_view()
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    return xlim, ylim


def adjust_limits(ax, xlim, ylim, padding=1):
    # Add some padding around the given limits and give a square aspect to the plot
    x_min, x_max = xlim
    y_min, y_max = ylim
    x_min, x_max = x_min - padding, x_max + padding
    y_min, y_max = y_min - padding, y_max + padding
    x_range = x_max - x_min
    y_range = y_max - y_min
    max_range = max(x_range, y_range)
    x_center = (x_min + x_max) / 2
    y_center = (y_min + y_max) / 2
    xlim = x_center - max_range / 2, x_center + max_range / 2
    ylim = y_center - max_range / 2, y_center + max_range / 2
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)


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


def add_cities(ax, xlim, ylim, read_df=readinput.read_cities_df,
               lon_field='longitude', lat_field='latitude',
               label_field='name'):
    data = read_df(lon_field, lat_field, label_field)
    if data is None:
        return
    data = data[(data[lon_field] >= xlim[0]) & (data[lon_field] <= xlim[1])
                & (data[lat_field] >= ylim[0]) & (data[lat_field] <= ylim[1])]
    if len(data) == 0:
        return
    ax.scatter(data[lon_field], data[lat_field], label="Populated places",
               s=2, color='black', alpha=0.5)
    for _, row in data.iterrows():
        ax.text(row[lon_field], row[lat_field], row[label_field], fontsize=7,
                ha='right', alpha=0.5)


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
                  with_cities=False, return_base64=False,
                  rupture=None):
    plt = import_plt()
    if backend is not None:
        # we may need to use a non-interactive backend
        import matplotlib
        matplotlib.use(backend)
    _fig, ax = plt.subplots(figsize=figsize)
    ax.set_aspect('equal')
    # ax.grid(True)
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    title = 'Avg GMF for %s' % imt
    ax.set_title(title)
    gmf = shakemap_array['val'][imt]
    markersize = 0.005
    transformer = Transformer.from_crs('EPSG:4326', 'EPSG:3857', always_xy=True)
    x_webmercator, y_webmercator = transformer.transform(
        shakemap_array['lon'], shakemap_array['lat'])
    coll = ax.scatter(shakemap_array['lon'], shakemap_array['lat'], c=gmf,
                      cmap='jet', s=markersize)
    plt.colorbar(coll)
    if rupture is not None:
        add_rupture_webmercator(
            ax, rupture, hypo_alpha=0.8, hypo_markersize=8, surf_alpha=1,
            surf_facecolor='none', surf_linestyle='--')
    xlim, ylim = auto_limits(ax)
    x_min, x_max = xlim
    y_min, y_max = ylim
    add_basemap(ax, x_min, y_min, x_max, y_max)
    coll = ax.scatter(x_webmercator, y_webmercator, c=gmf, cmap='jet', s=markersize,
                      alpha=0.4)
    plt.colorbar(coll, ax=ax)
    adjust_limits(ax, xlim, ylim, padding=1E5)
    if with_cities:
        add_cities(ax, xlim, ylim)
    if return_base64:
        return plt_to_base64(plt)
    else:
        return plt


def plot_avg_gmf(ex, imt):
    plt = import_plt()
    _fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_aspect('equal')
    # ax.grid(True)
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
    transformer = Transformer.from_crs('EPSG:4326', 'EPSG:3857', always_xy=True)
    x_webmercator, y_webmercator = transformer.transform(
        avg_gmf['lons'], avg_gmf['lats'])
    xlim, ylim = auto_limits(ax)
    x_min, x_max = xlim
    y_min, y_max = ylim
    add_basemap(ax, x_min, y_min, x_max, y_max)
    coll = ax.scatter(x_webmercator, y_webmercator, c=gmf, cmap='jet', s=markersize)
    plt.colorbar(coll, ax=ax)
    adjust_limits(ax, xlim, ylim, padding=1E5)
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


def add_surface_webmercator(
        ax, surface, label, alpha=0.5, facecolor=None, linestyle='-'):
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    lon, lat = surface.get_surface_boundaries()
    x, y = transformer.transform(lon, lat)  # Transform lat/lon to Web Mercator
    fill_params = {
        'alpha': alpha,
        'edgecolor': 'grey',
        'label': label
    }
    if facecolor is not None:
        fill_params['facecolor'] = facecolor
    ax.fill(x, y, **fill_params)


def add_rupture(ax, rup, hypo_alpha=0.5, hypo_markersize=8, surf_alpha=0.5,
                surf_facecolor=None, surf_linestyle='-'):
    if hasattr(rup.surface, 'surfaces'):
        for surf_idx, surface in enumerate(rup.surface.surfaces):
            add_surface(ax, surface, 'Surface %d' % surf_idx, alpha=surf_alpha,
                        facecolor=surf_facecolor, linestyle=surf_linestyle)
    else:
        add_surface(ax, rup.surface, 'Surface', alpha=surf_alpha,
                    facecolor=surf_facecolor, linestyle=surf_linestyle)
    ax.plot(rup.hypocenter.x, rup.hypocenter.y, marker='*',
            color='orange', label='Hypocenter', alpha=hypo_alpha,
            linestyle='', markersize=8)


def add_rupture_webmercator(
        ax, rup, hypo_alpha=0.5, hypo_markersize=8, surf_alpha=0.5,
        surf_facecolor=None, surf_linestyle='-'):
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    if hasattr(rup.surface, 'surfaces'):
        for surf_idx, surface in enumerate(rup.surface.surfaces):
            add_surface_webmercator(
                ax, surface, 'Surface %d' % surf_idx, alpha=surf_alpha,
                facecolor=surf_facecolor, linestyle=surf_linestyle)
    else:
        add_surface_webmercator(
            ax, rup.surface, 'Surface', alpha=surf_alpha,
            facecolor=surf_facecolor, linestyle=surf_linestyle)
    hypo_x, hypo_y = transformer.transform(rup.hypocenter.longitude,
                                           rup.hypocenter.latitude)
    ax.plot(hypo_x, hypo_y, marker='*', color='orange', label='Hypocenter',
            alpha=hypo_alpha, linestyle='', markersize=hypo_markersize)


def plot_rupture(rup, backend=None, figsize=(10, 10),
                 with_cities=False, with_borders=True, return_base64=False):
    # NB: matplotlib is imported inside since it is a costly import
    plt = import_plt()
    if backend is not None:
        # we may need to use a non-interactive backend
        import matplotlib
        matplotlib.use(backend)
    _fig, ax = plt.subplots(figsize=figsize)
    title = f"width={rup.surface.get_width():.4f}"
    if hasattr(rup.surface, 'length'):
        title += f", length={rup.surface.length:.4f}"
    title += f", area={rup.surface.get_area():.4f}"
    ax.set_title(title)
    ax.set_aspect('equal')
    ax.grid(True)
    add_rupture(ax, rup)
    xlim, ylim = auto_limits(ax)
    if with_borders:
        add_borders(ax)
    if with_cities:
        add_cities(ax, xlim, ylim)
    adjust_limits(ax, xlim, ylim, padding=3)
    ax.legend()
    if return_base64:
        return plt_to_base64(plt)
    else:
        return plt


def plot_rupture_webmercator(rup, backend=None, figsize=(10, 10), return_base64=False):
    # NB: matplotlib is imported inside since it is a costly import
    plt = import_plt()
    if backend is not None:
        # we may need to use a non-interactive backend
        import matplotlib
        matplotlib.use(backend)
    _fig, ax = plt.subplots(figsize=figsize)
    ax.set_aspect('equal')
    # ax.grid(True)
    add_rupture_webmercator(
        ax, rup, hypo_alpha=0.8, hypo_markersize=8, surf_alpha=0.3,
        surf_linestyle='--')
    xlim, ylim = auto_limits(ax)
    x_min, x_max = xlim
    y_min, y_max = ylim
    add_basemap(ax, x_min, y_min, x_max, y_max,
                source=contextily.providers.TopPlusOpen.Color)
    adjust_limits(ax, xlim, ylim, padding=1E5)
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


# useful for plotting mmi_tags
def plot_geom(multipol, lons, lats):
    plt = import_plt()
    ax = plt.figure().add_subplot(111)
    for pol in list(multipol.geoms):
        ax.add_patch(PolygonPatch(pol, alpha=0.1))
    plt.scatter(lons, lats, marker='.', color='green')
    plt.show()


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
