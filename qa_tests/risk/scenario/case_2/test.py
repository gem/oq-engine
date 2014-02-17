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
        helpers.populate_gmf_data_from_csv(job, fname)
        return job

    def actual_data(self, job):
        maps = models.LossMapData.objects.filter(
            loss_map__output__oq_job=job).order_by('asset_ref', 'value')
        agg = models.AggregateLoss.objects.get(output__oq_job=job)
        return [[[m.value, m.std_dev] for m in maps],
                [agg.mean, agg.std_dev]]

    def expected_data(self):
        return [[[522.40316578, 249.26357273],
                 [512.3892894, 347.75665613],
                 [200.21969199, 95.12689831]],
                [1235.01214717, 503.25181506]]
