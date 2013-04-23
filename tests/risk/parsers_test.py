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

from lxml.etree import DocumentInvalid
from openquake.nrmllib.risk import parsers


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
    <exposureModel gml:id="ep1"/>
</nrml>
"""

        self.assertRaises(DocumentInvalid, parsers.ExposureModelParser,
                          StringIO.StringIO(invalid_exposure))

    def test_parsing(self):
        exposure = """\
<?xml version='1.0' encoding='utf-8'?>
  <nrml xmlns:gml="http://www.opengis.net/gml"
    xmlns="http://openquake.org/xmlns/nrml/0.4">

  <exposureModel gml:id="ep1">
    <config/>
    <exposureList gml:id="PAV01" areaType="per_asset" areaUnit="GBP"
      assetCategory="buildings" cocoType="per_area" cocoUnit="CHF"
      recoType="aggregated" recoUnit="EUR" stcoType="aggregated"
      stcoUnit="USD">

      <gml:description>Buildings in Pavia</gml:description>
      <taxonomySource>Pavia taxonomy</taxonomySource>
      <assetDefinition gml:id="asset_01">
        <site>
          <gml:Point srsName="epsg:4326">
            <gml:pos>9.15000 45.16667</gml:pos>
          </gml:Point>
        </site>

        <area>120</area>
        <coco>12.95</coco>
        <deductible>55</deductible>
        <limit>999</limit>
        <number>7</number>
        <reco>109876</reco>
        <stco>150000</stco>
        <taxonomy>RC/DMRF-D/LR</taxonomy>
      </assetDefinition>

      <assetDefinition gml:id="asset_02">
        <site>
          <gml:Point srsName="epsg:4326">
            <gml:pos>9.15333 45.12200</gml:pos>
          </gml:Point>
        </site>

        <area>119</area>
        <coco>21.95</coco>
        <deductible>66</deductible>
        <limit>1999</limit>
        <number>6</number>
        <occupants description="day">12</occupants>
        <occupants description="night">50</occupants>
        <reco>205432</reco>
        <stco>250000</stco>
        <taxonomy>RC/DMRF-D/HR</taxonomy>
      </assetDefinition>

    </exposureList>
  </exposureModel>
</nrml>
"""

        expected_result = [
            ([9.15000, 45.16667], [], {
                "area": 120.0,
                "areaType": "per_asset",
                "areaUnit": "GBP",
                "assetCategory": "buildings",
                "assetID": "asset_01",
                "coco": 12.95,
                "cocoType": "per_area",
                "cocoUnit": "CHF",
                "deductible": 55.0,
                "limit": 999.0,
                "listDescription": "Buildings in Pavia",
                "listID": "PAV01",
                "number": 7.0,
                "reco": 109876.0,
                "recoType": "aggregated",
                "recoUnit": "EUR",
                "stco": 150000.0,
                "stcoType": "aggregated",
                "stcoUnit": "USD",
                "taxonomy": "RC/DMRF-D/LR",
                "taxonomySource": "Pavia taxonomy",
            }),
            ([9.15333, 45.12200], [
            parsers.OCCUPANCY(12, "day"), parsers.OCCUPANCY(50, "night")], {
                 "area": 119.0,
                 "areaType": "per_asset",
                 "areaUnit": "GBP",
                 "assetCategory": "buildings",
                 "assetID": "asset_02",
                 "coco": 21.95,
                 "cocoType": "per_area",
                 "cocoUnit": "CHF",
                 "deductible": 66.0,
                 "limit": 1999.0,
                 "listDescription": "Buildings in Pavia",
                 "listID": "PAV01",
                 "number": 6.0,
                 "reco": 205432.0,
                 "recoType": "aggregated",
                 "recoUnit": "EUR",
                 "stco": 250000.0,
                 "stcoType": "aggregated",
                 "stcoUnit": "USD",
                 "taxonomy": "RC/DMRF-D/HR",
                 "taxonomySource": "Pavia taxonomy",
            }),
        ]

        parser = parsers.ExposureModelParser(StringIO.StringIO(exposure))
        for ctr, (exposure_point, occupancy_data, exposure_data) \
                in enumerate(parser):

            self.assertEqual(expected_result[ctr][0], exposure_point)
            self.assertEqual(expected_result[ctr][1], occupancy_data)
            self.assertEqual(expected_result[ctr][2], exposure_data)


class VulnerabilityModelParserTestCase(unittest.TestCase):

    def test_schema_validation(self):
        invalid_vulnerability_model = """\
<?xml version='1.0' encoding='utf-8'?>
  <nrml xmlns:gml="http://www.opengis.net/gml"
    xmlns="http://openquake.org/xmlns/nrml/0.4">
    <vulnerabilityModel/>
</nrml>
"""

        self.assertRaises(DocumentInvalid, parsers.VulnerabilityModelParser,
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
        <lossRatio>0.18 0.36 0.36 0.36</lossRatio>
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

        self.assertEqual([0.18, 0.36, 0.36, 0.36], model["PK"]["lossRatio"])

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
