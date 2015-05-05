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

import numpy

from openquake.commonlib.calculators import base
from openquake.commonlib.parallel import PerformanceMonitor
from openquake.commonlib import readinput, oqvalidation


class DifferentFiles(Exception):
    pass


def columns(line):
    data = []
    for column in line.split(','):
        data.append(numpy.array(map(float, column.split(' '))))
    return data


class CalculatorTestCase(unittest.TestCase):
    OVERWRITE_EXPECTED = False

    def get_calc(self, testfile, job_ini, **kw):
        """
        Return the outputs of the calculation as a dictionary
        """
        self.testdir = os.path.dirname(testfile) if os.path.isfile(testfile) \
            else testfile
        inis = [os.path.join(self.testdir, ini) for ini in job_ini.split(',')]
        params = readinput.get_params(inis)
        kw.setdefault('usecache', '0')
        params.update(kw)
        oq = oqvalidation.OqParam(**params)
        oq.validate()
        # change this when debugging the test
        monitor = PerformanceMonitor(
            self.testdir,
            monitor_csv=os.path.join(oq.export_dir, 'performance.csv'))
        return base.calculators(oq, monitor)

    def run_calc(self, testfile, job_ini, **kw):
        """
        Return the outputs of the calculation as a dictionary
        """
        self.calc = self.get_calc(testfile, job_ini, **kw)
        self.calc.run()
        return self.calc.datastore['exported']

    def execute(self, testfile, job_ini):
        """
        Return the result of the calculation without exporting it
        """
        self.calc = self.get_calc(testfile, job_ini)
        self.calc.pre_execute()
        return self.calc.execute()

    def practicallyEqual(self, line1, line2, delta):
        """
        Compare lines containing numbers up to the given delta
        """
        columns1 = columns(line1)
        columns2 = columns(line2)
        for c1, c2 in zip(columns1, columns2):
            numpy.testing.assert_allclose(c1, c2, atol=delta)

    def assertEqualFiles(
            self, fname1, fname2, make_comparable=lambda lines: lines,
            delta=None):
        """
        Make sure the expected and actual files have the same content.
        `make_comparable` is a function processing the lines of the
        files to make them comparable. By default it does nothing,
        but in some tests sorting function is passed, because some
        files can be equal only up to the ordering.
        """
        expected = os.path.join(self.testdir, fname1)
        actual = os.path.join(self.calc.oqparam.export_dir, fname2)
        expected_content = ''.join(
            make_comparable(open(expected).readlines()))
        actual_content = ''.join(make_comparable(open(actual).readlines()))
        try:
            if delta:
                self.practicallyEqual(expected_content, actual_content, delta)
            else:
                self.assertEqual(expected_content, actual_content)
        except AssertionError:
            if self.OVERWRITE_EXPECTED:
                # use this path when the expected outputs have changed
                # for a good reason
                open(expected, 'w').write(actual_content)
            else:
                # normally raise an exception
                raise DifferentFiles('%s %s' % (expected, actual))

    def assertGot(self, expected_content, fname):
        """
        Make sure the content of the exported file is the expected one
        """
        with open(os.path.join(self.calc.oqparam.export_dir, fname)) as actual:
            self.assertEqual(expected_content, actual.read())
