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

from nose.plugins.attrib import attr

from openquake.engine.tests.utils import helpers
from qa_tests import risk


class ScenarioDamageRiskCase2TestCase(risk.BaseRiskQATestCase):
    output_type = "gmf_scenario"

    EXPECTED_DMG_DIST_PER_ASSET = '''<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
  <dmgDistPerAsset>
    <damageStates>no_damage LS1 LS2</damageStates>
    <DDNode>
      <gml:Point>
        <gml:pos>15.48 38.09</gml:pos>
      </gml:Point>
      <asset assetRef="a1">
        <damage ds="no_damage" mean="1562.60873676" stddev="968.935196007"/>
        <damage ds="LS1" mean="1108.0179559" stddev="652.736659161"/>
        <damage ds="LS2" mean="329.37330734" stddev="347.391647796"/>
      </asset>
    </DDNode>
    <DDNode>
      <gml:Point>
        <gml:pos>15.56 38.17</gml:pos>
      </gml:Point>
      <asset assetRef="a2">
        <damage ds="no_damage" mean="56.7203646693" stddev="117.780724159"/>
        <damage ds="LS1" mean="673.104377189" stddev="485.202354464"/>
        <damage ds="LS2" mean="1270.17525814" stddev="575.872927586"/>
      </asset>
    </DDNode>
    <DDNode>
      <gml:Point>
        <gml:pos>15.48 38.25</gml:pos>
      </gml:Point>
      <asset assetRef="a3">
        <damage ds="no_damage" mean="417.329450348" stddev="304.476603429"/>
        <damage ds="LS1" mean="387.208726145" stddev="181.141228526"/>
        <damage ds="LS2" mean="195.461823506" stddev="253.91290672"/>
      </asset>
    </DDNode>
  </dmgDistPerAsset>
</nrml>
'''

    EXPECTED_DMG_DIST_PER_TAXONOMY = '''<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
  <dmgDistPerTaxonomy>
    <damageStates>no_damage LS1 LS2</damageStates>
    <DDNode>
      <taxonomy>RM</taxonomy>
      <damage ds="no_damage" mean="1979.93818711" stddev="1103.59950218"/>
      <damage ds="LS1" mean="1495.22668204" stddev="745.325447387"/>
      <damage ds="LS2" mean="524.835130846" stddev="401.918282572"/>
    </DDNode>
    <DDNode>
      <taxonomy>RC</taxonomy>
      <damage ds="no_damage" mean="56.7203646693" stddev="117.780724159"/>
      <damage ds="LS1" mean="673.104377189" stddev="485.202354464"/>
      <damage ds="LS2" mean="1270.17525814" stddev="575.872927586"/>
    </DDNode>
  </dmgDistPerTaxonomy>
</nrml>
'''

    EXPECTED_DMG_DIST_TOTAL = '''<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
  <totalDmgDist>
    <damageStates>no_damage LS1 LS2</damageStates>
    <damage ds="no_damage" mean="2036.65855178" stddev="1075.31798196"/>
    <damage ds="LS1" mean="2168.33105923" stddev="1076.43488958"/>
    <damage ds="LS2" mean="1795.01038899" stddev="687.09098615"/>
  </totalDmgDist>
</nrml>
'''

    EXPECTED_COLLAPSE_MAP = '''<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
  <collapseMap>
    <CMNode>
      <gml:Point>
        <gml:pos>15.48 38.09</gml:pos>
      </gml:Point>
      <cf assetRef="a1" mean="329.37330734" stdDev="347.391647796"/>
    </CMNode>
    <CMNode>
      <gml:Point>
        <gml:pos>15.56 38.17</gml:pos>
      </gml:Point>
      <cf assetRef="a2" mean="1270.17525814" stdDev="575.872927586"/>
    </CMNode>
    <CMNode>
      <gml:Point>
        <gml:pos>15.48 38.25</gml:pos>
      </gml:Point>
      <cf assetRef="a3" mean="195.461823506" stdDev="253.91290672"/>
    </CMNode>
  </collapseMap>
</nrml>
'''

    @attr('qa', 'risk', 'scenario_damage')
    def test(self):
        self._run_test()

    def get_hazard_job(self):
        job = helpers.get_job(
            helpers.get_data_path("scenario_hazard/job.ini"))
        fname = self._test_path('../case_1/gmf_scenario.csv')
        helpers.populate_gmf_data_from_csv(job, fname)
        return job

    def expected_outputs(self):
        return [self.EXPECTED_DMG_DIST_PER_ASSET,
                self.EXPECTED_COLLAPSE_MAP,
                self.EXPECTED_DMG_DIST_PER_TAXONOMY,
                self.EXPECTED_DMG_DIST_TOTAL]
