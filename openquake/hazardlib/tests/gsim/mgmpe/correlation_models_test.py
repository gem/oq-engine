# The Hazard Library
# Copyright (C) 2012-2026 GEM Foundation
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
from openquake.hazardlib.gsim.mgmpe.generic_gmpe_avgsa import (
    BaseAvgSACorrelationModel
)

class BaseAvgSACorrelationModelTestCase(unittest.TestCase):
    """
    Testing instantiation of the BaseAvgSACorrelationModel class
    """

    def test_instantiation_with_periods(self):
        avg_periods = np.array([1, 2, 3])
        corr_model = BaseAvgSACorrelationModel(avg_periods)

        # Assertions:
        np.testing.assert_array_almost_equal(corr_model.avg_periods, avg_periods)
        with self.assertRaises(AttributeError):
            # it goes into build_correlation_matrix nothing happens 
            corr_model.rho      
        

    def test_instantiation_without_periods(self):
        corr_model = BaseAvgSACorrelationModel()

        # Assertions:
        assert corr_model.rho is None
        assert corr_model.avg_periods is None
        with self.assertRaises(RuntimeError) as e:
            # it goes into build_correlation_matrix nothing happens 
            corr_model(0, 0)

        assert str(e.exception) == \
            "Correlation Matrix not built. Provide 'avg_periods' at init."


