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
import os
import shutil
import tempfile
from nose.plugins.attrib import attr

from openquake import export
from qa_tests import _utils as qa_utils


class ScenarioHazardCase1TestCase(qa_utils.BaseQATestCase):

    EXPECTED_XML = """<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <gmfSet>
    <gmf IMT="PGA">
      <node iml="9.94109290291e-11" lon="0.0" lat="0.0"/>
      <node iml="1.28672099356e-10" lon="0.0" lat="0.0"/>
      <node iml="1.43477895793e-10" lon="0.0" lat="0.0"/>
      <node iml="1.74094358458e-10" lon="0.0" lat="0.0"/>
      <node iml="2.03781345853e-10" lon="0.0" lat="0.0"/>
      <node iml="2.13405169958e-10" lon="0.0" lat="0.0"/>
      <node iml="2.13705478231e-10" lon="0.0" lat="0.0"/>
      <node iml="2.6779608608e-10" lon="0.0" lat="0.0"/>
      <node iml="2.7343570164e-10" lon="0.0" lat="0.0"/>
      <node iml="3.41401290589e-10" lon="0.0" lat="0.0"/>
    </gmf>
    <gmf IMT="PGA">
      <node iml="1.61846273093e-10" lon="0.0" lat="0.1"/>
      <node iml="1.7366529578e-10" lon="0.0" lat="0.1"/>
      <node iml="1.82023245497e-10" lon="0.0" lat="0.1"/>
      <node iml="1.86981032598e-10" lon="0.0" lat="0.1"/>
      <node iml="1.93482796144e-10" lon="0.0" lat="0.1"/>
      <node iml="1.96170244383e-10" lon="0.0" lat="0.1"/>
      <node iml="2.41935206552e-10" lon="0.0" lat="0.1"/>
      <node iml="2.63364010931e-10" lon="0.0" lat="0.1"/>
      <node iml="2.75667076328e-10" lon="0.0" lat="0.1"/>
      <node iml="3.03603764945e-10" lon="0.0" lat="0.1"/>
    </gmf>
    <gmf IMT="PGA">
      <node iml="1.96605724932e-10" lon="0.0" lat="0.2"/>
      <node iml="2.15601083271e-10" lon="0.0" lat="0.2"/>
      <node iml="2.29847104327e-10" lon="0.0" lat="0.2"/>
      <node iml="2.3386739866e-10" lon="0.0" lat="0.2"/>
      <node iml="2.40117491804e-10" lon="0.0" lat="0.2"/>
      <node iml="2.56875810501e-10" lon="0.0" lat="0.2"/>
      <node iml="2.67444671721e-10" lon="0.0" lat="0.2"/>
      <node iml="2.76165990877e-10" lon="0.0" lat="0.2"/>
      <node iml="2.77868503385e-10" lon="0.0" lat="0.2"/>
      <node iml="3.72099540392e-10" lon="0.0" lat="0.2"/>
    </gmf>
  </gmfSet>
</nrml>
"""

    @attr('qa', 'scenario')
    def test(self):
        result_dir = tempfile.mkdtemp()

        try:
            cfg = os.path.join(os.path.dirname(__file__), 'job.ini')
            job = self.run_hazard(cfg)
            [output] = export.core.get_outputs(job.id)
            [exported_file] = export.hazard.export(
                output.id, result_dir)
            self.assert_xml_equal(
                StringIO.StringIO(self.EXPECTED_XML), exported_file)
        finally:
            shutil.rmtree(result_dir)
