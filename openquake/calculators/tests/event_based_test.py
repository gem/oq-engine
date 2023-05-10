# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2023 GEM Foundation
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

import io
import os
import re
import math
import pandas

import numpy.testing

from openquake.baselib.hdf5 import read_csv
from openquake.baselib.general import countby, gettemp
from openquake.hazardlib import InvalidFile
from openquake.commonlib.datastore import read
from openquake.baselib.writers import write_csv
from openquake.commonlib.util import max_rel_diff_index
from openquake.commonlib.calc import gmvs_to_poes
from openquake.calculators.views import view
from openquake.calculators.export import export
from openquake.calculators.extract import extract
from openquake.calculators.event_based import get_mean_curve, compute_avg_gmf
from openquake.calculators.tests import CalculatorTestCase
from openquake.qa_tests_data.classical import case_18 as gmpe_tables
from openquake.qa_tests_data.event_based import (
    blocksize, case_1, case_2, case_3, case_4, case_5, case_6, case_7,
    case_8, case_9, case_10, case_12, case_13, case_14, case_15, case_16,
    case_17,  case_18, case_19, case_20, case_21, case_22, case_23, case_24,
    case_25, case_26, case_27, case_28, mutex)
from openquake.qa_tests_data.event_based.spatial_correlation import (
    case_1 as sc1, case_2 as sc2, case_3 as sc3)

aac = numpy.testing.assert_allclose


def strip_calc_id(fname):
    name = os.path.basename(fname)
    return re.sub(r'_\d+\.', '.', name)


def joint_prob_of_occurrence(gmvs_site_1, gmvs_site_2, gmv, time_span,
                             num_ses, delta_gmv=0.1):
    """
    Compute the Poissonian probability of a ground shaking value to be in the
    range [``gmv`` - ``delta_gmv`` / 2, ``gmv`` + ``delta_gmv`` / 2] at two
    different locations within a given ``time_span``.

    :param gmvs_site_1, gmvs_site_2:
        Lists of ground motion values (as floats) for two different sites.
    :param gmv:
        Reference value for computing joint probability.
    :param time_span:
        `investigation_time` parameter from the calculation which produced
        these ground motion values.
    :param num_ses:
        `ses_per_logic_tree_path` parameter from the calculation which produced
        these ground motion values. In other words, the total number of
        stochastic event sets.
    :param delta_gmv:
        the interval to consider
    """
    assert len(gmvs_site_1) == len(gmvs_site_2)
    half_delta = float(delta_gmv) / 2

    def gmv_close(v):
        return (gmv - half_delta <= v <= gmv + half_delta)
    count = 0
    for gmv_site_1, gmv_site_2 in zip(gmvs_site_1, gmvs_site_2):
        if gmv_close(gmv_site_1) and gmv_close(gmv_site_2):
            count += 1

    prob = 1 - math.exp(- (float(count) / num_ses))
    return prob


class EventBasedTestCase(CalculatorTestCase):

    def check_avg_gmf(self):
        # checking avg_gmf with a single site
        min_iml = self.calc.oqparam.min_iml
        df = self.calc.datastore.read_df('gmf_data', 'sid')
        weights = self.calc.datastore['weights'][:]
        rlzs = self.calc.datastore['events']['rlz_id']
        [(sid, avgstd)] = compute_avg_gmf(df, weights[rlzs], min_iml).items()
        avg_gmf = self.calc.datastore['avg_gmf'][:]  # 2, N, M
        aac(avg_gmf[:, 0], avgstd)

    def test_compute_avg_gmf(self):
        numpy.random.seed(42)
        E = 1000
        eids = numpy.arange(E)
        min_iml = numpy.array([.05])
        gmvs = numpy.random.lognormal(mean=-2.0, sigma=.5, size=E)
        ok = gmvs >= min_iml
        self.assertEqual(ok.sum(), 983)
        gmf_df = pandas.DataFrame(dict(eid=eids[ok], gmv_0=gmvs[ok]),
                                  numpy.zeros(E, int)[ok])
        weights = numpy.ones(E)
        [(sid, avgstd)] = compute_avg_gmf(gmf_df, weights, min_iml).items()
        # aac(avgstd, [[0.13664978], [1.63127694]]) without cutting min_iml
        # aac(avgstd, [[0.14734], [1.475266]], atol=1E-6)  # cutting at .10
        aac(avgstd, [[0.137023], [1.620616]], atol=1E-6)

    def test_spatial_correlation(self):
        expected = {sc1: [0.99, 0.41],
                    sc2: [0.99, 0.64],
                    sc3: [0.99, 0.22]}

        for case in expected:
            self.run_calc(case.__file__, 'job.ini')
            oq = self.calc.oqparam
            self.assertEqual(list(oq.imtls), ['PGA'])
            dstore = read(self.calc.datastore.calc_id)
            gmf = dstore.read_df('gmf_data', 'sid')
            gmvs_site_0 = gmf.loc[0]['gmv_0']
            gmvs_site_1 = gmf.loc[1]['gmv_0']
            joint_prob_0_5 = joint_prob_of_occurrence(
                gmvs_site_0, gmvs_site_1, 0.5, oq.investigation_time,
                oq.ses_per_logic_tree_path)
            joint_prob_1_0 = joint_prob_of_occurrence(
                gmvs_site_0, gmvs_site_1, 1.0, oq.investigation_time,
                oq.ses_per_logic_tree_path)

            p05, p10 = expected[case]
            aac(joint_prob_0_5, p05, atol=.1)
            aac(joint_prob_1_0, p10, atol=.1)

    def test_blocksize(self):
        out = self.run_calc(blocksize.__file__, 'job.ini',
                            concurrent_tasks='3', exports='csv')
        [fname, _, sitefile] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/gmf-data.csv', fname)
        self.assertEqualFiles('expected/sites.csv', sitefile)

        out = self.run_calc(blocksize.__file__, 'job.ini',
                            concurrent_tasks='4', exports='csv')
        [fname, sig_eps, _] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/gmf-data.csv', fname)
        self.assertEqualFiles('expected/sig-eps.csv', sig_eps)

    def test_case_1(self):
        out = self.run_calc(case_1.__file__, 'job.ini', exports='csv,xml')

        etime = self.calc.datastore.get_attr('gmf_data', 'effective_time')
        self.assertEqual(etime, 80000.)  # ses_per_logic_tree_path = 80000
        imts = self.calc.datastore.get_attr('gmf_data', 'imts')
        self.assertEqual(imts, 'PGA')
        self.check_avg_gmf()

        # make sure ses_id >= 65536 is valid
        high_ses = (self.calc.datastore['events']['ses_id'] >= 65536).sum()
        self.assertGreater(high_ses, 1000)

        [fname] = export(('hcurves', 'csv'), self.calc.datastore)
        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1.csv', fname)

        export(('hcurves', 'xml'), self.calc.datastore)  # check it works

        [fname] = out['hcurves', 'xml']
        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1-PGA.xml', fname)

        # compute hcurves in postprocessing and compare with inprocessing
        # take advantage of the fact that there is a single site
        df = self.calc.datastore.read_df('gmf_data', 'sid')
        oq = self.calc.datastore['oqparam']
        poes = gmvs_to_poes(df, oq.imtls, oq.ses_per_logic_tree_path)
        hcurve = self.calc.datastore['hcurves-stats'][0, 0]  # shape (M, L)
        aac(poes, hcurve)

        # test gsim_by_imt
        out = self.run_calc(case_1.__file__, 'job.ini',
                            ses_per_logic_tree_path='30',
                            gsim_logic_tree_file='gsim_by_imt_logic_tree.xml',
                            exports='csv')

        # testing event_info
        einfo = dict(extract(self.calc.datastore, 'event_info/0'))
        self.assertEqual(einfo['trt'], 'active shallow crust')
        self.assertEqual(einfo['rupture_class'],
                         'ParametricProbabilisticRupture')
        self.assertEqual(einfo['surface_class'], 'PlanarSurface')
        self.assertEqual(einfo['seed'], 1483155045)
        self.assertEqual(str(einfo['gsim']),
                         '[MultiGMPE."PGA".AkkarBommer2010]\n'
                         '[MultiGMPE."SA(0.1)".SadighEtAl1997]')
        self.assertEqual(einfo['rlzi'], 0)
        self.assertEqual(einfo['trt_smr'], 0)
        aac(einfo['occurrence_rate'], 0.6)
        aac(einfo['hypo'], [0., 0., 4.])

        [fname, _, _] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/gsim_by_imt.csv', fname)

    def test_case_1_ruptures(self):
        self.run_calc(case_1.__file__, 'job_ruptures.ini')
        self.assertEqual(len(self.calc.datastore['ruptures']), 2)
        [fname] = export(('events', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/events.csv', fname)

    def test_minimum_intensity(self):
        out = self.run_calc(case_2.__file__, 'job.ini', exports='csv',
                            minimum_intensity='0.2')

        [fname, _, _] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/minimum-intensity-gmf-data.csv', fname)

        # test gmf_data.hdf5 exporter
        [fname] = export(('gmf_data', 'hdf5'), self.calc.datastore)
        self.assertIn('gmf-data_', fname)

    def test_case_2(self):
        out = self.run_calc(case_2.__file__, 'job.ini', exports='csv',
                            concurrent_tasks='4')

        [gmfs, sig_eps, _sitefile] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/gmf-data.csv', gmfs)
        # this is a case with truncation_level=0: sig-eps.csv must be empty
        self.assertEqualFiles('expected/sig-eps.csv', sig_eps)

        [fname] = out['hcurves', 'csv']
        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1.csv', fname)

    def test_case_2bis(self):  # oversampling
        out = self.run_calc(case_2.__file__, 'job_2.ini', exports='csv,xml')
        [fname, _, _] = out['gmf_data', 'csv']  # 2 realizations, 1 TRT
        self.assertEqualFiles('expected/gmf-data-bis.csv', fname)
        for fname in out['hcurves', 'csv']:
            self.assertEqualFiles('expected/' + strip_calc_id(fname), fname,
                                  delta=1E-6)

    def test_case_3(self):  # 1 site, 1 rupture, 2 GSIMs, 10,000 years
        self.run_calc(case_3.__file__, 'job.ini')
        [f] = export(('avg_gmf', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/avg_gmf.csv', f)

        [f] = export(('ruptures', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/ruptures.csv', f)

        # check association events <-> GSIMs are 50-50 for full enum
        rlzs = self.calc.datastore['full_lt'].get_realizations()
        gsim = [rlz.gsim_rlz.value[0] for rlz in rlzs]
        edf = self.calc.datastore.read_df('events', 'id')
        edf['gsim'] = [gsim[r] for r in edf.rlz_id]
        A, S = edf.groupby('gsim').rlz_id.count()
        self.assertEqual(A, 5191)  # AkkarBommer2010 assocs
        self.assertEqual(S, 4930)  # SadighEtAl1997 assocs

        # check association events <-> GSIMs are 90-10 for sampling
        self.run_calc(case_3.__file__, 'job.ini',
                      number_of_logic_tree_samples=10000,
                      ses_per_logic_tree_path=1)
        rlzs = self.calc.datastore['full_lt'].get_realizations()
        gsim = [rlz.gsim_rlz.value[0] for rlz in rlzs]
        edf = self.calc.datastore.read_df('events', 'id')
        edf['gsim'] = [gsim[r] for r in edf.rlz_id]
        A, S = edf.groupby('gsim').rlz_id.count()
        self.assertEqual(A, 9130)  # AkkarBommer2010 assocs
        self.assertEqual(S, 991)   # SadighEtAl1997 assocs

    def test_case_4(self):
        out = self.run_calc(case_4.__file__, 'job.ini', exports='csv')
        [fname] = out['hcurves', 'csv']
        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1.csv', fname)

        # exercise preclassical
        self.run_calc(case_4.__file__, 'job.ini',
                      calculation_mode='preclassical')

    def test_case_5(self):
        out = self.run_calc(case_5.__file__, 'job.ini', exports='csv')
        [fname, _, _] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/%s' % strip_calc_id(fname), fname,
                              delta=1E-6)

        [fname] = export(('ruptures', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/ruptures.csv', fname, delta=1E-6)

        tmp = gettemp(extract(self.calc.datastore, 'ruptures').array)
        self.assertEqualFiles('expected/ruptures_full.csv', tmp, delta=1E-6)

        # check MFD
        aw = extract(self.calc.datastore, 'event_based_mfd?')
        aac(aw.mag, [4.6, 4.7, 4.9, 5.1, 5.3, 5.7], atol=1E-6)
        aac(aw.freq, [0.004444, 0.004444, 0.006667, 0.002222,
                      0.002222, 0.002222], atol=1E-4)

    def test_case_6(self):
        # 2 models x 3 GMPEs, different weights
        expected = [
            'hazard_curve-mean.csv',
            'quantile_curve-0.1.csv',
        ]
        out = self.run_calc(case_6.__file__, 'job.ini', exports='csv')
        fnames = out['hcurves', 'csv']
        for exp, got in zip(expected, fnames):
            self.assertEqualFiles('expected/%s' % exp, got)

        [fname] = export(('realizations', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/realizations.csv', fname)

        # comparing with the full calculation
        # weights = [0.3 , 0.18, 0.12, 0.2 , 0.12, 0.08] for 6 realizations
        self.check_avg_gmf()

    def test_case_7(self):
        # 2 models x 3 GMPEs, 1000 samples * 10 SES
        expected = [
            'hazard_curve-mean.csv',
        ]
        out = self.run_calc(case_7.__file__, 'job.ini', exports='csv')
        aw = extract(self.calc.datastore, 'realizations')
        dic = countby(aw.array, 'branch_path')
        self.assertEqual({b'A~A': 308,  # w = .6 * .5 = .30
                          b'A~B': 173,  # w = .6 * .3 = .18
                          b'A~C': 119,  # w = .6 * .2 = .12
                          b'B~A': 192,  # w = .4 * .5 = .20
                          b'B~B': 127,  # w = .4 * .3 = .12
                          b'B~C': 81},  # w = .4 * .2 = .08
                         dic)

        fnames = out['hcurves', 'csv']
        mean_eb = get_mean_curve(self.calc.datastore, 'PGA', slice(None))
        for exp, got in zip(expected, fnames):
            self.assertEqualFiles('expected/%s' % exp, got)
        mean_cl = get_mean_curve(self.calc.cl.datastore, 'PGA', slice(None))
        reldiff, _index = max_rel_diff_index(mean_cl, mean_eb, min_value=0.1)
        self.assertLess(reldiff, 0.05)

    def test_case_8(self):
        out = self.run_calc(case_8.__file__, 'job.ini', exports='csv')
        [fname] = out['ruptures', 'csv']
        self.assertEqualFiles('expected/rup_data.csv', fname, delta=1E-4)

    def test_case_9(self):
        # example with correlation: the site collection must not be filtered
        self.run_calc(case_9.__file__, 'job.ini', exports='csv')
        # this is a case where there are 2 ruptures and 1 gmv per site
        self.assertEqual(len(self.calc.datastore['gmf_data/eid']), 14)

    def test_case_10(self):
        # this is a case with multiple files in the smlt uncertaintyModel
        # and with sampling
        self.run_calc(case_10.__file__, 'job.ini')
        [fname] = export(('realizations', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/realizations.csv', fname)

    def test_case_12(self):
        out = self.run_calc(case_12.__file__, 'job.ini', exports='csv')
        [fname] = out['hcurves', 'csv']
        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1_b2.csv', fname)

    def test_case_13(self):
        out = self.run_calc(case_13.__file__, 'job.ini', exports='csv')
        [fname, _, _] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/gmf-data.csv', fname)

        [fname] = out['hcurves', 'csv']
        self.assertEqualFiles(
            'expected/hazard_curve-smltp_b1-gsimltp_b1.csv', fname)

    def test_case_14(self):
        # sampling of a logic tree of kind `is_source_specific`
        out = self.run_calc(case_14.__file__, 'job.ini', exports='csv')
        [fname, _, _] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/gmf-data.csv', fname)

    def test_case_15(self):
        # an example for Japan testing also the XML rupture exporter
        self.run_calc(case_15.__file__, 'job.ini')
        [fname] = export(('ruptures', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/ruptures.csv', fname, delta=.004)

    def test_case_16(self):
        # an example with site model raising warnings and autogridded exposure
        # and GMF amplification too
        self.run_calc(case_16.__file__, 'job.ini')
        hid = str(self.calc.datastore.calc_id)
        self.run_calc(case_16.__file__, 'job.ini', hazard_calculation_id=hid)
        tmp = gettemp(view('global_gmfs', self.calc.datastore))
        self.assertEqualFiles('expected/global_gmfs.txt', tmp)

    def test_case_17(self):  # oversampling
        # also, grp-00 does not produce ruptures
        expected = [
            'hazard_curve-mean.csv',
            'hazard_curve-rlz-001.csv',
            'hazard_curve-rlz-002.csv',
            'hazard_curve-rlz-003.csv',
            'hazard_curve-rlz-004.csv',
        ]
        # test the --hc functionality, i.e. that ruptures are read correctly
        out = self.run_calc(case_17.__file__, 'job.ini,job.ini', exports='csv')
        fnames = out['hcurves', 'csv']
        for exp, got in zip(expected, fnames):
            self.assertEqualFiles('expected/%s' % exp, got)

        # check that GMFs are not stored
        with self.assertRaises(KeyError):
            self.calc.datastore['gmf_data']

    def test_case_18(self):  # oversampling, 3 realizations
        out = self.run_calc(case_18.__file__, 'job.ini', exports='csv')
        [fname, _, _] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/%s' % strip_calc_id(fname), fname,
                              delta=1E-6)

    def test_case_19(self):  # test for Vancouver using the NRCan15SiteTerm
        self.run_calc(case_19.__file__, 'job.ini')
        [gmf, _, _] = export(('gmf_data', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/gmf-data.csv', gmf)

        # a test with grid and site model
        self.run_calc(case_19.__file__, 'job_grid.ini')
        self.assertEqual(len(self.calc.datastore['ruptures']), 2)

        # error for missing intensity_measure_types
        with self.assertRaises(InvalidFile) as ctx:
            self.run_calc(
                case_19.__file__, 'job.ini',
                hazard_calculation_id=str(self.calc.datastore.calc_id),
                intensity_measure_types='')
        self.assertIn('There are no intensity measure types in',
                      str(ctx.exception))

    def test_case_20(self):  # test for Vancouver using the NRCan15SiteTerm
        self.run_calc(case_20.__file__, 'job.ini')
        [gmf, _, _] = export(('gmf_data', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/gmf-data.csv', gmf)

        # check the relevant_events
        E = extract(self.calc.datastore, 'num_events')['num_events']
        e = len(extract(self.calc.datastore, 'events'))
        self.assertAlmostEqual(e/E, 0.189723320158)

        # run again the GMF calculation, but this time from stored ruptures
        hid = str(self.calc.datastore.calc_id)
        self.run_calc(case_20.__file__, 'job.ini', hazard_calculation_id=hid)
        [gmf, _, _] = export(('gmf_data', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/gmf-data-from-ruptures.csv', gmf)

    def test_case_21(self):
        self.run_calc(case_21.__file__, 'job.ini', exports='csv,xml')
        self.run_calc(case_21.__file__, 'job.ini',
                      ses_per_logic_tree_path='900',
                      number_of_logic_tree_samples='0')

    def test_case_22(self):
        out = self.run_calc(case_22.__file__, 'job.ini', exports='csv')
        [fname, _, _] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/%s' % strip_calc_id(fname), fname,
                              delta=1E-6)

    def test_case_23(self):
        # case with implicit grid and site model on a larger grid
        out = self.run_calc(case_23.__file__, 'job.ini', exports='csv')
        [fname] = out['ruptures', 'csv']
        self.assertEqualFiles('expected/%s' % strip_calc_id(fname), fname,
                              delta=1E-4)
        sio = io.StringIO()
        write_csv(sio, self.calc.datastore['sitecol'].array)
        tmp = gettemp(sio.getvalue())
        self.assertEqualFiles('expected/sitecol.csv', tmp)

    def test_case_24(self):
        # This is a test for shift_hypo = true - The expected results are the
        # same ones defined for the case_44 of the classical methodology
        self.run_calc(case_24.__file__, 'job.ini')
        [fname] = export(('hcurves', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hazard_curve-mean-PGA.csv', fname)

    def test_case_25(self):
        # logic tree common + extra
        # common1.xml contains "5" "6"
        # common2.xml contains "1" "2"
        # extra1.xml contains "3"
        # extra2.xml contains "4"
        # extra3.xml contains "7"
        self.run_calc(case_25.__file__, 'job.ini')
        mean, *others = export(('hcurves', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hazard_curve-PGA.csv', mean)

        self.run_calc(case_25.__file__, 'job2.ini')
        mean, *others = export(('hcurves', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/hazard_curve-PGA.csv', mean)

        # test with common1.xml present into branchs and sampling
        self.run_calc(case_25.__file__, 'job_common.ini')
        mean, *others = export(('ruptures', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/ruptures.csv', mean)

    def test_case_26_land(self):
        # cali landslide simplified
        self.run_calc(case_26.__file__, 'job_land.ini')
        df = self.calc.datastore.read_df('gmf_data', 'sid')
        pd_mean = df[df.DispProb > 0].DispProb.mean()
        nd_mean = df[df.Disp > 0].Disp.mean()
        self.assertGreater(pd_mean, 0)
        self.assertGreater(nd_mean, 0)
        [fname, _, _] = export(('gmf_data', 'csv'), self.calc.datastore)
        arr = read_csv(fname)[:2]
        self.assertEqual(arr.dtype.names,
                         ('site_id', 'event_id', 'gmv_PGA',
                          'sep_Disp', 'sep_DispProb'))

    def test_case_26_liq(self):
        # cali liquefaction simplified
        self.run_calc(case_26.__file__, 'job_liq.ini')
        [fname] = export(('avg_gmf', 'csv'), self.calc.datastore)
        self.assertEqualFiles('avg_gmf.csv', fname)

    def test_case_27(self):
        # splitting ruptures + gmf1 + gmf2
        self.run_calc(case_27.__file__, 'job.ini',
                      ground_motion_fields="false")
        self.assertEqual(len(self.calc.datastore['ruptures']), 15)
        hc_id = str(self.calc.datastore.calc_id)

        self.run_calc(case_27.__file__, 'job.ini', sites_slice="0:41",
                      hazard_calculation_id=hc_id)
        [fname] = export(('avg_gmf', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/avg_gmf1.csv', fname)

        self.run_calc(case_27.__file__, 'job.ini', sites_slice="41:82",
                      hazard_calculation_id=hc_id)
        [fname] = export(('avg_gmf', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/avg_gmf2.csv', fname)

    def test_case_28(self):
        out = self.run_calc(case_28.__file__, 'job.ini', exports='csv')
        [fname, _, _] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/%s' % strip_calc_id(fname), fname,
                              delta=1E-6)

    def test_overflow(self):
        too_many_imts = {'SA(%s)' % period: [0.1, 0.2, 0.3]
                         for period in numpy.arange(0.1,  1, 0.001)}
        with self.assertRaises(ValueError) as ctx:
            self.run_calc(
                case_2.__file__, 'job.ini',
                intensity_measure_types_and_levels=str(too_many_imts))
        self.assertEqual(str(ctx.exception),
                         'The event_based calculator is restricted '
                         'to 256 imts, got 900')

    def test_mutex(self):
        out = self.run_calc(mutex.__file__, 'job.ini', exports='csv,xml')
        [fname] = out['ruptures', 'csv']
        self.assertEqualFiles('expected/ruptures.csv', fname, delta=1E-6)

    def test_gmpe_tables(self):
        out = self.run_calc(
            gmpe_tables.__file__, 'job.ini',
            calculation_mode='event_based',
            investigation_time='100',
            exports='csv')
        [fname, _, _] = out['gmf_data', 'csv']
        self.assertEqualFiles('expected/gmf.csv', fname, delta=1E-6)
