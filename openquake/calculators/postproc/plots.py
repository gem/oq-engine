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
from pathlib import Path
from shapely.geometry import Polygon, box
from openquake.commonlib import readinput, datastore
from openquake.hmtk.plotting.patch import PolygonPatch


def import_plt():
    if os.environ.get('TEXT'):
        import plotext as plt
    else:
        import matplotlib.pyplot as plt
    return plt


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


def add_borders(
        ax, read_df=readinput.read_countries_df,
        facecolor='#F5F5F2',   # Very light grey
        edgecolor='#D0D0D0',   # Faint grey for borders
        linewidth=0.4, alpha=1.0, zorder=0,
        sea_color='#E0F2F7'):  # Pale blue
    """
    Draw filled land regions clipped to the current viewport,
    with seas colored via the axes background.
    Automatically updates on zoom/pan.
    """

    from matplotlib.patches import PathPatch
    from matplotlib.path import Path
    from matplotlib.collections import PatchCollection

    df = read_df()
    geometries = df.geometry.values
    sindex = df.sindex
    ax.set_facecolor(sea_color)

    # Persistent storage for the collection
    state = {'coll': None}

    def _polygon_to_path(polygon):
        if polygon.is_empty:
            return None
        vertices = []
        codes = []
        # Exterior
        ext_coords = numpy.array(polygon.exterior.coords)
        vertices.append(ext_coords)
        codes.append(
            [Path.MOVETO] + [Path.LINETO] * (len(ext_coords) - 2)
            + [Path.CLOSEPOLY])
        # Interiors, holes
        for interior in polygon.interiors:
            int_coords = numpy.array(interior.coords)
            vertices.append(int_coords)
            codes.append(
                [Path.MOVETO] + [Path.LINETO] * (len(int_coords) - 2)
                + [Path.CLOSEPOLY])
        return Path(numpy.concatenate(vertices), numpy.concatenate(codes))

    def redraw(event_ax=None):
        if state['coll'] is not None:
            state['coll'].remove()
            state['coll'] = None

        # Get current viewport
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()
        viewport = box(xmin, ymin, xmax, ymax)
        # Spatial query to only process what is visible
        idx = list(sindex.intersection((xmin, ymin, xmax, ymax)))
        patches = []

        for geom in geometries[idx]:
            try:
                clipped = geom.intersection(viewport)
                if clipped.is_empty:
                    continue
                parts = clipped.geoms if hasattr(clipped, 'geoms') else [clipped]
                for part in parts:
                    if isinstance(part, Polygon):
                        path = _polygon_to_path(part)
                        if path:
                            patches.append(PathPatch(path))
            except Exception:
                continue

        if patches:
            pc = PatchCollection(
                patches, facecolor=facecolor, edgecolor=edgecolor,
                linewidth=linewidth, alpha=alpha, zorder=zorder)
            ax.add_collection(pc)
            state['coll'] = pc

        # Draw without full GUI refresh for speed
        ax.figure.canvas.draw_idle()

    # Re-calculate borders only when the user stops zooming/panning
    ax.callbacks.connect('xlim_changed', redraw)
    ax.callbacks.connect('ylim_changed', redraw)
    # Initial draw
    redraw()


def viewport_label_point(geom, viewport):
    """
    Return a label point guaranteed to be inside
    the visible portion of the geometry.
    """
    try:
        rp = geom.representative_point()
        if viewport.contains(rp):
            return rp
        clipped = geom.intersection(viewport)
        if clipped.is_empty:
            return None
        return clipped.representative_point()
    except Exception:
        return None


def add_region_labels(
        ax, read_df=readinput.read_countries_df, label_field='code',
        fontsize=8, max_extent_deg=40):
    """
    Add region labels that update dynamically on zoom/pan.

    :param ax: matplotlib axis
    :param read_df: function returning DataFrame with 'geom' column
    :param label_field: column name used for labeling
    :param fontsize: label font size
    :param max_extent_deg: hide labels if view wider than this (degrees)
    """

    df = read_df()
    geometries = df.geometry.values
    labels = df[label_field].values
    sindex = df.sindex

    state = {'texts': []}

    def redraw(event_ax):
        # Remove old labels
        for txt in state['texts']:
            txt.remove()
        state['texts'].clear()
        xmin, xmax = event_ax.get_xlim()
        ymin, ymax = event_ax.get_ylim()
        # Hide labels when zoomed too far out
        if (xmax - xmin) > max_extent_deg:
            event_ax.figure.canvas.draw_idle()
            return
        viewport = box(xmin, ymin, xmax, ymax)
        # spatial index query
        idx = list(sindex.intersection((xmin, ymin, xmax, ymax)))
        for i in idx:
            geom = geometries[i]
            if not geom.intersects(viewport):
                continue
            pt = viewport_label_point(geom, viewport)
            if pt is None:
                continue
            txt = event_ax.text(
                pt.x, pt.y, str(labels[i]), ha='center', va='center',
                fontsize=fontsize, color='0.25', zorder=10)
            state['texts'].append(txt)
        event_ax.figure.canvas.draw_idle()

    # Initial draw
    redraw(ax)
    # Redraw on viewport change
    ax.callbacks.connect('xlim_changed', redraw)
    ax.callbacks.connect('ylim_changed', redraw)


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
                  rupture=None, data_alpha=0.8):
    plt = import_plt()
    if backend is not None:
        # we may need to use a non-interactive backend
        import matplotlib
        matplotlib.use(backend)

    # Constrained layout prevents labels from being cut off
    fig, ax = plt.subplots(figsize=figsize, layout='constrained')
    lons = shakemap_array['lon']
    lats = shakemap_array['lat']
    gmf = shakemap_array['val'][imt]

    # Force the axes to shrink to the map's shape instead of staying square
    ax.set_adjustable('box')

    # Calculate data extent and add padding
    lon_min, lon_max = numpy.min(lons), numpy.max(lons)
    lat_min, lat_max = numpy.min(lats), numpy.max(lats)
    # Add 10% padding around the data
    lon_pad = (lon_max - lon_min) * 0.1
    lat_pad = (lat_max - lat_min) * 0.1

    view_limits = [
        lon_min - lon_pad, lon_max + lon_pad,
        lat_min - lat_pad, lat_max + lat_pad
    ]

    # Draw basemap
    # add_borders uses ax.get_xlim/ylim, so we set them now
    ax.set_xlim(view_limits[0], view_limits[1])
    ax.set_ylim(view_limits[2], view_limits[3])
    add_borders(ax, alpha=1.0, zorder=0)

    marker_size = 5
    coll = ax.scatter(shakemap_array['lon'], shakemap_array['lat'], c=gmf,
                      cmap='jet', s=marker_size)

    fig.colorbar(coll, ax=ax, shrink=0.6)

    if rupture is not None:
        add_rupture(ax, rupture, hypo_alpha=0.8, hypo_markersize=8, surf_alpha=0.9,
                    surf_facecolor='none', surf_linestyle='-', zorder=4)

    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title(f'Avg GMF for {imt}')

    if with_cities:
        # Pass the padded limits to add_cities
        add_cities(ax, (view_limits[0], view_limits[1]),
                   (view_limits[2], view_limits[3]))

    if return_base64:
        return plt_to_base64(plt)
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

    xlim, ylim = auto_limits(ax)
    add_borders(ax)
    adjust_limits(ax, xlim, ylim)
    return plt


def add_surface(ax, surface, label, alpha=0.5, facecolor=None, linestyle='-',
                zorder=4):
    fill_params = {
        'alpha': alpha,
        'edgecolor': 'grey',
        'linewidth': 1.2,
        'linestyle': linestyle,
        'label': label,
        'zorder': zorder,
    }
    if facecolor is not None:
        fill_params['facecolor'] = facecolor
    ax.fill(*surface.get_surface_boundaries(), **fill_params)


def add_rupture(ax, rup, hypo_alpha=0.5, hypo_markersize=8, surf_alpha=0.5,
                surf_facecolor=None, surf_linestyle='-', zorder=5):
    """
    Plots the rupture surface and hypocenter.
    """
    from matplotlib import patheffects

    # Plot the Surface Traces/Projections
    if hasattr(rup.surface, 'surfaces'):
        for surf_idx, surface in enumerate(rup.surface.surfaces):
            add_surface(ax, surface, label=f'Surface {surf_idx}',
                        alpha=surf_alpha, facecolor=surf_facecolor,
                        linestyle=surf_linestyle, zorder=zorder)
    else:
        add_surface(ax, rup.surface, label='Surface',
                    alpha=surf_alpha, facecolor=surf_facecolor,
                    linestyle=surf_linestyle, zorder=zorder)

    # Plot the Hypocenter
    # Using a white outline (path_effects) ensures the orange star is visible
    # against both light sea and dark intensity colors.
    ax.plot(rup.hypocenter.x, rup.hypocenter.y,
            marker='*', color='#FFD700',  # Bright Gold/Orange
            markeredgecolor='black', markeredgewidth=0.7,
            label='Hypocenter', alpha=hypo_alpha,
            linestyle='', markersize=hypo_markersize,
            zorder=zorder + 1,
            path_effects=[patheffects.withStroke(
                linewidth=2, foreground="white")])


def plot_rupture(rup, backend=None, figsize=(10, 10),
                 with_cities=False, with_borders=True,
                 with_region_labels=False, return_base64=False):
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
    if with_region_labels:
        add_region_labels(ax)
    if with_cities:
        add_cities(ax, xlim, ylim)
    adjust_limits(ax, xlim, ylim, padding=3)
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
    ax.invert_zaxis()  # positive depth goes downwards
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


def _resolve_limits(ax, x_limits, y_limits, epicenter=None, buffer_ratio=0.05):
    """
    Resolve axis limits ensuring epicenter visibility with a margin.
    :param buffer_ratio: fraction of axis span to use as padding
    """
    # Start from user limits or current limits
    xmin, xmax = x_limits if x_limits else ax.get_xlim()
    ymin, ymax = y_limits if y_limits else ax.get_ylim()

    if epicenter is not None:
        lon, lat = epicenter

        xmin = min(xmin, lon)
        xmax = max(xmax, lon)
        ymin = min(ymin, lat)
        ymax = max(ymax, lat)

        xspan = xmax - xmin
        yspan = ymax - ymin

        # Handle degenerate spans (e.g. single point)
        if xspan == 0:
            xspan = 1e-6
        if yspan == 0:
            yspan = 1e-6

        # Apply buffer
        xpad = xspan * buffer_ratio
        ypad = yspan * buffer_ratio

        xmin -= xpad
        xmax += xpad
        ymin -= ypad
        ymax += ypad

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)


def plot_variable(df, admin_boundaries, column, classifier, colors, *,
                  country_name=None, plot_title=None, legend_title=None,
                  cities=None, legend_digits=0, x_limits=None, y_limits=None,
                  basemap_path=None, font_size=18, city_font_size=10,
                  legend_font_size=10, title_font_size=20, figsize=(10, 10),
                  region_alpha=0.7, epicenter=None):
    """
    Plot a classified geospatial variable with optional basemap
    and annotations.

    :param df: geopandas.GeoDataFrame
        Input data with geometry column.
    :param admin_boundaries: geopandas.GeoDataFrame
        Administrative boundaries to overlay.
    :param column: str
        Column to classify and plot.
    :param classifier: mapclassify classifier
        Fitted classifier (e.g. NaturalBreaks).
    :param colors: list[str]
        One color per class (length must at least the same as classifier.k).
    :param country_name: str, optional
        Used only for output naming or titles.
    :param plot_title: str, optional
        Figure title.
    :param legend_title: str, optional
        Legend title.
    :param cities: dict[str, tuple[float, float]], optional
        Mapping of city name -> (lon, lat).
    :param legend_digits: int
        Decimal digits for legend bin labels.
    :param x_limits, y_limits: tuple, optional
        Axis limits.
    :param basemap_path: Path or str, optional
        Raster basemap path.
    :param font_size: int or float
        Base font size for axis labels.
    :param city_font_size: int or float
        Font size for city name annotations.
    :param legend_font_size: int or float
        Font size for legend entries.
    :param title_font_size: int or float
        Font size for the main plot title.
    :param figsize: tuple(float, float)
        Width and height of the figure in inches.
    :param region_alpha: float
        Transparency of the classified region fill, between 0 (fully
        transparent) and 1 (fully opaque)
    :param epicenter: tuple(float, float), optional
        Coordinates (lon, lat) of the earthquake epicenter to be
        plotted as a yellow star.
    """
    plt = import_plt()
    import matplotlib.patheffects as path_effects
    import matplotlib.patches as mpatches
    if len(colors) > classifier.k:
        # The classifier may settle on fewer bins than the caller anticipated;
        # silently truncate the surplus colors to match.
        colors = colors[:classifier.k]
    elif len(colors) < classifier.k:
        raise ValueError(
            f"Not enough colors: got {len(colors)}, need {classifier.k}. "
            f"Please supply at least as many colors as classifier bins.")
    if df.crs != admin_boundaries.crs:
        raise ValueError("df and admin_boundaries CRS do not match")
    df = df.copy()
    df["class"] = classifier(df[column])

    # Prepare labels for the legend
    bins = numpy.round(classifier.bins, legend_digits)
    labels = [f"≤ {bins[0]:.{legend_digits}f}"]
    labels += [
        f"{bins[i-1]:.{legend_digits}f} – {bins[i]:.{legend_digits}f}"
        for i in range(1, len(bins))
    ]
    labels[-1] = f"> {bins[-2]:.{legend_digits}f}"
    if len(labels) != classifier.k:
        raise RuntimeError("Generated labels do not match number of classes")

    fig, ax = plt.subplots(figsize=figsize)

    if basemap_path is not None:
        try:
            import rasterio
        except ImportError as exc:
            raise RuntimeError(
                "In order to plot raster basemaps, 'rasterio' should be installed"
                ) from exc
        from rasterio.plot import show
        basemap_path = Path(basemap_path)
        with rasterio.open(basemap_path) as src:
            if src.crs != df.crs:
                raise ValueError("Raster CRS does not match vector CRS")
            show(src, ax=ax, alpha=0.8)

    # Plot each class with its corresponding color
    for i, color in enumerate(colors):
        subset = df[df["class"] == i]
        if not subset.empty:  # skip classes with no geometries
            subset.plot(ax=ax, color=color, edgecolor="none",
                        alpha=region_alpha)

    epicenter_handle = None
    if epicenter is not None:
        lon, lat = epicenter
        epicenter_handle = ax.scatter(
            lon, lat, marker='*', s=150, color='yellow',
            edgecolor='black', linewidth=1, zorder=10,
            label='Epicenter')

    # Create legend handles based on color and label
    handles = [mpatches.Patch(color=color, label=label)
               for color, label in zip(colors, labels)]
    if epicenter_handle is not None:
        handles.append(epicenter_handle)
    ax.legend(handles=handles, title=legend_title, framealpha=0.7,
              title_fontsize=font_size, fontsize=legend_font_size,
              loc="best")

    admin_boundaries.plot(ax=ax, alpha=0.4, edgecolor="black",
                          facecolor="none", linewidth=0.4)

    _resolve_limits(ax, x_limits, y_limits, epicenter)

    city_scatters = []
    if cities:
        try:
            from adjustText import adjust_text
        except ImportError:
            adjust_text = None
        texts = []
        for city, (x, y) in cities.items():
            # Plot the city dot
            sc = ax.scatter(x, y, color='black', marker='o', s=8, zorder=6)
            city_scatters.append(sc)
            # Create the text object (don't offset it yet)
            t = ax.text(x, y, city, fontsize=city_font_size,
                        color="black", fontweight="normal",
                        zorder=7)
            t.set_path_effects([
                path_effects.Stroke(linewidth=1.5, foreground="white"),
                path_effects.Normal()])
            texts.append(t)
        # Automatically resolve all collisions
        if adjust_text and texts:
            legend = ax.get_legend()
            adjust_text(texts, ax=ax,
                        add_objects=city_scatters + [legend],
                        arrowprops=None,  # disable arrows completely
                        force_text=(0.1, 0.2),
                        expand_points=(1.2, 1.2),
                        save_steps=False)

    if plot_title:
        ax.set_title(plot_title, fontsize=title_font_size)

    ax.set_xlabel("Longitude", fontsize=font_size)
    ax.set_ylabel("Latitude", fontsize=font_size)
    # Legend is placed inside the axes (loc="best"), so no right-side
    # reservation is needed.
    fig.tight_layout()
    return fig, ax
