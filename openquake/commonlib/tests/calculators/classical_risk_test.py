from nose.plugins.attrib import attr

from openquake.qa_tests_data.classical_risk import (
    case_1, case_2, case_3)
from openquake.commonlib.tests.calculators import CalculatorTestCase


class ClassicalRiskTestCase(CalculatorTestCase):

    @attr('qa', 'risk', 'classical_risk')
    def _test_case_1(self):
        out = self.run_calc(case_1.__file__, 'job_haz.ini,job_risk.ini')
        self.assertEqualFiles(
            'expected/damage_discrete.csv', out['classical_damage', 'csv'])

    @attr('qa', 'risk', 'classical_risk')
    def _test_case_2(self):
        out = self.run_calc(case_2.__file__, 'job_haz.ini,job_risk.ini')
        self.assertEqualFiles(
            'expected/damage_discrete.csv', out['classical_damage', 'csv'])

    @attr('qa', 'risk', 'classical_risk')
    def _test_case_3(self):
        out = self.run_calc(case_3.__file__, 'job_haz.ini,job_risk.ini')
        self.assertEqualFiles(
            'expected/damage_discrete.csv', out['classical_damage', 'csv'])
