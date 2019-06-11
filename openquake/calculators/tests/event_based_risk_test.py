# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2019 GEM Foundation
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
import sys
import unittest
import numpy

from openquake.baselib.general import gettemp
from openquake.calculators.views import view, rst_table
from openquake.calculators.tests import CalculatorTestCase, strip_calc_id
from openquake.calculators.export import export
from openquake.calculators.extract import extract
from openquake.qa_tests_data.event_based_risk import (
    case_1, case_2, case_3, case_4, case_4a, case_6c, case_master, case_miriam,
    occupants, case_1g, case_7a)


def aae(data, expected):
    for data_, expected_ in zip(data, expected):
        for got, exp in zip(data_, expected_):
            if isinstance(got, str):
                numpy.testing.assert_equal(got, exp)
            else:
                numpy.testing.assert_almost_equal(got, numpy.float32(exp))


class EventBasedRiskTestCase(CalculatorTestCase):

    def check_attr(self, name, value):
        got = self.calc.datastore.get_attr('agg_curves-stats', name)
        numpy.testing.assert_equal(value, got)

    def assert_stats_ok(self, pkg, job_ini):
        out = self.run_calc(pkg.__file__, job_ini, exports='csv',
                            concurrent_tasks='4')
        # NB: it is important to use concurrent_tasks > 1 to test the
        # complications of concurrency (for instance the noncommutativity of
        # numpy.float32 addition when computing the average losses)
        all_csv = []
        for fnames in out.values():
            for fname in fnames:
                if 'rlz' in fname:
                    continue
                elif fname.endswith('.csv') and any(x in fname for x in (
                        'loss_curve', 'loss_map', 'agg_loss', 'avg_loss')):
                    all_csv.append(fname)
        assert all_csv, 'Could not find any CSV file??'
        for fname in all_csv:
            self.assertEqualFiles(
                'expected/%s' % strip_calc_id(fname), fname)

    def test_case_1(self):
        self.run_calc(case_1.__file__, 'job.ini')
        ekeys = [('agg_curves-stats', 'csv')]
        for ekey in ekeys:
            for fname in export(ekey, self.calc.datastore):
                self.assertEqualFiles(
                    'expected/%s' % strip_calc_id(fname), fname)

        # make sure the agg_curves-stats has the right attrs
        self.check_attr('return_periods', [30, 60, 120, 240, 480, 960])
        self.check_attr('units', [b'EUR', b'EUR'])
        self.check_attr('nbytes', 96)

        # test the loss curves exporter
        [f1] = export(('loss_curves/rlz-0', 'csv'), self.calc.datastore)
        [f2] = export(('loss_curves/rlz-1', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/loss_curves-rlz-000.csv', f1)
        self.assertEqualFiles('expected/loss_curves-rlz-001.csv', f2)

        [f] = export(('loss_curves/mean', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/loss_curves-mean.csv', f)

        # test the loss maps exporter
        fnames = export(('loss_maps-stats', 'csv'), self.calc.datastore)
        assert fnames
        for fname in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(fname),
                                  fname, delta=1E-5)

        # test portfolio loss
        tmp = gettemp(view('portfolio_loss', self.calc.datastore))
        self.assertEqualFiles('expected/portfolio_loss.txt', tmp)

        # test the rup_loss_table exporter
        fnames = export(('rup_loss_table', 'xml'), self.calc.datastore)
        self.assertEqual(len(fnames), 2)
        for fname in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(fname),
                                  fname)

        # test the src_loss_table extractor
        arr = extract(self.calc.datastore, 'src_loss_table/structural')
        tmp = gettemp(rst_table(arr))
        self.assertEqualFiles('expected/src_loss_table.txt', tmp)

    def test_case_1g(self):
        # vulnerability function with PMF
        self.run_calc(case_1g.__file__, 'job_h.ini,job_r.ini')
        [fname] = export(('avg_losses-rlzs', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/avg_losses.csv', fname)
        os.remove(fname)

    def test_case_12(self):
        # 1 assets, 2 samples
        self.run_calc(case_master.__file__, 'job12.ini', exports='csv')
        # alt = extract(self.calc.datastore, 'asset_loss_table')
        [fname] = export(('avg_losses', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/avg_loss_12.csv', fname)

    def test_case_2(self):
        self.run_calc(case_2.__file__, 'job.ini')

        # test the composite_risk_model keys (i.e. slash escaping)
        crm = sorted(self.calc.datastore.getitem('risk_model'))
        self.assertEqual(crm, ['RC%2B', 'RM', 'W%2F1'])

        # test the case when all GMFs are filtered out
        with self.assertRaises(RuntimeError) as ctx:
            self.run_calc(case_2.__file__, 'job.ini', minimum_intensity='10.0')
        self.assertEqual(
            str(ctx.exception),
            'No GMFs were generated, perhaps they were all below the '
            'minimum_intensity threshold')

    def test_case_2_sampling(self):
        self.run_calc(case_2.__file__, 'job_sampling.ini')
        self.assertEqual(len(self.calc.datastore['events']), 20)
        # TODO: improve this test

    def test_case_2_correlation(self):
        self.run_calc(case_2.__file__, 'job_loss.ini', asset_correlation=1.0)
        [fname] = export(('losses_by_event', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/agg_losses.csv', fname)

        # test losses_by_tag with a single realization
        [fname] = export(
            ('aggregate_by/avg_losses?tag=taxonomy&kind=rlz-0', 'csv'),
            self.calc.datastore)
        self.assertEqualFiles('expected/losses_by_tag.csv', fname)

    def test_missing_taxonomy(self):
        with self.assertRaises(RuntimeError) as ctx:
            self.run_calc(case_2.__file__, 'job_err.ini')
        self.assertIn('not in the risk model', str(ctx.exception))

    def test_case_3(self):
        # this is a test with statistics and without conditional_loss_poes
        self.run_calc(case_3.__file__, 'job.ini',
                      exports='csv', concurrent_tasks='4')

        # test the number of bytes saved in the rupture records
        nbytes = self.calc.datastore.get_attr('ruptures', 'nbytes')
        self.assertEqual(nbytes, 3180)

        # test postprocessing
        self.calc.datastore.close()
        hc_id = self.calc.datastore.calc_id
        self.run_calc(case_3.__file__, 'job.ini',
                      exports='csv', hazard_calculation_id=str(hc_id))
        [fname] = export(('agg_curves-stats', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/%s' % strip_calc_id(fname), fname)

    def test_case_4(self):
        # Turkey with SHARE logic tree
        self.run_calc(case_4.__file__, 'job.ini')
        [fname] = export(('avg_losses-stats', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/avg_losses-mean.csv', fname)

        fnames = export(('losses_by_event', 'csv'), self.calc.datastore)
        assert fnames, 'No agg_losses exported??'
        for fname in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(fname), fname)

        # check that individual_curves = false is honored
        self.assertFalse('curves-rlzs' in self.calc.datastore)
        self.assertTrue('curves-stats' in self.calc.datastore)

    def test_occupants(self):
        self.run_calc(occupants.__file__, 'job.ini')
        fnames = export(('agg_curves-rlzs', 'csv'), self.calc.datastore)
        for fname in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(fname),
                                  fname, delta=1E-5)

        fnames = export(('loss_maps-rlzs', 'csv'), self.calc.datastore)
        assert fnames, 'loss_maps-rlzs not exported?'
        for fname in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(fname),
                                  fname, delta=1E-5)

    def test_case_master(self):
        if sys.platform == 'darwin':
            raise unittest.SkipTest('MacOSX')
        self.run_calc(case_master.__file__, 'job.ini', exports='csv')
        fnames = export(('avg_losses-stats', 'csv'), self.calc.datastore)
        assert fnames, 'avg_losses-stats not exported?'
        for fname in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(fname), fname,
                                  delta=1E-5)

        # check event loss table
        [fname] = export(('losses_by_event', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/' + strip_calc_id(fname), fname,
                              delta=1E-5)

        # extract loss_curves/rlz-1 (with the first asset having zero losses)
        [fname] = export(('loss_curves/rlz-1', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/' + strip_calc_id(fname), fname,
                              delta=1E-5)

        fnames = export(('loss_maps-rlzs', 'csv'), self.calc.datastore)
        assert fnames, 'loss_maps-rlzs not exported?'
        for fname in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(fname),
                                  fname, delta=1E-5)

        fname = gettemp(view('portfolio_losses', self.calc.datastore))
        self.assertEqualFiles(
            'expected/portfolio_losses.txt', fname, delta=1E-5)
        os.remove(fname)

        # check ruptures are stored correctly
        fname = gettemp(view('ruptures_events', self.calc.datastore))
        self.assertEqualFiles('expected/ruptures_events.txt', fname)
        os.remove(fname)

        # check losses_by_tag
        fnames = export(
            ('aggregate_by/avg_losses?tag=occupancy&kind=mean', 'csv'),
            self.calc.datastore)
        self.assertEqualFiles('expected/losses_by_occupancy.csv', fnames[0])

        self.check_multi_tag(self.calc.datastore)

        # ------------------------- ebrisk calculator ---------------------- #
        self.run_calc(case_master.__file__, 'job.ini',
                      calculation_mode='ebrisk', exports='',
                      aggregate_by='id')

        # agg_losses-rlzs has shape (L=5, R=9)
        # agg_losses-stats has shape (L=5, S=4)
        fname = export(('agg_losses-stats', 'csv'), self.calc.datastore)[0]
        self.assertEqualFiles('expected/agglosses.csv', fname, delta=1E-5)

        fname = export(('agg_curves-stats', 'csv'), self.calc.datastore)[0]
        self.assertEqualFiles('expected/aggcurves.csv', fname, delta=1E-5)

        fname = export(('agg_maps-stats', 'csv'), self.calc.datastore)[0]
        self.assertEqualFiles('expected/aggmaps.csv', fname, delta=1E-5)

        fname = export(('avg_losses', 'csv'), self.calc.datastore)[0]
        self.assertEqualFiles('expected/avg_losses-mean.csv',
                              fname, delta=1E-5)

        fname = export(('losses_by_event', 'csv'), self.calc.datastore)[0]
        self.assertEqualFiles('expected/elt.csv', fname)

    def check_multi_tag(self, dstore):
        # multi-tag aggregations
        arr = extract(dstore, 'aggregate/avg_losses?'
                      'tag=taxonomy&tag=occupancy&kind=quantile-0.5')
        self.assertEqual(len(arr.to_table()), 1)

        # aggregate by all loss types
        fnames = export(
            ('aggregate_by/avg_losses?tag=taxonomy&tag=occupancy&kind=mean',
             'csv'),
            dstore)
        for fname in fnames:
            self.assertEqualFiles('expected/%s' % strip_calc_id(fname), fname)

    def test_case_miriam(self):
        # this is a case with a grid and asset-hazard association
        self.run_calc(case_miriam.__file__, 'job.ini')

        # check minimum_magnitude >= 5.2
        minmag = self.calc.datastore['ruptures']['mag'].min()
        self.assertGreaterEqual(minmag, 5.2)

        # check asset_loss_table
        tot = self.calc.datastore['asset_loss_table'][()].sum()
        self.assertEqual(tot, 15787827.0)
        fname = gettemp(view('portfolio_losses', self.calc.datastore))
        self.assertEqualFiles(
            'expected/portfolio_losses.txt', fname, delta=1E-5)

        # this is a case with exposure and region_grid_spacing=1
        self.run_calc(case_miriam.__file__, 'job2.ini')
        hcurves = dict(extract(self.calc.datastore, 'hcurves'))['all']
        sitecol = self.calc.datastore['sitecol']  # filtered sitecol
        self.assertEqual(len(hcurves), len(sitecol))
        assetcol = self.calc.datastore['assetcol']
        self.assertEqual(len(sitecol), 15)
        self.assertGreater(sitecol.vs30.sum(), 0)
        self.assertEqual(len(assetcol), 548)

    def test_case_7a(self):
        # case with preimported exposure
        self.run_calc(case_7a.__file__,  'job_h.ini')
        self.run_calc(case_7a.__file__,  'job_r.ini',
                      hazard_calculation_id=str(self.calc.datastore.calc_id))
        [fname] = export(('losses_by_event', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/agg_losses.csv', fname)

        [fname] = export(('agg_curves-rlzs', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/agg_curves.csv', fname)

    def test_case_4_hazard(self):
        # Turkey with SHARE logic tree; TODO: add site model
        # it has 8 realizations but 4 of them have 0 ruptures
        out = self.run_calc(case_4.__file__, 'job.ini',
                            calculation_mode='event_based', exports='csv')
        [f1, f2] = [f for f in out['hcurves', 'csv'] if 'mean' in f]
        self.assertEqualFiles('expected/hazard_curve-mean-PGA.csv', f1)
        self.assertEqualFiles('expected/hazard_curve-mean-SA(0.5).csv', f2)
        [fname] = [f for f in out['hmaps', 'csv'] if 'mean' in f]
        self.assertEqualFiles('expected/hazard_map-mean.csv', fname)

        fnames = export(('hmaps', 'xml'), self.calc.datastore)
        self.assertEqual(len(fnames), 4)  # 2 IMT x 2 poes

    def test_case_4a(self):
        # the case of a site_model.xml with 7 sites but only 1 asset
        out = self.run_calc(case_4a.__file__, 'job_hazard.ini',
                            exports='csv')
        [fname, _sigeps, _sitefile] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/gmf-data.csv', fname)

    def test_case_4b(self):
        # case with site collection extracted from site_model.xml
        self.run_calc(case_4a.__file__, 'job.ini')
        self.assertEqual(len(self.calc.datastore['events']), 8)

    def test_case_6c(self):
        # case with asset_correlation=1
        self.run_calc(case_6c.__file__, 'job_h.ini')
        hc = str(self.calc.datastore.calc_id)
        out = self.run_calc(case_6c.__file__, 'job_r.ini', exports='csv',
                            hazard_calculation_id=hc)
        [fname] = out['avg_losses-rlzs', 'csv']
        self.assertEqualFiles('expected/avg_losses.csv', fname, delta=1E-5)

        [fname] = out['agg_curves-rlzs', 'csv']
        self.assertEqualFiles('expected/agg_curves.csv', fname, delta=1E-5)

    def test_asset_loss_table(self):
        # this is a case with L=1, R=1, T=2, P=3
        out = self.run_calc(case_6c.__file__, 'job_eb.ini', exports='csv')
        [fname] = out['agg_curves-rlzs', 'csv']
        self.assertEqualFiles('expected/agg_curves_eb.csv', fname, delta=1E-5)
        [fname] = out['agg_maps-rlzs', 'csv']
        self.assertEqualFiles('expected/agg_maps.csv', fname, delta=1E-5)

        # regenerate loss curves and maps
        out = self.run_calc(
            case_6c.__file__, 'job_eb.ini', exports='csv',
            hazard_calculation_id=str(self.calc.datastore.calc_id))
        [fname] = out['agg_curves-rlzs', 'csv']
        self.assertEqualFiles('expected/agg_curves_eb.csv', fname, delta=1E-5)
        [fname] = out['agg_maps-rlzs', 'csv']
        self.assertEqualFiles('expected/agg_maps.csv', fname, delta=1E-5)
