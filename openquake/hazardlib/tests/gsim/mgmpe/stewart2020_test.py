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
Module :mod:`openquake.hazardlib.tests.gsim.mgmpe.stewartEtAl2020` implements
the ergodic amplification model of Stewart et al. (2020)
"""

import unittest
import numpy as np

from openquake.hazardlib.imt import from_string
from openquake.hazardlib.gsim.mgmpe.stewart2020 import vs30_scaling_model


class StewartEtAl2020Test(unittest.TestCase):

    def test_amplification_pga(self):
        vs30 = np.array([201.0, 400.0, 800.0])
        imt = from_string('PGA')
        wimp = 1.0
        wgr = 1.0 - wimp
        fv = vs30_scaling_model(imt, vs30, wimp, wgr)
        # hand computed results
        expected = np.array([0.25175693, 0.18613762, 0.0])
        np.testing.assert_allclose(fv, expected)
