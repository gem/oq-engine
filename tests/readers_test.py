import unittest
from openquake.nrmllib.readers import Reader, StringReader, collect_readers


class ReaderTestCase(unittest.TestCase):
    fake = StringReader('fake', '<gmfSet/>', '''\
lon,lat,gmv
1.0,2.0,0.1
1.0,2.1,0.1
1.0,2.2,0.2
1.0,2.3,0.2
''')

    def test_getitem(self):
        # test that a Reader object support the bracket notation
        self.assertEqual(self.fake[0],
                         {'lon': '1.0', 'lat': '2.0', 'gmv': '0.1'})
        self.assertEqual(self.fake[1],
                         {'lon': '1.0', 'lat': '2.1', 'gmv': '0.1'})
        self.assertEqual(
            self.fake[2:4],
            [{'lon': '1.0', 'lat': '2.2', 'gmv': '0.2'},
             {'lon': '1.0', 'lat': '2.3', 'gmv': '0.2'}])

    def test_collect_readers(self):
        # test the logic of the reader generator
        fnames = ['a.csv', 'a.mdata',  # group of one pair
                  'x__0.mdata', 'x__0.csv',  # group of two pairs
                  'x__1.mdata', 'x__1.csv',  # group of two pairs
                  'y.csv',  # unpaired file
                  'x__2.mdata',  # another unpaired file
                  'x__2.cs',  # ignored extension
                  ]
        got = []
        for name, readers in collect_readers(Reader, None, fnames):
            got.append((name, ' '.join(reader.name for reader in readers)))
        self.assertEqual(got, [('a', 'a'), ('x', 'x__0 x__1')])
