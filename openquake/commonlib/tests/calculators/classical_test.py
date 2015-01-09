from nose.plugins.attrib import attr
from openquake.commonlib.tests.calculators import CalculatorTestCase
from openquake.qa_tests_data.classical import case_17


class ClassicalTestCase(CalculatorTestCase):

    @attr('qa', 'hazard', 'classical')
    def test_case_17(self):
        out = self.run_calc(case_17.__file__, 'job.ini', exports='csv')
        self.assertEqualFiles(
            'expected_curve_0.csv',
            out['hazard_curve-smltp_b1-gsimltp_b1-ltr_0.csv'])
        self.assertEqualFiles(
            'expected_curve_1.csv',
            out['hazard_curve-smltp_b1-gsimltp_b1-ltr_1.csv'])
