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


import os
import unittest

from tests.utils import helpers


class LogFileTestCase(unittest.TestCase):
    """Tests for the --log-file openquake command line option."""

    def test_log_file(self):
        # Test logging to a file when running bin/oqscript.py.
        uhs_cfg = helpers.demo_file('uhs/config.gem')

        log_file = './%s.log' % helpers.random_string()
        self.assertFalse(os.path.exists(log_file))

        ret_code = helpers.run_job(
            uhs_cfg, ['--log-level', 'debug', '--log-file', log_file])
        self.assertEqual(0, ret_code)

        self.assertTrue(os.path.exists(log_file))
        # Make sure there is something in it.
        self.assertTrue(os.path.getsize(log_file) > 0)

        os.unlink(log_file)

    def test_log_file_access_denied(self):
        # Attempt to log to a location for which the user does not have write
        # access ('/', for example).
        uhs_cfg = helpers.demo_file('uhs/config.gem')

        result = helpers.run_job(uhs_cfg, ['--log-file', '/oq.log'],
                                 check_output=True)
        self.assertEqual(
            'Error writing to log file /oq.log: Permission denied\n',
            result)
