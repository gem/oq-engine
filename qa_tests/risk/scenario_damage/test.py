# Copyright (c) 2010-2014, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os
import copy
from nose.plugins.attrib import attr

from qa_tests import risk
from openquake.qa_tests_data.scenario_damage import (
    case_1, case_2, case_3, case_4)
from openquake.engine.tests.utils import helpers
from openquake.engine.db import models


class ScenarioDamageTestCase(risk.BaseRiskQATestCase):
    output_type = "gmf_scenario"

    def _test(self, module):
        testcase = copy.copy(self)
        testcase.module = module
        job = testcase._run_test()
        testcase.compare_xml_outputs(
            job,
            ['expected/dmg_dist_per_asset.xml',
             'expected/collapse_map.xml',
             'expected/dmg_dist_per_taxonomy.xml',
             'expected/dmg_dist_total.xml'])

    def get_hazard_job(self):
        job = helpers.get_job(
            helpers.get_data_path("scenario_hazard/job.ini"))
        fname = os.path.join(os.path.dirname(case_1.__file__),
                             'gmf_scenario.csv')
        helpers.create_gmf_from_csv(job, fname, 'gmf_scenario')
        return job

    def test_case_1(self):
        self._test(case_1)

    def test_case_2(self):
        self._test(case_2)

    def test_case_3(self):
        self._test(case_3)


# FIXME(lp). This is a regression test meant to exercise the sd-imt
# logic in the SR calculator. Data has not been validated
class ScenarioDamageRiskCase4TestCase(risk.FixtureBasedQATestCase):
    module = case_4
    output_type = 'gmf_scenario'
    hazard_calculation_fixture = 'Scenario Damage QA Test 4'

    @attr('qa', 'risk', 'scenario_damage')
    def test(self):
        self._run_test()

    def actual_data(self, job):
        per_asset = models.DmgDistPerAsset.objects.filter(
            dmg_state__risk_calculation=job).order_by(
            'exposure_data', 'dmg_state')
        totals = models.DmgDistTotal.objects.filter(
            dmg_state__risk_calculation=job).order_by(
            'dmg_state')
        data = [[[m.mean, m.stddev] for m in per_asset],
                [[total.mean, total.stddev] for total in totals]]
        return data

    def expected_data(self):
        return [
            [[2665.9251, 385.4088], [320.9249, 363.2749],
             [13.1498, 23.8620], [208.2695, 307.3967],
             [533.6744, 177.1909], [258.0559, 251.5760],
             [638.7025, 757.9946], [670.4166, 539.3635],
             [690.8808, 883.1827]],
            [[3512.8972, 1239.1419], [1525.0160, 685.8950],
             [962.0867, 1051.8785]]]
