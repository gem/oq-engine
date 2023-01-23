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
Implements the tests for the set of GMPE classes included within the
GMPE of Ameri et al (2017)
"""
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
import pathlib
from openquake.hazardlib import gsim
import numpy as np
import unittest


data = pathlib.Path(__file__).parent / 'data'

# Discrepancy percentages to be applied to all tests
MEAN_DISCREP = 0.1
STDDEV_DISCREP = 0.1
# Translated precision, in number of decimals:
MEAN_DECIMAL = np.abs(np.round(np.log10(MEAN_DISCREP*0.01)))
STDDEV_DECIMAL = np.abs(np.round(np.log10(STDDEV_DISCREP*0.01)))


class AmeriEtAl2017RjbTestCase(BaseGSIMTestCase):
    """
    Tests the Ameri et al (2017) GMPE for the case in which Joyner-Boore
    distance is the preferred distance metric, and standard deviation
    is provided using the heteroscedastic formulation
    """
    GSIM_CLASS = gsim.ameri_2017.AmeriEtAl2017Rjb
    # File containing the results for the Mean
    MEAN_FILE = "AMERI2017/A17_Rjb_Heteroscedastic_MEAN.csv"
    # File contaning the results for the Total Standard Deviation
    STD_FILE = "AMERI2017/A17_Rjb_Heteroscedastic_TOTAL_STDDEV.csv"
    # File contaning the results for the Inter-Event Standard Deviation
    INTER_FILE = "AMERI2017/A17_Rjb_Heteroscedastic_INTER_EVENT_STDDEV.csv"
    # File contaning the results for the Intra-Event Standard Deviation
    INTRA_FILE = "AMERI2017/A17_Rjb_Heteroscedastic_INTRA_EVENT_STDDEV.csv"

    def test_all(self):
        self.check(self.MEAN_FILE,
                   self.STD_FILE,
                   self.INTER_FILE,
                   self.INTRA_FILE,
                   max_discrep_percentage=MEAN_DISCREP,
                   std_discrep_percentage=STDDEV_DISCREP)


class AmeriEtAl2017RepiTestCase(AmeriEtAl2017RjbTestCase):
    """
    Tests the Ameri et al (2017) GMPE for the case in which epicentral
    distance is the preferred distance metric, and standard deviation
    is provided using the heteroscedastic formulation
    """
    GSIM_CLASS = gsim.ameri_2017.AmeriEtAl2017Repi
    MEAN_FILE = "AMERI2017/A17_Repi_Heteroscedastic_MEAN.csv"
    STD_FILE = "AMERI2017/A17_Repi_Heteroscedastic_TOTAL_STDDEV.csv"
    INTER_FILE = "AMERI2017/A17_Repi_Heteroscedastic_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "AMERI2017/A17_Repi_Heteroscedastic_INTRA_EVENT_STDDEV.csv"


# Discrepancy percentages to be applied to all tests
MEAN_DISCREP = 0.01
STDDEV_DISCREP = 0.01


class AmeriEtAl2017RjbStressDropTestCase(BaseGSIMTestCase):
    """
    Tests the Ameri et al (2017) GMPE for the case in which Joyner-Boore
    distance is the preferred distance metric, and standard deviation
    is provided using the homoscedastic formulation
    """
    GSIM_CLASS = gsim.ameri_2017.AmeriEtAl2017RjbStressDrop

    def test_all(self):
        self.check("AmeriEtAl2017RjbStressDrop.csv",
                   max_discrep_percentage=MEAN_DISCREP,
                   std_discrep_percentage=STDDEV_DISCREP)


class AmeriEtAl2017RepiStressDropTestCase(BaseGSIMTestCase):
    """
    Tests the Ameri et al (2017) GMPE for the case in which epicentral
    distance is the preferred distance metric, and standard deviation
    is provided using the homoscedastic formulation
    """
    GSIM_CLASS = gsim.ameri_2017.AmeriEtAl2017RepiStressDrop

    def test_all(self):
        self.check("AmeriEtAl2017RepiStressDrop.csv",
                   max_discrep_percentage=MEAN_DISCREP,
                   std_discrep_percentage=STDDEV_DISCREP)


class Ameri2014TestCase(AmeriEtAl2017RjbTestCase):
    """
    Tests the Ameri (2014) GMPE for the case in which Joyner-Boore
    distance is the preferred distance metric, and standard deviation
    is provided using the homoskedastic formulation
    """
    GSIM_CLASS = gsim.ameri_2017.Ameri2014Rjb
    # File containing the results for the Mean
    MEAN_FILE = "ameri14/Ameri_2014_mean.csv"
    # File contaning the results for the Total Standard Deviation
    STD_FILE = "ameri14/Ameri_2014_total_stddev.csv"
    # File contaning the results for the Inter-Event Standard Deviation
    INTER_FILE = "ameri14/Ameri_2014_inter_event_stddev.csv"
    # File contaning the results for the Intra-Event Standard Deviation
    INTRA_FILE = "ameri14/Ameri_2014_intra_event_stddev.csv"
