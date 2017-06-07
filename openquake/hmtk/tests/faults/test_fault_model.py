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

'''
Module to test :openquake.hmtk.faults.fault_model classes
'''
import os
import unittest
import numpy as np
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.line import Line
from openquake.hazardlib.scalerel.wc1994 import WC1994
from openquake.hazardlib.mfd.evenly_discretized import EvenlyDiscretizedMFD
from openquake.hmtk.models import IncrementalMFD
from openquake.hmtk.sources.simple_fault_source import mtkSimpleFaultSource
from openquake.hmtk.sources.complex_fault_source import mtkComplexFaultSource
from openquake.hmtk.seismicity.catalogue import Catalogue
from openquake.hmtk.seismicity.selector import CatalogueSelector
from openquake.hmtk.faults.mfd.characteristic import Characteristic
from openquake.hmtk.faults.tectonic_regionalisation import TectonicRegionalisation
from openquake.hmtk.faults.fault_geometries import (SimpleFaultGeometry,
                                          ComplexFaultGeometry)
from openquake.hmtk.faults.fault_models import (_update_slip_rates_with_aseismic,
                                      RecurrenceBranch,
                                      mtkActiveFault)

BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'fault_data')
FAULT_RATE_DATA = np.genfromtxt(os.path.join(BASE_DATA_PATH,
                                'recurrence_branches_results.txt'))

COLLAPSE_DATA = np.array([
    [5.0, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 6.0, 6.1,
     6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 7.0, np.nan],
    [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
     1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.3],
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0,
     1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.2],
    [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
     1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.1],
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0,
     1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.4],
    [0.1, 0.1, 0.1, 0.1, 0.1, 0.4, 0.4, 0.4, 0.4, 0.4, 1.0, 1.0, 1.0, 1.0, 1.0,
     1.0, 0.7, 0.7, 0.7, 0.7, 0.7, np.nan]])


class TestFaultAncilliaries(unittest.TestCase):
    '''
    Small test of method to test ancillary functions of the fault classes
    '''
    def setUp(self):
        '''
        '''

    def test_update_slip_aseismic(self):
        '''
        Simple test to ensure slip is updates with aseismic rate correctly
        '''
        # Single slip observation
        slip_single = [(12.0, 1.0)]
        aseismic = 0.5
        self.assertListEqual(
            _update_slip_rates_with_aseismic(slip_single, aseismic),
            [(6.0, 1.0)])
        # Multiple slip observations
        slip_single = [(12.0, 0.5), (14.0, 0.5)]
        aseismic = 0.5
        self.assertListEqual(
            _update_slip_rates_with_aseismic(slip_single, aseismic),
            [(6.0, 0.5), (7.0, 0.5)])


class TestRecurrenceBranch(unittest.TestCase):
    '''
    Test the :class: openquake.hmtk.faults.fault_models.RecurrenceBranch - the class
    to control the recurrence calculation for a given model
    '''

    def setUp(self):
        '''
        '''
        self.msr = WC1994
        self.model = None
        self.mfd_config = None

    def test_simple_instantiation(self):
        '''
        Basic instantiation test
        '''
        # Area = 1200 km ^ 2, slip = 12 mm/yr, Rake = -90, Shear Mod =30. GPa
        self.model = RecurrenceBranch(1200., 12., self.msr, -90., 30.)
        expected_dict = {'area': 1200.0,
                         'branch_id': None,
                         'disp_length_ratio': None,
                         'magnitudes': None,
                         'max_mag': None,
                         'msr': WC1994,
                         'msr_sigma': 0.0,
                         'rake': -90.0,
                         'recurrence': None,
                         'shear_modulus': 30.0,
                         'slip': 12.0,
                         'weight': 1.0}
        self.assertDictEqual(self.model.__dict__, expected_dict)

    def test_update_weight(self):
        '''
        Tests the simple function to update the weight
        '''
        self.model = RecurrenceBranch(1200., 12., WC1994,  -90., 30.)
        self.model.update_weight(0.5)
        self.assertAlmostEqual(0.5, self.model.weight, 7)

    def test_get_recurrence_simple_characteristic(self):
        '''
        Tests the function to get the recurrence calculation for a simple
        characteristic earthquake
        '''
        self.mfd_config = {'MFD_spacing': 0.1,
                           'Model_Name': 'Characteristic',
                           'Model_Weight': 1.0,
                           'Maximum_Magnitude': None,
                           'Maximum_Uncertainty': None,
                           'Lower_Bound': -2.,
                           'Upper_Bound': 2., 'Sigma': 0.12}

        self.model = RecurrenceBranch(8500., 5., WC1994(), 0., 30.)
        self.model.get_recurrence(self.mfd_config)
        # Test the same process using just the openquake.hmtk.faults.mfd.characteristic
        # Implementation
        test_model = Characteristic()
        test_model.setUp(self.mfd_config)
        test_model.get_mmax(self.mfd_config, WC1994(), 0., 8500.)
        _ = test_model.get_mfd(5.0, 8500., 30.)
        self.assertTrue(isinstance(self.model.recurrence, IncrementalMFD))
        self.assertAlmostEqual(self.model.recurrence.min_mag,
                               test_model.mmin)
        self.assertAlmostEqual(self.model.recurrence.bin_width,
                               test_model.bin_width)
        np.testing.assert_array_almost_equal(self.model.recurrence.occur_rates,
                                             test_model.occurrence_rate)



class TestmtkActiveFault(unittest.TestCase):
    '''
    Tests the main active fault class openquake.hmtk.faults.fault_model.mtkActiveFault
    '''
    def setUp(self):
        '''
        '''
        self.fault = None
        self.regionalisation = None
        self.msr = [(WC1994(), 1.0)]
        self.msr_sigma = [(-1.5, 0.15), (0.0, 0.7), (1.5, 0.15)]
        self.shear_mod = [(30.0, 0.8), (35.0, 0.2)]
        self.dlr = [(1.25E-5, 1.0)]
        self.config = [{}]
        self.slip = [(10.0, 1.0)]
        x0 = Point(30., 30., 0.)
        x1 = x0.point_at(30., 0., 30.)
        x2 = x1.point_at(30., 0., 60.)
        # Total length is 60 km
        self.trace = Line([x0, x1, x2])
        self.dip = 90.
        self.upper_depth = 0.
        self.lower_depth = 20.
        self.simple_fault = SimpleFaultGeometry(self.trace,
                                                self.dip,
                                                self.upper_depth,
                                                self.lower_depth)
                # Creates a trace ~60 km long made of 3 points
        upper_edge = Line([x0, x1, x2])
        lower_edge = Line([x0.point_at(40., 20., 130.),
                           x1.point_at(42., 25., 130.),
                           x2.point_at(41., 22., 130.)])
        self.complex_fault = ComplexFaultGeometry([upper_edge, lower_edge],
                                                  2.0)


    def test_mtk_active_fault_instantiation(self):
        '''
        Tests core instantiation of mtkActiveFault Class
        '''

        self.fault = mtkActiveFault('001', 'A Fault', self.simple_fault,
                                    self.slip, 0., 'Active Shallow Crust',
                                    aseismic=0.5)
        self.assertListEqual([(0., 1.0)], self.fault.msr_sigma)
        self.assertAlmostEqual(self.fault.area, 1200.)
        self.assertListEqual([(5.0, 1.0)], self.fault.slip)

    def test_mtk_active_fault_not_bad_input_geometry(self):
        '''
        Tests the instantiation with a bad geometry input - should raise error
        '''
        with self.assertRaises(IOError) as ioe:
            self.fault = mtkActiveFault('001', 'A Fault', 'Nonsense',
                                        self.slip, 0., 'Active Shallow Crust')
        self.assertEqual(str(ioe.exception), 'Geometry must be instance '
                         'of openquake.hmtk.faults.fault_geometries.BaseFaultGeometry')

    def test_mtk_active_fault_not_bad_input_slip(self):
        '''
        Tests the instantiation with slip wieghts not equal to 1.0 -
        should raise value error
        '''
        with self.assertRaises(ValueError) as ae:
            self.fault = mtkActiveFault('001', 'A Fault', self.simple_fault,
                                        [(5.0, 0.5), (7.0, 0.4)], 0.,
                                        'Active Shallow Crust')
        self.assertEqual(str(ae.exception),
                         'Slip rate weightings must sum to 1.0')

    def test_get_tectonic_regionalisation(self):
        '''
        Tests the retreival of tectonic regionalisation information
        '''
        # Set up regionalistion
        region_dict = [{'Code': '001', 'Name': 'Active Shallow Crust'}]
        tect_reg = TectonicRegionalisation()
        tect_reg.populate_regions(region_dict)

        # Test successful case
        self.fault = mtkActiveFault('001', 'A Fault', self.simple_fault,
                                    self.slip, 0., None)
        self.fault.get_tectonic_regionalisation(tect_reg,
                                                'Active Shallow Crust')
        self.assertEqual(self.fault.trt, 'Active Shallow Crust')
        # Should take default values
        self.assertListEqual(self.fault.shear_modulus, [(30., 1.0)])
        self.assertListEqual(self.fault.disp_length_ratio, [(1.25E-5, 1.0)])
        self.assertTrue(isinstance(self.fault.msr[0][0], WC1994))
        self.assertAlmostEqual(self.fault.msr[0][1], 1.0)


    def test_get_tectonic_regionalisation_missing_case(self):
        '''
         Test case when no region is defined - should raise error
        '''
        # Set up regionalistion
        region_dict = [{'Code': '001', 'Name': 'Active Shallow Crust'}]
        tect_reg = TectonicRegionalisation()
        tect_reg.populate_regions(region_dict)

        self.fault = mtkActiveFault('001', 'A Fault', self.simple_fault,
                                    self.slip, 0., None)

        with self.assertRaises(ValueError) as ae:
            self.fault.get_tectonic_regionalisation(tect_reg, None)

        self.assertEqual(str(ae.exception),
                         'Tectonic region classification missing or '
                         'not defined in regionalisation')

    def test_generate_config_set_as_dict(self):
        '''
        Tests the function to generate a configuration tuple list from a
        single config dict
        '''
        self.fault = mtkActiveFault('001', 'A Fault', self.simple_fault,
                                    [(5., 1.0)], 0., None)
        good_config = {'MFD_spacing': 0.1,
                       'Maximum_Magnitude': None,
                       'Minimum_Magnitude': 5.0,
                       'Model_Name': 'AndersonLucoArbitrary',
                       'Model_Weight': 1.0,
                       'Model_Type': 'First',
                       'b_value': [0.8, 0.05]}
        self.fault.generate_config_set(good_config)
        self.assertTrue(isinstance(self.fault.config, list))
        self.assertDictEqual(self.fault.config[0][0], good_config)
        self.assertAlmostEqual(self.fault.config[0][1], 1.0)

    def test_generate_config_set_as_dict(self):
        '''
        Tests the function to generate a configuration tuple list from a
        list of multiple config dicts
        '''
        self.fault = mtkActiveFault('001', 'A Fault', self.simple_fault,
            [(5., 1.0)], 0., None)
        good_config = [{'MFD_spacing': 0.1,
                       'Maximum_Magnitude': None,
                       'Minimum_Magnitude': 5.0,
                        'Model_Name': 'AndersonLucoArbitrary',
                        'Model_Weight': 0.7,
                        'Model_Type': 'First',
                        'b_value': [0.8, 0.05]},
                       {'MFD_spacing': 0.1,
                        'Maximum_Magnitude': None,
                        'Maximum_Magnitude_Uncertainty': None,
                        'Minimum_Magnitude': 5.0,
                        'Model_Name': 'YoungsCoppersmithExp',
                        'Model_Weight': 0.3,
                        'b_value': [0.8, 0.05]}]
        self.fault.generate_config_set(good_config)
        self.assertTrue(isinstance(self.fault.config, list))
        self.assertEqual(len(self.fault.config), 2)
        self.assertDictEqual(self.fault.config[0][0], good_config[0])
        self.assertDictEqual(self.fault.config[1][0], good_config[1])
        self.assertAlmostEqual(self.fault.config[0][1], 0.7)
        self.assertAlmostEqual(self.fault.config[1][1], 0.3)

    def test_generate_config_set_bad_input(self):
        '''
        Tests that valueError is raised when the config is not input as either
        a list or dict
        '''
        self.fault = mtkActiveFault('001', 'A Fault', self.simple_fault,
                                    [(5., 1.0)], 0., None)
        with self.assertRaises(ValueError) as ae:
            self.fault.generate_config_set(None)
        self.assertEqual(str(ae.exception),
                         'MFD config must be input as dictionary or list!')

    def test_generate_config_set_with_bad_weights(self):
        '''
        Tests that a valueError is raised when the config weights do not sum
        to 1.0
        '''
        self.fault = mtkActiveFault('001', 'A Fault', self.simple_fault,
                                    [(5., 1.0)], 0., None)
        bad_config = [{'MFD_spacing': 0.1,
                       'Maximum_Magnitude': None,
                       'Minimum_Magnitude': 5.0,
                       'Model_Name': 'AndersonLucoArbitrary',
                       'Model_Weight': 0.5,
                       'Type': 'First',
                       'b_value': [0.8, 0.05]},
                      {'MFD_spacing': 0.1,
                       'Maximum_Magnitude': None,
                       'Maximum_Magnitude_Uncertainty': None,
                       'Minimum_Magnitude': 5.0,
                       'Model_Name': 'YoungsCoppersmithExponential',
                       'Model_Weight': 0.3,
                       'b_value': [0.8, 0.05]}]
        with self.assertRaises(ValueError) as ae:
            self.fault.generate_config_set(bad_config)
        self.assertEqual(str(ae.exception),
                         'MFD config weights do not sum to 1.0 for fault 001')


    def test_generate_branching_index(self):
        '''
        Simple test to check that a correct branching index is raised
        Slip - 2 values
        MSR - 1 value
        Shear Modulus - 2 value
        DLR - 1 value
        MSR_Sigma - 3 Values
        Config - 1 value
        '''
        self.fault = mtkActiveFault(
            '001',
            'A Fault',
            self.simple_fault,
            [(5., 0.5), (7., 0.5)],
            0.,
            None,
            msr_sigma=[(-1.5, 0.15), (0., 0.7), (1.5, 0.15)],
            neotectonic_fault=None,
            scale_rel=[(WC1994(), 1.0)],
            aspect_ratio=1.0,
            shear_modulus=[(28., 0.5), (30., 0.5)],
            disp_length_ratio=[(1.25E-5, 1.0)])
        # Set with only one config - no data input
        self.fault.generate_config_set({})
        expected_result = np.array([[0, 0, 0, 0, 0, 0],
                                    [0, 0, 0, 0, 1, 0],
                                    [0, 0, 0, 0, 2, 0],
                                    [0, 0, 1, 0, 0, 0],
                                    [0, 0, 1, 0, 1, 0],
                                    [0, 0, 1, 0, 2, 0],
                                    [1, 0, 0, 0, 0, 0],
                                    [1, 0, 0, 0, 1, 0],
                                    [1, 0, 0, 0, 2, 0],
                                    [1, 0, 1, 0, 0, 0],
                                    [1, 0, 1, 0, 1, 0],
                                    [1, 0, 1, 0, 2, 0]], dtype=int)
        branch_index, number_branches = \
            self.fault._generate_branching_index()
        np.testing.assert_array_equal(branch_index, expected_result)
        self.assertEqual(number_branches, 12)

    def test_generate_recurrence_models_bad_input(self):
        '''
        Tests to ensure correct errors are raised when input is bad
        '''
        self.fault = mtkActiveFault(
            '001',
            'A Fault',
            self.simple_fault,
            [(5., 0.5), (7., 0.5)],
            0.,
            None,
            msr_sigma=[(-1.5, 0.15), (0., 0.7), (1.5, 0.15)])

        # Test 1 - Non-iterable config
        bad_config = None
        with self.assertRaises(ValueError) as ae:
            self.fault.generate_recurrence_models(bad_config)
            self.assertEqual(
                str(ae.exception),
                'MFD configuration missing or incorrectly formatted')
        # Test 2 - Collapse is required but no msr set!
        with self.assertRaises(ValueError) as ae:
            self.fault.generate_recurrence_models(collapse=True)
            self.assertEqual(str(ae.exception),
                             'Collapsing logic tree branches requires input '
                             'of a single msr for rendering sources')

    def test_collapse_branches(self):
        '''
        Tests a simple collapsing of branches for uneven periods
        '''
        test_fault, expected_rates, mmin, mmax, weights = \
            self._build_mock_recurrence_branches()
        test_mfd = test_fault.collapse_branches(mmin, 0.1, mmax)
        np.testing.assert_array_almost_equal(test_mfd.occur_rates,
                                             expected_rates)

    def test_select_catalogue_rjb(self):
        """
        Tests catalogue selection with Joyner-Boore distance
        """
        self.fault = mtkActiveFault(
            '001',
            'A Fault',
            self.simple_fault,
            [(5., 0.5), (7., 0.5)],
            0.,
            None,
            msr_sigma=[(-1.5, 0.15), (0., 0.7), (1.5, 0.15)])
        cat1 = Catalogue()
        cat1.data = {"eventID": ["001", "002", "003", "004"],
                     "longitude": np.array([30.1, 30.1, 30.5, 31.5]),
                     "latitude": np.array([30.0, 30.25, 30.4, 30.5]),
                     "depth": np.array([5.0, 250.0, 10.0, 10.0])}
        selector = CatalogueSelector(cat1)
        # Select within 50 km of the fault
        self.fault.select_catalogue(selector, 50.0,
                                    distance_metric="joyner-boore")
        np.testing.assert_array_almost_equal(
            self.fault.catalogue.data["longitude"],
            np.array([30.1, 30.1, 30.5]))
        np.testing.assert_array_almost_equal(
            self.fault.catalogue.data["latitude"],
            np.array([30.0, 30.25, 30.4]))
        np.testing.assert_array_almost_equal(
            self.fault.catalogue.data["depth"],
            np.array([5.0, 250.0, 10.0]))

    def test_select_catalogue_rrup(self):
        """
        Tests catalogue selection with Joyner-Boore distance
        """
        self.fault = mtkActiveFault(
            '001',
            'A Fault',
            self.simple_fault,
            [(5., 0.5), (7., 0.5)],
            0.,
            None,
            msr_sigma=[(-1.5, 0.15), (0., 0.7), (1.5, 0.15)])

        cat1 = Catalogue()
        cat1.data = {"eventID": ["001", "002", "003", "004"],
                     "longitude": np.array([30.1, 30.1, 30.5, 31.5]),
                     "latitude": np.array([30.0, 30.25, 30.4, 30.5]),
                     "depth": np.array([5.0, 250.0, 10.0, 10.0])}
        selector = CatalogueSelector(cat1)
        # Select within 50 km of the fault
        self.fault.select_catalogue(selector, 50.0,
                                    distance_metric="rupture")
        np.testing.assert_array_almost_equal(
            self.fault.catalogue.data["longitude"],
            np.array([30.1, 30.5]))
        np.testing.assert_array_almost_equal(
            self.fault.catalogue.data["latitude"],
            np.array([30.0, 30.4]))
        np.testing.assert_array_almost_equal(
            self.fault.catalogue.data["depth"],
            np.array([5.0, 10.0]))

    def _build_mock_recurrence_branches(self):
        '''
        Given the mock branches return information necessary to define a
        collapse model
        '''
        # Build test data
        mags = COLLAPSE_DATA[0, :-1]
        weights = COLLAPSE_DATA[1:-1, -1]
        rates = COLLAPSE_DATA[1:-1:, :-1]
        expected_rate = COLLAPSE_DATA[-1, :-1]
        test_fault = mtkActiveFault(
            '001',
            'A Fault',
            self.simple_fault,
            [(5.0, 1.0)],
            0.,
            None)
        test_fault.mfd_models = []
        for (iloc, weight) in enumerate(weights):
            idx = rates[iloc, :] > 0
            model = RecurrenceBranch(None, None, None, None, None,
                                     weight=weight)
            model.recurrence = IncrementalMFD(np.min(rates[iloc, idx]), 0.1,
                                              rates[iloc, idx])
            model.magnitudes = mags[idx]
            test_fault.mfd_models.append(model)
        return test_fault, expected_rate, np.min(mags), np.max(mags), weights

    def test_generate_recurrence_models_no_collapse(self):
        '''
        Tests the generate recurrence models option without collapsing
        branches: simple example with two slip rates and two mfd configurations
        '''
        self.fault = mtkActiveFault(
            '001',
            'A Fault',
            self.simple_fault,
            [(5., 0.5), (7., 0.5)],
            0.,
            None,
            aseismic=0.,
            msr_sigma=[(0.0, 1.0)],
            neotectonic_fault=None,
            scale_rel=[(WC1994(), 1.0)],
            aspect_ratio=1.0,
            shear_modulus=[(30., 1.0)],
            disp_length_ratio=[(1.25E-5, 1.0)])
        mfd_config = [{'MFD_spacing': 0.1,
                       'Maximum_Magnitude': None,
                       'Minimum_Magnitude': 5.0,
                        'Model_Name': 'AndersonLucoArbitrary',
                        'Model_Weight': 0.7,
                        'Model_Type': 'First',
                        'b_value': [0.8, 0.05]},
                       {'MFD_spacing': 0.1,
                        'Maximum_Magnitude': None,
                        'Maximum_Magnitude_Uncertainty': None,
                        'Minimum_Magnitude': 5.0,
                        'Model_Name': 'YoungsCoppersmithExponential',
                        'Model_Weight': 0.3,
                        'b_value': [0.8, 0.05]}]

        # Enumerates branches should have four models
        self.fault.generate_recurrence_models(config=mfd_config)
        mfds = self.fault.mfd[0]
        weights = self.fault.mfd[1]
        np.testing.assert_array_almost_equal(
            weights,
            np.array([0.35, 0.15, 0.35, 0.15]))
        for (iloc, occur) in enumerate(mfds):
            np.testing.assert_array_almost_equal(
                np.log10(occur.occur_rates),
                FAULT_RATE_DATA[iloc, :])


    def test_recurrence_collapse_branches(self):
        '''
        Tests the recurrence model generated by collapsing branches
        '''

        self.fault = mtkActiveFault(
            '001',
            'A Fault',
            self.simple_fault,
            [(5., 0.5), (7., 0.5)],
            0.,
            None,
            aseismic=0.,
            msr_sigma=[(0.0, 1.0)],
            neotectonic_fault=None,
            scale_rel=[(WC1994(), 1.0)],
            aspect_ratio=1.0,
            shear_modulus=[(30., 1.0)],
            disp_length_ratio=[(1.25E-5, 1.0)])
        mfd_config = [{'MFD_spacing': 0.1,
                       'Maximum_Magnitude': None,
                       'Minimum_Magnitude': 5.0,
                        'Model_Name': 'AndersonLucoArbitrary',
                        'Model_Weight': 0.7,
                        'Model_Type': 'First',
                        'b_value': [0.8, 0.05]},
                       {'MFD_spacing': 0.1,
                        'Maximum_Magnitude': None,
                        'Maximum_Magnitude_Uncertainty': None,
                        'Minimum_Magnitude': 5.0,
                        'Model_Name': 'YoungsCoppersmithExponential',
                        'Model_Weight': 0.3,
                        'b_value': [0.8, 0.05]}]

        # Enumerated branches should have four models
        self.fault.generate_recurrence_models(collapse=True,
                                              rendered_msr=WC1994(),
                                              config=mfd_config)

        expected_rates = 0.
        expected_weights = np.array([0.35, 0.15, 0.35, 0.15])
        for iloc in range(0, 4):
            expected_rates = expected_rates + (expected_weights[iloc] *
                                               10. ** FAULT_RATE_DATA[iloc, :])
        np.testing.assert_array_almost_equal(
            np.log10(self.fault.mfd[0][0].occur_rates),
            np.log10(expected_rates))


    def test_generate_fault_source_model_simple(self):
        '''
        Tests the function to turn fault model into mtkSimpleFault or
        mtkComplexFault
        '''
        self.fault = mtkActiveFault(
            '001',
            'A Fault',
            self.simple_fault,
            [(5.0, 1.0)],
            0.,
            None,
            aseismic=0.,
            msr_sigma=[(0.0, 1.0)],
            neotectonic_fault=None,
            scale_rel=[(WC1994(), 1.0)],
            aspect_ratio=1.0,
            shear_modulus=[(30., 1.0)],
            disp_length_ratio=[(1.25E-5, 1.0)])
        # Define simple placeholder MFD
        rec_models = [IncrementalMFD(5.0, 0.1, 1.0 * np.ones(10)),
                      IncrementalMFD(5.0, 0.1, 2.0 * np.ones(10))]
        self.fault.mfd = (rec_models, [0.5, 0.5], [WC1994(), WC1994()])

        # Run model
        source_model, weights = self.fault.generate_fault_source_model()
        self.assertEqual(len(source_model), 2)
        self.assertTrue(isinstance(source_model[0], mtkSimpleFaultSource))
        for iloc, model in enumerate(source_model):
            self.assertEqual(model.id, '001')
            self.assertTrue(isinstance(model.mfd, EvenlyDiscretizedMFD))
            np.testing.assert_array_almost_equal(model.mfd.occurrence_rates,
                                                 rec_models[iloc].occur_rates)
            self.assertAlmostEqual(weights[iloc], 0.5)


    def test_generate_fault_source_model_complex(self):
        '''
        Tests the function to turn fault model into mtkSimpleFault or
        mtkComplexFault
        '''
        self.fault = mtkActiveFault(
            '001',
            'A Fault',
            self.complex_fault,
            [(5.0, 1.0)],
            0.,
            None,
            aseismic=0.,
            msr_sigma=[(0.0, 1.0)],
            neotectonic_fault=None,
            scale_rel=[(WC1994(), 1.0)],
            aspect_ratio=1.0,
            shear_modulus=[(30., 1.0)],
            disp_length_ratio=[(1.25E-5, 1.0)])
        # Define simple placeholder MFD
        rec_models = [IncrementalMFD(5.0, 0.1, 1.0 * np.ones(10)),
                      IncrementalMFD(5.0, 0.1, 2.0 * np.ones(10))]
        self.fault.mfd = (rec_models, [0.5, 0.5], [WC1994(), WC1994()])

        # Run model
        source_model, weights = self.fault.generate_fault_source_model()
        self.assertEqual(len(source_model), 2)
        self.assertTrue(isinstance(source_model[0], mtkComplexFaultSource))
        for iloc, model in enumerate(source_model):
            self.assertEqual(model.id, '001')
            self.assertTrue(isinstance(model.mfd, EvenlyDiscretizedMFD))
            np.testing.assert_array_almost_equal(model.mfd.occurrence_rates,
                                                 rec_models[iloc].occur_rates)
            self.assertAlmostEqual(weights[iloc], 0.5)
