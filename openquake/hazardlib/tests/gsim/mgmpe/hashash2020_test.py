# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2020, GEM Foundation
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
"""
Module :mod:`openquake.hazardlib.tests.gsim.mgmpe.hashash2020` tests
the ergodic nonlinear amplification model of Hashash et al. (2020)
"""

import unittest
import numpy as np

from openquake.hazardlib.imt import from_string
from openquake.hazardlib.gsim.mgmpe.hashash2020 import (
    hashash2020_non_linear_scaling)


class HashashEtAl2020Test(unittest.TestCase):

    def test_amplification_pga(self):
        vs30 = np.array([400.0, 2800.0, 3000.0])
        imtstr = from_string('PGA')
        ref_pga = np.ones_like(vs30) * 0.1
        ref_vs30 = 3000.0
        fv = hashash2020_non_linear_scaling(imtstr, vs30, ref_pga, ref_vs30)
        # results computed by hand
        expected = np.array([-0.146867, -0.      ,  0.])
        np.testing.assert_allclose(fv, expected, atol=1e-6)

    def test_usgs_vs30_floor(self):
        # Under usgs=True, Vs30 valus below 200 m/s should give the
        # same nonlinear term as Vs30 = 200 m/s (floor adopted by the
        # US 2023 NSHM revisions in Powers et al., EQS, 2026)
        imt = from_string('SA(1.0)')
        ref_vs30 = 3000.0
        ref_pga = np.array([0.3, 0.3])
        vs30_low = np.array([150.0, 180.0])
        vs30_floor = np.array([200.0, 200.0])
        f_low = hashash2020_non_linear_scaling(
            imt, vs30_low, ref_pga, ref_vs30, usgs=True)
        f_floor = hashash2020_non_linear_scaling(
            imt, vs30_floor, ref_pga, ref_vs30, usgs=True)
        np.testing.assert_allclose(f_low, f_floor, atol=1e-10)

    def test_usgs_pga_rock_cap(self):
        # Under usgs=True, PGA-rock values above 1.0 g should give the
        # same nonlinear term as PGA-rock = 1.0 g (cap adopted by the
        # US 2023 NSHM revisions in Powers et al., EQS, 2026)
        imt = from_string('SA(1.0)')
        ref_vs30 = 3000.0
        vs30 = np.array([250.0, 300.0])
        ref_pga_high = np.array([1.5, 2.0])
        ref_pga_cap = np.array([1.0, 1.0])
        f_high = hashash2020_non_linear_scaling(
            imt, vs30, ref_pga_high, ref_vs30, usgs=True)
        f_cap = hashash2020_non_linear_scaling(
            imt, vs30, ref_pga_cap, ref_vs30, usgs=True)
        np.testing.assert_allclose(f_high, f_cap, atol=1e-10)
