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

from openquake.commonlib.calculators import base
from openquake.commonlib.parallel import PerformanceMonitor, executor
from openquake.commonlib import readinput


class DifferentFiles(Exception):
    pass


class CalculatorTestCase(unittest.TestCase):

    def get_calc(self, testfile, job_ini):
        """
        Return the outputs of the calculation as a dictionary
        """
        self.testdir = os.path.dirname(testfile)
        inis = [os.path.join(self.testdir, ini) for ini in job_ini.split(',')]
        oq = self.oqparam = readinput.get_oqparam(inis)
        oq.concurrent_tasks = executor._max_workers
        oq.usecache = False
        # change this when debugging the test
        monitor = PerformanceMonitor(
            self.testdir,
            monitor_csv=os.path.join(oq.export_dir, 'performance_csv'))
        return base.calculators(self.oqparam, monitor)

    def run_calc(self, testfile, job_ini):
        """
        Return the outputs of the calculation as a dictionary
        """
        self.calc = self.get_calc(testfile, job_ini)
        self.calc.pre_execute()
        self.result = self.calc.execute()
        return self.calc.post_execute(self.result)

    def execute(self, testfile, job_ini):
        """
        Return the result of the calculation without exporting it
        """
        self.calc = self.get_calc(testfile, job_ini)
        self.calc.pre_execute()
        return self.calc.execute()

    def assertEqualFiles(self, fname1, fname2):
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

    def assertGot(self, expected_content, fname):
        """
        Make sure the content of the exported file is the expected one
        """
        with open(os.path.join(self.oqparam.export_dir, fname)) as actual:
            self.assertEqual(expected_content, actual.read())
