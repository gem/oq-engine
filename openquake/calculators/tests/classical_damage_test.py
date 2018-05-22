# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2018 GEM Foundation
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

from nose.plugins.attrib import attr

from openquake.qa_tests_data.classical_damage import (
    case_1, case_2, case_1a, case_1b, case_1c, case_2a, case_2b, case_3a,
    case_4a, case_4b, case_4c, case_5a, case_6a, case_6b, case_7a, case_7b,
    case_7c, case_8a, case_master)
from openquake.calculators.export import export
from openquake.calculators.tests import (
    CalculatorTestCase, strip_calc_id, NOT_DARWIN)

import numpy

aae = numpy.testing.assert_almost_equal


class ClassicalDamageCase1TestCase(CalculatorTestCase):

    @attr('qa', 'risk', 'classical_damage')
    def test_continuous(self):
        self.run_calc(case_1.__file__, 'job_continuous.ini')
        [fname] = export(('damages-rlzs', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/damage_continuous.csv', fname)

    @attr('qa', 'risk', 'classical_damage')
    def test_discrete(self):
        self.run_calc(case_1.__file__, 'job_discrete.ini')
        [fname] = export(('damages-rlzs', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/damage_discrete.csv', fname)

    @attr('qa', 'risk', 'classical_damage')
    def test_interpolation(self):
        self.run_calc(case_1.__file__, 'job_interpolation.ini')
        [fname] = export(('damages-rlzs', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/damage_interpolation.csv', fname)


# tests with no damage limit
class ClassicalDamageCase2TestCase(CalculatorTestCase):

    @attr('qa', 'risk', 'classical_damage')
    def test_continuous(self):
        self.run_calc(case_2.__file__, 'job_continuous.ini')
        [fname] = export(('damages-rlzs', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/damage_continuous.csv', fname)

    @attr('qa', 'risk', 'classical_damage')
    def test_discrete(self):
        self.run_calc(case_2.__file__, 'job_discrete.ini')
        [fname] = export(('damages-rlzs', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/damage_discrete.csv', fname)

    @attr('qa', 'risk', 'classical_damage')
    def test_interpolation(self):
        self.run_calc(case_2.__file__, 'job_interpolation.ini')
        [fname] = export(('damages-rlzs', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/damage_interpolation.csv', fname)


class ClassicalDamageCase8TestCase(CalculatorTestCase):
    @attr('qa', 'risk', 'classical_damage')
    def test_case_8a(self):
        self.run_calc(
            case_8a.__file__, 'job_haz.ini,job_risk.ini')
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

    @attr('qa', 'risk', 'classical_damage')
    def test_case_1a(self):
        self.check(case_1a)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_1b(self):
        self.check(case_1b)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_1c(self):
        self.check(case_1c)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_2a(self):
        self.check(case_2a)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_2b(self):
        self.check(case_2b)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_3a(self):
        self.check(case_3a)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_4a(self):
        self.check(case_4a)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_4b(self):
        self.check(case_4b)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_4c(self):
        self.check(case_4c)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_5a(self):
        self.check(case_5a)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_6a(self):
        # this is a tricky test where the region_constraint discards an asset
        # so the risk sites are different from the hazard sites
        self.check(case_6a)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_6b(self):
        self.check(case_6b)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_7a(self):
        self.check(case_7a)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_7b(self):
        self.check(case_7b)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_7c(self):
        self.check(case_7c)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_master(self):
        if NOT_DARWIN:  # skip on macOS
            self.check(case_master)
