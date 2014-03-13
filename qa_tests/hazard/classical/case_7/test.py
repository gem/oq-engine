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


class ClassicalHazardCase7TestCase(qa_utils.BaseQATestCase):

    EXPECTED_XML_B1 = """<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <hazardCurves sourceModelTreePath="b1" gsimTreePath="b1" IMT="PGA" investigationTime="1.0">
    <IMLs>0.1 0.12 0.2</IMLs>
    <hazardCurve>
      <gml:Point>
        <gml:pos>0.0 0.0</gml:pos>
      </gml:Point>
      <poEs>0.864664716763 0.824184571746 0.366622358502</poEs>
    </hazardCurve>
  </hazardCurves>
</nrml>
"""

    EXPECTED_XML_B2 = """<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <hazardCurves sourceModelTreePath="b2" gsimTreePath="b1" IMT="PGA" investigationTime="1.0">
    <IMLs>0.1 0.12 0.2</IMLs>
    <hazardCurve>
      <gml:Point>
        <gml:pos>0.0 0.0</gml:pos>
      </gml:Point>
      <poEs>0.632120558829 0.611128414527 0.251495554108</poEs>
    </hazardCurve>
  </hazardCurves>
</nrml>
"""

    EXPECTED_XML_MEAN = """<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <hazardCurves statistics="mean" IMT="PGA" investigationTime="1.0">
    <IMLs>0.1 0.12 0.2</IMLs>
    <hazardCurve>
      <gml:Point>
        <gml:pos>0.0 0.0</gml:pos>
      </gml:Point>
      <poEs>0.794901469383 0.76026772458 0.332084317184</poEs>
    </hazardCurve>
  </hazardCurves>
</nrml>
"""

    @attr('qa', 'hazard', 'classical')
    def test(self):
        result_dir = tempfile.mkdtemp()

        try:
            cfg = os.path.join(os.path.dirname(__file__), 'job.ini')
            expected_curve_poes_b1 = [0.86466, 0.82460, 0.36525]
            expected_curve_poes_b2 = [0.63212, 0.61186, 0.25110]
            expected_mean_poes = [0.794898, 0.760778, 0.331005]

            job = self.run_hazard(cfg)

            # Test the poe values for the two curves.
            actual_curve_b1, actual_curve_b2 = (
                models.HazardCurveData.objects
                .filter(hazard_curve__output__oq_job=job.id,
                        hazard_curve__lt_realization__isnull=False)
                .order_by('hazard_curve__lt_realization__lt_model__sm_lt_path')
            )

            # Sanity check, to make sure we have the curves ordered correctly:
            self.assertEqual(
                ['b1'], actual_curve_b1.hazard_curve.lt_realization.sm_lt_path)
            self.assertEqual(
                ['b2'], actual_curve_b2.hazard_curve.lt_realization.sm_lt_path)

            numpy.testing.assert_array_almost_equal(
                expected_curve_poes_b1, actual_curve_b1.poes, decimal=3)

            numpy.testing.assert_array_almost_equal(
                expected_curve_poes_b2, actual_curve_b2.poes, decimal=3)

            # Test the mean curve:
            [mean_curve] = models.HazardCurveData.objects\
                .filter(hazard_curve__output__oq_job=job.id,
                        hazard_curve__statistics='mean')
            numpy.testing.assert_array_almost_equal(
                expected_mean_poes, mean_curve.poes, decimal=3)

            # Test the exports as well:
            exported_file_b1 = hazard_export.export(
                actual_curve_b1.hazard_curve.output.id, result_dir)
            self.assert_xml_equal(
                StringIO.StringIO(self.EXPECTED_XML_B1), exported_file_b1)

            exported_file_b2 = hazard_export.export(
                actual_curve_b2.hazard_curve.output.id, result_dir)
            self.assert_xml_equal(
                StringIO.StringIO(self.EXPECTED_XML_B2), exported_file_b2)

            # mean:
            exported_file_mean = hazard_export.export(
                mean_curve.hazard_curve.output.id, result_dir)
            self.assert_xml_equal(
                StringIO.StringIO(self.EXPECTED_XML_MEAN), exported_file_mean)
        finally:
            shutil.rmtree(result_dir)
