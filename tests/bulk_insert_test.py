# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.


import unittest

from django.db import transaction

from openquake.engine import writer

from openquake.engine.db.models import OqUser, GmfAgg
from openquake.engine.writer import BulkInserter, CacheInserter


def _map_values(fields, values):
    return sum(([item[key] for key in fields] for item in values), [])


class DummyConnection(object):
    @property
    def connection(self):
        return self

    def cursor(self):
        return self

    def execute(self, sql, values):
        self.sql = sql
        self.values = values

    def copy_from(self, stringio, table, columns):
        self.data = stringio.getvalue()
        self.table = table
        self.columns = columns


class BulkInserterTestCase(unittest.TestCase):
    """
    Unit tests for the BulkInserter class, which simplifies database
    bulk insert
    """

    def setUp(self):
        self.connections = writer.connections

        writer.connections = dict(
            admin=DummyConnection(), reslt_writer=DummyConnection())

    def tearDown(self):
        writer.connections = self.connections

    def test_add_entry(self):
        """Test multiple add entry calls"""
        inserter = BulkInserter(OqUser)

        inserter.add_entry(user_name='user1', full_name='An user')

        self.assertEquals(sorted(['user_name', 'full_name']),
                          sorted(inserter.fields))
        self.assertEquals(inserter.count, 1)
        self.assertEquals(_map_values(inserter.fields,
                                      [{'user_name': 'user1',
                                        'full_name': 'An user'}]),
                          inserter.values)

        inserter.add_entry(user_name='user2', full_name='Another user')
        inserter.add_entry(user_name='user3', full_name='A third user')

        self.assertEquals(sorted(['user_name', 'full_name']),
                          sorted(inserter.fields))
        self.assertEquals(inserter.count, 3)
        self.assertEquals(_map_values(inserter.fields,
                                      [{'user_name': 'user1',
                                        'full_name': 'An user'},
                                       {'user_name': 'user2',
                                        'full_name': 'Another user'},
                                       {'user_name': 'user3',
                                        'full_name': 'A third user'}]),
                          inserter.values)

    def test_add_entry_different_keys(self):
        inserter = BulkInserter(OqUser)

        inserter.add_entry(user_name='user1', full_name='An user')
        self.assertRaises(AssertionError, inserter.add_entry,
                          user_name='user1')
        self.assertRaises(AssertionError, inserter.add_entry,
                          user_name='user1',
                          full_name='An user',
                          data_is_open=False)

    @transaction.commit_on_success('admin')
    def test_flush(self):
        inserter = BulkInserter(OqUser)
        connection = writer.connections['admin']

        inserter.add_entry(user_name='user1', full_name='An user')
        fields = inserter.fields
        inserter.flush()

        self.assertEquals('INSERT INTO "admin"."oq_user" (%s) VALUES'
                          ' (%%s, %%s)' %
                          (", ".join(fields)), connection.sql)

        inserter.add_entry(user_name='user1', full_name='An user')
        inserter.add_entry(user_name='user2', full_name='Another user')
        fields = inserter.fields
        inserter.flush()

        self.assertEquals('INSERT INTO "admin"."oq_user" (%s) VALUES'
                          ' (%%s, %%s), (%%s, %%s)' %
                          (", ".join(fields)), connection.sql)


class CacheInserterTestCase(unittest.TestCase):
    """
    Unit tests for the CacheInserter class.
    """
    def setUp(self):
        self.connections = writer.connections
        writer.connections = dict(
            admin=DummyConnection(), reslt_writer=DummyConnection())

    def tearDown(self):
        writer.connections = self.connections

    # this test is probably too strict and testing implementation details
    def test_insert_gmf(self):
        cache = CacheInserter(GmfAgg, 10)
        gmf1 = GmfAgg(
            gmf_id=1, imt='PGA', gmvs=[], rupture_ids=[],
            site_id=1)
        gmf2 = GmfAgg(
            gmf_id=1, imt='PGA', gmvs=[], rupture_ids=[],
            site_id=2)
        cache.add(gmf1)
        cache.add(gmf2)
        cache.flush()
        connection = writer.connections['reslt_writer']
        self.assertEqual(
            connection.data,
            '1\t\\N\tPGA\t\\N\t\\N\t{}\t{}\t1\n1\t\\N\tPGA\t\\N\t\\N\t{}\t{}\t2\n')
        self.assertEqual(connection.table, '"hzrdr"."gmf_data"')
        self.assertEqual(
            connection.columns,
            ['gmf_id', 'ses_id', 'imt', 'sa_period', 'sa_damping',
             'gmvs', 'rupture_ids', 'site_id'])
