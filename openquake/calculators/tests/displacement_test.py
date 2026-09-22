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

from openquake.calculators.export import export
from openquake.calculators.tests import CalculatorTestCase
from openquake.qa_tests_data.pfd import case_1, case_2


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