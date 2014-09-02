import os
import mock
import unittest
import psycopg2
import importlib
from contextlib import contextmanager

from openquake.engine.db.models import getcursor
from openquake.engine.db.upgrade_manager import (
    upgrade_db, version_db, what_if_I_upgrade, DuplicatedVersion)

conn = getcursor('admin').connection
pkg = 'openquake.engine.tests.db.upgrades'
upgrader = importlib.import_module(pkg).upgrader


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
    # Apply the scripts in openquake.engine.tests.db.upgrades to the database.
    # All the tables in the test scripts are in the `test` schema, which is
    # automatically created an destroyed in the setUp/tearDown methods.
    # This test consider the 5 scripts in openquake.engine.tests.db.upgrades:

    ## 0000-base_schema.sql
    ## 0001-populate.sql
    ## 0002-a-syntax-error.sql
    ## 0003-insert-error.sql
    ## 0005-populate_model.py

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
        applied = upgrade_db(conn, pkg, skip_versions='0002 0003'.split())
        self.assertEqual(applied, '0001 0005'.split())
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
        with temp_script('0004-do-nothing.sql', 'SELECT 1'):
            applied = upgrade_db(conn, pkg, skip_versions='0002 0003'.split())
            self.assertEqual(applied, ['0004'])

    def test_syntax_error(self):
        with self.assertRaises(psycopg2.ProgrammingError) as ctx:
            upgrade_db(conn, pkg, skip_versions=['0001'])
        self.assertTrue(str(ctx.exception).startswith(
            'syntax error at or near'))

    def test_insert_error(self):
        with self.assertRaises(psycopg2.DataError):
            # run 03-insert-error.sql
            upgrade_db(conn, pkg, skip_versions=['0002'])
        # check that the rollback works: the version
        # table contains only the base script and the
        # tables are not populated, i.e. '0001' was rolled back
        self.assertEqual(count(conn, 'test.version'), 1)
        self.assertEqual(count(conn, 'test.hazard_calculation'), 0)
        self.assertEqual(count(conn, 'test.lt_source_model'), 0)

    def test_duplicated_version(self):
        # there are two scripts with version '0001'
        with self.assertRaises(DuplicatedVersion):
            with temp_script('0001-do-nothing.sql', 'SELECT 1'):
                upgrade_db(conn, pkg)

    def test_version_db(self):
        self.assertEqual(version_db(conn, pkg), '0000')

    def check_message(self, html, expected):
        with mock.patch('urllib.urlopen') as urlopen:
            urlopen().read.return_value = html
            self.assertEqual(expected, what_if_I_upgrade(conn, pkg))

    def test_safe_upgrade(self):
        self.check_message('''
>0000-base_schema.sql<
>0001-uniq-ruptures.sql<
''', 'Your database is at version 0000. If you upgrade to the latest master, you will arrive at version 0001.\nThe following scripts can be applied safely:\nhttps://github.com/gem/oq-engine/tree/master/openquake/engine/db/schema/upgrades/0000-base_schema.sql\nhttps://github.com/gem/oq-engine/tree/master/openquake/engine/db/schema/upgrades/0001-uniq-ruptures.sql')

    def test_tricky_upgrade(self):
        self.check_message('''
>0000-base_schema.sql<
>0001-slow-uniq-ruptures.sql<
>0002-danger-drop-gmf.sql<
''', 'Your database is at version 0000. If you upgrade to the latest master, you will arrive at version 0002.\nThe following scripts can be applied safely:\nhttps://github.com/gem/oq-engine/tree/master/openquake/engine/db/schema/upgrades/0000-base_schema.sql\nPlease note that the following scripts could be slow:\nhttps://github.com/gem/oq-engine/tree/master/openquake/engine/db/schema/upgrades/0001-slow-uniq-ruptures.sql\nPlease note that the following scripts are potentially dangerous and could destroy your data:\nhttps://github.com/gem/oq-engine/tree/master/openquake/engine/db/schema/upgrades/0002-danger-drop-gmf.sql')

    def tearDown(self):
        # in case of errors upgrade_db has already performed a rollback
        conn.cursor().execute('DROP SCHEMA test CASCADE')
        conn.commit()
