# Copyright (c) 2010-2013, GEM Foundation.
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
import shutil
import tempfile
import StringIO

import numpy
from nose.plugins.attrib import attr

from qa_tests import risk
from tests.utils import helpers
from openquake.db import models
from openquake import export


class ScenarioDamageRiskCase1TestCase(risk.BaseRiskQATestCase):
    cfg = os.path.join(os.path.dirname(__file__), 'job.ini')

    EXPECTED_DMG_DIST_PER_ASSET_XML = '''<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <dmgDistPerAsset>
    <damageStates>no_damage minor moderate severe collapse</damageStates>
    <DDNode>
      <gml:Point>
        <gml:pos>9.15333 45.122</gml:pos>
      </gml:Point>
      <asset assetRef="asset_02">
        <damage ds="no_damage" mean="6.0" stddev="0.0"/>
        <damage ds="minor" mean="0.0" stddev="0.0"/>
        <damage ds="moderate" mean="0.0" stddev="0.0"/>
        <damage ds="severe" mean="0.0" stddev="0.0"/>
        <damage ds="collapse" mean="0.0" stddev="0.0"/>
      </asset>
    </DDNode>
    <DDNode>
      <gml:Point>
        <gml:pos>9.15 45.16667</gml:pos>
      </gml:Point>
      <asset assetRef="asset_01">
        <damage ds="no_damage" mean="7.0" stddev="0.0"/>
        <damage ds="minor" mean="0.0" stddev="0.0"/>
        <damage ds="moderate" mean="0.0" stddev="0.0"/>
        <damage ds="severe" mean="0.0" stddev="0.0"/>
        <damage ds="collapse" mean="0.0" stddev="0.0"/>
      </asset>
    </DDNode>
    <DDNode>
      <gml:Point>
        <gml:pos>9.14777 45.17999</gml:pos>
      </gml:Point>
      <asset assetRef="asset_03">
        <damage ds="no_damage" mean="5.0" stddev="0.0"/>
        <damage ds="minor" mean="0.0" stddev="0.0"/>
        <damage ds="moderate" mean="0.0" stddev="0.0"/>
        <damage ds="severe" mean="0.0" stddev="0.0"/>
        <damage ds="collapse" mean="0.0" stddev="0.0"/>
      </asset>
    </DDNode>
  </dmgDistPerAsset>
</nrml>
'''

    EXPECTED_DMG_DIST_PER_TAXONOMY_XML = '''<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <dmgDistPerTaxonomy>
    <damageStates>no_damage minor moderate severe collapse</damageStates>
    <DDNode>
      <taxonomy>RC/DMRF-D/LR</taxonomy>
      <damage ds="no_damage" mean="12.0" stddev="0.0"/>
      <damage ds="minor" mean="0.0" stddev="0.0"/>
      <damage ds="moderate" mean="0.0" stddev="0.0"/>
      <damage ds="severe" mean="0.0" stddev="0.0"/>
      <damage ds="collapse" mean="0.0" stddev="0.0"/>
    </DDNode>
    <DDNode>
      <taxonomy>RC/DMRF-D/HR</taxonomy>
      <damage ds="no_damage" mean="6.0" stddev="0.0"/>
      <damage ds="minor" mean="0.0" stddev="0.0"/>
      <damage ds="moderate" mean="0.0" stddev="0.0"/>
      <damage ds="severe" mean="0.0" stddev="0.0"/>
      <damage ds="collapse" mean="0.0" stddev="0.0"/>
    </DDNode>
  </dmgDistPerTaxonomy>
</nrml>
'''

    EXPECTED_DMG_DIST_TOTAL_XML = '''<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <totalDmgDist>
    <damageStates>no_damage minor moderate severe collapse</damageStates>
    <damage ds="no_damage" mean="18.0" stddev="0.0"/>
    <damage ds="minor" mean="0.0" stddev="0.0"/>
    <damage ds="moderate" mean="0.0" stddev="0.0"/>
    <damage ds="severe" mean="0.0" stddev="0.0"/>
    <damage ds="collapse" mean="0.0" stddev="0.0"/>
  </totalDmgDist>
</nrml>
'''

    EXPECTED_COLLAPSE_MAP_XML = '''<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <collapseMap>
    <CMNode>
      <gml:Point>
        <gml:pos>9.15 45.16667</gml:pos>
      </gml:Point>
      <cf assetRef="asset_01" mean="0.0" stdDev="0.0"/>
    </CMNode>
    <CMNode>
      <gml:Point>
        <gml:pos>9.15333 45.122</gml:pos>
      </gml:Point>
      <cf assetRef="asset_02" mean="0.0" stdDev="0.0"/>
    </CMNode>
    <CMNode>
      <gml:Point>
        <gml:pos>9.14777 45.17999</gml:pos>
      </gml:Point>
      <cf assetRef="asset_03" mean="0.0" stdDev="0.0"/>
    </CMNode>
  </collapseMap>
</nrml>
'''

    @attr('qa', 'risk', 'scenario_damage')
    def test(self):
        self._run_test()

    def hazard_id(self):
        job = helpers.get_hazard_job(
            helpers.demo_file("scenario_hazard/job.ini"))

        job.hazard_calculation = models.HazardCalculation.objects.create(
            owner=job.hazard_calculation.owner,
            truncation_level=job.hazard_calculation.truncation_level,
            maximum_distance=job.hazard_calculation.maximum_distance,
            intensity_measure_types_and_levels=(
                job.hazard_calculation.intensity_measure_types_and_levels),
            calculation_mode="scenario")

        job.save()

        output = models.Output.objects.create_output(
            job, "Test Hazard output", "gmf_scenario")

        fname = os.path.join(os.path.dirname(__file__), 'gmf_scenario.csv')
        with open(fname, 'rb') as csvfile:
            gmfreader = csv.reader(csvfile, delimiter=',')
            locations = gmfreader.next()

            arr = numpy.array([map(float, row) for row in gmfreader])
            for i, gmvs in enumerate(arr.transpose()):
                models.GmfScenario.objects.create(
                    output=output,
                    imt="MMI",
                    gmvs=gmvs,
                    result_grp_ordinal=1,
                    location="POINT(%s)" % locations[i])

        return output.id

    # no time to implement this: checking the XML includes it
    def actual_data(self, job):
        return []

    # no time to implement this: checking the XML includes it
    def expected_data(self):
        return []

    def expected_outputs(self):
        return [self.EXPECTED_DMG_DIST_PER_ASSET_XML,
                self.EXPECTED_DMG_DIST_PER_TAXONOMY_XML,
                self.EXPECTED_DMG_DIST_TOTAL_XML]

    def test_export_collapse_map(self):
        # the collapse map is a special case of dmt_dist_per_asset
        result_dir = tempfile.mkdtemp()
        try:
            job = self.run_risk(self.cfg, self.hazard_id())
            output = models.Output.objects.get(
                oq_job=job, output_type='dmg_dist_per_asset')
            [exported_file] = export.risk.export_collapse_map(
                output, result_dir)
            self.assert_xml_equal(
                StringIO.StringIO(self.EXPECTED_COLLAPSE_MAP_XML),
                exported_file)
        finally:
            shutil.rmtree(result_dir)
