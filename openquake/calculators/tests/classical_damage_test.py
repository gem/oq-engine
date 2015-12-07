from nose.plugins.attrib import attr

from openquake.qa_tests_data.classical_damage import (
    case_1, case_2, case_1a, case_1b, case_1c)
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
