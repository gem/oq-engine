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

from openquake.db.alchemy.models import OqUser, GMFData
from openquake.writer import BulkInserterSA as BulkInserter


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


class DummySession(object):
    CONNECTION = DummyConnection()

    def connection(self):
        return self.CONNECTION

    @property
    def sql(self):
        return self.CONNECTION.sql

    @property
    def values(self):
        return self.CONNECTION.values


class BulkInserterTestCase(unittest.TestCase):
    """
    Unit tests for the BulkInserter class, which simplifies database
    bulk insert
    """

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

    def test_flush(self):
        inserter = BulkInserter(OqUser)
        session = DummySession()

        inserter.add_entry(user_name='user1', full_name='An user')
        fields = inserter.fields
        inserter.flush(session)

        self.assertEquals('INSERT INTO admin.oq_user (%s) VALUES (%%s, %%s)' %
                          (", ".join(fields)), session.sql)

        inserter.add_entry(user_name='user1', full_name='An user')
        inserter.add_entry(user_name='user2', full_name='Another user')
        fields = inserter.fields
        inserter.flush(session)

        self.assertEquals('INSERT INTO admin.oq_user (%s) VALUES' \
                              ' (%%s, %%s), (%%s, %%s)' %
                          (", ".join(fields)), session.sql)

    def test_flush_geometry(self):
        inserter = BulkInserter(GMFData)
        session = DummySession()

        inserter.add_entry(location='POINT(1 1)', output_id=1)
        fields = inserter.fields
        inserter.flush(session)

        if fields[0] == 'output_id':
            values = '%s, GeomFromText(%s, 4326)'
        else:
            values = 'GeomFromText(%s, 4326), %s'

        self.assertEquals('INSERT INTO hzrdr.gmf_data (%s) VALUES (%s)' %
                          (", ".join(fields), values), session.sql)
