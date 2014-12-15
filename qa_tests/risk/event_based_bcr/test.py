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

from nose.plugins.attrib import attr as noseattr

from qa_tests import risk
from openquake.qa_tests_data.event_based_bcr import case_1
from openquake.engine.tests.utils import helpers

from openquake.engine.db import models


# FIXME(lp). This is a regression test. Data has not been validated
# by an alternative reliable implemantation
class EventBasedBCRCase1TestCase(risk.BaseRiskQATestCase):
    module = case_1

    output_type = "gmf"

    @noseattr('qa', 'risk', 'event_based_bcr')
    def test(self):
        self._run_test()

    def get_hazard_job(self):
        job = helpers.get_job(
            helpers.get_data_path("event_based_hazard/job.ini"),
            region_grid_spacing='0', ses_per_logic_tree_path='1')
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
        return [(0.2311358, 0.0, 39.970994),
                (0.3344297, 0.0, 28.916953),
                (0.2479981, 0.0, 21.443528)]
