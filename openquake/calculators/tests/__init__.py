# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2023 GEM Foundation
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
from openquake.baselib import general, parallel, writers
from openquake.commonlib import datastore, readinput, oqvalidation, logs


NOT_DARWIN = sys.platform != 'darwin'
OUTPUTS = os.path.join(os.path.dirname(__file__), 'outputs')
OQ_CALC_OUTPUTS = os.environ.get('OQ_CALC_OUTPUTS')


class DifferentFiles(Exception):
    pass


def strip_calc_id(fname):
    name = os.path.basename(fname)
    return re.sub(r'_\d+', '', name)


def ignore_gsd_fields(header, lines):
    # strip columns starting with gsd_ (used when checking avg_gmf)
    h = header.split(',')
    for i, line in enumerate(lines):
        stripped = [val for col, val in zip(h, line.split(','))
                    if not col.startswith('gsd_')]
        lines[i] = ','.join(stripped)
    return lines


def columns(line):
    numeric_columns = []
    textual_columns = []
    if ',' in line:  # csv file
        for column in line.split(','):
            try:
                floats = list(map(float, column.split(' ')))
            except ValueError:
                textual_columns.append(column)
            else:
                numeric_columns.append(numpy.array(floats))
    elif '|' in line:  # org file
        for column in line.split('|'):
            try:
                numeric_columns.append(float(column))
            except ValueError:
                textual_columns.append(column)
    else:  # txt file
        for column in line.split(' '):
            try:
                numeric_columns.append(float(column))
            except ValueError:
                textual_columns.append(column)
    return numeric_columns, textual_columns


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
        os.environ['OQ_DATABASE'] = 'local'
        parallel.Starmap.maxtasksperchild = None

    def get_calc(self, testfile, job_ini, **kw):
        """
        Return the outputs of the calculation as a dictionary
        """
        self.testdir = os.path.dirname(testfile) if os.path.isfile(testfile) \
            else testfile
        params = readinput.get_params(os.path.join(self.testdir, job_ini), kw)
        oq = oqvalidation.OqParam(**params)
        oq._input_files = readinput.get_input_files(oq)
        oq.validate()
        # change this when debugging the test
        log = logs.init('calc', params)
        return base.calculators(oq, log.calc_id)

    def run_calc(self, testfile, job_ini, **kw):
        """
        Return the outputs of the calculation as a dictionary
        """
        inis = job_ini.split(',')
        assert len(inis) in (1, 2), inis
        self.calc = self.get_calc(testfile, inis[0], **kw)
        self.edir = tempfile.mkdtemp()
        with self.calc._monitor:
            result = self.calc.run(export_dir=self.edir,
                                   exports=kw.get('exports', ''))
        self.calc.datastore.close()
        duration = {inis[0]: self.calc._monitor.duration}
        if len(inis) == 2:
            hc_id = self.calc.datastore.calc_id
            calc = self.get_calc(
                testfile, inis[1], hazard_calculation_id=str(hc_id), **kw)
            with calc._monitor:
                exported = calc.run(export_dir=self.edir,
                                    exports=kw.get('exports', ''))
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

    def practicallyEqual(self, line1, line2, delta, check_text=False):
        """
        Compare lines containing numbers up to the given delta
        If check_text is True, also textual values are compared
        """
        num_columns1, txt_columns1 = columns(line1)
        num_columns2, txt_columns2 = columns(line2)
        for c1, c2 in zip(num_columns1, num_columns2):
            numpy.testing.assert_allclose(c1, c2, atol=delta, rtol=delta)
        if check_text:
            for txt_c1, txt_c2 in zip(txt_columns1, txt_columns2):
                self.assertEqual(txt_c1, txt_c2)

    def assertEqualFiles(
            self, fname1, fname2, make_comparable=lambda header, lines: lines,
            delta=1E-6, lastline=None, check_text=False):
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
            header = expected_lines[0]
            if header[0] != '+':  # header unless .rst table
                self.assertEqual(header, actual_lines[0])
            for exp, got in zip(make_comparable(header, expected_lines),
                                make_comparable(header, actual_lines)):
                if delta:
                    self.practicallyEqual(exp, got, delta, check_text)
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
        parallel.Starmap.maxtasksperchild = 1
        builtins.open = orig_open
        export.sanity_check = False
        if OQ_CALC_OUTPUTS:
            if not os.path.exists(OUTPUTS):
                os.mkdir(OUTPUTS)
            for name, lines in collect_csv.items():
                fname = os.path.join(OUTPUTS, name)
                with open(fname, 'w') as f:
                    f.write(''.join(lines))
