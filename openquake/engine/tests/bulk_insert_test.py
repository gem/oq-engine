# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2014, GEM Foundation.
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

from openquake.engine import writer

from openquake.engine.db.models import GmfData
from openquake.engine.writer import CacheInserter


class DummyConnection(object):
    @property
    def connection(self):
        return self

    @property
    def description(self):
        # a mock to the test insertion in the GmfData table
        return [['id'], ['gmf_id'], ['task_no'], ['imt'], ['sa_period'],
                ['sa_damping'], ['gmvs'], ['rupture_ids'], ['site_id']]

    def cursor(self):
        return self

    def execute(self, sql, values=()):
        self.sql = sql
        self.values = values

    def copy_from(self, stringio, table, columns):
        self.data = stringio.getvalue()
        self.table = table
        self.columns = columns


class CacheInserterTestCase(unittest.TestCase):
    """
    Unit tests for the CacheInserter class.
    """
    def setUp(self):
        self.connections = writer.connections
        writer.connections = dict(
            admin=DummyConnection(), job_init=DummyConnection())

    def tearDown(self):
        writer.connections = self.connections

    # this test is probably too strict and testing implementation details
    def test_insert_gmf(self):
        cache = CacheInserter(GmfData, 10)
        gmf1 = GmfData(
            gmf_id=1, imt='PGA', gmvs=[], rupture_ids=[],
            site_id=1)
        gmf2 = GmfData(
            gmf_id=1, imt='PGA', gmvs=[], rupture_ids=[],
            site_id=2)
        cache.add(gmf1)
        cache.add(gmf2)
        cache.flush()
        connection = writer.connections['job_init']
        self.assertEqual(
            connection.data,
            '1\t\\N\tPGA\t\\N\t\\N\t{}\t{}\t1\n1\t\\N\tPGA\t\\N\t\\N\t{}\t{}\t2\n')
        self.assertEqual(connection.table, '"hzrdr"."gmf_data"')
        self.assertEqual(
            connection.columns,
            ['gmf_id', 'task_no', 'imt', 'sa_period', 'sa_damping',
             'gmvs', 'rupture_ids', 'site_id'])
