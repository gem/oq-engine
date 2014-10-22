#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2014, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os
import unittest
from contextlib import contextmanager
from openquake.commonlib.calculators import calculators
from openquake.commonlib import readinput


class DifferentFiles(Exception):
    pass


class CalculatorTestCase(unittest.TestCase):

    @contextmanager
    def run_calc(self, testfile):
        """
        Example of usage:

        def test_calc1(self):
            with self.run_calc(__file__) as calc:
                self.assertOk('pippo.xml')

        """
        self.testdir = os.path.dirname(testfile)
        with open(os.path.join(self.testdir, 'job.ini')) as job_ini:
            self.oqparam = readinput.get_oqparam(job_ini)
            self.oqparam.concurrent_tasks = 0  # to make the test debuggable
            calc = calculators(self.oqparam)
            calc.run()
            yield calc

    def assertEqualContent(self, fname1, fname2):
        """
        Make sure the expected and actual files have the same content
        """
        expected = os.path.join(self.testdir, fname1)
        actual = os.path.join(self.oqparam.export_dir, fname2)
        expected_content = open(expected).read()
        actual_content = open(actual).read()
        try:
            self.assertEqual(expected_content, actual_content)
        except:
            raise DifferentFiles('%s %s' % (expected, actual))
