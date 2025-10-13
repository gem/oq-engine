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
