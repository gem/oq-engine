from nose.plugins.attrib import attr
from openquake.calculators.tests import CalculatorTestCase
from openquake.qa_tests_data.classical_tiling import case_1


class ClassicalTestCase(CalculatorTestCase):
    @attr('qa', 'hazard', 'classical_tiling')
    def test_case_1(self):
        out = self.run_calc(case_1.__file__, 'job.ini', exports='csv')
        expected = [
            'hazard_curve-mean.csv',
            'hazard_curve-smltp_b1-gsimltp_b1.csv',
            'hazard_curve-smltp_b1-gsimltp_b2.csv',
            'quantile_curve-0.1.csv',
            'hazard_map-mean.csv',
            'hazard_map-smltp_b1-gsimltp_b1.csv',
            'hazard_map-smltp_b1-gsimltp_b2.csv',
            'quantile_map-0.1.csv',
            'hazard_uhs-mean.csv',
            'hazard_uhs-smltp_b1-gsimltp_b1.csv',
            'hazard_uhs-smltp_b1-gsimltp_b2.csv',
            'quantile_uhs-0.1.csv',
        ]
        got = (out['hcurves', 'csv'] +
               out.get(('hmaps', 'csv'), []) +
               out.get(('uhs', 'csv'), []))
        self.assertEqual(len(expected), len(got))
        for fname, actual in zip(expected, got):
            self.assertEqualFiles('expected/%s' % fname, actual, delta=1E-6)
