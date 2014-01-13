# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.


"""
Unit tests for the tools/dbmaint.py tool.
"""

from distutils import version
import os
import shutil
import sys
import tempfile
import unittest
from openquake.engine.tests.utils.helpers import patch
from tools.dbmaint import (
    error_occurred, find_scripts, psql, run_cmd, run_scripts, scripts_to_run,
    version_key, script_sort_key)


def touch(path):
    """Create an empty file with the given `path`."""
    open(path, "w+").close()


class RunCmdTestCase(unittest.TestCase):
    """Tests the behaviour of dbmaint.run_cmd()."""

    def setUp(self):
        self.orig_env = os.environ.copy()
        os.environ["LANG"] = 'C'

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.orig_env)

    def test_run_cmd_with_success(self):
        """Invoke a command without errors."""
        code, out, err = run_cmd(["echo", "-n", "Hello world!"])
        self.assertEqual(0, code)
        self.assertEqual("Hello world!", out)
        self.assertEqual("", err)

    def test_run_cmd_with_errors(self):
        """Invoke a command with errors."""
        # The expected error message varies between Linux and OSX.
        if sys.platform == 'darwin':
            expected_error = ('ls terminated with exit code: 1\nls: '
                '/this/does/not/exist: No such file or directory\n')
        else:
            expected_error = ('ls terminated with exit code: 2\nls: cannot '
                'access /this/does/not/exist: No such file or directory\n')

        try:
            code, out, err = run_cmd(["ls", "-AF", "/this/does/not/exist"])
        except Exception, e:
            self.assertEqual(expected_error, e.args[0])
        else:
            self.fail("exception not raised")

    def test_run_cmd_with_errors_and_ignore_exit_code(self):
        """Invoke a command with errors but ignore the exit code."""
        # Both the expected exit code and error message vary between Linux and
        # OSX.
        if sys.platform == 'darwin':
            expected_code = 1
            expected_error = ("ls: /this/does/not/exist: No such file or "
                "directory\n")
        else:
            expected_code = 2
            expected_error = ("ls: cannot access /this/does/not/exist: No such"
                " file or directory\n")

        code, out, err = run_cmd(
            ["ls", "-AF", "/this/does/not/exist"], ignore_exit_code=True)
        self.assertEqual(expected_code, code)
        self.assertEqual("", out)
        self.assertEqual(expected_error, err)


class PsqlTestCase(unittest.TestCase):
    """Tests the behaviour of dbmaint.psql()."""

    def test_psql_cmd_with_script(self):
        """Tests the psql command params with an SQL script file."""
        def fake_runner(cmds):
            """Fake command runner function to be used in this test."""
            fake_runner.args = cmds
        fake_runner.args = []

        config = {"dryrun": False, "path": "/tmp", "host": "localhost",
                  "db": "0penquark", "user": "postgres"}
        psql(config, script="xxx", runner=fake_runner)
        self.assertEqual(
            ["psql", "--set", "ON_ERROR_STOP=1", "-d", "0penquark", "-U",
             "postgres", "-f", "/tmp/xxx"],
            fake_runner.args)

    def test_psql_cmd_with_command(self):
        """Tests the psql command params with an SQL command."""
        def fake_runner(cmds):
            """Fake command runner function to be used in this test."""
            fake_runner.args = cmds
        fake_runner.args = []

        config = {"dryrun": False, "path": "/tmp", "host": "localhost",
                  "db": "openquake", "user": "chuckn"}
        psql(config, cmd="SELECT * from admin.revision_info",
             runner=fake_runner)
        self.assertEqual(
            ["psql", "--set", "ON_ERROR_STOP=1", "-d", "openquake", "-U",
             "chuckn", "-c", "SELECT * from admin.revision_info"],
            fake_runner.args)

    def test_psql_with_non_local_host(self):
        """
        The `-h` flag *is* specified in the `psql` command when the host in
        the configuration is not `localhost`.
        """
        def fake_runner(cmds):
            """Fake command runner function to be used in this test."""
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
            """Fake command runner function to be used in this test."""
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
            """Fake command runner function to be used in this test."""
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
            """Fake command runner function to be used in this test."""
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
            """Fake command runner function to be used in this test."""
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
            self.fail("exception not raised")

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
            self.fail("exception not raised")


class FindScriptsTestCase(unittest.TestCase):
    """Tests the behaviour of dbmaint.find_scripts()."""

    def setUp(self):
        self.tdir = tempfile.mkdtemp()
        self.top = "%s/schema/upgrades/openquake/hzrdi/0.3.9-1" % self.tdir
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
        touch("%s/03-c.py" % self.path1)
        touch("%s/01-a.sql" % self.path2)
        self.assertEqual(["1/01-a.sql", "1/02-b.sql", "1/03-c.py",
                          "2/01-a.sql"],
                         list(sorted(find_scripts(self.top))))


class ScriptsToRunTestCase(unittest.TestCase):
    """Tests the behaviour of dbmaint.scripts_to_run()."""

    def setUp(self):
        self.tdir = tempfile.mkdtemp()
        self.path = "%s/schema/upgrades" % self.tdir
        self.top = "%s/" % self.path
        # older revision
        self.path_38_1 = "%s/0.3.8/1" % self.top
        os.makedirs(self.path_38_1)
        self.path_38_5 = "%s/0.3.8/5" % self.top
        os.makedirs(self.path_38_5)
        # current revision
        self.path_39_1 = "%s/0.3.9-1/1" % self.top
        os.makedirs(self.path_39_1)
        self.path_39_1d = "%s/0.3.9-1/1/too_deep" % self.top
        os.makedirs(self.path_39_1d)
        self.path_39_2 = "%s/0.3.9-1/2" % self.top
        os.makedirs(self.path_39_2)
        self.path_39_3 = "%s/0.3.9-1/3" % self.top
        os.makedirs(self.path_39_3)
        # newer revision
        self.path_42_1 = "%s/0.4.2/1" % self.top
        os.makedirs(self.path_42_1)

    def tearDown(self):
        shutil.rmtree(self.tdir)

    def test_scripts_to_run_with_no_upgrades(self):
        """No upgrades are available."""
        artefact = "openquake/hzrdi"
        rev_info = {"step": "2", "id": "3", "revision": "0.3.9-1"}
        config = {"dryrun": True, "path": self.path, "host": "localhost",
                  "db": "openquake", "user": "postgres"}
        touch("%s/01-a.sql" % self.path_38_1)
        touch("%s/01-a.sql" % self.path_38_5)
        touch("%s/01-a.sql" % self.path_39_1)
        touch("%s/01-a.sql" % self.path_39_2)
        self.assertEqual([], scripts_to_run(artefact, rev_info, config))

    def test_scripts_to_run_with_available_upgrades(self):
        """Upgrades are available."""
        artefact = "openquake/hzrdi"
        rev_info = {"step": "2", "id": "3", "revision": "0.3.9-1"}
        config = {"dryrun": True, "path": self.path, "host": "localhost",
                  "db": "openquake", "user": "postgres"}
        touch("%s/01-a.sql" % self.path_38_1)
        touch("%s/01-a.sql" % self.path_39_1)
        touch("%s/01-a.sql" % self.path_38_5)
        touch("%s/01-b.sql" % self.path_39_2)
        touch("%s/01-c.sql" % self.path_39_3)
        touch("%s/02-d.sql" % self.path_39_3)
        touch("%s/01-a.sql" % self.path_42_1)
        touch("%s/02-b.sql" % self.path_42_1)
        self.assertEqual(["0.3.9-1/3/01-c.sql", "0.3.9-1/3/02-d.sql",
                          "0.4.2/1/01-a.sql", "0.4.2/1/02-b.sql"],
                         scripts_to_run(artefact, rev_info, config))


class ErrorOccuredTestCase(unittest.TestCase):
    """Tests the behaviour of dbmaint.error_occurred()."""

    def test_error_occured_with_error(self):
        """A psql error is detected correctly."""
        output = '''
            psql:/tmp/openquake/hzrdi/0.3.9-1/5/55-eee.sql:1: ERROR:  relation
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

    def test_run_scripts_with_available_upgrades(self):
        """
        The `psql` function is called for every upgrade script and at the
        very end to update the revision step.
        """

        artefact = "openquake/hzrdi"
        rev_info = {"step": "2", "id": "3", "revision": "0.3.9-1"}
        config = {"dryrun": True, "path": "/tmp", "host": "localhost",
                  "db": "openquake", "user": "postgres"}
        scripts = ["0.3.9-1/3/01-c.sql", "0.3.9-1/3/02-d.sql",
                   "0.4.2/2/01-a.sql"]
        with patch('tools.dbmaint.psql') as mock_psql:
            # Make all the calls pass.
            mock_psql.return_value = (0, "", "")

            # Run the actual function that is to be tested.
            run_scripts(artefact, rev_info, scripts, config)

            # The mock was called four times.
            self.assertEqual(4, mock_psql.call_count)
            # The first call executed an SQL script.
            self.assertEqual({"script": "0.3.9-1/3/01-c.sql"},
                             mock_psql.call_args_list[0][1])
            # The second call executed the second SQL script.
            self.assertEqual({"script": "0.3.9-1/3/02-d.sql"},
                             mock_psql.call_args_list[1][1])
            # The third call executed the second SQL script.
            self.assertEqual({"script": "0.4.2/2/01-a.sql"},
                             mock_psql.call_args_list[2][1])
            # The last call executed the command to update the revision step.
            self.assertEqual(
                {"cmd": "UPDATE admin.revision_info SET step=2, "
                        "revision='0.4.2', "
                        "last_update=timezone('UTC'::text, now()) WHERE "
                        "artefact='openquake/hzrdi' AND revision = '0.3.9-1'"},
                mock_psql.call_args_list[3][1])

    def test_run_scripts_with_failing_upgrades(self):
        """Upgrades are available but the second one will fail."""
        def fail_on_first_even_script(
            config, script=None, cmd=None, ignore_dryrun=False, runner=None):
            """Pretend that the second SQL script failed on execution."""
            if script and script.find("02-d.sql") >= 0:
                return(1, "", '02-d.sql:1: ERROR:  relation "admin.dbm_test" ')
            else:
                return(0, "All goood", "")

        artefact = "openquake/hzrdi"
        rev_info = {"step": "2", "id": "3", "revision": "0.3.9-1"}
        config = {"dryrun": False, "path": "/tmp", "host": "localhost",
                  "db": "openquake", "user": "postgres"}
        scripts = ["0.3.9-1/3/01-c.sql", "0.3.9-1/3/02-d.sql",
                   "0.4.2/1/01-a.sql"]
        with patch('tools.dbmaint.psql') as mock_psql:
            # Make all the calls pass.
            mock_psql.side_effect = fail_on_first_even_script

            # Run the actual function that is to be tested.
            run_scripts(artefact, rev_info, scripts, config)

            # The mock was called thrice.
            self.assertEqual(3, mock_psql.call_count)
            # The first call executed an SQL script.
            self.assertEqual({"script": "0.3.9-1/3/01-c.sql"},
                             mock_psql.call_args_list[0][1])
            # The second call executed the second SQL script.
            self.assertEqual({"script": "0.3.9-1/3/02-d.sql"},
                             mock_psql.call_args_list[1][1])
            # Please note how the step is assigned a -1 value which indicates
            # a database upgrade failure.
            self.assertEqual(
                {"cmd": "UPDATE admin.revision_info SET step=-1, "
                        "revision='0.3.9-1', "
                        "last_update=timezone('UTC'::text, now()) WHERE "
                        "artefact='openquake/hzrdi' AND revision = '0.3.9-1'"},
                mock_psql.call_args_list[2][1])


class VersionKeyTestCase(unittest.TestCase):
    """Tests the behaviour of dbmaint.version_key()."""

    def test_version_with_dash(self):
        self.assertEquals('3.9.1', str(version_key('3.9.1-1')))

    def test_plain_version(self):
        self.assertEquals('3.9.1', str(version_key('3.9.1')))


class ScriptSortKeyTestCase(unittest.TestCase):
    """Tests the behaviour of dbmaint.script_sort_key()."""

    def test_sanity(self):
        self.assertEquals((version.StrictVersion("0.3.9"), 7, "01-a.sql"),
                          script_sort_key("0.3.9-1/7/01-a.sql"))

    def test_different_revision(self):
        self.assertTrue(script_sort_key("0.3.9-1/1/01-a.sql") <
                        script_sort_key("0.4.2/1/01-a.sql"))
        self.assertTrue(script_sort_key("0.3.9-1/1/01-a.sql") <
                        script_sort_key("0.3.10/1/01-a.sql"))
        self.assertTrue(script_sort_key("0.3.9-1/4/01-a.sql") <
                        script_sort_key("0.4.2/1/01-a.sql"))
        self.assertTrue(script_sort_key("0.3.9-1/1/04-a.sql") <
                        script_sort_key("0.4.2/1/01-a.sql"))

    def test_different_step(self):
        self.assertTrue(script_sort_key("0.4.2/1/01-a.sql") <
                        script_sort_key("0.4.2/2/01-a.sql"))
        self.assertTrue(script_sort_key("0.4.2/9/01-a.sql") <
                        script_sort_key("0.4.2/10/01-a.sql"))

    def test_different_file(self):
        self.assertTrue(script_sort_key("0.3.9-1/1/01-a.sql") <
                        script_sort_key("0.3.9-1/1/02-a.sql"))
        self.assertTrue(script_sort_key("0.4.2/1/01-a.sql") <
                        script_sort_key("0.4.2/1/02-a.sql"))
