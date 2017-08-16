# The Hazard Library
# Copyright (C) 2013-2017 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import sys
import unittest
import numpy

from openquake.hazardlib.geo.surface.multi import MultiSurface
from openquake.hazardlib.geo import Mesh, Point, PlanarSurface

if sys.platform == 'win32':
    raise unittest.SkipTest('temporarily skipped on Windows')


class _BaseMultiTestCase(unittest.TestCase):
    class FakeSurface(object):
        def __init__(self, distances, lons, lats, depths, top_edge_depth,
                     strike, dip, width, area):
            self.distances = distances
            self.lons = lons
            self.lats = lats
            self.depths = depths
            self.top_edge_depth = top_edge_depth
            self.strike = strike
            self.dip = dip
            self.width = width
            self.area = area

        def get_min_distance(self, mesh):
            assert mesh.shape == self.distances.shape
            return self.distances

        def get_closest_points(self, mesh):
            assert mesh.shape == self.lons.shape
            return Mesh(self.lons, self.lats, self.depths)

        def get_joyner_boore_distance(self, mesh):
            assert mesh.shape == self.distances.shape
            return self.distances

        def get_rx_distance(self, mesh):
            assert mesh.shape == self.distances.shape
            return self.distances

        def get_top_edge_depth(self):
            return self.top_edge_depth

        def get_strike(self):
            return self.strike

        def get_dip(self):
            return self.dip

        def get_width(self):
            return self.width

        def get_area(self):
            return self.area

        def get_bounding_box(self):
            return numpy.min(self.lons), numpy.max(self.lons), \
                   numpy.max(self.lats), numpy.min(self.lats)

        def get_middle_point(self):
            return Point(self.lons.flatten()[0], self.lats.flatten()[0],
                         self.depths.flatten()[0])


    def setUp(self):
        self.surfaces_mesh2D = [
            self.FakeSurface(numpy.array([[-1., 2., 3.], [4., 5., 6.]]),
                             numpy.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]),
                             numpy.array([[1.1, 1.2, 1.3], [1.4, 1.5, 1.6]]),
                             numpy.array([[1.1, 1.2, 1.3], [1.4, 1.5, 1.6]]),
                             2.0, 45.0, 60.0, 10.0, 10.0),
            self.FakeSurface(numpy.array([[-0.5, 3., 2.], [5., 4., 5.]]),
                             numpy.array([[2.1, 2.2, 2.3], [2.4, 2.5, 2.6]]),
                             numpy.array([[3.1, 3.2, 3.3], [3.4, 3.5, 3.6]]),
                             numpy.array([[2.1, 2.2, 2.3], [2.4, 2.5, 2.6]]),
                             6, 70.0, 90.0, 8, 20.0),
            self.FakeSurface(numpy.array([[5., 4., 4.], [6., 6., 7.]]),
                             numpy.array([[4.1, 4.2, 4.3], [4.4, 4.5, 4.6]]),
                             numpy.array([[5.1, 5.2, 5.3], [5.4, 5.5, 5.6]]),
                             numpy.array([[6.1, 6.2, 6.3], [6.4, 6.5, 6.6]]),
                             10, 100.0, 40.0, 15, 60.0)
        ]

        self.mesh2D = Mesh(numpy.array([[1., 2., 3.], [4., 5., 6.]]),
                           numpy.array([[1., 2., 3.], [4., 5., 6.]]),
                           numpy.array([[1., 2., 3.], [4., 5., 6.]]))

        self.surfaces_mesh1D = [
            self.FakeSurface(numpy.array([-1., 2., 3.]),
                             numpy.array([0.1, 0.2, 0.3]),
                             numpy.array([1.1, 1.2, 1.3]),
                             numpy.array([1.1, 1.2, 1.3]),
                             2.0, 45.0, 60.0, 10.0, 10.0),
            self.FakeSurface(numpy.array([-0.5, 3., 2.]),
                             numpy.array([2.1, 2.2, 2.3]),
                             numpy.array([3.1, 3.2, 3.3]),
                             numpy.array([2.1, 2.2, 2.3]),
                             6, 70.0, 90.0, 8, 20.0),
            self.FakeSurface(numpy.array([5., 4., 4.]),
                             numpy.array([4.1, 4.2, 4.3]),
                             numpy.array([5.1, 5.2, 5.3]),
                             numpy.array([6.1, 6.2, 6.3]),
                             10, 100.0, 40.0, 15, 60.0)
        ]

        self.mesh1D = Mesh(numpy.array([1., 2., 3.]),
                           numpy.array([1., 2., 3.]),
                           numpy.array([1., 2., 3.]))


class DistancesTestCase(_BaseMultiTestCase):
    def test_min_distance_mesh2D(self):
        surf = MultiSurface(self.surfaces_mesh2D)
        numpy.testing.assert_equal(surf.get_min_distance(self.mesh2D),
                                   numpy.array([[-1., 2., 2.], [4., 4., 5.]]))

    def test_min_distance_mesh1D(self):
        surf = MultiSurface(self.surfaces_mesh1D)
        numpy.testing.assert_equal(surf.get_min_distance(self.mesh1D),
                                   numpy.array([-1., 2., 2.]))

    def test_get_closest_points_mesh2D(self):
        surf = MultiSurface(self.surfaces_mesh2D)
        closest_points = surf.get_closest_points(self.mesh2D)
        numpy.testing.assert_equal(
            closest_points.lons,
            numpy.array([[0.1, 0.2, 2.3], [0.4, 2.5, 2.6]])
        )
        numpy.testing.assert_equal(
            closest_points.lats,
            numpy.array([[1.1, 1.2, 3.3], [1.4, 3.5, 3.6]])
        )
        numpy.testing.assert_equal(
            closest_points.depths,
            numpy.array([[1.1, 1.2, 2.3], [1.4, 2.5, 2.6]])
        )

    def test_get_closest_points_mesh1D(self):
        surf = MultiSurface(self.surfaces_mesh1D)
        closest_points = surf.get_closest_points(self.mesh1D)
        numpy.testing.assert_equal(
            closest_points.lons,
            numpy.array([0.1, 0.2, 2.3])
        )
        numpy.testing.assert_equal(
            closest_points.lats,
            numpy.array([1.1, 1.2, 3.3])
        )
        numpy.testing.assert_equal(
            closest_points.depths,
            numpy.array([1.1, 1.2, 2.3])
        )

    def test_joyner_boore_distance_mesh2D(self):
        surf = MultiSurface(self.surfaces_mesh2D)
        numpy.testing.assert_equal(surf.get_joyner_boore_distance(self.mesh2D),
                                   numpy.array([[-1., 2., 2.], [4., 4., 5.]]))

    def test_joyner_boore_distance_mesh1D(self):
        surf = MultiSurface(self.surfaces_mesh1D)
        numpy.testing.assert_equal(surf.get_joyner_boore_distance(self.mesh1D),
                                   numpy.array([-1., 2., 2.]))

    def test_rx_distance_mesh2D(self):
        surf = MultiSurface(self.surfaces_mesh2D)
        numpy.testing.assert_equal(surf.get_rx_distance(self.mesh2D),
                                   numpy.array([[-1., 2., 2.], [4., 4., 5.]]))

    def test_rx_distance_mesh1D(self):
        surf = MultiSurface(self.surfaces_mesh1D)
        numpy.testing.assert_equal(surf.get_rx_distance(self.mesh1D),
                                   numpy.array([-1., 2., 2.]))

    def test_ry0_distance_mesh1D(self):
        surf = MultiSurface(self.surfaces_mesh1D)
        self.assertRaises(NotImplementedError, surf.get_ry0_distance,
                          self.mesh1D)


class SurfacePropertiesTestCase(_BaseMultiTestCase):
    def test_top_edge_depth(self):
        surf = MultiSurface(self.surfaces_mesh2D)
        self.assertAlmostEqual(8.22222222, surf.get_top_edge_depth())

    def test_get_strike(self):
        surf = MultiSurface(self.surfaces_mesh2D)
        self.assertAlmostEqual(87.64579754, surf.get_strike())

    def test_get_dip(self):
        surf = MultiSurface(self.surfaces_mesh2D)
        self.assertAlmostEqual(53.33333333, surf.get_dip())

    def test_get_width(self):
        surf = MultiSurface(self.surfaces_mesh2D)
        self.assertAlmostEqual(12.88888888, surf.get_width())

    def test_area(self):
        surf = MultiSurface(self.surfaces_mesh2D)
        self.assertAlmostEqual(90.0, surf.get_area())

    def test_bounding_box(self):
        surf = MultiSurface(self.surfaces_mesh2D)
        west, east, north, south = surf.get_bounding_box()
        self.assertEqual(0.1, west)
        self.assertEqual(4.6, east)
        self.assertEqual(5.6, north)
        self.assertEqual(1.1, south)

    def test_middle_point_single_surface(self):
        surf = MultiSurface([self.surfaces_mesh2D[0]])
        middle_point = surf.get_middle_point()
        self.assertTrue(Point(0.1, 1.1, 1.1) == middle_point)

    def test_middle_point_multi_surfaces(self):
        surf = MultiSurface([PlanarSurface(1.0, 0.0, 90.0,
                                           Point(0.0, -1.0, 0.0),
                                           Point(0.0, 1.0, 0.0),
                                           Point(0.0, 1.0, 10.0),
                                           Point(0.0, -1.0, 10.0)),
                             PlanarSurface(1.0, 135.0, 90.0,
                                           Point(0.0, -1.0, 0.0),
                                           Point(1.0, 1.0, 0.0),
                                           Point(1.0, 1.0, 10.0),
                                           Point(0.0, -1.0, 10.0))])
        middle_point = surf.get_middle_point()
        self.assertTrue(Point(0.5, 0.0, 5.0) == middle_point)
