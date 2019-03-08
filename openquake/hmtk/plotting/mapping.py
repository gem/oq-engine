# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (C) 2010-2019 GEM Foundation, G. Weatherill, M. Pagani,
# D. Monelli., L. E. Rodriguez-Abreu
#
# The Hazard Modeller's Toolkit is free software: you can redistribute
# it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
# DISCLAIMER
#
# The software Hazard Modeller's Toolkit (openquake.hmtk) provided herein
# is released as a prototype implementation on behalf of
# scientists and engineers working within the GEM Foundation (Global
# Earthquake Model).
#
# It is distributed for the purpose of open collaboration and in the
# hope that it will be useful to the scientific, engineering, disaster
# risk and software design communities.
#
# The software is NOT distributed as part of GEM's OpenQuake suite
# (https://www.globalquakemodel.org/tools-products) and must be considered as a
# separate entity. The software provided herein is designed and implemented
# by scientific staff. It is not developed to the design standards, nor
# subject to same level of critical review by professional software
# developers, as GEM's OpenQuake software suite.
#
# Feedback and contribution to the software is welcome, and can be
# directed to the hazard scientific staff of the GEM Model Facility
# (hazard@globalquakemodel.org).
#
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

'''
Module openquake.hmtk.plotting.catalogue.map is a graphical
function for plotting the spatial distribution of events
'''
from builtins import range
import collections
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from openquake.hmtk.sources.area_source import mtkAreaSource
from openquake.hmtk.sources.point_source import mtkPointSource
from openquake.hmtk.plotting.beachball import Beach
from openquake.hmtk.plotting.plotting_utils import DISSIMILAR_COLOURLIST
from openquake.hmtk.sources.simple_fault_source import mtkSimpleFaultSource
from openquake.hmtk.sources.complex_fault_source import mtkComplexFaultSource


DEFAULT_SYMBOLOGY = [(-np.inf, 1., 'k.'),  # M < 1
                     (1., 2., 'g*'),  # 1 < M < 2
                     (2., 3., 'cx'),  # 2 < M < 3
                     (3., 4., 'yd'),  # 3 < M < 4
                     (4., 5., 'm^'),  # 4 < M < 5
                     (5., 6., 'go'),  # 5 < M < 6
                     (6., 7., 'yh'),  # 6 < M < 7
                     (7., 8., 'bs'),  # 7 < M < 8
                     (8., 9., 'k^'),  # 8 < M < 9
                     (9., np.inf, 'ro')]  # 9 < M < 10

LEGEND_OFFSET = (1.3, 1.0)
PORTRAIT_ASPECT = (6, 8)
LANDSCAPE_ASPECT = (8, 6)
NCOLS = len(DISSIMILAR_COLOURLIST)


def _fault_polygon_from_mesh(source):
    # Mesh
    upper_edge = np.column_stack([source.geometry.mesh.lons[1],
                                  source.geometry.mesh.lats[1],
                                  source.geometry.mesh.depths[1]])
    lower_edge = np.column_stack([source.geometry.mesh.lons[-1],
                                  source.geometry.mesh.lats[-1],
                                  source.geometry.mesh.depths[-1]])
    return np.vstack([upper_edge, np.flipud(lower_edge), upper_edge[0, :]])


class HMTKBaseMap(object):
    '''
    Class to plot the spatial distribution of events based in the Catalogue
    imported from openquake.hmtk.
    '''

    def __init__(self, config,
                 title=None, dpi=300, ax=None, lat_lon_spacing=2.):
        """
        :param dict config:
            Configuration parameters of the algorithm, containing the
            following information -
                'min_lat' Minimum value of latitude (in degrees, float)
                'max_lat' Minimum value of longitude (in degrees, float)
                (min_lat, min_lon) Defines the inferior corner of the map

                'min_lon' Maximum value of latitude (in degrees, float)
                'max_lon' Maximum value of longitude (in degrees, float)
                (min_lon, max_lon) Defines the upper corner of the map
        :param str title:
            Title string
        """
        self.config = config
        self.title = title
        self.dpi = dpi
        self.lat_lon_spacing = lat_lon_spacing
        self.fig = None
        self.ax = ax
        self.m = None
        self._build_basemap()

    def _build_basemap(self):
        '''
        Creates the map according to the input configuration
        '''
        if self.config['min_lon'] >= self.config['max_lon']:
            raise ValueError('Upper limit of long is smaller than lower limit')

        if self.config['min_lon'] >= self.config['max_lon']:
            raise ValueError('Upper limit of long is smaller than lower limit')
        # Corners of the map
        lowcrnrlat = self.config['min_lat']
        lowcrnrlon = self.config['min_lon']
        uppcrnrlat = self.config['max_lat']
        uppcrnrlon = self.config['max_lon']
        if 'resolution' not in self.config.keys():
            self.config['resolution'] = 'l'

        lat0 = lowcrnrlat + ((uppcrnrlat - lowcrnrlat) / 2)
        lon0 = lowcrnrlon + ((uppcrnrlon - lowcrnrlon) / 2)
        if (uppcrnrlat - lowcrnrlat) >= (uppcrnrlon - lowcrnrlon):
            fig_aspect = PORTRAIT_ASPECT
        else:
            fig_aspect = LANDSCAPE_ASPECT

        if self.ax is None:
            self.fig, self.ax = plt.subplots(figsize=fig_aspect,
                                             facecolor='w',
                                             edgecolor='k')
        else:
            self.fig = self.ax.get_figure()

        if self.title:
            self.ax.set_title(self.title, fontsize=16)
        parallels = np.arange(-90., 90., self.lat_lon_spacing)
        meridians = np.arange(0., 360., self.lat_lon_spacing)

        # Build Map
        # Do not import Basemap at top level since it's an optional feature
        # and it would break doctests
        from mpl_toolkits.basemap import Basemap
        self.m = Basemap(
            llcrnrlon=lowcrnrlon, llcrnrlat=lowcrnrlat,
            urcrnrlon=uppcrnrlon, urcrnrlat=uppcrnrlat,
            projection='stere', resolution=self.config['resolution'],
            area_thresh=1000.0, lat_0=lat0, lon_0=lon0, ax=self.ax)
        self.m.drawcountries()
        self.m.drawmapboundary()
        self.m.drawcoastlines()
        self.m.drawstates()
        self.m.drawparallels(parallels, labels=[1, 0, 0, 0], fontsize=12)
        self.m.drawmeridians(meridians, labels=[0, 0, 0, 1], fontsize=12)
        self.m.fillcontinents(color='wheat')

    def savemap(self, filename, filetype='png', papertype="a4"):
        """
        Save the figure
        """
        self.fig.savefig(filename,
                         dpi=self.dpi,
                         format=filetype,
                         papertype=papertype)

    def add_catalogue(self, catalogue, overlay=False):
        '''
        :param catalogue:
            Earthquake catalogue as instance of
            :class:`openquake.hmtk.seismicity.catalogue.Catalogue`

        :param dict config:
            Configuration parameters of the algorithm, containing the
            following information:
            'min_lat' Minimum value of latitude (in degrees, float)
            'max_lat' Minimum value of longitude (in degrees, float)
            (min_lat, min_lon) Defines the inferior corner of the map
            'min_lon' Maximum value of latitude (in degrees, float)
            'max_lon' Maximum value of longitude (in degrees, float)
            (min_lon, max_lon) Defines the upper corner of the map

        :returns:
            Figure with the spatial distribution of the events.
        '''
        # Magnitudes bins and minimum marrker size
        # min_mag = np.min(catalogue.data['magnitude'])
        # max_mag = np.max(catalogue.data['magnitude'])
        con_min = np.where(np.array([symb[0] for symb in DEFAULT_SYMBOLOGY]) <
                           np.min(catalogue.data['magnitude']))[0]
        con_max = np.where(np.array([symb[1] for symb in DEFAULT_SYMBOLOGY]) >
                           np.max(catalogue.data['magnitude']))[0]
        if len(con_min) == 1:
            min_loc = con_min[0]
        else:
            min_loc = con_min[-1]
        if len(con_max) == 1:
            max_loc = con_max[0]
        else:
            max_loc = con_max[1]
        # min_loc = np.where(np.array([symb[0] for symb in DEFAULT_SYMBOLOGY])
        #                   < np.min(catalogue.data['magnitude']))[0][-1]
        # max_loc = np.where(np.array([symb[1] for symb in DEFAULT_SYMBOLOGY])
        #                   > np.max(catalogue.data['magnitude']))[0][1]
        symbology = DEFAULT_SYMBOLOGY[min_loc:max_loc]
        for sym in symbology:
            # Create legend string
            if np.isinf(sym[0]):
                leg_str = 'M < %5.2f' % sym[1]
            elif np.isinf(sym[1]):
                leg_str = 'M >= %5.2f' % sym[0]
            else:
                leg_str = '%5.2f <= M < %5.2f' % (sym[0], sym[1])
            idx = np.logical_and(catalogue.data['magnitude'] >= sym[0],
                                 catalogue.data['magnitude'] < sym[1])
            mag_size = 1.2 * np.min([sym[0] + 0.5, sym[1] - 0.5])
            x, y = self.m(catalogue.data['longitude'][idx],
                          catalogue.data['latitude'][idx])
            self.m.plot(x, y, sym[2], markersize=mag_size, label=leg_str)

        self.ax.legend(bbox_to_anchor=LEGEND_OFFSET)
        if self.title:
            self.ax.set_title(self.title, fontsize=16)
        if not overlay:
            plt.show()

    def _plot_area_source(self, source, border='k-', border_width=1.0):
        """
        Plots the area source
        :param source:
            Area source as instance of :class: mtkAreaSource
        :param str border:
            Line properties of border (see matplotlib documentation for detail)
        :param float border_width:
            Line width of border (see matplotlib documentation for detail)
        """
        lons = np.hstack([source.geometry.lons, source.geometry.lons[0]])
        lats = np.hstack([source.geometry.lats, source.geometry.lats[0]])
        x, y = self.m(lons, lats)
        self.m.plot(x, y, border, linewidth=border_width)

    def _plot_point_source(self, source, point_marker='ks', point_size=2.0):
        """
        Plots the area source
        :param source:
            Area source as instance of :class: mtkPointSource
        :param str point_marker:
            Marker style for point (see matplotlib documentation for detail)
        :param float marker size for point:
            Line width of border (see matplotlib documentation for detail)
        """
        x, y = self.m(source.geometry.longitude, source.geometry.latitude)
        self.m.plot(x, y, point_marker, markersize=point_size)

    def _plot_simple_fault(self, source, border='k-', border_width=1.0):
        """
        Plots the simple fault source as a composite of the fault trace
        and the surface projection of the fault.
        :param source:
            Fault source as instance of :class: mtkSimpleFaultSource
        :param str border:
            Line properties of border (see matplotlib documentation for detail)
        :param float border_width:
            Line width of border (see matplotlib documentation for detail)
        """
        # Get the trace
        trace_lons = np.array([pnt.longitude
                               for pnt in source.fault_trace.points])
        trace_lats = np.array([pnt.latitude
                               for pnt in source.fault_trace.points])
        surface_projection = _fault_polygon_from_mesh(source)
        # Plot surface projection first
        x, y = self.m(surface_projection[:, 0], surface_projection[:, 1])
        self.m.plot(x, y, border, linewidth=border_width)
        # Plot fault trace
        x, y = self.m(trace_lons, trace_lats)
        self.m.plot(x, y, border, linewidth=1.3 * border_width)

    def _plot_complex_fault(self, source, border='k-', border_width=1.0,
                            min_depth=0., max_depth=None, alpha=1.0):
        """
        Plots the simple fault source as a composite of the fault trace
        and the surface projection of the fault.
        :param source:
            Fault source as instance of :class: mtkSimpleFaultSource
        :param str border:
            Line properties of border (see matplotlib documentation for detail)
        :param float border_width:
            Line width of border (see matplotlib documentation for detail)
        """
        if not max_depth:
            max_depth = 70.
        # Get outline
        top_edge = np.column_stack([source.geometry.mesh.lons[0],
                                    source.geometry.mesh.lats[0]])

        bottom_edge = np.column_stack([source.geometry.mesh.lons[-1][::-1],
                                       source.geometry.mesh.lats[-1][::-1]])
        outline = np.vstack([top_edge, bottom_edge, top_edge[0, :]])
        lons = source.geometry.mesh.lons.flatten()
        lats = source.geometry.mesh.lats.flatten()
        depths = source.geometry.mesh.depths.flatten()
        norm = Normalize(vmin=min_depth, vmax=max_depth)
        x1, y1 = self.m(lons, lats)
        self.m.scatter(x1, y1,
                       marker=".",
                       s=20,
                       c=depths,
                       norm=norm,
                       cmap="jet_r",
                       alpha=alpha,
                       linewidths=0.0,
                       zorder=4)
        # Plot border
        x2, y2 = self.m(outline[:, 0], outline[:, 1])
        self.m.plot(x2, y2, border, linewidth=border_width)

    def add_source_model(
            self, model, area_border='k-', border_width=1.0,
            point_marker='ks', point_size=2.0, overlay=False, min_depth=0.,
            max_depth=None, alpha=1.0):
        """
        Adds a source model to the map

        :param model:
            Source model of mixed typologies as instance of :class:
            openquake.hmtk.sources.source_model.mtkSourceModel
        """
        for source in model.sources:
            if isinstance(source, mtkAreaSource):
                self._plot_area_source(source, area_border, border_width)
            elif isinstance(source, mtkPointSource):
                self._plot_point_source(source, point_marker, point_size)
            elif isinstance(source, mtkComplexFaultSource):
                self._plot_complex_fault(source, area_border, border_width,
                                         min_depth, max_depth, alpha)
            elif isinstance(source, mtkSimpleFaultSource):
                self._plot_simple_fault(source, area_border, border_width)
            else:
                pass
        if not overlay:
            plt.show()

    def add_colour_scaled_points(self, longitude, latitude, data, shape='s',
                                 alpha=1.0, size=20, norm=None, overlay=False):
        """
        Overlays a set of points on a map with a fixed size but colour scaled
        according to the data

        :param np.ndarray longitude:
            Longitude
        :param np.ndarray latitude:
            Latitude
        :param np.ndarray data:
            Data for plotting
        :param str shape:
            Marker style
        :param float alpha:
            Sets the transparency of the marker (0 for transparent, 1 opaque)
        :param int size:
            Marker size
        :param norm:
            Normalisation as instance of :class: matplotlib.colors.Normalize
        """
        if not norm:
            norm = Normalize(vmin=np.min(data), vmax=np.max(data))
        x, y, = self.m(longitude, latitude)
        mappable = self.m.scatter(x, y,
                                  marker=shape,
                                  s=size,
                                  c=data,
                                  norm=norm,
                                  alpha=alpha,
                                  linewidths=0.0,
                                  zorder=4)
        self.m.colorbar(mappable=mappable, fig=self.fig, ax=self.ax)
        if not overlay:
            plt.show()

    def add_size_scaled_points(
            self, longitude, latitude, data, shape='o',
            logplot=False, alpha=1.0, colour='b', smin=2.0, sscale=2.0,
            overlay=False):
        """
        Plots a set of points with size scaled according to the data

        :param bool logplot:
            Choose to scale according to the logarithm (base 10) of the data
        :param float smin:
            Minimum scale size
        :param float sscale:
            Scaling factor
        """
        if logplot:
            data = np.log10(data.copy())

        x, y, = self.m(longitude, latitude)
        self.m.scatter(x, y,
                       marker=shape,
                       s=(smin + data ** sscale),
                       c=colour,
                       alpha=alpha,
                       zorder=2)
        if not overlay:
            plt.show()

    def _select_color_mag(self, mag):
        if (mag > 8.0):
            color = 'k'
            # color.append('k')
        elif (mag < 8.0) and (mag >= 7.0):
            color = 'b'
            # color.append('b')
        elif (mag < 7.0) and (mag >= 6.0):
            color = 'y'
            # color.append('y')
        elif (mag < 6.0) and (mag >= 5.0):
            color = 'g'
            # color.append('g')
        elif (mag < 5.0):
            color = 'm'
            # color.append('m')
        return color

    def add_focal_mechanism(self, catalogue, magnitude=None, overlay=True):
        """
        Plots a the the focal mechanism based on the beachball representation.
        The focal_menchanism flag must contain: strike, dip, rake.
        """
        longitude = catalogue.data['longitude']
        latitude = catalogue.data['latitude']
        strike = catalogue.data['strike1']
        dip = catalogue.data['dip1']
        rake = catalogue.data['rake1']

        if not magnitude or (magnitude < 0):
            magnitude = catalogue.data['magnitude']
            for i, mag in enumerate(magnitude):
                color = self._select_color_mag(mag)
                focal_mechanism = [strike[i], dip[i], rake[i]]
                x, y = self.m(longitude[i], latitude[i])
                self.m.plot(x, y)
                size = mag * 10000
                beach = Beach(focal_mechanism, linewidth=1, xy=(x, y),
                              width=size, zorder=size, facecolor=color)
                self.ax.add_collection(beach)
                if not overlay:
                    plt.show()
        else:
            for i in range(0, catalogue.get_number_tensors()):
                x, y = self.m(longitude[i], latitude[i])
                self.m.plot(x, y)
                focal_mechanism = [strike[i], dip[i], rake[i]]
                size = magnitude * 10000.
                beach = Beach(focal_mechanism, linewidth=1, xy=(x, y),
                              width=size, zorder=size, facecolor='r')
                self.ax.add_collection(beach)
                if not overlay:
                    plt.show()

    def add_catalogue_cluster(self, catalogue, vcl, flagvector,
                              cluster_id=None, overlay=True):
        """
        Creates a plot of a catalogue showing where particular clusters exist
        """
        # Create simple magnitude scaled point basemap
        self.add_size_scaled_points(catalogue.data['longitude'],
                                    catalogue.data['latitude'],
                                    catalogue.data['magnitude'],
                                    shape="o",
                                    alpha=0.8,
                                    colour=(0.5, 0.5, 0.5),
                                    smin=1.0,
                                    sscale=1.5,
                                    overlay=True)
        # If cluster ID is not specified just show mainshocks
        if cluster_id is None:
            idx = flagvector == 0
            self.add_size_scaled_points(catalogue.data['longitude'][idx],
                                        catalogue.data['latitude'][idx],
                                        catalogue.data['magnitude'][idx],
                                        shape="o",
                                        colour="r",
                                        smin=1.0,
                                        sscale=1.5,
                                        overlay=overlay)
            return
        if not isinstance(cluster_id, collections.Iterable):
            cluster_id = [cluster_id]
        for iloc, clid in enumerate(cluster_id):
            if iloc == (len(cluster_id) - 1):
                # On last iteration set overlay to function overlay
                temp_overlay = overlay
            else:
                temp_overlay = True
            idx = vcl == clid
            self.add_size_scaled_points(
                catalogue.data["longitude"][idx],
                catalogue.data["latitude"][idx],
                catalogue.data["magnitude"][idx],
                shape="o",
                colour=DISSIMILAR_COLOURLIST[(iloc + 1) % NCOLS],
                smin=1.0,
                sscale=1.5,
                overlay=temp_overlay)
