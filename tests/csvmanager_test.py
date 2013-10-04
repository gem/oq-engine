import os
import unittest
import tempfile
from openquake.nrmllib import records
from openquake.nrmllib.csvmanager import create_table, ZipArchive


class TableTestCase(unittest.TestCase):
    def test_getitem(self):
        tbl = create_table(records.Location, '''\
1,1.0,2.0
2,1.0,2.1
3,1.0,2.2
4,1.0,2.3
''')
        # test that a Table object support the bracket notation
        self.assertEqual(tbl[0].cast(), (1, 1.0, 2.0))
        self.assertEqual(tbl[1].cast(), (2, 1.0, 2.1))
        self.assertEqual([r.cast() for r in tbl[2:4]],
                         [(3, 1.0,  2.2), (4, 1.0, 2.3)])

    def test_unique_constraint(self):
        with self.assertRaises(KeyError) as ctxt:
            create_table(records.Location, '''\
1,1.0,2.0
2,1.0,2.0
''')
        self.assertEqual(str(ctxt.exception),
                         "'Location:1:Duplicate record:lon=1.0,lat=2.0'")

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
        finally:
            os.remove(archive.name)
