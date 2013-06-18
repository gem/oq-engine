# Copyright (c) 2013, GEM Foundation.
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


class ScenarioRiskCase3TestCase(risk.End2EndRiskQATestCase):
    hazard_cfg = os.path.join(os.path.dirname(__file__), 'job_haz.ini')
    risk_cfg = os.path.join(os.path.dirname(__file__), 'job_risk.ini')

    output_type = "gmf_scenario"

    @attr('qa', 'risk', 'scenario', 'e2e')
    def test(self):
        self._run_test()

    def actual_data(self, job):
        maps = models.LossMapData.objects.filter(
            loss_map__output__oq_job=job).order_by('asset_ref', 'value')
        agg = models.AggregateLoss.objects.get(output__oq_job=job)
        return [[[m.value, m.std_dev] for m in maps],
                [agg.mean, agg.std_dev]]

    def expected_data(self):
        return [[[137.845249153057, 59.9469210580522],
                 [198.616188792658, 228.997177825263],
                 [246.496563592118, 257.441758287348]],
                [582.958001537833, 352.612171969444]]
