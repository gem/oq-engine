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
from shapely import wkt

from openquake.engine.db import models

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
        poly_wkt = (
            "POLYGON((954158 4215137, 954159 4215138, "
            "954160 4215139, 954158 4215137))"
        )

        psrc.polygon = GEOSGeometry("SRID=32140;%s" % poly_wkt)
        psrc.save()
        psrc = models.ParsedSource.objects.get(id=psrc.id)
        self.assertEqual(4326, psrc.polygon.get_srid())
        self.assertNotEqual(wkt.loads(poly_wkt).wkt, psrc.polygon.wkt)

    def test_parsed_source_with_invalid_number_of_dimensions(self):
        # An exception is raised in cases where the number of dimensions is not
        # two.
        psrc = models.ParsedSource(input=self.input, source_type="point")
        # 3D geometries are not allowed:
        psrc.polygon = GEOSGeometry(
            "SRID=4326;POLYGON((20.1 42.1 10, 20.2 42.2 10, "
            "20.3 42.3 10, 20.1 42.1 10))"
        )
        try:
            psrc.save()
        except DatabaseError, de:
            self.assertTrue('violates check constraint "enforce_dims_polygon"'
                            in de.args[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")
