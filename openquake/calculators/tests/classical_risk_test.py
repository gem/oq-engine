# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2025 GEM Foundation
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

from openquake.qa_tests_data.classical_risk import (
    case_2, case_3, case_4, case_5, case_master)
from openquake.calculators.tests import CalculatorTestCase, strip_calc_id
from openquake.calculators.export import export
from openquake.baselib import InvalidFile


class ClassicalRiskTestCase(CalculatorTestCase):

    def test_case_2(self):
        self.run_calc(case_2.__file__, 'job_risk.ini', exports='csv')
        [fname] = export(('loss_curves/rlz-0', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/loss_curves.csv', fname)

        [fname] = export(('loss_maps-stats', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/loss_maps.csv', fname)

        [fname] = export(('avg_losses-stats', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/avg_losses-mean.csv', fname)

    def test_prob_above1(self):
        with self.assertRaises(InvalidFile) as ctx:
            self.run_calc(
                case_2.__file__, 'job_risk-prob_above1.ini')
        self.assertIn('contains probabilities > 1', str(ctx.exception))

    def test_prob_below0(self):
        with self.assertRaises(InvalidFile) as ctx:
            self.run_calc(
                case_2.__file__, 'job_risk-prob_below0.ini')
        self.assertIn('contains probabilities < 0', str(ctx.exception))

    def test_case_3(self):
        self.run_calc(case_3.__file__, 'job.ini', exports='csv')
        [fname] = export(('loss_curves/rlz-0/sid-0', 'csv'),
                         self.calc.datastore)
        self.assertEqualFiles('expected/loss_curves-000.csv', fname)
        [fname] = export(('loss_curves/rlz-0/ref-a8', 'csv'),
                         self.calc.datastore)
        self.assertEqualFiles('expected/loss_curves-ref-a8-000.csv', fname)

    def test_case_4(self):
        self.run_calc(case_4.__file__, 'job_haz.ini,job_risk.ini',
                      exports='csv')

        fnames = export(('loss_maps-rlzs', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/loss_maps-b1,b1.csv', fnames[0])
        self.assertEqualFiles('expected/loss_maps-b1,b2.csv', fnames[1])

        fnames = export(('loss_curves/rlzs/sid-0', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/loss_curves-000.csv', fnames[0])
        self.assertEqualFiles('expected/loss_curves-001.csv', fnames[1])

        fnames = export(('loss_maps-stats', 'csv'), self.calc.datastore)
        self.assertEqual(len(fnames), 1)  # mean
        self.assertEqualFiles('expected/loss_maps-mean.csv', fnames[0])

        [fname] = export(('loss_curves/mean/sid-1', 'csv'),
                         self.calc.datastore)
        self.assertEqualFiles('expected/loss_curves-sid-1-mean.csv',
                              fname)

    # test with 1 hazard site and 2 risk sites using assoc_assets_sites
    def test_case_5(self):
        # test with different curve resolution for different taxonomies
        self.run_calc(case_5.__file__, 'job_h.ini,job_r.ini')

        # check mean loss curves
        [fname] = export(('loss_curves/mean', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/loss_curves-mean.csv', fname)

        # check avg losses
        [fname] = export(('avg_losses-stats', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/avg_losses-mean.csv', fname)
        fnames = export(('avg_losses-rlzs', 'csv'), self.calc.datastore)
        assert len(fnames) == 4  # there are 4 realizations
        self.assertEqualFiles('expected/avg_losses-000.csv', fnames[0])

    def test_case_master(self):
        self.run_calc(case_master.__file__, 'job.ini')

        # checking custom_site_id in UHS curves
        [mean, _q15] = export(('uhs', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/uhs-mean.csv', mean, delta=1E-5)

        # checking the avg_losses
        [_, fname] = export(('avg_losses-stats', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/' + strip_calc_id(fname),
                              fname, delta=1E-5)

        # checking the loss maps
        fnames = export(('loss_maps-stats', 'csv'), self.calc.datastore)
        assert fnames  # sanity check
        for fname in fnames:
            self.assertEqualFiles(  # very sensitive to shapely version
                'expected/' + strip_calc_id(fname), fname, delta=1E-3)

        # exported the npz, not checking the content
        for kind in ('rlzs', 'stats'):
            [fname] = export(('loss_maps-' + kind, 'npz'), self.calc.datastore)
            print('Generated ' + fname)
