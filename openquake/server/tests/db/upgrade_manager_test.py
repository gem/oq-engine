# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import os
import mock
import sqlite3
import unittest
import tempfile
import importlib
import urllib
from contextlib import contextmanager

from openquake.server.db.upgrade_manager import (
    upgrade_db, version_db, what_if_I_upgrade,
    VersionTooSmall, DuplicatedVersion)

pkg = 'openquake.server.tests.db.upgrades'
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
    # Apply the scripts in openquake.server.tests.db.upgrades to the database.
    # All the tables in the test scripts are in the `test` schema, which is
    # automatically created an destroyed in the setUp/tearDown methods.
    # This test consider the 5 scripts in openquake.server.tests.db.upgrades:

    # 0000-base_schema.sql
    # 0001-populate.sql
    # 0002-a-syntax-error.sql
    # 0003-insert-error.sql
    # 0005-populate_model.py

    def setUp(self):
        global conn, tmpfile
        fd, tmpfile = tempfile.mkstemp()
        os.close(fd)
        conn = sqlite3.connect(tmpfile)

    def tearDown(self):
        conn.close()
        os.remove(tmpfile)

    def test_missing_pkg(self):
        with self.assertRaises(SystemExit) as ctx:
            upgrade_db(conn, 'openquake.server.tests.db.not_exists')
        self.assertTrue(str(ctx.exception).startswith(
            'Could not import openquake.server.tests.db.not_exists'))

    def test_no_upgrades(self):
        with self.assertRaises(SystemExit) as ctx:
            upgrade_db(conn, 'openquake.server.tests.db.no_upgrades')
        self.assertTrue(str(ctx.exception).startswith(
            'The upgrade_dir does not contain scripts matching the pattern'))

    def test_script_lower_than_current_version(self):
        applied = upgrade_db(conn, pkg, skip_versions='0002 0003'.split())
        self.assertEqual(applied, '0001 0005'.split())
        self.assertEqual(count(conn, 'test_hazard_calculation'), 2)
        self.assertEqual(count(conn, 'test_lt_source_model'), 6)

        # a script 0004 can enter when the database is already at version 0005
        # (this is a convenient feature during development) but officially
        # this is not supported and what_if_I_upgrade must raise an exception
        with temp_script('0004-do-nothing.sql', 'SELECT 1'):
            applied = upgrade_db(conn, pkg, skip_versions='0002 0003'.split())
            self.assertEqual(applied, ['0004'])

        # check that the script 0004 is rejected by what_if_I_upgrade
        with temp_script('0004-do-nothing.sql', 'SELECT 1'):
            with self.assertRaises(VersionTooSmall):
                what_if_I_upgrade(conn, pkg, 'read_scripts')

    def test_syntax_error(self):
        with self.assertRaises(sqlite3.OperationalError) as ctx:
            upgrade_db(conn, pkg, skip_versions=['0001'])
        self.assertIn('syntax error', str(ctx.exception))

    def test_insert_error(self):
        with self.assertRaises(sqlite3.IntegrityError):
            # run 03-insert-error.sql
            upgrade_db(conn, pkg, skip_versions=['0002'])
        # check that the rollback works: the version
        # table contains only the base script and the
        # tables are not populated, i.e. '0001' has to be rolled back
        raise unittest.SkipTest
        self.assertEqual(count(conn, 'test_version'), 1)
        self.assertEqual(count(conn, 'test_hazard_calculation'), 0)
        self.assertEqual(count(conn, 'test_lt_source_model'), 0)

    def test_duplicated_version(self):
        # there are two scripts with version '0001'
        with self.assertRaises(DuplicatedVersion):
            with temp_script('0001-do-nothing.sql', 'SELECT 1'):
                upgrade_db(conn, pkg)

    def test_version_db(self):
        self.assertEqual(version_db(conn, pkg), '0000')

    def check_message(self, html, expected):
        if hasattr(urllib, 'urlopen'):  # Python 2
            with mock.patch('urllib.urlopen') as urlopen:
                urlopen().read.return_value = html
                got = what_if_I_upgrade(conn, pkg)
                self.assertEqual(got, expected)

    def test_safe_upgrade(self):
        expected = '''\
Your database is at version 0000.
The following scripts can be applied safely:
https://github.com/gem/oq-engine/tree/master/openquake/server/db/schema/upgrades/0001-uniq-ruptures.sql
Click on the links if you want to know what exactly the scripts are doing.'''
        self.check_message('''
>0000-base_schema.sql<
>0001-uniq-ruptures.sql<''', expected)

    def test_tricky_upgrade(self):
        expected = '''\
Your database is at version 0000.
Please note that the following scripts could be slow:
https://github.com/gem/oq-engine/tree/master/openquake/server/db/schema/upgrades/0001-slow-uniq-ruptures.sql
Please note that the following scripts are potentially dangerous and could destroy your data:
https://github.com/gem/oq-engine/tree/master/openquake/server/db/schema/upgrades/0002-danger-drop-gmf.sql
Click on the links if you want to know what exactly the scripts are doing.
Even slow script can be fast if your database is small or the upgrade affects tables that are empty.
Even dangerous scripts are fine if they affect empty tables or data you are not interested in.'''
        self.check_message('''
>0000-base_schema.sql<
>0001-slow-uniq-ruptures.sql<
>0002-danger-drop-gmf.sql<
''', expected)

    def test_updated(self):
        self.check_message(
            '', 'Your database is already updated at version 0000.')
