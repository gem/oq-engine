# The Hazard Library
# Copyright (C) 2012-2017 GEM Foundation
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
import unittest
import collections

import numpy

from openquake.hazardlib.geo import geodetic

Point = collections.namedtuple("Point",  'lon lat')

# these points and tests that use them are from
# http://williams.best.vwh.net/avform.htm#Example
LAX = (118 + 24 / 60., 33 + 57 / 60.)
JFK = (73 + 47 / 60., 40 + 38 / 60.)

assert_aeq = numpy.testing.assert_almost_equal


class TestGeodeticDistance(unittest.TestCase):
    def test_LAX_to_JFK(self):
        dist = geodetic.geodetic_distance(*(LAX + JFK))
        self.assertAlmostEqual(dist, 0.623585 * geodetic.EARTH_RADIUS,
                               delta=0.1)
        dist2 = geodetic.geodetic_distance(*(JFK + LAX))
        self.assertAlmostEqual(dist, dist2)

    def test_on_equator(self):
        dist = geodetic.geodetic_distance(0, 0, 1, 0)
        self.assertAlmostEqual(dist, 111.1949266)
        [dist2] = geodetic.geodetic_distance([-5], [0], [-6], [0])
        self.assertAlmostEqual(dist, dist2)

    def test_along_meridian(self):
        coords = list(map(numpy.array, [(77.5, -150.), (-10., 15.),
                                   (77.5, -150.), (-20., 25.)]))
        dist = geodetic.geodetic_distance(*coords)
        assert_aeq(dist, [1111.949, 1111.949], decimal=3)

    def test_one_point_on_pole(self):
        dist = geodetic.geodetic_distance(0, 90, 0, 88)
        self.assertAlmostEqual(dist, 222.3898533)

    def test_small_distance(self):
        dist = geodetic.geodetic_distance(0, 0, 0, 1e-10)
        self.assertAlmostEqual(dist, 0)
        dist = geodetic.geodetic_distance(-1e-12, 0, 0, 0)
        self.assertAlmostEqual(dist, 0)

    def test_opposite_points(self):
        dist = geodetic.geodetic_distance(110, -10, -70, 10)
        self.assertAlmostEqual(dist, geodetic.EARTH_RADIUS * numpy.pi,
                               places=3)

    def test_arrays(self):
        lons1 = numpy.array([[-50.03824533, -153.97808192],
                             [-106.36068694, 47.06944014]])
        lats1 = numpy.array([[52.20211151, 17.018482],
                             [-26.06421527, -20.30383723]])
        lons2 = numpy.array([[49.97448794, 52.3126795],
                             [-165.13925579, 162.16421979]])
        lats2 = numpy.array([[-27.66510775, -73.66591257],
                             [-60.24498761,  -9.92908014]])
        edist = numpy.array([[13061.87935023, 13506.24000062],
                             [5807.34519649, 12163.45759805]])
        dist = geodetic.geodetic_distance(lons1, lats1, lons2, lats2)
        self.assertEqual(dist.shape, edist.shape)
        assert_aeq(dist, edist, decimal=2)

    def test_one_to_many(self):
        dist = geodetic.geodetic_distance(0, 0, [-1, 1], [0, 0])
        assert_aeq(dist, [111.195, 111.195], decimal=4)
        dist = geodetic.geodetic_distance(0, 0, [[-1, 0], [1, 0]],
                                                [[0, 0], [0, 0]])
        assert_aeq(dist, [[111.195, 0], [111.195, 0]], decimal=4)


class TestAzimuth(unittest.TestCase):
    def test_LAX_to_JFK(self):
        az = geodetic.azimuth(*(LAX + JFK))
        self.assertAlmostEqual(az, 360 - 65.8922, places=4)

    def test_meridians(self):
        az = geodetic.azimuth(0, 0, 0, 1)
        self.assertEqual(az, 0)
        az = geodetic.azimuth(0, 2, 0, 1)
        self.assertEqual(az, 180)

    def test_equator(self):
        az = geodetic.azimuth(0, 0, 1, 0)
        self.assertEqual(az, 90)
        az = geodetic.azimuth(1, 0, 0, 0)
        self.assertEqual(az, 270)

    def test_quadrants(self):
        az = geodetic.azimuth(0, 0, [0.01, 0.01, -0.01, -0.01],
                                    [0.01, -0.01, -0.01, 0.01])
        assert_aeq(az, [45, 135, 225, 315], decimal=5)

    def test_arrays(self):
        lons1 = numpy.array([[156.49676849, 150.03697145],
                             [-77.96053914, -109.36694411]])
        lats1 = numpy.array([[-79.78522764, -89.15044328],
                             [-32.28244296, -25.11092309]])
        lons2 = numpy.array([[-84.6732372, 140.08382287],
                             [82.69227935, -18.9919318]])
        lats2 = numpy.array([[82.16896786, 26.16081412],
                             [41.21501474, -2.88241099]])
        eazimuths = numpy.array([[47.07336955, 350.11740733],
                                 [54.46959147, 92.76923701]])
        az = geodetic.azimuth(lons1, lats1, lons2, lats2)
        assert_aeq(az, eazimuths)


class TestDistance(unittest.TestCase):
    def test(self):
        p1 = (0, 0, 10)
        p2 = (0.5, -0.3, 5)
        distance = geodetic.distance(*(p1 + p2))
        self.assertAlmostEqual(distance, 65.0295143)

    def test_topo(self):
        p1 = (0, 0, 1)
        p2 = (0, 0, -1)
        distance = geodetic.distance(*(p1 + p2))
        self.assertAlmostEqual(distance, 2.0)

    def test_topo2(self):
        p1 = (0, 0, 3)
        p2 = (0.5, -0.3, -2)
        distance = geodetic.distance(*(p1 + p2))
        self.assertAlmostEqual(distance, 65.0295143)


class MinDistanceTest(unittest.TestCase):
    # test relies on geodetic.distance() to work right
    def _test(self, mlons, mlats, mdepths, slons, slats, sdepths,
              expected_mpoint_indices):
        mlons, mlats, mdepths = [numpy.array(arr, float)
                                 for arr in (mlons, mlats, mdepths)]
        slons, slats, sdepths = [numpy.array(arr, float)
                                 for arr in (slons, slats, sdepths)]
        actual_indices, dists = geodetic.min_idx_dst(mlons, mlats, mdepths,
                                                     slons, slats, sdepths)
        numpy.testing.assert_equal(actual_indices, expected_mpoint_indices)
        expected_closest_mlons = mlons.flat[expected_mpoint_indices]
        expected_closest_mlats = mlats.flat[expected_mpoint_indices]
        expected_closest_mdepths = mdepths.flat[expected_mpoint_indices]
        expected_distances = geodetic.distance(
            expected_closest_mlons, expected_closest_mlats,
            expected_closest_mdepths,
            slons, slats, sdepths
        )
        assert_aeq(dists, expected_distances)

        # testing min_geodetic_distance with the same lons and lats
        min_geo_distance = geodetic.min_geodetic_distance(mlons, mlats,
                                                          slons, slats)
        min_distance = geodetic.min_idx_dst(mlons, mlats, mdepths * 0,
                                            slons, slats, sdepths * 0)[1]
        numpy.testing.assert_almost_equal(min_geo_distance, min_distance)

    def test_one_point(self):
        mlons = numpy.array([-0.1, 0.0, 0.1])
        mlats = numpy.array([0.0, 0.0, 0.0])
        mdepths = numpy.array([0.0, 10.0, 20.0])

        self._test(mlons, mlats, mdepths, [-0.05], [0.0], [0],
                   expected_mpoint_indices=0)
        self._test(mlons, mlats, mdepths, [-0.1], [0.0], [20.0],
                   expected_mpoint_indices=1)

    def test_several_points(self):
        self._test(mlons=[10., 11.], mlats=[-40, -41], mdepths=[10., 20.],
                   slons=[9., 9.], slats=[-39, -45], sdepths=[0.1, 0.2],
                   expected_mpoint_indices=[0, 1])

    def test_different_shapes(self):
        self._test(mlons=[0.5, 0.7], mlats=[0.7, 0.9], mdepths=[13., 17.],
                   slons=[-0.5] * 3, slats=[0.6] * 3, sdepths=[0.1] * 3,
                   expected_mpoint_indices=[0, 0, 0])

    def test_rect_mesh(self):
        self._test(mlons=[[10., 11.]], mlats=[[-40, -41]], mdepths=[[1., 2.]],
                   slons=[9., 9.], slats=[-39, -45], sdepths=[0.1, 0.2],
                   expected_mpoint_indices=[0, 1])


class MinDistanceToSegmentTest(unittest.TestCase):

    def setUp(self):
        self.slons = numpy.array([-1.2, 1.4])
        self.slats = numpy.array([-0.3, 0.5])

    def test_one(self):
        # Positive distance halfspace - within segment
        dist = float(geodetic.min_distance_to_segment(
            self.slons, self.slats, lons=numpy.array([0.0]),
            lats=numpy.array([-2.0])))
        self.assertAlmostEqual(dist, 219.90986712)

    def test_two(self):
        # Negative distance halfspace - within segment
        dist = float(geodetic.min_distance_to_segment(
            self.slons, self.slats, lons=numpy.array([0.0]),
            lats=numpy.array([2.0])))
        self.assertAlmostEqual(dist, -205.18959626)

    def test_three(self):
        # Positive distance halfspace - outside segment
        dist = float(geodetic.min_distance_to_segment(
            self.slons, self.slats, lons=numpy.array([3.0]),
            lats=numpy.array([0.0])))
        self.assertAlmostEqual(dist, 186.394507344)

    def test_four(self):
        # Negative distance halfspace - outside segment
        dist = float(geodetic.min_distance_to_segment(
            self.slons, self.slats,
            lons=numpy.array([-2.0]),
            lats=numpy.array([0.5])))
        self.assertAlmostEqual(dist, -125.802091893)

    def test_five(self):
        # Seglons with three elements
        self.assertRaises(AssertionError,
                          geodetic.min_distance_to_segment,
                          numpy.array([0., 0., 0.]),
                          self.slats,
                          lons=numpy.array([-2.0]),
                          lats=numpy.array([0.5]))


class DistanceToSemiArcTest(unittest.TestCase):
    # values in this test are based on the tests used for the
    # DistanceToArcTest
    def test_one_point(self):
        dist = float(geodetic.distance_to_semi_arc(
            12.3, 44.5, 39.4, plons=13.4, plats=46.9))
        self.assertAlmostEqual(dist, -105.12464364)
        dist = float(geodetic.distance_to_arc(
            12.3, 44.5, 219.4, plons=13.4, plats=46.9))
        self.assertAlmostEqual(dist, +105.12464364)
        dist = float(geodetic.distance_to_semi_arc(
            12.3, 44.5, 39.4, plons=13.4, plats=44.9))
        self.assertAlmostEqual(dist, 38.34459954)
        # This tests the distance to a point in the y-negative halfspace in a
        # reference system which uses as the origin the reference point
        # (i.e. (12.3; 44.5)) and the y direction as the direction with
        # azimuth = 39.4)
        dist = float(geodetic.distance_to_semi_arc(
            12.3, 44.5, 39.4, plons=11.3, plats=44.5))
        self.assertAlmostEqual(dist, -79.3093368)


class DistanceToArcTest(unittest.TestCase):
    # values in this test have not been checked by hand
    def test_one_point(self):
        dist = float(
            geodetic.distance_to_arc(12.3, 44.5, 39.4, plons=13.4, plats=46.9))
        self.assertAlmostEqual(dist, -105.12464364)
        dist = geodetic.distance_to_arc(12.3, 44.5, 219.4,
                                        plons=13.4, plats=46.9)
        self.assertAlmostEqual(dist, +105.12464364)
        dist = float(geodetic.distance_to_arc(
            12.3, 44.5, 39.4, plons=13.4, plats=44.9))
        self.assertAlmostEqual(dist, 38.34459954)

    def test_several_points(self):
        plons = numpy.array([3.3, 4.3])
        plats = numpy.array([20.3, 15.3])
        dists = geodetic.distance_to_arc(4.0, 17.0, -123.0, plons, plats)
        expected_dists = [347.61490787, -176.03785187]
        assert_aeq(dists, expected_dists)


class PointAtTest(unittest.TestCase):
    # values are verified using pyproj's spherical Geod
    def test(self):
        lon, lat = geodetic.point_at(10.0, 20.0, 30.0, 50.0)
        self.assertAlmostEqual(lon, 10.239856504796101, places=6)
        self.assertAlmostEqual(lat, 20.38925590463351, places=6)

        lon, lat = geodetic.point_at(-13.5, 22.4, -140.0, 120.0)
        self.assertAlmostEqual(lon, -14.245910669126582, places=6)
        self.assertAlmostEqual(lat, 21.57159463157223, places=6)

    def test_zero_distance(self):
        lon, lat = geodetic.point_at(1.3, -5.6, -35.0, 0)
        self.assertAlmostEqual(lon, 1.3)
        self.assertAlmostEqual(lat, -5.6)


class NPointsBetweenTest(unittest.TestCase):
    # values are verified using pyproj's spherical Geod
    def test(self):
        lons, lats, depths = geodetic.npoints_between(
            lon1=40.77, lat1=38.9, depth1=17.5,
            lon2=31.14, lat2=46.23, depth2=5.2,
            npoints=7
        )
        expected_lons = [40.77, 39.316149154562076, 37.8070559966114,
                         36.23892429550906, 34.60779411051164,
                         32.90956020775102, 31.14]
        expected_lats = [38.9, 40.174608368560094, 41.43033989236144,
                         42.66557829138413, 43.87856696738466,
                         45.067397797471415, 46.23]
        expected_depths = [17.5, 15.45, 13.4, 11.35, 9.3, 7.25, 5.2]
        assert_aeq(lons, expected_lons)
        assert_aeq(lats, expected_lats)
        assert_aeq(depths, expected_depths)
        # the last and the first points should be exactly the same as two
        # original corner points, so no "assertAlmostEqual" for them
        self.assertEqual(lons[0], 40.77)
        self.assertEqual(lats[0], 38.9)
        self.assertEqual(depths[0], 17.5)
        self.assertEqual(lons[-1], 31.14)
        self.assertEqual(lats[-1], 46.23)
        self.assertEqual(depths[-1], 5.2)

    def test_same_points(self):
        lon, lat, depth = 1.2, 3.4, 5.6
        lons, lats, depths = geodetic.npoints_between(
            lon, lat, depth, lon, lat, depth, npoints=7
        )
        expected_lons = [lon] * 7
        expected_lats = [lat] * 7
        expected_depths = [depth] * 7
        assert_aeq(lons, expected_lons)
        assert_aeq(lats, expected_lats)
        assert_aeq(depths, expected_depths)

    def test_topo(self):
        lons, lats, depths = geodetic.npoints_between(
            lon1=40.77, lat1=38.9, depth1=2,
            lon2=31.14, lat2=46.23, depth2=-4,
            npoints=7
        )
        expected_lons = [40.77, 39.316149154562076, 37.8070559966114,
                         36.23892429550906, 34.60779411051164,
                         32.90956020775102, 31.14]
        expected_lats = [38.9, 40.174608368560094, 41.43033989236144,
                         42.66557829138413, 43.87856696738466,
                         45.067397797471415, 46.23]
        expected_depths = [2, 1, 0, -1, -2, -3, -4]
        assert_aeq(lons, expected_lons)
        assert_aeq(lats, expected_lats)
        assert_aeq(depths, expected_depths)
        # the last and the first points should be exactly the same as two
        # original corner points, so no "assertAlmostEqual" for them
        self.assertEqual(lons[0], 40.77)
        self.assertEqual(lats[0], 38.9)
        self.assertEqual(depths[0], 2)
        self.assertEqual(lons[-1], 31.14)
        self.assertEqual(lats[-1], 46.23)
        self.assertEqual(depths[-1], -4)


class NPointsTowardsTest(unittest.TestCase):
    # values in this test have not been checked by hand
    def test(self):
        lons, lats, depths = geodetic.npoints_towards(
            lon=-30.5, lat=23.6, depth=55, azimuth=-100.5,
            hdist=400, vdist=-40, npoints=5
        )
        expected_lons = [-30.5, -31.46375358, -32.42503446,
                         -33.3837849, -34.33995063]
        expected_lats = [23.6, 23.43314083, 23.26038177,
                         23.08178673, 22.8974212]
        expected_depths = [55, 45, 35, 25, 15]
        assert_aeq(lons, expected_lons)
        assert_aeq(lats, expected_lats)
        assert_aeq(depths, expected_depths)
        # the first point should be exactly the same
        # as the original starting point
        self.assertEqual(lons[0], -30.5)
        self.assertEqual(lats[0], 23.6)
        self.assertEqual(depths[0], 55)

    def test_zero_distance(self):
        lon, lat, depth, azimuth = 12, 34, 56, 78
        lons, lats, depths = geodetic.npoints_towards(
            lon, lat, depth, azimuth, hdist=0, vdist=0, npoints=5
        )
        expected_lons = [lon] * 5
        expected_lats = [lat] * 5
        expected_depths = [depth] * 5
        assert_aeq(lons, expected_lons)
        assert_aeq(lats, expected_lats)
        assert_aeq(depths, expected_depths)

    def test_input_as_int(self):
        lons, lats, depths = geodetic.npoints_towards(
            lon=0, lat=0, depth=0, azimuth=0,
            hdist=0, vdist=5, npoints=7
        )
        expected_lons = [0, 0, 0, 0, 0, 0, 0]
        expected_lats = [0, 0, 0, 0, 0, 0, 0]
        expected_depths = [0, 0.8333333, 1.6666667, 2.5, 3.3333333, 4.1666667, 5]
        numpy.testing.assert_almost_equal(lons, expected_lons)
        numpy.testing.assert_almost_equal(lats, expected_lats)
        numpy.testing.assert_almost_equal(depths, expected_depths)
        self.assertEqual(lons[0], 0)
        self.assertEqual(lats[0], 0)
        self.assertEqual(depths[0], 0)

    def test_topo(self):
        lons, lats, depths = geodetic.npoints_towards(
            lon=-30.5, lat=23.6, depth=2, azimuth=-100.5,
            hdist=400, vdist=-4, npoints=5
        )
        expected_lons = [-30.5, -31.46375358, -32.42503446,
                         -33.3837849, -34.33995063]
        expected_lats = [23.6, 23.43314083, 23.26038177,
                         23.08178673, 22.8974212]
        expected_depths = [2, 1, 0, -1, -2]
        assert_aeq(lons, expected_lons)
        assert_aeq(lats, expected_lats)
        assert_aeq(depths, expected_depths)
        # the first point should be exactly the same
        # as the original starting point
        self.assertEqual(lons[0], -30.5)
        self.assertEqual(lats[0], 23.6)
        self.assertEqual(depths[0], 2)


class IntervalsBetweenTest(unittest.TestCase):
    # values in this test have not been checked by hand
    def test_round_down(self):
        lons, lats, depths = geodetic.intervals_between(
            lon1=10, lat1=-4, depth1=100,
            lon2=12, lat2=4, depth2=60,
            length=380
        )
        expected_lons = [10., 10.82836972, 11.65558943]
        expected_lats = [-4, -0.68763949, 2.62486454]
        expected_depths = [100, 83.43802828, 66.87605655]
        assert_aeq(lons, expected_lons)
        assert_aeq(lats, expected_lats)
        assert_aeq(depths, expected_depths)

    def test_round_up(self):
        lons, lats, depths = geodetic.intervals_between(
            lon1=10, lat1=-4, depth1=100,
            lon2=12, lat2=4, depth2=60,
            length=350
        )
        expected_lons = [10., 10.76308634, 11.52482625, 12.28955192]
        expected_lats = [-4, -0.94915589, 2.10185625, 5.15249576]
        expected_depths = [100, 84.74555236, 69.49110472, 54.23665708]
        assert_aeq(lons, expected_lons)
        assert_aeq(lats, expected_lats)
        assert_aeq(depths, expected_depths)

    def test_round_down_topo(self):
        lons, lats, depths = geodetic.intervals_between(
            lon1=0, lat1=0, depth1=0,
            lon2=0, lat2=0, depth2=-2.9,
            length=2
        )
        expected_lons = [0, 0]
        expected_lats = [0, 0]
        expected_depths = [0, -2]
        assert_aeq(lons, expected_lons)
        assert_aeq(lats, expected_lats)
        assert_aeq(depths, expected_depths)

    def test_round_up_topo(self):
        lons, lats, depths = geodetic.intervals_between(
            lon1=0, lat1=0, depth1=0,
            lon2=0, lat2=0, depth2=-3,
            length=2
        )
        expected_lons = [0, 0, 0]
        expected_lats = [0, 0, 0]
        expected_depths = [0, -2, -4]
        assert_aeq(lons, expected_lons)
        assert_aeq(lats, expected_lats)
        assert_aeq(depths, expected_depths)

    def test_zero_intervals(self):
        lons, lats, depths = geodetic.intervals_between(
            lon1=10, lat1=1, depth1=100, lon2=10.04, lat2=1.5, depth2=90,
            length=140
        )
        expected_lons = [10]
        expected_lats = [1]
        expected_depths = [100]
        assert_aeq(lons, expected_lons)
        assert_aeq(lats, expected_lats)
        assert_aeq(depths, expected_depths)

    def test_same_number_of_intervals(self):
        # these two set of points are separated by a distance of 65 km. By
        # discretizing the line every 2 km, the number of expected points for
        # both sets (after rounding) must be 34
        lons_1, lats_1, depths_1 = geodetic.intervals_between(
            lon1=132.2272081355264675, lat1=31.0552366690758639,
            depth1=7.7000000000000002,
            lon2=131.6030780890111203, lat2=31.1968015468782589,
            depth2=28.8619300397151832,
            length=2.0
        )

        lons_2, lats_2, depths_2 = geodetic.intervals_between(
            lon1=132.2218096511129488, lat1=31.0378653652772165,
            depth1=7.7000000000000002,
            lon2=131.5977943677305859, lat2=31.1794320218608547,
            depth2=28.8619300397151832,
            length=2.0
        )

        assert_aeq(34, lons_1.shape[0])
        assert_aeq(34, lons_2.shape[0])
        assert_aeq(34, lats_1.shape[0])
        assert_aeq(34, lats_2.shape[0])
        assert_aeq(34, depths_1.shape[0])
        assert_aeq(34, depths_2.shape[0])
