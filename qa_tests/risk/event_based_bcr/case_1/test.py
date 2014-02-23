# Copyright (c) 2010-2012, GEM Foundation.
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

from nose.plugins.attrib import attr as noseattr

from qa_tests import risk
from openquake.engine.tests.utils import helpers

from openquake.engine.db import models


# FIXME(lp). This is a regression test. Data has not been validated
# by an alternative reliable implemantation


class EventBasedBCRCase1TestCase(risk.BaseRiskQATestCase):
    output_type = "gmf"

    check_exports = False

    @noseattr('qa', 'risk', 'event_based_bcr')
    def test(self):
        self._run_test()

    def get_hazard_job(self):
        job = helpers.get_job(
            helpers.get_data_path("event_based_hazard/job.ini"))

        job.hazard_calculation = models.HazardCalculation.objects.create(
            truncation_level=job.hazard_calculation.truncation_level,
            maximum_distance=job.hazard_calculation.maximum_distance,
            intensity_measure_types_and_levels=(
                job.hazard_calculation.intensity_measure_types_and_levels),
            calculation_mode="event_based",
            investigation_time=50,
            ses_per_logic_tree_path=1)
        job.save()

        helpers.create_gmf_from_csv(job, self._test_path('gmf.csv'))

        return job

    def actual_data(self, job):
        data = [(result.average_annual_loss_original,
                 result.average_annual_loss_retrofitted, result.bcr)
                for result in models.BCRDistributionData.objects.filter(
                    bcr_distribution__output__oq_job=job).order_by(
                        'asset_ref')]
        return data

    def expected_data(self):
        return [
            [0.15280346, 0., 26.42475147],
            [0.31141922, 0., 26.92732075],
            [0.39231522, 0., 33.92211259]]
