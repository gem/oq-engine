# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2021 GEM Foundation
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

# Test data have been generated from the Python implementation available from the authors


from openquake.hazardlib.gsim.manea_2021 import ManeaEtAl2021fore, ManeaEtAl2021back, ManeaEtAl2021along
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

#forearc test case
class ManeaEtAl2021foreTestCase(BaseGSIMTestCase):
    """
    Test the default model, the total standard deviation, the between- and the within-event
    standard deviation. 
    """

    GSIM_CLASS = ManeaEtAl2021fore

    def test_all(self):
        self.check('MANEA20/Manea_2020_mean_fore.csv',
                   'MANEA20/Manea_2020_total_fore.csv',
                   'MANEA20/Manea_2020_inter_fore.csv',
                   'MANEA20/Manea_2020_intra_fore.csv',
                   max_discrep_percentage=0.1)
        
#alongarc test case
class ManeaEtAl2021alongTestCase(BaseGSIMTestCase):
    """
    Test the default model, the total standard deviation, the between- and the within-event
    standard deviation. 
    """

    GSIM_CLASS = ManeaEtAl2021along

    def test_all(self):
        self.check('MANEA20/Manea_2020_mean_along.csv',
                   max_discrep_percentage=0.1)
        
        
#backarc test case
class ManeaEtAl2021backTestCase(BaseGSIMTestCase):
    """
    Test the default model, the total standard deviation, the between- and the within-event
    standard deviation. 
    """

    GSIM_CLASS = ManeaEtAl2021back

    def test_all(self):
        self.check('MANEA20/Manea_2020_mean_back.csv',
                   max_discrep_percentage=0.1)
