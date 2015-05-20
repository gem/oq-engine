import os
from nose.plugins.attrib import attr

from openquake.commonlib.tests.calculators import CalculatorTestCase
from openquake.qa_tests_data.event_based_risk import case_1, case_2, case_3


class EventBasedRiskTestCase(CalculatorTestCase):

    def assert_stats_ok(self, pkg):
        out = self.run_calc(pkg.__file__, 'job_haz.ini,job_risk.ini',
                            exports='csv', individual_curves='false',
                            concurrent_tasks=0)
        all_csv = []
        for fnames in out.itervalues():
            for fname in fnames:
                if ('rlz-' not in fname and fname.endswith('.csv')
                        and 'sitecol' not in fname and 'ses-'not in fname):
                    all_csv.append(fname)
        for fname in all_csv:
            self.assertEqualFiles(
                'expected/%s' % os.path.basename(fname), fname)

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_1(self):
        self.assert_stats_ok(case_1)

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_2(self):
        out = self.run_calc(case_2.__file__, 'job_haz.ini,job_risk.ini',
                            concurrent_tasks=0, exports='csv')
        [fname] = out['/loss_curves-rlzs', 'csv']
        self.assertEqualFiles(
            'expected/rlz-000-structural-loss_curves.csv', fname)

        [fname] = out['/agg_loss_curve-rlzs', 'csv']
        self.assertEqualFiles(
            'expected/rlz-000-structural-agg_loss_curve.csv', fname)

        [fname] = out['event_loss_asset', 'csv']
        self.assertEqualFiles(
            'expected/rlz-000-structural-event_loss_asset.csv', fname)

        [fname] = out['event_loss', 'csv']
        self.assertEqualFiles(
            'expected/rlz-000-structural-event_loss.csv', fname)

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_3(self):
        self.assert_stats_ok(case_3)
