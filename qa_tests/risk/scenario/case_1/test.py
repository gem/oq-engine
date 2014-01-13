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
from openquake.engine.tools.import_gmf_scenario import import_gmf_scenario


class ScenarioRiskCase1TestCase(risk.BaseRiskQATestCase):
    output_type = "gmf_scenario"

    @attr('qa', 'risk', 'scenario')
    def test(self):
        self._run_test()

    def get_hazard_job(self):
        job = helpers.get_hazard_job(
            helpers.get_data_path("scenario_hazard/job.ini"))
        fname = self._test_path('gmf_scenario.csv')
        helpers.populate_gmf_data_from_csv(job, fname)
        return job

    def actual_data(self, job):
        maps = models.LossMapData.objects.filter(
            loss_map__output__oq_job=job,
            loss_map__insured=False).order_by('asset_ref', 'value')
        agg = models.AggregateLoss.objects.get(output__oq_job=job,
                                               insured=False)
        insured_maps = models.LossMapData.objects.filter(
            loss_map__output__oq_job=job,
            loss_map__insured=True).order_by('asset_ref', 'value')
        insured_agg = models.AggregateLoss.objects.get(
            output__oq_job=job,
            insured=True)

        return [[[m.value, m.std_dev] for m in maps],
                [agg.mean, agg.std_dev],
                [[m.value, m.std_dev] for m in insured_maps],
                [insured_agg.mean, insured_agg.std_dev]]

    def expected_data(self):
        return [[[440.14707, 182.6159],
                 [432.2254, 186.8644],
                 [180.7175, 92.2122]],
                [1053.09, 246.62],
                [[147.49208753, 141.02819028],
                 [104.85957932, 145.36984417],
                 [76.75091081, 69.96900115]],
                [329.10257766, 193.67786848]]


class ImportGmfScenarioTestCase(risk.BaseRiskQATestCase):
    output_type = "gmf_scenario"

    @attr('qa', 'risk', 'scenario')
    def test(self):
        # check that the imported GMFs can be read by the risk calculator
        self._run_test()

    def get_hazard_job(self):
        with open('gmf-scenario.xml') as data:
            output = import_gmf_scenario(data)
        return output.oq_job
