#
# LICENSE
#
# Copyright (c) 2010-2017, GEM Foundation, G. Weatherill, M. Pagani,
# D. Monelli.
#
# The Hazard Modeller's Toolkit is free software: you can redistribute
# it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version
# of the License, or (at your option) any later version.
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

'''
Module to test :openquake.hmtk.faults.active_fault_model.mtkActiveFaultModel
'''


import unittest
import numpy as np
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.line import Line
from openquake.hazardlib.scalerel.wc1994 import WC1994
from openquake.hmtk.sources.simple_fault_source import mtkSimpleFaultSource
from openquake.hmtk.sources.complex_fault_source import mtkComplexFaultSource
from openquake.hmtk.faults.fault_models import mtkActiveFault
from openquake.hmtk.faults.fault_geometries import (SimpleFaultGeometry,
                                          ComplexFaultGeometry)
from openquake.hmtk.faults.active_fault_model import mtkActiveFaultModel


class TestmtkActiveFaultModel(unittest.TestCase):
    '''
    Tests the basic class to contain a set of active faults
    '''
    def setUp(self):
        '''
        '''
        self.model = None

    def test_instantiation_no_data(self):
        '''
        Tests instantiation of the class with no information
        '''
        self.model = mtkActiveFaultModel()
        self.assertIsNone(self.model.id)
        self.assertIsNone(self.model.name)
        self.assertListEqual(self.model.faults, [])

    def test_instatiation_all_correct(self):
        # Tests instatiation of the class with correct data
        self.model = mtkActiveFaultModel('001', 'A Fault Model', faults=[])
        self.assertEqual(self.model.id, '001')
        self.assertEqual(self.model.name, 'A Fault Model')
        self.assertListEqual(self.model.faults, [])

    def test_instantiation_bad_fault(self):
        # Tests instantiation with a bad fault input - should raise error
        with self.assertRaises(ValueError) as ae:
            self.model = mtkActiveFaultModel('001',
                                             'A Fault Model',
                                             'bad input')
            self.assertEqual(str(ae.exception),
                             'Faults must be input as list')

    def test_get_number_faults(self):
        # Tests the count of the number of faults

        # No faults
        self.model = mtkActiveFaultModel('001', 'A Fault Model', faults=[])
        self.assertEqual(self.model.get_number_faults(), 0)

        # Two faults
        self.model = mtkActiveFaultModel(
            identifier='001', name='A Fault Model',
            faults=[mtkActiveFault, mtkActiveFault])
        self.assertEqual(self.model.get_number_faults(), 2)

    def test_build_fault_model(self):
        # Tests the constuction of a fault model with two faults (1 simple,
        # 1 complex) each with two mfd rates - should produce four sources
        self.model = mtkActiveFaultModel('001', 'A Fault Model', faults=[])
        x0 = Point(30., 30., 0.)
        x1 = x0.point_at(30., 0., 30.)
        x2 = x1.point_at(30., 0., 60.)
        # Total length is 60 km
        trace = Line([x0, x1, x2])
        simple_fault = SimpleFaultGeometry(trace, 90., 0., 20.)
        # Creates a trace ~60 km long made of 3 points
        upper_edge = Line([x0, x1, x2])
        lower_edge = Line(
            [x0.point_at(40., 20., 130.),
             x1.point_at(42., 25., 130.),
             x2.point_at(41., 22., 130.)])
        complex_fault = ComplexFaultGeometry([upper_edge, lower_edge], 2.0)
        config = [{'MFD_spacing': 0.1,
                   'Maximum_Magnitude': 7.0,
                   'Maximum_Uncertainty': None,
                   'Model_Name': 'Characteristic',
                   'Model_Weight': 0.5,
                   'Sigma': 0.1,
                   'Lower_Bound': -1.,
                   'Upper_Bound': 1.},
                  {'MFD_spacing': 0.1,
                   'Maximum_Magnitude': 7.5,
                   'Maximum_Uncertainty': None,
                   'Model_Name': 'Characteristic',
                   'Model_Weight': 0.5,
                   'Sigma': 0.1,
                   'Lower_Bound': -1.,
                   'Upper_Bound': 1.}]
        fault1 = mtkActiveFault('001', 'Simple Fault 1', simple_fault,
                                [(10.0, 1.0)], -90., None,
                                aspect_ratio=1.0,
                                scale_rel=[(WC1994(), 1.0)],
                                shear_modulus=[(30.0, 1.0)],
                                disp_length_ratio=[(1E-5, 1.0)])
        fault1.generate_config_set(config)
        fault2 = mtkActiveFault('002', 'Complex Fault 1', complex_fault,
                                [(10.0, 1.0)], -90., None,
                                aspect_ratio=1.0,
                                scale_rel=[(WC1994(), 1.0)],
                                shear_modulus=[(30.0, 1.0)],
                                disp_length_ratio=[(1E-5, 1.0)])
        fault2.generate_config_set(config)
        self.model.faults = [fault1, fault2]

        # Generate source model
        self.model.build_fault_model()
        self.assertEqual(len(self.model.source_model.sources), 4)
        # First source should be an instance of a mtkSimpleFaultSource
        model1 = self.model.source_model.sources[0]
        self.assertTrue(isinstance(model1, mtkSimpleFaultSource))
        self.assertEqual(model1.id, '001_1')
        self.assertAlmostEqual(model1.mfd.min_mag, 6.9)
        np.testing.assert_array_almost_equal(
            np.log10(np.array(model1.mfd.occurrence_rates)),
            np.array([-2.95320041, -2.54583708, -2.953200413]))

        # Second source should be an instance of a mtkSimpleFaultSource
        model2 = self.model.source_model.sources[1]
        self.assertTrue(isinstance(model2, mtkSimpleFaultSource))
        self.assertEqual(model2.id, '001_2')
        self.assertAlmostEqual(model2.mfd.min_mag, 7.4)
        np.testing.assert_array_almost_equal(
            np.log10(np.array(model2.mfd.occurrence_rates)),
            np.array([-3.70320041, -3.29583708, -3.70320041]))

        # Third source should be an instance of a mtkComplexFaultSource
        model3 = self.model.source_model.sources[2]
        self.assertTrue(isinstance(model3, mtkComplexFaultSource))
        self.assertEqual(model3.id, '002_1')
        self.assertAlmostEqual(model3.mfd.min_mag, 6.9)
        np.testing.assert_array_almost_equal(
            np.log10(np.array(model3.mfd.occurrence_rates)),
            np.array([-2.59033387, -2.18297054, -2.59033387]))

        # Fourth source should be an instance of a mtkComplexFaultSource
        model4 = self.model.source_model.sources[3]
        self.assertTrue(isinstance(model4, mtkComplexFaultSource))
        self.assertEqual(model4.id, '002_2')
        self.assertAlmostEqual(model4.mfd.min_mag, 7.4)
        np.testing.assert_array_almost_equal(
            np.log10(np.array(model4.mfd.occurrence_rates)),
            np.array([-3.34033387, -2.93297054, -3.34033387]))
