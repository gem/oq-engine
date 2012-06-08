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


from django.contrib.gis.geos import GEOSGeometry
from django.db import transaction
from django.db.utils import DatabaseError
from django.test import TestCase as DjangoTestCase

from openquake.db import models

from tests.utils import helpers


class ParsedSourceTestCase(DjangoTestCase, helpers.DbTestCase):
    """Test parsed source database constraints."""

    job = None
    input = None

    @classmethod
    def setUpClass(cls):
        cls.job = cls.setup_classic_job()
        cls.input = models.Input(
            input_type="source", size=123, path="/tmp/fake-source-path",
            owner=cls.job.owner)
        cls.input.save()
        i2j = models.Input2job(input=cls.input, oq_job=cls.job)
        i2j.save()

    @classmethod
    def tearDownClass(cls):
        cls.teardown_job(cls.job)

    def test_parsed_source_with_wrong_srid(self):
        # Coordinates with an SRID other than 4326 are transformed.
        psrc = models.ParsedSource(input=self.input, source_type="point")
        psrc.geom = GEOSGeometry("SRID=32140;POINT(954158.1 4215137.1)")
        psrc.save()
        psrc = models.ParsedSource.objects.get(id=psrc.id)
        self.assertEqual(4326, psrc.geom.get_srid())
        self.assertNotEqual(954158.1, psrc.geom.x)
        self.assertNotEqual(4215137.1, psrc.geom.y)

    def test_parsed_source_with_invalid_number_of_dimensions(self):
        # An exception is raised in cases where the number of dimensions is not
        # two.
        psrc = models.ParsedSource(input=self.input, source_type="point")
        psrc.geom = GEOSGeometry("SRID=4326;POINT(9.1 4.1 12.2)")
        try:
            psrc.save()
        except DatabaseError, de:
            self.assertTrue('violates check constraint "enforce_dims_geom"'
                            in de.args[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")
