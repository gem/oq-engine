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
from tools.dbmaint import (
    error_occurred, find_scripts, psql, run_cmd, scripts_to_run)


def touch(path):
    """Create an empty file with the given `path`."""
    open(path, "w+").close()


class RunCmdTestCase(unittest.TestCase):
    """Tests the behaviour of dbmaint.run_cmd()."""

    def test_run_cmd_with_success(self):
        """Invoke a command without errors."""
        code, out, err = run_cmd(["echo", "-n", "Hello world!"])
        self.assertEqual(0, code)
        self.assertEqual("Hello world!", out)
        self.assertEqual("", err)

    def test_run_cmd_with_errors(self):
        """Invoke a command with errors."""
        try:
            code, out, err = run_cmd(["ls", "-AF", "/this/does/not/exist"])
        except Exception, e:
            self.assertEqual(
                "ls terminated with exit code: 2\nls: cannot access "
                "/this/does/not/exist: No such file or directory\n", e.args[0])
        else:
            raise Exception("exception not raised")

    def test_run_cmd_with_errors_and_ignore_exit_code(self):
        """Invoke a command with errors but ignore the exit code."""
        code, out, err = run_cmd(
            ["ls", "-AF", "/this/does/not/exist"], ignore_exit_code=True)
        self.assertEqual(2, code)
        self.assertEqual("", out)
        self.assertEqual("ls: cannot access /this/does/not/exist: No such "
                         "file or directory\n", err)


class PsqlTestCase(unittest.TestCase):
    """Tests the behaviour of dbmaint.psql()."""

    def test_psql_cmd_with_script(self):
        """Tests the psql command params with an SQL script file."""
        def fake_runner(cmds):
            """Fake serialization function to be used in this test."""
            fake_runner.args = cmds
        fake_runner.args = []

        config = {"dryrun": False, "path": "/tmp", "host": "localhost",
                  "db": "0penquark", "user": "postgres"}
        psql(config, script="xxx", runner=fake_runner)
        self.assertEqual(
            ["psql", "-d", "0penquark", "-U", "postgres", "-f", "/tmp/xxx"],
            fake_runner.args)

    def test_psql_cmd_with_command(self):
        """Tests the psql command params with an SQL command."""
        def fake_runner(cmds):
            """Fake serialization function to be used in this test."""
            fake_runner.args = cmds
        fake_runner.args = []

        config = {"dryrun": False, "path": "/tmp", "host": "localhost",
                  "db": "openquake", "user": "chuckn"}
        psql(config, cmd="SELECT * from admin.revision_info",
             runner=fake_runner)
        self.assertEqual(
            ["psql", "-d", "openquake", "-U", "chuckn", "-c",
             "SELECT * from admin.revision_info"], fake_runner.args)

    def test_psql_with_non_local_host(self):
        """
        The `-h` flag *is* specified in the `psql` command when the host in
        the configuration is not `localhost`.
        """
        def fake_runner(cmds):
            """Fake serialization function to be used in this test."""
            fake_runner.args = cmds
        fake_runner.args = []

        config = {"dryrun": False, "path": "/tmp", "host": "gozilla",
                  "db": "openquake", "user": "postgres"}
        psql(config, cmd="SELECT * from admin.revision_info",
             runner=fake_runner)
        self.assertTrue("-h" in fake_runner.args)

    def test_psql_with_local_host(self):
        """
        Does not specify the `-h` flag in the `psql` command when the host in
        the configuration is `localhost`.
        """
        def fake_runner(cmds):
            """Fake serialization function to be used in this test."""
            fake_runner.args = cmds
        fake_runner.args = []

        config = {"dryrun": False, "path": "/tmp", "host": "localhost",
                  "db": "openquake", "user": "postgres"}
        psql(config, cmd="SELECT * from admin.revision_info",
             runner=fake_runner)
        self.assertTrue("-h" not in fake_runner.args)

    def test_psql_with_local_host_ip(self):
        """
        Does not specify the `-h` flag in the `psql` command when the host in
        the configuration is `127.0.0.1`.
        """
        def fake_runner(cmds):
            """Fake serialization function to be used in this test."""
            fake_runner.args = cmds
        fake_runner.args = []

        config = {"dryrun": False, "path": "/tmp", "host": "127.0.0.1",
                  "db": "openquake", "user": "postgres"}
        psql(config, cmd="SELECT * from admin.revision_info",
             runner=fake_runner)
        self.assertTrue("-h" not in fake_runner.args)

    def test_psql_with_dry_run_flag(self):
        """
        Does not call the psql command if the `dryrun` flag is set in
        the configuration.
        """
        def fake_runner(cmds):
            """Fake serialization function to be used in this test."""
            fake_runner.number_of_calls += 1
        fake_runner.number_of_calls = 0

        config = {"dryrun": True, "path": "/tmp", "host": "localhost",
                  "db": "openquake", "user": "postgres"}
        psql(config, cmd="SELECT * from admin.revision_info",
             runner=fake_runner)
        self.assertEqual(0, fake_runner.number_of_calls)

    def test_psql_with_ignored_dry_run_flag(self):
        """
        Calls the psql command if the `dryrun` flag is set in the configuration
        but the 'ignore_dryrun' parameter is set to `True`.
        """
        def fake_runner(cmds):
            """Fake serialization function to be used in this test."""
            fake_runner.number_of_calls += 1
        fake_runner.number_of_calls = 0

        config = {"dryrun": True, "path": "/tmp", "host": "localhost",
                  "db": "openquake", "user": "postgres"}
        psql(config, cmd="SELECT * from admin.revision_info",
             ignore_dryrun=True, runner=fake_runner)
        self.assertEqual(1, fake_runner.number_of_calls)

    def test_psql_with_both_script_and_command(self):
        """
        Raises an `Exception` if both a command and a script are passed.
        """
        config = {"dryrun": True, "path": "/tmp", "host": "localhost",
                  "db": "openquake", "user": "postgres"}
        try:
            psql(config, cmd="SELECT * from admin.revision_info", script="xxx")
        except Exception, e:
            self.assertEqual(
                "Please specify either an SQL script or a command.", e.args[0])
        else:
            raise Exception("exception not raised")

    def test_psql_with_neither_script_nor_command(self):
        """
        Raises an `Exception` if neither a command nor a script are passed.
        """
        config = {"dryrun": True, "path": "/tmp", "host": "localhost",
                  "db": "openquake", "user": "postgres"}
        try:
            psql(config)
        except Exception, e:
            self.assertEqual(
                "Neither SQL script nor command specified.", e.args[0])
        else:
            raise Exception("exception not raised")


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

    def setUp(self):
        self.tdir = tempfile.mkdtemp()
        self.path = "%s/schema/upgrades" % self.tdir
        self.top = "%s/openquake/pshai/0.3.9-1" % self.path
        self.path1 = "%s/1" % self.top
        os.makedirs(self.path1)
        self.path1d = "%s/1/too_deep" % self.top
        os.makedirs(self.path1d)
        self.path2 = "%s/2" % self.top
        os.makedirs(self.path2)
        self.path3 = "%s/3" % self.top
        os.makedirs(self.path3)

    def tearDown(self):
        shutil.rmtree(self.tdir)

    def test_scripts_to_run_with_no_upgrades(self):
        """No upgrades are available."""
        artefact = "openquake/pshai"
        rev_info = {"step": "2", "id": "3", "revision": "0.3.9-1"}
        config = {"dryrun": True, "path": self.path, "host": "localhost",
                  "db": "openquake", "user": "postgres"}
        touch("%s/01-a.sql" % self.path1)
        touch("%s/01-a.sql" % self.path2)
        self.assertEqual([], scripts_to_run(artefact, rev_info, config))

    def test_scripts_to_run_with_available_upgrades(self):
        """Upgrades are available."""
        artefact = "openquake/pshai"
        rev_info = {"step": "2", "id": "3", "revision": "0.3.9-1"}
        config = {"dryrun": True, "path": self.path, "host": "localhost",
                  "db": "openquake", "user": "postgres"}
        touch("%s/01-a.sql" % self.path1)
        touch("%s/01-b.sql" % self.path2)
        touch("%s/01-c.sql" % self.path3)
        touch("%s/02-d.sql" % self.path3)
        self.assertEqual(["3/01-c.sql", "3/02-d.sql"],
                         scripts_to_run(artefact, rev_info, config))


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
