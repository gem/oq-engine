# Copyright (c) 2010-2015, GEM Foundation.
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
import tempfile

from nose.plugins.attrib import attr

from qa_tests import risk
from openquake.qa_tests_data.classical_risk import (
    case_1, case_2, case_3, case_4)
from openquake.engine.tests.utils import helpers
from openquake.commonlib import writers
from openquake.engine.db import models


class ClassicalRiskCase1TestCase(risk.BaseRiskQATestCase):
    module = case_1

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

    @attr('qa', 'risk', 'classical')
    def test(self):
        self._run_test()

    def get_hazard_job(self):
        hazard_imls = [0.001, 0.01, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4,
                       0.45, 0.5, 0.55, 0.6, 0.7, 0.8, 0.9, 1.0]
        poes = [0.039861266979, 0.039861266979, 0.0397287574803,
                0.0296134266256, 0.0198273287565, 0.0130622701615,
                0.00865538795, 0.00589852059369, 0.00406169858951,
                0.00281172717953, 0.00199511741778, 0.00135870597285,
                0.000989667841574, 0.000757544444296, 0.000272824002046,
                0.0, 0.0, 0.]
        job = helpers.get_job(
            helpers.get_data_path("simple_fault_demo_hazard/job.ini"),
            intensity_measure_types_and_levels=str({'PGA': hazard_imls}))

        models.HazardSite.objects.create(
            hazard_calculation=job, location="POINT(1 1)")
        models.HazardCurveData.objects.create(
            hazard_curve=models.HazardCurve.objects.create(
                output=models.Output.objects.create_output(
                    job, "Test Hazard curve", "hazard_curve"),
                investigation_time=50,
                imt="PGA", imls=hazard_imls,
                statistics="mean"),
            poes=poes,
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


class ClassicalRiskCase2TestCase(ClassicalRiskCase1TestCase):
    module = case_2

    EXPECTED_LOSS_CURVE_XML = """<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <lossCurves investigationTime="50.0" statistics="mean" unit="USD" lossType="structural">
    <lossCurve assetRef="a1">
      <gml:Point>
        <gml:pos>1.0 1.0</gml:pos>
      </gml:Point>
      <poEs>0.0393347533677 0.0391254281716 0.0376741689433 0.0347597109836 0.0310305310068 0.0271795287863 0.023629919279 0.0205495084461 0.0179532864059 0.0157897693715 0.0139899994698 0.011228361585 0.00925277823514 0.00777698111944 0.00661872190264 0.00567849220587 0.00429320981949 0.00342379135052 0.00285158950286 0.00237111635038 0.00190153868716 0.00114593052735 0.000834074579572 0.000755265952957 0.000655382394931 0.000422046545858 0.000266286103069 0.00012403689013 3.28497166703e-05 2.17866446601e-06 0.0</poEs>
      <losses>0.0 0.02 0.04 0.06 0.08 0.1 0.12 0.14 0.16 0.18 0.2 0.24 0.28 0.32 0.36 0.4 0.48 0.56 0.64 0.72 0.8 0.96 1.12 1.28 1.44 1.6 1.68 1.76 1.84 1.92 2.0</losses>
      <lossRatios>0.0 0.01 0.02 0.03 0.04 0.05 0.06 0.07 0.08 0.09 0.1 0.12 0.14 0.16 0.18 0.2 0.24 0.28 0.32 0.36 0.4 0.48 0.56 0.64 0.72 0.8 0.84 0.88 0.92 0.96 1.0</lossRatios>
      <averageLoss>9.3932e-03</averageLoss>
    </lossCurve>
  </lossCurves>
</nrml>"""

    EXPECTED_LOSS_MAP_0_01_XML = """<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
  <lossMap investigationTime="50.0" poE="0.01"
           statistics="mean" lossCategory="single_asset" unit="USD" lossType="structural">
    <node>
      <gml:Point>
        <gml:pos>1.0 1.0</gml:pos>
      </gml:Point>
      <loss assetRef="a1" value="0.264870863284"/>
    </node>
  </lossMap>
</nrml>
    """

    def actual_data(self, job):
        return ([curve.loss_ratios
                for curve in models.LossCurveData.objects.filter(
                    loss_curve__output__oq_job=job).order_by(
                    'asset_ref')] +
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
            0.264870863283]

    def expected_outputs(self):
        return [self.EXPECTED_LOSS_CURVE_XML, self.EXPECTED_LOSS_MAP_0_01_XML]


class ClassicalRiskCase3TestCase(
        risk.CompleteTestCase, risk.FixtureBasedQATestCase):

    module = case_3
    hazard_calculation_fixture = "Classical PSHA - Loss fractions QA test"

    @attr('qa', 'risk', 'classical')
    def test(self):
        job = self._run_test()
        data = [[curve.asset_ref, curve.average_loss]
                for curve in models.LossCurveData.objects.filter(
                    loss_curve__output__oq_job=job).order_by('asset_ref')]
        fd, fname = tempfile.mkstemp(suffix='.csv')
        os.close(fd)
        writers.save_csv(
            fname, [['asset_ref', 'avg_loss']] + data, fmt='%11.8E')
        expected = self._test_path('expected/rlz-000-avg_loss.csv')
        self.assertEqual(open(fname).read(), open(expected).read())

    items_per_output = None

    def expected_output_data(self):
        b1 = models.Output.HazardMetadata(
            investigation_time=50.0,
            statistics=None, quantile=None,
            sm_path=('b1',), gsim_path=('b1',))

        values = self._csv('fractions', dtype="f4, f4, S3, f4, f4")

        return zip(
            [("loss_fraction", b1, None, None, "taxonomy", 0.1,
              "structural") + ('%.5f' % lon, '%.5f' % lat, taxonomy)
             for lon, lat, taxonomy, _loss, _fraction in values],
            [models.LossFractionData(absolute_loss=v) for v in values['f3']])


class ClassicalRiskCase4TestCase(
        risk.CompleteTestCase, risk.FixtureBasedQATestCase):

    module = case_4
    hazard_calculation_fixture = "Classical Hazard-Risk QA test 4"

    @attr('qa', 'risk', 'classical')
    def test(self):
        job = self._run_test()
        outputs = models.Output.objects.filter(
            oq_job=job, output_type='loss_curve').order_by('id')
        for out in outputs:
            if out.display_name.startswith('Mean'):
                continue
            loss_curve = out.loss_curve
            rlz = loss_curve.hazard_output.hazard_curve.lt_realization
            key = 'rlz-%03d-avg_loss' % rlz.ordinal
            data = [[curve.asset_ref, curve.average_loss]
                    for curve in models.LossCurveData.objects.filter(
                        loss_curve=loss_curve).order_by('asset_ref')]
            fd, fname = tempfile.mkstemp(prefix=key, suffix='.csv')
            os.close(fd)
            writers.save_csv(
                fname, [['asset_ref', 'avg_loss']] + data, fmt='%11.8E')
            expected = self._test_path('expected/%s.csv' % key)
            self.assertEqual(open(fname).read(), open(expected).read())
