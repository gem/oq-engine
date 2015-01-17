import unittest
from nose.plugins.attrib import attr
from openquake.commonlib.tests.calculators import CalculatorTestCase
from openquake.qa_tests_data.event_based import case_1


class ClassicalTestCase(CalculatorTestCase):

    @attr('qa', 'hazard', 'classical')
    def test_case_1(self):
        out = self.run_calc(case_1.__file__, 'job.ini', exports='csv')
        raise unittest.SkipTest  # temporarily skipped
        self.assertEqualFiles(
            'expected/0-SadighEtAl1997.csv', out[0, 'SadighEtAl1997'])

        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1-ltr_0.csv',
            out['hazard_curve-smltp_b1-gsimltp_b1-ltr_0.csv'])
