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

from nose.plugins.attrib import attr

from qa_tests import risk
from openquake.qa_tests_data.scenario_damage import (
    case_1, case_2, case_3, case_4)
from openquake.engine.tests.utils import helpers
from openquake.engine.db import models


class ScenarioDamageRiskCase1TestCase(risk.BaseRiskQATestCase):
    module = case_1
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
        job = helpers.get_job(
            helpers.get_data_path("scenario_hazard/job.ini"))
        fname = self._test_path('gmf_scenario.csv')
        helpers.create_gmf_from_csv(job, fname, 'gmf_scenario')
        return job

    def expected_outputs(self):
        return [self.EXPECTED_DMG_DIST_PER_ASSET,
                self.EXPECTED_COLLAPSE_MAP,
                self.EXPECTED_DMG_DIST_PER_TAXONOMY,
                self.EXPECTED_DMG_DIST_TOTAL]


class ScenarioDamageRiskCase2TestCase(risk.BaseRiskQATestCase):
    module = case_2
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
        helpers.create_gmf_from_csv(job, fname, 'gmf_scenario')
        return job

    def expected_outputs(self):
        return [self.EXPECTED_DMG_DIST_PER_ASSET,
                self.EXPECTED_COLLAPSE_MAP,
                self.EXPECTED_DMG_DIST_PER_TAXONOMY,
                self.EXPECTED_DMG_DIST_TOTAL]


class ScenarioDamageRiskCase3TestCase(risk.BaseRiskQATestCase):
    """
    There are not enough taxonomies in the fragility_function (RM is missing)
    but the parameter taxonomies_from_model is set, so assets of
    unknown taxonomy are simply ignored.
    """
    output_type = "gmf_scenario"
    module = case_3

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
        helpers.create_gmf_from_csv(
            job, self._test_path('../case_1/gmf_scenario.csv'), 'gmf_scenario')
        return job

    def expected_outputs(self):
        return [self.EXPECTED_DMG_DIST_PER_ASSET,
                self.EXPECTED_COLLAPSE_MAP,
                self.EXPECTED_DMG_DIST_PER_TAXONOMY,
                self.EXPECTED_DMG_DIST_TOTAL]


# FIXME(lp). This is a regression test meant to exercise the sd-imt
# logic in the SR calculator. Data has not been validated
class ScenarioDamageRiskCase4TestCase(risk.FixtureBasedQATestCase):
    module = case_4
    output_type = 'gmf_scenario'
    hazard_calculation_fixture = 'Scenario Damage QA Test 4'

    @attr('qa', 'risk', 'scenario_damage')
    def test(self):
        self._run_test()

    def actual_data(self, job):
        per_asset = models.DmgDistPerAsset.objects.filter(
            dmg_state__risk_calculation=job).order_by(
            'exposure_data', 'dmg_state')
        totals = models.DmgDistTotal.objects.filter(
            dmg_state__risk_calculation=job).order_by(
            'dmg_state')
        data = [[[m.mean, m.stddev] for m in per_asset],
                [[total.mean, total.stddev] for total in totals]]
        return data

    def expected_data(self):
        return [
            [[2665.9251, 385.4088], [320.9249, 363.2749],
             [13.1498, 23.8620], [208.2695, 307.3967],
             [533.6744, 177.1909], [258.0559, 251.5760],
             [638.7025, 757.9946], [670.4166, 539.3635],
             [690.8808, 883.1827]],
            [[3512.8972, 1239.1419], [1525.0160, 685.8950],
             [962.0867, 1051.8785]]]
