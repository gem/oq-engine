import os
from nose.plugins.attrib import attr

from openquake.commonlib.export import export
from openquake.commonlib.datastore import DataStore
from openquake.calculators.tests import CalculatorTestCase
from openquake.qa_tests_data.event_based_risk import (
    case_1, case_2, case_3, case_4, case_4a)


def is_stat(fname):
    # True if the CSV file is related to a statistical output
    # hack: this is determined by the absence of commas in the filename
    return ',' not in fname and any(x in fname for x in (
        'loss_curve', 'loss_map', 'agg_loss', 'avg_loss'))


class EventBasedRiskTestCase(CalculatorTestCase):

    def assert_stats_ok(self, pkg):
        out = self.run_calc(pkg.__file__, 'job_haz.ini,job_risk.ini',
                            exports='csv', individual_curves='false',
                            concurrent_tasks=0)
        all_csv = []
        for fnames in out.values():
            for fname in fnames:
                if fname.endswith('.csv') and is_stat(fname):
                    all_csv.append(fname)
        for fname in all_csv:
            self.assertEqualFiles(
                'expected/%s' % os.path.basename(fname), fname)

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_1(self):
        self.assert_stats_ok(case_1)

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_2(self):
        self.assert_stats_ok(case_2)

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_3(self):
        self.assert_stats_ok(case_3)

    @attr('qa', 'risk', 'ebr')
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
        out = self.run_calc(case_4.__file__, 'job_hazard.ini',
                            ground_motion_fields='false', exports='csv')
        [fname] = out['hcurves', 'csv']
        self.assertEqualFiles('expected/hazard_curve-mean.csv', fname)

    @attr('qa', 'risk', 'ebr')
    def test_case_4(self):
        # Turkey with SHARE logic tree
        out = self.run_calc(case_4.__file__, 'job_ebr.ini',
                            exports='csv')
        fnames = out['agg_losses-rlzs', 'csv']
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
