# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2023 GEM Foundation
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

from openquake.hazardlib.gsim.arroyo_2010 import ArroyoEtAl2010SInter
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# The verification tables were generated using a Visual Basic code 
# provided by Danny Arroyo. The format of the tables was adapted to 
# the requirements of the OQ tests.

class ArroyoEtAl2010SInterTestCase(BaseGSIMTestCase):
    """
    Test Arroyo et al. (2010) GMPE for Mexican subduction
    interface earthquakes.
    """
    GSIM_CLASS = ArroyoEtAl2010SInter
    def test_all(self):
        self.check('AR10/AR10_SINTER_MEAN.csv',
                   'AR10/AR10_SINTER_STD_TOTAL.csv',
                   'AR10/AR10_SINTER_STD_INTER.csv',
                   'AR10/AR10_SINTER_STD_INTRA.csv',
                   max_discrep_percentage=0.01,
                   std_discrep_percentage=0.01)
