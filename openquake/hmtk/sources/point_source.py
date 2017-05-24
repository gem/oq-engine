#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# LICENSE
#
# Copyright (c) 2010-2017, GEM Foundation, G. Weatherill, M. Pagani,
# D. Monelli.
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
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

# -*- coding: utf-8 -*-
'''
Module implements openquake.hmtk.sources.point_source.mtkPointSource class, which
represents the mtk implementation of the point source typology. This extends
the class nrml.models.PointSource
'''
import warnings
import numpy as np
from openquake.hazardlib.geo.point import Point
import openquake.hmtk.sources.source_conversion_utils as conv
from openquake.hazardlib.source.point import PointSource

class mtkPointSource(object):
    '''New class to describe the mtkPointsource object

    :param str identifier:
        ID code for the source
    :param str name:
        Source name
    :param str trt:
        Tectonic region type
    :param geometry:
        Instance of :class: nhlib.geo.point.Point class
    :param float upper_depth:
        Upper seismogenic depth (km)
    :param float lower_depth:
        Lower seismogenic depth (km)
    :param str mag_scale_rel:
        Magnitude scaling relationsip
    :param float rupt_aspect_ratio:
        Rupture aspect ratio
    :param mfd:
        Magnitude frequency distribution as instance of
        :class: openquake.hazardlib.mfd.BaseMFD
    :param list nodal_plane_dist:
        List of :class: openquake.hazardlib.geo.nodal_plane.NodalPlane
        objects representing nodal plane distribution
    :param list hypo_depth_dist:
        List of :class: nrml.models.HypocentralDepth instances describing
        the hypocentral depth distribution
    :param catalogue:
        Earthquake catalogue associated to source as instance of
        openquake.hmtk.seismicity.catalogue.Catalogue object
    '''

    def __init__(self, identifier, name, trt=None, geometry=None,
                 upper_depth=None, lower_depth=None, mag_scale_rel=None,
                 rupt_aspect_ratio=None, mfd=None, nodal_plane_dist=None,
                 hypo_depth_dist=None):
        '''
        Instantiates class with two essential attributes: identifier and name
        '''
        self.typology = 'Point'
        self.id = identifier
        self.name = name
        self.trt = trt
        self.geometry = geometry
        self.upper_depth = upper_depth
        self.lower_depth = lower_depth
        self.mag_scale_rel = mag_scale_rel
        self.rupt_aspect_ratio = rupt_aspect_ratio
        self.mfd = mfd
        self.nodal_plane_dist = nodal_plane_dist
        self.hypo_depth_dist = hypo_depth_dist
        # Check consistency of hypocentral depth inputs
        self._check_seismogenic_depths(upper_depth, lower_depth)
        self.catalogue = None

    def create_geometry(self, input_geometry, upper_depth, lower_depth):
        '''
        If geometry is defined as a numpy array then create instance of
        nhlib.geo.point.Point class, otherwise if already instance of class
        accept class

        :param input_geometry:
            Input geometry (point) as either
            i) instance of nhlib.geo.point.Point class
            ii) numpy.ndarray [Longitude, Latitude]

        :param float upper_depth:
            Upper seismogenic depth (km)

        :param float lower_depth:
            Lower seismogenic depth (km)
        '''
        self._check_seismogenic_depths(upper_depth, lower_depth)

        # Check/create the geometry class
        if not isinstance(input_geometry, Point):
            if not isinstance(input_geometry, np.ndarray):
                raise ValueError('Unrecognised or unsupported geometry '
                                 'definition')
            self.geometry = Point(input_geometry[0], input_geometry[1])
        else:
            self.geometry = input_geometry

    def _check_seismogenic_depths(self, upper_depth, lower_depth):
        '''
        Checks the seismic depths for physical consistency
        :param float upper_depth:
            Upper seismogenic depth (km)
        :param float lower_depth:
            Lower seismogenis depth (km)
        '''
        # Simple check on depths
        if upper_depth:
            if upper_depth < 0.:
                raise ValueError('Upper seismogenic depth must be greater than'
                                 ' or equal to 0.0!')
            else:
                self.upper_depth = upper_depth
        else:
            self.upper_depth = 0.0

        if lower_depth:
            if lower_depth < self.upper_depth:
                raise ValueError('Lower seismogenic depth must take a greater'
                                 ' value than upper seismogenic depth')
            else:
                self.lower_depth = lower_depth
        else:
            self.lower_depth = np.inf

    def select_catalogue(self, selector, distance, selector_type='circle',
                         distance_metric='epicentral', point_depth=None,
                         upper_eq_depth=None, lower_eq_depth=None):
        '''
        Selects the catalogue associated to the point source.
        Effectively a wrapper to the two functions select catalogue within
        a distance of the point and select catalogue within cell centred on
        point

        :param selector:
            Populated instance of :class:
            `openquake.hmtk.seismicity.selector.CatalogueSelector`
        :param float distance:
            Distance from point (km) for selection
        :param str selector_type:
            Chooses whether to select within {'circle'} or within a {'square'}.
        :param str distance_metric:
            'epicentral' or 'hypocentral' (only for 'circle' selector type)
        :param float point_depth:
            Assumed hypocentral depth of the point (only applied to 'circle'
            distance type)
        :param float upper_depth:
            Upper seismogenic depth (km) (only for 'square')
        :param float lower_depth:
            Lower seismogenic depth (km) (only for 'square')
        '''

        if selector.catalogue.get_number_events() < 1:
            raise ValueError('No events found in catalogue!')

        if 'square' in selector_type:
            # Calls select catalogue within cell function
            self.select_catalogue_within_cell(selector,
                                              distance,
                                              upper_depth=upper_eq_depth,
                                              lower_depth=lower_eq_depth)

        elif 'circle' in selector_type:
            # Calls select catalogue within distance function
            self.select_catalogue_within_distance(selector, distance,
                                                  distance_metric, point_depth)

        else:
            raise ValueError('Unrecognised selection type for point source!')

    def select_catalogue_within_distance(
            self, selector, distance,
            distance_metric='epicentral', point_depth=None):
        '''
        Selects catalogue of earthquakes within distance from point

        :param selector:
            Populated instance of :class:
            `openquake.hmtk.seismicity.selector.CatalogueSelector`
        :param distance:
            Distance from point (km) for selection
        :param str distance_metric:
            Choice of point source distance metric 'epicentral' or
            'hypocentral'
        '''
        if ('hypocentral' in distance_metric) and point_depth:
            # If a hypocentral distance metric is chosen and a
            # hypocentral depth specified then update geometry
            self.geometry = Point(self.geometry.longitude,
                                  self.geometry.latitude,
                                  point_depth)

        self.catalogue = selector.circular_distance_from_point(
            self.geometry,
            distance,
            distance_type=distance_metric)

        if self.catalogue.get_number_events() < 5:
            # Throw a warning regarding the small number of earthquakes in
            # the source!
            warnings.warn('Source %s (%s) has fewer than 5 events'
                          % (self.id, self.name))

    def select_catalogue_within_cell(self, selector, distance,
                                     upper_depth=None, lower_depth=None):
        '''
        Selects catalogue of earthquakes within distance from point

        :param selector:
            Populated instance of :class:
            `openquake.hmtk.seismicity.selector.CatalogueSelector`
        :param distance:
            Distance from point (km) for selection
        '''

        self.catalogue = selector.cartesian_square_centred_on_point(
            self.geometry, distance)

        if self.catalogue.get_number_events() < 5:
            # Throw a warning regarding the small number of earthquakes in
            # the source!
            warnings.warn('Source %s (%s) has fewer than 5 events'
                          % (self.id, self.name))

    def create_oqhazardlib_source(self, tom, mesh_spacing, use_defaults=False):
        """
        Converts the point source model into an instance of the :class:
        openquake.hazardlib.source.point_source.PointSource

        :param bool use_defaults:
            If set to true, will use put in default values for magitude
            scaling relation, rupture aspect ratio, nodal plane distribution
            or hypocentral depth distribution where missing. If set to False
            then value errors will be raised when information is missing.
        """
        if not self.mfd:
            raise ValueError("Cannot write to hazardlib without MFD")
        return PointSource(
            self.id,
            self.name,
            self.trt,
            self.mfd,
            mesh_spacing,
            conv.mag_scale_rel_to_hazardlib(self.mag_scale_rel, use_defaults),
            conv.render_aspect_ratio(self.rupt_aspect_ratio, use_defaults),
            tom,
            self.upper_depth,
            self.lower_depth,
            self.geometry,
            conv.npd_to_pmf(self.nodal_plane_dist, use_defaults),
            conv.hdd_to_pmf(self.hypo_depth_dist, use_defaults))
