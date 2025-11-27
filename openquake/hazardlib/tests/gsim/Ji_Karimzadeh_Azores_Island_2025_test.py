# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2025 GEM Foundation
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

from openquake.hazardlib.gsim.Ji_Karimzadeh_Azores_Island_2025 import JiEtAl2025Azores
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class JiEtAl2025AzoresTestCase(BaseGSIMTestCase):
    GSIM_CLASS = JiEtAl2025Azores


    
    def test_mean(self):
        """
        Median Ground Motion
        """
        self.check('JI25/JI25_MEDIAN.csv',
                   max_discrep_percentage=0.6) 

    def test_std_total(self):
        """
        (Total Standard Deviation)
         sqrt(stdintra^2 + stdinter^2)
        """
        self.check('JI25/JI25_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)

    def test_std_inter(self):
        """
         (Inter-event Standard Deviation)
        stdinter (Tau)
        """
        self.check('JI25/JI25_STD_INTER.csv',
                   max_discrep_percentage=0.1)

    def test_std_intra(self):
        """
         (Intra-event Standard Deviation)
         stdintra (Phi)
        """
        self.check('JI25/JI25_STD_INTRA.csv',
                   max_discrep_percentage=0.1)