# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2023 GEM Foundation
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
from unittest import mock, SkipTest
import numpy

from openquake.baselib.general import gettemp
from openquake.baselib.hdf5 import read_csv
from openquake.hazardlib.source.rupture import get_ruptures
from openquake.commonlib import logs, readinput
from openquake.calculators.views import view, text_table
from openquake.calculators.tests import CalculatorTestCase, strip_calc_id
from openquake.calculators.export import export
from openquake.calculators.extract import extract
from openquake.calculators.post_risk import PostRiskCalculator
from openquake.qa_tests_data.event_based_risk import (
    case_1, case_2, case_3, case_4, case_4a, case_5, case_6c, case_master,
    case_miriam, occupants, case_1f, case_1g, case_7a, case_8,
    recompute, reinsurance_1, reinsurance_2, reinsurance_3,
    reinsurance_4, reinsurance_5)

aac = numpy.testing.assert_allclose


def aae(data, expected):
    for data_, expected_ in zip(data, expected):
        for got, exp in zip(data_, expected_):
            if isinstance(got, str):
                numpy.testing.assert_equal(got, exp)
            else:
                numpy.testing.assert_almost_equal(got, numpy.float32(exp))


class EventBasedRiskTestCase(CalculatorTestCase):

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
                        'aggcurves', 'avg_loss')):
                    all_csv.append(fname)
        assert all_csv, 'Could not find any CSV file??'
        for fname in all_csv:
            self.assertEqualFiles(
                'expected/%s' % strip_calc_id(fname), fname)

    def test_case_1(self):
        self.run_calc(case_1.__file__, 'job.ini')

        # checking aggcurves
        fnames = export(('aggcurves', 'csv'), self.calc.datastore)
        for fname in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(fname), fname,
                                  delta=1E-5)

        # test the src_loss_table extractor
        fnames = export(('src_loss_table', 'csv'), self.calc.datastore)
        for fname in fnames:
            self.assertEqualFiles('expected/%s' % strip_calc_id(fname), fname,
                                  delta=1E-5)

    def test_case_1_ins(self):
        # no aggregation
        self.run_calc(case_1.__file__, 'job2.ini')
        [fname] = export(('aggrisk', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/aggrisk.csv', fname, delta=1E-5)

        # this is a case with insured losses and tags
        self.run_calc(case_1.__file__, 'job_ins.ini', concurrent_tasks='4')

        # testing the view agg_id
        agg_id = view('agg_id', self.calc.datastore)
        self.assertEqual(str(agg_id), '''\
       policy taxonomy
agg_id                
0           B       RM
1           B        W
2           B       RC
3           A       RM
4           A        W
5           A       RC''')

        [fname] = export(('avg_losses-stats', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/%s' % strip_calc_id(fname), fname,
                              delta=1E-5)

        aw = extract(self.calc.datastore, 'agg_losses/structural')
        self.assertEqual(aw.stats, ['mean'])
        numpy.testing.assert_allclose(aw.array, [880.4989], atol=.001)

        fnames = export(('aggrisk', 'csv'), self.calc.datastore)
        for fname in fnames:
            self.assertEqualFiles('expected/%s' % strip_calc_id(fname),
                                  fname, delta=1E-5)

        fnames = export(('aggcurves', 'csv'), self.calc.datastore)
        for fname in fnames:
            self.assertEqualFiles('expected/eb_%s' % strip_calc_id(fname),
                                  fname, delta=1E-5)

        [fname] = export(('risk_by_event', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/%s' % strip_calc_id(fname), fname,
                              delta=1E-5)

        # extract agg_curves with tags
        aw = extract(self.calc.datastore, 'agg_curves?kind=stats&'
                     'loss_type=structural&absolute=1&policy=A&taxonomy=RC')
        tmp = gettemp(text_table(aw.to_dframe()))
        self.assertEqualFiles('expected/agg_curves5.csv', tmp)

        aw = extract(self.calc.datastore, 'agg_curves?kind=stats&'
                     'loss_type=structural&absolute=0&policy=A&taxonomy=RC')
        tmp = gettemp(text_table(aw.to_dframe()))
        self.assertEqualFiles('expected/agg_curves7.csv', tmp)

        self.assertEqual(aw.return_period, [30, 60, 120, 240, 480, 960])
        self.assertEqual(aw.kind, ["mean"])
        self.assertEqual(aw.units, ["EUR", "EUR"])
        self.assertEqual(aw.policy, ["A"])
        self.assertEqual(aw.taxonomy, ["RC"])

        # extract individual curves
        aw = extract(self.calc.datastore, 'agg_curves?kind=rlzs&'
                     'loss_type=structural&absolute=0&policy=A&taxonomy=RC')
        tmp = gettemp(text_table(aw.to_dframe()))
        self.assertEqualFiles('expected/agg_curves3.csv', tmp)

        # test ct_independence
        loss4 = view('portfolio_losses', self.calc.datastore)
        self.run_calc(case_1.__file__, 'job_ins.ini', concurrent_tasks='0')
        loss0 = view('portfolio_losses', self.calc.datastore)
        self.assertEqual(loss0, loss4)

    def test_case_1_deductible_gt_ins_limit(self):
        with self.assertRaises(ValueError) as ctx:
            self.run_calc(case_1.__file__, 'job2.ini',
                          insurance_csv="{'structural': 'policy_ins_ko.csv'}")
        self.assertIn(
            "Please check deductible values. Values larger than the insurance"
            " limit were found for asset(s) {'a3'}.",
            str(ctx.exception))

    def test_case_1f(self):
        # vulnerability function with BT
        self.run_calc(case_1f.__file__, 'job_h.ini,job_r.ini')
        fname = gettemp(view('portfolio_losses', self.calc.datastore))
        # sensitive to shapely version
        self.assertEqualFiles('portfolio_losses.txt', fname, delta=2E-4)
        os.remove(fname)

    def test_ct_independence(self):
        # vulnerability function with BT
        self.run_calc(case_1f.__file__, 'job.ini', concurrent_tasks='0')
        loss0 = view('portfolio_losses', self.calc.datastore)
        self.run_calc(case_1f.__file__, 'job.ini', concurrent_tasks='2')
        loss2 = view('portfolio_losses', self.calc.datastore)
        self.assertEqual(loss0, loss2)

    def test_case_1g(self):
        # vulnerability function with PMF
        self.run_calc(case_1g.__file__, 'job_h.ini,job_r.ini')
        [fname] = export(('avg_losses-rlzs', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/avg_losses.csv', fname)
        os.remove(fname)

    def test_case_2(self):
        self.run_calc(case_2.__file__, 'job.ini', concurrent_tasks='0')
        loss0 = view('portfolio_losses', self.calc.datastore)
        # test ct_independence
        self.run_calc(case_2.__file__, 'job.ini', concurrent_tasks='2')
        loss2 = view('portfolio_losses', self.calc.datastore)
        self.assertEqual(loss0, loss2)

        # test the case when all GMFs are filtered out
        with self.assertRaises(RuntimeError) as ctx:
            self.run_calc(case_2.__file__, 'job.ini', minimum_intensity='10.0')
        self.assertEqual(
            str(ctx.exception),
            'No GMFs were generated, perhaps they were all below the '
            'minimum_intensity threshold')

    def test_case_2_sampling(self):
        self.run_calc(case_2.__file__, 'job_sampling.ini')

        # avg_losses
        [fname] = export(('avg_losses-stats', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/%s' % strip_calc_id(fname), fname,
                              delta=1E-5)
        self.assertEqual(len(self.calc.datastore['events']), 22)

        losses0 = self.calc.datastore['avg_losses-stats/structural'][:, 0]
        losses1 = self.calc.datastore['avg_losses-stats/structural'][:, 0]
        avg = (losses0 + losses1).sum() / 2

        # agg_losses
        [fname] = export(('aggrisk', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/%s' % strip_calc_id(fname), fname,
                              delta=1E-5)

        calc_id = str(self.calc.datastore.calc_id)
        self.run_calc(case_2.__file__, 'job_sampling.ini',
                      collect_rlzs='true', hazard_calculation_id=calc_id)
        [fname] = export(('aggcurves', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/%s' % strip_calc_id(fname), fname,
                              delta=1E-5)

        # avg_losses
        [fname] = export(('avg_losses-rlzs', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/%s' % strip_calc_id(fname), fname,
                              delta=1E-5)
        tot = self.calc.datastore['avg_losses-rlzs/structural'][:, 0].sum()
        aac(avg, tot, rtol=1E-6)

        # aggrisk
        [fname] = export(('aggrisk', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/aggrisk_sampling.csv', fname,
                              delta=1E-5)

    def test_case_2_correlation(self):
        self.run_calc(case_2.__file__, 'job_loss.ini', asset_correlation='1')
        [fname] = export(('risk_by_event', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/agg_losses.csv', fname, delta=1E-5)

        # test losses_by_tag with a single realization
        [fname] = export(
            ('aggregate_by/avg_losses?tag=taxonomy&kind=rlz-0', 'csv'),
            self.calc.datastore)
        self.assertEqualFiles('expected/losses_by_tag.csv', fname, delta=1E-5)

        # losses by taxonomy for loss_type=structural
        [fname] = export(
            ('aggregate_by/avg_losses?tag=taxonomy&kind=rlz-0&'
             'loss_type=structural', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/losses_by_taxo.csv', fname, delta=1E-5)

    def test_missing_taxonomy(self):
        with self.assertRaises(RuntimeError) as ctx:
            self.run_calc(case_2.__file__, 'job_err.ini')
        self.assertIn('not in the fragility/vulnerability/consequence model',
                      str(ctx.exception))

    def test_case_3(self):
        # this is a test with statistics
        self.run_calc(case_3.__file__, 'job.ini',
                      exports='csv', concurrent_tasks='4')

        # test postprocessing
        self.calc.datastore.close()
        hc_id = self.calc.datastore.calc_id
        self.run_calc(case_3.__file__, 'job.ini',
                      exports='csv', hazard_calculation_id=str(hc_id))
        [fname] = export(('avg_losses-stats', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/%s' % strip_calc_id(fname), fname,
                              delta=1E-5)
        for fname in export(('aggcurves', 'csv'), self.calc.datastore):
            self.assertEqualFiles('expected/%s' % strip_calc_id(fname), fname,
                                  delta=1E-5)

    def test_case_4(self):
        # Turkey with SHARE logic tree
        self.run_calc(case_4.__file__, 'job.ini')
        [fname] = export(('avg_losses-stats', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/avg_losses-mean.csv', fname)

        fnames = export(('risk_by_event', 'csv'), self.calc.datastore)
        assert fnames, 'No agg_losses exported??'
        for fname in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(fname), fname,
                                  delta=2E-5)

    def test_case_5(self):
        # taxonomy mapping, the numbers are different in Ubuntu 20 vs 18
        self.run_calc(case_5.__file__, 'job.ini')
        fnames = export(('aggcurves', 'csv'), self.calc.datastore)
        for fname in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(fname),
                                  fname, delta=5E-4)

        # check aggrisk-stats
        fnames = export(('aggrisk-stats', 'csv'), self.calc.datastore)
        for fname in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(fname),
                                  fname, delta=5E-4)

        # check aggcurves-stats
        fnames = export(('aggcurves-stats', 'csv'), self.calc.datastore)
        for fname in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(fname),
                                  fname, delta=5E-4)

    def test_occupants(self):
        self.run_calc(occupants.__file__, 'job.ini')
        fnames = export(('aggcurves', 'csv'), self.calc.datastore)
        for fname in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(fname),
                                  fname, delta=1E-4)

    def test_case_master(self):
        # needs a large tolerance: https://github.com/gem/oq-engine/issues/5825
        # it looks like the cholesky decomposition is OS-dependent, so
        # the GMFs are different of macOS/Ubuntu20/Ubuntu18
        self.run_calc(case_master.__file__, 'job.ini', exports='csv')
        fnames = export(('avg_losses-stats', 'csv'), self.calc.datastore)
        assert fnames, 'avg_losses-stats not exported?'
        for fname in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(fname), fname,
                                  delta=1E-4)

        # check event loss table
        [fname] = export(('risk_by_event', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/' + strip_calc_id(fname), fname,
                              delta=1E-4)

        # check total variance
        K = self.calc.datastore['risk_by_event'].attrs.get('K', 0)
        elt_df = self.calc.datastore.read_df(
            'risk_by_event', 'event_id', dict(agg_id=K, loss_id=4))
        elt_df['cov'] = numpy.sqrt(elt_df.variance) / elt_df.loss
        elt_df.sort_index(inplace=True)
        del elt_df['agg_id']
        del elt_df['loss_id']
        del elt_df['variance']
        fname = gettemp(str(elt_df))
        self.assertEqualFiles('expected/stddevs.txt', fname, delta=1E-4)

        fname = gettemp(view('portfolio_losses', self.calc.datastore))
        self.assertEqualFiles(
            'expected/portfolio_losses.txt', fname, delta=1E-4)
        os.remove(fname)

        # check ruptures are stored correctly
        fname = gettemp(view('ruptures_events', self.calc.datastore))
        self.assertEqualFiles('expected/ruptures_events.txt', fname)
        os.remove(fname)

        # check losses_by_tag
        fnames = export(
            ('aggregate_by/avg_losses?tag=occupancy&kind=quantile-0.5', 'csv'),
            self.calc.datastore)
        self.assertEqualFiles('expected/losses_by_occupancy.csv', fnames[0],
                              delta=1E-4)

        self.check_multi_tag(self.calc.datastore)

        # check aggcurves with aggregate_by=id
        fname = export(('aggcurves', 'csv'), self.calc.datastore)[0]
        self.assertEqualFiles('expected/aggcurves.csv', fname, delta=1E-4)

        # test the view gsim_for_event
        gsim = view('gsim_for_event:0', self.calc.datastore)
        self.assertEqual(str(gsim), "[BooreAtkinson2008]")
        gsim = view('gsim_for_event:10', self.calc.datastore)
        self.assertEqual(str(gsim), "[ChiouYoungs2008]")

        # test with correlation
        self.run_calc(case_master.__file__, 'job.ini',
                      hazard_calculation_id=str(self.calc.datastore.calc_id),
                      asset_correlation='1')

        # check aggcurves-stats
        [_, fname] = export(('aggcurves-stats', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/%s' % strip_calc_id(fname),
                              fname, delta=2E-4)

        # check aggrisk-stats
        [_, fname] = export(('aggrisk-stats', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/%s' % strip_calc_id(fname),
                              fname, delta=2E-4)

    def check_multi_tag(self, dstore):
        # multi-tag aggregations
        arr = extract(dstore, 'aggregate/avg_losses?'
                      'tag=taxonomy&tag=occupancy&kind=quantile-0.5')
        self.assertEqual(len(arr.to_dframe()), 0)

        # aggregate by all loss types
        fnames = export(
            ('aggregate_by/avg_losses?tag=taxonomy&tag=occupancy&'
             'kind=quantile-0.5', 'csv'),
            dstore)
        for fname in fnames:
            self.assertEqualFiles('expected/%s' % strip_calc_id(fname), fname,
                                  delta=1E-4)

    def test_case_miriam(self):
        # this is a case with a grid and asset-hazard association
        self.run_calc(case_miriam.__file__, 'job.ini')

        # check minimum_magnitude >= 5.2
        minmag = self.calc.datastore['ruptures']['mag'].min()
        self.assertGreaterEqual(minmag, 5.2)

        fname = gettemp(view('portfolio_losses', self.calc.datastore))
        self.assertEqualFiles(
            'expected/portfolio_losses.txt', fname, delta=1E-5)

        # this is a case with exposure, site model and region_grid_spacing
        self.run_calc(case_miriam.__file__, 'job2.ini', concurrent_tasks=4)
        hcurves = dict(extract(self.calc.datastore, 'hcurves'))['all']
        sitecol = self.calc.datastore['sitecol']  # filtered sitecol
        self.assertEqual(len(hcurves), len(sitecol))
        assetcol = self.calc.datastore['assetcol']
        self.assertEqual(len(sitecol), 12)
        self.assertGreater(sitecol.vs30.sum(), 0)
        self.assertEqual(len(assetcol), 548)

        # ebrisk with amplification
        hc_id = str(self.calc.datastore.calc_id)
        self.run_calc(case_miriam.__file__, 'job3.ini',
                      hazard_calculation_id=hc_id)
        fname = gettemp(view('portfolio_losses', self.calc.datastore))
        self.assertEqualFiles(
            'expected/portfolio_losses_ampl.txt', fname, delta=1E-5)

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

    # NB: big difference between Ubuntu 18 and 20
    def test_case_4a(self):
        # the case of a site_model.xml with 7 sites but only 1 asset
        out = self.run_calc(case_4a.__file__, 'job_hazard.ini',
                            exports='csv')
        [fname, _sigeps, _sitefile] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/gmf-data.csv', fname, delta=5E-5)

    def test_case_4b(self):
        # case with site collection extracted from site_model.xml
        self.run_calc(case_4a.__file__, 'job.ini')
        self.assertEqual(len(self.calc.datastore['events']), 3)

    def test_case_6c(self):
        # case with asset_correlation=1
        self.run_calc(case_6c.__file__, 'job_h.ini')
        hc = str(self.calc.datastore.calc_id)
        out = self.run_calc(case_6c.__file__, 'job_r.ini', exports='csv',
                            hazard_calculation_id=hc)

        # very sensitive to shapely version
        [fname] = out['avg_losses-rlzs', 'csv']
        self.assertEqualFiles('expected/avg_losses.csv', fname, delta=3E-4)
        [fname] = out['aggcurves', 'csv']
        self.assertEqualFiles('expected/aggcurves.csv', fname, delta=2E-3)

        # check total stddev
        elt_df = self.calc.datastore.read_df(
            'risk_by_event', 'event_id', dict(agg_id=0))
        elt_df['cov'] = numpy.sqrt(elt_df.variance) / elt_df.loss
        elt_df.sort_index(inplace=True)
        del elt_df['agg_id']
        del elt_df['loss_id']
        del elt_df['variance']
        fname = gettemp(str(elt_df))
        self.assertEqualFiles('expected/stddevs.txt', fname, delta=2E-3)

    def test_case_7a(self):
        # case with preimported exposure
        self.run_calc(case_7a.__file__,  'job_h.ini')
        self.run_calc(case_7a.__file__,  'job_r.ini',
                      hazard_calculation_id=str(self.calc.datastore.calc_id))
        [fname] = export(('risk_by_event', 'csv'), self.calc.datastore)

        # sensitive to shapely version
        self.assertEqualFiles('expected/agg_losses.csv', fname, delta=2E-3)
        rup_ids = set(read_csv(fname, {None: '<S50'})['rup_id'])

        [fname] = export(('aggcurves', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/aggcurves.csv', fname, delta=2E-3)

        # check that the IDs in risk_by_event.csv exist in ruptures.csv
        # this is using extract/rupture_info internally
        [fname] = export(('ruptures', 'csv'), self.calc.datastore)
        rupids = set(read_csv(fname, {None: '<S50'})['rup_id'])
        self.assertTrue(rup_ids <= rupids, 'There are non-existing rupture IDs'
                        ' in the event loss table!')

        # check that the exported ruptures can be re-imported
        text = extract(self.calc.datastore, 'ruptures').array
        rups = get_ruptures(gettemp(text))
        aac(rups['n_occ'], [1, 1, 1, 1])

    def test_case_8(self):
        # nontrivial taxonomy mapping
        out = self.run_calc(case_8.__file__,  'job.ini', exports='csv',
                            concurrent_tasks='0')
        for fname in out['aggrisk', 'csv']:
            self.assertEqualFiles('expected/' + strip_calc_id(fname), fname)

        # NB: there was a taskno-dependency here, so make sure there are
        # no regressions
        out = self.run_calc(case_8.__file__,  'job.ini', exports='csv',
                            concurrent_tasks='4')
        for fname in out['aggrisk', 'csv']:
            self.assertEqualFiles('expected/' + strip_calc_id(fname), fname)

    # NB: big difference between Ubuntu 18 and 20
    def test_asset_loss_table(self):
        # this is a case with L=1, R=1, T1=2, P=6
        out = self.run_calc(case_6c.__file__, 'job_eb.ini', exports='csv',
                            minimum_asset_loss='100')
        _tot, fname = out['aggcurves', 'csv']
        # very sensitive to shapely version
        self.assertEqualFiles('expected/aggcurves_eb.csv', fname, delta=2E-3)

        curves = self.calc.datastore.read_df('aggcurves')
        self.assertEqual(len(curves), 18)  # (2 tags + 1 total) x 6 periods

        # regenerate loss curves
        out = self.run_calc(
            case_6c.__file__, 'job_eb.ini', exports='csv',
            hazard_calculation_id=str(self.calc.datastore.calc_id))
        _tot, fname = out['aggcurves', 'csv']
        self.assertEqualFiles('expected/aggcurves_eb.csv', fname, delta=2E-3)

    def test_recompute(self):
        # test recomputing aggregate loss curves with post_risk
        # this is starting from a ruptures.csv file
        out = self.run_calc(recompute.__file__, 'job.ini', exports='csv')
        [_total, fname] = out['aggrisk', 'csv']
        self.assertEqualFiles('expected/agg_losses.csv', fname, delta=1E-5)
        [_total, fname] = out['aggcurves', 'csv']
        self.assertEqualFiles('expected/aggcurves.csv', fname, delta=1E-5)

        parent = self.calc.datastore
        # the parent has aggregate_by = NAME_1, NAME_2, taxonomy
        oq = parent['oqparam']
        oq.__dict__['aggregate_by'] = [['NAME_1']]
        log = logs.init('job', {'calculation_mode': 'post_risk',
                                'description': 'test recompute'})
        prc = PostRiskCalculator(oq, log.calc_id)
        prc.assetcol = self.calc.assetcol
        oq.hazard_calculation_id = parent.calc_id
        with mock.patch.dict(os.environ, {'OQ_DISTRIBUTE': 'no'}), log:
            prc.run()
        [_total, fname] = export(('aggrisk', 'csv'), prc.datastore)
        self.assertEqualFiles('expected/recomputed_losses.csv', fname,
                              delta=1E-5)

    def test_scenario_from_ruptures(self):
        # same files as in test_recompute, but performing a scenario
        self.run_calc(recompute.__file__, 'job_scenario.ini')


class ReinsuranceTestCase(CalculatorTestCase):

    def test_no_reinsurance(self):
        rf = "{'structural+nonstructural': 'no_reinsurance.xml'}"
        self.run_calc(reinsurance_1.__file__, 'job.ini', reinsurance_file=rf)
        [fname] = export(('reinsurance-risk_by_event', 'csv'),
                         self.calc.datastore)
        self.assertEqualFiles('expected/no_reinsurance-risk_by_event.csv',
                              fname, delta=1E-5)

    def test_prop(self):
        rf = "{'structural+nonstructural': 'reinsurance_prop.xml'}"
        self.run_calc(reinsurance_1.__file__, 'job.ini', reinsurance_file=rf)
        [fname] = export(('reinsurance-risk_by_event', 'csv'),
                         self.calc.datastore)
        self.assertEqualFiles('expected/reinsurance-risk_by_event_prop.csv',
                              fname, delta=1E-5)
        [fname] = export(('reinsurance-aggcurves', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/reinsurance-aggcurves_prop.csv', fname,
                              delta=1E-5)

    def test_nonprop(self):
        rf = "{'structural+nonstructural': 'reinsurance_np.xml'}"
        self.run_calc(reinsurance_1.__file__, 'job.ini', reinsurance_file=rf)
        [fname] = export(('reinsurance-risk_by_event', 'csv'),
                         self.calc.datastore)
        self.assertEqualFiles('expected/reinsurance-risk_by_event_np.csv',
                              fname, delta=1E-5)
        [fname] = export(('reinsurance-aggcurves', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/reinsurance-aggcurves_np.csv', fname,
                              delta=1E-5)

    def test_prop_nonprop(self):
        self.run_calc(reinsurance_1.__file__, 'job.ini')
        [fname] = export(('reinsurance-risk_by_event', 'csv'),
                         self.calc.datastore)
        self.assertEqualFiles('expected/reinsurance-risk_by_event.csv',
                              fname, delta=1E-5)
        [fname] = export(('reinsurance-aggcurves', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/reinsurance-aggcurves.csv', fname,
                              delta=1E-5)
        [fname] = export(('reinsurance-avg_portfolio', 'csv'),
                         self.calc.datastore)
        self.assertEqualFiles('expected/reinsurance-avg_portfolio.csv',
                              fname, delta=1E-5)

    def test_overspill_with_xlwr(self):
        self.run_calc(reinsurance_3.__file__, 'job.ini')
        [fname] = export(('reinsurance-risk_by_event', 'csv'),
                         self.calc.datastore)
        self.assertEqualFiles('expected/reinsurance-risk_by_event.csv',
                              fname, delta=5E-5)

    def test_many_levels(self):
        self.run_calc(reinsurance_1.__file__, 'job2.ini')
        [fname] = export(('reinsurance-risk_by_event', 'csv'),
                         self.calc.datastore)
        self.assertEqualFiles('expected/reinsurance-risk_by_event2.csv',
                              fname, delta=1E-5)
        [fname] = export(('reinsurance-aggcurves', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/reinsurance-aggcurves2.csv', fname,
                              delta=1E-5)
        [fname] = export(('reinsurance-avg_portfolio', 'csv'),
                         self.calc.datastore)
        self.assertEqualFiles('expected/reinsurance-avg_portfolio2.csv',
                              fname, delta=1E-5)
        [fname] = export(('reinsurance-avg_policy', 'csv'),
                         self.calc.datastore)
        self.assertEqualFiles('expected/reinsurance-avg_policy.csv',
                              fname, delta=1E-5)

    def test_post_risk(self):
        # calculation from a source model producing 4 events
        self.run_calc(reinsurance_2.__file__, 'job.ini')

        # make sure oq zip finds all the relevant files
        files = readinput.get_input_files(self.calc.oqparam)
        self.assertEqual([os.path.basename(f) for f in files],
                         ['contents_vulnerability_model.xml',
                          'exposure_model.csv',
                          'exposure_model.xml',
                          'gsim_logic_tree.xml',
                          'job.ini',
                          'nonstructural_vulnerability_model.xml',
                          'policy.csv',
                          'reinsurance2.xml',
                          'source_model.xml',
                          'source_model_logic_tree.xml',
                          'structural_vulnerability_model.xml'])

        # make sure reaggreate works
        self.run_calc(reinsurance_2.__file__, 'job.ini',
                      calculation_mode='post_risk',
                      hazard_calculation_id=str(self.calc.datastore.calc_id))

        [fname] = export(('reinsurance-aggcurves', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/reinsurance-aggcurves.csv', fname,
                              delta=4E-4)
        [fname] = export(('reinsurance-avg_portfolio', 'csv'),
                         self.calc.datastore)
        self.assertEqualFiles('expected/reinsurance-avg_portfolio.csv',
                              fname, delta=4E-5)

    def test_ideductible(self):
        if sys.platform == 'darwin':
            raise SkipTest('Numbers different as 0.16% on macos')

        self.run_calc(reinsurance_4.__file__, 'job.ini')
        f1, f2 = export(('aggrisk', 'csv'), self.calc.datastore)
        # abs difference of 1E-4 on macos (57.0276 => 57.0277)
        self.assertEqualFiles('expected/aggrisk.csv', f1, delta=2E-4)
        self.assertEqualFiles('expected/aggrisk-policy.csv', f2, delta=2E-4)

        f1, f2 = export(('aggcurves', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/aggcurves.csv', f1, delta=2E-4)
        self.assertEqualFiles('expected/aggcurves-policy.csv', f2, delta=2E-4)

        [fname] = export(('reinsurance-aggcurves', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/reinsurance-aggcurves.csv',
                              fname, delta=2E-4)
        [fname] = export(('reinsurance-avg_portfolio', 'csv'),
                         self.calc.datastore)
        self.assertEqualFiles('expected/reinsurance-avg_portfolio.csv',
                              fname, delta=2E-4)

    def test_ideductible_exposure(self):
        if sys.platform == 'darwin':
            raise SkipTest('Numbers different as 0.16% on macos')

        # this is a test with pure insurance
        self.run_calc(reinsurance_5.__file__, 'job_1.ini')  # 2 policies
        [fname] = export(('reinsurance-aggcurves', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/reinsurance-aggcurves.csv',
                              fname, delta=.002)  # big diffs on macos, 0.16%

        # check moving the ideductible in the exposure produce the same
        # aggcurve
        self.run_calc(reinsurance_5.__file__, 'job_2.ini')  # 1 policy
        [fname] = export(('reinsurance-aggcurves', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/reinsurance-aggcurves.csv',
                              fname, delta=.002)  # big diffs on macos, 0.16%
