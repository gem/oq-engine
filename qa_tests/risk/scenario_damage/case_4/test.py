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
        return [[[m.mean, m.stddev] for m in per_asset],
                [[total.mean, total.stddev] for total in totals]]

    def expected_data(self):
        return [[[2831.39440276538, 272.496770998072],
                 [161.947302372973, 249.774966981951],
                 [6.65829486164962, 29.46078616569],
                 [160.845510534195, 260.559970809904],
                 [428.273449106381, 290.835857759211],
                 [410.881040359423, 378.302327897718],
                 [516.766483950188, 646.868485847065],
                 [777.664421126009, 535.83594187711],
                 [705.569094923804, 743.547507821238]],
                [[3509.00639724976, 741.459174207617],
                 [1367.88517260537, 666.080418405019],
                 [1123.10843014487, 836.390985994778]]]
