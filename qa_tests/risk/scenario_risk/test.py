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
from openquake.qa_tests_data.scenario_risk import (
    case_1, case_2, case_3, occupants)
from openquake.engine.tests.utils import helpers
from openquake.engine.db import models
from openquake.engine.utils import config


class ScenarioRiskCase1TestCase(risk.BaseRiskQATestCase):
    module = case_1
    output_type = "gmf_scenario"

    @attr('qa', 'risk', 'scenario')
    def test(self):
        with config.context('celery', concurrent_tasks=1):
            self._run_test()
        with config.context('celery', concurrent_tasks=10):
            self._run_test()

    def get_hazard_job(self):
        job = helpers.get_job(
            helpers.get_data_path("scenario_hazard/job.ini"))
        fname = self._test_path('gmf_scenario.csv')
        helpers.create_gmf_from_csv(job, fname, 'gmf_scenario')
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

        data = [[[m.value, m.std_dev] for m in maps],
                [agg.mean, agg.std_dev],
                [[m.value, m.std_dev] for m in insured_maps],
                [insured_agg.mean, insured_agg.std_dev]]
        return data

    def expected_data(self):
        return [[[440.14707, 182.6159],
                 [432.2254, 186.8644],
                 [180.7175, 92.2122]],
                [1053.09, 246.62],
                [[147.49208753, 141.02819028],
                 [104.85957932, 145.36984417],
                 [76.75091081, 69.96900115]],
                [329.10257766, 193.67786848]]


class ScenarioRiskCase2TestCase(risk.BaseRiskQATestCase):
    module = case_2
    output_type = "gmf_scenario"

    @attr('qa', 'risk', 'scenario')
    def test(self):
        self._run_test()

    def get_hazard_job(self):
        job = helpers.get_job(
            helpers.get_data_path("scenario_hazard/job.ini"),
            number_of_ground_motion_fields=1000)
        fname = self._test_path('gmf_scenario.csv')
        helpers.create_gmf_from_csv(job, fname, 'gmf_scenario')
        return job

    def actual_data(self, job):
        maps = models.LossMapData.objects.filter(
            loss_map__output__oq_job=job).order_by('asset_ref', 'value')
        agg = models.AggregateLoss.objects.get(output__oq_job=job)
        data = [[[m.value, m.std_dev] for m in maps],
                [agg.mean, agg.std_dev]]
        return data

    def expected_data(self):
        return [[[523.06275339, 248.83131322],
                 [500.83619571, 324.42264285],
                 [200.3348642,  96.17884412]],
                [1224.23381329, 478.73144303]]


class ScenarioRiskCase3TestCase(risk.FixtureBasedQATestCase):
    module = case_3
    hazard_calculation_fixture = 'Scenario QA Test 3'

    @attr('qa', 'risk', 'scenario')
    def test(self):
        self._run_test()

    def actual_data(self, job):
        maps = models.LossMapData.objects.filter(
            loss_map__output__oq_job=job).order_by('asset_ref', 'value')
        agg = models.AggregateLoss.objects.get(output__oq_job=job)
        data = [[[m.value, m.std_dev] for m in maps],
                [agg.mean, agg.std_dev]]
        return data

    def expected_data(self):
        return [[[138.78573075, 58.27789895],
                 [196.7998648, 228.41381954],
                 [252.37890689, 264.81701577]],
                [587.96450244, 358.39744028]]


class ScenarioOccupantsQATestCase1(risk.FixtureBasedQATestCase):
    module = occupants
    output_type = "gmf_scenario"
    hazard_calculation_fixture = 'Scenario QA Test for occupants'

    @attr('qa', 'risk', 'scenario')
    def test(self):
        self._run_test()

    def actual_data(self, job):
        latest_loss_map = job.output_set.filter(
            output_type="loss_map", loss_map__loss_type="fatalities").latest(
            'last_update').loss_map
        latest_aggregated = job.output_set.filter(
            output_type="aggregate_loss",
            aggregate_loss__loss_type="fatalities").latest(
            'last_update').aggregate_loss

        data = [(d.value, d.std_dev)
                for d in latest_loss_map.lossmapdata_set.all().order_by(
                    'asset_ref')] + [
            (latest_aggregated.mean, latest_aggregated.std_dev)]
        return data

    def expected_data(self):
        return [(0.36863306563175, 0.198942735032192),
                (1.58950924789158, 1.8570835311939),
                (1.12788692684151, 0.698151682472273),
                (3.08602924036484, 1.97594906538496)]

# For NIGHT:

# Asset 1
# Mean: 0.8981603187500
# Std Dev: 0.479301017326327

# Asset 2
# Mean: 1.67389744650000
# Std Dev: 1.64243715167681

# Asset 3
# Mean: 1.60533374061429
# Std Dev: 1.13698143346693

# Mean: 4.1774
# Std Dev: 3.1036
