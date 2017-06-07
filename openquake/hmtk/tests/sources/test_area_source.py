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
openquake.hmtk.sources.area_source.mtkAreaSource
'''

import unittest
import warnings
import numpy as np
from openquake.hazardlib.geo import point, polygon
from openquake.hazardlib.source.area import AreaSource
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.mfd.truncated_gr import TruncatedGRMFD
from openquake.hazardlib.scalerel.wc1994 import WC1994
from openquake.hmtk.sources.area_source import mtkAreaSource
from openquake.hmtk.seismicity.catalogue import Catalogue
from openquake.hmtk.seismicity.selector import CatalogueSelector

TOM = PoissonTOM(50.0)
SOURCE_ATTRIBUTES = ['mfd', 'name', 'geometry', 'nodal_plane_dist', 'typology',
                     'upper_depth', 'catalogue', 'rupt_aspect_ratio',
                     'lower_depth', 'id', 'hypo_depth_dist', 'mag_scale_rel',
                     'trt']


class TestAreaSource(unittest.TestCase):
    '''
    Tester class for openquake.hmtk.sources.area_source.mtkAreaSource
    '''
    def setUp(self):
        warnings.simplefilter("ignore")
        self.catalogue = Catalogue()
        self.area_source = mtkAreaSource('101', 'A Source')

    def test_area_source_instantiation(self):
        # Tests the core (minimal) instantiation of the class
        # Check source has all required attributes
        self.assertListEqual(sorted(self.area_source.__dict__),
                             sorted(SOURCE_ATTRIBUTES))
        self.assertEqual(self.area_source.id, '101')
        self.assertEqual(self.area_source.name, 'A Source')
        self.assertEqual(self.area_source.typology, 'Area')

    def test_depth_checker(self):
        # Tests the checker to ensure correct depth values
        # Bad Case - Negative upper depths
        with self.assertRaises(ValueError) as ver:
            self.area_source._check_seismogenic_depths(-1.0, 20.)
        self.assertEqual(str(ver.exception),
                         'Upper seismogenic depth must be greater than or '
                         'equal to 0.0!')

        # Bad Case - Lower depth smaller than upper depth
        with self.assertRaises(ValueError) as ver:
            self.area_source._check_seismogenic_depths(30., 20.)
        self.assertEqual(str(ver.exception),
                         'Lower seismogenic depth must take a greater value '
                         'than upper seismogenic depth')
        # Good Case
        self.area_source._check_seismogenic_depths(0.0, 20.)
        self.assertAlmostEqual(0.0, self.area_source.upper_depth)
        self.assertAlmostEqual(20.0, self.area_source.lower_depth)

    def test_geometry_inputs(self):
        # Tests the geometry definition
        simple_polygon = polygon.Polygon([point.Point(2.0, 3.0),
                                          point.Point(3.0, 3.0),
                                          point.Point(3.0, 2.0),
                                          point.Point(2.0, 2.0)])

        simple_polygon_array = np.array([[2.0, 3.0],
                                         [3.0, 3.0],
                                         [3.0, 2.0],
                                         [2.0, 2.0]])
        # Using nhlib.geo.polygon.Polygon class as input
        self.area_source.create_geometry(simple_polygon, 0.0, 30.0)
        # Check that geometry is an instance of nhlib.geo.polygon.Polygon
        self.assertTrue(isinstance(self.area_source.geometry,
                                   polygon.Polygon))

        np.testing.assert_array_almost_equal(self.area_source.geometry.lons,
                                             np.array([2., 3., 3., 2.]))
        np.testing.assert_array_almost_equal(self.area_source.geometry.lats,
                                             np.array([3., 3., 2., 2.]))
        self.assertAlmostEqual(0.0, self.area_source.upper_depth)
        self.assertAlmostEqual(30.0, self.area_source.lower_depth)

        self.area_source = mtkAreaSource('101', 'A Source')
        # Using numpy array as input
        self.area_source.create_geometry(simple_polygon_array, 0.0, 30.0)
        self.assertTrue(isinstance(self.area_source.geometry,
                                   polygon.Polygon))

        # Check that geometry is an instance of nhlib.geo.polygon.Polygon
        np.testing.assert_array_almost_equal(self.area_source.geometry.lons,
                                             np.array([2., 3., 3., 2.]))
        np.testing.assert_array_almost_equal(self.area_source.geometry.lats,
                                             np.array([3., 3., 2., 2.]))

        self.assertAlmostEqual(0.0, self.area_source.upper_depth)
        self.assertAlmostEqual(30.0, self.area_source.lower_depth)

        # For any other input type - check ValueError is raised
        self.area_source = mtkAreaSource('101', 'A Source')
        with self.assertRaises(ValueError) as ver:
            self.area_source.create_geometry('a bad input', 0.0, 30.0)
        self.assertEqual(str(ver.exception),
                         'Unrecognised or unsupported geometry definition')

        # For numpy array with only two rows
        self.area_source = mtkAreaSource('101', 'A Source')
        simple_polygon_array = np.array([[2.0, 3.0],
                                         [3.0, 3.0]])
        with self.assertRaises(ValueError) as ver:
            self.area_source.create_geometry(simple_polygon_array, 0.0, 30.0)
        self.assertEqual(str(ver.exception),
                         'Incorrectly formatted polygon geometry - '
                         'needs three or more vertices')

    def test_select_events_in_source(self):
        # Basic test of method to select events from catalogue in polygon
        self.area_source = mtkAreaSource('101', 'A Source')
        simple_polygon = polygon.Polygon([point.Point(2.0, 3.0),
                                          point.Point(3.0, 3.0),
                                          point.Point(3.0, 2.0),
                                          point.Point(2.0, 2.0)])

        self.catalogue.data['eventID'] = np.arange(0, 7, 1)
        self.catalogue.data['longitude'] = np.arange(1.0, 4.5, 0.5)
        self.catalogue.data['latitude'] = np.arange(1.0, 4.5, 0.5)
        self.catalogue.data['depth'] = np.ones(7, dtype=float)
        # Simple Case - No buffer
        selector0 = CatalogueSelector(self.catalogue)
        self.area_source.create_geometry(simple_polygon, 0., 30.)
        self.area_source.select_catalogue(selector0, 0.)
        np.testing.assert_array_almost_equal(
            np.array([2., 2.5, 3.]),
            self.area_source.catalogue.data['longitude'])

        np.testing.assert_array_almost_equal(
            np.array([2., 2.5, 3.]),
            self.area_source.catalogue.data['latitude'])

        np.testing.assert_array_almost_equal(
            np.array([1., 1., 1.]),
            self.area_source.catalogue.data['depth'])

        # Simple case - dilated by 200 km (selects all)
        self.area_source.select_catalogue(selector0, 200.)
        np.testing.assert_array_almost_equal(
            np.array([1., 1.5, 2., 2.5, 3., 3.5, 4.0]),
            self.area_source.catalogue.data['longitude'])

        np.testing.assert_array_almost_equal(
            np.array([1., 1.5, 2., 2.5, 3., 3.5, 4.0]),
            self.area_source.catalogue.data['latitude'])

        np.testing.assert_array_almost_equal(
            np.ones(7, dtype=float),
            self.area_source.catalogue.data['depth'])

        # Bad case - no events in catalogue
        self.catalogue = Catalogue()
        selector0 = CatalogueSelector(self.catalogue)

        with self.assertRaises(ValueError) as ver:
            self.area_source.select_catalogue(selector0, 0.0)
            self.assertEqual(str(ver.exception),
                             'No events found in catalogue!')

    def test_create_oqhazardlib_source(self):
        # Define a complete source
        area_geom = polygon.Polygon([point.Point(10., 10.),
                                     point.Point(12., 10.),
                                     point.Point(12., 8.),
                                     point.Point(10., 8.)])
        mfd1 = TruncatedGRMFD(5.0, 8.0, 0.1, 3.0, 1.0)
        self.area_source = mtkAreaSource(
            '001',
            'A Point Source',
            trt='Active Shallow Crust',
            geometry=area_geom,
            upper_depth=0.,
            lower_depth=20.,
            mag_scale_rel=None,
            rupt_aspect_ratio=1.0,
            mfd=mfd1,
            nodal_plane_dist=None,
            hypo_depth_dist=None)
        test_source = self.area_source.create_oqhazardlib_source(TOM, 1.0,
                                                                 10.0, True)
        self.assertIsInstance(test_source, AreaSource)
        self.assertIsInstance(test_source.mfd, TruncatedGRMFD)
        self.assertAlmostEqual(test_source.mfd.b_val, 1.0)
        self.assertIsInstance(test_source.nodal_plane_distribution, PMF)
        self.assertIsInstance(test_source.hypocenter_distribution, PMF)
        self.assertIsInstance(test_source.magnitude_scaling_relationship,
                              WC1994)

    def tearDown(self):
        warnings.resetwarnings()
