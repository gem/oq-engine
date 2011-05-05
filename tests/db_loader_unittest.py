# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.

import unittest

from openquake.utils import db
from openquake.utils.db import loader as db_loader
from tests.utils import helpers

TEST_SRC_FILE = helpers.get_data_path('example-source-model.xml')
TEST_DB = 'openquake'
TEST_DB_USER = 'oq_pshai_etl'

class NrmlModelLoaderTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        """
        One-time setup stuff for this entire test case class.
        """
        super(NrmlModelLoaderTestCase, self).__init__(*args, **kwargs)
        self.engine = db.create_engine(TEST_DB, TEST_DB_USER)
        self.src_loader = db_loader.SourceModelLoader(TEST_SRC_FILE, self.engine) 
        self.sources = self.src_loader.src_reader.read()
        self.simple, self.complex, self.area, self.point = self.sources

    def test_get_simple_fault_surface(self):
        surface = db_loader.get_fault_surface(self.simple)
        surface_type = surface.__javaclass__.getName()
        self.assertEqual('org.opensha.sha.faultSurface.StirlingGriddedSurface',
            surface_type)

        # these surfaces are complex objects
        # there is a lot here we can test
        # for now, we only test the overall surface area
        # the test value is derived from our test data
        self.assertEqual(200.0, surface.getSurfaceArea())

    def test_get_complex_fault_surface(self):
        surface = db_loader.get_fault_surface(self.complex)
        surface_type = surface.__javaclass__.getName()
        self.assertEqual('org.opensha.sha.faultSurface.ApproxEvenlyGriddedSurface',
            surface_type)

        # as with the simple fault surface, we're only going to test
        # the surface area (for now)
        # the test value is derived from our test data
        self.assertEqual(126615.0, surface.getSurfaceArea())

    def test_get_fault_surface_raises(self):
        """
        Test that the :py:function:`openquake.utils.db.loader.get_fault_surface`
        function raises when passed an inappropriate source type.
        """
        self.assertRaises(ValueError, db_loader.get_fault_surface, self.area)
        self.assertRaises(ValueError, db_loader.get_fault_surface, self.point)


    def test_parse_mfd_simple_fault(self):

        expected = {
            'table': 'pshai.mfd_evd',
            'data': {
                'max_val': 6.9500000000000002,
                'total_cumulative_rate': 1.8988435199999998e-05,
                'min_val': 6.5499999999999998,
                'bin_size': 0.10000000000000009,
                'mfd_values': [
                    0.0010614989,
                    0.00088291626999999998,
                    0.00073437776999999999,
                    0.00061082879999999995,
                    0.00050806530000000003],
                'total_moment_rate': 281889786038447.25,
                'owner_id': None}}

        mfd = self.simple.getMfd()

        # Assume that this is an 'evenly discretized' MFD
        # We want to do this check so we know right away if our test data
        # has been altered.
        mfd_type = mfd.__javaclass__.getName()
        self.assertEqual('%s.IncrementalMagFreqDist' % db_loader.MFD_PACKAGE, mfd_type)

        # this is the dict we'll be passing to sqlalchemy to do the db insert
        mfd_insert = db_loader.parse_mfd(self.simple, mfd)

        self.assertEqual(expected, mfd_insert)


    def test_parse_mfd_complex_fault(self):
        expected = {
            'table': 'pshai.mfd_tgr',
            'data': {
                'b_val': 0.80000000000000004,
                'total_cumulative_rate': 4.933442096397671e-10,
                'min_val': 6.5499999999999998,
                'max_val': 8.9499999999999993,
                'total_moment_rate': 198544639016.43918,
                'a_val': 1.0,
                'owner_id': None}}

        mfd = self.complex.getMfd()

        mfd_type = mfd.__javaclass__.getName()
        self.assertEqual('%s.GutenbergRichterMagFreqDist' % db_loader.MFD_PACKAGE, mfd_type)

        mfd_insert = db_loader.parse_mfd(self.complex, mfd)

        self.assertEqual(expected, mfd_insert)


    @helpers.skipit
    def test_parse_simple_fault_src(self):

        stuff = db_loader.parse_simple_fault_src(self.simple)
        print "len(stuff) %s" % len(stuff)

        db_loader.write_simple_fault(self.engine, stuff)

        self.assertTrue(False)

    def test_serialize(self):
        results = None

        results = self.src_loader.serialize()

        print results

        self.assertTrue(False)
