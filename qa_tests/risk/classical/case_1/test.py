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
from tests.utils import helpers

from openquake.engine.db import models


class ClassicalRiskCase1TestCase(risk.BaseRiskQATestCase):
    EXPECTED_LOSS_CURVE_XML = """<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
  <lossCurves investigationTime="50.0" statistics="mean" unit="USD" lossType="structural">
    <lossCurve assetRef="a1">
      <gml:Point>
        <gml:pos>1.0 1.0</gml:pos>
      </gml:Point>
      <poEs>0.0393347533677 0.039319630829 0.0384540639673 0.0353555683375 0.0310809359515 0.0269219661169 0.0233091854249 0.0202549286473 0.0176926044553 0.0155616221765 0.0138044829893 0.0111599850445 0.00927277820929 0.00780386210329 0.00660104748954 0.00562104810103 0.00426294495221 0.00347810187546 0.00291642896185 0.00237546166034 0.00185477228722 0.00113319071162 0.000862358303707 0.000784269030445 0.000660062215756 0.000374938542786 0.000230249004394 0.000122823654476 5.72790058706e-05 2.35807221323e-05 8.66392324538e-06</poEs>
      <losses>0.0 0.02 0.04 0.06 0.08 0.1 0.12 0.14 0.16 0.18 0.2 0.24 0.28 0.32 0.36 0.4 0.48 0.56 0.64 0.72 0.8 0.96 1.12 1.28 1.44 1.6 1.68 1.76 1.84 1.92 2.0</losses>
      <lossRatios>0.0 0.01 0.02 0.03 0.04 0.05 0.06 0.07 0.08 0.09 0.1 0.12 0.14 0.16 0.18 0.2 0.24 0.28 0.32 0.36 0.4 0.48 0.56 0.64 0.72 0.8 0.84 0.88 0.92 0.96 1.0</lossRatios>
      <averageLoss>9.3929e-03</averageLoss>
    </lossCurve>
  </lossCurves>
</nrml>
    """

    EXPECTED_LOSS_MAP_0_01_XML = """<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
  <lossMap investigationTime="50.0" poE="0.01" statistics="mean"
    lossCategory="single_asset" unit="USD" lossType="structural">
    <node>
      <gml:Point>
        <gml:pos>1.0 1.0</gml:pos>
      </gml:Point>
      <loss assetRef="a1" value="0.264586283238"/>
    </node>
  </lossMap>
</nrml>
    """

    EXPECTED_LOSS_MAP_0_02_XML = """<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
  <lossMap investigationTime="50.0" poE="0.02"
           statistics="mean" lossCategory="single_asset" unit="USD" lossType="structural">
    <node>
      <gml:Point>
        <gml:pos>1.0 1.0</gml:pos>
      </gml:Point>
      <loss assetRef="a1" value="0.141989823521"/>
    </node>
  </lossMap>
</nrml>"""

    EXPECTED_LOSS_MAP_0_05_XML = """<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
  <lossMap investigationTime="50.0" poE="0.05" statistics="mean"
           lossCategory="single_asset" unit="USD" lossType="structural">
    <node>
      <gml:Point>
        <gml:pos>1.0 1.0</gml:pos>
      </gml:Point>
      <loss assetRef="a1" value="0.0"/>
    </node>
  </lossMap>
</nrml>
    """

    @noseattr('qa', 'risk', 'classical')
    def test(self):
        self._run_test()

    def get_hazard_job(self):
        job = helpers.get_hazard_job(
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

        models.HazardCurveData.objects.create(
            hazard_curve=models.HazardCurve.objects.create(
                output=models.Output.objects.create(
                    oq_job=job,
                    display_name="Test Hazard curve",
                    output_type="hazard_curve"),
                investigation_time=50,
                imt="PGA", imls=[hz[0] for hz in hazard_curve],
                statistics="mean"),
            poes=[hz[1] for hz in hazard_curve],
            location="POINT(1 1)")

        return job

    def actual_data(self, job):
        return ([curve.loss_ratios
                for curve in models.LossCurveData.objects.filter(
                    loss_curve__output__oq_job=job).order_by('asset_ref')] +
                [point.value
                 for point in models.LossMapData.objects.filter(
                    loss_map__output__oq_job=job).order_by(
                        'asset_ref', 'loss_map__poe')])

    def expected_data(self):
        return [[
            0.00, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06,
            0.07, 0.08, 0.09, 0.10, 0.12, 0.14, 0.16,
            0.18, 0.20, 0.24, 0.28, 0.32, 0.36, 0.40,
            0.48, 0.56, 0.64, 0.72, 0.80, 0.84, 0.88,
            0.92, 0.96, 1.00],
            0.264586283238, 0.141989823521, 0]

    def expected_outputs(self):
        return [self.EXPECTED_LOSS_CURVE_XML,
                self.EXPECTED_LOSS_MAP_0_01_XML,
                self.EXPECTED_LOSS_MAP_0_02_XML,
                self.EXPECTED_LOSS_MAP_0_05_XML]
