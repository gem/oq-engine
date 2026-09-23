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
from openquake.qa_tests_data.pfd import case_1, case_2, case_3, case_4
from openquake.qa_tests_data.pfd import case_5, case_6, case_7, case_8


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
        # only the surface-reaching ruptures are used: 10 of 15 (the engine
        # source has 5 buried down-dip floats, dropped by the surface-rupture
        # depth tolerance), matching oq-pfdha
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
        # in the logic tree; the reference is oq-pfdha's `job_kuehn2024`
        # demo, regenerated with the current oq-pfdha (the checked-in
        # out/aggregate_hazard.csv was stale). The mean epistemic reduction
        # reproduces it to a few 1e-5 relative.
        self.run_calc(case_5.__file__, 'job.ini')
        dstore = self.calc.datastore
        hcurves = dstore['hcurves-rlzs'][0, 0, 0, :]
        self.assertEqual(hcurves.shape, (18,))
        expected = numpy.array([
            0.011072213972454593, 0.011070271216337666,
            0.01106091761479565, 0.011046256358457199,
            0.01102900767605022, 0.010966027581042233,
            0.010864239079824886, 0.010719145882599649,
            0.010561764070417123, 0.010227437275303472,
            0.009197341447809022, 0.007933601570482441,
            0.0066067101704247125, 0.005533482411750099,
            0.0016196042822896285, 0.0005844579327410797,
            0.00019667554911984074, 7.728637804974222e-05])
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