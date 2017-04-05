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
Defines the :class openquake.hmtk.sources.mtk_area_source.mtkAreaSource  which represents
the openquake.hmtk defition of an area source. This extends the :class:
nrml.models.AreaSource
'''
import warnings
import numpy as np
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.polygon import Polygon
from openquake.hazardlib.source.area import AreaSource
import openquake.hmtk.sources.source_conversion_utils as conv


class mtkAreaSource(object):
    '''
    Describes the Area Source

    :param str identifier:
        ID code for the source
    :param str name:
        Source name
    :param str trt:
        Tectonic region type
    :param geometry:
        Instance of :class: nhlib.geo.polygon.Polygon class
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
        :class: nrml.models.IncrementalMFD or
        :class: nrml.models.TGRMFD
    :param list nodal_plane_dist:
        List of :class: nrml.models.NodalPlane objects representing
        nodal plane distribution
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
        self.typology = 'Area'
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
        nhlib.geo.polygon.Polygon class, otherwise if already instance of class
        accept class

        :param input_geometry:
            Input geometry (polygon) as either
            i) instance of nhlib.geo.polygon.Polygon class
            ii) numpy.ndarray [Longitude, Latitude]

        :param float upper_depth:
            Upper seismogenic depth (km)

        :param float lower_depth:
            Lower seismogenic depth (km)
        '''
        self._check_seismogenic_depths(upper_depth, lower_depth)

        # Check/create the geometry class
        if not isinstance(input_geometry, Polygon):
            if not isinstance(input_geometry, np.ndarray):
                raise ValueError('Unrecognised or unsupported geometry '
                                 'definition')

            if np.shape(input_geometry)[0] < 3:
                raise ValueError('Incorrectly formatted polygon geometry -'
                                 ' needs three or more vertices')
            geometry = []
            for row in input_geometry:
                geometry.append(Point(row[0], row[1], self.upper_depth))
            self.geometry = Polygon(geometry)
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

    def select_catalogue(self, selector, distance=None):
        '''
        Selects the catalogue of earthquakes attributable to the source

        :param selector:
            Populated instance of openquake.hmtk.seismicity.selector.CatalogueSelector
            class
        :param float distance:
            Distance (in km) to extend or contract (if negative) the zone for
            selecting events
        '''
        if selector.catalogue.get_number_events() < 1:
            raise ValueError('No events found in catalogue!')

        self.catalogue = selector.within_polygon(self.geometry,
                                                 distance,
                                                 upper_depth=self.upper_depth,
                                                 lower_depth=self.lower_depth)
        if self.catalogue.get_number_events() < 5:
            # Throw a warning regarding the small number of earthquakes in
            # the source!
            warnings.warn('Source %s (%s) has fewer than 5 events'
                          % (self.id, self.name))

    def create_oqhazardlib_source(self, tom, mesh_spacing, area_discretisation,
                                  use_defaults=False):
        """
        Converts the source model into an instance of the :class:
        openquake.hazardlib.source.area.AreaSource
        
        :param tom:
            Temporal Occurrence model as instance of :class:
            openquake.hazardlib.tom.TOM
        :param float mesh_spacing:
            Mesh spacing
        """
        if not self.mfd:
            raise ValueError("Cannot write to hazardlib without MFD")
        return AreaSource(
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
            conv.npd_to_pmf(self.nodal_plane_dist, use_defaults),
            conv.hdd_to_pmf(self.hypo_depth_dist, use_defaults),
            self.geometry,
            area_discretisation)

