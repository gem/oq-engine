#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2013, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import unittest
from django.db import connection
from openquake.engine.tools.pg_importer import PGImporter
from openquake.engine.db.models import Output
from cStringIO import StringIO


def to_csv(conn, tname, fieldstr, wherestr):
    query = 'COPY (SELECT %s FROM %s WHERE %s ORDER BY id) TO stdout' % (
        fieldstr, tname, wherestr)
    s = StringIO()
    try:
        conn.cursor().copy_expert(query, s)
        return s.getvalue()
    finally:
        s.close()


class PGImporterTestCase(unittest.TestCase):
    @classmethod
    def setupClass(cls):
        connection.cursor()  # open the connection
        cls.imp = PGImporter(connection.connection)

    def test_empty_file(self):
        out = Output.objects.latest('id')
        last_id = self.imp.import_templ('uiapi.output', '')
        self.assertEqual(last_id, out.id)  # inserted nothing
        self.imp.conn.rollback()  # cleanup

    def test_serial_updated(self):
        output_str = '''\
$out1	\N	gmf-rlz-1	gmf	2013-04-11 03:08:46
$out2	\N	gmf-rlz-2	gmf	2013-04-11 03:08:47
'''
        out = Output.objects.latest('id')
        last_id = self.imp.import_templ('uiapi.output', output_str)
        self.assertEqual(last_id, out.id + 2)  # inserted 2 rows
        self.imp.conn.rollback()  # cleanup
