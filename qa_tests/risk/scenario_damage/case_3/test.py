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


class ScenarioDamageRiskCase3TestCase(risk.BaseRiskQATestCase):
    """
    There are not enough taxonomies in the fragility_function (RM is missing)
    but the parameter taxonomies_from_model is set, so assets of
    unknown taxonomy are simply ignored.
    """

    output_type = "gmf_scenario"

    EXPECTED_DMG_DIST_PER_ASSET = '''<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
  <dmgDistPerAsset>
    <damageStates>no_damage LS1 LS2</damageStates>
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
  </dmgDistPerAsset>
</nrml>
'''

    EXPECTED_DMG_DIST_PER_TAXONOMY = '''<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
  <dmgDistPerTaxonomy>
    <damageStates>no_damage LS1 LS2</damageStates>
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
    <damage ds="no_damage" mean="344.90869" stddev="300.611885456"/>
    <damage ds="LS1" mean="747.62374" stddev="144.648244809"/>
    <damage ds="LS2" mean="907.46757" stddev="417.307715071"/>
  </totalDmgDist>
</nrml>
'''

    EXPECTED_COLLAPSE_MAP = '''<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
  <collapseMap>
    <CMNode>
      <gml:Point>
        <gml:pos>15.56 38.17</gml:pos>
      </gml:Point>
      <cf assetRef="a2" mean="907.46757" stdDev="417.307715071"/>
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
        helpers.populate_gmf_data_from_csv(
            job, self._test_path('../case_1/gmf_scenario.csv'))
        return job

    def expected_outputs(self):
        return [self.EXPECTED_DMG_DIST_PER_ASSET,
                self.EXPECTED_COLLAPSE_MAP,
                self.EXPECTED_DMG_DIST_PER_TAXONOMY,
                self.EXPECTED_DMG_DIST_TOTAL]
