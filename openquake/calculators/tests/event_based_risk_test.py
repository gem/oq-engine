# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2017 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.
import unittest
from nose.plugins.attrib import attr

from openquake.baselib.general import writetmp
from openquake.commonlib.writers import OLD_NUMPY
from openquake.calculators.views import view
from openquake.calculators.tests import CalculatorTestCase, strip_calc_id
from openquake.calculators.export import export
from openquake.calculators.tests import check_platform
from openquake.qa_tests_data.event_based_risk import (
    case_1, case_2, case_3, case_4, case_4a, case_master, case_miriam,
    occupants)


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
        self.assert_stats_ok(case_1, 'job.ini', individual_curves='false')

        # the numbers in the xml and geojson files are extremely sensitive to
        # the libraries; while waiting for the opt project we skip this test
        check_platform('xenial')
        ekeys = [
            ('rcurves-stats', 'xml'),
            ('rcurves-stats', 'geojson'),

            ('loss_maps-stats', 'csv'),
            ('loss_maps-stats', 'xml'),
            ('loss_maps-stats', 'geojson'),

            ('agg_curve-stats', 'xml'),
        ]
        for ekey in ekeys:
            for fname in export(ekey, self.calc.datastore):
                self.assertEqualFiles(
                    'expected/%s' % strip_calc_id(fname), fname)

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_2(self):
        if OLD_NUMPY:
            raise unittest.SkipTest('numpy too old to export agg_loss_table')
        self.assert_stats_ok(case_2, 'job.ini', individual_curves='true')
        fname = writetmp(view('mean_avg_losses', self.calc.datastore))
        self.assertEqualFiles('expected/mean_avg_losses.txt', fname)

        # test the composite_risk_model keys (i.e. slash escaping)
        crm = sorted(self.calc.datastore.getitem('composite_risk_model'))
        self.assertEqual(crm, ['RC%2B', 'RM', 'W%2F1'])
        # export a specific eid
        [fname] = export(('all_loss_ratios:0', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/losses-eid=0.csv', fname)

        # test the case when all GMFs are filtered out
        with self.assertRaises(RuntimeError) as ctx:
            self.run_calc(case_2.__file__, 'job.ini', minimum_intensity='10.0')
        self.assertEqual(
            str(ctx.exception),
            'No GMFs were generated, perhaps they were all below the '
            'minimum_intensity threshold')

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_2_correlation(self):
        out = self.run_calc(case_2.__file__, 'job_loss.ini', exports='csv',
                            asset_correlation=1.0)
        [fname] = out['agg_loss_table', 'csv']
        if OLD_NUMPY:
            raise unittest.SkipTest('numpy too old to export agg_loss_table')
        self.assertEqualFiles('expected/agg_losses.csv', fname)

    @attr('qa', 'risk', 'event_based_risk')
    def test_missing_taxonomy(self):
        with self.assertRaises(RuntimeError) as ctx:
            self.run_calc(case_2.__file__, 'job_err.ini')
        self.assertIn('not in the risk model', str(ctx.exception))

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_3(self):
        # this is a test with statistics and without conditional_loss_poes
        self.run_calc(case_3.__file__, 'job.ini',
                      exports='xml', individual_curves='false',
                      concurrent_tasks='4')
        [fname] = export(('agg_curve-stats', 'xml'), self.calc.datastore)
        self.assertEqualFiles('expected/%s' % strip_calc_id(fname), fname)

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_4(self):
        # Turkey with SHARE logic tree
        out = self.run_calc(case_4.__file__, 'job.ini',
                            exports='csv', individual_curves='true')
        [fname] = export(('avg_losses-stats', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/avg_losses-mean.csv', fname)
        if OLD_NUMPY:
            raise unittest.SkipTest('numpy too old to export agg_loss_table')

        fnames = out['agg_loss_table', 'csv']
        assert fnames, 'No agg_losses exported??'
        for fname in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(fname), fname)

        # this is a case without loss_ratios in the .ini file
        # we check that no risk curves are generated
        self.assertNotIn('rcurves-rlzs', self.calc.datastore)
        self.assertNotIn('rcurves-stats', self.calc.datastore)

    @attr('qa', 'risk', 'event_based_risk')
    def test_occupants(self):
        out = self.run_calc(occupants.__file__, 'job.ini',
                            exports='xml', individual_curves='true')
        fnames = export(('loss_maps-rlzs', 'xml'), self.calc.datastore) + \
                 out['agg_curve-rlzs', 'xml']
        self.assertEqual(len(fnames), 3)  # 2 loss_maps + 1 agg_curve
        for fname in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(fname), fname)

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_master(self):
        self.assert_stats_ok(case_master, 'job.ini', individual_curves='false')

        fnames = export(('loss_maps-rlzs', 'csv'), self.calc.datastore)
        for fname in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(fname), fname)

        fname = writetmp(view('portfolio_loss', self.calc.datastore))
        self.assertEqualFiles('expected/portfolio_loss.txt', fname, delta=1E-5)

        # check rup_data is stored correctly
        fname = writetmp(view('ruptures_events', self.calc.datastore))
        self.assertEqualFiles('expected/ruptures_events.txt', fname)

        # export a specific eid
        fnames = export(('all_loss_ratios:0', 'csv'), self.calc.datastore)
        for fname in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(fname), fname)
        self.assertEqualFiles('expected/losses-eid=0.csv', fname)

        # export a specific pair (sm_id, eid)
        fnames = export(('all_loss_ratios:1:0', 'csv'),
                        self.calc.datastore)
        for fname in fnames:
            self.assertEqualFiles('expected/%s' % strip_calc_id(fname), fname)

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_miriam(self):
        # this is a case with a grid and asset-hazard association
        out = self.run_calc(case_miriam.__file__, 'job.ini', exports='csv')
        if OLD_NUMPY:
            raise unittest.SkipTest('numpy too old to export agg_loss_table')

        [fname] = out['agg_loss_table', 'csv']
        self.assertEqualFiles('expected/agg_losses-rlz000-structural.csv',
                              fname)
        fname = writetmp(view('portfolio_loss', self.calc.datastore))
        self.assertEqualFiles(
            'expected/portfolio_loss.txt', fname, delta=1E-5)

    # now a couple of hazard tests

    @attr('qa', 'hazard', 'event_based')
    def test_case_4_hazard(self):
        # Turkey with SHARE logic tree; TODO: add site model
        out = self.run_calc(case_4.__file__, 'job.ini',
                            calculation_mode='event_based',
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
                            exports='txt')
        [fname] = out['gmf_data', 'txt']
        self.assertEqualFiles(
            'expected/gmf-smltp_b1-gsimltp_b1.txt', fname)
