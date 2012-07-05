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
import tempfile
import unittest

from django.contrib.gis import geos

from openquake import xml
from openquake import shapes
from openquake.db import models
from openquake.output.scenario_damage import DmgDistPerAssetXMLWriter
from openquake.output.scenario_damage import DmgDistPerTaxonomyXMLWriter
from openquake.output.scenario_damage import DmgDistTotalXMLWriter
from openquake.output.scenario_damage import CollapseMapXMLWriter

from tests.utils import helpers


class DmgDistPerAssetXMLWriterTestCase(unittest.TestCase, helpers.DbTestCase):

    job = None

    @classmethod
    def setUpClass(cls):
        inputs = [("exposure", "")]
        cls.job = cls.setup_classic_job(inputs=inputs)

    def setUp(self):
        self.data = []
        self.dda = None

        self.damage_states = ["no_damage", "slight", "moderate",
                "extensive", "complete"]

    def test_serialize(self):
        expected_file = helpers.get_data_path(
            "expected-dmg-dist-per-asset.xml")

        expected_text = open(expected_file, "r").readlines()

        self.make_dist()
        asset_1, asset_2, asset_3 = self.make_assets()

        self.make_data(asset_1, "no_damage", 1.0, 1.6)
        self.make_data(asset_1, "slight", 34.8, 18.3)
        self.make_data(asset_1, "moderate", 64.2, 19.8)
        self.make_data(asset_1, "extensive", 64.3, 19.7)
        self.make_data(asset_1, "complete", 64.3, 19.7)

        self.make_data(asset_2, "no_damage", 1.0, 1.6)
        self.make_data(asset_2, "slight", 34.8, 18.3)
        self.make_data(asset_2, "moderate", 64.2, 19.8)
        self.make_data(asset_2, "extensive", 64.3, 19.7)
        self.make_data(asset_2, "complete", 64.3, 19.7)

        self.make_data(asset_3, "no_damage", 1.1, 1.7)
        self.make_data(asset_3, "slight", 34.9, 18.4)
        self.make_data(asset_3, "moderate", 64.3, 19.7)
        self.make_data(asset_3, "extensive", 64.3, 19.7)
        self.make_data(asset_3, "complete", 64.3, 19.7)

        try:
            _, result_xml = tempfile.mkstemp()

            writer = DmgDistPerAssetXMLWriter(result_xml,
                    "ebl1", self.damage_states)

            writer.serialize(self.data)
            actual_text = open(result_xml, "r").readlines()

            self.assertEqual(expected_text, actual_text)

            self.assertTrue(xml.validates_against_xml_schema(
                    result_xml))
        finally:
            os.unlink(result_xml)

    def test_no_empty_dist(self):
        # an empty distribution is not supported by the schema
        writer = DmgDistPerAssetXMLWriter("output.xml",
                "ebl1", self.damage_states)

        self.assertRaises(RuntimeError, writer.serialize, [])
        self.assertFalse(os.path.exists("output.xml"))

        self.assertRaises(RuntimeError, writer.serialize, None)
        self.assertFalse(os.path.exists("output.xml"))

    def make_assets(self):
        [ism] = models.inputs4job(self.job.id, input_type="exposure")

        em = models.ExposureModel(
            owner=ism.owner, input=ism,
            name="AAA", category="single_asset",
            reco_type="aggregated", reco_unit="USD",
            stco_type="aggregated", stco_unit="USD")

        em.save()

        site_1 = shapes.Site(-116.0, 41.0)
        site_2 = shapes.Site(-117.0, 42.0)

        asset_1 = models.ExposureData(
            exposure_model=em, taxonomy="RC",
            asset_ref="asset_1", number_of_units=100, stco=1,
            site=geos.GEOSGeometry(site_1.point.to_wkt()), reco=1)

        asset_2 = models.ExposureData(
            exposure_model=em, taxonomy="RM",
            asset_ref="asset_2", number_of_units=40, stco=1,
            site=geos.GEOSGeometry(site_2.point.to_wkt()), reco=1)

        asset_3 = models.ExposureData(
            exposure_model=em, taxonomy="RM",
            asset_ref="asset_3", number_of_units=40, stco=1,
            site=geos.GEOSGeometry(site_2.point.to_wkt()), reco=1)

        asset_1.save()
        asset_2.save()
        asset_3.save()

        return asset_1, asset_2, asset_3

    def make_dist(self):
        output = models.Output(
            owner=self.job.owner,
            oq_job=self.job,
            display_name="",
            db_backed=True,
            output_type="dmg_dist_per_asset")

        output.save()

        self.dda = models.DmgDistPerAsset(
            output=output,
            dmg_states=self.damage_states)

        self.dda.save()

    def make_data(self, asset, dmg_state, mean, stddev):
        data = models.DmgDistPerAssetData(
            dmg_dist_per_asset=self.dda,
            exposure_data=asset,
            dmg_state=dmg_state,
            mean=mean,
            stddev=stddev,
            location=asset.site)

        data.save()
        self.data.append(data)


class CollapseMapXMLWriterTestCase(unittest.TestCase, helpers.DbTestCase):

    job = None

    @classmethod
    def setUpClass(cls):
        inputs = [("exposure", "")]
        cls.job = cls.setup_classic_job(inputs=inputs)

    def setUp(self):
        self.data = []

        self.em = None
        self.cm = None

    def test_serialize(self):
        expected_file = helpers.get_data_path(
            "expected-collapse-map.xml")

        expected_text = open(expected_file, "r").readlines()

        asset_1, asset_2, asset_3, asset_4 = self.make_assets()
        self.make_map()

        self.make_data(asset_1, 1.6, 1.7)
        self.make_data(asset_2, 2.9, 3.1)
        self.make_data(asset_3, 4.9, 5.1)
        self.make_data(asset_4, 10.6, 11.7)

        try:
            _, result_xml = tempfile.mkstemp()

            writer = CollapseMapXMLWriter(result_xml, "ebl1")

            writer.serialize(self.data)
            actual_text = open(result_xml, "r").readlines()

            self.assertEqual(expected_text, actual_text)

            self.assertTrue(xml.validates_against_xml_schema(
                    result_xml))
        finally:
            os.unlink(result_xml)

    def test_no_empty_dist(self):
        # an empty distribution is not supported by the schema
        writer = CollapseMapXMLWriter("output.xml", "ebl1")

        self.assertRaises(RuntimeError, writer.serialize, [])
        self.assertFalse(os.path.exists("output.xml"))

        self.assertRaises(RuntimeError, writer.serialize, None)
        self.assertFalse(os.path.exists("output.xml"))

    def make_assets(self):
        [ism] = models.inputs4job(self.job.id, input_type="exposure")

        self.em = models.ExposureModel(
            owner=ism.owner, input=ism,
            name="AAA", category="single_asset",
            reco_type="aggregated", reco_unit="USD",
            stco_type="aggregated", stco_unit="USD")

        self.em.save()

        site_1 = shapes.Site(-72.20, 18.00)
        site_2 = shapes.Site(-72.25, 18.00)

        asset_1 = models.ExposureData(
            exposure_model=self.em, taxonomy="RC",
            asset_ref="a1", number_of_units=100, stco=1,
            site=geos.GEOSGeometry(site_1.point.to_wkt()), reco=1)

        asset_2 = models.ExposureData(
            exposure_model=self.em, taxonomy="RM",
            asset_ref="a2", number_of_units=40, stco=1,
            site=geos.GEOSGeometry(site_1.point.to_wkt()), reco=1)

        asset_3 = models.ExposureData(
            exposure_model=self.em, taxonomy="RM",
            asset_ref="a3", number_of_units=40, stco=1,
            site=geos.GEOSGeometry(site_1.point.to_wkt()), reco=1)

        asset_4 = models.ExposureData(
            exposure_model=self.em, taxonomy="RM",
            asset_ref="a4", number_of_units=40, stco=1,
            site=geos.GEOSGeometry(site_2.point.to_wkt()), reco=1)

        asset_1.save()
        asset_2.save()
        asset_3.save()
        asset_4.save()

        return asset_1, asset_2, asset_3, asset_4

    def make_map(self):
        output = models.Output(
            owner=self.job.owner,
            oq_job=self.job,
            display_name="",
            db_backed=True,
            output_type="collapse_map")

        output.save()

        self.cm = models.CollapseMap(
            output=output,
            exposure_model=self.em)

        self.cm.save()

    def make_data(self, asset, mean, stddev):
        data = models.CollapseMapData(
            collapse_map=self.cm,
            asset_ref=asset.asset_ref,
            value=mean,
            std_dev=stddev,
            location=asset.site)

        data.save()
        self.data.append(data)


class DmgDistPerTaxonomyXMLWriterTestCase(
    unittest.TestCase, helpers.DbTestCase):

    job = None

    @classmethod
    def setUpClass(cls):
        cls.job = cls.setup_classic_job(inputs=[])

    def setUp(self):
        self.data = []
        self.ddt = None

        self.damage_states = ["no_damage", "slight", "moderate",
                "extensive", "complete"]

    def test_serialize(self):
        expected_file = helpers.get_data_path(
            "expected-dmg-dist-per-taxonomy.xml")

        expected_text = open(expected_file, "r").readlines()

        self.make_dist()

        self.make_data("RC", "no_damage", 1.1, 1.7)
        self.make_data("RC", "slight", 34.9, 18.4)
        self.make_data("RC", "moderate", 64.3, 19.7)
        self.make_data("RC", "extensive", 64.3, 19.7)
        self.make_data("RC", "complete", 64.3, 19.7)

        self.make_data("RM", "no_damage", 1.2, 1.6)
        self.make_data("RM", "slight", 35.0, 18.5)
        self.make_data("RM", "moderate", 64.4, 19.8)
        self.make_data("RM", "extensive", 64.3, 19.7)
        self.make_data("RM", "complete", 64.3, 19.7)

        try:
            _, result_xml = tempfile.mkstemp()

            writer = DmgDistPerTaxonomyXMLWriter(result_xml,
                    "ebl1", self.damage_states)

            writer.serialize(self.data)
            actual_text = open(result_xml, "r").readlines()

            self.assertEqual(expected_text, actual_text)

            self.assertTrue(xml.validates_against_xml_schema(
                    result_xml))
        finally:
            os.unlink(result_xml)

    def test_no_empty_dist(self):
        # an empty distribution is not supported by the schema
        writer = DmgDistPerTaxonomyXMLWriter("output.xml",
                "ebl1", self.damage_states)

        self.assertRaises(RuntimeError, writer.serialize, [])
        self.assertFalse(os.path.exists("output.xml"))

        self.assertRaises(RuntimeError, writer.serialize, None)
        self.assertFalse(os.path.exists("output.xml"))

    def make_dist(self):
        output = models.Output(
            owner=self.job.owner,
            oq_job=self.job,
            display_name="",
            db_backed=True,
            output_type="dmg_dist_per_taxonomy")

        output.save()

        self.ddt = models.DmgDistPerTaxonomy(
            output=output,
            dmg_states=self.damage_states)

        self.ddt.save()

    def make_data(self, taxonomy, dmg_state, mean, stddev):
        data = models.DmgDistPerTaxonomyData(
            dmg_dist_per_taxonomy=self.ddt,
            taxonomy=taxonomy,
            dmg_state=dmg_state,
            mean=mean,
            stddev=stddev)

        data.save()
        self.data.append(data)


class DmgDistTotalXMLWriterTestCase(
    unittest.TestCase, helpers.DbTestCase):

    job = None

    @classmethod
    def setUpClass(cls):
        cls.job = cls.setup_classic_job(inputs=[])

    def setUp(self):
        self.data = []
        self.ddt = None

        self.damage_states = ["no_damage", "slight", "moderate",
                "extensive", "complete"]

    def test_serialize(self):
        expected_file = helpers.get_data_path(
            "expected-dmg-dist-total.xml")

        expected_text = open(expected_file, "r").readlines()

        self.make_dist()

        self.make_data("no_damage", 1.0, 1.6)
        self.make_data("slight", 34.8, 18.3)
        self.make_data("moderate", 64.2, 19.8)
        self.make_data("extensive", 64.3, 19.7)
        self.make_data("complete", 64.3, 19.7)

        try:
            _, result_xml = tempfile.mkstemp()

            writer = DmgDistTotalXMLWriter(result_xml,
                    "ebl1", self.damage_states)

            writer.serialize(self.data)
            actual_text = open(result_xml, "r").readlines()

            self.assertEqual(expected_text, actual_text)

            self.assertTrue(xml.validates_against_xml_schema(
                    result_xml))
        finally:
            os.unlink(result_xml)

    def test_no_empty_dist(self):
        # an empty distribution is not supported by the schema
        writer = DmgDistTotalXMLWriter("output.xml",
                "ebl1", self.damage_states)

        self.assertRaises(RuntimeError, writer.serialize, [])
        self.assertFalse(os.path.exists("output.xml"))

        self.assertRaises(RuntimeError, writer.serialize, None)
        self.assertFalse(os.path.exists("output.xml"))

    def make_dist(self):
        output = models.Output(
            owner=self.job.owner,
            oq_job=self.job,
            display_name="",
            db_backed=True,
            output_type="dmg_dist_total")

        output.save()

        self.ddt = models.DmgDistTotal(
            output=output,
            dmg_states=self.damage_states)

        self.ddt.save()

    def make_data(self, dmg_state, mean, stddev):
        data = models.DmgDistTotalData(
            dmg_dist_total=self.ddt,
            dmg_state=dmg_state,
            mean=mean,
            stddev=stddev)

        data.save()
        self.data.append(data)
