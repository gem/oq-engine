# Copyright (c) 2010-2013, GEM Foundation.
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

from nose.plugins.attrib import attr

from qa_tests import risk
from openquake.engine.db import models


# FIXME(lp). This is a regression testing meant to exercize the sd-imt
# logic in the SR calculator. Data has not been validated


class ScenarioDamageRiskCase4TestCase(risk.End2EndRiskQATestCase):
    hazard_cfg = os.path.join(os.path.dirname(__file__), 'job_haz.ini')
    risk_cfg = os.path.join(os.path.dirname(__file__), 'job_damage.ini')

    @attr('qa', 'risk', 'scenario_damage', 'e2e')
    def test(self):
        self._run_test()

    def hazard_id(self):
        return models.Output.objects.latest('last_update').id

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
        return [[[2812.89159829, 305.30774015],
                 [176.46099651, 260.49485714],
                 [10.6474052, 67.91431319],
                 [170.586342372, 269.649798893],
                 [429.890862122, 293.620740973],
                 [399.522795506, 379.53932617],
                 [613.816376078, 692.704382194],
                 [791.456779538, 539.202644042],
                 [594.726844384, 704.006611109]],
                [[3597.29431674, 799.587511177],
                 [1397.80863817, 652.81154025],
                 [1004.89704509, 813.235867669]]]
