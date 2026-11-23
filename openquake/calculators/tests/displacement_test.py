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

import numpy

from openquake.calculators.export import export
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

