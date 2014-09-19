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
            [[2665.92514738795, 385.408846601969], [320.924965874035, 363.274973366753],
             [13.1498867380187, 23.8620047204362], [208.269578176731, 307.396726473713],
             [533.674469271356, 177.190914484958], [258.055952551913, 251.576066029219],
             [638.702514496033, 757.994603683792], [670.416600459505, 539.363527776893],
             [690.880885044462, 883.18277798177]],
            [[3512.89724006071, 1239.14198904676], [1525.0160356049, 685.895079593009],
             [962.086724334393, 1051.8785015279]]]


