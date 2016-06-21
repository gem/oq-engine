# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2016 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import os
import unittest
import io

from openquake.commonlib import risk_parsers as parsers
from openquake.commonlib import nrml_examples

EXAMPLES_DIR = os.path.dirname(nrml_examples.__file__)


def get_example(fname):
    return os.path.join(EXAMPLES_DIR, fname)


class ExposureModelParserTestCase(unittest.TestCase):

    def test_parsing(self):
        exposure = b"""\
<?xml version='1.0' encoding='utf-8'?>
  <nrml xmlns="http://openquake.org/xmlns/nrml/0.4">

  <exposureModel id="ep1"
                 category="buildings"
                 taxonomySource="source">
        <conversions>
          <area type="per_asset" unit="GBP"/>
          <costTypes>
             <costType name="contents" type="per_area" unit="CHF"/>
             <costType name="structural" type="aggregated" unit="USD"
                       retrofittedType="aggregated" retrofittedUnit="EUR"/>
             <costType name="nonStructural" type="aggregated" unit="USD"/>
          </costTypes>
          <deductible isAbsolute="false"/>
          <insuranceLimit isAbsolute="true"/>
        </conversions>

    <description>Buildings in Pavia</description>

    <assets>
      <asset id="asset_01" area="120" number="7" taxonomy="RC/DMRF-D/LR">
        <location lon="9.15000" lat="45.16667"/>

        <costs>
          <cost type="contents" value="12.95" />
          <cost type="structural" value="150000"
                deductible="55" insuranceLimit="999"/>
          <cost type="nonStructural" value="25000" />
        </costs>
      </asset>

      <asset id="asset_02" area="119" number="6" taxonomy="RC/DMRF-D/HR">
        <location lon="9.15333" lat="45.12200"/>

        <costs>
          <cost type="contents" value="21.95"/>
          <cost type="structural" value="250000"
                insuranceLimit="1999" deductible="66"/>
        </costs>

        <occupancies>
          <occupancy period="day" occupants="12"/>
          <occupancy period="night" occupants="50"/>
        </occupancies>
      </asset>
    </assets>
  </exposureModel>
</nrml>
"""

        parser = parsers.ExposureModelParser(io.BytesIO(exposure))

        for i, asset_data in enumerate(parser):
            self.assertEqual(
                parsers.ExposureMetadata(
                    "ep1", "source", "buildings", "Buildings in Pavia",
                    parsers.Conversions(
                        [parsers.CostType(
                            "contents", "per_area", "CHF", None, None),
                         parsers.CostType(
                             "structural",
                             "aggregated", "USD",
                             "aggregated", "EUR"),
                         parsers.CostType(
                             "nonStructural",
                             "aggregated", "USD", None, None)],
                        "per_asset", "GBP", False, True)),
                asset_data.exposure_metadata)

            self.assertEqual(
                [parsers.Site(9.15000, 45.16667),
                 parsers.Site(9.15333, 45.12200)][i],
                asset_data.site)

            self.assertEqual(["asset_01", "asset_02"][i], asset_data.asset_ref)

            self.assertEqual(
                ["RC/DMRF-D/LR", "RC/DMRF-D/HR"][i], asset_data.taxonomy)

            self.assertEqual([120, 119][i], asset_data.area)
            self.assertEqual([7, 6][i], asset_data.number)

            self.assertEqual(
                [[parsers.Cost("contents", 12.95, None, None, None),
                  parsers.Cost("structural", 150000, None, 55, 999),
                  parsers.Cost("nonStructural", 25000, None, None, None)],
                 [parsers.Cost("contents", 21.95, None, None, None),
                  parsers.Cost("structural", 250000.0, None, 66, 1999)]][i],
                asset_data.costs)

            self.assertEqual(
                [[], [parsers.Occupancy(12, "day"),
                      parsers.Occupancy(50, "night")]][i],
                asset_data.occupancy)
