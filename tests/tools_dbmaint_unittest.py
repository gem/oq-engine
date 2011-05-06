# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.


"""
Unit tests for the tools/dbmaint.py tool.
"""

import os
import shutil
import tempfile
import unittest
from tools.dbmaint import error_occurred, find_scripts

def touch(path):
    """Create an empty file with the given `path`."""
    open(path, "w+").close()

class PsqlTestCase(unittest.TestCase):
    """Tests the behaviour of dbmaint.psql()."""

    def __init__(self, *args, **kwargs):
        super(PsqlTestCase, self).__init__(*args, **kwargs)


class FindScriptsTestCase(unittest.TestCase):
    """Tests the behaviour of dbmaint.find_scripts()."""

    def setUp(self):
        self.tdir = tempfile.mkdtemp()
        self.top = "%s/schema/upgrades/openquake/pshai/0.3.9-1" % self.tdir
        self.path1 = "%s/1" % self.top
        os.makedirs(self.path1)
        self.path1d = "%s/1/too_deep" % self.top
        os.makedirs(self.path1d)
        self.path2 = "%s/2" % self.top
        os.makedirs(self.path2)

    def tearDown(self):
        shutil.rmtree(self.tdir)

    def test_with_files_in_dir_too_deep_in_hierarchy(self):
        """
        Files too far up or too far down will be ignored.
        """
        touch("%s/01-too-far-up.sql" % self.top)
        touch("%s/01-too-far-down.sql" % self.path1d)
        self.assertEqual([], find_scripts(self.top))

    def test_with_non_sql_files(self):
        """
        Files with extensions other than ".sql" are ignored.
        """
        touch("%s/01-not-a-sql-file.txt" % self.path1)
        touch("%s/01-no-sql-extensionsql" % self.path2)
        self.assertEqual([], find_scripts(self.top))

    def test_with_files_at_level_two(self):
        """
        Files that are at level 3 relative to the artefact subdirectory will be
        found.
        """
        touch("%s/01-a.sql" % self.path1)
        touch("%s/02-b.sql" % self.path1)
        touch("%s/01-a.sql" % self.path2)
        self.assertEqual(["1/01-a.sql", "1/02-b.sql", "2/01-a.sql"],
                         list(sorted(find_scripts(self.top))))


class ScriptsToRunTestCase(unittest.TestCase):
    """Tests the behaviour of dbmaint.scripts_to_run()."""

    def __init__(self, *args, **kwargs):
        super(ScriptsToRunTestCase, self).__init__(*args, **kwargs)


class ErrorOccuredTestCase(unittest.TestCase):
    """Tests the behaviour of dbmaint.error_occurred()."""

    def __init__(self, *args, **kwargs):
        super(ErrorOccuredTestCase, self).__init__(*args, **kwargs)
        self.maxDiff = None

    def test_error_occured_with_error(self):
        """A psql error is detected correctly."""
        output = '''
            psql:/tmp/openquake/pshai/0.3.9-1/5/55-eee.sql:1: ERROR:  relation
            "admin.dbm_test" does not exist
            LINE 1: INSERT INTO admin.dbm_test(name) VALUES('5/55-eee.sql');
        '''
        self.assertTrue(error_occurred(output))

    def test_error_occured_with_no_error(self):
        """A psql error is not detected (which is correct)."""
        output = '''
            LINE 1: INSERT INTO admin.dbm_test(name) VALUES('5/55-eee.sql');
        '''
        self.assertFalse(error_occurred(output))


class RunScriptsTestCase(unittest.TestCase):
    """Tests the behaviour of dbmaint.run_scripts()."""

    def __init__(self, *args, **kwargs):
        super(RunScriptsTestCase, self).__init__(*args, **kwargs)
