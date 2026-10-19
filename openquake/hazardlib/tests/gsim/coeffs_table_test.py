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
import toml
import numpy as np
from openquake.hazardlib.gsim.coeffs_table import CoeffsTable
from openquake.hazardlib.imt import SA, PGA
from openquake.hazardlib.gsim.atkinson_boore_2006 import (
    AtkinsonBoore2006Modified2011)


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

    def test_to_dict(self):
        ddic = self.ctab.to_dict()
        self.assertEqual(toml.dumps(ddic), '''\
[PGA]
a1 = 0.1
a2 = 0.2
a3 = 0.3

["SA(0.01)"]
a1 = 0.4
a2 = 0.5
a3 = 0.6

["SA(0.05)"]
a1 = 0.7
a2 = 0.8
a3 = 0.9
''')
        self.ctab.fromdict(ddic)

    def test_update_coeff(self):
        self.ctab |= CoeffsTable.fromtoml('["SA(0.01)"]\na1 = 0.11')
        coeffs = self.ctab[SA(0.01)]
        np.testing.assert_array_equal(list(coeffs), [0.11, 0.5, 0.6])

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

    def test_pga_fallback_below_min_sa(self):
        """
        SA periods below the smallest tabulated SA row interpolate in
        log-period between PGA (treated as SA at 0.01 s) and the smallest
        tabulated SA period, but only when the smallest tabulated SA period
        is at most 0.05 s AND the target period is at least 0.01 s. Otherwise
        an error is raised. This avoids interpolation over wide period
        gaps, e.g. from PGA at 0.01 s to SA at 0.1 s or beyond.
        """
        anchor = 0.01 # Treat PGA as SA(0.01)

        # TEST 1: PGA-anchored fallback on a real GMM's coefficient table
        table = AtkinsonBoore2006Modified2011().COEFFS_BC
        t_min = 0.025 # Min of GMM is 0.025 s (below 0.05 s)
        t_tar = 0.02  # Target T is 0.02
        pga = np.array(list(table[PGA()]))
        row_min = np.array(list(table[SA(t_min)]))
        ratio = np.log(t_tar / anchor) / np.log(t_min / anchor)
        expected = pga + ratio * (row_min - pga)
        result = table._pga_interp_fallback(SA(t_tar), SA(t_min))
        np.testing.assert_allclose(list(result), expected)

        # TEST 2: Check a table with smallest SA period above 0.05 s does not
        # interpolate. The min SA here is 0.1 s, so SA(0.05) raises a ValueError
        # telling the user the gap is too wide for "safe" interpolation
        wide_gap = CoeffsTable(sa_damping=5, table="""
            imt   a
            pga   1
            0.1   10
            1.0   3""")
        with self.assertRaises(ValueError) as cm:
            wide_gap[SA(0.05)]
        self.assertEqual(
            str(cm.exception),
            "Cannot interpolate SA(0.05): PGA-anchored fallback requires "
            "the smallest tabulated SA period to be <= 0.05 s, but this "
            "GMM's smallest SA period is 0.1 s")

        # TEST 3: Table with no PGA row - fallback needs a PGA anchor row
        no_pga = CoeffsTable(sa_damping=5, table="""
            imt   a
            0.02  5
            0.1   10
            1.0   3""")
        with self.assertRaises(ValueError) as cm:
            no_pga[SA(0.015)]
        self.assertEqual(
            str(cm.exception),
            "Cannot interpolate SA(0.015): PGA-anchored fallback requires "
            "a PGA row in the coefficient table, but none is present")

        # TEST 4: Target period below the PGA anchor (0.01 s) - fallback
        # cannot extrapolate below PGA
        with self.assertRaises(ValueError) as cm:
            table[SA(0.005)]
        self.assertEqual(
            str(cm.exception),
            "Cannot interpolate SA(0.005): PGA-anchored fallback cannot "
            "extrapolate below the PGA anchor at 0.01 s")

        # TEST 5: Smallest SA exactly at the 0.05 s gate - fallback accepts
        at_gate = CoeffsTable(sa_damping=5, table="""
            imt   a
            pga   1.0
            0.05  5.0
            1.0   9.0""")
        ratio = np.log(0.02 / anchor) / np.log(0.05 / anchor)
        np.testing.assert_allclose(
            list(at_gate[SA(0.02)]), [1.0 + ratio * (5.0 - 1.0)])

        # TEST 6: Target exactly at the PGA anchor (0.01 s) - returns PGA row
        np.testing.assert_allclose(
            list(at_gate[SA(anchor)]), list(at_gate[PGA()]))

        # TEST 7: Smallest SA just above the 0.05 s gate - fallback rejects
        just_over = CoeffsTable(sa_damping=5, table="""
            imt   a
            pga   1.0
            0.051 5.0
            1.0   9.0""")
        with self.assertRaises(ValueError) as cm:
            just_over[SA(0.02)]
        self.assertEqual(
            str(cm.exception),
            "Cannot interpolate SA(0.02): PGA-anchored fallback requires "
            "the smallest tabulated SA period to be <= 0.05 s, but this "
            "GMM's smallest SA period is 0.051 s")
