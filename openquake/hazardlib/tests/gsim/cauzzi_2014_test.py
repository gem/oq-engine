# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
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
Implements the test cases for the Cauzzi et al. (2014) GMPE
Test data taken from the Matlab implementation provided as a supplement
to the original manuscript
"""

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.gsim.cauzzi_2014 import (
    CauzziEtAl2014,
    CauzziEtAl2014NoSOF,
    CauzziEtAl2014FixedVs30,
    CauzziEtAl2014FixedVs30NoSOF,
    CauzziEtAl2014Eurocode8,
    CauzziEtAl2014Eurocode8NoSOF)

# Discrepency percentages to be applied to all tests
MEAN_DISCREP = 0.1
STDDEV_DISCREP = 0.1


class CauzziEtAl2014TestCase(BaseGSIMTestCase):
    """
    Implements the test case for the class with required style of faulting
    and period-dependent reference Vs30
    """
    GSIM_CLASS = CauzziEtAl2014

    # File containing the mean data
    MEAN_FILE = "C14/CAUZZI_MEAN.csv"
    # File containing the total standard deviation test data
    STD_FILE = "C14/CAUZZI_TOTAL_STD.csv"

    # File containing the inter-event standard deviation test data
    INTER_FILE = "C14/CAUZZI_INTER_STD.csv"

    # File containing the inter-event standard deviation test data
    INTRA_FILE = "C14/CAUZZI_INTRA_STD.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE,
                   max_discrep_percentage=MEAN_DISCREP)

    def test_std_total(self):
        self.check(self.STD_FILE,
                   max_discrep_percentage=STDDEV_DISCREP)

    def test_std_inter(self):
        self.check(self.INTER_FILE,
                   max_discrep_percentage=STDDEV_DISCREP)

    def test_std_intra(self):
        self.check(self.INTRA_FILE,
                   max_discrep_percentage=STDDEV_DISCREP)


class CauzziEtAl2014NoSOFTestCase(CauzziEtAl2014TestCase):
    """
    Implements the test case for the class with unspecified style of faulting
    and period-dependent reference Vs30
    """
    GSIM_CLASS = CauzziEtAl2014NoSOF
    MEAN_FILE = "C14/CAUZZI_NoSOF_MEAN.csv"
    STD_FILE = "C14/CAUZZI_NoSOF_TOTAL_STD.csv"
    INTER_FILE = "C14/CAUZZI_NoSOF_INTER_STD.csv"
    INTRA_FILE = "C14/CAUZZI_NoSOF_INTRA_STD.csv"


class CauzziEtAl2014FixedVs30TestCase(CauzziEtAl2014TestCase):
    """
    Implements the test case for the class with required style of faulting
    and fixed reference Vs30
    """
    GSIM_CLASS = CauzziEtAl2014FixedVs30
    MEAN_FILE = "C14/CAUZZI_FIXEDVS_MEAN.csv"
    STD_FILE = "C14/CAUZZI_FIXEDVS_TOTAL_STD.csv"
    INTER_FILE = "C14/CAUZZI_FIXEDVS_INTER_STD.csv"
    INTRA_FILE = "C14/CAUZZI_FIXEDVS_INTRA_STD.csv"


class CauzziEtAl2014FixedVs30NoSOFTestCase(CauzziEtAl2014TestCase):
    """
    Implements the test case for the class with unspecified style of faulting
    and fixed reference Vs30
    """
    GSIM_CLASS = CauzziEtAl2014FixedVs30NoSOF
    MEAN_FILE = "C14/CAUZZI_NoSOF_FIXEDVS_MEAN.csv"
    STD_FILE = "C14/CAUZZI_NoSOF_FIXEDVS_TOTAL_STD.csv"
    INTER_FILE = "C14/CAUZZI_NoSOF_FIXEDVS_INTER_STD.csv"
    INTRA_FILE = "C14/CAUZZI_NoSOF_FIXEDVS_INTRA_STD.csv"


class CauzziEtAl2014Eurocode8(CauzziEtAl2014TestCase):
    """
    Implements the test case for the class with required style of faulting
    and Eurocode 8 site classification
    """
    GSIM_CLASS = CauzziEtAl2014Eurocode8
    MEAN_FILE = "C14/CAUZZI_EC8_MEAN.csv"
    STD_FILE = "C14/CAUZZI_EC8_TOTAL_STD.csv"
    INTER_FILE = "C14/CAUZZI_EC8_INTER_STD.csv"
    INTRA_FILE = "C14/CAUZZI_EC8_INTRA_STD.csv"


class CauzziEtAl2014Eurocode8NoSOF(CauzziEtAl2014TestCase):
    """
    Implements the test case for the class with unspecified style of faulting
    and Eurocode 8 site classification
    """
    GSIM_CLASS = CauzziEtAl2014Eurocode8NoSOF
    MEAN_FILE = "C14/CAUZZI_NoSOF_EC8_MEAN.csv"
    STD_FILE = "C14/CAUZZI_NoSOF_EC8_TOTAL_STD.csv"
    INTER_FILE = "C14/CAUZZI_NoSOF_EC8_INTER_STD.csv"
    INTRA_FILE = "C14/CAUZZI_NoSOF_EC8_INTRA_STD.csv"
