from nose.plugins.attrib import attr
from openquake.calculators.tests import CalculatorTestCase
from openquake.qa_tests_data.disagg import case_1, case_2


class DisaggregationTestCase(CalculatorTestCase):

    def assert_curves_ok(self, expected, test_dir, delta=None):
        out = self.run_calc(test_dir, 'job.ini', exports='xml')
        got = out['disagg', 'xml']
        self.assertEqual(len(expected), len(got))
        for fname, actual in zip(expected, got):
            self.assertEqualFiles(
                'expected_output/disagg_matrix/%s' % fname, actual)

    @attr('qa', 'hazard', 'classical')
    def test_case_1(self):
        self.assert_curves_ok([
            'PGA/disagg_matrix(0.02)-lon_10.1-lat_40.1-smltp_b1-gsimltp_b1.xml',
            'SA-0.025/disagg_matrix(0.02)-lon_10.1-lat_40.1-smltp_b1-gsimltp_b1.xml',
            'PGA/disagg_matrix(0.1)-lon_10.1-lat_40.1-smltp_b1-gsimltp_b1.xml',
            'SA-0.025/disagg_matrix(0.1)-lon_10.1-lat_40.1-smltp_b1-gsimltp_b1.xml'
            ], case_1.__file__)

    @attr('qa', 'hazard', 'classical')
    def test_case_2(self):
        pass
