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

"""
    Unittests for NRML/CSV input files loaders to the database
"""

import unittest

from openquake import java
from openquake import xml
from openquake.db import models
from openquake.utils.db import loader as db_loader

from tests.utils import helpers

TEST_SRC_FILE = helpers.get_data_path('example-source-model.xml')
TGR_MFD_TEST_FILE = helpers.get_data_path('one-simple-source-tgr-mfd.xml')

SIMPLE_FAULT_OUTLINE_WKT = \
'''SRID=4326;POLYGON((
-121.7467204676017 37.7997646326561 8.0,
 -121.75532031089188 37.805642887351446 8.0,
 -121.76392151966904 37.81152051630329 8.0,
 -121.77252409429458 37.817397519279645 8.0,
 -121.78112803513002 37.82327389604836 8.0,
 -121.78973334253678 37.82914964637729 8.0,
 -121.79834001687624 37.83502477003418 8.0,
 -121.80694805850989 37.840899266786685 8.0,
 -121.81555746779918 37.84677313640241 8.0,
 -121.82416824510553 37.85264637864887 8.0,
 -121.8327803907904 37.85851899329353 8.0,
 -121.8413939052153 37.86439098010374 8.0,
 -121.85000878874159 37.87026233884681 8.0,
 -121.85862504173078 37.87613306928992 8.0,
 -121.86724266454432 37.88200317120026 8.0,
 -121.8758616575437 37.88787264434489 8.0,
 -121.88448202109029 37.893741488490775 8.0,
 -121.89310375554568 37.89960970340485 8.0,
 -121.90172686127129 37.90547728885395 8.0,
 -121.91035133862856 37.91134424460486 8.0,
 -121.91897718797895 37.91721057042425 8.0,
 -121.92760440968398 37.92307626607874 8.0,
 -121.93623300410509 37.92894133133485 8.0,
 -121.94486297160377 37.93480576595908 8.0,
 -121.95349431254148 37.94066956971779 8.0,
 -121.96212702727968 37.9465327423773 8.0,
 -121.96212702727968 37.9465327423773 8.0,
 -121.95625230605336 37.9518957106558 8.615661475325659,
 -121.95037672704326 37.95725838678357 9.231322950651316,
 -121.94450029000527 37.96262077066159 9.846984425976975,
 -121.93862299469524 37.967982862190716 10.462645901302633,
 -121.932744840869 37.97334466127188 11.078307376628292,
 -121.92686582828229 37.978706167805875 11.69396885195395,
 -121.92098595669077 37.98406738169352 12.309630327279608,
 -121.91510522585013 37.98942830283558 12.925291802605265,
 -121.91510522585013 37.98942830283558 12.925291802605265,
 -121.90647626854076 37.98356513215041 12.925291802605265,
 -121.8978486843434 37.97770133036593 12.925291802605265,
 -121.88922247289645 37.97183689771583 12.925291802605265,
 -121.88059763383829 37.96597183443374 12.925291802605265,
 -121.87197416680722 37.96010614075318 12.925291802605265,
 -121.8633520714417 37.95423981690762 12.925291802605265,
 -121.85473134738001 37.94837286313044 12.925291802605265,
 -121.84611199426057 37.94250527965494 12.925291802605265,
 -121.83749401172173 37.936637066714376 12.925291802605265,
 -121.82887739940193 37.93076822454189 12.925291802605265,
 -121.82026215693944 37.92489875337057 12.925291802605265,
 -121.8116482839727 37.919028653433436 12.925291802605265,
 -121.80303578014009 37.913157924963414 12.925291802605265,
 -121.79442464507997 37.90728656819335 12.925291802605265,
 -121.7858148784307 37.90141458335603 12.925291802605265,
 -121.77720647983072 37.89554197068414 12.925291802605265,
 -121.76859944891841 37.88966873041036 12.925291802605265,
 -121.75999378533214 37.88379486276721 12.925291802605265,
 -121.7513894887103 37.87792036798718 12.925291802605265,
 -121.74278655869134 37.87204524630267 12.925291802605265,
 -121.73418499491355 37.86616949794599 12.925291802605265,
 -121.7255847970154 37.86029312314944 12.925291802605265,
 -121.71698596463537 37.854416122145146 12.925291802605265,
 -121.70838849741173 37.84853849516526 12.925291802605265,
 -121.69979239498296 37.84266024244175 12.925291802605265,
 -121.69979239498296 37.84266024244175 12.925291802605265,
 -121.70566138792265 37.83729930973308 12.309630327279608,
 -121.71152952784557 37.831938085823225 11.69396885195395,
 -121.71739681499416 37.82657657081076 11.078307376628292,
 -121.72326324961074 37.82121476479418 10.462645901302633,
 -121.72912883193759 37.815852667871994 9.846984425976975,
 -121.73499356221691 37.81049028014264 9.231322950651316,
 -121.7408574406909 37.805127601704555 8.615661475325659,
 -121.7467204676017 37.7997646326561 8.0))'''.replace('\n', '')

SIMPLE_FAULT_EDGE_WKT = \
    'SRID=4326;LINESTRING(-121.8229 37.7301 0.0, -122.0388 37.8771 0.0)'


class NrmlModelLoaderTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        """
        One-time setup stuff for this entire test case class.
        """
        super(NrmlModelLoaderTestCase, self).__init__(*args, **kwargs)

        self.src_reader = java.jclass('SourceModelReader')(
            TEST_SRC_FILE, db_loader.SourceModelLoader.DEFAULT_MFD_BIN_WIDTH)
        java.jvm().java.lang.System.setProperty("openquake.nrml.schema",
                                                xml.nrml_schema_file())
        self.sources = self.src_reader.read()
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
        self.assertEqual(
            'org.opensha.sha.faultSurface.ApproxEvenlyGriddedSurface',
            surface_type)

        # as with the simple fault surface, we're only going to test
        # the surface area (for now)
        # the test value is derived from our test data
        self.assertEqual(126615.0, surface.getSurfaceArea())

    def test_get_fault_surface_raises(self):
        """
        Test that the
        :py:function:`openquake.utils.db.loader.get_fault_surface` function
        raises when passed an inappropriate source type.
        """
        self.assertRaises(ValueError, db_loader.get_fault_surface, self.area)
        self.assertRaises(ValueError, db_loader.get_fault_surface, self.point)

    def test_parse_mfd_simple_fault(self):

        expected = models.MfdEvd(
            max_val=6.9500000000000002,
            total_cumulative_rate=1.8988435199999998e-05,
            min_val=6.5499999999999998,
            bin_size=0.10000000000000009,
            mfd_values=[
                0.0010614989,
                0.00088291626999999998,
                0.00073437776999999999,
                0.00061082879999999995,
                0.00050806530000000003],
            total_moment_rate=281889786038447.25)

        mfd = self.simple.getMfd()

        # Assume that this is an 'evenly discretized' MFD
        # We want to do this check so we know right away if our test data
        # has been altered.
        mfd_type = mfd.__javaclass__.getName()
        self.assertEqual(
            '%s.IncrementalMagFreqDist' % db_loader.MFD_PACKAGE, mfd_type)

        # this is the dict we'll be passing to Django to do the db insert
        mfd_insert = db_loader.parse_mfd(self.simple, mfd)

        helpers.assertModelAlmostEqual(self, expected, mfd_insert)

    def test_parse_mfd_complex_fault(self):
        expected = models.MfdTgr(
            b_val=0.80000000000000004,
            total_cumulative_rate=4.933442096397671e-10,
            min_val=6.5499999999999998,
            max_val=8.9499999999999993,
            total_moment_rate=198544639016.43918,
            a_val=1.0)

        mfd = self.complex.getMfd()

        mfd_type = mfd.__javaclass__.getName()
        self.assertEqual(
            '%s.GutenbergRichterMagFreqDist' % db_loader.MFD_PACKAGE, mfd_type)

        mfd_insert = db_loader.parse_mfd(self.complex, mfd)

        helpers.assertModelAlmostEqual(self, expected, mfd_insert)

    def test_parse_simple_fault_src(self):

        expected = (
            models.MfdEvd(
                max_val=6.9500000000000002,
                total_cumulative_rate=1.8988435199999998e-05,
                min_val=6.5499999999999998,
                bin_size=0.10000000000000009,
                mfd_values=[
                    0.0010614989, 0.00088291626999999998,
                    0.00073437776999999999, 0.00061082879999999995,
                    0.00050806530000000003],
                total_moment_rate=281889786038447.25,
                owner_id=None),
            models.SimpleFault(
                name='Mount Diablo Thrust',
                upper_depth=8.0,
                outline=SIMPLE_FAULT_OUTLINE_WKT,
                edge=SIMPLE_FAULT_EDGE_WKT,
                lower_depth=13.0,
                gid='src01',
                dip=38.0,
                description=None),
            models.Source(
                name='Mount Diablo Thrust',
                tectonic_region='active',
                rake=90.0,
                si_type='simple',
                gid='src01',
                hypocentral_depth=None,
                description=None))

        simple_data = db_loader.parse_simple_fault_src(self.simple)

        # Now we can test the rest of the data.
        helpers.assertModelAlmostEqual(self, expected[0], simple_data[0])
        helpers.assertModelAlmostEqual(self, expected[1], simple_data[1])
        helpers.assertModelAlmostEqual(self, expected[2], simple_data[2])

    def _serialize_test_helper(self, test_file, expected_tables):
        java.jvm().java.lang.System.setProperty("openquake.nrml.schema",
                                                xml.nrml_schema_file())
        src_loader = db_loader.SourceModelLoader(test_file)

        results = src_loader.serialize()

        # we should get a 3 item list of results
        self.assertEquals(3, len(results))

        # We expect there to have been 3 inserts.
        # The results are a list of dicts with a single key.
        # The key is the table name (including table space);
        # the value is the id (as an int) of the new record.

        # First, check that the results includes the 3 tables we expect:
        result_tables = [x.keys()[0] for x in results]

        self.assertEqual(expected_tables, result_tables)

        # Everything appears to be fine, but let's query the database to make
        # sure the expected records are there.
        # At this point, we're not going to check every single value; we just
        # want to make sure the records made it into the database.

        # list of tuples of (table name, id)
        table_id_pairs = [x.items()[0] for x in results]

        for table_name, record_id in table_id_pairs:
            table = db_loader.TABLE_MAP[table_name]

            # run a query against the table object to get a ResultProxy
            result_proxy = table.objects.filter(id=record_id).all()

            # there should be 1 record here
            self.assertEqual(1, len(result_proxy))

    def test_serialize(self):
        """
        Test serialization of a single simple fault source with an
        Evenly-Discretized MFD.
        """
        expected_tables = \
            ['hzrdi.mfd_evd', 'hzrdi.simple_fault', 'hzrdi.source']
        self._serialize_test_helper(TEST_SRC_FILE, expected_tables)

    def test_serialize_with_tgr_mfd(self):
        """
        Similar to test_serialize, except the test input data includes a
        Truncated Gutenberg-Richter MFD (so we exercise all paths inside the
        loader code).
        """
        expected_tables = \
            ['hzrdi.mfd_tgr', 'hzrdi.simple_fault', 'hzrdi.source']
        self._serialize_test_helper(TGR_MFD_TEST_FILE, expected_tables)


class CsvLoaderTestCase(unittest.TestCase):
    """
        Main class to execute tests about CSV
    """

    def setUp(self):
        csv_file = "ISC_snippet.csv"
        self.csv_path = helpers.get_data_path(csv_file)
        self.db_loader = db_loader.CsvModelLoader(self.csv_path)
        self.db_loader._read_model()
        self.csv_reader = self.db_loader.csv_reader

        # start from a clean state
        self._clean_db_data()

    def tearDown(self):
        # clean up after the test
        self._clean_db_data()

    def test_input_csv_is_of_the_right_len(self):
        # without the header line is 100
        expected_len = 100

        self.assertEqual(len(list(self.csv_reader)), expected_len)

    def test_csv_headers_are_correct(self):
        expected_headers = ['eventid', 'agency', 'identifier', 'year',
            'month', 'day', 'hour', 'minute', 'second', 'time_error',
            'longitude', 'latitude', 'semi_major', 'semi_minor', 'strike',
            'depth', 'depth_error', 'mw_val', 'mw_val_error',
            'ms_val', 'ms_val_error', 'mb_val', 'mb_val_error', 'ml_val',
            'ml_val_error']

        # it's not important that the headers of the csv are in the right or
        # wrong order, by using the DictReader it is sufficient to compare the
        # headers
        expected_headers = sorted(expected_headers)
        csv_headers = sorted(self.csv_reader.next().keys())
        self.assertEqual(csv_headers, expected_headers)

    def _retrieve_db_data(self):
        values = models.Catalog.objects.order_by('eventid').values(
            'id', 'time', 'time_error', 'depth', 'depth_error', 'agency',
            'eventid', 'identifier',
            'surface__semi_minor', 'surface__semi_major', 'surface__strike',
            'magnitude__mb_val', 'magnitude__mb_val_error',
            'magnitude__ml_val', 'magnitude__ml_val_error',
            'magnitude__ms_val', 'magnitude__ms_val_error',
            'magnitude__mw_val', 'magnitude__mw_val_error',
            )

        def _strip_table(dic):
            # only return the column name
            return dict((k.split('__')[-1], v) for k, v in dic.items())

        return [_strip_table(r) for r in values]

    def _verify_db_data(self, csv_loader, db_rows):

        def _pop_date_fields(csv):
            date_fields = ['year', 'month', 'day', 'hour', 'minute', 'second']
            res = [csv.pop(csv.index(field)) for field in date_fields]
            return res

        def _prepare_date(csv_r, date_fields):
            return [int(csv_r[field]) for field in date_fields]

        def _pop_geometry_fields(csv):
            unused_fields = ['longitude', 'latitude']
            [csv.pop(csv.index(field)) for field in unused_fields]

        # skip the header
        csv_loader.csv_reader.next()
        csv_els = list(csv_loader.csv_reader)
        for csv_row, db_row in zip(csv_els, db_rows):
            csv_keys = csv_row.keys()
            # pops 'longitude', 'latitude' which are used to populate
            # geometry_columns
            _pop_geometry_fields(csv_keys)

            timestamp = _prepare_date(csv_row, _pop_date_fields(csv_keys))
            csv_time = csv_loader._date_to_timestamp(*timestamp)
            # first we compare the timestamps
            self.assertEqual(str(db_row['time']), csv_time)

            # then, we cycle through the csv keys and consider some special
            # cases
            for csv_key in csv_keys:
                db_val = db_row[csv_key]
                csv_val = csv_row[csv_key]

                def convert_val(v):
                    v = v.strip()

                    if csv_key in ['agency', 'identifier']:
                        coerce_to = str
                    else:
                        coerce_to = float

                    if not len(v):
                        return None
                    else:
                        return coerce_to(v)

                self.assertEqual(db_val, convert_val(csv_val))

    def _clean_db_data(self):
        db_rows = self._retrieve_db_data()

        for db_row in db_rows:
            models.Catalog.objects.get(id=db_row['id']).delete()

    def test_csv_to_db_loader_end_to_end(self):
        """
            * Serializes the csv into the database
            * Queries the database for the data just inserted
            * Verifies the data against the csv
            * Deletes the inserted records from the database
        """

        csv_loader = db_loader.CsvModelLoader(self.csv_path)
        csv_loader.serialize()
        db_rows = self._retrieve_db_data()

        # rewind the file
        csv_loader.csv_fd.seek(0)

        self._verify_db_data(csv_loader, db_rows)
