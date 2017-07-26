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
import re
import shutil
import logging
import tempfile
import unittest
import platform

import numpy

from openquake.calculators import base
from openquake.baselib.performance import Monitor
from openquake.commonlib import readinput, oqvalidation, datastore


REFERENCE_OS = 'Ubuntu-16.04' in platform.platform()


class DifferentFiles(Exception):
    pass


def strip_calc_id(fname):
    name = os.path.basename(fname)
    return re.sub('_\d+\.', '.', name)


def columns(line):
    data = []
    if ',' in line:  # csv file
        for column in line.split(','):
            try:
                floats = list(map(float, column.split(' ')))
            except ValueError:  # skip header
                pass
            else:
                data.append(numpy.array(floats))
    else:  # txt file
        for column in line.split(' '):
            try:
                data.append(float(column))
            except ValueError:
                pass  # ignore nonfloats
    return data


class CalculatorTestCase(unittest.TestCase):
    OVERWRITE_EXPECTED = False
    edir = None  # will be set to a temporary directory

    def get_calc(self, testfile, job_ini, **kw):
        """
        Return the outputs of the calculation as a dictionary
        """
        self.testdir = os.path.dirname(testfile) if os.path.isfile(testfile) \
            else testfile
        inis = [os.path.join(self.testdir, ini) for ini in job_ini.split(',')]
        params = readinput.get_params(inis)
        params.update(kw)

        oqvalidation.OqParam.calculation_mode.validator.choices = tuple(
            base.calculators)
        oq = oqvalidation.OqParam(**params)
        oq.validate()
        # change this when debugging the test
        monitor = Monitor(self.testdir)
        return base.calculators(oq, monitor)

    def run_calc(self, testfile, job_ini, **kw):
        """
        Return the outputs of the calculation as a dictionary
        """
        inis = job_ini.split(',')
        assert len(inis) in (1, 2), inis
        self.calc = self.get_calc(testfile, inis[0], **kw)
        self.edir = tempfile.mkdtemp()
        with self.calc._monitor:
            result = self.calc.run(export_dir=self.edir)
        if len(inis) == 2:
            hc_id = self.calc.datastore.calc_id
            self.calc = self.get_calc(
                testfile, inis[1], hazard_calculation_id=str(hc_id), **kw)
            with self.calc._monitor:
                result.update(self.calc.run(export_dir=self.edir))
        # reopen datastore, since some tests need to export from it
        dstore = datastore.read(self.calc.datastore.calc_id)
        self.calc.datastore = dstore
        return result

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
            numpy.testing.assert_allclose(c1, c2, atol=delta, rtol=delta)

    def assertEqualFiles(
            self, fname1, fname2, make_comparable=lambda lines: lines,
            delta=None, lastline=None):
        """
        Make sure the expected and actual files have the same content.
        `make_comparable` is a function processing the lines of the
        files to make them comparable. By default it does nothing,
        but in some tests a sorting function is passed, because some
        files can be equal only up to the ordering.
        """
        expected = os.path.abspath(os.path.join(self.testdir, fname1))
        if not os.path.exists(expected) and self.OVERWRITE_EXPECTED:
            open(expected, 'w').write('')
        actual = os.path.abspath(
            os.path.join(self.calc.oqparam.export_dir, fname2))
        expected_lines = make_comparable(open(expected).readlines())
        actual_lines = make_comparable(open(actual).readlines()[:lastline])
        try:
            self.assertEqual(len(expected_lines), len(actual_lines))
            for exp, got in zip(expected_lines, actual_lines):
                if delta:
                    self.practicallyEqual(exp, got, delta)
                else:
                    self.assertEqual(exp, got)
        except AssertionError:
            if self.OVERWRITE_EXPECTED:
                # use this path when the expected outputs have changed
                # for a good reason
                logging.info('overriding %s', expected)
                open(expected, 'w').write(''.join(actual_lines))
            else:
                # normally raise an exception
                raise DifferentFiles('%s %s' % (expected, actual))

    def assertGot(self, expected_content, fname):
        """
        Make sure the content of the exported file is the expected one
        """
        with open(os.path.join(self.calc.oqparam.export_dir, fname)) as actual:
            self.assertEqual(expected_content, actual.read())

    def run(self, result=None):
        res = super(CalculatorTestCase, self).run(result)
        if res is not None:  # for Python 3
            issues = len(res.errors) + len(res.failures)
        else:
            issues = 0  # this is bad, but Python 2 will die soon or later
        # remove temporary dir only for success
        if self.edir and not issues:
            shutil.rmtree(self.edir)
        return res
