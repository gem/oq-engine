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


class ScenarioRiskCase3TestCase(risk.FixtureBasedQATestCase):
    hazard_calculation_fixture = 'Scenario QA Test 3'

    @attr('qa', 'risk', 'scenario')
    def test(self):
        self._run_test()

    def actual_data(self, job):
        maps = models.LossMapData.objects.filter(
            loss_map__output__oq_job=job).order_by('asset_ref', 'value')
        agg = models.AggregateLoss.objects.get(output__oq_job=job)
        return [[[m.value, m.std_dev] for m in maps],
                [agg.mean, agg.std_dev]]

    def expected_data(self):
        return [[[138.78573075, 58.27789895],
                 [196.7998648, 228.41381954],
                 [252.37890689, 264.81701577]],
                [587.96450244, 358.39744028]]
