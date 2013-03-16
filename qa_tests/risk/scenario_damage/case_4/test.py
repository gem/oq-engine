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
        return [[[2874.69636761608, 197.792901143125],
                 [122.855791108662, 191.068095747441],
                 [2.44784127525955, 6.96559410484012],
                 [227.163109698912, 409.831523111090],
                 [416.615638168489, 332.480242607810],
                 [356.221252132599, 339.438202966314],
                 [654.287293017278, 766.567549865467],
                 [912.676055800385, 636.202291872638],
                 [433.036651182337, 615.022456277666]],
                [[3756.14677033227, 1270.35632891829],
                 [1452.14748507754, 887.121887430101],
                 [791.705744590195, 946.270780416918]]]
