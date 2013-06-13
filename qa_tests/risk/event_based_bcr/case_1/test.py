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

import os
import csv
import numpy

from nose.plugins.attrib import attr as noseattr

from qa_tests import risk
from tests.utils import helpers

from openquake.engine.db import models


# FIXME(lp). This is a regression test. Data has not been validated
# by an alternative reliable implemantation


class EventBasedBCRCase1TestCase(risk.BaseRiskQATestCase):
    risk_cfg = os.path.join(os.path.dirname(__file__), 'job.ini')
    output_type = "gmf"

    check_exports = False

    @noseattr('qa', 'risk', 'event_based_bcr')
    def test(self):
        self._run_test()

    def get_hazard_job(self):
        job = helpers.get_hazard_job(
            helpers.get_data_path("event_based_hazard/job.ini"))

        job.hazard_calculation = models.HazardCalculation.objects.create(
            owner=job.hazard_calculation.owner,
            truncation_level=job.hazard_calculation.truncation_level,
            maximum_distance=job.hazard_calculation.maximum_distance,
            intensity_measure_types_and_levels=(
                job.hazard_calculation.intensity_measure_types_and_levels),
            calculation_mode="event_based",
            investigation_time=50,
            ses_per_logic_tree_path=1)
        job.save()
        hc = job.hazard_calculation

        gmf_set = models.GmfSet.objects.create(
            gmf_collection=models.GmfCollection.objects.create(
                output=models.Output.objects.create_output(
                    job, "Test Hazard output", "gmf"),
                lt_realization=models.LtRealization.objects.create(
                    hazard_calculation=job.hazard_calculation,
                    ordinal=1, seed=1, weight=None,
                    sm_lt_path="test_sm", gsim_lt_path="test_gsim",
                    is_complete=False, total_items=1, completed_items=1)),
            investigation_time=hc.investigation_time,
            ses_ordinal=1)

        with open(os.path.join(
                os.path.dirname(__file__), 'gmf.csv'), 'rb') as csvfile:
            gmfreader = csv.reader(csvfile, delimiter=',')
            locations = gmfreader.next()

            for i, gmvs in enumerate(
                    numpy.array([[float(x) * 10 for x in row]
                                 for row in gmfreader]).transpose()):
                models.Gmf.objects.create(
                    gmf_set=gmf_set,
                    imt="PGA", gmvs=gmvs,
                    result_grp_ordinal=1,
                    location="POINT(%s)" % locations[i])

        return job

    def actual_data(self, job):
        return [(result.average_annual_loss_original,
                 result.average_annual_loss_retrofitted, result.bcr)
                for result in models.BCRDistributionData.objects.filter(
                    bcr_distribution__output__oq_job=job).order_by(
                        'asset_ref')]

    def expected_data(self):
        return [[1.37096021, 0.95967214, 71.12525504],
                [0.7280975, 0.50966825, 18.88680667],
                [2.08079383, 1.45655568, 53.97567025]]
