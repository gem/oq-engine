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
from openquake.qa_tests_data.pfd import case_1, case_2, case_3


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