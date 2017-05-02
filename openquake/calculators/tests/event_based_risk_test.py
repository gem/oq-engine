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
import re
import sys
import unittest
import subprocess
import numpy
from nose.plugins.attrib import attr

from openquake.baselib.general import writetmp
from openquake.calculators.views import view
from openquake.calculators.tests import (
    CalculatorTestCase, strip_calc_id, REFERENCE_OS)
from openquake.calculators.export import export
from openquake.qa_tests_data.event_based_risk import (
    case_1, case_2, case_3, case_4, case_4a, case_master, case_miriam,
    occupants, case_1g)


# used for a sanity check
def check_agg_loss_table(dstore, loss_dt):
    L1 = len(loss_dt.names)
    L = L1 // 2
    data1 = numpy.zeros(L1, numpy.float32)
    for dset in dstore['agg_loss_table'].values():
        for l, lt in enumerate(loss_dt.names):
            i = lt.endswith('_ins')
            data1[l] += dset['loss'][:, l - L * i, i].sum()

    # check the sums are consistent with the ones coming from losses_by_taxon
    data2 = numpy.zeros(L1, numpy.float32)
    lbt = dstore['losses_by_taxon-rlzs']
    for l in range(L1):
        data2[l] += lbt[:, :, l].sum()
    numpy.testing.assert_allclose(data1, data2, 1E-6)


def run_precalc(pkgfile, job_ini):
    """
    Returns the parent calculation ID as a string
    """
    job_ini = os.path.join(os.path.dirname(pkgfile), job_ini)
    out = subprocess.check_output(
        [sys.executable, '-m', 'openquake.commands', 'run', job_ini])
    return re.search('calc_(\d+)\.hdf5', out).group(1)


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
        parent_id = run_precalc(case_1.__file__, 'job.ini')
        self.run_calc(case_1.__file__, 'job.ini',
                      exports='csv', individual_curves='false',
                      hazard_calculation_id=parent_id)
        ekeys = [('agg_curve-stats', 'xml')]
        for ekey in ekeys:
            for fname in export(ekey, self.calc.datastore):
                self.assertEqualFiles(
                    'expected/%s' % strip_calc_id(fname), fname)

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
        self.assert_stats_ok(case_2, 'job.ini', individual_curves='true')
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

        # test the number of bytes saved in the rupture records
        grp00 = self.calc.datastore.get_attr('ruptures/grp-00', 'nbytes')
        grp02 = self.calc.datastore.get_attr('ruptures/grp-02', 'nbytes')
        grp03 = self.calc.datastore.get_attr('ruptures/grp-03', 'nbytes')
        self.assertEqual(grp00, 545)
        self.assertEqual(grp02, 545)
        self.assertEqual(grp03, 218)

        hc_id = self.calc.datastore.calc_id
        self.run_calc(case_3.__file__, 'job.ini',
                      exports='xml', individual_curves='false',
                      hazard_calculation_id=str(hc_id))
        [fname] = export(('agg_curve-stats', 'xml'), self.calc.datastore)
        self.assertEqualFiles('expected/%s' % strip_calc_id(fname), fname)

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_4(self):
        # Turkey with SHARE logic tree
        out = self.run_calc(case_4.__file__, 'job.ini',
                            exports='csv', individual_curves='true')
        [fname] = export(('avg_losses-stats', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/avg_losses-mean.csv', fname)

        fnames = out['agg_loss_table', 'csv']
        assert fnames, 'No agg_losses exported??'
        for fname in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(fname), fname)

    @attr('qa', 'risk', 'event_based_risk')
    def test_occupants(self):
        parent_id = run_precalc(occupants.__file__, 'job.ini')
        self.run_calc(occupants.__file__, 'job.ini',
                      hazard_calculation_id=parent_id)
        fnames = export(('loss_maps-rlzs', 'xml'), self.calc.datastore) + \
                 export(('agg_curve-rlzs', 'xml'), self.calc.datastore)
        self.assertEqual(len(fnames), 3)  # 2 loss_maps + 1 agg_curve
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
        self.run_calc(case_master.__file__, 'job.ini',
                      exports='csv', individual_curves='false')
        fnames = export(('avg_losses-stats', 'csv'), self.calc.datastore)
        assert fnames, 'avg_losses-stats not exported?'
        for fname in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(fname), fname,
                                  delta=1E-5)

        fnames = export(('losses_by_taxon-stats', 'csv'), self.calc.datastore)
        assert fnames, 'losses_by_taxon-stats not exported?'
        for fname in fnames:
            self.assertEqualFiles('expected/' + strip_calc_id(fname), fname)

        check_agg_loss_table(self.calc.datastore, self.calc.oqparam.loss_dt())

        fname = writetmp(view('portfolio_loss', self.calc.datastore))
        self.assertEqualFiles('expected/portfolio_loss.txt', fname, delta=1E-5)
        os.remove(fname)

        # check ruptures are stored correctly
        fname = writetmp(view('ruptures_events', self.calc.datastore))
        self.assertEqualFiles('expected/ruptures_events.txt', fname)
        os.remove(fname)

        hc_id = self.calc.datastore.calc_id
        self.run_calc(case_master.__file__, 'job.ini',
                      exports='csv', hazard_calculation_id=str(hc_id))
        fnames = export(('loss_maps-rlzs', 'csv'), self.calc.datastore)
        assert fnames, 'loss_maps-rlzs not exported?'
        if REFERENCE_OS:
            for fname in fnames:
                self.assertEqualFiles('expected/' + strip_calc_id(fname),
                                      fname, delta=1E-5)

        # check job_info is stored
        job_info = dict(self.calc.datastore['job_info'])
        self.assertIn(b'build_loss_maps.sent', job_info)
        self.assertIn(b'build_loss_maps.received', job_info)

    @attr('qa', 'risk', 'event_based_risk')
    def test_case_miriam(self):
        # this is a case with a grid and asset-hazard association
        out = self.run_calc(case_miriam.__file__, 'job.ini', exports='csv')

        [fname] = out['agg_loss_table', 'csv']
        self.assertEqualFiles('expected/agg_losses-rlz000-structural.csv',
                              fname)
        fname = writetmp(view('portfolio_loss', self.calc.datastore))
        self.assertEqualFiles(
            'expected/portfolio_loss.txt', fname, delta=1E-5)
        os.remove(fname)

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
