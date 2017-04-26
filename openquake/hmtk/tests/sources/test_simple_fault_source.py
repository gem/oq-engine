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
openquake.hmtk.sources.simple_fault_source.mtkSimpleFaultSource
'''

import unittest
import warnings
import numpy as np
from openquake.hazardlib.geo import point, line
from openquake.hazardlib.geo.surface.simple_fault import SimpleFaultSurface
from openquake.hazardlib.source.simple_fault import SimpleFaultSource
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.scalerel.wc1994 import WC1994
from openquake.hazardlib.mfd.truncated_gr import TruncatedGRMFD
from openquake.hmtk.sources.simple_fault_source import mtkSimpleFaultSource
from openquake.hmtk.seismicity.catalogue import Catalogue
from openquake.hmtk.seismicity.selector import CatalogueSelector

TOM = PoissonTOM(50.0)

SOURCE_ATTRIBUTES = ['mfd', 'name', 'geometry', 'rake', 'fault_trace',
                     'typology', 'upper_depth', 'catalogue',
                     'rupt_aspect_ratio', 'lower_depth', 'id',
                     'mag_scale_rel', 'dip', 'trt']


class TestSimpleFaultSource(unittest.TestCase):
    '''
    Test module for the openquake.hmtk.sources.simple_fault_source.mtkSimpleFaultSource
    class
    '''
    def setUp(self):
        warnings.simplefilter("ignore")
        self.catalogue = Catalogue()
        self.fault_source = None

    def test_simple_fault_instantiation(self):
        # Tests the core instantiation of the module
        # Simple instantiation - minimual data
        self.fault_source = mtkSimpleFaultSource('101', 'A simple fault')
        self.assertListEqual(sorted(self.fault_source.__dict__),
                             sorted(SOURCE_ATTRIBUTES))
        self.assertEqual(self.fault_source.id, '101')
        self.assertEqual(self.fault_source.name, 'A simple fault')
        self.assertEqual(self.fault_source.typology, 'SimpleFault')

        # Simple instantiation with dip
        self.fault_source = mtkSimpleFaultSource('101',
                                                 'A simple fault',
                                                 dip=60.)
        self.assertAlmostEqual(self.fault_source.dip, 60.)
        # Instantiation with an invalid dip range - raises AssertionError
        self.assertRaises(AssertionError,
                          mtkSimpleFaultSource,
                          identifier='101',
                          name='A simple fault',
                          dip=95.)

    def test_check_seismogenic_depths(self):
        # Tests the check on seismogenic depths - behaviour different from
        # equivalent function in area and point sources as simple faults cannot
        # have an undefined lower seismogenic depth, and upper seismogenic
        # depth with default to 0 if undefined

        self.fault_source = mtkSimpleFaultSource('101', 'A simple fault')
        # Test 1 - Good case - upper and lower seismogenic depths defined
        self.fault_source._check_seismogenic_depths(2.0, 30.0)
        self.assertAlmostEqual(self.fault_source.upper_depth, 2.)
        self.assertAlmostEqual(self.fault_source.lower_depth, 30.)

        # Test 2 - Acceptable case - upper depth not defined, lower depth given
        self.fault_source._check_seismogenic_depths(None, 30.0)
        self.assertAlmostEqual(self.fault_source.upper_depth, 0.)
        self.assertAlmostEqual(self.fault_source.lower_depth, 30.)

        # Test 3 - Raises error when no lower depth is defined
        with self.assertRaises(ValueError) as ver:
            self.fault_source._check_seismogenic_depths(2., None)
        self.assertEqual(str(ver.exception),
                         'Lower seismogenic depth must be defined for '
                         'simple fault source!')
        # Test 4 - Raises error when lower depth is less than upper depth
        with self.assertRaises(ValueError) as ver:
            self.fault_source._check_seismogenic_depths(upper_depth=20.,
                                                        lower_depth=15.)
        self.assertEqual(str(ver.exception),
                         'Lower seismogenic depth must take a greater value'
                         ' than upper seismogenic depth')

        # Test 4 - Raises value error when upper depth is less than 0.
        with self.assertRaises(ValueError) as ver:
            self.fault_source._check_seismogenic_depths(upper_depth=-0.5,
                                                        lower_depth=15.)
        self.assertEqual(str(ver.exception),
                         'Upper seismogenic depth must be greater than or '
                         'equal to 0.0!')

    def test_create_fault_geometry(self):
        # Tests the creation of the fault geometry. Testing only behaviour
        # for creating SimpleFaultSurface classes - not the values in the
        # class (assumes nhlib implementation is correct)
        # Case 1 - trace input as instance of nhlib.geo.line.Line class
        self.fault_source = mtkSimpleFaultSource('101', 'A simple fault')
        trace_as_line = line.Line([point.Point(2.0, 3.0),
                                   point.Point(3.0, 2.0)])
        self.fault_source.create_geometry(trace_as_line, 60., 0., 30.)
        self.assertIsInstance(self.fault_source.geometry,
                              SimpleFaultSurface)

        # Case 2 - trace input as numpy array
        trace_as_array = np.array([[2.0, 3.0], [3.0, 2.0]])
        self.fault_source = mtkSimpleFaultSource('101', 'A simple fault')
        self.fault_source.create_geometry(trace_as_array, 60., 0., 30.)
        self.assertIsInstance(self.fault_source.geometry,
                              SimpleFaultSurface)
        # Case 3 - raises error when something else is input
        with self.assertRaises(ValueError) as ver:
            self.fault_source.create_geometry('a bad input!', 60., 0., 30.)
        self.assertEqual(str(ver.exception),
                         'Unrecognised or unsupported geometry definition')

    def test_select_within_fault_distance(self):
        # Tests the selection of events within a distance from the fault
        # Set up catalouge
        self.catalogue = Catalogue()
        self.catalogue.data['longitude'] = np.arange(0., 5.5, 0.5)
        self.catalogue.data['latitude'] = np.arange(0., 5.5, 0.5)
        self.catalogue.data['depth'] = np.zeros(11, dtype=float)
        self.catalogue.data['eventID'] = np.arange(0, 11, 1)
        self.fault_source = mtkSimpleFaultSource('101', 'A simple fault')
        trace_as_line = line.Line([point.Point(2.0, 3.0),
                                   point.Point(3.0, 2.0)])
        self.fault_source.create_geometry(trace_as_line, 30., 0., 30.)
        selector0 = CatalogueSelector(self.catalogue)

        # Test 1 - simple case Joyner-Boore distance
        self.fault_source.select_catalogue(selector0, 40.)
        np.testing.assert_array_almost_equal(
            np.array([2., 2.5]),
            self.fault_source.catalogue.data['longitude'])
        np.testing.assert_array_almost_equal(
            np.array([2., 2.5]),
            self.fault_source.catalogue.data['latitude'])

        # Test 2 - simple case Rupture distance
        self.fault_source.catalogue = None
        self.fault_source.select_catalogue(selector0, 40., 'rupture')
        np.testing.assert_array_almost_equal(
            np.array([2.5]),
            self.fault_source.catalogue.data['longitude'])
        np.testing.assert_array_almost_equal(
            np.array([2.5]),
            self.fault_source.catalogue.data['latitude'])

        # Test 3 - for vertical fault ensure that Joyner-Boore distance
        # behaviour is the same as for rupture distance
        fault1 = mtkSimpleFaultSource('102', 'A vertical fault')
        fault1.create_geometry(trace_as_line, 90., 0., 30.)
        self.fault_source.create_geometry(trace_as_line, 90., 0., 30.)

        # Joyner-Boore
        self.fault_source.select_catalogue(selector0, 40.)
        # Rupture
        fault1.select_catalogue(selector0, 40., 'rupture')
        np.testing.assert_array_almost_equal(
            self.fault_source.catalogue.data['longitude'],
            fault1.catalogue.data['longitude'])
        np.testing.assert_array_almost_equal(
            self.fault_source.catalogue.data['latitude'],
            fault1.catalogue.data['latitude'])

        # The usual test to ensure error is raised when no events in catalogue
        self.catalogue = Catalogue()
        selector0 = CatalogueSelector(self.catalogue)
        with self.assertRaises(ValueError) as ver:
            self.fault_source.select_catalogue(selector0, 40.0)
        self.assertEqual(str(ver.exception),
                         'No events found in catalogue!')

    def test_create_oqhazardlib_source(self):
        # Tests to ensure the hazardlib source is created
        trace = line.Line([point.Point(10., 10.), point.Point(11., 10.)])
        mfd1 = TruncatedGRMFD(5.0, 8.0, 0.1, 3.0, 1.0)
        self.fault_source = mtkSimpleFaultSource(
            '001',
            'A Fault Source',
            trt='Active Shallow Crust',
            geometry=None,
            dip=90.,
            upper_depth=0.,
            lower_depth=20.,
            mag_scale_rel=None,
            rupt_aspect_ratio=1.0,
            mfd=mfd1,
            rake=0.)
        self.fault_source.create_geometry(trace, 90., 0., 20., 1.0)
        test_source = self.fault_source.create_oqhazardlib_source(TOM,
                                                                  2.0,
                                                                  True)
        self.assertIsInstance(test_source, SimpleFaultSource)
        self.assertIsInstance(test_source.mfd, TruncatedGRMFD)
        self.assertAlmostEqual(test_source.mfd.b_val, 1.0)
        self.assertIsInstance(test_source.magnitude_scaling_relationship,
                              WC1994)

    def tearDown(self):
        warnings.resetwarnings()
