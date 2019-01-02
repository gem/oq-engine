#
# Copyright (C) 2014-2018 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import unittest
import numpy as np
from openquake.hazardlib.gsim.can15.utils import (
    get_equivalent_distances_west, get_rup_len_west, get_rup_wid_west,
    get_equivalent_distances_east)


class WesternRuptureDimensionTestCase(unittest.TestCase):
    """
    This class tests the calculation of rupture length and width in active
    shallow crust
    """

    def test_get_length(self):
        """ Test the calculation of rupture length"""
        mags = np.array([4.5, 5.5, 6.5, 7.5])
        computed = get_rup_len_west(mags)
        # values computed by hand
        expected = np.array([1.64058977, 6.38263486, 24.83133105, 96.6050879])
        np.testing.assert_almost_equal(computed, expected)

    def test_get_width(self):
        """ Test the calculation of rupture length"""
        mags = np.array([4.5, 5.5, 6.5, 7.5])
        computed = get_rup_wid_west(mags)
        # values computed by hand
        expected = np.array([2.6915348, 5.62341325, 11.74897555, 24.54708916])
        np.testing.assert_almost_equal(computed, expected)


class GetEquivalenDistanceWestTestCase(unittest.TestCase):
    """ This class tests the calculation of equivalent distances """

    def test_get_distances(self):
        mag = 6.5
        repi = 15.
        focal_depth = 10.
        comp_rrup, comp_rjb = get_equivalent_distances_west(mag, repi,
                                                            focal_depth)
        expected_rrup = 7.5506
        self.assertAlmostEqual(comp_rrup, expected_rrup, places=2)
        expected_rjb = 8.60615
        self.assertAlmostEqual(comp_rjb, expected_rjb, places=2)


class GetEquivalenDistanceEastTestCase(unittest.TestCase):
    """ This class tests the calculation of equivalent distances """

    def test_get_distances(self):
        mag = 6.5
        repi = 15.
        focal_depth = 10.
        comp_rrup, comp_rjb = get_equivalent_distances_east(mag, repi,
                                                            focal_depth)
        expected_rrup = 10.53042
        self.assertAlmostEqual(comp_rrup, expected_rrup, places=2)
        expected_rjb = 12.36326
        self.assertAlmostEqual(comp_rjb, expected_rjb, places=2)

    def test_get_distances_ab06(self):
        mag = 6.5
        repi = 15.
        focal_depth = 10.
        comp_rrup, comp_rjb = get_equivalent_distances_east(mag, repi,
                                                            focal_depth, True)
        expected_rrup = 10.53042
        self.assertAlmostEqual(comp_rrup, expected_rrup, places=2)
        expected_rjb = 12.36326
        self.assertAlmostEqual(comp_rjb, expected_rjb, places=2)

    def test_get_distances_ab06_01(self):
        mag = 6.5
        repi = 15.
        focal_depth = 10.
        comp_rrup, comp_rjb = get_equivalent_distances_east(mag, repi,
                                                            focal_depth, True)
        expected_rrup = 10.53042
        self.assertAlmostEqual(comp_rrup, expected_rrup, places=2)
        expected_rjb = 12.36326
        self.assertAlmostEqual(comp_rjb, expected_rjb, places=2)

