# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2017 GEM Foundation
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
    case_7c, case_8a)
from openquake.calculators.export import export
from openquake.calculators.tests import CalculatorTestCase

import numpy

aae = numpy.testing.assert_almost_equal


class ClassicalDamageCase1TestCase(CalculatorTestCase):

    @attr('qa', 'risk', 'classical_damage')
    def test_continuous(self):
        out = self.run_calc(case_1.__file__, 'job_continuous.ini',
                            exports='csv')
        [fname] = out['damages-rlzs', 'csv']
        self.assertEqualFiles('expected/damage_continuous.csv', fname)

    @attr('qa', 'risk', 'classical_damage')
    def test_discrete(self):
        out = self.run_calc(case_1.__file__, 'job_discrete.ini',
                            exports='csv')
        [fname] = out['damages-rlzs', 'csv']
        self.assertEqualFiles('expected/damage_discrete.csv', fname)

    @attr('qa', 'risk', 'classical_damage')
    def test_interpolation(self):
        out = self.run_calc(case_1.__file__, 'job_interpolation.ini',
                            exports='csv')
        [fname] = out['damages-rlzs', 'csv']
        self.assertEqualFiles('expected/damage_interpolation.csv', fname)


# tests with no damage limit
class ClassicalDamageCase2TestCase(CalculatorTestCase):

    @attr('qa', 'risk', 'classical_damage')
    def test_continuous(self):
        out = self.run_calc(case_2.__file__, 'job_continuous.ini',
                            exports='csv')
        [fname] = out['damages-rlzs', 'csv']
        self.assertEqualFiles('expected/damage_continuous.csv', fname)

    @attr('qa', 'risk', 'classical_damage')
    def test_discrete(self):
        out = self.run_calc(case_2.__file__, 'job_discrete.ini',
                            exports='csv')
        [fname] = out['damages-rlzs', 'csv']
        self.assertEqualFiles('expected/damage_discrete.csv', fname)

    @attr('qa', 'risk', 'classical_damage')
    def test_interpolation(self):
        out = self.run_calc(case_2.__file__, 'job_interpolation.ini',
                            exports='csv')
        [fname] = out['damages-rlzs', 'csv']
        self.assertEqualFiles('expected/damage_interpolation.csv', fname)


class ClassicalDamageTestCase(CalculatorTestCase):

    def check(self, case):
        out = self.run_calc(
            case.__file__, 'job_haz.ini,job_risk.ini', exports='csv',
            concurrent_tasks='0')  # avoid the usual fork issue
        [fname] = out['damages-rlzs', 'csv']
        self.assertEqualFiles('expected/damages.csv', fname)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_1a(self):
        self.run_calc(case_1a.__file__, 'job_haz.ini,job_risk.ini')
        damages = tuple(self.calc.datastore['damages-rlzs'][0, 0])
        aae(damages, [0.97179, 0.00488, 0.006703, 0.005186, 0.011442], 6)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_1b(self):
        self.run_calc(case_1b.__file__, 'job_haz.ini,job_risk.ini')
        damages = tuple(self.calc.datastore['damages-rlzs'][0, 0])
        aae(damages, [0.982802, 0.001031, 0.002865, 0.003263, 0.010039], 6)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_1c(self):
        self.run_calc(case_1c.__file__, 'job_haz.ini,job_risk.ini')
        damages = tuple(self.calc.datastore['damages-rlzs'][0, 0])
        expected = [0.97211, 0.00477, 0.00659, 0.00513, 0.0114]
        aae(damages, expected, 5)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_2a(self):
        self.run_calc(case_2a.__file__, 'job_haz.ini,job_risk.ini')
        damages = tuple(self.calc.datastore['damages-rlzs'][0, 0])
        aae(damages, (0.97087, 0.00451, 0.00844, 0.00526, 0.01092), 5)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_2b(self):
        self.run_calc(case_2b.__file__, 'job_haz.ini,job_risk.ini')
        damages = tuple(self.calc.datastore['damages-rlzs'][0, 0])
        aae(damages, [0.97089, 0.0045, 0.00843, 0.00525, 0.01092], 5)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_3a(self):
        self.run_calc(case_3a.__file__, 'job_haz.ini,job_risk.ini')
        damages = tuple(self.calc.datastore['damages-rlzs'][0, 0])
        aae(damages, [0.97263, 0.00799, 0.01054, 0.0057, 0.00314], 5)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_4a(self):
        self.run_calc(case_4a.__file__, 'job_haz.ini,job_risk.ini')
        damages = tuple(self.calc.datastore['damages-rlzs'][0, 0])
        aae(damages, [0.971, 0.00442, 0.00837, 0.00525, 0.01096], 5)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_4b(self):
        self.run_calc(case_4b.__file__, 'job_haz.ini,job_risk.ini')
        damages = tuple(self.calc.datastore['damages-rlzs'][0, 0])
        aae(damages, [0.10998, 0.04461, 0.13879, 0.14406, 0.56256], 5)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_4c(self):
        self.run_calc(case_4c.__file__, 'job_haz.ini,job_risk.ini')
        damages = tuple(self.calc.datastore['damages-rlzs'][0, 0])
        aae(damages, [0.10998, 0.04461, 0.13879, 0.14406, 0.56256], 5)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_5a(self):
        self.run_calc(case_5a.__file__, 'job_haz.ini,job_risk.ini')
        damages = tuple(self.calc.datastore['damages-rlzs'][0, 0])
        aae(damages, [4.85498, 0.02209, 0.04184, 0.02627, 0.05482], 5)

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
    def test_case_8a(self):
        self.run_calc(
            case_8a.__file__, 'job_haz.ini,job_risk.ini', exports='csv')
        f1, f2 = export(('damages-rlzs', 'csv'), self.calc.datastore)
        self.assertEqualFiles(
            'expected/damages-rlzs-AkkarBommer2010().csv', f2)
        self.assertEqualFiles(
            'expected/damages-rlzs-SadighEtAl1997().csv', f1)
        [f] = export(('damages-stats', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/damages-stats.csv', f)
