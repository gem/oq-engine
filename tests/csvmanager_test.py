import unittest
from openquake.nrmllib import records
from openquake.nrmllib.csvmanager import create_table


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

    def test_get_all(self):
        # test the logic of the table generator, in particular the
        # `<groupname>__` convention in the name of the files to specify
        # files belonging to the same group
        # also test the lexicographic ordering of the tables
        pass
