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

"""
Implements the set of tests for the Boore, Stewart, Seyhan and Atkinson (2014)
GMPE
Test data are generated from the Fortran implementation provided by
David M. Boore (Jul, 2014)
"""
import openquake.hazardlib.gsim.boore_2014 as bssa
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Discrepency percentages to be applied to all tests
MEAN_DISCREP = 2.0
STDDEV_DISCREP = 1.0


def dic(templ):
    return {
        ('nobasin', True): templ % "",
        ('CAL', True): templ % "CALIFORNIA_",
        ('JPN', True): templ % "JAPAN_",
        ('nobasin', False): templ % "NOSOF_",
        ('CAL', False): templ % "CALIFORNIA_NOSOF_",
        ('JPN', False): templ % "JAPAN_NOSOF_",
    }


class BooreEtAl2014TestCase(BaseGSIMTestCase):
    """
    Tests the Boore et al. (2014) GMPE for the "global {default}" condition:
    Style of faulting included - "Global" Q model - No basin term
    """
    GSIM_CLASS = bssa.BooreEtAl2014
    MEAN_FILE = dic("BSSA2014/BSSA_2014_%sMEAN.csv")
    STD_FILE = dic("BSSA2014/BSSA_2014_%sTOTAL_STD.csv")
    INTER_FILE = dic("BSSA2014/BSSA_2014_%sINTER_STD.csv")
    INTRA_FILE = dic("BSSA2014/BSSA_2014_%sINTRA_STD.csv")

    def test_all(self):
        for region in ('nobasin', 'CAL', 'JPN'):
            for sof in (True, False):
                self.check(self.MEAN_FILE[region, sof],
                           self.STD_FILE[region, sof],
                           self.INTER_FILE[region, sof],
                           self.INTRA_FILE[region, sof],
                           max_discrep_percentage=MEAN_DISCREP,
                           std_discrep_percentage=STDDEV_DISCREP,
                           region=region, sof=sof)


class BooreEtAl2014HighQTestCase(BooreEtAl2014TestCase):
    """
    Tests the Boore et al. (2014) GMPE for the conditions:
    Style of faulting included - High Q (China/Turkey) - No basin term
    """
    GSIM_CLASS = bssa.BooreEtAl2014HighQ
    MEAN_FILE = dic("BSSA2014/BSSA_2014_HIGHQ_%sMEAN.csv")
    STD_FILE = dic("BSSA2014/BSSA_2014_HIGHQ_%sTOTAL_STD.csv")
    INTER_FILE = dic("BSSA2014/BSSA_2014_HIGHQ_%sINTER_STD.csv")
    INTRA_FILE = dic("BSSA2014/BSSA_2014_HIGHQ_%sINTRA_STD.csv")


class BooreEtAl2014LowQTestCase(BooreEtAl2014TestCase):
    """
    Tests the Boore et al. (2014) GMPE for the conditions:
    Style of faulting included - Low Q (Italy/Japan) - No basin term
    """
    GSIM_CLASS = bssa.BooreEtAl2014LowQ
    MEAN_FILE = dic("BSSA2014/BSSA_2014_LOWQ_%sMEAN.csv")
    STD_FILE = dic("BSSA2014/BSSA_2014_LOWQ_%sTOTAL_STD.csv")
    INTER_FILE = dic("BSSA2014/BSSA_2014_LOWQ_%sINTER_STD.csv")
    INTRA_FILE = dic("BSSA2014/BSSA_2014_LOWQ_%sINTRA_STD.csv")
