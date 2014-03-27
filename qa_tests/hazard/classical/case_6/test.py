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

import StringIO
import numpy
import os
import shutil
import tempfile

from nose.plugins.attrib import attr
from openquake.engine.db import models
from openquake.engine.export import hazard as hazard_export
from qa_tests import _utils as qa_utils


class ClassicalHazardCase6TestCase(qa_utils.BaseQATestCase):

    EXPECTED_XML = """<?xml version='1.0' encoding='UTF-8'?>
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

    @attr('qa', 'hazard', 'classical')
    def test(self):
        result_dir = tempfile.mkdtemp()

        try:
            cfg = os.path.join(os.path.dirname(__file__), 'job.ini')
            expected_curve_poes = [0.86466, 0.82460, 0.36525]

            job = self.run_hazard(cfg)

            # Test the poe values of the single curve:
            [actual_curve] = models.HazardCurveData.objects.filter(
                hazard_curve__output__oq_job=job.id)

            numpy.testing.assert_array_almost_equal(
                expected_curve_poes, actual_curve.poes, decimal=2)

            # Test the export as well:
            exported_file = hazard_export.export(
                actual_curve.hazard_curve.output.id, result_dir)
            self.assert_xml_equal(
                StringIO.StringIO(self.EXPECTED_XML), exported_file)
        finally:
            shutil.rmtree(result_dir)
