import unittest
from openquake.nrmllib.readers import StringReader


class ReaderTestCase(unittest.TestCase):
    fake = StringReader('fake', '<gmfSet/>', '''\
lon,lat,gmv
1.0,2.0,0.1
1.0,2.1,0.1
1.0,2.2,0.2
1.0,2.3,0.2
''')

    def test1(self):
        self.assertEqual(self.fake[0],
                         {'lon': '1.0', 'lat': '2.0', 'gmv': '0.1'})
        self.assertEqual(self.fake[1],
                         {'lon': '1.0', 'lat': '2.1', 'gmv': '0.1'})
        self.assertEqual(
            self.fake[2:4],
            [{'lon': '1.0', 'lat': '2.2', 'gmv': '0.2'},
             {'lon': '1.0', 'lat': '2.3', 'gmv': '0.2'}])
