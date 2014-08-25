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

from nose.plugins.attrib import attr

from qa_tests import risk
from openquake.engine.tests.utils import helpers
from openquake.engine.db import models


class ScenarioRiskCase2TestCase(risk.BaseRiskQATestCase):
    output_type = "gmf_scenario"

    @attr('qa', 'risk', 'scenario')
    def test(self):
        self._run_test()

    def get_hazard_job(self):
        job = helpers.get_job(
            helpers.get_data_path("scenario_hazard/job.ini"))
        fname = self._test_path('gmf_scenario.csv')
        helpers.create_gmf_from_csv(job, fname, 'gmf_scenario')
        # this is needed to make happy the GetterBuilder
        job.hazard_calculation.number_of_ground_motion_fields = 1000
        job.hazard_calculation.save()
        return job

    def actual_data(self, job):
        maps = models.LossMapData.objects.filter(
            loss_map__output__oq_job=job).order_by('asset_ref', 'value')
        agg = models.AggregateLoss.objects.get(output__oq_job=job)
        data = [[[m.value, m.std_dev] for m in maps],
                [agg.mean, agg.std_dev]]
        return data

    def expected_data(self):
        return [[[522.675485, 248.86320],
                 [516.1156, 369.162],
                 [200.0154, 94.8534]],
                [1238.806, 519.7878]]
