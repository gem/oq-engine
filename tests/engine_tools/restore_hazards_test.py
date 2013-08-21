import io
import unittest
from openquake.engine.db.models import getcursor
from openquake.engine.tools.restore_hazards import safe_restore


class TestCase(unittest.TestCase):
    TO_IMPORT_1 = io.StringIO(u'''\
    11\ta
    12\tb''')

    TO_IMPORT_2 = io.StringIO(u'''\
    11\tx
    12\ty''')

    TO_IMPORT_3 = io.StringIO(u'''\
    14\tc
    15\td
    16\te''')

    TO_IMPORT_4 = io.StringIO(u'''\
    4\tc
    5\td
    6\te''')

    def setUp(self):
        self.curs = getcursor('job_init')
        self.curs.execute('create table _example('
                          'id serial primary key, data text)')

    def testrestore4lines(self):
        blocksize = 2

        # restore ids=11, 12
        imported_total = safe_restore(
            self.curs, self.TO_IMPORT_1, '_example', blocksize)
        self.assertEqual(imported_total, (2, 2))

        # try to restore ids already taken
        imported_total = safe_restore(
            self.curs, self.TO_IMPORT_2, '_example', blocksize)
        self.assertEqual(imported_total, (0, 2))
        self.curs.execute("select currval('_example_id_seq')")
        currval = self.curs.fetchone()[0]
        self.assertEqual(currval, 12)

        # restore ids=14, 15, 16
        imported_total = safe_restore(
            self.curs, self.TO_IMPORT_3, '_example', blocksize)
        self.assertEqual(imported_total, (3, 3))
        self.curs.execute("select currval('_example_id_seq')")
        currval = self.curs.fetchone()[0]
        self.assertEqual(currval, 16)

        # restore ids=4, 5, 6
        imported_total = safe_restore(
            self.curs, self.TO_IMPORT_4, '_example', blocksize)
        self.assertEqual(imported_total, (3, 3))
        self.curs.execute("select currval('_example_id_seq')")
        currval = self.curs.fetchone()[0]
        self.assertEqual(currval, 16)  # the insertion routines contains
        # a setval of the sequence id to the highest available value, so
        # that some ids can be skipped; this behaviour avoids id clashes

    def tearDown(self):
        self.curs.execute('drop table _example')
        self.curs.connection.commit()
