# Copyright (c) 2010-2012, GEM Foundation.
#
# NRML is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# NRML is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with NRML.  If not, see <http://www.gnu.org/licenses/>.


import numpy
import unittest

from openquake.nrmllib import utils


class UtilsTestCase(unittest.TestCase):
    """Tests for general NRML util functions."""

    def test_coords_to_linestr_wkt_2d(self):
        expected = 'LINESTRING(1.0 1.0, 2.0 2.0, 3.0 3.0)'

        # Mixed input types for robustness testing
        coords = [1.0, '1.0', '2.0', 2.0, 3.0, '3.0']

        actual = utils.coords_to_linestr_wkt(coords, 2)

        self.assertEqual(expected, actual)

    def test_coords_to_linestr_wkt_3d(self):
        expected = 'LINESTRING(1.0 1.0 2.0, 2.0 3.0 3.0)'

        coords = [1.0, '1.0', '2.0', 2.0, 3.0, '3.0']

        actual = utils.coords_to_linestr_wkt(coords, 3)

        self.assertEqual(expected, actual)

    def test_coords_to_poly_wkt_2d(self):
        expected = 'POLYGON((1.0 1.0, 2.0 2.0, 3.0 3.0, 1.0 1.0))'

        coords = [1.0, '1.0', '2.0', 2.0, 3.0, '3.0']

        actual = utils.coords_to_poly_wkt(coords, 2)

        self.assertEqual(expected, actual)

    def test_coords_to_poly_wkt_3d(self):
        expected = (
            'POLYGON((1.0 1.0 0.1, 2.0 2.0 0.2, 3.0 3.0 0.3, 1.0 1.0 0.1))')

        coords = [1.0, '1.0', 0.1, '2.0', 2.0, '0.2', 3.0, '3.0', 0.3]

        actual = utils.coords_to_poly_wkt(coords, 3)

        self.assertEqual(expected, actual)


class NDEnumTestCase(unittest.TestCase):

    def test_1d(self):
        a = numpy.array([x * 3 for x in range(4)])
        expected = [
            ((0,), 0),
            ((1,), 3),
            ((2,), 6),
            ((3,), 9),
        ]
        actual = list(utils.ndenumerate(a))
        self.assertEqual(expected, actual)

    def test_3d(self):
        a = numpy.array([x * 3 for x in range(24)]).reshape((3, 2, 4))
        expected = [
            ((0, 0, 0), 0),
            ((0, 0, 1), 3),
            ((0, 0, 2), 6),
            ((0, 0, 3), 9),
            ((0, 1, 0), 12),
            ((0, 1, 1), 15),
            ((0, 1, 2), 18),
            ((0, 1, 3), 21),
            ((1, 0, 0), 24),
            ((1, 0, 1), 27),
            ((1, 0, 2), 30),
            ((1, 0, 3), 33),
            ((1, 1, 0), 36),
            ((1, 1, 1), 39),
            ((1, 1, 2), 42),
            ((1, 1, 3), 45),
            ((2, 0, 0), 48),
            ((2, 0, 1), 51),
            ((2, 0, 2), 54),
            ((2, 0, 3), 57),
            ((2, 1, 0), 60),
            ((2, 1, 1), 63),
            ((2, 1, 2), 66),
            ((2, 1, 3), 69),
        ]
        actual = list(utils.ndenumerate(a))
        self.assertEqual(expected, actual)

    def test_4d(self):
        a = numpy.array([x * 3 for x in range(48)]).reshape((2, 2, 3, 4))
        expected = [
            ((0, 0, 0, 0), 0),
            ((0, 0, 0, 1), 3),
            ((0, 0, 0, 2), 6),
            ((0, 0, 0, 3), 9),
            ((0, 0, 1, 0), 12),
            ((0, 0, 1, 1), 15),
            ((0, 0, 1, 2), 18),
            ((0, 0, 1, 3), 21),
            ((0, 0, 2, 0), 24),
            ((0, 0, 2, 1), 27),
            ((0, 0, 2, 2), 30),
            ((0, 0, 2, 3), 33),
            ((0, 1, 0, 0), 36),
            ((0, 1, 0, 1), 39),
            ((0, 1, 0, 2), 42),
            ((0, 1, 0, 3), 45),
            ((0, 1, 1, 0), 48),
            ((0, 1, 1, 1), 51),
            ((0, 1, 1, 2), 54),
            ((0, 1, 1, 3), 57),
            ((0, 1, 2, 0), 60),
            ((0, 1, 2, 1), 63),
            ((0, 1, 2, 2), 66),
            ((0, 1, 2, 3), 69),
            ((1, 0, 0, 0), 72),
            ((1, 0, 0, 1), 75),
            ((1, 0, 0, 2), 78),
            ((1, 0, 0, 3), 81),
            ((1, 0, 1, 0), 84),
            ((1, 0, 1, 1), 87),
            ((1, 0, 1, 2), 90),
            ((1, 0, 1, 3), 93),
            ((1, 0, 2, 0), 96),
            ((1, 0, 2, 1), 99),
            ((1, 0, 2, 2), 102),
            ((1, 0, 2, 3), 105),
            ((1, 1, 0, 0), 108),
            ((1, 1, 0, 1), 111),
            ((1, 1, 0, 2), 114),
            ((1, 1, 0, 3), 117),
            ((1, 1, 1, 0), 120),
            ((1, 1, 1, 1), 123),
            ((1, 1, 1, 2), 126),
            ((1, 1, 1, 3), 129),
            ((1, 1, 2, 0), 132),
            ((1, 1, 2, 1), 135),
            ((1, 1, 2, 2), 138),
            ((1, 1, 2, 3), 141),
        ]
        actual = list(utils.ndenumerate(a))
        self.assertEqual(expected, actual)
