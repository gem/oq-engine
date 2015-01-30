from nose.plugins.attrib import attr
from openquake.commonlib.tests.calculators import CalculatorTestCase
from openquake.qa_tests_data.classical import (
    case_1, case_2, case_3, case_4, case_5, case_6, case_7, case_8, case_9,
    case_10, case_11, case_12, case_13, case_14, case_15, case_16, case_17)


class ClassicalTestCase(CalculatorTestCase):
    @attr('qa', 'hazard', 'classical')
    def test_case_1(self):
        out = self.run_calc(case_1.__file__, 'job.ini', exports='csv')
        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1-ltr_0.csv',
            out['hazard_curve-smltp_b1-gsimltp_b1-ltr_0.csv'])

    @attr('qa', 'hazard', 'classical')
    def test_case_2(self):
        out = self.run_calc(case_2.__file__, 'job.ini', exports='csv')
        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1-ltr_0.csv',
            out['hazard_curve-smltp_b1-gsimltp_b1-ltr_0.csv'])

    @attr('qa', 'hazard', 'classical')
    def test_case_3(self):
        out = self.run_calc(case_3.__file__, 'job.ini', exports='csv')
        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1-ltr_0.csv',
            out['hazard_curve-smltp_b1-gsimltp_b1-ltr_0.csv'])

    @attr('qa', 'hazard', 'classical', 'slow')
    def test_case_4(self):
        out = self.run_calc(case_4.__file__, 'job.ini', exports='csv')
        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1-ltr_0.csv',
            out['hazard_curve-smltp_b1-gsimltp_b1-ltr_0.csv'])

    @attr('qa', 'hazard', 'classical', 'slow')
    def test_case_5(self):
        out = self.run_calc(case_5.__file__, 'job.ini', exports='csv')
        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1-ltr_0.csv',
            out['hazard_curve-smltp_b1-gsimltp_b1-ltr_0.csv'])

    @attr('qa', 'hazard', 'classical', 'slow')
    def test_case_6(self):
        out = self.run_calc(case_6.__file__, 'job.ini', exports='csv')
        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1-ltr_0.csv',
            out['hazard_curve-smltp_b1-gsimltp_b1-ltr_0.csv'])

    @attr('qa', 'hazard', 'classical', 'slow')
    def test_case_7(self):
        expected = [
            'hazard_curve-smltp_b1-gsimltp_b1-ltr_0.csv',
            'hazard_curve-smltp_b2-gsimltp_b1-ltr_1.csv',
            'hazard_curve-mean.csv',
        ]
        out = self.run_calc(case_7.__file__, 'job.ini', exports='csv')
        for fname in expected:
            self.assertEqualFiles('expected/%s' % fname, out[fname])

    @attr('qa', 'hazard', 'classical')
    def test_case_8(self):
        expected = [
            'hazard_curve-smltp_b1_b2-gsimltp_b1-ltr_0.csv',
            'hazard_curve-smltp_b1_b3-gsimltp_b1-ltr_1.csv',
            'hazard_curve-smltp_b1_b4-gsimltp_b1-ltr_2.csv',
        ]
        out = self.run_calc(case_8.__file__, 'job.ini', exports='csv')
        for fname in expected:
            self.assertEqualFiles('expected/%s' % fname, out[fname])

    @attr('qa', 'hazard', 'classical')
    def test_case_9(self):
        expected = [
            'hazard_curve-smltp_b1_b2-gsimltp_b1-ltr_0.csv',
            'hazard_curve-smltp_b1_b3-gsimltp_b1-ltr_1.csv',
        ]
        out = self.run_calc(case_9.__file__, 'job.ini', exports='csv')
        for fname in expected:
            self.assertEqualFiles('expected/%s' % fname, out[fname])

    @attr('qa', 'hazard', 'classical')
    def test_case_10(self):
        expected = [
            'hazard_curve-smltp_b1_b2-gsimltp_b1-ltr_0.csv',
            'hazard_curve-smltp_b1_b3-gsimltp_b1-ltr_1.csv',
        ]
        out = self.run_calc(case_10.__file__, 'job.ini', exports='csv')
        for fname in expected:
            self.assertEqualFiles('expected/%s' % fname, out[fname])

    @attr('qa', 'hazard', 'classical')
    def test_case_11(self):
        expected = [
            'hazard_curve-smltp_b1_b2-gsimltp_b1-ltr_0.csv',
            'hazard_curve-smltp_b1_b3-gsimltp_b1-ltr_1.csv',
            'hazard_curve-smltp_b1_b4-gsimltp_b1-ltr_2.csv',
            'hazard_curve-mean.csv',
        ]
        out = self.run_calc(case_11.__file__, 'job.ini', exports='csv')
        for fname in expected:
            self.assertEqualFiles('expected/%s' % fname, out[fname])

    @attr('qa', 'hazard', 'classical')
    def test_case_12(self):
        expected = [
            'hazard_curve-smltp_b1-gsimltp_b1_b2-ltr_0.csv',
        ]
        out = self.run_calc(case_12.__file__, 'job.ini', exports='csv')
        for fname in expected:
            self.assertEqualFiles('expected/%s' % fname, out[fname])

    @attr('qa', 'hazard', 'classical')
    def test_case_13(self):
        expected = [
            'hazard_curve-smltp_aFault_aPriori_D2.1-gsimltp_BooreAtkinson2008-ltr_0.csv',
            'hazard_curve-smltp_aFault_aPriori_D2.1-gsimltp_ChiouYoungs2008-ltr_1.csv',
            'hazard_curve-smltp_bFault_stitched_D2.1_Char-gsimltp_BooreAtkinson2008-ltr_2.csv',
            'hazard_curve-smltp_bFault_stitched_D2.1_Char-gsimltp_ChiouYoungs2008-ltr_3.csv',
            'hazard_curve-mean.csv',
            'hazard_map-smltp_aFault_aPriori_D2.1-gsimltp_BooreAtkinson2008-ltr_0.csv',
            'hazard_map-smltp_aFault_aPriori_D2.1-gsimltp_ChiouYoungs2008-ltr_1.csv',
            'hazard_map-smltp_bFault_stitched_D2.1_Char-gsimltp_BooreAtkinson2008-ltr_2.csv',
            'hazard_map-smltp_bFault_stitched_D2.1_Char-gsimltp_ChiouYoungs2008-ltr_3.csv',
            'hazard_map-mean.csv',
        ]
        out = self.run_calc(case_13.__file__, 'job.ini', exports='csv')
        for fname in expected:
            self.assertEqualFiles('expected/%s' % fname, out[fname])

    @attr('qa', 'hazard', 'classical')
    def test_case_14(self):
        expected = [
            'hazard_curve-smltp_simple_fault-gsimltp_AbrahamsonSilva2008-ltr_0.csv',
            'hazard_curve-smltp_simple_fault-gsimltp_CampbellBozorgnia2008-ltr_1.csv',
        ]
        out = self.run_calc(case_14.__file__, 'job.ini', exports='csv')
        for fname in expected:
            self.assertEqualFiles('expected/%s' % fname, out[fname])

    @attr('qa', 'hazard', 'classical')
    def test_case_15(self):
        expected = [
            'hazard_curve-smltp_SM1-gsimltp_BA2008_C2003-ltr_0.csv',
            'hazard_curve-smltp_SM1-gsimltp_BA2008_T2002-ltr_1.csv',
            'hazard_curve-smltp_SM1-gsimltp_CB2008_C2003-ltr_2.csv',
            'hazard_curve-smltp_SM1-gsimltp_CB2008_T2002-ltr_3.csv',
            'hazard_curve-smltp_SM2_a3b1-gsimltp_BA2008-ltr_6.csv',
            'hazard_curve-smltp_SM2_a3b1-gsimltp_CB2008-ltr_7.csv',
            'hazard_curve-smltp_SM2_a3pt2b0pt8-gsimltp_BA2008-ltr_4.csv',
            'hazard_curve-smltp_SM2_a3pt2b0pt8-gsimltp_CB2008-ltr_5.csv',
            'hazard_curve-mean.csv',
            'hazard_uhs-smltp_SM1-gsimltp_BA2008_C2003-ltr_0.csv',
            'hazard_uhs-smltp_SM1-gsimltp_BA2008_T2002-ltr_1.csv',
            'hazard_uhs-smltp_SM1-gsimltp_CB2008_C2003-ltr_2.csv',
            'hazard_uhs-smltp_SM1-gsimltp_CB2008_T2002-ltr_3.csv',
            'hazard_uhs-smltp_SM2_a3b1-gsimltp_BA2008-ltr_6.csv',
            'hazard_uhs-smltp_SM2_a3b1-gsimltp_CB2008-ltr_7.csv',
            'hazard_uhs-smltp_SM2_a3pt2b0pt8-gsimltp_BA2008-ltr_4.csv',
            'hazard_uhs-smltp_SM2_a3pt2b0pt8-gsimltp_CB2008-ltr_5.csv',
            'hazard_uhs-mean.csv',
        ]
        out = self.run_calc(case_15.__file__, 'job.ini', exports='csv')
        for fname in expected:
            self.assertEqualFiles('expected/%s' % fname, out[fname])

    @attr('qa', 'hazard', 'classical')
    def test_case_16(self):
        expected = [
            'hazard_curve-mean.csv',
            'quantile_curve.csv',
        ]
        out = self.run_calc(case_16.__file__, 'job.ini', exports='csv')
        for fname in expected:
            self.assertEqualFiles('expected/%s' % fname, out[fname])

    @attr('qa', 'hazard', 'classical')
    def test_case_17(self):
        expected = [
            'hazard_curve-smltp_b2-gsimltp_b1-ltr_0.csv',
            'hazard_curve-smltp_b2-gsimltp_b1-ltr_1.csv',
            'hazard_curve-smltp_b1-gsimltp_b1-ltr_2.csv',
            'hazard_curve-smltp_b2-gsimltp_b1-ltr_3.csv',
            'hazard_curve-smltp_b2-gsimltp_b1-ltr_4.csv',
        ]
        out = self.run_calc(case_17.__file__, 'job.ini', exports='csv')
        for fname in expected:
            self.assertEqualFiles('expected/%s' % fname, out[fname])
