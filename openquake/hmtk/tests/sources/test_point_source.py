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
Tests the construction and methods within the :class:
openquake.hmtk.sources.point_source.mtkPointSource
'''

import unittest
import warnings
import numpy as np
from copy import deepcopy
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.source.point import PointSource
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.mfd.truncated_gr import TruncatedGRMFD
from openquake.hazardlib.scalerel.wc1994 import WC1994
from openquake.hmtk.sources.point_source import mtkPointSource
from openquake.hmtk.seismicity.catalogue import Catalogue
from openquake.hmtk.seismicity.selector import CatalogueSelector


TOM = PoissonTOM(50.0)
SOURCE_ATTRIBUTES = ['mfd', 'name', 'geometry', 'nodal_plane_dist', 'typology',
                     'upper_depth', 'catalogue', 'rupt_aspect_ratio',
                     'lower_depth', 'id', 'hypo_depth_dist', 'mag_scale_rel',
                     'trt']


class TestPointSource(unittest.TestCase):
    '''
    Tester class for openquake.hmtk.sources.point_source.mtkAreaSource
    '''
    def setUp(self):
        warnings.simplefilter("ignore")  # Suppress warnings during test
        self.catalogue = Catalogue()
        self.point_source = mtkPointSource('101', 'A Point Source')

    def test_point_source_instantiation(self):
        # Tests the core (minimal) instantiation of the class

        # Check source has all required attributes
        self.assertListEqual(sorted(self.point_source.__dict__),
                             sorted(SOURCE_ATTRIBUTES))
        self.assertEqual(self.point_source.id, '101')
        self.assertEqual(self.point_source.name, 'A Point Source')
        self.assertEqual(self.point_source.typology, 'Point')

    def test_depth_checker(self):
        # Tests the checker to ensure correct depth values
        # Bad Case - Negative upper depths
        with self.assertRaises(ValueError) as ver:
            self.point_source._check_seismogenic_depths(-1.0, 20.)
        self.assertEqual(str(ver.exception),
                         'Upper seismogenic depth must be greater than or '
                         'equal to 0.0!')

        # Bad Case - Lower depth smaller than upper depth
        with self.assertRaises(ValueError) as ver:
            self.point_source._check_seismogenic_depths(30., 20.)
        self.assertEqual(str(ver.exception),
                         'Lower seismogenic depth must take a greater value '
                         'than upper seismogenic depth')
        # Good Case
        self.point_source._check_seismogenic_depths(0.0, 20.)
        self.assertAlmostEqual(0.0, self.point_source.upper_depth)
        self.assertAlmostEqual(20.0, self.point_source.lower_depth)

    def test_geometry_inputs(self):
        # Tests the geometry definitions
        simple_point = Point(2.0, 3.0)
        simple_point_array = np.array([2.0, 3.0])

        # Using nhlib.geo.polygon.Polygon class as input
        self.point_source.create_geometry(simple_point, 0.0, 30.0)
        # Check that geometry is an instance of nhlib.geo.polygon.Polygon
        self.assertTrue(isinstance(self.point_source.geometry, Point))
        self.assertAlmostEqual(self.point_source.geometry.longitude, 2.0)
        self.assertAlmostEqual(self.point_source.geometry.latitude, 3.0)
        self.assertAlmostEqual(self.point_source.geometry.depth, 0.0)
        self.assertAlmostEqual(0.0, self.point_source.upper_depth)
        self.assertAlmostEqual(30.0, self.point_source.lower_depth)

        self.point_source = mtkPointSource('101', 'A Point Source')
        # Using numpy array as input
        self.point_source.create_geometry(simple_point_array, 0.0, 30.0)
        self.assertTrue(isinstance(self.point_source.geometry, Point))
        self.assertAlmostEqual(self.point_source.geometry.longitude, 2.0)
        self.assertAlmostEqual(self.point_source.geometry.latitude, 3.0)
        self.assertAlmostEqual(self.point_source.geometry.depth, 0.0)
        self.assertAlmostEqual(0.0, self.point_source.upper_depth)
        self.assertAlmostEqual(30.0, self.point_source.lower_depth)

        # For any other input type - check ValueError is raised
        self.point_source = mtkPointSource('101', 'A Point Source')
        with self.assertRaises(ValueError) as ver:
            self.point_source.create_geometry('a bad input', 0.0, 30.0)
        self.assertEqual(str(ver.exception),
                         'Unrecognised or unsupported geometry definition')

    def test_select_events_in_circular_distance(self):
        # Basic test of method to select events within a distance of the point
        self.point_source = mtkPointSource('101', 'A Point Source')
        simple_point = Point(4.5, 4.5)

        self.catalogue.data['eventID'] = np.arange(0, 7, 1)
        self.catalogue.data['longitude'] = np.arange(4.0, 7.5, 0.5)
        self.catalogue.data['latitude'] = np.arange(4.0, 7.5, 0.5)
        self.catalogue.data['depth'] = np.ones(7, dtype=float)
        # Simple Case - 100 km epicentral distance
        selector0 = CatalogueSelector(self.catalogue)
        self.point_source.create_geometry(simple_point, 0., 30.)
        self.point_source.select_catalogue_within_distance(selector0, 100.,
                                                           'epicentral')
        np.testing.assert_array_almost_equal(
            np.array([0, 1, 2]),
            self.point_source.catalogue.data['eventID'])
        np.testing.assert_array_almost_equal(
            np.array([4., 4.5, 5.]),
            self.point_source.catalogue.data['longitude'])

        np.testing.assert_array_almost_equal(
            np.array([4., 4.5, 5.]),
            self.point_source.catalogue.data['latitude'])

        np.testing.assert_array_almost_equal(
            np.array([1., 1., 1.]),
            self.point_source.catalogue.data['depth'])

        # Simple case - 100 km hypocentral distance (hypocentre at 70 km)
        self.point_source.select_catalogue_within_distance(
            selector0, 100., 'hypocentral', 70.)

        np.testing.assert_array_almost_equal(
            np.array([1]),
            self.point_source.catalogue.data['eventID'])

        np.testing.assert_array_almost_equal(
            np.array([4.5]),
            self.point_source.catalogue.data['longitude'])

        np.testing.assert_array_almost_equal(
            np.array([4.5]),
            self.point_source.catalogue.data['latitude'])

        np.testing.assert_array_almost_equal(
            np.array([1.]),
            self.point_source.catalogue.data['depth'])

    def test_select_events_within_cell(self):
        # Tests the selection of events within a cell centred on the point
        self.point_source = mtkPointSource('101', 'A Point Source')
        simple_point = Point(4.5, 4.5)
        self.point_source.create_geometry(simple_point, 0., 30.)
        self.catalogue = Catalogue()
        self.catalogue.data['eventID'] = np.arange(0, 7, 1)
        self.catalogue.data['longitude'] = np.arange(4.0, 7.5, 0.5)
        self.catalogue.data['latitude'] = np.arange(4.0, 7.5, 0.5)
        self.catalogue.data['depth'] = np.ones(7, dtype=float)
        selector0 = CatalogueSelector(self.catalogue)

        # Simple case - 200 km by 200 km cell centred on point
        self.point_source.select_catalogue_within_cell(selector0, 100.)
        np.testing.assert_array_almost_equal(
            np.array([4., 4.5, 5.]),
            self.point_source.catalogue.data['longitude'])

        np.testing.assert_array_almost_equal(
            np.array([4., 4.5, 5.]),
            self.point_source.catalogue.data['latitude'])

        np.testing.assert_array_almost_equal(
            np.array([1., 1., 1.]),
            self.point_source.catalogue.data['depth'])

    def test_select_catalogue(self):
        # Tests the select_catalogue function - essentially a wrapper to the
        # two selection functions
        self.point_source = mtkPointSource('101', 'A Point Source')
        simple_point = Point(4.5, 4.5)
        self.point_source.create_geometry(simple_point, 0., 30.)

        # Bad case - no events in catalogue
        self.catalogue = Catalogue()
        selector0 = CatalogueSelector(self.catalogue)

        with self.assertRaises(ValueError) as ver:
            self.point_source.select_catalogue(selector0, 100.)
            self.assertEqual(str(ver.exception),
                             'No events found in catalogue!')

        # Create a catalogue
        self.catalogue = Catalogue()
        self.catalogue.data['eventID'] = np.arange(0, 7, 1)
        self.catalogue.data['longitude'] = np.arange(4.0, 7.5, 0.5)
        self.catalogue.data['latitude'] = np.arange(4.0, 7.5, 0.5)
        self.catalogue.data['depth'] = np.ones(7, dtype=float)
        selector0 = CatalogueSelector(self.catalogue)

        # To ensure that square function is called - compare against direct
        # instance
        # First implementation - compare select within distance
        self.point_source.select_catalogue_within_distance(selector0,
                                                           100.,
                                                           'epicentral')
        expected_catalogue = deepcopy(self.point_source.catalogue)
        self.point_source.catalogue = None  # Reset catalogue
        self.point_source.select_catalogue(selector0, 100., 'circle')
        np.testing.assert_array_equal(
            self.point_source.catalogue.data['eventID'],
            expected_catalogue.data['eventID'])

        # Second implementation  - compare select within cell
        expected_catalogue = None
        self.point_source.select_catalogue_within_cell(selector0, 150.)
        expected_catalogue = deepcopy(self.point_source.catalogue)
        self.point_source.catalogue = None  # Reset catalogue
        self.point_source.select_catalogue(selector0, 150., 'square')
        np.testing.assert_array_equal(
            self.point_source.catalogue.data['eventID'],
            expected_catalogue.data['eventID'])

        # Finally ensure error is raised when input is neither
        # 'circle' nor 'square'
        with self.assertRaises(ValueError) as ver:
            self.point_source.select_catalogue(selector0, 100., 'bad input')
        self.assertEqual(str(ver.exception),
                         'Unrecognised selection type for point source!')

    def test_create_oq_hazardlib_point_source(self):
        # Tests the function to create a point source model
        mfd1 = TruncatedGRMFD(5.0, 8.0, 0.1, 3.0, 1.0)
        self.point_source = mtkPointSource(
            '001',
            'A Point Source',
            trt='Active Shallow Crust',
            geometry=Point(10., 10.),
            upper_depth=0.,
            lower_depth=20.,
            mag_scale_rel=None,
            rupt_aspect_ratio=1.0,
            mfd=mfd1,
            nodal_plane_dist=None,
            hypo_depth_dist=None)
        test_source = self.point_source.create_oqhazardlib_source(
            TOM, 2.0, True)
        self.assertIsInstance(test_source, PointSource)
        self.assertIsInstance(test_source.mfd, TruncatedGRMFD)
        self.assertAlmostEqual(test_source.mfd.b_val, 1.0)
        self.assertIsInstance(test_source.nodal_plane_distribution, PMF)
        self.assertIsInstance(test_source.hypocenter_distribution, PMF)
        self.assertIsInstance(test_source.magnitude_scaling_relationship,
                              WC1994)

    def tearDown(self):
        warnings.resetwarnings()
