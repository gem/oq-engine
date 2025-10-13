# The Hazard Library
# Copyright (C) 2014-2025 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import unittest
import numpy as np

from openquake.hazardlib.gsim.utils_usgs_basin_scaling import (
    _get_z2pt5_usgs_basin_scaling, _get_z1pt0_usgs_basin_scaling)


aae = np.testing.assert_almost_equal

exp_z1pt0_baf = np.array([[0., 0., 0.0, 0., 0.],
                          [0.585, 0., 0.4593127, 0.5828355, 0.585],
                          [1., 0., 0.78515, 0.9963, 1.],
                          [1., 0., 0.78515, 0.9963, 1.]])

exp_z2pt5_baf = np.array([[0., 0., 0.0, 0., 0.],
                          [0.585, 0., 0.21645, 0.40365, 0.585],
                          [1., 0., 0.37, 0.69, 1.],
                          [1., 0., 0.37, 0.69, 1.]])


class USGSBasinScalingTestCase(unittest.TestCase):
    """
    Check execution and correctness of values for the USGS basin scaling
    factors (scaling factors can be applied to basin terms in GMMs)
    """
    def test_usgs_basin_scaling(self):
        # Some physically correlated z1pt0 and z2pt5 (from US sites model)
        z1pt0 = np.array([522.31, 0.03, 457.03, 499.26, 520.23]) # units is
                                                                 # metres
        z2pt5 = np.array([6.29, 0.18, 1.74, 2.38, 4.39])  # units is km
        # Some periods
        periods = np.array([0.0, 0.75, 2, 3.])

        # Get the baf per period at each site and check against exp values
        for idx, period in enumerate(periods):
            z1pt0_baf = _get_z1pt0_usgs_basin_scaling(z1pt0, period)
            aae(z1pt0_baf, exp_z1pt0_baf[idx])
            z2pt5_baf = _get_z2pt5_usgs_basin_scaling(z2pt5, period)
            aae(z2pt5_baf, exp_z2pt5_baf[idx])