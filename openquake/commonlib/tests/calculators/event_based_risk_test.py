from nose.plugins.attrib import attr

from openquake.commonlib.tests.calculators import CalculatorTestCase
from openquake.qa_tests_data.event_based_risk import case_1, case_2, case_3


class EventBasedRiskTestCase(CalculatorTestCase):
    @attr('qa', 'risk', 'event_based_risk')
    def test_case_1(self):
        out = self.run_calc(case_1.__file__, 'job_haz.ini,job_risk.ini',
                            exports='csv', individual_curves='false',
                            concurrent_tasks=0)
        for key in out:
            self.assertEqualFiles('expected/%s.csv' % key, out[key])

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_2(self):
        out = self.run_calc(case_2.__file__, 'job_haz.ini,job_risk.ini',
                            concurrent_tasks=0, exports='csv')
        self.assertEqualFiles(
            'expected/rlz-000-structural-event-loss-asset.csv',
            out['rlz-000-structural-event-loss-asset'])

        self.assertEqualFiles(
            'expected/rlz-000-structural-event-loss.csv',
            out['rlz-000-structural-event-loss'])

        self.assertEqualFiles(
            'expected/rlz-000-structural-agg-loss-curve.csv',
            out['rlz-000-structural-agg-loss-curve'])

        self.assertEqualFiles(
            'expected/rlz-000-structural-loss-curves.csv',
            out['rlz-000-structural-loss-curves'])

    @attr('qa', 'risk', 'event_loss')
    def test_case_3(self):
        out = self.run_calc(case_3.__file__, 'job_haz.ini,job_risk.ini',
                            exports='csv', individual_curves='false',
                            concurrent_tasks=0)
        for key in out:
            self.assertEqualFiles('expected/%s.csv' % key, out[key])
