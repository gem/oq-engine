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


import os
import unittest
import tempfile

from tests.utils import helpers
from openquake import shapes

from openquake import flags

FLAGS = flags.FLAGS

INSIDE = [(50, 50),
          (11, 11),
          (99, 99)]

OUTSIDE = [(50, 9),
           (9, 50),
           (9, 9),
           (101, 50),
           (50, 101),
           (101, 101)]


class GeoSiteTestCase(unittest.TestCase):

    def test_sites_can_be_keys(self):
        """ Site objects can be dictionary keys,
        So must hash reliably."""
        lat = 10.5
        lon = -49.5
        first_site = shapes.Site(lon, lat)
        second_site = shapes.Site(lon, lat)
        sites = {}
        sites[first_site] = "one"
        sites[second_site] = "two"
        # BOTH will now be "two"! This is correct

        self.assertEqual(first_site, second_site)
        self.assertEqual(sites[first_site], "two")
        self.assertEqual(sites[second_site], "two")

    def test_sites_have_geo_accessors(self):
        lat = 10.5
        lon = -49.5
        first_site = shapes.Site(lon, lat)
        self.assertEqual(first_site.latitude, lat)
        self.assertEqual(first_site.longitude, lon)


class RegionTestCase(unittest.TestCase):
    def _check_match(self, constraint):
        for point in INSIDE:
            self.assert_(constraint.match(point),
                         'did not match inside: %s' % str(point))

        for point in OUTSIDE:
            self.assert_(not constraint.match(point),
                         'matched outside: %s' % str(point))

    def test_from_coordinates(self):
        constraint = shapes.RegionConstraint.from_coordinates(
                [(10.0, 100.0), (100.0, 100.0), (100.0, 10.0), (10.0, 10.0)])
        self._check_match(constraint)

    def test_from_simple(self):
        constraint = shapes.RegionConstraint.from_simple(
            (10.0, 10.0), (100.0, 100.0))
        self._check_match(constraint)

    def test_bounding_box(self):
        switzerland = shapes.Region.from_coordinates(
            [(10.0, 100.0), (100.0, 100.0), (100.0, 10.0), (10.0, 10.0)])


class GridTestCase(unittest.TestCase):

    def test_grid_iterates_all_points(self):
        constraint = shapes.RegionConstraint.from_simple(
            (10.0, 10.0), (100.0, 100.0))
        constraint.cell_size = 10.0
        grid = constraint.grid
        for point in grid:
            print "Point at %s and %s" % (point.row, point.column)
            # TODO(JMC): assert the sequence is correct


class GeoCurveTestCase(unittest.TestCase):

    def test_equals_when_have_the_same_values(self):
        curve1 = shapes.Curve([(0.1, 1.0), (0.2, 2.0)])
        curve2 = shapes.Curve([(0.1, 1.0), (0.2, 2.0)])
        curve3 = shapes.Curve([(0.1, 1.0), (0.2, 5.0)])
        curve4 = shapes.Curve([(0.1, (1.0, 0.3)), (0.2, (2.0, 0.3))])
        curve5 = shapes.Curve([(0.1, (1.0, 0.3)), (0.2, (2.0, 0.3))])
        curve6 = shapes.Curve([(0.1, (1.0, 0.5)), (0.2, (2.0, 0.3))])

        self.assertEquals(curve1, curve2)
        self.assertNotEquals(curve1, curve3)
        self.assertNotEquals(curve1, curve4)
        self.assertNotEquals(curve3, curve4)
        self.assertEquals(curve4, curve5)
        self.assertNotEquals(curve5, curve6)

    def test_can_construct_a_curve_from_dict(self):
        curve1 = shapes.Curve([(0.1, 1.0), (0.2, 2.0)])
        curve2 = shapes.Curve.from_dict({"0.1": 1.0, "0.2": 2.0})
        curve3 = shapes.Curve([(0.1, (1.0, 0.3)), (0.2, (2.0, 0.3))])
        curve4 = shapes.Curve.from_dict({"0.1": (1.0, 0.3), "0.2": (2.0, 0.3)})

        # keys are already floats
        curve5 = shapes.Curve.from_dict({0.1: (1.0, 0.3), 0.2: (2.0, 0.3)})

        self.assertEquals(curve1, curve2)
        self.assertEquals(curve3, curve4)
        self.assertEquals(curve3, curve5)

    def test_can_serialize_in_json(self):
        curve1 = shapes.Curve([(0.1, 1.0), (0.2, 2.0)])
        curve2 = shapes.Curve([(0.1, (1.0, 0.3)), (0.2, (2.0, 0.3))])
        self.assertEquals(curve1, shapes.Curve.from_json(curve1.to_json()))
        self.assertEquals(curve2, shapes.Curve.from_json(curve2.to_json()))

    def test_can_construct_with_unordered_values(self):
        curve = shapes.Curve([(0.5, 1.0), (0.4, 2.0), (0.3, 2.0)])

        self.assertEqual(1.0, curve.ordinate_for(0.5))
        self.assertEqual(2.0, curve.ordinate_for(0.4))
        self.assertEqual(2.0, curve.ordinate_for(0.3))


class FieldTestCase(unittest.TestCase):

    def setUp(self):
        self.gmf_string = open(helpers.get_data_path("gmfs.json")).readline()
        region = shapes.Region.from_coordinates(
                 [(-118.30, 34.12), (-118.18, 34.12),
                 (-118.18,  34.00), (-118.30,  34.00)])
        region.cell_size = 0.02
        self.grid = region.grid

    def test_can_serialize_field(self):
        field_set = shapes.FieldSet.from_json(self.gmf_string, grid=self.grid)
        for field in field_set:
            print field.field
            self.assertTrue(field)
            print field.get(5, 5)
