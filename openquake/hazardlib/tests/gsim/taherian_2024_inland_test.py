# -*- coding: utf-8 -*-
"""
Created on Tue Sep 30 16:13:22 2025

@author: 35191
"""

# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2025-2026 GEM Foundation
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
Test suite for Taherian et al. (2024) GMPE for inland scenarios.
"""

from openquake.hazardlib.gsim.taherian_2024_inland import (
    Taherian2024Inland
)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class Taherian2024InlandTestCase(BaseGSIMTestCase):
    """
    Tests the Taherian et al. (2024) GMPE for inland scenarios in
    Western Iberia.
    
    Verification tables were generated using the original ONNX model
    implementation with embedded scalers as provided by the authors.
    """
    GSIM_CLASS = Taherian2024Inland
    
    def test_mean(self):
        """
        Test mean ground motion predictions.
        """
        self.check('TAHERIAN2024INLAND/TAHERIAN2024INLAND_MEAN.csv',
                   max_discrep_percentage=0.1)
    
    def test_std_total(self):
        """
        Test total standard deviation predictions.
        """
        self.check('TAHERIAN2024INLAND/TAHERIAN2024INLAND_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)