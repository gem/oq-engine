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
                'exposure_data_id', 'dmg_state_id')
        total = models.DmgDistTotal.objects.get(
            dmg_state__risk_calculation=job.risk_calculation)
        return [[[m.value, m.stddev] for m in per_asset],
                [total.mean, total.stddev]]

    def expected_data(self):
        return [[[129.816031875000, 68.8305957840654],
                 [148.677565155000, 145.463557832699],
                 [172.300742141476, 204.843616089138]],
                [450.7943,  389.1273]]
