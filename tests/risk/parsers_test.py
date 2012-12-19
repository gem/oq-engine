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

import unittest
import StringIO

from nrml.risk import parsers


class ExposureModelParserTestCase(unittest.TestCase):

    def test_schema_validation(self):
        invalid_exposure = """\
<?xml version='1.0' encoding='utf-8'?>
  <nrml xmlns:gml="http://www.opengis.net/gml"
    xmlns="http://openquake.org/xmlns/nrml/0.4">
    <exposureModel gml:id="ep1"/>
</nrml>
"""

        self.assertRaises(ValueError, parsers.ExposureModelParser,
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
        for ctr, (exposure_point, occupancy_data, exposure_data)\
            in enumerate(parser):

            self.assertEqual(expected_result[ctr][0], exposure_point)
            self.assertEqual(expected_result[ctr][1], occupancy_data)
            self.assertEqual(expected_result[ctr][2], exposure_data)
