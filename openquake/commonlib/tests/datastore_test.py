# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2017 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import re
import os
import unittest
import tempfile
import numpy
from openquake.commonlib.datastore import DataStore, read


class DataStoreTestCase(unittest.TestCase):
    def setUp(self):
        self.dstore = DataStore()

    def tearDown(self):
        self.dstore.clear()

    def test_pik(self):
        # store pickleable Python objects
        self.dstore['key1'] = 'value1'
        self.assertEqual(len(self.dstore), 1)
        self.dstore['key2'] = 'value2'
        self.assertEqual(list(self.dstore), ['key1', 'key2'])
        del self.dstore['key2']
        self.assertEqual(list(self.dstore), ['key1'])
        self.assertEqual(self.dstore['key1'], 'value1')

    def test_hdf5(self):
        # store numpy arrays as hdf5 files
        self.assertEqual(len(self.dstore), 0)
        self.dstore['/key1'] = value1 = numpy.array(['a', 'b'], dtype=bytes)
        self.dstore['/key2'] = numpy.array([1, 2])
        self.assertEqual(list(self.dstore), ['key1', 'key2'])
        del self.dstore['/key2']
        self.assertEqual(list(self.dstore), ['key1'])
        numpy.testing.assert_equal(self.dstore['key1'], value1)

        self.assertGreater(self.dstore.getsize('key1'), 0)
        self.assertGreater(self.dstore.getsize(), 0)

        # test creating and populating a dset
        dset = self.dstore.hdf5.create_dataset('dset', shape=(4, 2),
                                               dtype=int)
        dset[0] = [1, 2]
        dset[3] = [4, 5]
        numpy.testing.assert_equal(
            self.dstore['dset'][:], [[1, 2], [0, 0], [0, 0], [4, 5]])

        # it is possible to store twice the same key (work around a bug)
        self.dstore['key1'] = 'value1'

        # test `in` functionality with composite keys
        self.dstore['a/b'] = 42
        self.assertTrue('a/b' in self.dstore)

    def test_export_path(self):
        path = self.dstore.export_path('hello.txt', tempfile.mkdtemp())
        mo = re.search('hello_\d+', path)
        self.assertIsNotNone(mo)

    def test_read(self):
        # cas of a non-existing directory
        with self.assertRaises(OSError):
            read(42, datadir='/fake/directory')
        # case of a non-existing file
        with self.assertRaises(IOError):
            read(42, datadir='/tmp')
        # case of no read permission
        tmp = tempfile.mkdtemp()
        fname = os.path.join(tmp, 'calc_42.hdf5')
        open(fname, 'w').write('')
        os.chmod(fname, 0)
        with self.assertRaises(IOError) as ctx:
            read(42, datadir=tmp)
        self.assertIn('permission denied', str(ctx.exception).lower())
