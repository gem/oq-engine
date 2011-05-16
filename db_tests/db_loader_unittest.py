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

TEST_SRC_FILE = helpers.get_data_path('example-source-model.xml')
TGR_MFD_TEST_FILE = helpers.get_data_path('one-simple-source-tgr-mfd.xml')

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
