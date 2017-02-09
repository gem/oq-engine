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
Implements the set of tests for the Douglas et al (2013) stochastic GMPE
Test data are generated from the Fortran implementation provided by
J. Douglas (February, 2014)
"""
import openquake.hazardlib.gsim.douglas_stochastic_2013 as dst
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


# Discrepency percentages to be applied to all tests
MEAN_DISCREP = 0.01
STDDEV_DISCREP = 0.01

#/////////////////////////////////////////////////////////////////////////////
##############################################################################
#                    Stress Drop = 10 bar
##############################################################################
#/////////////////////////////////////////////////////////////////////////////

################################# Q = 200 ####################################


class Douglas2013TestCaseSD001Q200K005(BaseGSIMTestCase):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 001  Q = 200  K = 0.005

    Due to the large number
    of GMPEs the test files for the corresponding GMPE are now added as
    attributes of the class. Subsequent GMPEs will be testing by inheriting
    this class and modifying the GSIM_CLASS and corresponding files
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD001Q200K005

    # File containing the results for the mean
    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD001Q0200K005.csv'

    # File containing the results for the total standard deviation
    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD001Q0200K005.csv'

    # File containing the results for the inter-event standard deviation
    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD001Q0200K005.csv'

    # File containing the results for the inter-event standard deviation
    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD001Q0200K005.csv'

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


class Douglas2013TestCaseSD001Q200K020(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 001  Q = 200  K = 0.020
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD001Q200K020

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD001Q0200K020.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD001Q0200K020.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD001Q0200K020.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD001Q0200K020.csv'


class Douglas2013TestCaseSD001Q200K040(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 001  Q = 200  K = 0.040
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD001Q200K040

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD001Q0200K040.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD001Q0200K040.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD001Q0200K040.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD001Q0200K040.csv'


class Douglas2013TestCaseSD001Q200K060(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 001  Q = 200  K = 0.060
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD001Q200K060

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD001Q0200K060.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD001Q0200K060.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD001Q0200K060.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD001Q0200K060.csv'


################################# Q = 600 ####################################
class Douglas2013TestCaseSD001Q600K005(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 001  Q = 600  K = 0.005
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD001Q600K005

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD001Q0600K005.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD001Q0600K005.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD001Q0600K005.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD001Q0600K005.csv'


class Douglas2013TestCaseSD001Q600K020(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 001  Q = 600  K = 0.020
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD001Q600K020

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD001Q0600K020.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD001Q0600K020.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD001Q0600K020.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD001Q0600K020.csv'


class Douglas2013TestCaseSD001Q600K040(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 001  Q = 600  K = 0.040
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD001Q600K040

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD001Q0600K040.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD001Q0600K040.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD001Q0600K040.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD001Q0600K040.csv'


class Douglas2013TestCaseSD001Q600K060(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 001  Q = 600  K = 0.060
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD001Q600K060

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD001Q0600K060.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD001Q0600K060.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD001Q0600K060.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD001Q0600K060.csv'


############################### Q = 1800  ###################################
class Douglas2013TestCaseSD001Q1800K005(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 001  Q = 1800  K = 0.005
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD001Q1800K005

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD001Q1800K005.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD001Q1800K005.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD001Q1800K005.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD001Q1800K005.csv'


class Douglas2013TestCaseSD001Q1800K020(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 001  Q = 1800  K = 0.020
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD001Q1800K020

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD001Q1800K020.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD001Q1800K020.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD001Q1800K020.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD001Q1800K020.csv'


class Douglas2013TestCaseSD001Q1800K040(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 001  Q = 1800  K = 0.040
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD001Q1800K040

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD001Q1800K040.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD001Q1800K040.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD001Q1800K040.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD001Q1800K040.csv'


class Douglas2013TestCaseSD001Q1800K060(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 001  Q = 1800  K = 0.060
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD001Q1800K060

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD001Q1800K060.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD001Q1800K060.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD001Q1800K060.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD001Q1800K060.csv'

#/////////////////////////////////////////////////////////////////////////////
##############################################################################
#                           Stress Drop = 10 bar
##############################################################################
#/////////////////////////////////////////////////////////////////////////////

################################# Q = 200 ####################################


class Douglas2013TestCaseSD0101Q200K005(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 010  Q = 200  K = 0.005
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD010Q200K005

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD010Q0200K005.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD010Q0200K005.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD010Q0200K005.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD010Q0200K005.csv'


class Douglas2013TestCaseSD010Q200K020(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 010  Q = 200  K = 0.020
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD010Q200K020

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD010Q0200K020.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD010Q0200K020.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD010Q0200K020.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD010Q0200K020.csv'


class Douglas2013TestCaseSD010Q200K040(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 010  Q = 200  K = 0.040
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD010Q200K040

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD010Q0200K040.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD010Q0200K040.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD010Q0200K040.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD010Q0200K040.csv'


class Douglas2013TestCaseSD010Q200K060(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 010  Q = 200  K = 0.060
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD010Q200K060

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD010Q0200K060.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD010Q0200K060.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD010Q0200K060.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD010Q0200K060.csv'


################################# Q = 600 ####################################
class Douglas2013TestCaseSD010Q600K005(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 010  Q = 600  K = 0.005
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD010Q600K005

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD010Q0600K005.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD010Q0600K005.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD010Q0600K005.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD010Q0600K005.csv'


class Douglas2013TestCaseSD010Q600K020(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 010  Q = 600  K = 0.020
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD010Q600K020

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD010Q0600K020.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD010Q0600K020.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD010Q0600K020.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD010Q0600K020.csv'


class Douglas2013TestCaseSD010Q600K040(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 010  Q = 600  K = 0.040
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD010Q600K040

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD010Q0600K040.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD010Q0600K040.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD010Q0600K040.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD010Q0600K040.csv'


class Douglas2013TestCaseSD010Q600K060(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 010  Q = 600  K = 0.060
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD010Q600K060

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD010Q0600K060.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD010Q0600K060.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD010Q0600K060.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD010Q0600K060.csv'


############################### Q = 1800  ###################################
class Douglas2013TestCaseSD010Q1800K005(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 010  Q = 1800  K = 0.005
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD010Q1800K005

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD010Q1800K005.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD010Q1800K005.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD010Q1800K005.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD010Q1800K005.csv'


class Douglas2013TestCaseSD010Q1800K020(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 010  Q = 1800  K = 0.020
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD010Q1800K020

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD010Q1800K020.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD010Q1800K020.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD010Q1800K020.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD010Q1800K020.csv'


class Douglas2013TestCaseSD010Q1800K040(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 010  Q = 1800  K = 0.040
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD010Q1800K040

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD010Q1800K040.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD010Q1800K040.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD010Q1800K040.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD010Q1800K040.csv'


class Douglas2013TestCaseSD010Q1800K060(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 010  Q = 1800  K = 0.060
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD010Q1800K060

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD010Q1800K060.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD010Q1800K060.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD010Q1800K060.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD010Q1800K060.csv'

#/////////////////////////////////////////////////////////////////////////////
##############################################################################
#                           Stress Drop = 100 bar
##############################################################################
#/////////////////////////////////////////////////////////////////////////////

################################# Q = 200 ####################################


class Douglas2013TestCaseSD1001Q200K005(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 100  Q = 200  K = 0.005
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD100Q200K005

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD100Q0200K005.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD100Q0200K005.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD100Q0200K005.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD100Q0200K005.csv'


class Douglas2013TestCaseSD100Q200K020(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 100  Q = 200  K = 0.020
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD100Q200K020

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD100Q0200K020.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD100Q0200K020.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD100Q0200K020.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD100Q0200K020.csv'


class Douglas2013TestCaseSD100Q200K040(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 100  Q = 200  K = 0.040
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD100Q200K040

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD100Q0200K040.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD100Q0200K040.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD100Q0200K040.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD100Q0200K040.csv'


class Douglas2013TestCaseSD100Q200K060(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 100  Q = 200  K = 0.060
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD100Q200K060

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD100Q0200K060.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD100Q0200K060.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD100Q0200K060.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD100Q0200K060.csv'


################################# Q = 600 ####################################
class Douglas2013TestCaseSD100Q600K005(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 100  Q = 600  K = 0.005
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD100Q600K005

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD100Q0600K005.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD100Q0600K005.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD100Q0600K005.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD100Q0600K005.csv'


class Douglas2013TestCaseSD100Q600K020(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 100  Q = 600  K = 0.020
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD100Q600K020

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD100Q0600K020.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD100Q0600K020.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD100Q0600K020.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD100Q0600K020.csv'


class Douglas2013TestCaseSD100Q600K040(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 100  Q = 600  K = 0.040
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD100Q600K040

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD100Q0600K040.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD100Q0600K040.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD100Q0600K040.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD100Q0600K040.csv'


class Douglas2013TestCaseSD100Q600K060(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 100  Q = 600  K = 0.060
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD100Q600K060

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD100Q0600K060.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD100Q0600K060.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD100Q0600K060.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD100Q0600K060.csv'


############################### Q = 1800  ###################################
class Douglas2013TestCaseSD100Q1800K005(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 100  Q = 1800  K = 0.005
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD100Q1800K005

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD100Q1800K005.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD100Q1800K005.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD100Q1800K005.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD100Q1800K005.csv'


class Douglas2013TestCaseSD100Q1800K020(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 100  Q = 1800  K = 0.020
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD100Q1800K020

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD100Q1800K020.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD100Q1800K020.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD100Q1800K020.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD100Q1800K020.csv'


class Douglas2013TestCaseSD100Q1800K040(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 100  Q = 1800  K = 0.040
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD100Q1800K040

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD100Q1800K040.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD100Q1800K040.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD100Q1800K040.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD100Q1800K040.csv'


class Douglas2013TestCaseSD100Q1800K060(Douglas2013TestCaseSD001Q200K005):
    """
    Tests the Douglas et al (2013) stochastic GMPE.
    SD = 100  Q = 1800  K = 0.060
    """
    GSIM_CLASS = dst.DouglasEtAl2013StochasticSD100Q1800K060

    MEAN_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_MEAN_SD100Q1800K060.csv'

    STD_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_STD_SD100Q1800K060.csv'

    INTER_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTER_SD100Q1800K060.csv'

    INTRA_FILE = 'DOUG2013/DOUGLAS_2013_STOCHASTIC_INTRA_SD100Q1800K060.csv'
