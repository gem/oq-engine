import unittest
from nose.plugins.attrib import attr

from openquake.qa_tests_data.classical_risk import (
    case_1, case_2, case_3)
from openquake.commonlib.tests.calculators import CalculatorTestCase


class ClassicalRiskTestCase(CalculatorTestCase):

    @attr('qa', 'risk', 'classical_risk')
    def test_case_1(self):
        raise unittest.SkipTest

    @attr('qa', 'risk', 'classical_risk')
    def test_case_2(self):
        raise unittest.SkipTest

    @attr('qa', 'risk', 'classical_risk')
    def test_case_3(self):
        out = self.run_calc(case_3.__file__, 'job_haz.ini,job_risk.ini',
                            exports='csv')
        self.assertEqualFiles(
            'expected/rlz-000-avg_loss.csv', out['rlz-000-avg_loss'])
