# coding=utf-8
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

import os
import unittest
import StringIO

from openquake.nrmllib.risk import parsers
from openquake.nrmllib import InvalidFile


EXAMPLES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'examples')


def get_example(fname):
    return os.path.join(EXAMPLES_DIR, fname)


class ExposureModelParserTestCase(unittest.TestCase):

    def test_schema_validation(self):
        invalid_exposure = """\
<?xml version='1.0' encoding='utf-8'?>
  <nrml xmlns:gml="http://www.opengis.net/gml"
    xmlns="http://openquake.org/xmlns/nrml/0.4">
    <exposureModel id="ep1"/>
</nrml>
"""

        self.assertRaises(InvalidFile, parsers.ExposureModelParser,
                          StringIO.StringIO(invalid_exposure))

    def test_parsing(self):
        exposure = """\
<?xml version='1.0' encoding='utf-8'?>
  <nrml xmlns="http://openquake.org/xmlns/nrml/0.4">

  <exposureModel id="ep1"
                 category="buildings"
                 taxonomySource="Pavia buildings">
        <conversions>
          <area type="per_asset" unit="GBP"/>
          <costTypes>
             <costType name="contents" type="per_area" unit="CHF"/>
             <costType name="structural" type="aggregated" unit="USD"
                       retrofittedType="aggregated" retrofittedUnit="EUR"/>
             <costType name="nonStructural" type="aggregated" unit="USD"/>
          </costTypes>
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

        expected_result = [
            ([9.15000, 45.16667], [], {
                "area": 120.0,
                "areaType": "per_asset",
                "areaUnit": "GBP",
                "category": "buildings",
                "id": "asset_01",
                "description": "Buildings in Pavia",
                "exposureID": "ep1",
                "number": 7.0,
                "taxonomy": "RC/DMRF-D/LR",
                "taxonomySource": "Pavia buildings",
            }, [
                parsers.Cost("contents", 12.95, None, None, None),
                parsers.Cost("structural", 150000.0, None, 55.0, 999.0),
                parsers.Cost("nonStructural", 25000.0, None, None, None)
            ], {
                "contents": ("per_area", "CHF", None, None),
                "structural": ("aggregated", "USD", "aggregated", "EUR"),
                "nonStructural": ("aggregated", "USD", None, None),
            }),
            ([9.15333, 45.12200], [
                parsers.Occupancy(12, "day"),
                parsers.Occupancy(50, "night")], {
                    "area": 119.0,
                    "areaType": "per_asset",
                    "areaUnit": "GBP",
                    "category": "buildings",
                    "id": "asset_02",
                    "description": "Buildings in Pavia",
                    "exposureID": "ep1",
                    "number": 6.0,
                    "taxonomy": "RC/DMRF-D/HR",
                    "taxonomySource": "Pavia buildings",
                }, [
                    parsers.Cost("contents", 21.95, None, None, None),
                    parsers.Cost(
                        "structural", 250000.0, None, 66.0, 1999.0)
                ], {
                    "contents": ("per_area", "CHF", None, None),
                    "structural": ("aggregated", "USD", "aggregated", "EUR"),
                    "nonStructural": ("aggregated", "USD", None, None),
                }),
        ]

        parser = parsers.ExposureModelParser(StringIO.StringIO(exposure))

        i = None
        for ctr, (exposure_point, occupancy_data, exposure_data,
                  costs, conversions) in enumerate(parser):
            self.assertEqual(expected_result[ctr][0], exposure_point)
            self.assertEqual(expected_result[ctr][1], occupancy_data)
            self.assertEqual(expected_result[ctr][2], exposure_data)
            self.assertEqual(expected_result[ctr][3], costs)
            self.assertEqual(expected_result[ctr][4], conversions)
            i = ctr

        self.assertEqual(2, i + 1)


class VulnerabilityModelParserTestCase(unittest.TestCase):

    def test_schema_validation(self):
        invalid_vulnerability_model = """\
<?xml version='1.0' encoding='utf-8'?>
  <nrml xmlns:gml="http://www.opengis.net/gml"
    xmlns="http://openquake.org/xmlns/nrml/0.4">
    <vulnerabilityModel/>
</nrml>
"""

        self.assertRaises(InvalidFile, parsers.VulnerabilityModelParser,
                          StringIO.StringIO(invalid_vulnerability_model))

    def test_parsing(self):
        vulnerability_model = """\
<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.4"
  xmlns:gml="http://www.opengis.net/gml">

  <vulnerabilityModel>
    <config/>
    <discreteVulnerabilitySet vulnerabilitySetID="PAGER"
      assetCategory="population" lossCategory="fatalities">
      <IML IMT="MMI">5.00 5.50 6.00 6.50</IML>
      <discreteVulnerability vulnerabilityFunctionID="IR" probabilisticDistribution="LN">
        <lossRatio>0.18 0.36 0.36 0.36</lossRatio>
        <coefficientsVariation>0.30 0.30 0.30 0.30</coefficientsVariation>
      </discreteVulnerability>
      <discreteVulnerability vulnerabilityFunctionID="PK" probabilisticDistribution="LN">
        <lossRatio>0.18 0.36 0.36 1.36</lossRatio>
        <coefficientsVariation>0.30 0.30 0.30 0.30</coefficientsVariation>
      </discreteVulnerability>
    </discreteVulnerabilitySet>
    <discreteVulnerabilitySet vulnerabilitySetID="NPAGER"
      assetCategory="population" lossCategory="fatalities">
      <IML IMT="MMI">6.00 6.50 7.00 7.50</IML>
      <discreteVulnerability vulnerabilityFunctionID="AA" probabilisticDistribution="LN">
        <lossRatio>0.00 0.00 0.00 0.00</lossRatio>
        <coefficientsVariation>0.50 0.50 0.50 0.50</coefficientsVariation>
      </discreteVulnerability>
      <discreteVulnerability vulnerabilityFunctionID="BB" probabilisticDistribution="LN">
        <lossRatio>0.06 0.18 0.36 0.36</lossRatio>
        <coefficientsVariation>0.30 0.30 0.30 0.30</coefficientsVariation>
      </discreteVulnerability>
    </discreteVulnerabilitySet>
  </vulnerabilityModel>
</nrml>
"""

        model = self._load_model(StringIO.StringIO(vulnerability_model))

        self.assertEqual("MMI", model["PK"]["IMT"])
        self.assertEqual("fatalities", model["PK"]["lossCategory"])
        self.assertEqual("PAGER", model["PK"]["vulnerabilitySetID"])
        self.assertEqual("population", model["PK"]["assetCategory"])
        self.assertEqual("LN", model["PK"]["probabilisticDistribution"])

        self.assertEqual([0.18, 0.36, 0.36, 1.36], model["PK"]["lossRatio"])

        self.assertEqual([0.30, 0.30, 0.30, 0.30],
                         model["PK"]["coefficientsVariation"])

        self.assertEqual([5.00, 5.50, 6.00, 6.50], model["PK"]["IML"])
        self.assertEqual([0.18, 0.36, 0.36, 0.36], model["IR"]["lossRatio"])

        self.assertEqual([0.30, 0.30, 0.30, 0.30],
                         model["IR"]["coefficientsVariation"])

        self.assertEqual([5.00, 5.50, 6.00, 6.50], model["IR"]["IML"])
        self.assertEqual("NPAGER", model["AA"]["vulnerabilitySetID"])
        self.assertEqual([6.00, 6.50, 7.00, 7.50], model["AA"]["IML"])

        self.assertEqual([0.50, 0.50, 0.50, 0.50],
                         model["AA"]["coefficientsVariation"])

    def _load_model(self, source):
        model = dict()
        parser = parsers.VulnerabilityModelParser(source)

        for vulnerability_function in parser:
            model[vulnerability_function["ID"]] = vulnerability_function

        return model


class FragilityModelParserTestCase(unittest.TestCase):

    def test_parse_continuous(self):
        p = iter(parsers.FragilityModelParser(get_example('fragm_c.xml')))

        fmt, limit_states = p.next()
        self.assertEqual(fmt, 'continuous')
        self.assertEqual(limit_states,
                         ['slight', 'moderate', 'extensive', 'complete'])

        ffs1, ffs2 = list(p)
        self.assertEqual(ffs1,
                         ('RC/DMRF-D/LR',
                          {'IMT': "PGA", 'imls': None},
                          [(11.19, 8.27), (27.98, 20.677),
                           (48.05, 42.49), (108.9, 123.7)], 0.05))
        self.assertEqual(ffs2,
                         ('RC/DMRF-D/HR',
                          {'IMT': "PGA", 'imls': None},
                          [(11.18, 8.28), (27.99, 20.667),
                           (48.06, 42.48), (108.8, 123.6)], None))

    def test_parse_discrete(self):
        p = iter(parsers.FragilityModelParser(get_example('fragm_d.xml')))

        fmt, limit_states = p.next()
        self.assertEqual(fmt, 'discrete')
        self.assertEqual(limit_states,
                         ['minor', 'moderate', 'severe', 'collapse'])

        ffs1, ffs2 = list(p)
        self.assertEqual(ffs1,
                         ('RC/DMRF-D/LR',
                          {'IMT': "MMI", 'imls': [7.0, 8.0, 9.0, 10.0, 11.0]},
                          [[0.0, 0.09, 0.56, 0.91, 0.98],
                           [0.0, 0.0, 0.04, 0.78, 0.96],
                           [0.0, 0.0, 0.0, 0.29, 0.88],
                           [0.0, 0.0, 0.0, 0.03, 0.63]], 5.0))
        self.assertEqual(ffs2,
                         ('RC/DMRF-D/HR',
                          {'IMT': "MMI", 'imls': [7.0, 8.0, 9.0, 10.0, 11.0]},
                          [[0.0, 0.09, 0.56, 0.92, 0.99],
                           [0.0, 0.0, 0.04, 0.79, 0.97],
                           [0.0, 0.0, 0.0, 0.3, 0.89],
                           [0.0, 0.0, 0.0, 0.04, 0.64]], None))
