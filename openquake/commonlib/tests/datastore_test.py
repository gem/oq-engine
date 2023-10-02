# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2023 GEM Foundation
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
import sys
import unittest
import tempfile
import numpy
from openquake.baselib import hdf5
from openquake.commonlib import datastore, logs


class DataStoreTestCase(unittest.TestCase):
    """
    Testing the complex interaction between datastore and database
    """
    def setUp(self):
        log = logs.init(
            "job", {'calculation_mode': 'scenario', 'sites': '0 0'})
        self.dstore = datastore.new(log.calc_id, log.get_oqparam())

    def tearDown(self):
        self.dstore.close()
        self.dstore.clear()

    def test_hdf5(self):
        # store numpy arrays as hdf5 files
        lst = ['oqparam', 'performance_data', 'task_info', 'task_sent']
        self.assertEqual(sorted(self.dstore), lst)
        # performance_data, task_info, task_sent
        self.dstore['/key1'] = value1 = numpy.array(['a', 'b'], dtype=bytes)
        self.dstore['/key2'] = numpy.array([1, 2])
        self.assertEqual(list(self.dstore), [
            'key1', 'key2', 'oqparam', 'performance_data',
            'task_info', 'task_sent'])
        del self.dstore['/key2']
        self.assertEqual(list(self.dstore), [
            'key1', 'oqparam', 'performance_data', 'task_info', 'task_sent'])
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
        mo = re.search(r'hello_\d+', path)
        self.assertIsNotNone(mo)

    def test_read(self):
        # windows does not manage permissions properly. Skip the test
        if sys.platform == 'win32':
            raise unittest.SkipTest('Windows')

        # case of a non-existing directory
        with self.assertRaises(OSError):
            datastore.read(42, 'r', '/fake/directory')
        # case of a non-existing file
        with self.assertRaises(IOError):
            datastore.read(42, 'r', '/tmp')
        # case of no read permission
        tmp = tempfile.mkdtemp()
        fname = os.path.join(tmp, 'calc_42.hdf5')
        open(fname, 'w').write('')
        os.chmod(fname, 0)
        with self.assertRaises(IOError) as ctx:
            datastore.read(42, 'r', tmp)
        self.assertIn('permission denied', str(ctx.exception).lower())
        os.remove(fname)

    def test_store_retrieve_files(self):
        fnames = []
        for cwd, dirs, files in os.walk(os.path.dirname(__file__)):
            for f in files:
                if f.endswith('.py'):
                    fnames.append(os.path.join(cwd, f))
        self.dstore.store_files(fnames)
        for name, data in self.dstore.retrieve_files():
            print(name)
        print(self.dstore.get_file(name))

    def test_hdf5_to_npz(self):
        # test a metadata bug with h5py 2.10.0
        # https://github.com/numpy/numpy/issues/14142#issuecomment-620980980
        dt = [('id', '<S20'), ('ordinal', numpy.uint32)]
        arr0 = numpy.array([(b'a11', 1), (b'a12', 2)], dt)
        self.dstore['assets'] = arr0
        arr1 = self.dstore['assets'][()]
        arr1.dtype = [(n, str(arr1.dtype[n])) for n in arr1.dtype.names]
        fd, fname = tempfile.mkstemp(suffix='.npz')
        os.close(fd)
        numpy.savez(fname, array=arr1)
        print('Saved %s' % fname)
        arr2 = numpy.load(fname)['array']
        self.assertEqual(arr2.dtype, dt)
        os.remove(fname)

    def test_sel(self):
        # test dstore.sel
        N, M, L = 1, 2, 3
        imts = 'PGA', 'SA(1.0)'
        self.dstore['hcurves'] = numpy.zeros((N, M, L))
        self.dstore.set_shape_descr('hcurves', sid=[0], imt=imts, lvl=L)
        arr = self.dstore.sel('hcurves', imt='PGA', lvl=2)
        self.assertEqual(arr.shape, (1, 1, 1))

    def test_pandas(self):
        sids = numpy.arange(3)
        eids = [2, 2, 0]
        vals = [.1, .2, .3]
        self.dstore['df/sid'] = sids
        self.dstore['df/eid'] = eids
        self.dstore['df/val'] = vals
        self.dstore.getitem('df').attrs['__pdcolumns__'] = 'sid eid val'

        # testing slice
        df = self.dstore.read_df('df', 'sid', slc=slice(1, 3))
        print(df)

        # testing selection
        df = self.dstore.read_df('df', 'eid', sel={'eid': 2, 'sid': 0})
        self.assertEqual(list(df.index), [2])
        self.assertEqual(list(df.sid), [0])
        self.assertEqual(list(df.val), [.1])

        # testing list selection
        df = self.dstore.read_df('df', 'eid', sel={'sid': [0, 2]})
        self.assertEqual(list(df.val), [.1, .3])

    def test_pandas_vlen(self):
        self.dstore['test/val'] = [.2, .3]
        self.dstore.hdf5.save_vlen(
            'test/val_', [numpy.array([1]), numpy.array([2, 3])])
        self.dstore.getitem('test').attrs['__pdcolumns__'] = 'val val_'
        df = self.dstore.read_df('test')
        numpy.testing.assert_equal(df['val_'].loc[0], [1])
        numpy.testing.assert_equal(df['val_'].loc[1], [2, 3])

    def test_ArrayWrapper(self):
        dic = dict(shape_descr=['taxonomy', 'occupancy'],
                   taxonomy=['RC', 'WOOD'],
                   occupancy=['RES', 'IND', 'COM'])
        arr = numpy.zeros((2, 3))
        arr[0, 0] = 2000.
        arr[0, 1] = 5000.
        arr[1, 0] = 500.
        aw = hdf5.ArrayWrapper(arr, dic)
        self.dstore['aw'] = aw
        aw1 = self.dstore['aw']
        print(aw1)
        aw.save('aw2', self.dstore.hdf5)
        aw2 = self.dstore['aw2']
        print(aw2)
        print(self.dstore.getitem('aw/taxonomy'))
        print(self.dstore.getitem('aw2/taxonomy'))
