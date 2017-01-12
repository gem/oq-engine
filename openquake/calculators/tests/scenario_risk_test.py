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

from openquake.qa_tests_data.scenario_risk import (
    case_1, case_2, case_2d, case_1g, case_3, case_4, case_5, occupants,
    case_6a, case_master)

from openquake.baselib.general import writetmp
from openquake.calculators.tests import CalculatorTestCase
from openquake.calculators.views import view
from openquake.calculators.export import export


class ScenarioRiskTestCase(CalculatorTestCase):

    @attr('qa', 'risk', 'scenario_risk')
    def test_case_1(self):
        out = self.run_calc(case_1.__file__, 'job_risk.ini', exports='csv')
        [fname] = out['agglosses-rlzs', 'csv']
        self.assertEqualFiles('expected/agg.csv', fname)

        # check the exported GMFs
        [fname] = export(('gmf_data', 'csv'), self.calc.datastore)
        self.assertEqualFiles('expected/gmf-FromFile-PGA.csv', fname)

    @attr('qa', 'risk', 'scenario_risk')
    def test_case_2(self):
        out = self.run_calc(case_2.__file__, 'job_risk.ini', exports='csv')
        [fname] = out['agglosses-rlzs', 'csv']
        self.assertEqualFiles('expected/agg.csv', fname)

    @attr('qa', 'risk', 'scenario_risk')
    def test_case_2d(self):
        # time_event not specified in job_h.ini but specified in job_r.ini
        out = self.run_calc(case_2d.__file__, 'job_h.ini,job_r.ini',
                            exports='csv')
        [fname] = out['losses_by_asset', 'csv']
        self.assertEqualFiles('expected/losses_by_asset.csv', fname)

    @attr('qa', 'risk', 'scenario_risk')
    def test_case_3(self):
        out = self.run_calc(case_3.__file__, 'job.ini', exports='csv')

        [fname] = out['losses_by_asset', 'csv']
        self.assertEqualFiles('expected/asset-loss.csv', fname)

        [fname] = out['agglosses-rlzs', 'csv']
        self.assertEqualFiles('expected/agg_loss.csv', fname)

    @attr('qa', 'risk', 'scenario_risk')
    def test_case_4(self):
        # this test is sensitive to the ordering of the epsilons
        # in openquake.riskinput.make_eps
        out = self.run_calc(case_4.__file__, 'job.ini', exports='csv')
        fname = writetmp(view('totlosses', self.calc.datastore))
        self.assertEqualFiles('expected/totlosses.txt', fname)

        [fname] = out['agglosses-rlzs', 'csv']
        self.assertEqualFiles('expected/agglosses.csv', fname)

    @attr('qa', 'risk', 'scenario_risk')
    def test_occupants(self):
        out = self.run_calc(occupants.__file__, 'job_haz.ini,job_risk.ini',
                            exports='csv,xml')

        [fname] = out['losses_by_asset', 'xml']
        self.assertEqualFiles('expected/loss_map.xml', fname)

        [fname] = out['losses_by_asset', 'csv']
        self.assertEqualFiles('expected/asset-loss.csv', fname)

        [fname] = out['agglosses-rlzs', 'csv']
        self.assertEqualFiles('expected/agg_loss.csv', fname)

    @attr('qa', 'risk', 'scenario_risk')
    def test_case_5(self):
        # case with site model
        out = self.run_calc(case_5.__file__, 'job.ini', exports='csv')
        [fname] = out['losses_by_asset', 'csv']
        self.assertEqualFiles('expected/losses_by_asset.csv', fname)

    @attr('qa', 'risk', 'scenario_risk')
    def test_case_6a(self):
        # case with two gsims
        out = self.run_calc(case_6a.__file__, 'job_haz.ini,job_risk.ini',
                            exports='csv')
        f1, f2 = out['agglosses-rlzs', 'csv']
        self.assertEqualFiles('expected/agg-gsimltp_b1_structural.csv', f1)
        self.assertEqualFiles('expected/agg-gsimltp_b2_structural.csv', f2)

        # testing the totlosses view
        dstore = self.calc.datastore
        fname = writetmp(view('totlosses', dstore))
        self.assertEqualFiles('expected/totlosses.txt', fname)

        # testing the npz export runs
        export(('all_losses-rlzs', 'npz'), self.calc.datastore)

    @attr('qa', 'risk', 'scenario_risk')
    def test_case_1g(self):
        out = self.run_calc(case_1g.__file__, 'job_haz.ini,job_risk.ini',
                            exports='csv')
        [fname] = out['agglosses-rlzs', 'csv']
        self.assertEqualFiles('expected/agg-gsimltp_@.csv', fname)

    @attr('qa', 'risk', 'scenario_risk')
    def test_case_master(self):
        self.run_calc(case_master.__file__, 'job.ini', exports='npz')
