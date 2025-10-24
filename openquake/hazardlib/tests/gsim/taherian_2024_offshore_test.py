# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2025 GEM Foundation
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
Test suite for Taherian et al. (2024) GMPE for offshore scenarios.
"""

from openquake.hazardlib.gsim.taherian_2024_offshore import (
    Taherian2024Offshore
)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class Taherian2024OffshoreTestCase(BaseGSIMTestCase):
    """
    Tests the Taherian et al. (2024) GMPE for offshore scenarios in
    Western Iberia.

    Verification tables were generated using the original ONNX model
    implementation with embedded scalers as provided by the authors.
    """
    GSIM_CLASS = Taherian2024Offshore

    def test_mean(self):
        """
        Test mean ground motion predictions.
        """
        self.check('TAHERIAN2024OFFSHORE/TAHERIAN2024OFFSHORE_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        """
        Test total standard deviation predictions.
        """
        self.check('TAHERIAN2024OFFSHORE/TAHERIAN2024OFFSHORE_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)