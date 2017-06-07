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
import os
import sys
import mock
import unittest
import numpy
import h5py
from nose.plugins.attrib import attr

from openquake.baselib.general import writetmp
from openquake.baselib.parallel import Sequential
from openquake.calculators.views import view
from openquake.calculators.tests import (
    CalculatorTestCase, strip_calc_id, REFERENCE_OS)
from openquake.calculators.export import export
from openquake.qa_tests_data.event_based_risk import (
    case_1, case_2, case_3, case_4, case_4a, case_master, case_miriam,
    occupants, case_1g, case_7a)


# used for a sanity check
def check_total_losses(calc):
    dstore = calc.datastore
    loss_dt = calc.oqparam.loss_dt()
    L1 = len(loss_dt.names)
    L = L1 // 2
    data1 = numpy.zeros(L1, numpy.float32)
    for dset in dstore['agg_loss_table'].values():
        for l, lt in enumerate(loss_dt.names):
            i = int(lt.endswith('_ins'))  # the cast avoids a numpy warning
            data1[l] += dset['loss'][:, l - L * i, i].sum()

    # check the sums are consistent with the ones coming from losses_by_taxon
    data2 = numpy.zeros(L1, numpy.float32)
    lbt = dstore['losses_by_taxon-rlzs']
    for l in range(L1):
        data2[l] += lbt[:, :, l].sum()
    numpy.testing.assert_allclose(data1, data2, 1E-6)

    # test the asset_loss_table exporter; notice that I need to disable
    # the parallelism to avoid reading bogus data: this is the usual
    # heisenbug when reading in parallel an .hdf5 generated in process
    with mock.patch('openquake.baselib.parallel.Starmap', Sequential):
        [fname] = export(('asset_loss_table', 'hdf5'), dstore)
    print('Generating %s' % fname)
    with h5py.File(fname) as f:
        total = f['asset_loss_table'].attrs['total']

    # check the sums are consistent with the ones coming from asset_loss_table
    numpy.testing.assert_allclose(data1, total, 1E-6)


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
                        'loss_curve', 'loss_map', 'agg_loss', 'avg_loss')):
                    all_csv.append(fname)
        assert all_csv, 'Could not find any CSV file??'
        for fname in all_csv:
            self.assertEqualFiles(
                'expected/%s' % strip_calc_id(fname), fname)

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_1(self):
        self.run_calc(case_1.__file__, 'job.ini')
        ekeys = [('agg_curve-stats', 'csv')]
        for ekey in ekeys:
            for fname in export(ekey, self.calc.datastore):
                self.assertEqualFiles(
                    'expected/%s' % strip_calc_id(fname), fname)

        # test the loss curves exporter
        [f1] = export(('loss_curves/rlz-0', 'csv'), self.calc.datastore)
        [f2] = export(('loss_curves/rlz-1', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/loss_curves-rlz-000.csv', f1)
        self.assertEqualFiles('expected/loss_curves-rlz-001.csv', f2)

        # test the loss maps exporter
        fnames = export(('loss_maps-stats', 'csv'), self.calc.datastore)
        assert fnames
        if REFERENCE_OS:
            for fname in fnames:
                self.assertEqualFiles('expected/' + strip_calc_id(fname),
                                      fname, delta=1E-5)

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_1g(self):
        # vulnerability function with PMF
        self.run_calc(case_1g.__file__, 'job.ini')
        fname = writetmp(view('mean_avg_losses', self.calc.datastore))
        self.assertEqualFiles('expected/avg_losses.txt', fname)
        os.remove(fname)

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_2(self):
        self.run_calc(case_2.__file__, 'job.ini')
        fname = writetmp(view('mean_avg_losses', self.calc.datastore))
        self.assertEqualFiles('expected/mean_avg_losses.txt', fname)
        os.remove(fname)

        # test the composite_risk_model keys (i.e. slash escaping)
        crm = sorted(self.calc.datastore.getitem('composite_risk_model'))
        self.assertEqual(crm, ['RC%2B', 'RM', 'W%2F1'])

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
        self.assertEqualFiles('expected/agg_losses.csv', fname)

        check_total_losses(self.calc)

    @attr('qa', 'risk', 'event_based_risk')
    def test_missing_taxonomy(self):
        with self.assertRaises(RuntimeError) as ctx:
            self.run_calc(case_2.__file__, 'job_err.ini')
        self.assertIn('not in the risk model', str(ctx.exception))

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_3(self):
        # this is a test with statistics and without conditional_loss_poes
        self.run_calc(case_3.__file__, 'job.ini',
                      exports='csv', concurrent_tasks='4')

        # test the number of bytes saved in the rupture records
        grp00 = self.calc.datastore.get_attr('ruptures/grp-00', 'nbytes')
        grp02 = self.calc.datastore.get_attr('ruptures/grp-02', 'nbytes')
        grp03 = self.calc.datastore.get_attr('ruptures/grp-03', 'nbytes')
        self.assertEqual(grp00, 545)
        self.assertEqual(grp02, 545)
        self.assertEqual(grp03, 218)

        hc_id = self.calc.datastore.calc_id
        self.run_calc(case_3.__file__, 'job.ini',
                      exports='csv', hazard_calculation_id=str(hc_id))
        [fname] = export(('agg_curve-stats', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/%s' % strip_calc_id(fname), fname)

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_4(self):
        # Turkey with SHARE logic tree
        out = self.run_calc(case_4.__file__, 'job.ini', exports='csv')
        [fname] = export(('avg_losses-stats', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/avg_losses-mean.csv', fname)

        fnames = out['agg_loss_table', 'csv']
        assert fnames, 'No agg_losses exported??'
        for fname in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(fname), fname)

    @attr('qa', 'risk', 'event_based_risk')
    def test_occupants(self):
        self.run_calc(occupants.__file__, 'job.ini')
        fnames = export(('agg_curve-rlzs', 'csv'), self.calc.datastore)
        for fname in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(fname),
                                  fname, delta=1E-5)

        fnames = export(('loss_maps-rlzs', 'csv'), self.calc.datastore)
        assert fnames, 'loss_maps-rlzs not exported?'
        if REFERENCE_OS:
            for fname in fnames:
                self.assertEqualFiles('expected/' + strip_calc_id(fname),
                                      fname, delta=1E-5)

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_master(self):
        if sys.platform == 'darwin':
            raise unittest.SkipTest('MacOSX')
        self.run_calc(case_master.__file__, 'job.ini', exports='csv')
        fnames = export(('avg_losses-stats', 'csv'), self.calc.datastore)
        assert fnames, 'avg_losses-stats not exported?'
        for fname in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(fname), fname,
                                  delta=1E-5)

        fnames = export(('loss_maps-rlzs', 'csv'), self.calc.datastore)
        assert fnames, 'loss_maps-rlzs not exported?'
        if REFERENCE_OS:
            for fname in fnames:
                self.assertEqualFiles('expected/' + strip_calc_id(fname),
                                      fname, delta=1E-5)

        fnames = export(('losses_by_taxon-stats', 'csv'), self.calc.datastore)
        assert fnames, 'losses_by_taxon-stats not exported?'
        for fname in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(fname), fname)

        fname = writetmp(view('portfolio_loss', self.calc.datastore))
        self.assertEqualFiles('expected/portfolio_loss.txt', fname, delta=1E-5)
        os.remove(fname)

        # check ruptures are stored correctly
        fname = writetmp(view('ruptures_events', self.calc.datastore))
        self.assertEqualFiles('expected/ruptures_events.txt', fname)
        os.remove(fname)

        # check job_info is stored
        job_info = dict(self.calc.datastore['job_info'])
        self.assertIn(b'build_loss_maps.sent', job_info)
        self.assertIn(b'build_loss_maps.received', job_info)

        check_total_losses(self.calc)

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_miriam(self):
        # this is a case with a grid and asset-hazard association
        out = self.run_calc(case_miriam.__file__, 'job.ini', exports='csv')
        [fname] = out['agg_loss_table', 'csv']
        self.assertEqualFiles('expected/agg_losses-rlz000-structural.csv',
                              fname, delta=1E-5)
        fname = writetmp(view('portfolio_loss', self.calc.datastore))
        self.assertEqualFiles(
            'expected/portfolio_loss.txt', fname, delta=1E-5)
        os.remove(fname)

    @attr('qa', 'risk', 'case_7a')
    def test_case_7a(self):
        # case with  <insuranceLimit isAbsolute="false"/>
        self.run_calc(case_7a.__file__,  'job_h.ini')
        self.run_calc(case_7a.__file__,  'job_r.ini',
                      hazard_calculation_id=str(self.calc.datastore.calc_id))
        [fname] = export(('agg_loss_table', 'csv'), self.calc.datastore)
        if REFERENCE_OS:
            self.assertEqualFiles('expected/agg_losses.csv', fname, delta=1E-5)

    @attr('qa', 'hazard', 'event_based')
    def test_case_4_hazard(self):
        # Turkey with SHARE logic tree; TODO: add site model
        # it has 8 realizations but 4 of them have 0 ruptures
        out = self.run_calc(case_4.__file__, 'job.ini',
                            calculation_mode='event_based',
                            ground_motion_fields='false', exports='csv')
        [fname] = [f for f in out['hcurves', 'csv'] if 'mean' in f]
        self.assertEqualFiles('expected/hazard_curve-mean.csv', fname)
        [fname] = [f for f in out['hmaps', 'csv'] if 'mean' in f]
        self.assertEqualFiles('expected/hazard_map-mean.csv', fname)

        fnames = export(('hmaps', 'xml'), self.calc.datastore)
        self.assertEqual(len(fnames), 36)  # 2 IMT x 2 poes + 32 files

    @attr('qa', 'hazard', 'event_based')
    def test_case_4a(self):
        # the case of a site_model.xml with 7 sites but only 1 asset
        out = self.run_calc(case_4a.__file__, 'job_hazard.ini',
                            exports='csv')
        [fname] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/gmf-data.csv', fname)
