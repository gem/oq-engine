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

from nose.plugins.attrib import attr

from openquake.qa_tests_data.classical_risk import (
    case_1, case_2, case_3, case_4, case_5, case_master)
from openquake.baselib.general import writetmp
from openquake.calculators.tests import CalculatorTestCase
from openquake.commonlib.writers import scientificformat
from openquake.calculators.export import export
from openquake.calculators.views import view


class ClassicalRiskTestCase(CalculatorTestCase):

    @attr('qa', 'risk', 'classical_risk')
    def test_case_1(self):
        out = self.run_calc(case_1.__file__, 'job_risk.ini', exports='xml')

        # check loss ratios
        lrs = self.calc.datastore['composite_risk_model/VF/structural']
        got = scientificformat(lrs.mean_loss_ratios, '%.2f')
        self.assertEqual(got, '0.05 0.10 0.20 0.40 0.80')

        # check loss curves
        [fname] = out['loss_curves-rlzs', 'xml']
        self.assertEqualFiles('expected/loss_curves.xml', fname)

        # check loss maps
        clp = self.calc.oqparam.conditional_loss_poes
        fnames = export(('loss_maps-rlzs', 'xml'), self.calc.datastore)
        self.assertEqual(len(fnames), 3)  # for 3 conditional loss poes
        for poe, fname in zip(clp, fnames):
            self.assertEqualFiles('expected/loss_map-poe-%s.xml' % poe, fname)

    @attr('qa', 'risk', 'classical_risk')
    def test_case_2(self):
        out = self.run_calc(case_2.__file__, 'job_risk.ini', exports='xml')
        [fname] = out['loss_curves-rlzs', 'xml']
        self.assertEqualFiles('expected/loss_curves.xml', fname)

        clp = self.calc.oqparam.conditional_loss_poes
        fnames = export(('loss_maps-rlzs', 'xml'), self.calc.datastore)
        self.assertEqual(len(fnames), 1)  # for 1 conditional loss poe
        for poe, fname in zip(clp, fnames):
            self.assertEqualFiles('expected/loss_map-poe-%s.xml' % poe, fname)

    @attr('qa', 'risk', 'classical_risk')
    def test_case_3(self):
        out = self.run_calc(case_3.__file__, 'job.ini', exports='csv')
        [fname] = out['loss_curves-rlzs', 'csv']
        self.assertEqualFiles('expected/loss_curves-000.csv', fname)

    @attr('qa', 'risk', 'classical_risk')
    def test_case_4(self):
        out = self.run_calc(case_4.__file__, 'job_haz.ini,job_risk.ini',
                            exports='csv,xml')
        fnames = export(('loss_maps-rlzs', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/loss_maps-b1,b1.csv', fnames[0])
        self.assertEqualFiles('expected/loss_maps-b1,b2.csv', fnames[1])

        fnames = out['loss_curves-rlzs', 'csv']
        self.assertEqualFiles('expected/loss_curves-000.csv', fnames[0])
        self.assertEqualFiles('expected/loss_curves-001.csv', fnames[1])

        [fname] = export(('loss_maps-stats', 'xml'), self.calc.datastore)
        self.assertEqualFiles('expected/loss_maps-mean-structural.xml', fname)

        [fname] = out['loss_curves-stats', 'xml']
        self.assertEqualFiles('expected/loss_curves-mean-structural.xml',
                              fname)

    # test with 1 hazard site and 2 risk sites using assoc_assets_sites
    @attr('qa', 'risk', 'classical_risk')
    def test_case_5(self):
        # test with different curve resolution for different taxonomies
        self.run_calc(case_5.__file__, 'job_h.ini,job_r.ini')

        # check mean loss curves
        [fname] = export(('loss_curves-stats', 'xml'), self.calc.datastore)
        self.assertEqualFiles('expected/loss_curves-mean.xml', fname)

        # check individual avg losses
        fname = writetmp(view('loss_curves_avg', self.calc.datastore))
        self.assertEqualFiles('expected/loss_curves_avg.txt', fname)

    @attr('qa', 'risk', 'classical_risk')
    def test_case_master(self):
        self.run_calc(case_master.__file__, 'job.ini')
        # TODO: check the expected mean/quantiles curves
