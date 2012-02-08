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
                "INSERT: error: area_type is mandatory for coco_type=per_area "
                "(exposure_model)", de.args[0].strip())
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
                "INSERT: error: area_type is mandatory for reco_type=per_area "
                "(exposure_model)", de.args[0].strip())
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
                "INSERT: error: area_type is mandatory for stco_type=per_area "
                "(exposure_model)", de.args[0].strip())
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
                "INSERT: error: area_type is mandatory for reco_type=per_area,"
                " stco_type=per_area (exposure_model)", de.args[0].strip())
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_exposure_model_with_no_area_unit_coco_per_area(self):
        # area unit not set but contents cost type is 'per_area' -> exception
        self.mdl.coco_type = "per_area"
        self.mdl.coco_unit = "EUR"
        self.mdl.area_type = "per_asset"
        try:
            self.mdl.save()
        except DatabaseError, de:
            self.assertEqual(
                "INSERT: error: area_unit is mandatory for coco_type=per_area "
                "(exposure_model)", de.args[0].strip())
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
                "INSERT: error: area_unit is mandatory for reco_type=per_area "
                "(exposure_model)", de.args[0].strip())
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
                "INSERT: error: area_unit is mandatory for stco_type=per_area "
                "(exposure_model)", de.args[0].strip())
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
                "INSERT: error: area_unit is mandatory for reco_type=per_area,"
                " stco_type=per_area (exposure_model)", de.args[0].strip())
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_exposure_model_with_coco_type_but_no_coco_unit(self):
        # contents cost type set but contents cost unit not set
        #   -> exception
        self.mdl.coco_type = "aggregated"
        try:
            self.mdl.save()
        except DatabaseError, de:
            self.assertEqual(
                "INSERT: error: coco_unit is mandatory for coco_type "
                "<aggregated> (exposure_model)", de.args[0].strip())
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
                "INSERT: error: reco_unit is mandatory for reco_type "
                "<aggregated> (exposure_model)", de.args[0].strip())
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
                "INSERT: error: stco_unit is mandatory for stco_type "
                "<aggregated> (exposure_model)", de.args[0].strip())
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
                "INSERT: error: stco_type is mandatory for category <economic"
                " loss> (exposure_model)", de.args[0].strip())
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

    def test_exposure_data_with_no_stco_and_population(self):
        # the structural cost needs not be present when we calculate exposure
        # in terms of population
        self.mdl.coco_type = "aggregated"
        self.mdl.coco_unit = "EUR"
        self.mdl.category = "population"
        self.mdl.save()
        site = shapes.Site(-122.5000, 37.5000)

        edata = models.ExposureData(
            exposure_model=self.mdl, asset_ref=helpers.random_string(),
            taxonomy=helpers.random_string(), number_of_units=111,
            site="POINT(%s %s)" % (site.point.x, site.point.y))
        edata.save()
