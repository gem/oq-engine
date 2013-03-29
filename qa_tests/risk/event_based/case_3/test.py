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


from nose.plugins.attrib import attr as noseattr

from qa_tests import risk

from openquake.engine.db import models


class EventBasedRiskCase3TestCase(risk.End2EndRiskQATestCase):
    hazard_cfg = os.path.join(os.path.dirname(__file__), 'job_haz.ini')
    risk_cfg = os.path.join(os.path.dirname(__file__), 'job_risk.ini')

    EXPECTED_LOSS_FRACTION = """<nrml xmlns:gml="http://www.opengis.net/gml"
    xmlns="http://openquake.org/xmlns/nrml/0.4">
  <lossFraction investigationTime="50.00" poE="0.1000"
                sourceModelTreePath="b1" gsimTreePath="b1"
                lossCategory="buildings" unit="USD" variable="taxonomy">
    <total/>
    <map>
      <node lon="80.317596" lat="28.87">
        <bin value="A" absoluteLoss="8.1652e+07" fraction="0.46765"/>
        <bin value="UFB" absoluteLoss="3.1436e+07" fraction="0.18005"/>
        <bin value="DS" absoluteLoss="4.7710e+07" fraction="0.27325"/>
        <bin value="W" absoluteLoss="1.3432e+07" fraction="0.07693"/>
        <bin value="RC" absoluteLoss="3.6983e+05" fraction="0.00212"/>
      </node>
    </map>
  </lossFraction>
</nrml>"""

    @noseattr('qa', 'risk', 'event_based', 'e2e')
    def test(self):
        self._run_test()

    def hazard_id(self):
        return models.Output.objects.latest('last_update').id

    def actual_xml_outputs(self, job):
        return models.Output.objects.filter(
            oq_job=job, output_type="loss_fraction").order_by('id')

    def expected_outputs(self):
        return [self.EXPECTED_LOSS_FRACTION]
