import io
import unittest
from openquake.engine.db.models import getcursor
from openquake.engine.tools.restore_hazards import safe_restore


class TestCase(unittest.TestCase):
    def setUp(self):
        self.curs = getcursor('job_init')
        self.curs.execute('create table _example(id serial primary key)')

    def testrestore4lines(self):
        blocksize = 2
        imported = safe_restore(
            self.curs, io.StringIO(u'1\n2\n3\n4\n'), '_example', blocksize)
        self.assertEqual(imported, 4)
        imported = safe_restore(
            self.curs, io.StringIO(u'1\n2\n3\n'), '_example', blocksize)
        self.assertEqual(imported, 0)
        self.curs.execute("select currval('_example_id_seq')")
        currval = self.curs.fetchone()[0]
        self.assertEqual(currval, 4)

    def tearDown(self):
        self.curs.execute('drop table _example')
