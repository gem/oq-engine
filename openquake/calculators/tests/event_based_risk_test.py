import os
from nose.plugins.attrib import attr

from openquake.calculators.tests import CalculatorTestCase
from openquake.qa_tests_data.event_based_risk import (
    case_1, case_2, case_3, case_4, case_4a)


class EventBasedRiskTestCase(CalculatorTestCase):

    def assert_stats_ok(self, pkg, individual_curves='false'):
        out = self.run_calc(pkg.__file__, 'job_haz.ini,job_risk.ini',
                            exports='csv', individual_curves=individual_curves,
                            concurrent_tasks=4)
        # NB: it is important to use concurrent_tasks > 1 to test the
        # complications of concurrency (for instance the noncommutativity of
        # numpy.float32 addition when computing the average losses)
        all_csv = []
        for fnames in out.values():
            for fname in fnames:
                if fname.endswith('.csv') and any(x in fname for x in (
                        'loss_curve', 'loss_map', 'agg_loss', 'avg_loss')):
                    all_csv.append(fname)
        assert all_csv, 'Could not find any CSV file??'
        for fname in all_csv:
            self.assertEqualFiles(
                'expected/%s' % os.path.basename(fname), fname)

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_1(self):
        self.assert_stats_ok(case_1)

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_2(self):
        self.assert_stats_ok(case_2, individual_curves='true')

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_3(self):
        self.assert_stats_ok(case_3)

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_2bis(self):
        # test for a single realization
        out = self.run_calc(case_2.__file__, 'job_loss.ini', exports='csv',
                            concurrent_tasks=0)
        # this also tests that concurrent_tasks=0 does not give issues
        [fname] = out['agg_losses-rlzs', 'csv']
        self.assertEqualFiles(
            'expected/agg_losses-b1,b1-structural.csv', fname)

    @attr('qa', 'hazard', 'event_based')
    def test_case_4_hazard(self):
        # Turkey with SHARE logic tree; TODO: add site model
        out = self.run_calc(case_4.__file__, 'job_h.ini',
                            ground_motion_fields='false', exports='csv')
        [fname] = out['hcurves', 'csv']
        self.assertEqualFiles('expected/hazard_curve-mean.csv', fname)

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_4(self):
        # Turkey with SHARE logic tree
        out = self.run_calc(case_4.__file__, 'job_h.ini,job_r.ini',
                            exports='csv', individual_curves='true')
        fnames = out['agg_losses-rlzs', 'csv']
        assert fnames, 'No agg_losses-rlzs exported??'
        for fname in fnames:
            self.assertEqualFiles('expected/' + os.path.basename(fname), fname)

    @attr('qa', 'hazard', 'event_based')
    def test_case_4a(self):
        # the case of a site_model.xml with 7 sites but only 1 asset
        out = self.run_calc(case_4a.__file__, 'job_hazard.ini',
                            exports='csv')
        [fname] = out['gmfs', 'csv']
        self.assertEqualFiles(
            'expected/gmf-smltp_b1-gsimltp_b1.csv', fname)
