import unittest
import numpy
from openquake.commonlib.datastore import DataStore


def key1_upper(key, dstore):
    return dstore['key1'].upper()


class DataStoreTestCase(unittest.TestCase):
    def setUp(self):
        self.dstore = DataStore()

    def test_pik(self):
        # store pickleable Python objects
        self.dstore['key1'] = 'value1'
        self.assertEqual(len(self.dstore), 1)
        self.dstore['key2'] = 'value2'
        self.assertEqual(list(self.dstore), [('key1',), ('key2',)])
        del self.dstore['key2']
        self.assertEqual(list(self.dstore), [('key1',)])
        self.assertEqual(self.dstore['key1'], 'value1')

        # store and retrieve a callable
        self.dstore['key1_upper'] = key1_upper
        self.assertEqual(self.dstore['key1_upper'], 'VALUE1')
        self.dstore.remove()

    def test_hdf5(self):
        # optional test, run only if h5py is available
        try:
            import h5py
        except ImportError:
            raise unittest.SkipTest

        # store numpy arrays as hdf5 files
        with self.assertRaises(ValueError):
            self.dstore['key1', 'h5'] = 'value1'
        self.assertEqual(len(self.dstore), 0)
        self.dstore['key1', 'h5'] = value1 = numpy.array(['a', 'b'])
        self.dstore['key2', 'h5'] = numpy.array([1, 2])
        self.assertEqual(list(self.dstore), [('key1', 'h5'), ('key2', 'h5')])
        del self.dstore['key2', 'h5']
        self.assertEqual(list(self.dstore), [('key1', 'h5')])
        numpy.testing.assert_equal(self.dstore['key1', 'h5'], value1)

        self.assertGreater(self.dstore.getsize('key1', 'h5'), 0)
        self.assertGreater(self.dstore.getsize(), 0)
        # store items; notice that the output order is lexicographic
        a1 = numpy.array([1, 2])
        a2 = numpy.array([3, 4, 5])
        items = [('a2', a2), ('a1', a1)]
        self.dstore['items', 'hdf5'] = items
        numpy.testing.assert_equal(
            list(self.dstore['items', 'hdf5']), sorted(items))

        # test creating and populating a dset
        with self.dstore.h5file(('xxx', 'h5')) as h5f:
            dset = h5f.create_dataset('dset', shape=(4, 2))
            dset[0] = [1, 2]
            dset[3] = [4, 5]
        numpy.testing.assert_equal(
            self.dstore['xxx', 'h5'],
            [[1., 2.], [0., 0.], [0., 0.], [4., 5.]])

        self.dstore.remove()
