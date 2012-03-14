# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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


from collections import namedtuple

from django.db import transaction
from django.db.utils import DatabaseError
from django.test import TestCase

from openquake import shapes
from openquake.db import models

from tests.utils import helpers


class ExposureModelTestCase(TestCase, helpers.DbTestCase):
    """Test the exposure_model database constraints."""

    job = None

    @classmethod
    def setUpClass(cls):
        cls.job = cls.setup_classic_job()

    @classmethod
    def tearDownClass(cls):
        cls.teardown_job(cls.job)

    def setUp(self):
        emdl_input = models.Input(
            input_type="exposure", size=123, path="/tmp/fake-exposure-path",
            owner=self.job.owner)
        emdl_input.save()
        i2j = models.Input2job(input=emdl_input, oq_job=self.job)
        i2j.save()
        self.mdl = models.ExposureModel(input=emdl_input, owner=self.job.owner,
                                        name="exposure-model-testing",
                                        category="economic loss")

    def test_exposure_model_with_no_area_type_coco_per_area(self):
        # area type not set but contents cost type is 'per_area' -> exception
        self.mdl.coco_type = "per_area"
        self.mdl.coco_unit = "BBD"
        try:
            self.mdl.save()
        except DatabaseError, de:
            self.assertEqual(
                "Exception: area_type is mandatory for <coco_type=per_area> "
                "(exposure_model)", de.args[0].split('\n', 1)[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_exposure_model_with_no_area_type_reco_per_area(self):
        # area type not set but retrofitting cost type is 'per_area'
        #   -> exception
        self.mdl.reco_type = "per_area"
        self.mdl.reco_unit = "USD"
        try:
            self.mdl.save()
        except DatabaseError, de:
            self.assertEqual(
                "Exception: area_type is mandatory for <reco_type=per_area> "
                "(exposure_model)", de.args[0].split('\n', 1)[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_exposure_model_with_no_area_type_stco_per_area(self):
        # area type not set but structural cost type is 'per_area'
        #   -> exception
        self.mdl.stco_type = "per_area"
        self.mdl.stco_unit = "MGF"
        try:
            self.mdl.save()
        except DatabaseError, de:
            self.assertEqual(
                "Exception: area_type is mandatory for <stco_type=per_area> "
                "(exposure_model)", de.args[0].split('\n', 1)[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_exposure_model_with_no_area_type_and_reco_stco_per_area(self):
        # area type not set but retrofitting and structural cost type is
        # 'per_area' -> exception
        self.mdl.reco_type = "per_area"
        self.mdl.reco_unit = "CHF"
        self.mdl.stco_type = "per_area"
        self.mdl.stco_unit = "GBP"
        try:
            self.mdl.save()
        except DatabaseError, de:
            self.assertEqual(
                "Exception: area_type is mandatory for <reco_type=per_area, "
                "stco_type=per_area> (exposure_model)",
                de.args[0].split('\n', 1)[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_exposure_model_with_no_area_unit_coco_per_area(self):
        # area unit not set but contents cost type is 'per_area' -> exception
        self.mdl.stco_type = "per_asset"
        self.mdl.stco_unit = "LTL"
        self.mdl.coco_type = "per_area"
        self.mdl.coco_unit = "BZD"
        self.mdl.area_type = "per_asset"
        try:
            self.mdl.save()
        except DatabaseError, de:
            self.assertEqual(
                "Exception: area_unit is mandatory for <coco_type=per_area> "
                "(exposure_model)",
                de.args[0].split('\n', 1)[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_exposure_model_with_no_area_unit_reco_per_area(self):
        # area unit not set but retrofitting cost type is 'per_area'
        #   -> exception
        self.mdl.reco_type = "per_area"
        self.mdl.reco_unit = "RWF"
        self.mdl.area_type = "per_asset"
        try:
            self.mdl.save()
        except DatabaseError, de:
            self.assertEqual(
                "Exception: area_unit is mandatory for <reco_type=per_area> "
                "(exposure_model)",
                de.args[0].split('\n', 1)[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_exposure_model_with_no_area_unit_stco_per_area(self):
        # area unit not set but structural cost type is 'per_area'
        #   -> exception
        self.mdl.stco_type = "per_area"
        self.mdl.stco_unit = "XOF"
        self.mdl.area_type = "per_asset"
        try:
            self.mdl.save()
        except DatabaseError, de:
            self.assertEqual(
                "Exception: area_unit is mandatory for <stco_type=per_area> "
                "(exposure_model)",
                de.args[0].split('\n', 1)[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_exposure_model_with_no_area_unit_and_reco_stco_per_area(self):
        # area unit not set but retrofitting and structural cost type is
        # 'per_area' -> exception
        self.mdl.reco_type = "per_area"
        self.mdl.reco_unit = "CHF"
        self.mdl.stco_type = "per_area"
        self.mdl.stco_unit = "AZM"
        self.mdl.area_type = "per_asset"
        try:
            self.mdl.save()
        except DatabaseError, de:
            self.assertEqual(
                "Exception: area_unit is mandatory for <reco_type=per_area, "
                "stco_type=per_area> (exposure_model)",
                de.args[0].split('\n', 1)[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_exposure_model_with_coco_type_but_no_coco_unit(self):
        # contents cost type set but contents cost unit not set
        #   -> exception
        self.mdl.stco_type = "per_asset"
        self.mdl.stco_unit = "TMM"
        self.mdl.coco_type = "aggregated"
        try:
            self.mdl.save()
        except DatabaseError, de:
            self.assertEqual(
                "Exception: coco_unit (None) and coco_type (aggregated) must "
                "both be either defined or undefined (exposure_model)",
                de.args[0].split('\n', 1)[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_exposure_model_with_reco_type_but_no_reco_unit(self):
        # retrofitting cost type set but retrofitting cost unit not set
        #   -> exception
        self.mdl.reco_type = "aggregated"
        try:
            self.mdl.save()
        except DatabaseError, de:
            self.assertEqual(
                "Exception: reco_unit (None) and reco_type (aggregated) must "
                "both be either defined or undefined (exposure_model)",
                de.args[0].split('\n', 1)[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_exposure_model_with_stco_type_but_no_stco_unit(self):
        # structural cost type set but structural cost unit not set
        #   -> exception
        self.mdl.stco_type = "aggregated"
        try:
            self.mdl.save()
        except DatabaseError, de:
            self.assertEqual(
                "Exception: stco_unit (None) and stco_type (aggregated) must "
                "both be either defined or undefined (exposure_model)",
                de.args[0].split('\n', 1)[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_exposure_model_with_coco_unit_but_no_coco_type(self):
        # contents cost unit set but contents cost type not set
        #   -> exception
        self.mdl.coco_unit = "BMD"
        try:
            self.mdl.save()
        except DatabaseError, de:
            self.assertEqual(
                "Exception: coco_unit (BMD) and coco_type (None) must both be "
                "either defined or undefined (exposure_model)",
                de.args[0].split('\n', 1)[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_exposure_model_with_reco_unit_but_no_reco_type(self):
        # retrofitting cost unit set but retrofitting cost type not set
        #   -> exception
        self.mdl.reco_unit = "CAD"
        try:
            self.mdl.save()
        except DatabaseError, de:
            self.assertEqual(
                "Exception: reco_unit (CAD) and reco_type (None) must both be "
                "either defined or undefined (exposure_model)",
                de.args[0].split('\n', 1)[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_exposure_model_with_stco_unit_but_no_stco_type(self):
        # structural cost unit set but structural cost type not set
        #   -> exception
        self.mdl.stco_unit = "FJD"
        try:
            self.mdl.save()
        except DatabaseError, de:
            self.assertEqual(
                "Exception: stco_unit (FJD) and stco_type (None) must both be "
                "either defined or undefined (exposure_model)",
                de.args[0].split('\n', 1)[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_exposure_model_with_no_stco_type_and_not_population(self):
        # structural cost type set must be set unless we are calculating
        # exposure in terms of population    -> exception
        self.mdl.category = "economic loss"
        try:
            self.mdl.save()
        except DatabaseError, de:
            self.assertEqual(
                "Exception: structural cost type is mandatory for "
                "<category=economic loss> (exposure_model)",
                de.args[0].split('\n', 1)[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")


class ExposureDataTestCase(TestCase, helpers.DbTestCase):
    """Test the exposure_data database constraints."""

    job = None

    @classmethod
    def setUpClass(cls):
        cls.job = cls.setup_classic_job()

    @classmethod
    def tearDownClass(cls):
        cls.teardown_job(cls.job)

    def setUp(self):
        emdl_input = models.Input(
            input_type="exposure", size=123, path="/tmp/fake-exposure-path",
            owner=self.job.owner)
        emdl_input.save()
        i2j = models.Input2job(input=emdl_input, oq_job=self.job)
        i2j.save()
        self.mdl = models.ExposureModel(input=emdl_input, owner=self.job.owner,
                                        name="exposure-data-testing",
                                        category="economic loss")
        self.mdl.stco_type = "aggregated"
        self.mdl.stco_unit = "GYD"

    def test_exposure_data_with_no_stco_and_population(self):
        # the structural cost needs not be present when we calculate exposure
        # in terms of population
        self.mdl.stco_type = None
        self.mdl.stco_unit = None
        self.mdl.category = "population"
        self.mdl.save()
        site = shapes.Site(-122.5000, 37.5000)
        edata = models.ExposureData(
            exposure_model=self.mdl, asset_ref=helpers.random_string(),
            taxonomy=helpers.random_string(), number_of_units=111,
            site=site.point.to_wkt())
        edata.save()

    def test_exposure_data_with_no_stco_and_category_not_population(self):
        # the structural cost must be present when we calculate exposure
        # in terms other than population.
        self.mdl.save()
        site = shapes.Site(-122.4000, 37.6000)
        edata = models.ExposureData(
            exposure_model=self.mdl, asset_ref=helpers.random_string(),
            taxonomy=helpers.random_string(), number_of_units=111,
            site=site.point.to_wkt())
        try:
            edata.save()
        except DatabaseError, de:
            self.assertEqual(
                "Exception: structural cost is mandatory for category "
                "<economic loss> (exposure_data)",
                de.args[0].split('\n', 1)[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_exposure_data_with_no_number_and_population(self):
        # the 'number_of_units' datum must be present when we calculate
        # exposure in terms of population
        self.mdl.category = "population"
        self.mdl.save()
        site = shapes.Site(-122.3000, 37.7000)
        edata = models.ExposureData(
            exposure_model=self.mdl, asset_ref=helpers.random_string(),
            taxonomy=helpers.random_string(),
            site=site.point.to_wkt())
        try:
            edata.save()
        except DatabaseError, de:
            self.assertEqual(
                "Exception: number_of_units is mandatory for "
                "<category=population> (exposure_data)",
                de.args[0].split('\n', 1)[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_exposure_data_with_no_number_and_stco_type_not_aggregated(self):
        # the 'number_of_units' datum must be present when the structural
        # cost type is not 'aggregated'.
        self.mdl.stco_type = "per_asset"
        self.mdl.save()
        site = shapes.Site(-122.2000, 37.8000)
        edata = models.ExposureData(
            exposure_model=self.mdl, asset_ref=helpers.random_string(),
            taxonomy=helpers.random_string(), stco=11.0,
            site=site.point.to_wkt())
        try:
            edata.save()
        except DatabaseError, de:
            self.assertEqual(
                "Exception: number_of_units is mandatory for "
                "<stco_type=per_asset> (exposure_data)",
                de.args[0].split('\n', 1)[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_exposure_data_with_no_number_and_reco_type_not_aggregated(self):
        # the 'number_of_units' datum must be present when the retrofitting
        # cost type is not 'aggregated'.
        self.mdl.reco_type = "per_asset"
        self.mdl.reco_unit = "LSM"
        self.mdl.save()
        site = shapes.Site(-122.2000, 37.9000)
        edata = models.ExposureData(
            exposure_model=self.mdl, asset_ref=helpers.random_string(),
            taxonomy=helpers.random_string(), stco=12.0, reco=13.0,
            site=site.point.to_wkt())
        try:
            edata.save()
        except DatabaseError, de:
            self.assertEqual(
                "Exception: number_of_units is mandatory for "
                "<reco_type=per_asset> (exposure_data)",
                de.args[0].split('\n', 1)[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_exposure_data_with_no_number_and_coco_type_not_aggregated(self):
        # the 'number_of_units' datum must be present when the contents
        # cost type is not 'aggregated'.
        self.mdl.coco_type = "per_asset"
        self.mdl.coco_unit = "SUR"
        self.mdl.save()
        site = shapes.Site(-122.0000, 38.0000)
        edata = models.ExposureData(
            exposure_model=self.mdl, asset_ref=helpers.random_string(),
            taxonomy=helpers.random_string(), stco=14.0, coco=15.0,
            site=site.point.to_wkt())
        try:
            edata.save()
        except DatabaseError, de:
            self.assertEqual(
                "Exception: number_of_units is mandatory for "
                "<coco_type=per_asset> (exposure_data)",
                de.args[0].split('\n', 1)[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_exposure_data_with_no_number_and_coco_reco_not_aggregated(self):
        # the 'number_of_units' datum must be present when the contents
        # and retrofitting cost type is not 'aggregated'.
        self.mdl.area_type = "per_asset"
        self.mdl.area_unit = "sqm"
        self.mdl.reco_type = "per_area"
        self.mdl.reco_unit = "TJR"
        self.mdl.coco_type = "per_asset"
        self.mdl.coco_unit = "MVR"
        self.mdl.save()
        site = shapes.Site(-121.9000, 38.1000)
        edata = models.ExposureData(
            exposure_model=self.mdl, asset_ref=helpers.random_string(),
            taxonomy=helpers.random_string(), stco=16.0, coco=17.0,
            site=site.point.to_wkt())
        try:
            edata.save()
        except DatabaseError, de:
            self.assertEqual(
                "Exception: number_of_units is mandatory for "
                "<coco_type=per_asset, reco_type=per_area> (exposure_data)",
                de.args[0].split('\n', 1)[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_exposure_reco_type_but_no_reco_value(self):
        # the retrofitting cost must be present if the retrofitting cost type
        # is set.
        self.mdl.reco_type = "per_asset"
        self.mdl.reco_unit = "INR"
        self.mdl.save()
        site = shapes.Site(-121.8000, 38.2000)
        edata = models.ExposureData(
            exposure_model=self.mdl, asset_ref=helpers.random_string(),
            taxonomy=helpers.random_string(), stco=18.0, number_of_units=22,
            site=site.point.to_wkt())
        try:
            edata.save()
        except DatabaseError, de:
            self.assertEqual(
                "Exception: retrofitting cost is mandatory for "
                "<reco_type=per_asset> (exposure_data)",
                de.args[0].split('\n', 1)[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_exposure_coco_type_but_no_coco_value(self):
        # the contents cost must be present if the contents cost type
        # is set.
        self.mdl.coco_type = "per_asset"
        self.mdl.coco_unit = "MUR"
        self.mdl.save()
        site = shapes.Site(-121.7000, 38.3000)
        edata = models.ExposureData(
            exposure_model=self.mdl, asset_ref=helpers.random_string(),
            taxonomy=helpers.random_string(), stco=19.0, number_of_units=23,
            site=site.point.to_wkt())
        try:
            edata.save()
        except DatabaseError, de:
            self.assertEqual(
                "Exception: contents cost is mandatory for "
                "<coco_type=per_asset> (exposure_data)",
                de.args[0].split('\n', 1)[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_exposure_stco_type_but_no_stco_value(self):
        # the structural cost must be present if the structural cost type
        # is set.
        self.mdl.category = "population"
        self.mdl.save()
        site = shapes.Site(-121.6000, 38.4000)
        edata = models.ExposureData(
            exposure_model=self.mdl, asset_ref=helpers.random_string(),
            taxonomy=helpers.random_string(), number_of_units=24,
            site=site.point.to_wkt())
        try:
            edata.save()
        except DatabaseError, de:
            self.assertEqual(
                "Exception: structural cost is mandatory for "
                "<stco_type=aggregated> (exposure_data)",
                de.args[0].split('\n', 1)[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_exposure_reco_type_per_area_but_no_area_value(self):
        # the area must be set if the retrofitting cost type is 'per_area'
        self.mdl.reco_type = "per_area"
        self.mdl.reco_unit = "NPR"
        self.mdl.area_type = "aggregated"
        self.mdl.area_unit = "PKR"
        self.mdl.save()
        site = shapes.Site(-121.5000, 38.5000)
        edata = models.ExposureData(
            exposure_model=self.mdl, asset_ref=helpers.random_string(),
            taxonomy=helpers.random_string(), stco=20.0,
            site=site.point.to_wkt())
        try:
            edata.save()
        except DatabaseError, de:
            self.assertEqual(
                "Exception: area is mandatory for <reco_type=per_area> "
                "(exposure_data)",
                de.args[0].split('\n', 1)[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_exposure_coco_type_per_area_but_no_area_value(self):
        # the area must be set if the contents cost type is 'per_area'
        self.mdl.coco_type = "per_area"
        self.mdl.coco_unit = "SCR"
        self.mdl.area_type = "aggregated"
        self.mdl.area_unit = "LKR"
        self.mdl.save()
        site = shapes.Site(-121.4000, 38.6000)
        edata = models.ExposureData(
            exposure_model=self.mdl, asset_ref=helpers.random_string(),
            taxonomy=helpers.random_string(), stco=21.0,
            site=site.point.to_wkt())
        try:
            edata.save()
        except DatabaseError, de:
            self.assertEqual(
                "Exception: area is mandatory for <coco_type=per_area> "
                "(exposure_data)",
                de.args[0].split('\n', 1)[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_exposure_stco_type_per_area_but_no_area_value(self):
        # the area must be set if the structural cost type is 'per_area'
        self.mdl.stco_type = "per_area"
        self.mdl.stco_unit = "IDR"
        self.mdl.area_type = "aggregated"
        self.mdl.area_unit = "ATS"
        self.mdl.save()
        site = shapes.Site(-121.3000, 38.7000)
        edata = models.ExposureData(
            exposure_model=self.mdl, asset_ref=helpers.random_string(),
            taxonomy=helpers.random_string(), stco=22.0,
            site=site.point.to_wkt())
        try:
            edata.save()
        except DatabaseError, de:
            self.assertEqual(
                "Exception: area is mandatory for <stco_type=per_area> "
                "(exposure_data)",
                de.args[0].split('\n', 1)[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")


class PerAssetValueTestCase(TestCase):
    """Test and exercise the per_asset_value() function."""

    # risk exposure data
    REXD = namedtuple(
        "REXD", "cost, cost_type, area, area_type, number_of_units")

    def test_per_asset_value_with_cost_type_aggreggated(self):
        # When the cost type is 'aggregated' per_asset_value() simply returns
        # the cost value.
        exd = self.REXD(cost=22.0, cost_type="aggregated", area=0.0,
                        area_type="aggregated", number_of_units=0.0)
        self.assertEqual(exd.cost, models.per_asset_value(exd))

    def test_per_asset_value_with_cost_type_per_asset(self):
        # When the cost type is 'per_asset' per_asset_value() returns:
        # cost * number_of_units
        exd = self.REXD(cost=23.0, cost_type="per_asset", area=0.0,
                        area_type="aggregated", number_of_units=2.0)
        self.assertEqual(exd.cost * exd.number_of_units,
                         models.per_asset_value(exd))

    def test_per_asset_value_with_cost_type_per_area_and_aggregated(self):
        # When the cost type is 'per_area' and the area type is 'aggregated'
        # per_asset_value() returns: cost * area
        exd = self.REXD(cost=24.0, cost_type="per_area", area=3.0,
                        area_type="aggregated", number_of_units=0.0)
        self.assertEqual(exd.cost * exd.area, models.per_asset_value(exd))

    def test_per_asset_value_with_cost_type_per_area_and_per_asset(self):
        # When the cost type is 'per_area' and the area type is 'per_asset'
        # per_asset_value() returns: cost * area * number_of_units
        exd = self.REXD(cost=25.0, cost_type="per_area", area=4.0,
                        area_type="per_asset", number_of_units=5.0)
        self.assertEqual(exd.cost * exd.area * exd.number_of_units,
                         models.per_asset_value(exd))

    def test_per_asset_value_with_invalid_exposure_data(self):
        # When the exposure data is invalid per_asset_value() returns: -1.0
        exd = self.REXD(cost=26.0, cost_type="too-expensive", area=0.0,
                        area_type="rough", number_of_units=0.0)
        self.assertRaises(ValueError, models.per_asset_value, exd)
