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
from openquake.hazardlib.gsim.boore_atkinson_2008 import BooreAtkinson2008
from openquake.hazardlib.gsim.campbell_bozorgnia_2014 import (
    CampbellBozorgnia2014)


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
        an error is raised. This avoids interpolation over wide gaps such
        as PGA (as 0.01 s) to SA at 0.1 s or larger.
        """
        anchor = 0.01

        # AtkinsonBoore2006Modified2011 smallest SA period = 0.025 s
        # (<= 0.05 s gate), so log-period interpolation between PGA (as SA
        # at 0.01 s) and SA(0.025) is applied for target T in [0.01, 0.025)
        table = AtkinsonBoore2006Modified2011().COEFFS_BC
        t_min = 0.025
        pga = np.array(list(table[PGA()]))
        row_min = np.array(list(table[SA(t_min)]))
        t_lo = np.sqrt(anchor * t_min)
        ratio = np.log(t_lo / anchor) / np.log(t_min / anchor)
        np.testing.assert_allclose(
            list(table[SA(t_lo)]), pga + ratio * (row_min - pga))

        # Synthetic table with smallest SA row 0.1 s: gate fails because
        # 0.1 > 0.05, so any target below 0.1 raises KeyError to avoid
        # interpolation across the wide PGA-to-SA(0.1) gap
        wide_gap = CoeffsTable(sa_damping=5, table="""
            imt   a
            pga   1
            0.1   10
            1.0   3""")
        with self.assertRaises(KeyError):
            wide_gap[SA(0.05)]

        # Real GMMs and their behaviour below the smallest SA row:
        # target periods below the 0.01 s anchor raise KeyError. In-range
        # SA targets still interpolate log-in-period between adjacent SA
        # rows without touching PGA (unchanged behaviour).
        # --> BooreAtkinson2008 lowest SA period = 0.01 s
        # --> CampbellBozorgnia2014 lowest SA period = 0.01 s
        # --> AtkinsonBoore2006Modified2011 lowest SA period = 0.025 s
        for cls, coeffs in [
            (BooreAtkinson2008, 'COEFFS'),
            (CampbellBozorgnia2014, 'COEFFS'),
            (AtkinsonBoore2006Modified2011, 'COEFFS_BC'),
        ]:
            table = getattr(cls(), coeffs)
            with self.assertRaises(KeyError):
                table[SA(0.005)]

            # In-range SA: log-interp between adjacent SA rows, no PGA
            t_min, t_next = sorted(imt.period for imt in table.sa_coeffs)[:2]
            row_min = np.array(list(table[SA(t_min)]))
            row_next = np.array(list(table[SA(t_next)]))
            t_in = np.sqrt(t_min * t_next)
            ratio = np.log(t_in / t_min) / np.log(t_next / t_min)
            np.testing.assert_allclose(
                list(table[SA(t_in)]), row_min + ratio * (row_next - row_min))
