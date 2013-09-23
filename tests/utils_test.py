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
