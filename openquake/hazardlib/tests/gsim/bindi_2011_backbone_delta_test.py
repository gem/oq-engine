# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
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

import numpy as np
import unittest

from openquake.hazardlib.imt import PGA, SA, PGV
from openquake.hazardlib.gsim.ita19.bindi_2011_backbone import BindiEtAl2011Ita19Low


class GetDeltaTest(unittest.TestCase):

    def test_mag5(self):
        m = 5.0
        gmm = BindiEtAl2011Ita19Low()
        imts = [PGA(), SA(0.05), SA(0.1), SA(0.15), SA(0.2),
                SA(0.3), SA(0.4), SA(0.5), SA(0.75), SA(1.00), SA(2.00),
                SA(3.00), SA(4.00), PGV()]
        computed = []
        for imt in imts:
            dlt = gmm._get_delta(imt, m)
            computed.append(dlt)
        expected = np.array([0.4, 0.366, 0.381, 0.362, 0.421, 0.384, 0.406,
                             0.428, 0.413, 0.39, 0.353, 0.363, 0.416, 0.345])
        np.testing.assert_array_almost_equal(computed, expected)

    def test_mag7pt2(self):
        m = 7.2
        gmm = BindiEtAl2011Ita19Low()
        imts = [PGA(), SA(0.05), SA(0.1), SA(0.15), SA(0.2),
                SA(0.3), SA(0.4), SA(0.5), SA(0.75), SA(1.00), SA(2.00),
                SA(3.00), SA(4.00), PGV()]
        computed = []
        for imt in imts:
            dlt = gmm._get_delta(imt, m)
            computed.append(dlt)
        expected = np.array([0.61164, 0.5662, 0.56228, 0.61236, 0.707, 0.65284,
                             0.62512, 0.64052, 0.59472, 0.54224, 0.32704,
                             0.3498, 0.46264, 0.48624])
        np.testing.assert_array_almost_equal(computed, expected)

