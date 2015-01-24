from nose.plugins.attrib import attr

from openquake.commonlib.tests.calculators import CalculatorTestCase
from openquake.qa_tests_data.event_based import (
    case_1, case_2, case_4, case_5, case_6, case_12, case_13, case_17)


# NB: the tests break for concurrent_tasks > 0 !
# this is due to the hazard curve conversion algorithm;
# maybe there is a way to solve this
class EventBasedTestCase(CalculatorTestCase):

    @attr('qa', 'hazard', 'event_based')
    def test_case_1(self):
        out = self.run_calc(case_1.__file__, 'job.ini', exports='csv',
                            concurrent_tasks=0)
        self.assertEqualFiles(
            'expected/0-SadighEtAl1997.csv',
            out['0-SadighEtAl1997.csv'], sorted)
        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1-ltr_0.csv',
            out['hazard_curve-smltp_b1-gsimltp_b1-ltr_0.csv'])

    @attr('qa', 'hazard', 'event_based')
    def test_case_2(self):
        out = self.run_calc(case_2.__file__, 'job.ini', exports='csv')
        self.assertEqualFiles(
            'expected/0-SadighEtAl1997.csv',
            out['0-SadighEtAl1997.csv'], sorted)
        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1-ltr_0.csv',
            out['hazard_curve-smltp_b1-gsimltp_b1-ltr_0.csv'])

    @attr('qa', 'hazard', 'event_based')
    def test_case_4(self):
        out = self.run_calc(case_4.__file__, 'job.ini', exports='csv')
        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1-ltr_0.csv',
            out['hazard_curve-smltp_b1-gsimltp_b1-ltr_0.csv'])

    @attr('qa', 'hazard', 'event_based')
    def test_case_5(self):
        expected = [
            '0-FaccioliEtAl2010.csv',
            '1-ChiouYoungs2008.csv',
            '2-Campbell2003SHARE.csv',
            '2-ToroEtAl2002SHARE.csv',
            '1-AkkarBommer2010.csv',
            '1-ZhaoEtAl2006Asc.csv',
            '2-CauzziFaccioli2008.csv',
            '3-FaccioliEtAl2010.csv',
            '1-CauzziFaccioli2008.csv',
            '2-AkkarBommer2010.csv',
            '2-ChiouYoungs2008.csv',
        ]
        out = self.run_calc(case_5.__file__, 'job.ini', exports='csv')
        for fname in expected:
            self.assertEqualFiles('expected/%s' % fname, out[fname], sorted)

    @attr('qa', 'hazard', 'event_based')
    def test_case_6(self):
        expected = [
            'hazard_curve-smltp_b11-gsimltp_b11-ltr_0.csv',
            'hazard_curve-smltp_b11-gsimltp_b12-ltr_1.csv',
            'hazard_curve-smltp_b11-gsimltp_b13-ltr_2.csv',
            'hazard_curve-smltp_b12-gsimltp_b11-ltr_3.csv',
            'hazard_curve-smltp_b12-gsimltp_b12-ltr_4.csv',
            'hazard_curve-smltp_b12-gsimltp_b13-ltr_5.csv',
            'hazard_curve-mean.csv',
        ]
        out = self.run_calc(case_6.__file__, 'job.ini', exports='csv')
        for fname in expected:
            self.assertEqualFiles('expected/%s' % fname, out[fname])

    @attr('qa', 'hazard', 'event_based')
    def test_case_12(self):
        out = self.run_calc(case_12.__file__, 'job.ini', exports='csv',
                            concurrent_tasks=0)
        self.assertEqualFiles('expected/0-SadighEtAl1997.csv',
                              out['0-SadighEtAl1997.csv'], sorted)
        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1_b2-ltr_0.csv',
            out['hazard_curve-smltp_b1-gsimltp_b1_b2-ltr_0.csv'])

    @attr('qa', 'hazard', 'event_based')
    def test_case_13(self):
        out = self.run_calc(case_13.__file__, 'job.ini', exports='csv',
                            concurrent_tasks=0)
        self.assertEqualFiles('expected/0-BooreAtkinson2008.csv',
                              out['0-BooreAtkinson2008.csv'], sorted)
        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1-ltr_0.csv',
            out['hazard_curve-smltp_b1-gsimltp_b1-ltr_0.csv'])

    @attr('qa', 'hazard', 'event_based')
    def test_case_17(self):
        expected = [
            'hazard_curve-smltp_b2-gsimltp_b1-ltr_0.csv',
            'hazard_curve-smltp_b2-gsimltp_b1-ltr_1.csv',
            'hazard_curve-smltp_b1-gsimltp_b1-ltr_2.csv',
            'hazard_curve-smltp_b2-gsimltp_b1-ltr_3.csv',
            'hazard_curve-smltp_b2-gsimltp_b1-ltr_4.csv',
            'hazard_curve-mean.csv',
        ]
        out = self.run_calc(case_17.__file__, 'job.ini', exports='csv',
                            concurrent_tasks=0)
        for fname in expected:
            self.assertEqualFiles('expected/%s' % fname, out[fname], sorted)
