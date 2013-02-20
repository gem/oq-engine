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

import numpy
from nose.plugins.attrib import attr

from qa_tests import risk
from tests.utils import helpers
from openquake.engine.db import models


class ScenarioDamageRiskCase1TestCase(risk.BaseRiskQATestCase):
    cfg = os.path.join(os.path.dirname(__file__), 'job.ini')

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

    def hazard_id(self):
        job = helpers.get_hazard_job(
            helpers.demo_file("scenario_hazard/job.ini"))
        hc = job.hazard_calculation
        job.hazard_calculation = models.HazardCalculation.objects.create(
            owner=hc.owner, truncation_level=hc.truncation_level,
            maximum_distance=hc.maximum_distance,
            intensity_measure_types=["PGA"],
            calculation_mode="scenario")
        job.status = "complete"
        job.save()

        output = models.Output.objects.create_output(
            job, "Test Hazard output", "gmf_scenario")

        fname = os.path.join(os.path.dirname(__file__), 'gmf_scenario.csv')
        with open(fname, 'rb') as csvfile:
            gmfreader = csv.reader(csvfile, delimiter=',')
            locations = gmfreader.next()

            arr = numpy.array([[float(x) for x in row] for row in gmfreader])
            for i, gmvs in enumerate(arr.transpose()):

                # In order to test properly the hazard getter we split
                # the available ground motion values in two result
                # groups (that we expect to be both considered).
                models.GmfScenario.objects.create(
                    output=output,
                    imt="PGA",
                    gmvs=gmvs[0:5],
                    result_grp_ordinal=1,
                    location="POINT(%s)" % locations[i])
                models.GmfScenario.objects.create(
                    output=output,
                    imt="PGA",
                    gmvs=gmvs[5:],
                    result_grp_ordinal=2,
                    location="POINT(%s)" % locations[i])

        return output.id

    def expected_outputs(self):
        return [self.EXPECTED_DMG_DIST_PER_ASSET,
                self.EXPECTED_DMG_DIST_PER_TAXONOMY,
                self.EXPECTED_DMG_DIST_TOTAL,
                self.EXPECTED_COLLAPSE_MAP]
