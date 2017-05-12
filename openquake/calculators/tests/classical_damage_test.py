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
from openquake.commonlib.oqvalidation import OqParam
from openquake.calculators.export import export
from openquake.calculators.tests import CalculatorTestCase
from openquake.calculators.classical_damage import ClassicalDamageCalculator

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
            case.__file__, 'job_haz.ini,job_risk.ini', exports='csv')
        [fname] = out['damages-rlzs', 'csv']
        self.assertEqualFiles('expected/damages.csv', fname)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_1a(self):
        self.run_calc(case_1a.__file__, 'job_haz.ini,job_risk.ini')
        damages = tuple(self.calc.datastore['damages-rlzs'][0, 0])
        aae(damages, [0.971702, 0.00488098, 0.0067176, 0.005205, 0.0114946], 6)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_1b(self):
        self.run_calc(case_1b.__file__, 'job_haz.ini,job_risk.ini')
        damages = tuple(self.calc.datastore['damages-rlzs'][0, 0])
        aae(damages, [0.98269, 0.001039, 0.0028866, 0.0032857, 0.01009], 5)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_1c(self):
        self.run_calc(case_1c.__file__, 'job_haz.ini,job_risk.ini')
        damages = tuple(self.calc.datastore['damages-rlzs'][0, 0])
        expected = [0.971993, 0.0047832, 0.006618, 0.0051539, 0.0114523]
        aae(damages, expected, 5)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_2a(self):
        self.run_calc(case_2a.__file__, 'job_haz.ini,job_risk.ini')
        damages = tuple(self.calc.datastore['damages-rlzs'][0, 0])
        aae(damages, (0.97072, 0.004527, 0.008484, 0.0052885, 0.010976), 5)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_2b(self):
        self.run_calc(case_2b.__file__, 'job_haz.ini,job_risk.ini')
        damages = tuple(self.calc.datastore['damages-rlzs'][0, 0])
        aae(damages, [0.970740, 0.004517, 0.00847858, 0.0052878, 0.0109759], 5)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_3a(self):
        self.run_calc(case_3a.__file__, 'job_haz.ini,job_risk.ini')
        damages = tuple(self.calc.datastore['damages-rlzs'][0, 0])
        aae(damages, [0.972491, 0.008021, 0.010599, 0.0057342, 0.0031543], 5)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_4a(self):
        self.run_calc(case_4a.__file__, 'job_haz.ini,job_risk.ini')
        damages = tuple(self.calc.datastore['damages-rlzs'][0, 0])
        aae(damages, [0.970851, 0.0044304, 0.00841, 0.00529, 0.01102], 5)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_4b(self):
        self.run_calc(case_4b.__file__, 'job_haz.ini,job_risk.ini')
        damages = tuple(self.calc.datastore['damages-rlzs'][0, 0])
        aae(damages, [0.108756, 0.044266, 0.138326, 0.14414, 0.564511], 5)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_4c(self):
        self.run_calc(case_4c.__file__, 'job_haz.ini,job_risk.ini')
        damages = tuple(self.calc.datastore['damages-rlzs'][0, 0])
        aae(damages, [0.108756, 0.044266, 0.138326, 0.14414, 0.564511], 5)

    @attr('qa', 'risk', 'classical_damage')
    def test_case_5a(self):
        self.run_calc(case_5a.__file__, 'job_haz.ini,job_risk.ini')
        damages = tuple(self.calc.datastore['damages-rlzs'][0, 0])
        aae(damages, [4.85426, 0.02215, 0.042048, 0.02643, 0.055113], 5)

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

    @attr('qa', 'risk', 'classical_damage')
    def test_poe_1(self):
        oq = object.__new__(OqParam)
        oq.hazard_imtls = {'PGA': [0.00001, 0.0001, 0.001, 0.002, 0.01, 0.05]}
        curves_by_trt_gsim = {
            (0, 0): {'PGA': numpy.array([1, 0.99, 0.95, 0.9, 0.6, 0.1])}}
        with self.assertRaises(ValueError):
            ClassicalDamageCalculator(oq).check_poes(curves_by_trt_gsim)
