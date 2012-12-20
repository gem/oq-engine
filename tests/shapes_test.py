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

import decimal
import json
import numpy
import re
import unittest

from numpy import allclose

from openquake import shapes
from openquake.utils import round_float

from tests.utils import helpers


def coord_list_from_wkt(wkt):
    """
    Given a Well Known Text string, extract the coordinate values and return
    them as a list of float values.

    Note: This is intended for use with 'primitve' WKT shapes (such as POINT,
    LINESTRING, and POLYGON). Input POLYGON shapes should not have holes.

    :param wkt: Well Known Text string for a POINT, LINESTRING, or POLYGON
        shape

    :returns: list of floats
    """
    return [float(x) for x in re.findall('[\d+?\.\d+]+', wkt)]


class ShapesTestCase(unittest.TestCase):

    TEST_IMLS = [0.005, 0.007, 0.0098, 0.0137, 0.0192, 0.0269]

    def test_round_float(self):
        """
        This test exercises the :py:function:`openquake.utils.round_float`
        function.

        Basically, the function should take any float number and round it to a
        fixed number of decimal places (for example, 7 places). The rounding
        method used is the default for the :py:module:`decimal` module, which
        is ROUND_HALF_EVEN.

        For more information on 'half-even' rounding, there is a good
        explanation here:
        http://www.diycalculator.com/popup-m-round.shtml#A5
        """
        in_values = (
            29.000000000000004, -121.00000009, -121.00000001, 121.00000005,
            121.00000006)
        out_values = (29.0, -121.0000001, -121.0, 121.0, 121.0000001)

        for i, _ in enumerate(in_values):
            self.assertEqual(out_values[i], round_float(in_values[i]))

    def test_round_float_rounding(self):
        """
        By default, the :py:module:`decimal` module uses the 'round-half-even'
        algorithm for rounding numbers.

        Since the rounding method can be set in a global context for the
        :py:module:`decimal` module, we want to make sure the
        :py:function:`openquake.utils.round_float` is unaffected context
        changes.
        """
        decimal.getcontext().rounding = decimal.ROUND_FLOOR

        # changing the decimal context rounding should not affect the behavior
        # of round_float
        self.assertEqual(-121.0000001, round_float(-121.00000009))

        # reset the global context so we don't potentially screw up other tests
        decimal.getcontext().rounding = decimal.ROUND_HALF_EVEN

    def test_simple_region_uses_round_floats(self):
        """
        This test ensures the coordinate precision is properly limited for
        instances of :py:class:`openquake.shapes.Region`.

        The region will be created using the
        :py:method:`openquake.shapes.Region.from_simple` method.
        """
        up_left = (29.00000006, 40.90000003)
        low_right = (25.70000005, 46.00000009)

        # Constrained versions of the corner points:
        exp_ul = (29.0000001, 40.9)
        exp_lr = (25.7, 46.0000001)

        region = shapes.Region.from_simple(up_left, low_right)

        # The easiest way to verify that the number precision of the region
        # is correct is to look at the WKT for the region polygon.
        coords = coord_list_from_wkt(region.polygon.wkt)

        actual_ul = tuple(coords[0:2])
        actual_lr = tuple(coords[4:6])

        self.assertEqual(exp_ul, actual_ul)
        self.assertEqual(exp_lr, actual_lr)

    def test_complex_region_uses_round_floats(self):
        """
        This test ensures the coordinate precision is properly limited for
        instance of :py:class:`openquake.shapes.Region`.

        The region will be created using the
        :py:method:`openquake.shapes.Region.from_coordinates` method.
        """
        # triangle
        input_coord_pairs = [
            (29.00000006, 40.90000003),
            (25.70000005, 46.00000009),
            (26.0, 45.00000001)]

        # we expect the first & last coord pair to be the same, since wkt
        # POLYGON shapes must form a closed loop
        expected_coord_list = [
            29.0000001, 40.9,
            25.7, 46.0000001,
            26.0, 45.0,
            29.0000001, 40.9]

        region = shapes.Region.from_coordinates(input_coord_pairs)

        actual_coord_list = coord_list_from_wkt(region.polygon.wkt)

        self.assertEqual(expected_coord_list, actual_coord_list)

    def test_for_hash_collisions(self):
        """The hash values for similar sites should *not* collide."""
        s1 = shapes.Site(-0.9, -1.0)
        s2 = shapes.Site(0.9, 0.0)
        self.assertNotEqual(hash(s1), hash(s2))


class SiteTestCase(unittest.TestCase):
    """
    Tests for the :py:class:`openquake.shapes.Site` class.
    """

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

    def test_site_uses_round_floats(self):
        """
        This test ensures the coordinate precision is properly limited for
        instances of :py:class:`openquake.shapes.Site`.
        """
        lon = -121.00000004
        lat = 29.00000006

        exp_lon = -121.0
        exp_lat = 29.0000001

        site = shapes.Site(lon, lat)

        self.assertEqual(exp_lon, site.longitude)
        self.assertEqual(exp_lat, site.latitude)

    def test_eq(self):
        """
        Test Site equality comparisons. Two sites with the same lon/lat should
        be considered equal.
        """
        lon = 121.0
        lat = 29.0

        site1 = shapes.Site(lon, lat)
        site2 = shapes.Site(lon, lat)

        self.assertEqual(site1, site2)

    def test_eq_with_rounded_lon_lat(self):
        """
        Test Site equality comparisons when using high-precision lon/lat values
        (which are rounded down when the Site object is created).
        """
        site1 = shapes.Site(-121.0, 29.0000001)
        site2 = shapes.Site(-121.00000004, 29.00000006)

        self.assertEqual(site1, site2)

    def test_hash(self):
        """
        Verify that two Sites with the same lon/lat have the same __hash__().
        """
        lon = 121.0
        lat = 29.0

        site1 = shapes.Site(lon, lat)
        site2 = shapes.Site(lon, lat)

        self.assertEqual(site1.__hash__(), site2.__hash__())

    def test_hash_with_rounded_lon_lat(self):
        """
        Test the __hash__() equality of two Sites when using high-precision
        lon/lat values (which are rounded down when the Site object is
        created).
        """
        site1 = shapes.Site(-121.0, 29.0000001)
        site2 = shapes.Site(-121.00000004, 29.00000006)

        self.assertEqual(site1.__hash__(), site2.__hash__())


class ShapesUtilsTestCase(unittest.TestCase):
    '''
    Tests for utility methods in the shapes module.
    '''

    def test_multipoint_ewkt(self):
        '''
        Test typical usage of
        :py:function:`openquake.shapes.multipoint_ewkt_from_coords`
        '''
        expected_ewkt = \
            'SRID=4326;MULTIPOINT((-122.0 38.113), (-122.114 38.113))'

        coords = '38.113, -122.0, 38.113, -122.114'

        actual_ewkt = shapes.multipoint_ewkt_from_coords(coords)

        self.assertEqual(expected_ewkt, actual_ewkt)

    def test_multipoint_ewkt_round_float(self):
        '''
        Test usage of
        :py:function:`openquake.shapes.multipoint_ewkt_from_coords` to ensure
        that high-precision coordinate values are rounded down a reasonable
        level of precision.
        '''
        expected_ewkt = \
            'SRID=4326;MULTIPOINT((-122.0 38.1130001), (-122.114 38.113))'

        coords = '38.11300006, -122.00000001, 38.113, -122.114'

        actual_ewkt = shapes.multipoint_ewkt_from_coords(coords)

        self.assertEqual(expected_ewkt, actual_ewkt)

    def test_polygon_ewkt(self):
        '''
        Test typical usage of
        :py:function:`openquake.shapes.polygon_ewkt_from_coords`
        '''
        # Note that the first & last coord are the same to form a closed loop.
        expected_ewkt = (
            'SRID=4326;POLYGON((-122.0 38.113, -122.114 38.113, '
            '-122.57 38.111, -122.0 38.113))')

        coords = '38.113, -122.0, 38.113, -122.114, 38.111, -122.57'

        actual_ewkt = shapes.polygon_ewkt_from_coords(coords)

        self.assertEqual(expected_ewkt, actual_ewkt)

    def test_polygon_ewkt_round_float(self):
        '''
        Test usage of
        :py:function:`openquake.shapes.polygon_ewkt_from_coords` to ensure
        that high-precision coordinate values are rounded down a reasonable
        level of precision.
        '''
        # Note that the first & last coord are the same to form a closed loop.
        expected_ewkt = (
            'SRID=4326;POLYGON((-122.0 38.113, -122.114 38.113, '
            '-122.57 38.1110001, -122.0 38.113))')

        coords = \
            '38.113, -122.00000001, 38.113, -122.114, 38.11100006, -122.57'

        actual_ewkt = shapes.polygon_ewkt_from_coords(coords)

        self.assertEqual(expected_ewkt, actual_ewkt)

    def test_hdistance(self):
        """Expected values are taken from OpenSHA,
        org.opensha.commons.geo.LocationUtilsTest.testHorzDistance."""

        site1 = shapes.Site(0.0, 90.0)
        site2 = shapes.Site(20.4, 32.6)
        site3 = shapes.Site(20.0, 32.4)
        site4 = shapes.Site(0.0, -90.0)
        site5 = shapes.Site(20.2, 32.0)
        site6 = shapes.Site(20.6, 32.2)

        test = lambda result, site1, site2: self.assertAlmostEqual(
            result, shapes.hdistance(site1.latitude, site1.longitude,
                                     site2.latitude, site2.longitude),
            places=6
        )
        test(6382.5960025, site1, site2)
        test(6404.835013, site3, site1)
        test(13565.796382, site5, site4)
        test(13588.035392, site4, site6)
        test(43.6090311, site2, site3)
        test(48.2790582, site2, site6)
        test(69.3145862, site2, site5)
        test(60.6198752, site3, site6)
        test(48.2952067, site5, site3)
        test(43.7518411, site5, site6)


class FieldTestCase(unittest.TestCase):

    def setUp(self):
        self.gmf_string = open(helpers.get_data_path("gmfs.json")).readline()
        region = shapes.Region.from_coordinates(
                 [(-118.30, 34.12), (-118.18, 34.12),
                 (-118.18, 34.00), (-118.30, 34.00)])
        region.cell_size = 0.02
        self.grid = region.grid

    def test_can_serialize_field(self):
        field_set = shapes.FieldSet.from_json(self.gmf_string, grid=self.grid)
        for field in field_set:
            print field.field
            self.assertTrue(field)
            print field.get(5, 5)


class GridTestCase(unittest.TestCase):

    def _test_expected_points(self, grid):
        for i, point in enumerate(grid):
            # check point iteration order
            expected_row = int(i / grid.columns)
            expected_column = i % grid.columns

            self.assertEquals((expected_row, expected_column),
                              (point.row, point.column))

    def test_grid_iterates_all_points(self):
        # basic grid
        constraint = shapes.RegionConstraint.from_simple(
            (120.0, 30.0), (100.0, 10.0))
        constraint.cell_size = 10.0
        self._test_expected_points(constraint.grid)

        # rounding (from the NSHMP smoke test)
        constraint = shapes.RegionConstraint.from_simple(
            (-118.3, 34.0), (-118.18, 34.12))
        constraint.cell_size = 0.02
        self._test_expected_points(constraint.grid)


class RegionTestCase(unittest.TestCase):
    INSIDE = [(50, 50),
              (11, 11),
              (99, 99)]

    OUTSIDE = [(50, 9),
               (9, 50),
               (9, 9),
               (101, 50),
               (50, 101),
               (101, 101)]

    def _check_match(self, constraint):
        for point in self.INSIDE:
            self.assert_(constraint.match(point),
                         'did not match inside: %s' % str(point))

        for point in self.OUTSIDE:
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

    def test_region_sites_boundary_1(self):
        # check that points really close to the
        # border of the region (longitude) have a corresponding
        # grid point. This is done by adding an additional
        # column to the grid (in this case [(2.5, 2.0),
        # (2.5, 1.5), (2.5, 1.0)]), even if the points that
        # are the center of the cell are outside the region.
        region = shapes.Region.from_coordinates(
            [(1.0, 2.0), (2.3, 2.0), (2.3, 1.0), (1.0, 1.0)])

        region.cell_size = 0.5

        expected_sites = set([
            shapes.Site(1.0, 1.0), shapes.Site(1.5, 1.0),
            shapes.Site(2.0, 1.0), shapes.Site(1.0, 1.5),
            shapes.Site(1.5, 1.5), shapes.Site(2.0, 1.5),
            shapes.Site(1.0, 2.0), shapes.Site(1.5, 2.0),
            shapes.Site(2.0, 2.0), shapes.Site(2.5, 2.0),
            shapes.Site(2.5, 1.0), shapes.Site(2.5, 1.5)])

        self.assertEquals(expected_sites, set(region.grid.centers()))

        self.assertTrue(region.grid.site_at(region.grid.point_at(
                shapes.Site(2.25, 2.0))) in region.grid.centers())

        self.assertTrue(region.grid.site_at(region.grid.point_at(
                shapes.Site(2.27, 2.0))) in region.grid.centers())

        self.assertTrue(region.grid.site_at(region.grid.point_at(
                shapes.Site(2.30, 2.0))) in region.grid.centers())

        # check we can ask for valid grid points from
        # the sites that represent the center of the cells
        for cell_center in region.grid.centers():
            self.assertTrue(region.grid.site_inside(cell_center))

    def test_region_sites_boundary_2(self):
        # same as above, but for latitude
        region = shapes.Region.from_coordinates(
            [(1.0, 2.0), (2.0, 2.0), (2.0, 0.6), (1.0, 0.6)])

        region.cell_size = 0.5

        self.assertTrue(region.grid.site_at(region.grid.point_at(
                shapes.Site(1.5, 0.61))) in region.grid.centers())

        self.assertTrue(region.grid.site_at(region.grid.point_at(
                shapes.Site(1.5, 0.60))) in region.grid.centers())

        self.assertTrue(region.grid.site_at(region.grid.point_at(
                shapes.Site(1.5, 2.0))) in region.grid.centers())

        self.assertTrue(region.grid.site_at(region.grid.point_at(
                shapes.Site(1.5, 1.9))) in region.grid.centers())

        self.assertTrue(region.grid.site_at(region.grid.point_at(
                shapes.Site(1.5, 1.8))) in region.grid.centers())

        # check we can ask for valid grid points from
        # the sites that represent the center of the cells
        for cell_center in region.grid.centers():
            self.assertTrue(region.grid.site_inside(cell_center))

    def test_region_sites_boundary_3(self):
        region = shapes.RegionConstraint.from_simple((0.0, 1.0), (1.0, 0.0))

        # Site(1.1, 1.1) is outside the region
        self.assertFalse(region.match(shapes.Site(1.1, 1.1)))

        # but inside the underlying grid because we add an
        # additional row and column
        self.assertTrue(region.grid.site_inside(shapes.Site(1.1, 1.1)))

        # same as above
        self.assertFalse(region.match(shapes.Site(1.04, 1.04)))
        self.assertFalse(region.match(shapes.Site(1.05, 1.05)))

        self.assertTrue(region.grid.site_inside(shapes.Site(1.04, 1.04)))
        self.assertTrue(region.grid.site_inside(shapes.Site(1.05, 1.05)))

        # this is too far away, even outside the grid
        self.assertRaises(ValueError,
                region.grid.point_at, shapes.Site(30.0, 30.0))

        region = shapes.RegionConstraint.from_simple((0.0, 1.0), (1.0, 0.0))
        region.cell_size = 0.5

        # same, points are outside the region
        self.assertFalse(region.match(shapes.Site(1.24, 1.24)))
        self.assertFalse(region.match(shapes.Site(1.25, 1.25)))
        self.assertFalse(region.match(shapes.Site(-0.24, -0.24)))
        self.assertFalse(region.match(shapes.Site(-0.25, -0.25)))

        # but inside the grid
        self.assertTrue(region.grid.site_inside(shapes.Site(1.24, 1.24)))
        self.assertTrue(region.grid.site_inside(shapes.Site(1.25, 1.25)))
        self.assertTrue(region.grid.site_inside(shapes.Site(-0.25, -0.25)))
        self.assertTrue(region.grid.site_inside(shapes.Site(-0.25, -0.24)))

        # latitude too low, too high
        self.assertFalse(region.grid.site_inside(shapes.Site(-0.25, -0.26)))
        self.assertFalse(region.grid.site_inside(shapes.Site(-0.25, 1.76)))

        # longitude too low, too high
        self.assertFalse(region.grid.site_inside(shapes.Site(1.76, 1.5)))
        self.assertFalse(region.grid.site_inside(shapes.Site(-0.26, 1.5)))
