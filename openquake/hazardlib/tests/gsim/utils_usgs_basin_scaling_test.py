# The Hazard Library
# Copyright (C) 2014-2023 GEM Foundation
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

exp_z1pt0_baf = np.array([[0.5, 0. , 0. , 0.5, 1. ],
                          [0.2925, 0.    , 0.    , 0.2925, 0.585 ],
                          [0.5, 0. , 0. , 0.5, 1. ],
                          [0.5, 0. , 0. , 0.5, 1. ]])

exp_z2pt5_baf = np.array([[0.5, 0. , 1. , 1. , 1. ],
                          [0.2925, 0.    , 0.585 , 0.585 , 0.585 ],
                          [0.5, 0. , 1. , 1. , 1. ],
                          [0.5, 0. , 1. , 1. , 1. ]])


class USGSBasinScalingTestCase(unittest.TestCase):
    """
    Check execution and correctness of values for the USGS basin scaling
    factors (scaling factors can be applied to basin terms in GMMs)
    """
    def test_usgs_basin_scaling(self):
        # Some example (physically correlated) z1pt0 and z2pt5
        z1pt0 = np.array([0.4, 0.3, 0.2, 0.4, 1])
        z2pt5 = np.array([2, 1, 4, 6, 3])
        # Some periods
        periods = np.array([0.0, 0.75, 2, 3.])

        for idx, period in enumerate(periods):
            z1pt0_baf = _get_z1pt0_usgs_basin_scaling(z1pt0, period)
            aae(z1pt0_baf, exp_z1pt0_baf[idx])
            z2pt5_baf = _get_z2pt5_usgs_basin_scaling(z2pt5, period)
            aae(z2pt5_baf, exp_z2pt5_baf[idx])