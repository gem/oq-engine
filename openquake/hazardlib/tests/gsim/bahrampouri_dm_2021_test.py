#!/usr/bin/env python
# coding: utf-8


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

"""
    Implements GMPE by Mahdi Bahrampouri, Adrian Rodriguez-Marek and Russell A Green 
    developed from the Kiban-Kyoshin network (KiK)-net database. This GMPE is specifically derived
    for significant durations: Ds5-Ds95,D25-Ds75 . This GMPE is described in a paper
    published in 2021 on Earthquake Spectra, Volume 37, Pg 903-920 and
    titled 'Ground motion prediction equations for significant duration using the KiK-net database'.
"""
from openquake.hazardlib.gsim.bahrampouri_dm_2021 import BahrampouriEtAldm2021Asc
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Discrepency percentages to be applied to all tests
MEAN_DISCREP = 0.1

class BahrampouriEtAl2021RSDTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BahrampouriEtAldm2021Asc
    # File containing the results for the Mean
    MEAN_FILE = "BMG20/BMG20_D_ASC_mean.csv"

    def test_all(self):
        self.check(self.MEAN_FILE,
		max_discrep_percentage=MEAN_DISCREP)


from openquake.hazardlib.gsim.bahrampouri_dm_2021 import BahrampouriEtAldm2021SInter

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Discrepency percentages to be applied to all tests
MEAN_DISCREP = 0.1

class BahrampouriEtAl2021RSDTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BahrampouriEtAldm2021SInter
    # File containing the results for the Mean
    MEAN_FILE = "BMG20/BMG20_D_SInter_mean.csv"

    def test_all(self):
        self.check(self.MEAN_FILE,
		max_discrep_percentage=MEAN_DISCREP)


# # In[3]:


from openquake.hazardlib.gsim.bahrampouri_dm_2021 import BahrampouriEtAldm2021SSlab

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Discrepency percentages to be applied to all tests
MEAN_DISCREP = 0.1


class BahrampouriEtAl2021RSDTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BahrampouriEtAldm2021SSlab
    # File containing the results for the Mean
    MEAN_FILE = "BMG20/BMG20_D_SSlab_mean.csv"

    def test_all(self):
        self.check(self.MEAN_FILE,
		max_discrep_percentage=MEAN_DISCREP)
