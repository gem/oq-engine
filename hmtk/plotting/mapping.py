# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (c) 2010-2014, GEM Foundation, G. Weatherill, M. Pagani, 
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
# The software Hazard Modeller's Toolkit (hmtk) provided herein 
# is released as a prototype implementation on behalf of 
# scientists and engineers working within the GEM Foundation (Global 
# Earthquake Model). 
#
# It is distributed for the purpose of open collaboration and in the 
# hope that it will be useful to the scientific, engineering, disaster
# risk and software design communities. 
# 
# The software is NOT distributed as part of GEM's OpenQuake suite 
# (http://www.globalquakemodel.org/openquake) and must be considered as a 
# separate entity. The software provided herein is designed and implemented 
# by scientific staff. It is not developed to the design standards, nor 
# subject to same level of critical review by professional software 
# developers, as GEM's OpenQuake software suite.  
# 
# Feedback and contribution to the software is welcome, and can be 
# directed to the hazard scientific staff of the GEM Model Facility 
# (hazard@globalquakemodel.org). 
# 
# The Hazard Modeller's Toolkit (hmtk) is therefore distributed WITHOUT 
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or 
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License 
# for more details.
# 
# The GEM Foundation, and the authors of the software, assume no 
# liability for use of the software. 

#!/usr/bin/env/python

'''
Module hmtk.plotting.catalogue.map is a graphical
function for plotting the spatial distribution of events
'''
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from matplotlib.colors import LogNorm, Normalize
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.line import Line
from openquake.hazardlib.geo.polygon import Polygon
from hmtk.sources.area_source import mtkAreaSource
from hmtk.sources.point_source import mtkPointSource
from hmtk.sources.simple_fault_source import mtkSimpleFaultSource

DEFAULT_SYMBOLOGY = [(-np.inf, 1., 'k.'), # M < 1
                     (1., 2., 'g*'), # 1 < M < 2
                     (2., 3.,'cx'), # 2 < M < 3
                     (3., 4.,'yd'), # 3 < M < 4
                     (4., 5.,'m^'), # 4 < M < 5
                     (5., 6.,'go'), # 5 < M < 6
                     (6., 7.,'yh'), # 6 < M < 7
                     (7., 8.,'bs'), # 7 < M < 8
                     (8., 9.,'k^'), # 8 < M < 9
                     (9., np.inf,'ro')] # 9 < M < 10

LEGEND_OFFSET=(1.3, 1.0)
PORTRAIT_ASPECT = (6, 8)
LANDSCAPE_ASPECT = (8, 6)

def _fault_polygon_from_mesh(source):
    """

    """
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
    imported from hmtk.
    '''
    def __init__(self, config, title, dpi=300):
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
        self.fig = None
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
        if not 'resolution' in self.config.keys():
            self.config['resolution'] = 'l'

        lat0 = lowcrnrlat + ((uppcrnrlat - lowcrnrlat) / 2)
        lon0 = lowcrnrlon + ((uppcrnrlon - lowcrnrlon) / 2)
        if (uppcrnrlat - lowcrnrlat) >= (uppcrnrlon - lowcrnrlon):
            fig_aspect = PORTRAIT_ASPECT
        else:
            fig_aspect = LANDSCAPE_ASPECT
        self.fig = plt.figure(num=None,
                              figsize=fig_aspect,
                              dpi=self.dpi,
                              facecolor='w',
                              edgecolor='k')
        if self.title:
            plt.title(self.title, fontsize=16)
        parallels = np.arange(0., 90., 2.)
        meridians = np.arange(0., 360., 2.)

        # Build Map
        self.m = Basemap(
            llcrnrlon=lowcrnrlon, llcrnrlat=lowcrnrlat,
            urcrnrlon=uppcrnrlon, urcrnrlat=uppcrnrlat,
            projection='stere', resolution=self.config['resolution'],
            area_thresh=1000.0, lat_0=lat0, lon_0=lon0)
        self.m.drawcountries()
        self.m.drawmapboundary()
        self.m.drawcoastlines()
        self.m.drawstates()
        self.m.drawparallels(parallels, labels=[1, 0, 0, 0], fontsize=12)
        self.m.drawmeridians(meridians, labels=[0, 0, 0, 1], fontsize=12)
        self.m.fillcontinents(color='wheat')

    def savemap(self, filename, filetype='png', papertype=None):
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
            :class: hmtk.seismicity.catalogue.Catalogue

        :param dict config:
            Configuration parameters of the algorithm, containing the
            following information -
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
        #min_mag = np.min(catalogue.data['magnitude'])
        #max_mag = np.max(catalogue.data['magnitude'])
        min_loc = np.where(np.array([symb[0] for symb in DEFAULT_SYMBOLOGY]) <
                           np.min(catalogue.data['magnitude']))[0][-1]
        max_loc = np.where(np.array([symb[1] for symb in DEFAULT_SYMBOLOGY]) >
                           np.max(catalogue.data['magnitude']))[0][1]
        symbology = DEFAULT_SYMBOLOGY[min_loc:max_loc]
        legend_list = []
        leg_handles = []
        for sym in symbology:
            # Create legend string
            if np.isinf(sym[0]):
                leg_str = 'M < %5.2f' % sym[1]
            elif np.isinf(sym[1]):
                leg_str = 'M >= %5.2f' % sym[0]
            else:
                leg_str = '%5.2f <= M < %5.2f' %(sym[0], sym[1])
            idx = np.logical_and(catalogue.data['magnitude'] >= sym[0],
                                 catalogue.data['magnitude'] < sym[1])
            mag_size = 1.2 * np.min([sym[0] + 0.5, sym[1] - 0.5])
            x, y = self.m(catalogue.data['longitude'][idx],
                           catalogue.data['latitude'][idx])
            self.m.plot(x, y, sym[2], markersize=mag_size, label=leg_str)

        plt.legend(bbox_to_anchor=LEGEND_OFFSET)
        if self.title:
            plt.title(self.title, fontsize=16)
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
        x, y = self.m(source.geometry.lons, source.geometry.lats)
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

    def add_source_model(self, model, area_border='k-', border_width=1.0,
            point_marker='ks', point_size=2.0, overlay=False):
        """
        Adds a source model to the map
        :param model:
            Source model of mixed typologies as instance of :class:
            hmtk.sources.source_model.mtkSourceModel
        """
        for source in model.sources:
            if isinstance(source, mtkAreaSource):
                self._plot_area_source(source, area_border, border_width)
            elif isinstance(source, mtkPointSource):
                self._plot_point_source(source, point_marker, point_size)
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
        :param bool logplot:
            Scales the data logarithmically if True
        :param float alpha:
            Sets the transparency of the marker (0 for transparent, 1 opaque)
        :param float vmin:
            Minimum data value of the colour scale
        :param float vmax:
            Maximum data value of the colour scale
        """
        if not norm:
            norm = Normalize(vmin=np.min(data), vmax=np.max(data))
        x, y, = self.m(longitude, latitude)
        self.m.scatter(x, y,
                       marker=shape,
                       s=size,
                       c=data,
                       norm=norm,
                       alpha=alpha,
                       linewidths=0.0,
                       zorder=4)
        self.m.colorbar()
        if not overlay:
            plt.show()

    def add_size_scaled_points(self, longitude, latitude, data, shape='o',
            logplot=False, alpha=1.0, colour='b', smin=2.0, sscale=2.0, 
            overlay=False):
        """
        Plots a set of points with size scaled according to the data
        """
        if logplot:
            data = np.log10(data.copy())
        #if not vmin:
        #    vmin = np.min(data)
        #if not vmax:
        #    vmax = np.max(data)
        #data = (data - vmin) / (vmax - vmin)
        #data[data > 1.0] = 1.0
        #data[data < 0.0] = 0.0

        x, y, = self.m(longitude, latitude)
        self.m.scatter(x, y,
                       marker=shape,
                       s=(smin + data ** sscale),
                       c=colour,
                       alpha=alpha,
                       zorder=4)
        if not overlay:
            plt.show()
