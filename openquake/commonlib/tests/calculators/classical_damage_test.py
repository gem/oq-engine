from nose.plugins.attrib import attr

from openquake.qa_tests_data.classical_damage import (
    case_1, case_2)
from openquake.commonlib.tests.calculators import CalculatorTestCase


class ClassicalDamageCase1TestCase(CalculatorTestCase):

    @attr('qa', 'risk', 'classical_damage')
    def test_continuous(self):
        out = self.run_calc(case_1.__file__, 'job_continuous.ini')
        [fname] = out['damages_by_rlz', 'csv']
        self.assertEqualFiles('expected/damage_continuous.csv', fname)

    @attr('qa', 'risk', 'classical_damage')
    def test_discrete(self):
        out = self.run_calc(case_1.__file__, 'job_discrete.ini')
        [fname] = out['damages_by_rlz', 'csv']
        self.assertEqualFiles('expected/damage_discrete.csv', fname)

    @attr('qa', 'risk', 'classical_damage')
    def test_interpolation(self):
        out = self.run_calc(case_1.__file__, 'job_interpolation.ini')
        [fname] = out['damages_by_rlz', 'csv']
        self.assertEqualFiles('expected/damage_interpolation.csv', fname)


# tests with no damage limit
class ClassicalDamageCase2TestCase(CalculatorTestCase):

    @attr('qa', 'risk', 'classical_damage')
    def test_continuous(self):
        out = self.run_calc(case_2.__file__, 'job_continuous.ini')
        [fname] = out['damages_by_rlz', 'csv']
        self.assertEqualFiles('expected/damage_continuous.csv', fname)

    @attr('qa', 'risk', 'classical_damage')
    def test_discrete(self):
        out = self.run_calc(case_2.__file__, 'job_discrete.ini')
        [fname] = out['damages_by_rlz', 'csv']
        self.assertEqualFiles('expected/damage_discrete.csv', fname)

    @attr('qa', 'risk', 'classical_damage')
    def test_interpolation(self):
        out = self.run_calc(case_2.__file__, 'job_interpolation.ini')
        [fname] = out['damages_by_rlz', 'csv']
        self.assertEqualFiles('expected/damage_interpolation.csv', fname)
