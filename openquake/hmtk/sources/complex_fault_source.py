# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# LICENSE
#
# Copyright (C) 2010-2025 GEM Foundation, G. Weatherill, M. Pagani,
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

"""
Defines the :class:
`openquake.hmtk.sources.complex_fault_source.mtkComplexFaultSource`, which
represents the openquake.hmtk defition of a complex fault source. This extends
the :class:`nrml.models.ComplexFaultSource`
"""
import warnings
import numpy as np
from math import fabs
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.line import Line
from openquake.hazardlib.geo.surface.complex_fault import ComplexFaultSurface
from openquake.hazardlib.source.complex_fault import ComplexFaultSource
import openquake.hmtk.sources.source_conversion_utils as conv


class mtkComplexFaultSource(object):
    """
    New class to describe the mtk complex fault source object

    :param str identifier:
        ID code for the source
    :param str name:
        Source name
    :param str trt:
        Tectonic region type
    :param geometry:
        Instance of :class: nhlib.geo.surface.complex_fault.ComplexFaultSource
    :param str mag_scale_rel:
        Magnitude scaling relationsip
    :param float rupt_aspect_ratio:
        Rupture aspect ratio
    :param mfd:
        Magnitude frequency distribution as instance of
        :class:`nrml.models.IncrementalMFD` or
        :class:`nrml.models.TGRMFD`
    :param float rake:
        Rake of fault
    :param float upper_depth:
        Upper seismogenic depth (km)
    :param float lower_depth:
        Lower seismogenic depth (km)
    :param catalogue:
        Earthquake catalogue associated to source as instance of
        :class:`openquake.hmtk.seismicity.catalogue.Catalogue` object
    """

    def __init__(
        self,
        identifier,
        name,
        trt=None,
        geometry=None,
        mag_scale_rel=None,
        rupt_aspect_ratio=None,
        mfd=None,
        rake=None,
    ):
        """
        Instantiate class with just the basic attributes: identifier and name
        """
        self.typology = "ComplexFault"
        self.id = identifier
        self.name = name
        self.trt = trt
        self.geometry = geometry
        self.fault_edges = None
        self.mag_scale_rel = mag_scale_rel
        self.rupt_aspect_ratio = rupt_aspect_ratio
        self.mfd = mfd
        self.rake = rake
        self.upper_depth = None
        self.lower_depth = None
        self.catalogue = None
        self.dip = None

    def create_geometry(self, input_geometry, mesh_spacing=1.0):
        """
        If geometry is defined as a numpy array then create instance of
        nhlib.geo.line.Line class, otherwise if already instance of class
        accept class

        :param input_geometry:
            List of at least two fault edges of the fault source from
            shallowest to deepest. Each edge can be represented as as either
            i) instance of nhlib.geo.polygon.Polygon class
            ii) numpy.ndarray [Longitude, Latitude, Depth]

        :param float mesh_spacing:
            Spacing of the fault mesh (km) {default = 1.0}

        """
        if not isinstance(input_geometry, list) or len(input_geometry) < 2:
            raise ValueError("Complex fault geometry incorrectly defined")

        self.fault_edges = []
        for edge in input_geometry:
            if not isinstance(edge, Line):
                if not isinstance(edge, np.ndarray):
                    raise ValueError(
                        "Unrecognised or unsupported geometry " "definition"
                    )
                else:
                    self.fault_edges.append(
                        Line([Point(row[0], row[1], row[2]) for row in edge])
                    )
            else:
                self.fault_edges.append(edge)
            # Updates the upper and lower sesmogenic depths to reflect geometry
            self._get_minmax_edges(edge)
        # Build fault surface
        self.geometry = ComplexFaultSurface.from_fault_data(
            self.fault_edges, mesh_spacing
        )
        # Get a mean dip
        self.dip = self.geometry.get_dip()

    def _get_minmax_edges(self, edge):
        """
        Updates the upper and lower depths based on the input edges
        """
        if isinstance(edge, Line):
            # For instance of line class need to loop over values
            depth_vals = np.array([node.depth for node in edge.points])
        else:
            depth_vals = edge[:, 2]

        temp_upper_depth = np.min(depth_vals)
        if not self.upper_depth:
            self.upper_depth = temp_upper_depth
        else:
            if temp_upper_depth < self.upper_depth:
                self.upper_depth = temp_upper_depth

        temp_lower_depth = np.max(depth_vals)
        if not self.lower_depth:
            self.lower_depth = temp_lower_depth
        else:
            if temp_lower_depth > self.lower_depth:
                self.lower_depth = temp_lower_depth

    def select_catalogue(
        self,
        selector,
        distance,
        distance_metric="joyner-boore",
        upper_eq_depth=None,
        lower_eq_depth=None,
    ):
        """
        Selects earthquakes within a distance of the fault

        :param selector:
            Populated instance of :class:
            `openquake.hmtk.seismicity.selector.CatalogueSelector`

        :param distance:
            Distance from point (km) for selection

        :param str distance_metric
            Choice of fault source distance metric 'joyner-boore' or 'rupture'

        :param float upper_eq_depth:
            Upper hypocentral depth of hypocentres to be selected

        :param float lower_eq_depth:
            Lower hypocentral depth of hypocentres to be selected

        """
        if selector.catalogue.get_number_events() < 1:
            raise ValueError("No events found in catalogue!")

        # If dip is != 90 and 'rupture' distance metric is selected
        if ("rupture" in distance_metric) and (fabs(self.dip - 90) > 1e-5):
            # Use rupture distance
            self.catalogue = selector.within_rupture_distance(
                self.geometry,
                distance,
                upper_depth=upper_eq_depth,
                lower_depth=lower_eq_depth,
            )
        else:
            # Use Joyner-Boore distance
            self.catalogue = selector.within_joyner_boore_distance(
                self.geometry,
                distance,
                upper_depth=upper_eq_depth,
                lower_depth=lower_eq_depth,
            )

        if self.catalogue.get_number_events() < 5:
            # Throw a warning regarding the small number of earthquakes in
            # the source!
            warnings.warn(
                "Source %s (%s) has fewer than 5 events" % (self.id, self.name)
            )

    def create_oqhazardlib_source(self, tom, mesh_spacing, use_defaults=False):
        """
        Creates an instance of the source model as :class:
        openquake.hazardlib.source.complex_fault.ComplexFaultSource
        """
        if not self.mfd:
            raise ValueError("Cannot write to hazardlib without MFD")
        return ComplexFaultSource(
            self.id,
            self.name,
            self.trt,
            self.mfd,
            mesh_spacing,
            conv.mag_scale_rel_to_hazardlib(self.mag_scale_rel, use_defaults),
            conv.render_aspect_ratio(self.rupt_aspect_ratio, use_defaults),
            tom,
            self.fault_edges,
            self.rake,
        )
