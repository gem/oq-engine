# The Hazard Library
# Copyright (C) 2013-2025 GEM Foundation
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

from openquake.hazardlib.gsim.wang_2025_turkey import WangEtAl2025
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class WangEtAl2025TestCase(BaseGSIMTestCase):
    GSIM_CLASS = WangEtAl2025

    
    def test_mean(self):
        """
        Median Prediction
        """
        self.check('Wang2025/Wang2025_MEAN.csv',
                   max_discrep_percentage=0.1) 

    def test_std_total(self):
        """
        (Total Standard Deviation)
        """
        self.check('Wang2025/Wang2025_TOTAL_STD.csv',
                   max_discrep_percentage=0.1)

    def test_std_inter(self):
        """
         (Inter-Event Standard Deviation)
        """
        self.check('Wang2025/Wang2025_INTER_STD.csv',
                   max_discrep_percentage=0.1)

    def test_std_intra(self):
        """
         (Intra-Event Standard Deviation)
        """
        self.check('Wang2025/Wang2025_INTRA_STD.csv',
                   max_discrep_percentage=0.1)
