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
        # test the logic of the reader generator, in particular the
        # `<groupname>__` convention in the name of the files to specify
        # files belonging to the same group
        # also test the lexicographic ordering of the readers
        fnames = ['a.csv', 'a.mdata',  # group of one pair
                  'x__1.mdata', 'x__1.csv', 'x__0.mdata', 'x__0.csv',  # group
                  'y.csv',  # unpaired file
                  'x__2.mdata',  # another unpaired file
                  'x__2.cs',  # ignored extension
                  ]
        got = []
        for groupname, readers in collect_readers(Reader, None, fnames):
            got.append((groupname, ' '.join(r.name for r in readers)))
        self.assertEqual(got, [('a', 'a'), ('x', 'x__0 x__1')])
