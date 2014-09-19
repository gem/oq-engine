# Copyright (c) 2014, GEM Foundation.
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

from nose.plugins.attrib import attr

from qa_tests import risk
from openquake.engine.db import models


# FIXME(lp). This is a regression test meant to exercise the sd-imt
# logic in the SR calculator. Data has not been validated


class ScenarioDamageRiskCase4TestCase(risk.FixtureBasedQATestCase):
    output_type = 'gmf_scenario'
    hazard_calculation_fixture = 'Scenario Damage QA Test 4'

    @attr('qa', 'risk', 'scenario_damage')
    def test(self):
        self._run_test()

    def actual_data(self, job):
        per_asset = models.DmgDistPerAsset.objects.filter(
            dmg_state__risk_calculation=job.risk_calculation).order_by(
            'exposure_data', 'dmg_state')
        totals = models.DmgDistTotal.objects.filter(
            dmg_state__risk_calculation=job.risk_calculation).order_by(
            'dmg_state')
        data = [[[m.mean, m.stddev] for m in per_asset],
                [[total.mean, total.stddev] for total in totals]]
        return data

    def expected_data(self):
        return [
            [[2865.56659994412, 251.75309801695], [131.153758939588, 244.490527409288],
             [3.2796411162954, 7.28196701654181], [208.269578176731, 307.396726473713],
             [533.674469271356, 177.190914484958], [258.055952551913, 251.576066029219],
             [315.97214788513, 499.175873518367], [882.004283952979, 538.955224664139],
             [802.023568161892, 778.670960533344]],
            [[3389.80832600598, 441.45241318856], [1546.83251216392, 646.854021137942],
             [1063.3591618301, 862.120309729941]]]

