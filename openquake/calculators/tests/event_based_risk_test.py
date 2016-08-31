# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2016 GEM Foundation
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

import os
import re
from nose.plugins.attrib import attr

from openquake.baselib.general import writetmp
from openquake.calculators.views import view
from openquake.calculators.tests import CalculatorTestCase
from openquake.commonlib.export import export
from openquake.calculators.tests import check_platform
from openquake.qa_tests_data.event_based_risk import (
    case_1, case_2, case_3, case_4, case_4a, case_master, case_miriam,
    occupants)


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
        check_platform('trusty')
        self.assert_stats_ok(case_1, 'job.ini')

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
        self.assert_stats_ok(case_2, 'job.ini', individual_curves='true')
        fname = writetmp(view('mean_avg_losses', self.calc.datastore))
        self.assertEqualFiles('expected/mean_avg_losses.txt', fname)

        # test the case when all GMFs are filtered out
        with self.assertRaises(RuntimeError) as ctx:
            self.run_calc(case_2.__file__, 'job.ini', minimum_intensity='10.0')
        self.assertEqual(
            str(ctx.exception),
            'No GMFs were generated, perhaps they were all below the '
            'minimum_intensity threshold')

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_2bis(self):
        # test for a single realization
        out = self.run_calc(case_2.__file__, 'job_loss.ini', exports='csv',
                            concurrent_tasks='0')
        # this also tests that concurrent_tasks=0 does not give issues
        [fname] = out['agg_loss_table', 'csv']
        self.assertEqualFiles('expected/agg_losses_bis.csv', fname)

    @attr('qa', 'risk', 'event_based_risk')
    def test_missing_taxonomy(self):
        with self.assertRaises(RuntimeError) as ctx:
            self.run_calc(case_2.__file__, 'job_err.ini')
        self.assertIn('not in the risk model', str(ctx.exception))

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_3(self):
        # this is a test with statistics and without conditional_loss_poes
        out = self.run_calc(case_3.__file__, 'job.ini',
                            exports='xml', individual_curves='false',
                            concurrent_tasks='4')
        [fname] = out['agg_curve-stats', 'xml']
        self.assertEqualFiles('expected/%s' % strip_calc_id(fname), fname)

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_4(self):
        # Turkey with SHARE logic tree
        out = self.run_calc(case_4.__file__, 'job.ini',
                            exports='csv', individual_curves='true')
        [fname] = out['avg_losses-stats', 'csv']
        self.assertEqualFiles('expected/avg_losses-mean.csv', fname)

        fnames = out['agg_loss_table', 'csv']
        assert fnames, 'No agg_losses exported??'
        for fname in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(fname), fname)

    @attr('qa', 'risk', 'event_based_risk')
    def test_occupants(self):
        out = self.run_calc(occupants.__file__, 'job.ini',
                            exports='xml', individual_curves='true')
        fnames = out['loss_maps-rlzs', 'xml'] + out['agg_curve-rlzs', 'xml']
        self.assertEqual(len(fnames), 3)  # 2 loss_maps + 1 agg_curve
        for fname in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(fname), fname)

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_master(self):
        check_platform('trusty')
        self.assert_stats_ok(case_master, 'job.ini')
        fname = writetmp(view('portfolio_loss', self.calc.datastore))
        self.assertEqualFiles('expected/portfolio_loss.txt', fname)

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_miriam(self):
        # this is a case with a grid and asset-hazard association
        out = self.run_calc(case_miriam.__file__, 'job.ini', exports='csv')
        [fname] = out['agg_loss_table', 'csv']
        self.assertEqualFiles('expected/agg_losses-rlz000-structural.csv',
                              fname)

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

        # export a single rupture
        [f1, f2] = export(('gmfs:0', 'csv'), self.calc.datastore)
        self.assertEqualFiles(
            'expected/gmf-trt=05'
            '~ses=0001~src=AS_TRAS334~rup=612021-01-PGA.csv', f1)
        self.assertEqualFiles(
            'expected/gmf-trt=05'
            '~ses=0001~src=AS_TRAS334~rup=612021-01-SA(0.5).csv', f2)

    @attr('qa', 'hazard', 'event_based')
    def test_case_4a(self):
        # the case of a site_model.xml with 7 sites but only 1 asset
        out = self.run_calc(case_4a.__file__, 'job_hazard.ini',
                            exports='txt')
        [fname] = out['gmf_data', 'txt']
        self.assertEqualFiles(
            'expected/gmf-smltp_b1-gsimltp_b1.txt', fname)
