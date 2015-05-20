import unittest
from nose.plugins.attrib import attr

from openquake.qa_tests_data.classical_risk import (
    case_1, case_2, case_3, case_4)
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
        [fname] = out['/avg_losses', 'csv']
        self.assertEqualFiles('expected/rlz-000-avg_loss.csv', fname)

    @attr('qa', 'risk', 'classical_risk')
    def test_case_4(self):
        out = self.run_calc(case_4.__file__, 'job_haz.ini,job_risk.ini',
                            exports='csv')
        fnames = out['/avg_losses', 'csv']
        self.assertEqualFiles('expected/rlz-000-avg_loss.csv', fnames[0])
        self.assertEqualFiles('expected/rlz-001-avg_loss.csv', fnames[1])
