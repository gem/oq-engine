# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2019 GEM Foundation
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

import numpy as np
import unittest
from openquake.hazardlib.imt import PGA
from openquake.hazardlib.contexts import DistancesContext
from openquake.hazardlib.tests.gsim.mgmpe.dummy import Dummy
from openquake.hazardlib.gsim.yenier_atkinson_2015 import (
    YenierAtkinson2015BSSA)


class YenierAtkinson2015BSSATest(unittest.TestCase):

    """
    def test_f_z(self):
        mag = 6.0
        rrup = [10., 50., 100.]
        rrup = np.array([10.])
        imt = PGA()
        gmm = YenierAtkinson2015BSSA(focal_depth=10.)
        computed = gmm._get_f_z(gmm.TAB2[imt], imt, rrup, mag)
        expected = np.array([-3.537768])
        np.testing.assert_allclose(computed, expected)

    def test_delta_sigma(self):
        mag = 6.0
        rrup = [10., 50., 100.]
        rrup = np.array([10.])
        imt = PGA()
        gmm = YenierAtkinson2015BSSA(focal_depth=10.)
        computed = gmm._get_delta_sigma(gmm.TAB2[imt], imt, mag)
        expected = np.array([-3.537768])
        print(computed)
        np.testing.assert_allclose(computed, expected)
    """

    def test_gm(self):
        dists = DistancesContext()
        dists.rrup = np.array([10.])
        imt = PGA()
        mag = 6.0
        rup = Dummy.get_rupture(mag=mag)
        slen = len(dists.rrup)
        sites = Dummy.get_site_collection(slen, vs30=760.)
        gmm = YenierAtkinson2015BSSA(focal_depth=10.)
        mean, _ = gmm.get_mean_std(sites, rup, dists, [imt])
        print('mean:', mean)
