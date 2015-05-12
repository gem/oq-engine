from nose.plugins.attrib import attr
from openquake.commonlib.tests.calculators import CalculatorTestCase
from openquake.qa_tests_data.classical import (
    case_1, case_2, case_3, case_4, case_5, case_6, case_7, case_8, case_9,
    case_10, case_11, case_12, case_13, case_14, case_15, case_16, case_17,
    case_19)


class ClassicalTestCase(CalculatorTestCase):

    def assert_curves_ok(self, expected, test_dir, delta=None):
        out = self.run_calc(test_dir, 'job.ini', exports='csv')
        got = (out['/hcurves', 'csv'] +
               out.get(('/hmaps', 'csv'), []) +
               out.get(('/uhs', 'csv'), []))
        self.assertEqual(len(expected), len(got))
        for fname, actual in zip(expected, got):
            self.assertEqualFiles('expected/%s' % fname, actual, delta=delta)

    @attr('qa', 'hazard', 'classical')
    def test_case_1(self):
        self.assert_curves_ok(
            ['hazard_curve-smltp_b1-gsimltp_b1.csv'],
            case_1.__file__)

    @attr('qa', 'hazard', 'classical')
    def test_case_2(self):
        self.assert_curves_ok(
            ['hazard_curve-smltp_b1-gsimltp_b1.csv'],
            case_2.__file__)

    @attr('qa', 'hazard', 'classical')
    def test_case_3(self):
        self.assert_curves_ok(
            ['hazard_curve-smltp_b1-gsimltp_b1.csv'],
            case_3.__file__)

    @attr('qa', 'hazard', 'classical', 'slow')
    def test_case_4(self):
        self.assert_curves_ok(
            ['hazard_curve-smltp_b1-gsimltp_b1.csv'],
            case_4.__file__)

    @attr('qa', 'hazard', 'classical', 'slow')
    def test_case_5(self):
        self.assert_curves_ok(
            ['hazard_curve-smltp_b1-gsimltp_b1.csv'],
            case_5.__file__)

    @attr('qa', 'hazard', 'classical', 'slow')
    def test_case_6(self):
        self.assert_curves_ok(
            ['hazard_curve-smltp_b1-gsimltp_b1.csv'],
            case_6.__file__)

    @attr('qa', 'hazard', 'classical', 'slow')
    def test_case_7(self):
        self.assert_curves_ok(
            ['hazard_curve-mean.csv',
             'hazard_curve-smltp_b1-gsimltp_b1.csv',
             'hazard_curve-smltp_b2-gsimltp_b1.csv'],
            case_7.__file__)

    @attr('qa', 'hazard', 'classical')
    def test_case_8(self):
        self.assert_curves_ok(
            ['hazard_curve-smltp_b1_b2-gsimltp_b1.csv',
             'hazard_curve-smltp_b1_b3-gsimltp_b1.csv',
             'hazard_curve-smltp_b1_b4-gsimltp_b1.csv'],
            case_8.__file__)

    @attr('qa', 'hazard', 'classical')
    def test_case_9(self):
        self.assert_curves_ok(
            ['hazard_curve-smltp_b1_b2-gsimltp_b1.csv',
             'hazard_curve-smltp_b1_b3-gsimltp_b1.csv'],
            case_9.__file__)

    @attr('qa', 'hazard', 'classical')
    def test_case_10(self):
        self.assert_curves_ok(
            ['hazard_curve-smltp_b1_b2-gsimltp_b1.csv',
             'hazard_curve-smltp_b1_b3-gsimltp_b1.csv'],
            case_10.__file__)

    @attr('qa', 'hazard', 'classical')
    def test_case_11(self):
        self.assert_curves_ok(
            ['hazard_curve-mean.csv',
             'hazard_curve-smltp_b1_b2-gsimltp_b1.csv',
             'hazard_curve-smltp_b1_b3-gsimltp_b1.csv',
             'hazard_curve-smltp_b1_b4-gsimltp_b1.csv',
             'quantile_curve-0.1.csv',
             'quantile_curve-0.9.csv'],
            case_11.__file__)

    @attr('qa', 'hazard', 'classical')
    def test_case_12(self):
        self.assert_curves_ok(
            ['hazard_curve-smltp_b1-gsimltp_b1_b2.csv'],
            case_12.__file__)

    @attr('qa', 'hazard', 'classical')
    def test_case_13(self):
        self.assert_curves_ok(
            ['hazard_curve-mean.csv',
             'hazard_map-mean.csv'],
            case_13.__file__)

    @attr('qa', 'hazard', 'classical')
    def test_case_14(self):
        self.assert_curves_ok([
            'hazard_curve-smltp_simple_fault-gsimltp_AbrahamsonSilva2008.csv',
            'hazard_curve-smltp_simple_fault-gsimltp_CampbellBozorgnia2008.csv'
        ], case_14.__file__)

    @attr('qa', 'hazard', 'classical')
    def test_case_15(self):  # full enumeration
        self.assert_curves_ok('''\
hazard_curve-mean.csv
hazard_curve-smltp_SM1-gsimltp_BA2008_C2003.csv
hazard_curve-smltp_SM1-gsimltp_BA2008_T2002.csv
hazard_curve-smltp_SM1-gsimltp_CB2008_C2003.csv
hazard_curve-smltp_SM1-gsimltp_CB2008_T2002.csv
hazard_curve-smltp_SM2_a3b1-gsimltp_BA2008_*.csv
hazard_curve-smltp_SM2_a3b1-gsimltp_CB2008_*.csv
hazard_curve-smltp_SM2_a3pt2b0pt8-gsimltp_BA2008_*.csv
hazard_curve-smltp_SM2_a3pt2b0pt8-gsimltp_CB2008_*.csv
hazard_map-mean.csv
hazard_map-smltp_SM1-gsimltp_BA2008_C2003.csv
hazard_map-smltp_SM1-gsimltp_BA2008_T2002.csv
hazard_map-smltp_SM1-gsimltp_CB2008_C2003.csv
hazard_map-smltp_SM1-gsimltp_CB2008_T2002.csv
hazard_map-smltp_SM2_a3b1-gsimltp_BA2008_*.csv
hazard_map-smltp_SM2_a3b1-gsimltp_CB2008_*.csv
hazard_map-smltp_SM2_a3pt2b0pt8-gsimltp_BA2008_*.csv
hazard_map-smltp_SM2_a3pt2b0pt8-gsimltp_CB2008_*.csv
hazard_uhs-mean.csv
hazard_uhs-smltp_SM1-gsimltp_BA2008_C2003.csv
hazard_uhs-smltp_SM1-gsimltp_BA2008_T2002.csv
hazard_uhs-smltp_SM1-gsimltp_CB2008_C2003.csv
hazard_uhs-smltp_SM1-gsimltp_CB2008_T2002.csv
hazard_uhs-smltp_SM2_a3b1-gsimltp_BA2008_*.csv
hazard_uhs-smltp_SM2_a3b1-gsimltp_CB2008_*.csv
hazard_uhs-smltp_SM2_a3pt2b0pt8-gsimltp_BA2008_*.csv
hazard_uhs-smltp_SM2_a3pt2b0pt8-gsimltp_CB2008_*.csv'''.split(),
                              case_15.__file__)

    @attr('qa', 'hazard', 'classical')
    def test_case_16(self):   # sampling
        self.assert_curves_ok(
            ['hazard_curve-mean.csv',
             'quantile_curve-0.1.csv',
             'quantile_curve-0.9.csv'],
            case_16.__file__)

    @attr('qa', 'hazard', 'classical')
    def test_case_17(self):  # oversampling
        self.assert_curves_ok(
            ['hazard_curve-smltp_b1-gsimltp_b1-ltr_0.csv',
             'hazard_curve-smltp_b2-gsimltp_b1-ltr_1.csv',
             'hazard_curve-smltp_b2-gsimltp_b1-ltr_2.csv',
             'hazard_curve-smltp_b2-gsimltp_b1-ltr_3.csv',
             'hazard_curve-smltp_b2-gsimltp_b1-ltr_4.csv'],
            case_17.__file__)

    @attr('qa', 'hazard', 'classical')
    def test_case_19(self):
        self.assert_curves_ok([
            'hazard_curve-mean.csv',
            'hazard_curve-smltp_b1-gsimltp_*_*_*_*_b51_*_*.csv',
            'hazard_curve-smltp_b1-gsimltp_*_*_*_*_b52_*_*.csv',
            'hazard_curve-smltp_b1-gsimltp_*_*_*_*_b53_*_*.csv',
            'hazard_curve-smltp_b1-gsimltp_*_*_*_*_b54_*_*.csv',
        ], case_19.__file__, delta=1E-7)
