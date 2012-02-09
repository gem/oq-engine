# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.


from django.test import TestCase

from django.db import transaction
from django.db.utils import DatabaseError


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
            input_type="exposure", input_set=self.job.oq_job_profile.input_set,
            size=123, path="/tmp/fake-exposure-path")
        self.mdl = models.ExposureModel(input=emdl_input, owner=self.job.owner,
                                        name="exposure-model-testing",
                                        category="economic loss")

    def test_exposure_model_with_no_area_type_coco_per_area(self):
        # area type not set but contents cost type is 'per_area' -> exception
        self.mdl.coco_type = "per_area"
        self.mdl.coco_unit = "EUR"
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
        self.mdl.stco_unit = "USD"
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
        self.mdl.stco_unit = "GBP"
        self.mdl.coco_type = "per_area"
        self.mdl.coco_unit = "EUR"
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
        self.mdl.reco_unit = "USD"
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
        self.mdl.stco_unit = "USD"
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
        self.mdl.stco_unit = "GBP"
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
        self.mdl.stco_unit = "GBP"
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
            input_type="exposure", input_set=self.job.oq_job_profile.input_set,
            size=123, path="/tmp/fake-exposure-path")
        self.mdl = models.ExposureModel(input=emdl_input, owner=self.job.owner,
                                        name="exposure-data-testing",
                                        category="economic loss")
        self.mdl.stco_type = "aggregated"
        self.mdl.stco_unit = "EUR"

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
            site="POINT(%s %s)" % (site.point.x, site.point.y))
        edata.save()

    def test_exposure_data_with_no_stco_and_category_not_population(self):
        # the structural cost must be present when we calculate exposure
        # in terms other than population.
        self.mdl.save()
        site = shapes.Site(-122.4000, 37.6000)
        edata = models.ExposureData(
            exposure_model=self.mdl, asset_ref=helpers.random_string(),
            taxonomy=helpers.random_string(), number_of_units=111,
            site="POINT(%s %s)" % (site.point.x, site.point.y))
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
            site="POINT(%s %s)" % (site.point.x, site.point.y))
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
            site="POINT(%s %s)" % (site.point.x, site.point.y))
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
        self.mdl.reco_unit = "GBP"
        self.mdl.save()
        site = shapes.Site(-122.2000, 37.9000)
        edata = models.ExposureData(
            exposure_model=self.mdl, asset_ref=helpers.random_string(),
            taxonomy=helpers.random_string(), stco=12.0, reco=13.0,
            site="POINT(%s %s)" % (site.point.x, site.point.y))
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
        self.mdl.coco_unit = "YEN"
        self.mdl.save()
        site = shapes.Site(-122.0000, 38.0000)
        edata = models.ExposureData(
            exposure_model=self.mdl, asset_ref=helpers.random_string(),
            taxonomy=helpers.random_string(), stco=14.0, coco=15.0,
            site="POINT(%s %s)" % (site.point.x, site.point.y))
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
        self.mdl.reco_unit = "YEN"
        self.mdl.coco_type = "per_asset"
        self.mdl.coco_unit = "YEN"
        self.mdl.save()
        site = shapes.Site(-121.9000, 38.1000)
        edata = models.ExposureData(
            exposure_model=self.mdl, asset_ref=helpers.random_string(),
            taxonomy=helpers.random_string(), stco=16.0, coco=17.0,
            site="POINT(%s %s)" % (site.point.x, site.point.y))
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
        self.mdl.reco_unit = "YEN"
        self.mdl.save()
        site = shapes.Site(-121.8000, 38.2000)
        edata = models.ExposureData(
            exposure_model=self.mdl, asset_ref=helpers.random_string(),
            taxonomy=helpers.random_string(), stco=18.0, number_of_units=22,
            site="POINT(%s %s)" % (site.point.x, site.point.y))
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
