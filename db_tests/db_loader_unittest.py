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

TEST_DB = 'openquake'
TEST_DB_USER = 'oq_pshai_etl'
TEST_DB_HOST = 'localhost'
TEST_DB_PASSWORD = 'openquake'

TEST_SRC_FILE = helpers.get_data_path('example-source-model.xml')
TGR_MFD_TEST_FILE = helpers.get_data_path('one-simple-source-tgr-mfd.xml')

TEST_EQCAT_DB_USER = 'oq_eqcat_etl'


class NrmlModelLoaderDBTestCase(unittest.TestCase):
    """
    This test case class is a counterpart to the
    :py:class:`tests.db_loader_unittest.NrmlModelLoaderTestCase`. This class
    includes related tests that need to run against the OpenQuake database.
    """

    def _serialize_test_helper(self, test_file, expected_tables):
        engine = db.create_engine(TEST_DB, TEST_DB_USER, host=TEST_DB_HOST)
        src_loader = db_loader.SourceModelLoader(test_file, engine)

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
        tables = src_loader.meta.tables

        # list of tuples of (table name, id)
        table_id_pairs = [x.items()[0] for x in results]

        for table_name, record_id in table_id_pairs:
            table = tables[table_name]

            # run a query against the table object to get a ResultProxy
            result_proxy = table.select(table.c.id == record_id).execute()

            # there should be 1 record here
            self.assertEqual(1, result_proxy.rowcount)

        # clean up db resources
        src_loader.close()

    def test_serialize(self):
        """
        Test serialization of a single simple fault source with an
        Evenly-Discretized MFD.
        """
        expected_tables = \
            ['pshai.mfd_evd', 'pshai.simple_fault', 'pshai.source']
        self._serialize_test_helper(TEST_SRC_FILE, expected_tables)

    def test_serialize_with_tgr_mfd(self):
        """
        Similar to test_serialize, except the test input data includes a
        Truncated Gutenberg-Richter MFD (so we exercise all paths inside the
        loader code).
        """
        expected_tables = \
            ['pshai.mfd_tgr', 'pshai.simple_fault', 'pshai.source']
        self._serialize_test_helper(TGR_MFD_TEST_FILE, expected_tables)


class CsvModelLoaderDBTestCase(unittest.TestCase):

    def setUp(self):
        csv_file = "ISC_sampledata1.csv"
        self.csv_path = helpers.get_data_path(csv_file)
        self.db_loader = db_loader.CsvModelLoader(self.csv_path, None, 'eqcat')
        self.db_loader._read_model()
        self.csv_reader = self.db_loader.csv_reader

    def test_csv_to_db_loader_end_to_end(self):
        """
            * Serializes the csv into the database
            * Queries the database for the data just inserted
            * Verifies the data against the csv
            * Deletes the inserted records from the database
        """
        def _pop_date_fields(csv):
            date_fields = ['year', 'month', 'day', 'hour', 'minute', 'second']
            res = [csv.pop(csv.index(field)) for field in date_fields]
            return res

        def _prepare_date(csv_r, date_fields):
            return [int(csv_r[field]) for field in date_fields]

        def _pop_geometry_fields(csv):
            unused_fields = ['longitude', 'latitude']
            [csv.pop(csv.index(field)) for field in unused_fields]

        # compatible with SQLAlchemy 0.6.4; a bit of an hack because
        # it knows how ".join" is implemented in SQLSoup; there does
        # not seem a cleaner solution
        def _join(soup_db, left, right, **kwargs):
            from sqlalchemy import join

            j = join(left, right)
            return soup_db.map(j, **kwargs)

        def _retrieve_db_data(soup_db):

            # doing some "trickery" with *properties and primary_key,
            # to adapt the code for sqlalchemy 0.7

            # surface join
            surf_join = _join(soup_db, soup_db.catalog, soup_db.surface,
                properties={'id_surface': [soup_db.surface.c.id]},
                            exclude_properties=[soup_db.surface.c.id,
                                soup_db.surface.c.last_update],
                primary_key=[soup_db.surface.c.id])

            # magnitude join
            mag_join = _join(soup_db, surf_join, soup_db.magnitude,
                properties={'id_magnitude': [soup_db.magnitude.c.id],
                        'id_surface': [soup_db.surface.c.id]},
                            exclude_properties=[soup_db.magnitude.c.id,
                                soup_db.magnitude.c.last_update,
                                soup_db.surface.c.last_update],
                primary_key=[soup_db.magnitude.c.id, soup_db.surface.c.id])

            return mag_join.order_by(soup_db.catalog.eventid).all()

        def _verify_db_data(csv_loader, db_rows):
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
                self.assertEqual(str(db_row.time), csv_time)

                # then, we cycle through the csv keys and consider some special
                # cases
                for csv_key in csv_keys:
                    db_val = getattr(db_row, csv_key)
                    csv_val = csv_row[csv_key]
                    if not len(csv_val.strip()):
                        csv_val = None
                    if csv_key == 'agency':
                        self.assertEqual(str(db_val), str(csv_val))
                    else:
                        self.assertEqual(float(db_val), float(csv_val))

        def _delete_db_data(soup_db, db_rows):
            # cleaning the db
            for db_row in db_rows:
                soup_db.delete(db_row)

        engine = db.create_engine(dbname=TEST_DB, user=TEST_EQCAT_DB_USER,
                                  password=TEST_DB_PASSWORD)

        csv_loader = db_loader.CsvModelLoader(self.csv_path, engine, 'eqcat')
        csv_loader.serialize()
        db_rows = _retrieve_db_data(csv_loader.soup)

        # rewind the file
        csv_loader.csv_fd.seek(0)

        _verify_db_data(csv_loader, db_rows)

        _delete_db_data(csv_loader.soup, db_rows)

        csv_loader.soup.commit()
