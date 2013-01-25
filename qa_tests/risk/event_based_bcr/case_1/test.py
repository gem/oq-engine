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

from openquake.db import models


class EventBasedRiskCase1TestCase(risk.BaseRiskQATestCase):
    cfg = os.path.join(os.path.dirname(__file__), 'job.ini')

    EXPECTED_BCR_DISTRIBUTION = """<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
  <bcrMap interestRate="0.05" assetLifeExpectancy="40.0"
          sourceModelTreePath="test_sm" gsimTreePath="test_gsim" unit="USD">
    <node>
      <gml:Point>
        <gml:pos>-122.0 38.225</gml:pos>
      </gml:Point>
      <bcr assetRef="a1" ratio="77.9106047897"
           aalOrig="1.50174981661" aalRetr="1.05122487163"/>
    </node>
    <node>
      <gml:Point>
        <gml:pos>-120.0 37.225</gml:pos>
      </gml:Point>
      <bcr assetRef="a2" ratio="54.1889945306"
           aalOrig="2.08901760725" aalRetr="1.46231232508"/>
      <bcr assetRef="a3" ratio="52.4972213244"
           aalOrig="2.02379875523" aalRetr="1.41665912866"/>
    </node>
  </bcrMap>
</nrml>
"""

    @noseattr('qa', 'risk', 'event_based_bcr')
    def test(self):
        self._run_test()

    def hazard_id(self):
        job = helpers.get_hazard_job(
            helpers.demo_file("event_based_hazard/job.ini"))

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
                    is_complete=False, total_items=1, completed_items=1),
                complete_logic_tree_gmf=False),
            investigation_time=hc.investigation_time,
            ses_ordinal=1,
            complete_logic_tree_gmf=False)

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

        return gmf_set.gmf_collection.output.id

    def actual_data(self, job):
        return [(result.average_annual_loss_original,
                 result.average_annual_loss_retrofitted, result.bcr)
                for result in models.BCRDistributionData.objects.filter(
                    bcr_distribution__output__oq_job=job).order_by(
                        'asset_ref')]

    def expected_data(self):
        return [[1.50174982, 1.05122487, 77.91060479],
                [2.08901761, 1.46231233, 54.18899453],
                [2.02379876, 1.41665913, 52.49722132]]

    def expected_outputs(self):
        return [self.EXPECTED_BCR_DISTRIBUTION]
