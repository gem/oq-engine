#!/usr/bin/env python
#
# LICENSE
#
#

'''
Module :mod: tests.seismicity.test_selector.tests algorithms for
geographical selection of seismicity with respect to various source geometries
'''

import unittest
import numpy as np
import datetime
from openquake.hmtk.seismicity.catalogue import Catalogue
from openquake.hmtk.seismicity.selector import (_check_depth_limits,
                                      _get_decimal_from_datetime,
                                      CatalogueSelector)
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.polygon import Polygon
from openquake.hazardlib.geo.line import Line
from openquake.hazardlib.geo.surface.simple_fault import SimpleFaultSurface


class TestSelector(unittest.TestCase):
    '''
    Tests the openquake.hmtk.seismicity.selector.Selector class
    '''
    def setUp(self):
        self.catalogue = Catalogue()
        self.polygon = None

    def test_check_on_depth_limits(self):
        # Tests the checks on depth limits
        test_dict = {'upper_depth': None, 'lower_depth': None}
        self.assertTupleEqual((0.0, np.inf), _check_depth_limits(test_dict))

        test_dict = {'upper_depth': 2.0, 'lower_depth': None}
        self.assertTupleEqual((2.0, np.inf), _check_depth_limits(test_dict))

        test_dict = {'upper_depth': None, 'lower_depth': 10.0}
        self.assertTupleEqual((0.0, 10.0), _check_depth_limits(test_dict))

        test_dict = {'upper_depth': -4.2, 'lower_depth': None}
        self.assertRaises(ValueError, _check_depth_limits, test_dict)

        test_dict = {'upper_depth': 5.0, 'lower_depth': 1.0}
        self.assertRaises(ValueError, _check_depth_limits, test_dict)

    def test_convert_datetime_to_decimal(self):
        # Tests the function to convert a time from a datetime object to a
        # decimal - simple test to check conversion
        # NB Still will not work for BCE dates
        simple_time = datetime.datetime(1900, 6, 6, 1, 1, 1, 0)
        stime = float(_get_decimal_from_datetime(simple_time))
        self.assertAlmostEqual(stime, 1900.42751335)

    def test_catalogue_selection(self):
        # Tests the tools for selecting events within the catalogue
        self.catalogue.data['longitude'] = np.arange(1.,6., 1.)
        self.catalogue.data['latitude'] = np.arange(6., 11., 1.)
        self.catalogue.data['depth'] = np.ones(5, dtype=bool)

        # No events selected
        flag_none = np.zeros(5, dtype=bool)
        selector0 = CatalogueSelector(self.catalogue)
        test_cat1 = selector0.select_catalogue(flag_none)
        self.assertEqual(len(test_cat1.data['longitude']), 0)
        self.assertEqual(len(test_cat1.data['latitude']), 0)
        self.assertEqual(len(test_cat1.data['depth']), 0)

        # All events selected
        flag_all = np.ones(5, dtype=bool)
        test_cat1 = selector0.select_catalogue(flag_all)
        self.assertTrue(np.allclose(test_cat1.data['longitude'],
                                    self.catalogue.data['longitude']))
        self.assertTrue(np.allclose(test_cat1.data['latitude'],
                                    self.catalogue.data['latitude']))
        self.assertTrue(np.allclose(test_cat1.data['depth'],
                                    self.catalogue.data['depth']))

        # Some events selected
        flag_1 = np.array([True, False, True, False, True])
        test_cat1 = selector0.select_catalogue(flag_1)
        self.assertTrue(np.allclose(test_cat1.data['longitude'],
                                    np.array([1., 3., 5.])))
        self.assertTrue(np.allclose(test_cat1.data['latitude'],
                                    np.array([6., 8., 10])))
        self.assertTrue(np.allclose(test_cat1.data['depth'],
                                    np.array([1., 1., 1.])))

    def test_select_within_polygon(self):
        # Tests the selection of points within polygon

        # Setup polygon
        nodes = np.array([[5.0, 6.0], [6.0, 6.0], [6.0, 5.0], [5.0, 5.0]])
        polygon0 = Polygon([Point(nodes[iloc, 0], nodes[iloc, 1])
                            for iloc in range(0, 4)])
        self.catalogue.data['longitude'] = np.arange(4.0, 7.5, 0.5)
        self.catalogue.data['latitude'] = np.arange(4.0, 7.5, 0.5)
        self.catalogue.data['depth'] = np.ones(7, dtype=float)
        # Simple case with nodes inside, outside and on the border of polygon
        selector0 = CatalogueSelector(self.catalogue)
        test_cat1 = selector0.within_polygon(polygon0)
        self.assertTrue(np.allclose(test_cat1.data['longitude'],
                                    np.array([5.0, 5.5, 6.0])))
        self.assertTrue(np.allclose(test_cat1.data['latitude'],
                                    np.array([5.0, 5.5, 6.0])))
        self.assertTrue(np.allclose(test_cat1.data['depth'],
                                    np.array([1.0, 1.0, 1.0])))
        # CASE 2: As case 1 with one of the inside nodes outside of the depths
        self.catalogue.data['depth'] = \
            np.array([1.0, 1.0, 1.0, 50.0, 1.0, 1.0, 1.0], dtype=float)
        selector0 = CatalogueSelector(self.catalogue)
        test_cat1 = selector0.within_polygon(polygon0, upper_depth=0.0,
                                             lower_depth=10.0)
        self.assertTrue(np.allclose(test_cat1.data['longitude'],
                                    np.array([5.0, 6.0])))
        self.assertTrue(np.allclose(test_cat1.data['latitude'],
                                    np.array([5.0, 6.0])))
        self.assertTrue(np.allclose(test_cat1.data['depth'],
                                    np.array([1.0])))

    def test_point_in_circular_distance(self):
        # Tests point in circular distance

        self.catalogue.data['longitude'] = np.arange(4.0, 7.5, 0.5)
        self.catalogue.data['latitude'] = np.arange(4.0, 7.5, 0.5)
        self.catalogue.data['depth'] = np.ones(7, dtype=float)
        test_point = Point(5.5, 5.5)
        test_mesh = self.catalogue.hypocentres_as_mesh()
        selector0 = CatalogueSelector(self.catalogue)
        # Within 10 km
        test_cat_10 = selector0.circular_distance_from_point(
            test_point, 10., distance_type='epicentral')
        np.testing.assert_array_equal(test_cat_10.data['longitude'],
                                      np.array([5.5]))
        np.testing.assert_array_equal(test_cat_10.data['latitude'],
                                      np.array([5.5]))
        np.testing.assert_array_equal(test_cat_10.data['depth'],
                                      np.array([1.0]))

        # Within 100 km
        test_cat_100 = selector0.circular_distance_from_point(
            test_point, 100., distance_type='epicentral')
        np.testing.assert_array_equal(test_cat_100.data['longitude'],
                                      np.array([5.0, 5.5, 6.0]))
        np.testing.assert_array_equal(test_cat_100.data['latitude'],
                                      np.array([5.0, 5.5, 6.0]))
        np.testing.assert_array_equal(test_cat_100.data['depth'],
                                      np.array([1.0, 1.0, 1.0]))

        # Within 1000 km
        test_cat_1000 = selector0.circular_distance_from_point(
            test_point, 1000., distance_type='epicentral')
        np.testing.assert_array_equal(test_cat_1000.data['longitude'],
                                      self.catalogue.data['longitude'])
        np.testing.assert_array_equal(test_cat_1000.data['latitude'],
                                      self.catalogue.data['latitude'])
        np.testing.assert_array_equal(test_cat_1000.data['depth'],
                                      self.catalogue.data['depth'])

    def test_cartesian_square_on_point(self):
        # Tests the cartesian square centres on point

        self.catalogue.data['longitude'] = np.arange(4.0, 7.5, 0.5)
        self.catalogue.data['latitude'] = np.arange(4.0, 7.5, 0.5)
        self.catalogue.data['depth'] = np.ones(7, dtype=float)
        test_point = Point(5.5, 5.5)
        test_mesh = self.catalogue.hypocentres_as_mesh()
        selector0 = CatalogueSelector(self.catalogue)
        # Within 10 km
        test_cat_10 = selector0.cartesian_square_centred_on_point(
            test_point, 10., distance_type='epicentral')
        np.testing.assert_array_equal(test_cat_10.data['longitude'],
                                      np.array([5.5]))
        np.testing.assert_array_equal(test_cat_10.data['latitude'],
                                      np.array([5.5]))
        np.testing.assert_array_equal(test_cat_10.data['depth'],
                                      np.array([1.0]))

        # Within 100 km
        test_cat_100 = selector0.cartesian_square_centred_on_point(
            test_point, 100., distance_type='epicentral')
        np.testing.assert_array_almost_equal(
            test_cat_100.data['longitude'], np.array([5.0, 5.5, 6.0]))
        np.testing.assert_array_almost_equal(
            test_cat_100.data['latitude'], np.array([5.0, 5.5, 6.0]))
        np.testing.assert_array_almost_equal(
            test_cat_100.data['depth'], np.array([1.0, 1.0, 1.0]))

        # Within 1000 km
        test_cat_1000 = selector0.cartesian_square_centred_on_point(
            test_point, 1000., distance_type='epicentral')
        np.testing.assert_array_almost_equal(
            test_cat_1000.data['longitude'], self.catalogue.data['longitude'])
        np.testing.assert_array_almost_equal(
            test_cat_1000.data['latitude'], self.catalogue.data['latitude'])
        np.testing.assert_array_almost_equal(
            test_cat_1000.data['depth'], self.catalogue.data['depth'])

    def test_within_joyner_boore_distance(self):
        # Tests the function to select within Joyner-Boore distance

        self.catalogue.data['longitude'] = np.arange(4.0, 7.5, 0.5)
        self.catalogue.data['latitude'] = np.arange(4.0, 7.5, 0.5)
        self.catalogue.data['depth'] = np.ones(7, dtype=float)
        selector0 = CatalogueSelector(self.catalogue)
        # Construct Fault
        trace0 = np.array([[5.5, 6.0], [5.5, 5.0]])
        fault_trace = Line([Point(trace0[i, 0], trace0[i, 1])
                           for i in range(0, 2)])

        # Simple fault with vertical dip
        fault0 = SimpleFaultSurface.from_fault_data(fault_trace, 0., 20., 90.,
                                                   1.)

        # Within 100 km
        test_cat_100 = selector0.within_joyner_boore_distance(fault0, 100.)
        np.testing.assert_array_almost_equal(
            test_cat_100.data['longitude'], np.array([5.0, 5.5, 6.0]))
        np.testing.assert_array_almost_equal(
            test_cat_100.data['latitude'], np.array([5.0, 5.5, 6.0]))
        np.testing.assert_array_almost_equal(
            test_cat_100.data['depth'], np.array([1.0, 1.0, 1.0]))

        # Simple fault with 30 degree dip
        fault0 = SimpleFaultSurface.from_fault_data(
            fault_trace, 0., 20., 30., 1.)

        # Within 100 km
        test_cat_100 = selector0.within_joyner_boore_distance(fault0, 100.)
        np.testing.assert_array_almost_equal(
            test_cat_100.data['longitude'], np.array([4.5, 5.0, 5.5, 6.0]))
        np.testing.assert_array_almost_equal(
            test_cat_100.data['latitude'], np.array([4.5, 5.0, 5.5, 6.0]))
        np.testing.assert_array_almost_equal(
            test_cat_100.data['depth'], np.array([1.0, 1.0, 1.0, 1.0]))

    def test_within_rupture_distance(self):
        # Tests the function to select within Joyner-Boore distance

        self.catalogue.data['longitude'] = np.arange(4.0, 7.5, 0.5)
        self.catalogue.data['latitude'] = np.arange(4.0, 7.5, 0.5)
        self.catalogue.data['depth'] = np.ones(7, dtype=float)
        selector0 = CatalogueSelector(self.catalogue)
        # Construct Fault
        trace0 = np.array([[5.5, 6.0], [5.5, 5.0]])
        fault_trace = Line([Point(trace0[i, 0], trace0[i, 1])
                           for i in range(0, 2)])

        # Simple fault with vertical dip
        fault0 = SimpleFaultSurface.from_fault_data(fault_trace, 0., 20., 90.,
                                                   1.)

        # Within 100 km
        test_cat_100 = selector0.within_rupture_distance(fault0, 100.)
        np.testing.assert_array_almost_equal(
            test_cat_100.data['longitude'], np.array([5.0, 5.5, 6.0]))
        np.testing.assert_array_almost_equal(
            test_cat_100.data['latitude'], np.array([5.0, 5.5, 6.0]))
        np.testing.assert_array_almost_equal(
            test_cat_100.data['depth'], np.array([1.0, 1.0, 1.0]))

        # Simple fault with 30 degree dip
        fault0 = SimpleFaultSurface.from_fault_data(
            fault_trace, 0., 20., 30., 1.)

        # Within 100 km
        test_cat_100 = selector0.within_rupture_distance(fault0, 100.)
        np.testing.assert_array_almost_equal(
            test_cat_100.data['longitude'], np.array([4.5, 5.0, 5.5, 6.0]))
        np.testing.assert_array_almost_equal(
            test_cat_100.data['latitude'], np.array([4.5, 5.0, 5.5, 6.0]))
        np.testing.assert_array_almost_equal(
            test_cat_100.data['depth'], np.array([1.0, 1.0, 1.0, 1.0]))

    def test_select_within_time(self):
        # Tests the function to select within a time period

        self.catalogue.data['year'] = np.arange(1900, 2010, 20)
        self.catalogue.data['month'] = np.arange(1, 12, 2)
        self.catalogue.data['day'] = np.ones(6, dtype=int)
        self.catalogue.data['hour'] = np.ones(6, dtype=int)
        self.catalogue.data['minute'] = np.zeros(6, dtype=int)
        self.catalogue.data['second'] = np.ones(6, dtype=float)

        selector0 = CatalogueSelector(self.catalogue)

        # Start time and End time not defined
        test_cat_1 = selector0.within_time_period()
        self._compare_time_data_dictionaries(test_cat_1.data,
                                             self.catalogue.data)

        # Start time defined - end time not defined
        begin_time = datetime.datetime(1975, 1, 1, 0, 0, 0, 0)
        expected_data = {'year': np.array([1980, 2000]),
                         'month': np.array([9, 11]),
                         'day': np.array([1, 1]),
                         'hour': np.array([1, 1]),
                         'minute': np.array([0, 0]),
                         'second': np.array([1., 1.])}

        test_cat_1 = selector0.within_time_period(start_time=begin_time)
        self._compare_time_data_dictionaries(expected_data, test_cat_1.data)


        # Test 3 - Start time not defined, end-time defined
        finish_time = datetime.datetime(1965, 1, 1, 0, 0, 0, 0)
        expected_data = {'year': np.array([1900, 1920, 1940, 1960]),
                         'month': np.array([1, 3, 5, 7]),
                         'day': np.array([1, 1, 1, 1]),
                         'hour': np.array([1, 1, 1, 1]),
                         'minute': np.array([0, 0, 0, 0]),
                         'second': np.array([1., 1., 1., 1.])}

        test_cat_1 = selector0.within_time_period(end_time=finish_time)
        self._compare_time_data_dictionaries(expected_data, test_cat_1.data)

        # Test 4 - both start time and end-time defined
        begin_time = datetime.datetime(1935, 1, 1, 0, 0, 0, 0)
        finish_time = datetime.datetime(1995, 1, 1, 0, 0, 0, 0)
        expected_data = {'year': np.array([1940, 1960, 1980]),
                         'month': np.array([5, 7, 9]),
                         'day': np.array([1, 1, 1]),
                         'hour': np.array([1, 1, 1]),
                         'minute': np.array([0, 0, 0]),
                         'second': np.array([1., 1., 1.])}

        test_cat_1 = selector0.within_time_period(begin_time, finish_time)
        self._compare_time_data_dictionaries(expected_data, test_cat_1.data)

    def _compare_time_data_dictionaries(self, expected, modelled):
        '''
        Compares the relevant time and date information in the catalogue
        data dictionaries
        '''
        time_keys = ['year', 'month', 'day', 'hour', 'minute', 'second']

        for key in time_keys:
            # The second value is a float - all others are integers
            if 'second' in key:
                np.testing.assert_array_almost_equal(expected[key],
                                                     modelled[key])
            else:
                np.testing.assert_array_equal(expected[key], modelled[key])

    def test_select_within_depth_range(self):
        # Tests the function to select within the depth range

        # Setup function
        self.catalogue = Catalogue()
        self.catalogue.data['depth'] = np.array([5., 15., 25., 35., 45.])

        selector0 = CatalogueSelector(self.catalogue)
        # Test case 1: No limits specified - all catalogue valid
        test_cat_1 = selector0.within_depth_range()
        np.testing.assert_array_almost_equal(test_cat_1.data['depth'],
                                             self.catalogue.data['depth'])

        # Test case 2: Lower depth limit specfied only
        test_cat_1 = selector0.within_depth_range(lower_depth=30.)
        np.testing.assert_array_almost_equal(test_cat_1.data['depth'],
                                             np.array([5., 15., 25.]))
        # Test case 3: Upper depth limit specified only
        test_cat_1 = selector0.within_depth_range(upper_depth=20.)
        np.testing.assert_array_almost_equal(test_cat_1.data['depth'],
                                             np.array([25., 35., 45.]))

        # Test case 4: Both depth limits specified
        test_cat_1 = selector0.within_depth_range(upper_depth=20.,
                                                  lower_depth=40.)
        np.testing.assert_array_almost_equal(test_cat_1.data['depth'],
                                             np.array([25., 35.]))


    def test_select_within_magnitude_range(self):
        '''
        Tests the function to select within the magnitude range
        '''
        # Setup function
        self.catalogue = Catalogue()
        self.catalogue.data['magnitude'] = np.array([4., 5., 6., 7., 8.])

        selector0 = CatalogueSelector(self.catalogue)
        # Test case 1: No limits specified - all catalogue valid
        test_cat_1 = selector0.within_magnitude_range()
        np.testing.assert_array_almost_equal(test_cat_1.data['magnitude'],
                                             self.catalogue.data['magnitude'])

        # Test case 2: Lower depth limit specfied only
        test_cat_1 = selector0.within_magnitude_range(lower_mag=5.5)
        np.testing.assert_array_almost_equal(test_cat_1.data['magnitude'],
                                             np.array([6., 7., 8.]))
        # Test case 3: Upper depth limit specified only
        test_cat_1 = selector0.within_magnitude_range(upper_mag=5.5)
        np.testing.assert_array_almost_equal(test_cat_1.data['magnitude'],
                                             np.array([4., 5.]))

        # Test case 4: Both depth limits specified
        test_cat_1 = selector0.within_magnitude_range(upper_mag=7.5,
                                                      lower_mag=5.5)
        np.testing.assert_array_almost_equal(test_cat_1.data['magnitude'],
                                             np.array([6., 7.]))

    def test_create_cluster_set(self):
        """

        """
        # Setup function
        self.catalogue = Catalogue()
        self.catalogue.data["EventID"] = np.array([1, 2, 3, 4, 5, 6])
        self.catalogue.data["magnitude"] = np.array([7.0, 5.0, 5.0,
                                                     5.0, 4.0, 4.0])
        selector0 = CatalogueSelector(self.catalogue)
        vcl = np.array([0, 1, 1, 1, 2, 2])
        cluster_set = selector0.create_cluster_set(vcl)
        np.testing.assert_array_equal(cluster_set[0].data["EventID"],
                                      np.array([1]))
        np.testing.assert_array_almost_equal(cluster_set[0].data["magnitude"],
                                             np.array([7.0]))
        np.testing.assert_array_equal(cluster_set[1].data["EventID"],
                                      np.array([2, 3, 4]))
        np.testing.assert_array_almost_equal(cluster_set[1].data["magnitude"],
                                             np.array([5.0, 5.0, 5.0]))
        np.testing.assert_array_equal(cluster_set[2].data["EventID"],
                                      np.array([5, 6]))
        np.testing.assert_array_almost_equal(cluster_set[2].data["magnitude"],
                                             np.array([4.0, 4.0])) 
