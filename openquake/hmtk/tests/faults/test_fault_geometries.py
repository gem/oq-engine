#
# LICENSE
#
# Copyright (c) 2010-2017, GEM Foundation, G. Weatherill, M. Pagani,
# D. Monelli.
#
# The Hazard Modeller's Toolkit is free software: you can redistribute
# it and/or modify it under the terms of the GNU Affero General Public
#License as published by the Free Software Foundation, either version
#3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
#DISCLAIMER
#
# The software Hazard Modeller's Toolkit (openquake.hmtk) provided herein
#is released as a prototype implementation on behalf of
# scientists and engineers working within the GEM Foundation (Global
#Earthquake Model).
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

import unittest
import numpy as np
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.line import Line
from openquake.hazardlib.geo.surface import complex_fault, simple_fault
from openquake.hmtk.faults.fault_models import (SimpleFaultGeometry,
                                      ComplexFaultGeometry)


class TestSimpleGeometry(unittest.TestCase):
    '''
    Tests the :class: openquake.hmtk.fault.fault_geometries.SimpleFaultGeometry
    '''
    def setUp(self):
        '''
        Create a simple fault of known length and downdip width
        '''
        # Creates a trace ~60 km long made of 3 points
        x0 = Point(30., 30., 0.)
        x1 = x0.point_at(30., 0., 30.)
        x2 = x1.point_at(30., 0., 60.)
        # Total length is 60 km
        self.trace = Line([x0, x1, x2])
        self.dip = 90.   # Simple Vertical Strike-Slip fault
        # Total downdip width = 20. km
        self.upper_depth = 0.
        self.lower_depth = 20.
        self.fault = None

    def test_simple_fault_instantiation(self):
        '''
        Test the instantiation of the fault and the calculation of the length
        '''
        expected_keys = sorted(['trace', 'downdip_width', 'area', 'surface',
                                'upper_depth', 'length', 'surface_width',
                                'lower_depth', 'dip', 'typology'])
        self.fault = SimpleFaultGeometry(self.trace, self.dip,
                                         self.upper_depth, self.lower_depth)
        self.assertListEqual(sorted(self.fault.__dict__), expected_keys)
        self.assertAlmostEqual(self.fault.length, 60., 5)
        self.assertEqual(self.fault.typology, 'Simple')
        self.assertTrue(isinstance(self.fault.surface,
                                   simple_fault.SimpleFaultSurface))

    def test_simple_get_area_vertical(self):
        '''
        Tests the area calculation for a vertical fault
        '''
        # Case 1 - Vertical fault
        self.fault = SimpleFaultGeometry(self.trace, self.dip,
                                         self.upper_depth, self.lower_depth)

        self.assertAlmostEqual(1200., self.fault.get_area(), 5)
        self.assertAlmostEqual(20., self.fault.downdip_width, 5)
        self.assertAlmostEqual(0., self.fault.surface_width, 5)

    def test_simple_get_area_dipping(self):
        '''
        Tests the area calculation for a dipping fault
        '''
        self.dip = 30.
        self.fault = SimpleFaultGeometry(self.trace, self.dip,
                                         self.upper_depth, self.lower_depth)
        self.assertAlmostEqual(2400., self.fault.get_area(), 5)
        self.assertAlmostEqual(40., self.fault.downdip_width, 5)


class TestComplexFaultGeometry(unittest.TestCase):
    '''
    Tests the:w implementation of the :class:
    openquake.hmtk.faults.fault_geometries.ComplexFaultGeometry
    '''
    def setUp(self):
        '''
        Creates a complex fault typology
        '''
        x0 = Point(30., 30., 0.)
        x1 = x0.point_at(30., 0., 30.)
        x2 = x1.point_at(30., 0., 60.)
        upper_edge = Line([x0, x1, x2])
        lower_edge = Line([x0.point_at(40., 20., 130.),
                           x1.point_at(42., 25., 130.),
                           x2.point_at(41., 22., 130.)])
        self.edges = [upper_edge, lower_edge]
        self.fault = None

    def test_instantiation_complex(self):
        '''
        Tests instantiation of the class
        '''
        self.fault = ComplexFaultGeometry(self.edges, 1.0)
        self.assertTrue(isinstance(self.fault.surface,
                                   complex_fault.ComplexFaultSurface))
        self.assertEqual(self.fault.typology, 'Complex')
        self.assertAlmostEqual(self.fault.dip, 30.8283885, 5)

    def test_get_area_complex(self):
        '''
        As the get area class simply implements the get_area() method of
        :class: openquake.hazardlib.geo.surface.complex_fault.
        ComplexFaultSurface this test simply checks that it is called.
        '''
        self.fault = ComplexFaultGeometry(self.edges, 1.0)
        self.assertAlmostEqual(2767.2418367330, self.fault.get_area(), 5)
