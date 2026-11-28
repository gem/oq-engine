# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import os
import shutil
import tempfile
from unittest import mock

import numpy

from openquake.baselib import hdf5
from openquake.hazardlib import InvalidFile
from openquake.hazardlib.stats import mean_curve
from openquake.hazardlib.tom import NegativeBinomialTOM
from openquake.hazardlib.calc.disagg import to_probs, to_rates
from openquake.commonlib import readinput
from openquake.calculators.export import export
from openquake.calculators.displacement import (
    DisplacementCalculator, explicit_rates, get_stat_curve)
from openquake.calculators.getters import MapGetter
from openquake.calculators.tests import CalculatorTestCase
from openquake.pfd.primary_surf_rup.mammarella2024 import (
    Mammarella2024PrimarySR)
from openquake.qa_tests_data.pfd import case_1, case_2, case_3, case_4
from openquake.qa_tests_data.pfd import case_5, case_6, case_7, case_8
from openquake.qa_tests_data.pfd import case_9, case_10, case_11


class DisplacementTestCase(CalculatorTestCase):

    def test_case_1(self):
        self.run_calc(case_1.__file__, 'job.ini')
        dstore = self.calc.datastore
        hcurves = dstore['hcurves-rlzs'][:]
        self.assertEqual(hcurves.shape, (1, 1, 1, 5))
        # the site is inside the distributed zone: positive probabilities
        self.assertTrue((hcurves > 0).all())
        stats = dstore['hcurves-stats'][:]
        self.assertEqual(stats.shape[0], 1)  # 1 site
        self.assertTrue((stats > 0).all())
        # per-source mean rates are stored, since disagg_by_src is required
        self.assertIn('mean_rates_by_src', dstore)
        # contexts are built for the float positions at the surface only:
        # 10 of 15 (magnitudes 6.55 and 6.65 also float down dip, 4 + 1
        # buried positions). The surface positions carry the whole rate
        # of their magnitude
        self.assertEqual(int(dstore['source_info'][0]['num_ctxs']), 10)
        # simple faults keep the mesh top edge (no declared trace attached)
        [src] = list(self.calc.csm.src_groups[0])
        rup = next(iter(src.iter_ruptures()))
        self.assertFalse(hasattr(rup.surface, 'original_tor'))
        # the mean curve can be exported as CSV
        [fname] = export(('hcurves/mean', 'csv'), dstore)
        self.assertTrue(os.path.exists(fname))
        with open(fname) as f:
            meta = f.readline()
            header = f.readline()
            row = f.readline().strip()
        self.assertIn("kind='mean'", meta)
        self.assertIn('poe-1.00000e-04', header)
        self.assertEqual(len(row.split(',')), 8)  # lon,lat,depth + 5 levels
        [fname2] = export(('mean_rates_by_src', 'csv'), dstore)
        self.assertTrue(os.path.exists(fname2))
        with open(fname2) as f:
            f.readline()  # metadata
            self.assertEqual(f.readline().split(',')[0], 'source_id')

    def test_case_1_investigation_time(self):
        # as in the classical calculator the curves are probabilities of
        # exceedance in the investigation time and the maps refer to the
        # poes in that time, while mean_rates_by_src stays annual: the
        # 5000-year displacement is the same with 1 and 50 years
        self.run_calc(case_1.__file__, 'job.ini',
                      poes=str(-numpy.expm1(-1 / 5000)))
        dstore = self.calc.datastore
        curve1 = dstore['hcurves-stats'][0, 0, 0].astype(float)
        hmap1 = dstore['hmaps-stats'][0, 0, 0]
        bysrc1 = dstore['mean_rates_by_src'][:]
        self.assertTrue(0.1 < hmap1[0] < 1.0)  # between two levels
        self.run_calc(case_1.__file__, 'job.ini', investigation_time='50',
                      poes=str(-numpy.expm1(-50 / 5000)))
        dstore = self.calc.datastore
        annual = -numpy.log1p(-curve1)
        numpy.testing.assert_allclose(
            dstore['hcurves-stats'][0, 0, 0], -numpy.expm1(-50 * annual),
            rtol=1e-5)
        # the maps interpolate log(poe) between the levels and the poe in
        # 50 years, 1 - exp(-50 rate), is not proportional to the rate:
        # 0.2% here, as in the classical calculator (before, 0 m)
        numpy.testing.assert_allclose(
            dstore['hmaps-stats'][0, 0, 0], hmap1, rtol=5e-3)
        numpy.testing.assert_allclose(
            dstore['mean_rates_by_src'][:], bysrc1, rtol=1e-6)

    def test_stat_curve_long_investigation_time(self):
        # one level, two realizations: over a long investigation time the
        # probability of the first one rounds to 1, and a rate recomputed
        # from it saturates at 100 instead of 43.76
        rates = numpy.array([[43.76, 0.5]])
        weights = numpy.array([0.01, 0.99])
        [mean] = get_stat_curve(rates, weights, mean_curve)
        self.assertAlmostEqual(mean, -numpy.expm1(-(0.4376 + 0.495)))
        [saturated] = to_probs(mean_curve(to_rates(to_probs(rates)).T,
                                          weights))
        self.assertGreater(saturated - mean, 0.1)

    def test_missing_investigation_time(self):
        params = readinput.get_params(
            os.path.join(os.path.dirname(case_1.__file__), 'job.ini'))
        del params['investigation_time']
        with self.assertRaises(InvalidFile) as ctx:
            readinput.get_oqparam(params)
        self.assertIn('missing investigation_time', str(ctx.exception))

    def test_case_2(self):
        # map mode: a region grid with a return period
        self.run_calc(case_2.__file__, 'job.ini')
        dstore = self.calc.datastore
        # characteristic faults carry the declared top edge, so their PFD
        # distances are not distorted by the resampled mesh top edge
        for sg in self.calc.csm.src_groups:
            for src in sg:
                self.assertTrue(hasattr(src.surface, 'original_tor'))
        hmaps = dstore['hmaps-rlzs'][:]
        self.assertEqual(hmaps.shape, (44, 1, 1, 1))  # 44 sites, 1 poe
        self.assertTrue((hmaps > 0).any())
        hstats = dstore['hmaps-stats'][:]
        self.assertEqual(hstats.shape[:2], (44, 4))  # mean + 3 quantiles
        [fname] = export(('hmaps/mean', 'csv'), dstore)
        self.assertTrue(os.path.exists(fname))
        with open(fname) as f:
            meta = f.readline()
            header = f.readline()
        self.assertIn("kind='mean'", meta)
        self.assertTrue(header.startswith('lon,lat,Disp-'))

    def test_case_3(self):
        # two source-model realizations selecting different source models:
        # R = 2 but each source group is active in a single realization
        self.run_calc(case_3.__file__, 'job.ini')
        dstore = self.calc.datastore
        self.assertEqual(self.calc.full_lt.get_num_paths(), 2)
        cmakers = self.calc.csm.get_cmakers()
        active = [len(next(iter(cm.gsims.values()))) for cm in cmakers]
        self.assertEqual(active, [1, 1])  # only 1 of the 2 realizations
        # with R > 1 and individual_rlzs=false only the stats are stored;
        # the individual curves are recomputed from the sparse _rates table
        self.assertIn('_rates', dstore)
        self.assertNotIn('hcurves-rlzs', dstore)
        self.assertIn('hcurves-stats', dstore)
        R = 2
        sids = self.calc.sitecol.sids
        getter = MapGetter([dstore.filename], 0,
                           [numpy.uint32([r]) for r in range(R)], sids, R,
                           self.calc.oqparam)
        hcurve = getter.get_hcurve(sids[0])  # (L, R) probabilities
        # the two sources have different aValues, so the curves differ
        self.assertFalse(numpy.allclose(hcurve[:, 0], hcurve[:, 1]))
        # both sources are exported, each scaled by its realization weight
        [fname] = export(('mean_rates_by_src', 'csv'), dstore)
        with open(fname) as f:
            f.readline()  # metadata
            f.readline()  # header
            rows = [ln.split(',') for ln in f.read().splitlines()]
        self.assertEqual(len(rows), 10)  # 2 sources x 5 displacement levels
        self.assertEqual({r[0] for r in rows}, {'1', '2'})
        [fname2] = export(('hcurves/mean', 'csv'), dstore)
        self.assertTrue(os.path.exists(fname2))

    def test_case_4(self):
        # a multiFaultSource built from kite sections: the PFD distances
        # come from the multi-surface 'segments' reference line
        self.run_calc(case_4.__file__, 'job.ini')
        dstore = self.calc.datastore
        hcurves = dstore['hcurves-rlzs'][:]
        self.assertEqual(hcurves.shape, (1, 1, 1, 5))
        self.assertTrue((hcurves > 0).all())
        # 3 ruptures, but only the 2 surface-reaching ones are used
        self.assertEqual(int(dstore['source_info'][0]['num_ctxs']), 2)
        # the section trace runs E-W at lat 45.0; the site sits on it, so
        # rtor ~ 0 while x/L is the GC2 position on the raw segmentation
        csm = self.calc.csm
        cmaker = csm.get_cmakers()[0]
        [src] = list(csm.src_groups[0])
        ctxs = list(cmaker.get_ctxs(src, self.calc.sitecol))
        self.assertEqual(len(ctxs), 2)
        single, multi = ctxs  # mag 5 (1 section), mag 6 (2 sections)
        self.assertAlmostEqual(float(single.rtor[0]), 0.0303, places=3)
        self.assertAlmostEqual(float(single.x_l[0]), 0.51728, places=4)
        self.assertAlmostEqual(float(single.length[0]), 38.0, places=1)
        # the 2-section rupture spans both kites (no gap bridging)
        self.assertAlmostEqual(float(multi.x_l[0]), 0.25425, places=4)
        self.assertAlmostEqual(float(multi.length[0]), 77.313, places=2)

    def run_case_4(self, probs_occur, **params):
        # case_4 with other probabilities of occurrence of its 3 ruptures
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        dest = os.path.join(tmp, 'case_4')
        shutil.copytree(os.path.dirname(case_4.__file__), dest)
        with hdf5.File(os.path.join(dest, 'ssm.hdf5'), 'r+') as h5:
            del h5['1/probs_occur']
            h5['1/probs_occur'] = numpy.array(probs_occur, float)
        # the source model declares the time of its probabilities, which
        # must be the investigation time of the job
        itime = params.get('investigation_time', '1.0')
        ssm = os.path.join(dest, 'ssm.xml')
        with open(ssm, encoding='utf-8') as f:
            text = f.read()
        with open(ssm, 'w', encoding='utf-8') as f:
            f.write(text.replace('investigation_time="1.0"',
                                 'investigation_time="%s"' % itime))
        self.run_calc(os.path.join(dest, 'job.ini'), 'job.ini', **params)
        dstore = self.calc.datastore
        return (dstore['hcurves-rlzs'][0, 0, 0].astype(float),
                dstore['mean_rates_by_src'][:])

    def test_case_4_probabilities_of_occurrence(self):
        # with infer_occur_rates = false (the default) the ruptures carry the
        # distribution of the number of occurrences in the investigation
        # time, used in full as in the classical calculator: P(no
        # exceedance) = sum_k p(k) (1 - q)^k (before, zero hazard)
        p0 = numpy.array([.8, .7, .9])  # P(no occurrence) of the ruptures
        poisson, _ = self.run_case_4(numpy.c_[p0, 1 - p0],
                                     infer_occur_rates='true')
        # the Poisson distribution with the same P(no occurrence) gives the
        # curve obtained by inferring the rates
        k = numpy.arange(40)
        lam = -numpy.log(p0)[:, None]
        pmf = numpy.exp(-lam + k * numpy.log(lam) - numpy.cumsum(
            numpy.log(numpy.maximum(k, 1))))
        got, by_src = self.run_case_4(pmf, infer_occur_rates='false')
        numpy.testing.assert_allclose(got, poisson, rtol=1e-6)
        # exactly one and exactly two occurrences: no P(no occurrence) to
        # infer a rate from, and P(no exceedance) is squared
        one, by_src = self.run_case_4([[0., 1., 0.]] * 3,
                                      infer_occur_rates='false')
        two, _ = self.run_case_4([[0., 0., 1.]] * 3,
                                 infer_occur_rates='false')
        self.assertTrue((one > 0).all())
        self.assertTrue(numpy.isfinite(by_src).all())
        numpy.testing.assert_allclose(two, 1 - (1 - one) ** 2, rtol=1e-6)

    def test_case_4_inferred_rates_investigation_time(self):
        # the probabilities of occurrence refer to the investigation time:
        # the same source over 50 years gives the same annual rates
        p0 = numpy.array([.8, .7, .9])
        curve1, by_src1 = self.run_case_4(numpy.c_[p0, 1 - p0],
                                          infer_occur_rates='true')
        p50 = p0 ** 50
        curve50, by_src50 = self.run_case_4(
            numpy.c_[p50, 1 - p50], infer_occur_rates='true',
            investigation_time='50')
        numpy.testing.assert_allclose(by_src50, by_src1, rtol=1e-6)
        annual = -numpy.log1p(-curve1)
        numpy.testing.assert_allclose(
            curve50, -numpy.expm1(-50 * annual), rtol=1e-5)

    def test_case_5(self):
        # a heavy CSV-backed model (Kuehn2024PrimaryFD, aggregate definition)
        # in the logic tree, on a floating simple fault. The expected rates
        # are the ones of the same job with the source written out position
        # by position (a characteristic fault for each float position at the
        # surface, with rate(m) / n_along_strike(m)), which the floating
        # source reproduces within 3e-5. They are larger than the rates of
        # oq-pfdha's `job_kuehn2024` demo pinned here before (by 43% at the
        # low levels), which kept only 1/10 and 1/5 of the rate of the two
        # magnitudes that float down dip, on top of P(SR | m).
        self.run_calc(case_5.__file__, 'job.ini')
        dstore = self.calc.datastore
        hcurves = dstore['hcurves-rlzs'][0, 0, 0, :]
        self.assertEqual(hcurves.shape, (18,))
        expected = numpy.array([
            1.58460233e-02, 1.58384051e-02, 1.58030409e-02, 1.57512520e-02,
            1.56937167e-02, 1.55008147e-02, 1.52200768e-02, 1.48563674e-02,
            1.44919800e-02, 1.37831867e-02, 1.18966578e-02, 9.89270490e-03,
            7.98811670e-03, 6.54683355e-03, 1.79177476e-03, 6.37581921e-04,
            2.14697502e-04, 8.51113073e-05])
        # hcurves store exceedance probabilities over investigation_time=1;
        # oq-pfdha's csv reports annual rates, so compare in rate space
        rates = -numpy.log1p(-hcurves)
        numpy.testing.assert_allclose(rates, expected, rtol=1e-4)
        self.assertTrue((hcurves > 0).all())

    def test_case_6(self):
        # IAEA Kumamoto: Chiou2025PrimaryFD x WC1993PrimarySR on a
        # strike-slip characteristicFaultSource; pinned to oq-pfdha's IAEA
        # computed curve
        self.run_calc(case_6.__file__, 'job.ini')
        dstore = self.calc.datastore
        rates = -numpy.log1p(-dstore['hcurves-rlzs'][0, 0, 0, :])
        expected = numpy.array([
            1.317754e-04, 1.315741e-04, 1.304114e-04, 1.287301e-04,
            1.269146e-04, 1.210404e-04, 1.128484e-04, 1.028074e-04,
            9.343359e-05, 7.719933e-05, 4.533372e-05, 2.469248e-05,
            1.304857e-05, 7.570827e-06, 4.378482e-07, 7.455173e-08,
            1.480967e-08, 4.191597e-09])
        numpy.testing.assert_allclose(rates, expected, rtol=1e-3)

    def test_case_7(self):
        # IAEA Le Teil: Lavrentiadis2023PrimaryFD_principal with a fixed
        # case-specific P_sr; the last levels underflow to 0 in the stored
        # single-precision poes, hence the tiny atol
        self.run_calc(case_7.__file__, 'job.ini')
        dstore = self.calc.datastore
        rates = -numpy.log1p(-dstore['hcurves-rlzs'][0, 0, 0, :])
        expected = numpy.array([
            2.754624e-05, 2.747966e-05, 2.725665e-05, 2.697595e-05,
            2.668124e-05, 2.572885e-05, 2.436464e-05, 2.260835e-05,
            2.086963e-05, 1.760204e-05, 1.015664e-05, 4.751256e-06,
            1.844652e-06, 7.297981e-07, 8.930973e-10, 2.613507e-12,
            3.724419e-15, 9.250608e-18])
        numpy.testing.assert_allclose(
            rates, expected, rtol=1e-3, atol=1e-12)

    def test_case_8(self):
        # IAEA Norcia: the combined Visini et al. (2025) distributed
        # pipeline (Takao2013PrimaryFD + Visini2025SecondarySR/FD, case3);
        # the checked-in IAEA computed csv was stale, so the expected
        # values come from a fresh oq-pfdha run of job_distributed_V24
        self.run_calc(case_8.__file__, 'job.ini')
        dstore = self.calc.datastore
        rates = -numpy.log1p(-dstore['hcurves-rlzs'][0, 0, 0, :])
        expected = numpy.array([
            5.266179186494684e-08, 5.266179186494684e-08,
            5.19298383624369e-08, 4.925340140048624e-08,
            4.5825476691286254e-08, 3.5788861736968006e-08,
            2.592424026375021e-08, 1.8045927372692255e-08,
            1.3086730752261963e-08, 7.538262169245839e-09,
            2.1811511322876093e-09, 6.508022191776344e-10,
            1.8156728523808872e-10, 4.976263365293209e-11,
            0.0, 0.0, 0.0, 0.0])
        numpy.testing.assert_allclose(
            rates, expected, rtol=1e-4, atol=1e-14)

    def test_case_9(self):
        # case_1 with twelve abGRAbsolute source-model branches of unequal
        # weight: a-value shifts scale all rates by 10**da, so the mean must
        # be sum(w_k * 10**da_k) times the case_1 curve. With 11+ branches
        # the context makers are ordered as strings ("10" before "2"), so a
        # group mapped by position gets another branch's weight.
        self.run_calc(case_1.__file__, 'job.ini')
        ref = -numpy.log1p(-self.calc.datastore['hcurves-stats'][0, 0, 0])
        self.run_calc(case_9.__file__, 'job.ini')
        rates = -numpy.log1p(-self.calc.datastore['hcurves-stats'][0, 0, 0])
        weights = numpy.arange(1, 13) / 78.
        shifts = 0.05 * (numpy.arange(1, 13) - 6)
        factor = (weights * 10 ** shifts).sum()
        numpy.testing.assert_allclose(rates, factor * ref, rtol=1e-4)

    def by_src(self):
        # mean annual rates per source at its own on-trace site, (2, L1)
        rates = self.calc.datastore['mean_rates_by_src'][:]  # N, M, L1, S
        return numpy.array([rates[0, 0, :, 0], rates[1, 0, :, 1]])

    def test_case_10(self):
        # P(SR | m) is counted once. Two simple faults, 24 km long, with
        # a single magnitude and ruptures as long as the fault, so that
        # they float down dip only: all the positions share the same
        # top edge, the trace. The hazard on the trace must then be the
        # one of the characteristic twins (same geometry, same MFD),
        # whatever the mesh; before, the engine kept the rate of the only
        # position at the surface, i.e. the rate times 1 / n_down_dip
        # (1/6 and 1/12 at 2 km, 1/10 and 1/24 at 1 km).
        self.run_calc(case_10.__file__, 'job_char.ini')
        char = self.by_src()
        self.assertTrue((char > 0).all())
        self.run_calc(case_10.__file__, 'job.ini')
        float2 = self.by_src()
        # one context per fault: the top position, with the whole rate
        info = self.calc.datastore['source_info'][:]
        self.assertEqual(list(info['num_ctxs']), [1, 1])
        self.assertEqual(list(info['num_ruptures']), [6, 12])
        self.run_calc(case_10.__file__, 'job.ini',
                      rupture_mesh_spacing='1.0')
        float1 = self.by_src()
        info = self.calc.datastore['source_info'][:]
        self.assertEqual(list(info['num_ruptures']), [10, 24])
        numpy.testing.assert_allclose(float2, char, rtol=1e-4)
        numpy.testing.assert_allclose(float1, float2, rtol=1e-6)

        # P(SR | m) comes from the model of the branch only. Mammarella
        # et al. (2024) leaves the geometry to the sources, so each fault
        # gets the probability for its own dip and seismogenic depth
        self.run_calc(case_10.__file__, 'job_psr1.ini')
        psr1 = self.by_src()
        model = Mammarella2024PrimarySR(
            MSR=0, HDD_str='AGG_N', style='normal', dip_sigma=5., t_d=2.,
            Zs_sigma=2., t_z=2.)
        p_a = model.get_prob(6.0, dip_mu=60., Zs_mu=12.)
        p_b = model.get_prob(6.5, dip_mu=35., Zs_mu=20.)
        self.assertGreater(abs(p_a - p_b), 0.05)
        numpy.testing.assert_allclose(
            float2 / psr1, [[p_a] * 5, [p_b] * 5], rtol=1e-5)

    def test_case_11(self):
        # the same source "3" in two source-model files (rates 1 and 2, weights
        # 0.75 and 0.25), so the engine renames the copies "3!b_a" and "3!b_b";
        # the PFD branch sets with applyToSources="3" must still apply to them,
        # and the rates by source must be stored under "3"
        self.run_calc(case_1.__file__, 'job.ini')
        ref = -numpy.log1p(-self.calc.datastore['hcurves-stats'][0, 0, 0])
        self.run_calc(case_11.__file__, 'job.ini')
        rates = -numpy.log1p(-self.calc.datastore['hcurves-stats'][0, 0, 0])
        numpy.testing.assert_allclose(rates, 1.25 * ref, rtol=1e-5)
        by_src = self.calc.datastore['mean_rates_by_src']
        self.assertEqual(list(by_src.src_id), ['3'])
        numpy.testing.assert_allclose(by_src.array[0, 0, :, 0], rates, rtol=1e-5)

    def copy_case(self, case, replacements):
        """
        :param replacements: file name -> list of (old, new) texts
        :returns: the directory of a copy of the case, with the replacements
        """
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        src = os.path.dirname(case.__file__)
        dest = os.path.join(tmp, os.path.basename(src))
        shutil.copytree(src, dest)
        for fname, pairs in replacements.items():
            path = os.path.join(dest, fname)
            with open(path, encoding='utf-8') as f:
                text = f.read()
            for old, new in pairs:
                self.assertIn(old, text)
                text = text.replace(old, new)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(text)
        return dest

    def test_case_10_colon_convention(self):
        # by the colon convention of the engine the sources "fault:17" and
        # "fault:18" are fragments of the source "fault", which is what the
        # logic trees refer to: applyToSources="fault" applies to both
        self.run_calc(case_10.__file__, 'job.ini')
        ref = self.calc.datastore['hcurves-stats'][:, 0]
        self.assertTrue((ref > 0).any())
        rename = [('id="A"', 'id="fault:17"'), ('id="B"', 'id="fault:18"')]
        bset = 'branchSetID="bs_psr"'
        dest = self.copy_case(case_10, {
            'source_model.xml': rename,
            'pfd_logic_tree.xml': [(bset, bset + ' applyToSources="fault"')]})
        self.run_calc(os.path.join(dest, 'job.ini'), 'job.ini')
        numpy.testing.assert_allclose(
            self.calc.datastore['hcurves-stats'][:, 0], ref, rtol=1e-6)
        # a fragment cannot be addressed on its own, as in the source model
        # logic tree, and a source that does not exist is an error
        for src_id, msg in [('fault:17', 'colon convention'),
                            ('faultX', 'no such source')]:
            dest = self.copy_case(case_10, {
                'source_model.xml': rename,
                'pfd_logic_tree.xml': [
                    (bset, bset + ' applyToSources="%s"' % src_id)]})
            with self.assertRaises(InvalidFile) as ctx:
                self.run_calc(os.path.join(dest, 'job.ini'), 'job.ini')
            self.assertIn(msg, str(ctx.exception))

    def test_case_4_split_source(self):
        # a multi-fault source with more ruptures than BLOCKSIZE is split in
        # blocks "1:0", "1:1", which the tasks read from the datastore: a
        # branch set with applyToSources="1" applies to them
        bset = 'branchSetID="bs_1_primary_surf_rup"'
        dest = self.copy_case(case_4, {'pfd_logic_tree.xml': [
            (bset, bset + ' applyToSources="1"')]})
        modes = []  # SWMR mode when the outputs are written
        post_execute = DisplacementCalculator.post_execute

        def spy(calc, *args):
            modes.append(calc.datastore.hdf5.swmr_mode)
            return post_execute(calc, *args)
        with mock.patch('openquake.hazardlib.source.multi_fault.BLOCKSIZE', 2):
            self.run_calc(case_4.__file__, 'job.ini')
            ref = self.calc.datastore['hcurves-stats'][0, 0, 0]
            with mock.patch.object(DisplacementCalculator, 'post_execute', spy):
                self.run_calc(os.path.join(dest, 'job.ini'), 'job.ini')
        ids = sorted(src.source_id for grp in self.calc.csm.src_groups
                     for src in grp)
        self.assertEqual(ids, ['1:0', '1:1'])
        # the outputs are written after leaving the SWMR mode of the tasks
        self.assertEqual(modes, [False])
        numpy.testing.assert_allclose(
            self.calc.datastore['hcurves-stats'][0, 0, 0], ref, rtol=1e-6)

    def test_case_10_negative_binomial(self):
        # fault A with a negative binomial TOM (rate 0.3, alpha 2): with q
        # the probability that one event exceeds the level, the probability
        # of no exceedance in the investigation time T is
        # (1 + alpha * rate * T * q) ** (-1 / alpha); where q = 0 (off the
        # trace, primary displacement only) there is no hazard at all
        head = ('<characteristicFaultSource id="A" name="Fault A" '
                'tectonicRegion="Active Shallow Crust">\n'
                '        <incrementalMFD binWidth="0.1" minMag="6.0">\n'
                '          <occurRates>1.0E-3</occurRates>')
        sites = '10.0 45.1079186, 10.025 45.1079186'
        poisson = self.copy_case(case_10, {'source_model_char.xml': [
            (head, head.replace('1.0E-3', '0.3'))]})
        negbinom = self.copy_case(case_10, {'source_model_char.xml': [
            (head, head.replace('1.0E-3', '0.3').replace(
                'tectonicRegion="Active Shallow Crust">',
                'tectonicRegion="Active Shallow Crust" '
                'tom="NegativeBinomialTOM" mu="0.3" alpha="2">', 1))]})

        def run(path, **params):
            self.run_calc(os.path.join(path, 'job_char.ini'), 'job_char.ini',
                          sites=sites, **params)
            on = numpy.argmin(numpy.abs(self.calc.sitecol.lons - 10.0))
            curves = self.calc.datastore['hcurves-stats'][:, 0, 0]
            return curves[on].astype(float), curves[1 - on]
        poe, _ = run(poisson)
        q = -numpy.log1p(-poe) / 0.3  # exceedance probability of one event
        self.assertTrue((q > 0).all())
        for itime in (1, 50):
            got, off = run(negbinom, investigation_time=str(itime))
            expected = 1 - (1 + 2 * 0.3 * itime * q) ** -.5
            # the closed form is the series summed by the TOM itself
            tom = NegativeBinomialTOM(itime, mu=0.3, alpha=2.)
            numpy.testing.assert_allclose(
                1 - tom.get_probability_no_exceedance(0.3, q[None])[0],
                expected, rtol=1e-9)
            numpy.testing.assert_allclose(got, expected, rtol=1e-5)
            numpy.testing.assert_array_equal(off, 0.)

    def test_case_10_single_source_filters(self):
        # a job restricted to source A (source_id) with a branch set for B:
        # applyToSources names a source of the whole model, so B is valid
        # and A gets the same curve as in the job with both sources, while a
        # misspelled ID is still an error
        bset = 'branchSetID="bs_psr"'
        dest = self.copy_case(case_10, {'pfd_logic_tree.xml': [
            (bset, bset + ' applyToSources="B"')]})
        self.run_calc(os.path.join(dest, 'job.ini'), 'job.ini')
        both = self.calc.datastore['hcurves-stats'][0, 0]
        self.run_calc(os.path.join(dest, 'job.ini'), 'job.ini', source_id='A')
        numpy.testing.assert_allclose(
            self.calc.datastore['hcurves-stats'][0, 0], both, rtol=1e-6)
        bad = self.copy_case(case_10, {'pfd_logic_tree.xml': [
            (bset, bset + ' applyToSources="Bx"')]})
        with self.assertRaises(InvalidFile) as ctx:
            self.run_calc(os.path.join(bad, 'job.ini'), 'job.ini',
                          source_id='A')
        self.assertIn('no such source', str(ctx.exception))

    def test_case_4_single_precision_probabilities(self):
        # the probabilities of occurrence stored in single precision do not
        # sum to 1 exactly (0.9 + 0.1 = 0.99999998): they are normalized,
        # and off the trace (primary displacement only, q = 0) the hazard
        # is exactly 0
        sites = '10.25 45.0, 10.25 45.015'
        curves = {}
        for dtype in ('float64', 'float32'):
            dest = self.copy_case(case_4, {})
            lt = os.path.join(dest, 'pfd_logic_tree.xml')
            with open(lt, encoding='utf-8') as f:
                text = f.read()
            primary = text[:text.index(
                '<logicTreeBranchSet branchSetID="bs_3_secondary_surf_rup"')]
            with open(lt, 'w', encoding='utf-8') as f:
                f.write(primary + '</logicTree>\n</nrml>\n')
            with hdf5.File(os.path.join(dest, 'ssm.hdf5'), 'r+') as h5:
                del h5['1/probs_occur']
                h5['1/probs_occur'] = numpy.array(
                    [[.9, .1], [.7, .3], [.9, .1]], dtype)
            self.run_calc(os.path.join(dest, 'job.ini'), 'job.ini',
                          sites=sites, infer_occur_rates='false')
            on = numpy.argmin(numpy.abs(self.calc.sitecol.lats - 45.0))
            hcurves = self.calc.datastore['hcurves-stats'][:, 0, 0]
            curves[dtype] = hcurves[on], hcurves[1 - on]
        for dtype, (on_trace, off_trace) in curves.items():
            self.assertTrue((on_trace > 0).all())
            numpy.testing.assert_array_equal(off_trace, 0.)
        numpy.testing.assert_allclose(
            curves['float32'][0], curves['float64'][0], rtol=1e-6)

    def test_case_10_mutex_sources(self):
        # the calculator does not use the weights of mutually exclusive
        # sources: such a group is rejected
        group = ('<sourceGroup name="faults" '
                 'tectonicRegion="Active Shallow Crust">')
        dest = self.copy_case(case_10, {'source_model_char.xml': [
            ('id="A"', 'id="fault:0"'), ('id="B"', 'id="fault:1"'),
            (group, group.replace(
                '>', ' src_interdep="mutex" srcs_weights="0.25 0.75">'))]})
        with self.assertRaises(InvalidFile) as ctx:
            self.run_calc(os.path.join(dest, 'job_char.ini'), 'job_char.ini')
        self.assertIn('mutually exclusive', str(ctx.exception))

    def test_case_10_cluster_sources(self):
        # the calculator does not use the occurrence rate of a cluster of
        # sources: such a group is rejected
        group = ('<sourceGroup name="faults" '
                 'tectonicRegion="Active Shallow Crust">')
        dest = self.copy_case(case_10, {'source_model_char.xml': [
            (group, group.replace('>', ' cluster="true" tom="PoissonTOM" '
                                  'occurrence_rate="0.1">'))]})
        with self.assertRaises(InvalidFile) as ctx:
            self.run_calc(os.path.join(dest, 'job_char.ini'), 'job_char.ini')
        self.assertIn('cluster', str(ctx.exception))

    def test_case_4_inferred_rate_from_zero_probability(self):
        # infer_occur_rates = true needs P(no occurrence) > 0
        with self.assertRaises(ValueError) as ctx:
            self.run_case_4([[0., 1.], [.7, .3], [.9, .1]],
                            infer_occur_rates='true')
        self.assertIn('infer_occur_rates = false', str(ctx.exception))

    def test_case_11_colon_convention(self):
        # the same job with the source declared as "fault:17", a fragment of
        # the source "fault" by the colon convention, and applyToSources
        # referring to "fault": the same curves (before, the source got no
        # P(SR) model, +22%)
        self.run_calc(case_11.__file__, 'job.ini')
        ref = self.calc.datastore['hcurves-stats'][0, 0, 0]
        rename = [('id="3"', 'id="fault:17"')]
        dest = self.copy_case(case_11, {
            'source_model_a.xml': rename, 'source_model_b.xml': rename,
            'pfd_logic_tree.xml': [('applyToSources="3"',
                                    'applyToSources="fault"')]})
        self.run_calc(os.path.join(dest, 'job.ini'), 'job.ini')
        numpy.testing.assert_allclose(
            self.calc.datastore['hcurves-stats'][0, 0, 0], ref, rtol=1e-6)


def test_pinned_geometry():
    # a primary surface-rupture branch pinning the dip or the depth of
    # Mammarella et al. (2024) is reported, to be logged by the calculator
    from types import SimpleNamespace
    from openquake.calculators.displacement import pinned_geometry

    def pfd_lt(**extra):
        params = dict(MSR=0, HDD_str='AGG_N', dip_sigma=5., t_d=2.,
                      Zs_sigma=2., t_z=2., **extra)
        return SimpleNamespace(branchsets=[
            SimpleNamespace(
                uncertainty_type='fdhaPrimarySRModel', branches=[
                    SimpleNamespace(
                        branch_id='MA', value=(
                            'Mammarella2024PrimarySR', params)),
                    SimpleNamespace(
                        branch_id='YO', value=(
                            'Youngs2003PrimarySR', {'style': 'all'}))]),
            SimpleNamespace(
                uncertainty_type='fdhaPrimaryFDModel', branches=[
                    SimpleNamespace(
                        branch_id='FD', value=(
                            'Youngs2003PrimaryFD', {'style': 'normal'}))])])

    assert pinned_geometry(pfd_lt()) == []
    assert pinned_geometry(pfd_lt(dip_mu=75., seismothickness=15.)) == [
        ('MA', 'Mammarella2024PrimarySR',
         {'dip_mu': 75., 'seismothickness': 15.})]


def test_visini_branch_segment_sampling_reaches_pipeline():
    # the combined Visini pipeline must use the Rank-2 sampling declared on
    # the secondary_surf_rup branch, not its own "truncated" default
    from types import SimpleNamespace
    from openquake.calculators.displacement import get_adapters

    def selections(**sr_params):
        return {
            'secondary_surf_rup': SimpleNamespace(
                class_name='Visini2025SecondarySR',
                params=dict(style='normal', pixel_size=100, **sr_params)),
            'secondary_surf_displ': SimpleNamespace(
                class_name='Visini2025SecondaryFD',
                params=dict(style='normal', tpfm=1.42, case='case3'))}

    adapters, _ = get_adapters(
        selections(segment_sampling='legacy'), 0., 0.2)
    assert adapters['secondary_combined'].segment_sampling == 'legacy'
    adapters, _ = get_adapters(selections(), 0., 0.2)
    assert adapters['secondary_combined'].segment_sampling == 'truncated'


def test_explicit_rates():
    # exactly 20 occurrences: -log P(no exceedance) = -20 log(1 - q) in both
    # tails (P(no exceedance) = 1e-20 at q = 0.9, where the probability of
    # exceedance rounds to 1), and the cap of to_rates where it is 0
    probs = numpy.zeros(21)
    probs[20] = 1.
    q = numpy.array([[0., 1e-12, .9, .99, 1.]])
    expected = [0., -20 * numpy.log1p(-1e-12), -20 * numpy.log(.1),
                -20 * numpy.log(.01), -numpy.log(1e-45)]
    numpy.testing.assert_allclose(explicit_rates(probs, q)[0], expected,
                                  rtol=1e-12)
    # q = 1 with a positive probability of no occurrence
    numpy.testing.assert_allclose(
        explicit_rates([.3, .7], numpy.ones((1, 1))), [[-numpy.log(.3)]],
        rtol=1e-12)
    # probabilities stored in single precision: exactly 0 where q = 0
    probs32 = numpy.array([.9, .1], numpy.float32)
    assert explicit_rates(probs32, numpy.zeros((1, 3))).tolist() == [[0.] * 3]
