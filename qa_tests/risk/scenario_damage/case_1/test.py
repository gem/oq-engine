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

from qa_tests import risk
from openquake.engine.tests.utils import helpers


class ScenarioDamageRiskCase1TestCase(risk.BaseRiskQATestCase):
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
        <damage ds="no_damage" mean="875.81199" stddev="757.540852525"/>
        <damage ds="LS1" mean="1448.2960791" stddev="256.15318195"/>
        <damage ds="LS2" mean="675.8919309" stddev="556.765558354"/>
      </asset>
    </DDNode>
    <DDNode>
      <gml:Point>
        <gml:pos>15.56 38.17</gml:pos>
      </gml:Point>
      <asset assetRef="a2">
        <damage ds="no_damage" mean="344.90869" stddev="300.611885456"/>
        <damage ds="LS1" mean="747.62374" stddev="144.648244809"/>
        <damage ds="LS2" mean="907.46757" stddev="417.307715071"/>
      </asset>
    </DDNode>
    <DDNode>
      <gml:Point>
        <gml:pos>15.48 38.25</gml:pos>
      </gml:Point>
      <asset assetRef="a3">
        <damage ds="no_damage" mean="224.41751" stddev="220.650927184"/>
        <damage ds="LS1" mean="465.6442715" stddev="136.927805797"/>
        <damage ds="LS2" mean="309.9382185" stddev="246.84411292"/>
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
      <damage ds="no_damage" mean="1100.2295" stddev="880.276624388"/>
      <damage ds="LS1" mean="1913.9403506" stddev="296.218619036"/>
      <damage ds="LS2" mean="985.8301494" stddev="616.562370911"/>
    </DDNode>
    <DDNode>
      <taxonomy>RC</taxonomy>
      <damage ds="no_damage" mean="344.90869" stddev="300.611885456"/>
      <damage ds="LS1" mean="747.62374" stddev="144.648244809"/>
      <damage ds="LS2" mean="907.46757" stddev="417.307715071"/>
    </DDNode>
  </dmgDistPerTaxonomy>
</nrml>
'''

    EXPECTED_DMG_DIST_TOTAL = '''<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
  <totalDmgDist>
    <damageStates>no_damage LS1 LS2</damageStates>
    <damage ds="no_damage" mean="1445.13819" stddev="824.78005267"/>
    <damage ds="LS1" mean="2661.5640906" stddev="373.99997281"/>
    <damage ds="LS2" mean="1893.2977194" stddev="661.810775842"/>
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
      <cf assetRef="a1" mean="675.8919309" stdDev="556.765558354"/>
    </CMNode>
    <CMNode>
      <gml:Point>
        <gml:pos>15.56 38.17</gml:pos>
      </gml:Point>
      <cf assetRef="a2" mean="907.46757" stdDev="417.307715071"/>
    </CMNode>
    <CMNode>
      <gml:Point>
        <gml:pos>15.48 38.25</gml:pos>
      </gml:Point>
      <cf assetRef="a3" mean="309.9382185" stdDev="246.84411292"/>
    </CMNode>
  </collapseMap>
</nrml>
'''

    @attr('qa', 'risk', 'scenario_damage')
    def test(self):
        self._run_test()

    def get_hazard_job(self):
        job = helpers.get_hazard_job(
            helpers.get_data_path("scenario_hazard/job.ini"))
        fname = self._test_path('gmf_scenario.csv')
        helpers.populate_gmf_data_from_csv(job, fname)
        return job

    def expected_outputs(self):
        return [self.EXPECTED_DMG_DIST_PER_ASSET,
                self.EXPECTED_COLLAPSE_MAP,
                self.EXPECTED_DMG_DIST_PER_TAXONOMY,
                self.EXPECTED_DMG_DIST_TOTAL]
