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

from tests.utils import helpers
from openquake.db import models


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
                                    name="no_area_type_coco_per_area")

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
