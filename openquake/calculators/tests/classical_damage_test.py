# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2020 GEM Foundation
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

from openquake.qa_tests_data.classical_damage import (
    case_01, case_02, case_01a, case_01b, case_01c, case_02a, case_02b,
    case_03a, case_04a, case_04b, case_04c, case_05a, case_06a, case_06b,
    case_07a, case_07b, case_07c, case_08a, case_master)
from openquake.calculators.export import export
from openquake.calculators.tests import (
    CalculatorTestCase, strip_calc_id, NOT_DARWIN)

import numpy

aae = numpy.testing.assert_almost_equal


class ClassicalDamageCase1TestCase(CalculatorTestCase):

    def test_continuous(self):
        self.run_calc(case_01.__file__, 'job_continuous.ini')
        [fname] = export(('damages-rlzs', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/damage_continuous.csv', fname)

    def test_discrete(self):
        self.run_calc(case_01.__file__, 'job_discrete.ini')
        [fname] = export(('damages-rlzs', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/damage_discrete.csv', fname)

    def test_interpolation(self):
        self.run_calc(case_01.__file__, 'job_interpolation.ini')
        [fname] = export(('damages-rlzs', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/damage_interpolation.csv', fname)


# tests with no damage limit
class ClassicalDamageCase2TestCase(CalculatorTestCase):

    def test_continuous(self):
        self.run_calc(case_02.__file__, 'job_continuous.ini')
        [fname] = export(('damages-rlzs', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/damage_continuous.csv', fname)

    def test_discrete(self):
        # a test producing NaNs
        self.run_calc(case_02.__file__, 'job_discrete.ini')
        [fname] = export(('damages-rlzs', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/damage_discrete.csv', fname)

    def test_interpolation(self):
        self.run_calc(case_02.__file__, 'job_interpolation.ini')
        [fname] = export(('damages-rlzs', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/damage_interpolation.csv', fname)


class ClassicalDamageCase8TestCase(CalculatorTestCase):

    def test_case_08a(self):
        self.run_calc(
            case_08a.__file__, 'job_haz.ini,job_risk.ini')
        f1, f2 = export(('damages-rlzs', 'csv'), self.calc.datastore)
        self.assertEqualFiles(
            'expected/damages-rlzs-AkkarBommer2010().csv', f2)
        self.assertEqualFiles(
            'expected/damages-rlzs-SadighEtAl1997().csv', f1)
        [f] = export(('damages-stats', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/damages-stats.csv', f)


class ClassicalDamageTestCase(CalculatorTestCase):
    # all the tests here are similar

    def check(self, case):
        self.run_calc(case.__file__, 'job_haz.ini')
        self.run_calc(case.__file__, 'job_risk.ini',
                      hazard_calculation_id=str(self.calc.datastore.calc_id))
        fnames = export(('damages-rlzs', 'csv'), self.calc.datastore)
        if len(fnames) == 1:
            self.assertEqualFiles('expected/damages.csv', fnames[0])
        else:
            for fname in fnames:
                self.assertEqualFiles(
                    'expected/%s' % strip_calc_id(fname), fname)

    def test_case_01a(self):
        self.check(case_01a)

    def test_case_01b(self):
        self.check(case_01b)

    def test_case_01c(self):
        self.check(case_01c)

    def test_case_02a(self):
        self.check(case_02a)

    def test_case_02b(self):
        self.check(case_02b)

    def test_case_03a(self):
        self.check(case_03a)

    def test_case_04a(self):
        self.check(case_04a)

    def test_case_04b(self):
        self.check(case_04b)

    def test_case_04c(self):
        self.check(case_04c)

    def test_case_05a(self):
        self.check(case_05a)

    def test_case_06a(self):
        # this is a tricky test where the region_constraint discards an asset
        # so the risk sites are different from the hazard sites
        self.check(case_06a)

    def test_case_06b(self):
        self.check(case_06b)

    def test_case_07a(self):
        self.check(case_07a)

    def test_case_07b(self):
        self.check(case_07b)

    def test_case_07c(self):
        self.check(case_07c)

    def test_case_master(self):
        if NOT_DARWIN:  # skip on macOS
            self.check(case_master)
            fnames = export(('hcurves', 'xml'), self.calc.datastore)
            for fname in fnames:
                self.assertEqualFiles(
                    'expected/%s' % strip_calc_id(fname), fname)
