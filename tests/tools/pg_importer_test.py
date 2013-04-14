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
from openquake.engine.db.models import Output, GmfCollection, OqJob
from tests.utils import gmf_collection as c


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
        data = '''\
$out1	1	\N	gmf-rlz-1	gmf	2013-04-11 03:08:46
$out2	1	\N	gmf-rlz-2	gmf	2013-04-11 03:08:47
'''
        out = Output.objects.latest('id')
        last_id = self.imp.import_templ('uiapi.output', data)
        self.assertEqual(last_id, out.id + 2)  # inserted 2 rows
        self.imp.conn.rollback()  # cleanup

    def testImportGmfCollection(self):
        gmf_coll_orig_id = GmfCollection.objects.latest('id').id

        c.import_a_gmf_collection(self.imp.conn)

        gmf_coll_id = GmfCollection.objects.latest('id').id
        self.assertEqual(gmf_coll_orig_id + 1, gmf_coll_id)

        # check that the db contains the expected GmfSets
        out = Output.objects.latest('id')
        out.oq_job = OqJob.objects.create(owner_id=1)  # fake job
        # the fake job is unfortunately needed in GmfSet.iter_gmfs
        out.save()
        [coll] = GmfCollection.objects.filter(output=out)
        set1, set2, set3 = sorted(coll, key=lambda s: s.id)
        set1_str = '\n'.join(
            map(str, set1.iter_gmfs(num_tasks=c.num_tasks, imts=c.imts)))
        set2_str = '\n'.join(
            map(str, set2.iter_gmfs(num_tasks=c.num_tasks, imts=c.imts)))
        set3_str = '\n'.join(
            map(str, set3.iter_gmfs(num_tasks=c.num_tasks, imts=c.imts)))
        self.assertEqual(set1_str, c.set1_exp)
        self.assertEqual(set2_str, c.set2_exp)
        self.assertEqual(set3_str, c.set3_exp)
