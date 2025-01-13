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
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

import abc
import numpy as np
from openquake.hazardlib.geo.surface.simple_fault import SimpleFaultSurface
from openquake.hazardlib.geo.surface.complex_fault import ComplexFaultSurface


class BaseFaultGeometry(object):
    """
    Abstract base class to support geometry parameters and methods
    """

    @abc.abstractmethod
    def get_area(self):
        """
        Returns the area of the fault surface
        """


class SimpleFaultGeometry(BaseFaultGeometry):
    """
    Describes the geometrical propeties of a simple fault surface

    :param str typology:
        Source typology
    :param trace:
        Fault trace as instance of :class: openquake.hazardlib.geo.line.Line
    :param float dip:
        Fault dip (degrees)
    :param float upper_depth:
        Upper seismogenic depth (km)
    :param float lower_depth:
        Lower seismogenic depth (km)
    :param surface:
        Instance of
        :class: openquake.hazardlib.geo.surface.simple_fault.SimpleFaultSurface
    :param float length:
        Along-strike length of fault (km)
    :param float width:
        Down-dip width of fault (km)
    :param float area:
        Length of fault (km)

    """

    def __init__(self, trace, dip, upper_depth, lower_depth, mesh_spacing=1.0):
        """
        Sets up the fault geometry parameters from the input fault definitions
        :param float mesh_spacing:
            Spacing (km) of the fault surface mesh
        """
        self.typology = "Simple"
        self.trace = trace
        self.dip = dip
        self.upper_depth = upper_depth
        self.lower_depth = lower_depth
        self.surface = SimpleFaultSurface.from_fault_data(
            self.trace,
            self.upper_depth,
            self.lower_depth,
            self.dip,
            mesh_spacing,
        )
        self.length = trace.get_length()
        self.downdip_width = None
        self.surface_width = None
        self.area = None

    def get_area(self):
        """
        Calculates the area of the fault (km ** 2.) as the product of length
        (km) and downdip width (km)
        """
        d_z = self.lower_depth - self.upper_depth
        self.downdip_width = d_z / np.sin(self.dip * np.pi / 180.0)
        self.surface_width = self.downdip_width * np.cos(
            self.dip * np.pi / 180.0
        )
        self.area = self.length * self.downdip_width
        return self.area


class ComplexFaultGeometry(BaseFaultGeometry):
    """
    Module openquake.hmtk.faults.fault_model.ComplexFaultGeometry describes the
    geometrical properties of a complex fault surface

    :param str typology:
        Source typology
    :param trace:
        Fault edges as list of instances of :class:
        openquake.hazardlib.geo.line.Line
    :param float dip:
        Fault dip (degrees)
    :param float upper_depth:
        Upper seismogenic depth (km)
    :param float lower_depth:
        Lower seismogenic depth (km)
    :param surface:
        Instance of :class:
        openquake.hazardlib.geo.surface.complex_fault.ComplexFaultSurface
    :param float length:
        Along-strike length of fault (km)
    :param float width:
        Down-dip width of fault (km)
    :param float area:
        Length of fault (km)
    """

    def __init__(self, traces, mesh_spacing=1.0):
        """
        Set up function an creates complex fault surface
        :param list traces:
            Edges of the complex fault as a list of :class:
            openquake.hazardlib.geo.line.Line. Please refer to documentation of
            openquake.hazardlib.geo.surface.complex_fault.ComplexFaultSurface
            for details.
        :param float mesh_spacing:
            Spacing (km) of the fault surface mesh
        """
        self.typology = "Complex"
        self.trace = traces
        self.upper_depth = None
        self.lower_depth = None
        self.surface = ComplexFaultSurface.from_fault_data(
            self.trace, mesh_spacing
        )
        self.dip = self.surface.get_dip()

    def get_area(self):
        """
        Calculates the area of the complex fault from the surface mesh uses
        :class: openquake.hazardlib.surface.complex_fault.ComplexFaultSurface
        """
        return self.surface.get_area()
