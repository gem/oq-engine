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

import StringIO
import numpy
import os
import shutil
import tempfile

from nose.plugins.attrib import attr
from openquake.engine.db import models
from openquake.engine.export import hazard as hazard_export
from qa_tests import _utils as qa_utils


class ClassicalHazardCase11TestCase(qa_utils.BaseQATestCase):

    EXPECTED_XML_B1_B2 = """<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <hazardCurves sourceModelTreePath="b1_b2" gsimTreePath="b1" IMT="PGA" investigationTime="1.0">
    <IMLs>0.1 0.4 0.6 1.0</IMLs>
    <hazardCurve>
      <gml:Point>
        <gml:pos>0.0 0.0</gml:pos>
      </gml:Point>
      <poEs>0.0055270921432 0.000421641883053 5.75154102291e-05 0.0</poEs>
    </hazardCurve>
  </hazardCurves>
</nrml>
"""

    EXPECTED_XML_B1_B3 = """<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <hazardCurves sourceModelTreePath="b1_b3" gsimTreePath="b1" IMT="PGA" investigationTime="1.0">
    <IMLs>0.1 0.4 0.6 1.0</IMLs>
    <hazardCurve>
      <gml:Point>
        <gml:pos>0.0 0.0</gml:pos>
      </gml:Point>
      <poEs>0.00994026570298 0.000753551720765 9.69007927378e-05 0.0</poEs>
    </hazardCurve>
  </hazardCurves>
</nrml>
"""

    EXPECTED_XML_B1_B4 = """<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <hazardCurves sourceModelTreePath="b1_b4" gsimTreePath="b1" IMT="PGA" investigationTime="1.0">
    <IMLs>0.1 0.4 0.6 1.0</IMLs>
    <hazardCurve>
      <gml:Point>
        <gml:pos>0.0 0.0</gml:pos>
      </gml:Point>
      <poEs>0.0180244115988 0.00133514260633 0.00013735539542 0.0</poEs>
    </hazardCurve>
  </hazardCurves>
</nrml>
"""

    EXPECTED_XML_MEAN = """<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <hazardCurves statistics="mean" IMT="PGA" investigationTime="1.0">
    <IMLs>0.1 0.4 0.6 1.0</IMLs>
    <hazardCurve>
      <gml:Point>
        <gml:pos>0.0 0.0</gml:pos>
      </gml:Point>
      <poEs>0.0106744601702 0.000803487930336 9.71146367725e-05 0.0</poEs>
    </hazardCurve>
  </hazardCurves>
</nrml>"""

    EXPECTED_XML_QUANTILE_0_9 = """<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <hazardCurves statistics="quantile" quantileValue="0.9" IMT="PGA" investigationTime="1.0">
    <IMLs>0.1 0.4 0.6 1.0</IMLs>
    <hazardCurve>
      <gml:Point>
        <gml:pos>0.0 0.0</gml:pos>
      </gml:Point>
      <poEs>0.0139823386509 0.00104434716355 0.000117128094079 0.0</poEs>
    </hazardCurve>
  </hazardCurves>
</nrml>
"""

    EXPECTED_XML_QUANTILE_0_1 = """<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <hazardCurves statistics="quantile" quantileValue="0.1" IMT="PGA" investigationTime="1.0">
    <IMLs>0.1 0.4 0.6 1.0</IMLs>
    <hazardCurve>
      <gml:Point>
        <gml:pos>0.0 0.0</gml:pos>
      </gml:Point>
      <poEs>0.0055270921432 0.000421641883053 5.75154102291e-05 0.0</poEs>
    </hazardCurve>
  </hazardCurves>
</nrml>
"""

    @attr('qa', 'hazard', 'classical')
    def test(self):
        result_dir = tempfile.mkdtemp()
        aaae = numpy.testing.assert_array_almost_equal

        try:
            cfg = os.path.join(os.path.dirname(__file__), 'job.ini')
            expected_curve_poes_b1_b2 = [0.0055, 0.00042, 5.77E-5, 0.0]
            expected_curve_poes_b1_b3 = [0.00995, 0.00076, 9.7E-5, 0.0]
            expected_curve_poes_b1_b4 = [0.018, 0.0013, 0.00014, 0.0]

            expected_mean_poes = [0.01067, 0.0008, 9.774E-5, 0.0]

            expected_q0_1_poes = [0.0055, 0.00042, 5.77E-5, 0.0]
            expected_q0_9_poes = [0.013975, 0.00103, 0.0001185, 0.0]

            job = self.run_hazard(cfg)

            # Test the poe values for the two curves:
            curve_b1_b2, curve_b1_b3, curve_b1_b4 = (
                models.HazardCurveData.objects
                .filter(hazard_curve__output__oq_job=job.id,
                        hazard_curve__lt_realization__isnull=False)
                .order_by(
                    'hazard_curve__lt_realization__lt_model__sm_lt_path'))

            # Sanity check, to make sure we have the curves ordered correctly:
            self.assertEqual(
                ['b1', 'b2'],
                curve_b1_b2.hazard_curve.lt_realization.sm_lt_path)
            self.assertEqual(
                ['b1', 'b3'],
                curve_b1_b3.hazard_curve.lt_realization.sm_lt_path)
            self.assertEqual(
                ['b1', 'b4'],
                curve_b1_b4.hazard_curve.lt_realization.sm_lt_path)

            aaae(expected_curve_poes_b1_b2, curve_b1_b2.poes, decimal=4)
            aaae(expected_curve_poes_b1_b3, curve_b1_b3.poes, decimal=4)
            aaae(expected_curve_poes_b1_b4, curve_b1_b4.poes, decimal=4)

            # Test the mean curve:
            [mean_curve] = models.HazardCurveData.objects\
                .filter(hazard_curve__output__oq_job=job.id,
                        hazard_curve__statistics='mean')
            aaae(expected_mean_poes, mean_curve.poes, decimal=4)

            # Test the quantile curves:
            quantile_0_1_curve, quantile_0_9_curve = \
                models.HazardCurveData.objects\
                    .filter(hazard_curve__output__oq_job=job.id,
                            hazard_curve__statistics='quantile')\
                    .order_by('hazard_curve__quantile')
            aaae(expected_q0_1_poes, quantile_0_1_curve.poes, decimal=4)
            aaae(expected_q0_9_poes, quantile_0_9_curve.poes, decimal=4)

            # Test the exports as well:
            exported_file_b1_b2 = hazard_export.export(
                curve_b1_b2.hazard_curve.output.id, result_dir)
            self.assert_xml_equal(
                StringIO.StringIO(self.EXPECTED_XML_B1_B2),
                exported_file_b1_b2)

            exported_file_b1_b3 = hazard_export.export(
                curve_b1_b3.hazard_curve.output.id, result_dir)
            self.assert_xml_equal(
                StringIO.StringIO(self.EXPECTED_XML_B1_B3),
                exported_file_b1_b3)

            exported_file_b1_b4 = hazard_export.export(
                curve_b1_b4.hazard_curve.output.id, result_dir)
            self.assert_xml_equal(
                StringIO.StringIO(self.EXPECTED_XML_B1_B4),
                exported_file_b1_b4)

            exported_file_mean = hazard_export.export(
                mean_curve.hazard_curve.output.id, result_dir)
            self.assert_xml_equal(
                StringIO.StringIO(self.EXPECTED_XML_MEAN),
                exported_file_mean)

            q01_file = hazard_export.export(
                quantile_0_1_curve.hazard_curve.output.id, result_dir)
            self.assert_xml_equal(
                StringIO.StringIO(self.EXPECTED_XML_QUANTILE_0_1),
                q01_file)

            q09_file = hazard_export.export(
                quantile_0_9_curve.hazard_curve.output.id, result_dir)
            self.assert_xml_equal(
                StringIO.StringIO(self.EXPECTED_XML_QUANTILE_0_9),
                q09_file)
        finally:
            shutil.rmtree(result_dir)
