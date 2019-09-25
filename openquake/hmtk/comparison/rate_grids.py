# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (C) 2015-2019 GEM Foundation, G. Weatherill, M. Pagani
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
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

"""
Python tools for calculating activity rates on a grid from a source model
"""
import numpy as np
from openquake.hazardlib.sourceconverter import SourceConverter
from openquake.hazardlib import nrml
from openquake.hazardlib.source.complex_fault import ComplexFaultSource
from openquake.hazardlib.source.characteristic import CharacteristicFaultSource
from openquake.hazardlib.source.simple_fault import SimpleFaultSource
from openquake.hazardlib.source.area import AreaSource
from openquake.hazardlib.source.point import PointSource
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.polygon import Polygon


class RateGrid(object):
    """
    Class for calculation of activity rate grids

    :param float xspc:
        Longitude spacing of grid
    :param float yspc:
        Latitude spacing of grid
    :param float zspc:
        Depth spacing (km) of grid
    :param np.ndarray xlim:
        Longitude cell bounds
    :param np.ndarray ylim:
        Latitude cell bounds
    :param np.ndarray zlim:
        Depth cell bounds
    :param int nx:
        Number of longitude cells
    :param int ny:
        Number of latitude cells
    :param int nz:
        Number of depth cells
    :param list source_model:
        Seismic source mode
    :param np.ndarray rates:
        Activity rates
    :param float area_discretisation:
        Discretisation step (km) of area sources
    """

    def __init__(self, limits, sources, area_discretisation=10.):
        """
        Instantiate class with grid configurations
        :param list limits:
             Grid configuration [west, east, xspc, south, north, yspc,
                                 upper, lower, zspc]
        """
        self.xspc = limits[2]
        self.yspc = limits[5]
        self.zspc = limits[8]
        self.xlim = np.arange(limits[0], limits[1] + self.xspc, self.xspc)
        self.ylim = np.arange(limits[3], limits[4] + self.yspc, self.yspc)
        self.zlim = np.arange(limits[6], limits[7] + self.zspc, self.zspc)
        self.nx = len(self.xlim)
        self.ny = len(self.ylim)
        self.nz = len(self.zlim)
        self.source_model = sources
        self.rates = np.zeros([self.nx - 1, self.ny - 1, self.nz - 1],
                              dtype=float)
        self.area_discretisation = area_discretisation

    @classmethod
    def from_model_files(cls, limits, input_model, investigation_time=1.0,
                         simple_mesh_spacing=1.0, complex_mesh_spacing=5.0,
                         mfd_width=0.1, area_discretisation=10.0):
        """
        Reads the hazard model from a file

        :param list limits:
             Grid configuration [west, east, xspc, south, north, yspc,
                                 upper, lower, zspc]
        :param str input_model:
            Path to input source model
        :param float investigation_time:
            Investigation time of Poisson model
        :param float simple_mesh_spacing:
            Rupture mesh spacing of simple fault (km)
        :param float complex_mesh_spacing:
            Rupture mesh spacing of complex fault (km)
        :param float mfd_width:
            Spacing (in magnitude units) of MFD
        :param float area_discretisation:
            Spacing of discretisation of area source (km)
        """
        converter = SourceConverter(investigation_time,
                                    simple_mesh_spacing,
                                    complex_mesh_spacing,
                                    mfd_width,
                                    area_discretisation)
        sources = []
        for grp in nrml.to_python(input_model, converter):
            sources.extend(grp.sources)
        return cls(limits, sources, area_discretisation)

    def number_sources(self):
        """
        Returns the number of sources
        """
        return len(self.source_model)

    def get_rates(self, mmin, mmax=np.inf):
        """
        Returns the cumulative rates greater than Mmin

        :param float mmin:
            Minimum magnitude
        """
        nsrcs = self.number_sources()
        for iloc, source in enumerate(self.source_model):
            print("Source Number %s of %s, Name = %s, Typology = %s" % (
                iloc + 1,
                nsrcs,
                source.name,
                source.__class__.__name__))
            if isinstance(source, CharacteristicFaultSource):
                self._get_fault_rates(source, mmin, mmax)
            elif isinstance(source, ComplexFaultSource):
                self._get_fault_rates(source, mmin, mmax)
            elif isinstance(source, SimpleFaultSource):
                self._get_fault_rates(source, mmin, mmax)
            elif isinstance(source, AreaSource):
                self._get_area_rates(source, mmin, mmax)
            elif isinstance(source, PointSource):
                self._get_point_rates(source, mmin, mmax)
            else:
                print("Source type %s not recognised - skipping!" % source)
                continue

    def _get_point_location(self, location):
        """
        Returns the location in the output grid corresponding to the cell in
        which the epicentre lays

        :param location:
            Source hypocentre as instance of :class:
            openquake.hazardlib.geo.point.Point
        :returns:
            xloc - Location of longitude cell
            yloc - Location of latitude cell
        """
        if (location.longitude < self.xlim[0]) or\
                (location.longitude > self.xlim[-1]):
            return None, None
        xloc = int(((location.longitude - self.xlim[0]) / self.xspc) + 1E-7)
        if (location.latitude < self.ylim[0]) or\
                (location.latitude > self.ylim[-1]):
            return None, None
        yloc = int(((location.latitude - self.ylim[0]) / self.yspc) + 1E-7)
        return xloc, yloc

    def _get_point_rates(self, source, mmin, mmax=np.inf):
        """
        Adds the rates for a point source

        :param source:
            Point source as instance of :class:
            openquake.hazardlib.source.point.PointSource
        :param float mmin:
            Minimum Magnitude
        :param float mmax:
            Maximum Magnitude
        """
        xloc, yloc = self._get_point_location(source.location)
        if (xloc is None) or (yloc is None):
            return
        # Get annual rates
        annual_rate = source.get_annual_occurrence_rates()
        mags = np.array([val[0] for val in annual_rate])
        annual_rate = np.array([val[1] for val in annual_rate])
        idx = np.logical_and(mags >= mmin, mags < mmax)
        annual_rate = np.sum(annual_rate[idx])
        for hypo_depth in source.hypocenter_distribution.data:
            zloc = int((hypo_depth[1] - self.zlim[0]) / self.zspc)
            if (zloc < 0) or (zloc >= (self.nz - 1)):
                continue
            else:
                self.rates[xloc, yloc, zloc] += float(hypo_depth[0]) * \
                    annual_rate

    def _get_area_rates(self, source, mmin, mmax=np.inf):
        """
        Adds the rates from the area source by discretising the source
        to a set of point sources

        :param source:
            Area source as instance of :class:
            openquake.hazardlib.source.area.AreaSource
        """
        points = list(source)
        for point in points:
            self._get_point_rates(point, mmin, mmax)

    def _get_fault_rates(self, source, mmin, mmax=np.inf):
        """
        Adds the rates for a simple or complex fault source

        :param source:
            Fault source as instance of :class:
            openquake.hazardlib.source.simple_fault.SimpleFaultSource or
            openquake.hazardlib.source.complex_fault.ComplexFaultSource
        """
        for rupt in list(source.iter_ruptures()):
            valid_rupt = (rupt.mag >= mmin) and (rupt.mag < mmax)
            if not valid_rupt:
                continue
            grd = np.column_stack([rupt.surface.mesh.lons.flatten(),
                                   rupt.surface.mesh.lats.flatten(),
                                   rupt.surface.mesh.depths.flatten()])
            npts = np.shape(grd)[0]
            counter = np.histogramdd(grd,
                                     bins=[self.xlim, self.ylim, self.zlim]
                                     )[0]
            point_rate = rupt.occurrence_rate / float(npts)
            self.rates += (point_rate * counter)


class RatePolygon(RateGrid):
    """
    Calculates the rate of events within a polygon

    :param limits:
        Polygon as instance of :class: openquake.hazardlib.geo.polygon.Polygon
    :param float upper_depth:
        Upper seismic depth of the polygon (km)
    :param float lower_depth:
        Lower seismic depth of the polygon (km)
    :param list source_model:
        List of seismic sources
    :param float rates:
        Activity rate of polygon
    :param float area_discretisation:
        Discretisation spacing (km) of the area source
    """

    def __init__(self, limits, sources, area_discretisation=10.):
        """
        Instantiate class with grid configurations
        :param dict limits:
             Configuration as dictionary containing:
             * polygon - OpenQuake Polygon
             * uppper_depth - upper seismogenic depth (km)
             * lower_depth - lower seismogenic depth (km)
        """
        assert isinstance(limits["polygon"], Polygon)
        self.limits = limits["polygon"]
        self.upper_depth = limits["upper_depth"]
        self.lower_depth = limits["lower_depth"]
        self.source_model = sources
        self.rates = 0.0
        self.area_discretisation = area_discretisation

    def _get_point_rates(self, source, mmin, mmax=np.inf):
        """
        Adds the rates for a point source

        :param source:
            Point source as instance of :class:
            openquake.hazardlib.source.point.PointSource
        :param float mmin:
            Minimum Magnitude
        :param float mmax:
            Maximum Magnitude
        """
        src_mesh = Mesh.from_points_list([source.location])
        in_poly = self.limits.intersects(src_mesh)[0]
        if not in_poly:
            return
        else:
            for (mag, rate) in source.get_annual_occurrence_rates():
                if (mag < mmin) or (mag > mmax):
                    return
                else:
                    for (prob, depth) in source.hypocenter_distribution.data:
                        if (depth < self.upper_depth) or\
                                (depth > self.lower_depth):
                            continue
                        else:
                            self.rates += (prob * rate)

    def _get_fault_rates(self, source, mmin, mmax=np.inf):
        """
        Adds the rates for a simple or complex fault source

        :param source:
            Fault source as instance of :class:
            openquake.hazardlib.source.simple_fault.SimpleFaultSource or
            openquake.hazardlib.source.complex_fault.ComplexFaultSource
        """
        for rup in list(source.iter_ruptures()):
            if (rup.mag < mmin) or (rup.mag > mmax):
                # Magnitude outside search range
                continue
            depths = rup.surface.mesh.depths.flatten()
            # Generate simple mesh from surface
            rupt_mesh = Mesh(rup.surface.mesh.lons.flatten(),
                             rup.surface.mesh.lats.flatten(),
                             depths)
            # Mesh points in polygon
            in_poly = self.limits.intersects(rupt_mesh)
            in_depth = np.logical_and(depths >= self.upper_depth,
                                      depths <= self.lower_depth)
            idx = np.logical_and(in_poly, in_depth)
            if np.any(idx):
                node_rate = rup.occurrence_rate / float(len(depths))
                self.rates += (node_rate * np.sum(idx))
