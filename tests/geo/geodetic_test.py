# nhlib: A New Hazard Library
# Copyright (C) 2012 GEM Foundation
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

import numpy

from nhlib.geo import geodetic


LAX = (118 + 24 / 60., 33 + 57 / 60.)
JFK = (73 + 47 / 60., 40 + 38 / 60.)


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
        coords = map(numpy.array, [(77.5, -150.), (-10., 15.),
                                   (77.5, -150.), (-20., 25.)])
        dist = geodetic.geodetic_distance(*coords)
        self.assertTrue(numpy.allclose(dist, [1111.949, 1111.949]), str(dist))

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
        self.assertTrue(numpy.allclose(dist, edist))

    def test_one_to_many(self):
        dist = geodetic.geodetic_distance(0, 0, [-1, 1], [0, 0])
        self.assertTrue(numpy.allclose(dist, [111.195, 111.195]), str(dist))
        dist = geodetic.geodetic_distance(0, 0, [[-1, 0], [1, 0]],
                                                [[0, 0], [0, 0]])
        self.assertTrue(numpy.allclose(dist, [[111.195, 0], [111.195, 0]]),
                        str(dist))
