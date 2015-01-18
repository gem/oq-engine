from nose.plugins.attrib import attr
from openquake.commonlib.tests.calculators import CalculatorTestCase
from openquake.qa_tests_data.classical import case_17


class ClassicalTestCase(CalculatorTestCase):
    expected = [
        'hazard_curve-smltp_b2-gsimltp_b1-ltr_0.csv',
        'hazard_curve-smltp_b2-gsimltp_b1-ltr_1.csv',
        'hazard_curve-smltp_b1-gsimltp_b1-ltr_2.csv',
        'hazard_curve-smltp_b2-gsimltp_b1-ltr_3.csv',
        'hazard_curve-smltp_b2-gsimltp_b1-ltr_4.csv',
        'hazard_curve-mean.csv',
    ]

    @attr('qa', 'hazard', 'classical')
    def test_case_17(self):
        out = self.run_calc(case_17.__file__, 'job.ini', exports='csv')
        for fname in self.expected:
            self.assertEqualFiles('expected/%s' % fname, out[fname])
