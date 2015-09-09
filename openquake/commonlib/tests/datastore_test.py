import unittest
import numpy
from openquake.commonlib.datastore import DataStore, view


@view.add('key1_upper')
def view_key1_upper(key, dstore):
    return dstore['key1'].upper()


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

        # test a datastore view
        self.assertEqual(view('key1_upper', self.dstore), 'VALUE1')

    def test_hdf5(self):
        # store numpy arrays as hdf5 files
        self.assertEqual(len(self.dstore), 0)
        self.dstore['/key1'] = value1 = numpy.array(['a', 'b'])
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

    def test_parent(self):
        # copy the attributes of the parent datastore on the child datastore,
        # without overriding the attributes with the same name
        self.dstore.attrs['a'] = 2
        parent = DataStore(params=[('a', 1), ('b', 2)])
        self.dstore.set_parent(parent)
        attrs = sorted(self.dstore.attrs.items())
        self.assertEqual(attrs, [('a', 2), ('b', 2)])
