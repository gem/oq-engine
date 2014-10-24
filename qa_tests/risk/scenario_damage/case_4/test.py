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
