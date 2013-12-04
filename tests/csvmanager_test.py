import os
import unittest
import tempfile
from openquake.nrmllib import records
from openquake.nrmllib.csvmanager import (
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
