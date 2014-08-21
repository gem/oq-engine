import os
import unittest
import psycopg2
import importlib
from contextlib import contextmanager

from openquake.engine.db.models import getcursor
from openquake.engine.db.upgrade_manager import upgrade_db, DuplicatedVersion

conn = getcursor('admin').connection
pkg = 'openquake.engine.tests.db.upgrades'
upgrader = importlib.import_module(pkg).upgrader


def upgrade_from_scratch(skip=None):
    return upgrade_db(conn, pkg, from_scratch=True, skip_versions=skip)


def count(conn, tablename):
    curs = conn.cursor()
    curs.execute('SELECT COUNT(*) FROM %s' % tablename)
    return curs.fetchall()[0][0]


@contextmanager
def temp_script(name, content):
    fname = os.path.join(upgrader.upgrade_dir, name)
    with open(fname, 'w') as s:
        s.write(content)
    try:
        yield
    finally:
        os.remove(fname)


class UpgradeManagerTestCase(unittest.TestCase):
    """
    Apply the scripts in openquake.engine.tests.db.upgrades to the database.
    All the tables in the test scripts are in the `test` schema, which
    automatically created an destroyed in the setUp/tearDown methods.
    """
    def setUp(self):
        conn.cursor().execute('CREATE SCHEMA test')
        conn.commit()  # make sure the schema really exists

    def test_missing_pkg(self):
        with self.assertRaises(SystemExit) as ctx:
            upgrade_db(conn, 'openquake.engine.tests.db.not_exists')
        self.assertTrue(str(ctx.exception).startswith(
            'Could not import openquake.engine.tests.db.not_exists'))

    def test_no_upgrades(self):
        with self.assertRaises(SystemExit) as ctx:
            upgrade_db(conn, 'openquake.engine.tests.db.no_upgrades')
        self.assertTrue(str(ctx.exception).startswith(
            'The upgrade_dir does not contain scripts matching the pattern'))

    def test_ok(self):
        applied = upgrade_from_scratch(skip='02 03'.split())
        self.assertEqual(applied, '01 05'.split())
        self.assertEqual(count(conn, 'test.hazard_calculation'), 2)
        self.assertEqual(count(conn, 'test.lt_source_model'), 6)

        # we support the use case of people reserving a number for a
        # a script which is not ready yet: so, if I tell people to start
        # numbering from 5 because I am working on the script #4,
        # when I finally merge my upgrade will not be lost even if
        # higher number scripts entered before it. One can even reserve
        # a bunch of numbers, say from 0020 to 0029, for upgrades affering
        # to the same project.
        # NB: if the higher number scripts contain incompatible changes
        # the migration will fail; then you must fix the script and
        # give it a higher number
        # here we emulate this use case with a reserved script 04 entering
        # when the database is already at version 05
        with temp_script('04-do-nothing.sql', 'select 1'):
            applied = upgrade_db(conn, pkg, skip_versions='02 03'.split())
            self.assertEqual(applied, ['04'])

    def test_syntax_error(self):
        with self.assertRaises(psycopg2.ProgrammingError) as ctx:
            upgrade_from_scratch(skip=['01'])
        self.assertTrue(str(ctx.exception).startswith(
            'syntax error at or near'))

    def test_insert_error(self):
        with self.assertRaises(psycopg2.DataError):
            upgrade_from_scratch(skip=['02'])  # run 03-insert-error.sql

    def test_duplicated_version(self):
        # there are two scripts with version '01'
        with self.assertRaises(DuplicatedVersion):
            with temp_script('01-do-nothing.sql', 'select 1'):
                upgrade_from_scratch()

    def tearDown(self):
        # in case of errors upgrade_db has already performed a rollback
        conn.cursor().execute('DROP SCHEMA test CASCADE')
        conn.commit()
