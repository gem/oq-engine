import os
import re
from nose.plugins.attrib import attr

from openquake.calculators.views import view
from openquake.calculators.tests import CalculatorTestCase
from openquake.commonlib.export import export
from openquake.qa_tests_data.event_based_risk import (
    case_1, case_2, case_3, case_4, case_4a, case_master, occupants)


def strip_calc_id(fname):
    name = os.path.basename(fname)
    return re.sub('_\d+\.', '.', name)


class EventBasedRiskTestCase(CalculatorTestCase):

    def assert_stats_ok(self, pkg, job_ini, individual_curves='false'):
        out = self.run_calc(pkg.__file__, job_ini, exports='csv',
                            individual_curves=individual_curves,
                            concurrent_tasks='4')
        # NB: it is important to use concurrent_tasks > 1 to test the
        # complications of concurrency (for instance the noncommutativity of
        # numpy.float32 addition when computing the average losses)
        all_csv = []
        for fnames in out.values():
            for fname in fnames:
                if 'rlz' in fname and individual_curves == 'false':
                    continue
                elif fname.endswith('.csv') and any(x in fname for x in (
                        'loss_curve', 'loss_map', 'agg_loss', 'avg_loss')):
                    all_csv.append(fname)
        assert all_csv, 'Could not find any CSV file??'
        for fname in all_csv:
            self.assertEqualFiles(
                'expected/%s' % strip_calc_id(fname), fname)

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_1(self):
        self.assert_stats_ok(case_1, 'job_haz.ini,job_risk.ini')

        # make sure the XML and JSON exporters run
        ekeys = [
            ('loss_curves-stats', 'xml'),
            ('loss_curves-stats', 'geojson'),
            ('rcurves-rlzs', 'xml'),
            ('rcurves-rlzs', 'geojson'),

            ('loss_maps-stats', 'xml'),
            ('loss_maps-stats', 'geojson'),
            ('loss_maps-rlzs', 'xml'),
            ('loss_maps-rlzs', 'geojson'),

            ('agg_curve-stats', 'xml'),
        ]
        for ekey in ekeys:
            export(ekey, self.calc.datastore)

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_2(self):
        self.assert_stats_ok(case_2, 'job_haz.ini,job_risk.ini',
                             individual_curves='true')
        text = view('mean_avg_losses', self.calc.datastore)
        self.assertEqual(text, '''\
========= ============ ============ ============ ==============
asset_ref lon          lat          structural   structural_ins
========= ============ ============ ============ ==============
a0        8.129850E+01 2.910980E+01 3.500932E+02 3.672644E+01  
a1        8.308230E+01 2.790060E+01 1.465656E+02 3.293761E+01  
a2        8.574770E+01 2.790150E+01 8.956219E+01 5.956219E+01  
a3        8.574770E+01 2.790150E+01 1.294835E+02 0.000000E+00  
========= ============ ============ ============ ==============''')

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_2bis(self):
        # test for a single realization
        out = self.run_calc(case_2.__file__, 'job_loss.ini', exports='csv',
                            concurrent_tasks='0')
        # this also tests that concurrent_tasks=0 does not give issues
        [fname] = out['agg_loss_table', 'csv']
        self.assertEqualFiles(
            'expected/agg_losses-b1,b1-structural.csv', fname)

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_3(self):
        out = self.run_calc(case_3.__file__, 'job_haz.ini,job_risk.ini',
                            exports='xml', individual_curves='false',
                            concurrent_tasks='4')
        [fname] = out['agg_curve-stats', 'xml']
        self.assertEqualFiles('expected/%s' % strip_calc_id(fname), fname)

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_4(self):
        # Turkey with SHARE logic tree
        out = self.run_calc(case_4.__file__, 'job_h.ini,job_r.ini',
                            exports='csv', individual_curves='true')
        fnames = out['agg_loss_table', 'csv']
        assert fnames, 'No agg_losses exported??'
        for fname in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(fname), fname)

    @attr('qa', 'risk', 'event_based_risk')
    def test_occupants(self):
        out = self.run_calc(occupants.__file__, 'job_h.ini,job_r.ini',
                            exports='xml', individual_curves='true')
        fnames = out['loss_maps-rlzs', 'xml'] + out['agg_curve-rlzs', 'xml']
        assert fnames, 'Nothing exported??'
        for fname in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(fname), fname)

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_master(self):
        self.assert_stats_ok(case_master, 'job.ini')

    # now a couple of hazard tests

    @attr('qa', 'hazard', 'event_based')
    def test_case_4_hazard(self):
        # Turkey with SHARE logic tree; TODO: add site model
        out = self.run_calc(case_4.__file__, 'job_h.ini',
                            ground_motion_fields='false', exports='csv')
        [fname] = out['hcurves', 'csv']
        self.assertEqualFiles('expected/hazard_curve-mean.csv', fname)
        [fname] = out['hmaps', 'csv']
        self.assertEqualFiles('expected/hazard_map-mean.csv', fname)

        fnames = export(('hmaps', 'xml'), self.calc.datastore)
        self.assertEqual(len(fnames), 4)  # 2 IMT x 2 poes

    @attr('qa', 'hazard', 'event_based')
    def test_case_4a(self):
        # the case of a site_model.xml with 7 sites but only 1 asset
        out = self.run_calc(case_4a.__file__, 'job_hazard.ini',
                            exports='csv')
        [fname] = out['gmfs', 'csv']
        self.assertEqualFiles(
            'expected/gmf-smltp_b1-gsimltp_b1.csv', fname)
