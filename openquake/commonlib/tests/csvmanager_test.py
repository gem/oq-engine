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

import os
import unittest
import tempfile
from openquake.commonlib import records
from openquake.commonlib.csvmanager import (
    create_table, ZipArchive, MemArchive, CSVManager,
    MultipleManagerError)


def cast(rec):
    return rec.cast()[0]


class TableTestCase(unittest.TestCase):
    def test_getitem(self):
        tbl = create_table(records.Location, '''\
1,1.0,2.0
2,1.0,2.1
3,1.0,2.2
4,1.0,2.3
''')
        # test that a Table object support the bracket notation
        self.assertEqual(cast(tbl[0]), (1, 1.0, 2.0))
        self.assertEqual(cast(tbl[1]), (2, 1.0, 2.1))
        self.assertEqual(map(cast, tbl[2:4]),
                         [(3, 1.0,  2.2), (4, 1.0, 2.3)])

    def test_unique_constraint(self):
        with self.assertRaises(KeyError) as ctxt:
            create_table(records.Location, '''\
1,1.0,2.0
2,1.0,2.0
''')
        self.assertEqual(str(ctxt.exception),
                         "'Location:1:Duplicated record:lon=1.0,lat=2.0'")

    def test_zip(self):
        with tempfile.NamedTemporaryFile() as f:
            name = f.name
        archive = ZipArchive(name, 'w')
        try:
            with archive.open('a', 'w') as f:
                f.write('1,2')
            with archive.open('b', 'w') as f:
                f.write('3,4')
            self.assertEqual(archive.extract_filenames(), set('ab'))
            self.assertEqual(archive.open('a').read(), '1,2')
        finally:
            os.remove(archive.name)

    def test_bad_prefix(self):
        archive = MemArchive([
            ('test__DiscreteVulnerabilitySet.csv', ''),
            ('test__DiscreteVulnerability.csv', ''),
            ('tes__DiscreteVulnerabilityData.csv', ''),
        ])
        man = CSVManager(archive)
        with self.assertRaises(MultipleManagerError):
            man._getconverter()
        # the case NotInArchive is convered in convert_test.py

    def test_is_valid(self):
        tbl = create_table(records.Location, '1,190.0,2.0')
        row, exc = tbl[0].cast()
        self.assertEqual(
            str(exc),
            'Location[lon]: 0,1: longitude 190.0 > 180')
