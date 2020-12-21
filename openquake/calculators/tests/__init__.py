# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2020 GEM Foundation
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
import builtins
import sys

import numpy

from openquake.calculators import base
from openquake.calculators.export import export
from openquake.baselib import datastore, general, parallel
from openquake.commonlib import readinput, oqvalidation, writers, logs


NOT_DARWIN = sys.platform != 'darwin'
OUTPUTS = os.path.join(os.path.dirname(__file__), 'outputs')
OQ_CALC_OUTPUTS = os.environ.get('OQ_CALC_OUTPUTS')


class DifferentFiles(Exception):
    pass


def strip_calc_id(fname):
    name = os.path.basename(fname)
    return re.sub(r'_\d+', '', name)


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


orig_open = open


def check_open(fname, mode='r', buffering=-1, encoding=None, errors=None,
               newline=None, closefd=True, opener=None):
    if (isinstance(fname, str) and fname.endswith('.xml') and 'b' not in mode
            and encoding != 'utf-8'):
        raise ValueError('Please set the encoding to utf-8!')
    return orig_open(fname, mode, buffering, encoding, errors, newline,
                     closefd, opener)


def open8(fname, mode='r'):
    return orig_open(fname, mode, encoding='utf-8')


collect_csv = {}  # outputname -> lines
orig_write_csv = writers.write_csv


def write_csv(dest, data, sep=',', fmt='%.6E', header=None, comment=None,
              renamedict=None):
    fname = orig_write_csv(dest, data, sep, fmt, header, comment, renamedict)
    if fname is None:  # writing on StringIO
        return
    lines = open(fname).readlines()[:3]
    name = re.sub(r'[\d\.]+', '.', strip_calc_id(fname))
    collect_csv[name] = lines
    return fname


class CalculatorTestCase(unittest.TestCase):
    OVERWRITE_EXPECTED = False
    edir = None  # will be set to a temporary directory

    @classmethod
    def setUpClass(cls):
        builtins.open = check_open
        export.sanity_check = True
        cls.duration = general.AccumDict()
        if OQ_CALC_OUTPUTS:
            writers.write_csv = write_csv

    def get_calc(self, testfile, job_ini, **kw):
        """
        Return the outputs of the calculation as a dictionary
        """
        self.testdir = os.path.dirname(testfile) if os.path.isfile(testfile) \
            else testfile
        params = readinput.get_params(os.path.join(self.testdir, job_ini), kw)

        oqvalidation.OqParam.calculation_mode.validator.choices = tuple(
            base.calculators)
        oq = oqvalidation.OqParam(**params)
        oq.validate()
        # change this when debugging the test
        return base.calculators(oq, logs.init())

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
        self.calc.datastore.close()
        duration = {inis[0]: self.calc._monitor.duration}
        if len(inis) == 2:
            hc_id = self.calc.datastore.calc_id
            calc = self.get_calc(
                testfile, inis[1], hazard_calculation_id=str(hc_id), **kw)
            with calc._monitor:
                exported = calc.run(export_dir=self.edir)
                result.update(exported)
            duration[inis[1]] = calc._monitor.duration
            self.calc = calc

        # reopen datastore, since some tests need to export from it
        dstore = datastore.read(self.calc.datastore.calc_id)
        self.calc.datastore = dstore
        self.__class__.duration += duration
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
            delta=1E-6, lastline=None):
        """
        Make sure the expected and actual files have the same content.
        `make_comparable` is a function processing the lines of the
        files to make them comparable. By default it does nothing,
        but in some tests a sorting function is passed, because some
        files can be equal only up to the ordering.
        """
        expected = os.path.abspath(os.path.join(self.testdir, fname1))
        if not os.path.exists(expected) and self.OVERWRITE_EXPECTED:
            expected_dir = os.path.dirname(expected)
            if not os.path.exists(expected_dir):
                os.makedirs(expected_dir)
            open8(expected, 'w').write('')
        actual = os.path.abspath(
            os.path.join(self.calc.oqparam.export_dir, fname2))
        expected_lines = [line for line in open8(expected)
                          if not line.startswith('#,')]
        comments = []
        actual_lines = []
        for line in open8(actual).readlines()[:lastline]:
            if line.startswith('#'):
                comments.append(line)
            else:
                actual_lines.append(line)
        try:
            self.assertEqual(len(expected_lines), len(actual_lines))
            self.assertEqual(expected_lines[0], actual_lines[0])  # header
            for exp, got in zip(make_comparable(expected_lines),
                                make_comparable(actual_lines)):
                if delta:
                    self.practicallyEqual(exp, got, delta)
                else:
                    self.assertEqual(exp, got)
        except AssertionError:
            if self.OVERWRITE_EXPECTED:
                # use this path when the expected outputs have changed
                # for a good reason
                logging.info('overriding %s', expected)
                open8(expected, 'w').write(''.join(comments + actual_lines))
            else:
                # normally raise an exception
                raise DifferentFiles('%s %s' % (expected, actual))

    def assertGot(self, expected_content, fname):
        """
        Make sure the content of the exported file is the expected one
        """
        if not os.path.isabs(fname):
            fname = os.path.join(self.calc.oqparam.export_dir, fname)
        if self.OVERWRITE_EXPECTED:
            open8(fname, 'w').write(expected_content)
        with open8(fname) as got:
            self.assertEqual(expected_content, got.read())

    def assertEventsByRlz(self, events_by_rlz):
        """
        Check the distribution of the events by realization index
        """
        n_events = numpy.zeros(self.calc.R, int)
        dic = general.group_array(self.calc.datastore['events'][()], 'rlz_id')
        for rlzi, events in dic.items():
            n_events[rlzi] = len(events)
        numpy.testing.assert_equal(n_events, events_by_rlz)

    def run(self, result=None):
        res = super().run(result)
        if hasattr(res, 'errors'):
            issues = len(res.errors) + len(res.failures)
        elif getattr(res, '_excinfo'):  # with pytest
            issues = len(res._excinfo)
        else:
            issues = 0
        # remove temporary dir only for success
        if self.edir and not issues:
            shutil.rmtree(self.edir)
        return res

    @classmethod
    def tearDownClass(cls):
        parallel.Starmap.shutdown()
        builtins.open = orig_open
        export.sanity_check = False
        if OQ_CALC_OUTPUTS:
            if not os.path.exists(OUTPUTS):
                os.mkdir(OUTPUTS)
            for name, lines in collect_csv.items():
                fname = os.path.join(OUTPUTS, name)
                with open(fname, 'w') as f:
                    f.write(''.join(lines))
