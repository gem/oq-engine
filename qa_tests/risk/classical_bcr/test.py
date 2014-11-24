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
from openquake.qa_tests_data.classical_bcr import case_1
from openquake.engine.tests.utils import helpers

from openquake.engine.db import models


class ClassicalBCRCase1TestCase(risk.BaseRiskQATestCase):
    module = case_1

    EXPECTED_BCR_DISTRIBUTION = """<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
  <bcrMap interestRate="0.05" assetLifeExpectancy="40.0" statistics="mean" unit="USD" lossType="structural">
    <node>
      <gml:Point>
        <gml:pos>1.0 1.0</gml:pos>
      </gml:Point>
      <bcr assetRef="a1" ratio="0.486045805147" aalOrig="0.00939290422672" aalRetr="0.00658230148253"/>
    </node>
  </bcrMap>
</nrml>
    """

    @attr('qa', 'risk', 'classical_bcr')
    def test(self):
        self._run_test()

    def get_hazard_job(self):
        job = helpers.get_job(
            helpers.get_data_path("simple_fault_demo_hazard/job.ini"))

        hazard_curve = [
            (0.001, 0.0398612669790014),
            (0.01, 0.039861266979001400), (0.05, 0.039728757480298900),
            (0.10, 0.029613426625612500), (0.15, 0.019827328756491600),
            (0.20, 0.013062270161451900), (0.25, 0.008655387950000430),
            (0.30, 0.005898520593689670), (0.35, 0.004061698589511780),
            (0.40, 0.002811727179526820), (0.45, 0.001995117417776690),
            (0.50, 0.001358705972845710), (0.55, 0.000989667841573727),
            (0.60, 0.000757544444296432), (0.70, 0.000272824002045979),
            (0.80, 0.00), (0.9, 0.00), (1.0, 0.00)]

        models.HazardSite.objects.create(
            hazard_calculation=job, location="POINT(1 1)")
        models.HazardCurveData.objects.create(
            hazard_curve=models.HazardCurve.objects.create(
                output=models.Output.objects.create_output(
                    job, "Test Hazard curve", "hazard_curve"),
                investigation_time=50, imt="PGA",
                imls=[hz[0] for hz in hazard_curve], statistics="mean"),
            poes=[hz[1] for hz in hazard_curve],
            location="POINT(1 1)")

        return job

    def actual_data(self, job):
        [result] = models.BCRDistributionData.objects.filter(
            bcr_distribution__output__oq_job=job)

        return [result.average_annual_loss_original,
                result.average_annual_loss_retrofitted, result.bcr]

    def expected_data(self):
        return [0.009379, 0.006586, 0.483091]

    def expected_outputs(self):
        return [self.EXPECTED_BCR_DISTRIBUTION]
