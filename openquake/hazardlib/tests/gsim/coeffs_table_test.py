# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2021, GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import unittest
import numpy as np
from openquake.hazardlib.gsim.coeffs_table import CoeffsTable


class TestGetCoefficient(unittest.TestCase):
    """
    This tests a method in the
    :class:`openquake.hazardlib.gsim.coeffs_table.CoeffsTable` that provides
    all the values for a set of coefficients
    """

    def setUp(self):
        ctab = CoeffsTable("""
            imt a1 a2 a3
            PGA 0.1 0.2 0.3
            0.01 0.4 0.5 0.6
            0.05 0.7 0.8 0.9""")
        self.ctab = ctab

        ctab = CoeffsTable("""
            imt a1 a2 a3
            EAS(0.1) 0.1 0.2 0.3
            EAS(1.0) 0.7 0.8 0.9
            EAS(10.0) 1.0 1.1 1.2
            EAS(0.5) 0.4 0.5 0.6
                           """)
        self.ctab_eas = ctab

    def test_get_coeffs(self):
        pof, cff = self.ctab.get_coeffs(['a1', 'a2'])
        expected = np.array([[0.4, 0.5], [0.7, 0.8]])
        expected_pof = np.array([0.01, 0.05])
        np.testing.assert_array_equal(cff, expected)
        np.testing.assert_array_equal(pof, expected_pof)

    def test_get_coeffs_eas(self):
        pof, cff = self.ctab_eas.get_coeffs(['a1', 'a2'])
        expected = np.array([[0.1, 0.2], [0.4, 0.5], [0.7, 0.8], [1.0, 1.1]])
        expected_pof = np.array([0.1, 0.5, 1., 10.0,])
        np.testing.assert_array_equal(pof, expected_pof)
        np.testing.assert_array_equal(cff, expected)
