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

from openquake.db import models

from tests.utils import helpers


class FragilityModelTestCase(DjangoTestCase, helpers.DbTestCase):
    """Test fragility model database constraints."""

    job = None

    @classmethod
    def setUpClass(cls):
        cls.job = cls.setup_classic_job()

    @classmethod
    def tearDownClass(cls):
        cls.teardown_job(cls.job)

    def setUp(self):
        fmdl_input = models.Input(
            input_type="fragility", size=123, path="/tmp/fake-fragility-path",
            owner=self.job.owner)
        fmdl_input.save()
        i2j = models.Input2job(input=fmdl_input, oq_job=self.job)
        i2j.save()
        self.mdl = models.FragilityModel(
            input=fmdl_input, owner=self.job.owner, format="continuous")

    def test_fragility_model_with_invalid_format(self):
        # model format not in ("continuous", "discrete") -> exception
        self.mdl.lss = "a b c".split()
        self.mdl.format = "invalid"
        try:
            self.mdl.save()
        except DatabaseError, de:
            self.assertTrue(
                '"fragility_model" violates check constraint "format_value"'
                in de.args[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_fragility_model_with_missing_limit_states(self):
        # no limit states -> exception
        try:
            self.mdl.save()
        except DatabaseError, de:
            self.assertTrue(
                'Exception: no limit states supplied (fragility_model)'
                in de.args[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")


class ContinuousFragilityModelTestCase(DjangoTestCase, helpers.DbTestCase):
    """Test the continuous fragility model database constraints."""

    job = None

    @classmethod
    def setUpClass(cls):
        cls.job = cls.setup_classic_job()

    @classmethod
    def tearDownClass(cls):
        cls.teardown_job(cls.job)

    def setUp(self):
        fmdl_input = models.Input(
            input_type="fragility", size=123, path="/tmp/fake-fragility-path",
            owner=self.job.owner)
        fmdl_input.save()
        i2j = models.Input2job(input=fmdl_input, oq_job=self.job)
        i2j.save()
        self.mdl = models.FragilityModel(
            input=fmdl_input, owner=self.job.owner, format="continuous")

    def test_continuous_fragility_model_with_imls(self):
        # continuous fragility model and IMLs -> exception
        self.mdl.lss = "a b c".split()
        self.mdl.imls = [0.1]
        try:
            self.mdl.save()
        except DatabaseError, de:
            self.assertTrue('IMLs defined for continuous fragility model'
                            in de.args[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_continuous_fragility_model_with_imt(self):
        # continuous fragility model and IMT -> exception
        self.mdl.lss = "a b c".split()
        self.mdl.imt = "MMI"
        try:
            self.mdl.save()
        except DatabaseError, de:
            self.assertTrue('IMT defined for continuous fragility model'
                            in de.args[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")


class DiscreteFragilityModelTestCase(DjangoTestCase, helpers.DbTestCase):
    """Test the discrete fragility model database constraints."""

    job = None

    @classmethod
    def setUpClass(cls):
        cls.job = cls.setup_classic_job()

    @classmethod
    def tearDownClass(cls):
        cls.teardown_job(cls.job)

    def setUp(self):
        fmdl_input = models.Input(
            input_type="fragility", size=123, path="/tmp/fake-fragility-path",
            owner=self.job.owner)
        fmdl_input.save()
        i2j = models.Input2job(input=fmdl_input, oq_job=self.job)
        i2j.save()
        self.mdl = models.FragilityModel(
            input=fmdl_input, owner=self.job.owner, format="discrete")

    def test_discrete_fragility_model_without_imls(self):
        # discrete fragility model and no IMLs -> exception
        self.mdl.lss = "a b c".split()
        try:
            self.mdl.save()
        except DatabaseError, de:
            self.assertTrue('no IMLs for discrete fragility model'
                            in de.args[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_discrete_fragility_model_with_empty_imls(self):
        # discrete fragility model and empty IMLs -> exception
        self.mdl.lss = "a b c".split()
        self.mdl.imls = []
        try:
            self.mdl.save()
        except DatabaseError, de:
            self.assertTrue('no IMLs for discrete fragility model'
                            in de.args[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_discrete_fragility_model_without_imt(self):
        # discrete fragility model and no IMT -> exception
        self.mdl.lss = "a b c".split()
        self.mdl.imls = [0.1]
        try:
            self.mdl.save()
        except DatabaseError, de:
            self.assertTrue('no IMT for discrete fragility model'
                            in de.args[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_discrete_fragility_model_with_invalid_imt(self):
        # discrete fragility model and invalid IMT -> exception
        self.mdl.lss = "a b c".split()
        self.mdl.imls = [0.1]
        self.mdl.imt = "xyz"
        try:
            self.mdl.save()
        except DatabaseError, de:
            self.assertTrue('invalid IMT (xyz)' in de.args[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")


class FfcTestCase(DjangoTestCase, helpers.DbTestCase):
    """Test the continuous fragility function database constraints."""

    job = None

    @classmethod
    def setUpClass(cls):
        cls.job = cls.setup_classic_job()

    @classmethod
    def tearDownClass(cls):
        cls.teardown_job(cls.job)

    def setUp(self):
        fmdl_input = models.Input(
            input_type="fragility", size=123, path="/tmp/fake-fragility-path",
            owner=self.job.owner)
        fmdl_input.save()
        i2j = models.Input2job(input=fmdl_input, oq_job=self.job)
        i2j.save()
        self.mdl = models.FragilityModel(
            input=fmdl_input, owner=self.job.owner, format="continuous",
            lss="a b c".split())
        self.mdl.save()
        self.discrete_mdl = models.FragilityModel(
            input=fmdl_input, owner=self.job.owner, format="discrete",
            lss="d e f".split(), imls=[0.2], imt="mmi")
        self.discrete_mdl.save()

    def test_ffc_with_no_ls(self):
        # continuous fragility function and no limit state -> exception
        ffc = models.Ffc(fragility_model=self.mdl, lsi=-2)
        try:
            ffc.save()
        except DatabaseError, de:
            self.assertTrue('Invalid limit state' in de.args[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_ffc_with_invalid_ls(self):
        # continuous fragility function and invalid limit state -> exception
        ffc = models.Ffc(fragility_model=self.mdl, ls="xyz", lsi=1)
        try:
            ffc.save()
        except DatabaseError, de:
            self.assertTrue('Invalid limit state' in de.args[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_ffc_with_discrete_model(self):
        # continuous fragility function and discrete model -> exception
        ffc = models.Ffc(fragility_model=self.discrete_mdl, ls="d", lsi=1)
        try:
            ffc.save()
        except DatabaseError, de:
            self.assertTrue('mismatch: discrete model but continuous function'
                            in de.args[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_ffc(self):
        # continuous fragility function with good data is inserted OK.
        ffc = models.Ffc(fragility_model=self.mdl, ls="a", taxonomy="T1",
                         mean=0.4, stddev=12.1, lsi=1)
        ffc.save()
        self.assertIs(self.mdl, ffc.fragility_model)
        self.assertEqual("T1", ffc.taxonomy)
        self.assertEqual("a", ffc.ls)
        self.assertEqual(1, ffc.lsi)
        self.assertEqual(0.4, ffc.mean)
        self.assertEqual(12.1, ffc.stddev)

    def test_ffc_with_invalid_lsi(self):
        # continuous fragility function with a limit state that's off by one
        #   -> exception
        ffc = models.Ffc(fragility_model=self.mdl, ls="a", taxonomy="T1",
                         mean=0.4, stddev=12.1, lsi=2)
        try:
            ffc.save()
        except DatabaseError, de:
            self.assertTrue('Invalid limit state index (2) for ffc(T1, a)'
                            in de.args[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_ffc_with_duplicate_ls_and_taxonomy(self):
        # continuous fragility function with duplicate limit state and taxonomy
        #   -> exception
        ffc = models.Ffc(fragility_model=self.mdl, ls="a", taxonomy="T1",
                         mean=0.4, stddev=12.1, lsi=1)
        ffc.save()
        self.assertIs(self.mdl, ffc.fragility_model)
        self.assertEqual("T1", ffc.taxonomy)
        self.assertEqual("a", ffc.ls)
        self.assertEqual(1, ffc.lsi)
        self.assertEqual(0.4, ffc.mean)
        self.assertEqual(12.1, ffc.stddev)
        ffc2 = models.Ffc(fragility_model=self.mdl, ls="a", taxonomy="T1",
                         mean=0.41, stddev=12.12, lsi=1)
        try:
            ffc2.save()
        except DatabaseError, de:
            self.assertTrue('duplicate key value violates unique constraint '
                            '"ffc_fragility_model_id_taxonomy_lsi_key"' in
                            de.args[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")


class FfdTestCase(DjangoTestCase, helpers.DbTestCase):
    """Test the discrete fragility function database constraints."""

    job = None

    @classmethod
    def setUpClass(cls):
        cls.job = cls.setup_classic_job()

    @classmethod
    def tearDownClass(cls):
        cls.teardown_job(cls.job)

    def setUp(self):
        fmdl_input = models.Input(
            input_type="fragility", size=123, path="/tmp/fake-fragility-path",
            owner=self.job.owner)
        fmdl_input.save()
        i2j = models.Input2job(input=fmdl_input, oq_job=self.job)
        i2j.save()
        self.mdl = models.FragilityModel(
            input=fmdl_input, owner=self.job.owner, format="discrete",
            lss="a b c".split(), imls=[0.2, 0.3], imt="mmi")
        self.mdl.save()
        self.continuous_mdl = models.FragilityModel(
            input=fmdl_input, owner=self.job.owner, format="continuous",
            lss="d e f".split())
        self.continuous_mdl.save()

    def test_ffd_with_no_ls(self):
        # discrete fragility function and no limit state -> exception
        ffd = models.Ffd(fragility_model=self.mdl, poes=[0.5, 0.6], lsi=-1)
        try:
            ffd.save()
        except DatabaseError, de:
            self.assertTrue('Invalid limit state' in de.args[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_ffd_with_invalid_ls(self):
        # discrete fragility function and invalid limit state -> exception
        ffd = models.Ffd(fragility_model=self.mdl, ls="xyz", lsi=1,
                         poes=[0.5, 0.6])
        try:
            ffd.save()
        except DatabaseError, de:
            self.assertTrue('Invalid limit state' in de.args[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_ffd_with_invalid_ls_not_int(self):
        # discrete fragility function and invalid limit state -> exception
        ffd = models.Ffd(fragility_model=self.mdl, ls="xyz", lsi="blah",
                         poes=[0.5, 0.6])
        try:
            ffd.save()
        except ValueError, de:
            self.assertTrue('invalid literal for int' in de.args[0])
            transaction.rollback()
        else:
            self.fail("ValueError not raised")

    def test_ffd_with_discrete_model(self):
        # discrete fragility function and discrete model -> exception
        ffd = models.Ffd(fragility_model=self.continuous_mdl, ls="d", lsi=1)
        try:
            ffd.save()
        except DatabaseError, de:
            self.assertTrue('mismatch: continuous model but discrete function'
                            in de.args[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_ffd_with_wrong_num_of_poes(self):
        # discrete fragility function and wrong #poes -> exception
        ffd = models.Ffd(fragility_model=self.mdl, ls="a", poes=[0.5], lsi=1)
        try:
            ffd.save()
        except DatabaseError, de:
            self.assertTrue('#poes differs from #imls (1 != 2)' in de.args[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_ffd(self):
        # discrete fragility function with good data is inserted OK.
        ffd = models.Ffd(fragility_model=self.mdl, ls="b", taxonomy="T2",
                         poes=[0.5, 0.6], lsi=2)
        ffd.save()
        self.assertIs(self.mdl, ffd.fragility_model)
        self.assertEqual("T2", ffd.taxonomy)
        self.assertEqual("b", ffd.ls)
        self.assertEqual(2, ffd.lsi)
        self.assertEqual([0.5, 0.6], ffd.poes)

    def test_ffd_with_invalid_sli(self):
        # discrete fragility function with with invalid limit state index
        #   -> exception
        ffd = models.Ffd(fragility_model=self.mdl, ls="b", taxonomy="T2",
                         poes=[0.5, 0.6], lsi=len(self.mdl.lss) * 2)
        try:
            ffd.save()
        except DatabaseError, de:
            self.assertTrue('Invalid limit state index (6) for ffd(T2, b)'
                            in de.args[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_ffd_with_duplicate_ls_and_taxonomy(self):
        # discrete fragility function with duplicate limit state and taxonomy
        #   -> exception
        ffd = models.Ffd(fragility_model=self.mdl, ls="b", taxonomy="T2",
                         poes=[0.5, 0.6], lsi=2)
        ffd.save()
        self.assertIs(self.mdl, ffd.fragility_model)
        self.assertEqual("T2", ffd.taxonomy)
        self.assertEqual("b", ffd.ls)
        self.assertEqual(2, ffd.lsi)
        self.assertEqual([0.5, 0.6], ffd.poes)
        ffd2 = models.Ffd(fragility_model=self.mdl, ls="b", taxonomy="T2",
                          poes=[0.51, 0.62], lsi=2)
        try:
            ffd2.save()
        except DatabaseError, de:
            self.assertTrue('duplicate key value violates unique constraint '
                            '"ffd_fragility_model_id_taxonomy_lsi_key"' in
                            de.args[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")
