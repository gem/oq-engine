import unittest
from openquake.nrmllib.readers import StringReader


class ReaderTestCase(unittest.TestCase):
    fake = StringReader('fake', '{"fieldnames": ["a", "b"]}', '''\
a,b
1,2
3,4
5,6
7,8
''')

    def test1(self):
        self.assertEqual(self.fake[0], {'a': '1', 'b': '2'})
        self.assertEqual(self.fake[1], {'a': '3', 'b': '4'})
        self.assertEqual(
            self.fake[2:4], [{'a': '5', 'b': '6'}, {'a': '7', 'b': '8'}])
