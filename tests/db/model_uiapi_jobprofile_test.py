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


from django.db import transaction
from django.db.utils import DatabaseError
from django.test import TestCase as DjangoTestCase

from openquake.engine.db import models

from tests.utils import helpers


class OqJobProfileTestCase(DjangoTestCase, helpers.DbTestCase):
    """Test oq_job_profile database constraints."""

    job = None
    profile = None

    @classmethod
    def setUpClass(cls):
        cls.job = cls.setup_classic_job(omit_profile=True)

    @classmethod
    def tearDownClass(cls):
        cls.teardown_job(cls.job)

    def setUp(self):
        self.profile = self.setup_job_profile(self.job, save2db=False)

    def test_not_uhs_and_invalid_imt(self):
        # imt not in ("pga", "sa", "pgv", "pgd", "ia", "rsd", "mmi")
        #   -> exception
        self.profile.imt = "no_such_thing"
        try:
            self.profile.save()
        except DatabaseError, de:
            self.assertTrue("Invalid intensity measure type: 'no_such_thing'"
                            in de.args[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_not_uhs_and_sa_and_no_period(self):
        # imt is "sa" and period is not set
        #   -> exception
        self.profile.imt = "sa"
        self.profile.period = None
        try:
            self.profile.save()
        except DatabaseError, de:
            self.assertTrue(
                "Period must be set for intensity measure type 'sa'"
                in de.args[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_not_uhs_and_not_sa_and_period_set(self):
        # imt is not "sa" and period *is* set
        #   -> exception
        self.profile.period = 1.1
        try:
            self.profile.save()
        except DatabaseError, de:
            self.assertTrue(
                "Period must not be set for intensity measure type 'pga'"
                in de.args[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_uhs_and_not_sa(self):
        # For uhs calculations the trigger will set the imt to "sa"
        self.profile.calc_mode = "uhs"
        self.profile.uhs_periods = [1.0, 1.1]
        self.profile.quantile_levels = None
        self.profile.compute_mean_hazard_curve = None
        self.profile.imt = "pga"
        self.profile.damping = 2.2
        self.profile.save()
        self.profile = models.OqJobProfile.objects.get(id=self.profile.id)
        self.assertEqual("sa", self.profile.imt)

    def test_uhs_and_period_set(self):
        # For uhs calculations the trigger will set the "period" to NULL/None
        self.profile.calc_mode = "uhs"
        self.profile.uhs_periods = [1.0, 1.1]
        self.profile.quantile_levels = None
        self.profile.compute_mean_hazard_curve = None
        self.profile.imt = "sa"
        self.profile.damping = 2.2
        self.profile.period = 3.3
        self.profile.save()
        self.profile = models.OqJobProfile.objects.get(id=self.profile.id)
        self.assertIs(None, self.profile.period)
