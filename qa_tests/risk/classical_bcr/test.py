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
from qa_tests.risk.classical_risk.test import ClassicalRiskCase1TestCase
from openquake.qa_tests_data.classical_bcr import case_1
from openquake.engine.db import models


class ClassicalBCRCase1TestCase(ClassicalRiskCase1TestCase):
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

    def actual_data(self, job):
        [result] = models.BCRDistributionData.objects.filter(
            bcr_distribution__output__oq_job=job)

        return [result.average_annual_loss_original,
                result.average_annual_loss_retrofitted, result.bcr]

    def expected_data(self):
        return [0.009379, 0.006586, 0.483091]

    def expected_outputs(self):
        return [self.EXPECTED_BCR_DISTRIBUTION]
