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


class BooreEtAl2014TestCase(BaseGSIMTestCase):
    """
    Tests the Boore et al. (2014) GMPE for the "global {default}" condition:
    Style of faulting included - "Global" Q model - No basin term
    """
    GSIM_CLASS = bssa.BooreEtAl2014

    # File containing results for the mean
    MEAN_FILE = "BSSA2014/BSSA_2014_MEAN.csv"
    # File containing results for the total standard deviation
    STD_FILE = "BSSA2014/BSSA_2014_TOTAL_STD.csv"
    # File containing results for the inter-event standard deviation
    INTER_FILE = "BSSA2014/BSSA_2014_INTER_STD.csv"
    # File containing results for the intra-event standard deviation
    INTRA_FILE = "BSSA2014/BSSA_2014_INTRA_STD.csv"

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


class BooreEtAl2014HighQTestCase(BooreEtAl2014TestCase):
    """
    Tests the Boore et al. (2014) GMPE for the conditions:
    Style of faulting included - High Q (China/Turkey) - No basin term
    """
    GSIM_CLASS = bssa.BooreEtAl2014HighQ

    # File containing results for the mean
    MEAN_FILE = "BSSA2014/BSSA_2014_HIGHQ_MEAN.csv"
    # File containing results for the total standard deviation
    STD_FILE = "BSSA2014/BSSA_2014_HIGHQ_TOTAL_STD.csv"
    # File containing results for the inter-event standard deviation
    INTER_FILE = "BSSA2014/BSSA_2014_HIGHQ_INTER_STD.csv"
    # File containing results for the intra-event standard deviation
    INTRA_FILE = "BSSA2014/BSSA_2014_HIGHQ_INTRA_STD.csv"


class BooreEtAl2014LowQTestCase(BooreEtAl2014TestCase):
    """
    Tests the Boore et al. (2014) GMPE for the conditions:
    Style of faulting included - Low Q (Italy/Japan) - No basin term
    """
    GSIM_CLASS = bssa.BooreEtAl2014LowQ

    # File containing results for the mean
    MEAN_FILE = "BSSA2014/BSSA_2014_LOWQ_MEAN.csv"
    # File containing results for the total standard deviation
    STD_FILE = "BSSA2014/BSSA_2014_LOWQ_TOTAL_STD.csv"
    # File containing results for the inter-event standard deviation
    INTER_FILE = "BSSA2014/BSSA_2014_LOWQ_INTER_STD.csv"
    # File containing results for the intra-event standard deviation
    INTRA_FILE = "BSSA2014/BSSA_2014_HIGHQ_INTRA_STD.csv"


class BooreEtAl2014CaliforniaBasinTestCase(BooreEtAl2014TestCase):
    """
    Tests the Boore et al. (2014) GMPE for the conditions:
    Style of faulting included - "Global" Q model - California basin term
    """
    GSIM_CLASS = bssa.BooreEtAl2014CaliforniaBasin

    # File containing results for the mean
    MEAN_FILE = "BSSA2014/BSSA_2014_CALIFORNIA_MEAN.csv"
    # File containing results for the total standard deviation
    STD_FILE = "BSSA2014/BSSA_2014_CALIFORNIA_TOTAL_STD.csv"
    # File containing results for the inter-event standard deviation
    INTER_FILE = "BSSA2014/BSSA_2014_CALIFORNIA_INTER_STD.csv"
    # File containing results for the intra-event standard deviation
    INTRA_FILE = "BSSA2014/BSSA_2014_CALIFORNIA_INTRA_STD.csv"


class BooreEtAl2014HighQCaliforniaBasinTestCase(BooreEtAl2014TestCase):
    """
    Tests the Boore et al. (2014) GMPE for the conditions:
    Style of faulting included - High Q model - California basin term
    """
    GSIM_CLASS = bssa.BooreEtAl2014HighQCaliforniaBasin

    # File containing results for the mean
    MEAN_FILE = "BSSA2014/BSSA_2014_HIGHQ_CALIFORNIA_MEAN.csv"
    # File containing results for the total standard deviation
    STD_FILE = "BSSA2014/BSSA_2014_HIGHQ_CALIFORNIA_TOTAL_STD.csv"
    # File containing results for the inter-event standard deviation
    INTER_FILE = "BSSA2014/BSSA_2014_HIGHQ_CALIFORNIA_INTER_STD.csv"
    # File containing results for the intra-event standard deviation
    INTRA_FILE = "BSSA2014/BSSA_2014_HIGHQ_CALIFORNIA_INTRA_STD.csv"


class BooreEtAl2014LowQCaliforniaBasinTestCase(BooreEtAl2014TestCase):
    """
    Tests the Boore et al. (2014) GMPE for the conditions:
    Style of faulting included - Low Q model - California basin term
    """
    GSIM_CLASS = bssa.BooreEtAl2014LowQCaliforniaBasin

    # File containing results for the mean
    MEAN_FILE = "BSSA2014/BSSA_2014_LOWQ_CALIFORNIA_MEAN.csv"
    # File containing results for the total standard deviation
    STD_FILE = "BSSA2014/BSSA_2014_LOWQ_CALIFORNIA_TOTAL_STD.csv"
    # File containing results for the inter-event standard deviation
    INTER_FILE = "BSSA2014/BSSA_2014_LOWQ_CALIFORNIA_INTER_STD.csv"
    # File containing results for the intra-event standard deviation
    INTRA_FILE = "BSSA2014/BSSA_2014_LOWQ_CALIFORNIA_INTRA_STD.csv"


class BooreEtAl2014JapanBasinTestCase(BooreEtAl2014TestCase):
    """
    Tests the Boore et al. (2014) GMPE for the conditions:
    Style of faulting included - "Global" Q model - Japan basin term
    """
    GSIM_CLASS = bssa.BooreEtAl2014JapanBasin

    # File containing results for the mean
    MEAN_FILE = "BSSA2014/BSSA_2014_JAPAN_MEAN.csv"
    # File containing results for the total standard deviation
    STD_FILE = "BSSA2014/BSSA_2014_JAPAN_TOTAL_STD.csv"
    # File containing results for the inter-event standard deviation
    INTER_FILE = "BSSA2014/BSSA_2014_JAPAN_INTER_STD.csv"
    # File containing results for the intra-event standard deviation
    INTRA_FILE = "BSSA2014/BSSA_2014_JAPAN_INTRA_STD.csv"


class BooreEtAl2014HighQJapanBasinTestCase(BooreEtAl2014TestCase):
    """
    Tests the Boore et al. (2014) GMPE for the conditions:
    Style of faulting included - High Q model - Japan basin term
    """
    GSIM_CLASS = bssa.BooreEtAl2014HighQJapanBasin

    # File containing results for the mean
    MEAN_FILE = "BSSA2014/BSSA_2014_HIGHQ_JAPAN_MEAN.csv"
    # File containing results for the total standard deviation
    STD_FILE = "BSSA2014/BSSA_2014_HIGHQ_JAPAN_TOTAL_STD.csv"
    # File containing results for the inter-event standard deviation
    INTER_FILE = "BSSA2014/BSSA_2014_HIGHQ_JAPAN_INTER_STD.csv"
    # File containing results for the intra-event standard deviation
    INTRA_FILE = "BSSA2014/BSSA_2014_HIGHQ_JAPAN_INTRA_STD.csv"


class BooreEtAl2014LowQJapanBasinTestCase(BooreEtAl2014TestCase):
    """
    Tests the Boore et al. (2014) GMPE for the conditions:
    Style of faulting included - Low Q model - Japan basin term
    """
    GSIM_CLASS = bssa.BooreEtAl2014LowQJapanBasin

    # File containing results for the mean
    MEAN_FILE = "BSSA2014/BSSA_2014_LOWQ_JAPAN_MEAN.csv"
    # File containing results for the total standard deviation
    STD_FILE = "BSSA2014/BSSA_2014_LOWQ_JAPAN_TOTAL_STD.csv"
    # File containing results for the inter-event standard deviation
    INTER_FILE = "BSSA2014/BSSA_2014_LOWQ_JAPAN_INTER_STD.csv"
    # File containing results for the intra-event standard deviation
    INTRA_FILE = "BSSA2014/BSSA_2014_LOWQ_JAPAN_INTRA_STD.csv"

#//////////////////////////////////////////////////////////////////////////
#---------------------- Excluding Style-of-faulting-----------------------
#//////////////////////////////////////////////////////////////////////////


class BooreEtAl2014NoSOFTestCase(BooreEtAl2014TestCase):
    """
    Tests the Boore et al. (2014) GMPE for the conditions:
    No style of faulting - "Global" Q model - No basin term
    """
    GSIM_CLASS = bssa.BooreEtAl2014NoSOF

    # File containing results for the mean
    MEAN_FILE = "BSSA2014/BSSA_2014_NOSOF_MEAN.csv"
    # File containing results for the total standard deviation
    STD_FILE = "BSSA2014/BSSA_2014_NOSOF_TOTAL_STD.csv"
    # File containing results for the inter-event standard deviation
    INTER_FILE = "BSSA2014/BSSA_2014_NOSOF_INTER_STD.csv"
    # File containing results for the intra-event standard deviation
    INTRA_FILE = "BSSA2014/BSSA_2014_NOSOF_INTRA_STD.csv"


class BooreEtAl2014NoSOFHighQTestCase(BooreEtAl2014TestCase):
    """
    Tests the Boore et al. (2014) GMPE for the conditions:
    No style of faulting - High Q model - No basin term
    """
    GSIM_CLASS = bssa.BooreEtAl2014HighQNoSOF

    # File containing results for the mean
    MEAN_FILE = "BSSA2014/BSSA_2014_HIGHQ_NOSOF_MEAN.csv"
    # File containing results for the total standard deviation
    STD_FILE = "BSSA2014/BSSA_2014_HIGHQ_NOSOF_TOTAL_STD.csv"
    # File containing results for the inter-event standard deviation
    INTER_FILE = "BSSA2014/BSSA_2014_HIGHQ_NOSOF_INTER_STD.csv"
    # File containing results for the intra-event standard deviation
    INTRA_FILE = "BSSA2014/BSSA_2014_HIGHQ_NOSOF_INTRA_STD.csv"


class BooreEtAl2014NoSOFLowQTestCase(BooreEtAl2014TestCase):
    """
    Tests the Boore et al. (2014) GMPE for the conditions:
    No style of faulting - Low Q model - No basin term
    """
    GSIM_CLASS = bssa.BooreEtAl2014LowQNoSOF

    # File containing results for the mean
    MEAN_FILE = "BSSA2014/BSSA_2014_LOWQ_NOSOF_MEAN.csv"
    # File containing results for the total standard deviation
    STD_FILE = "BSSA2014/BSSA_2014_LOWQ_NOSOF_TOTAL_STD.csv"
    # File containing results for the inter-event standard deviation
    INTER_FILE = "BSSA2014/BSSA_2014_LOWQ_NOSOF_INTER_STD.csv"
    # File containing results for the intra-event standard deviation
    INTRA_FILE = "BSSA2014/BSSA_2014_LOWQ_NOSOF_INTRA_STD.csv"


class BooreEtAl2014CaliforniaBasinNoSOFTestCase(BooreEtAl2014TestCase):
    """
    Tests the Boore et al. (2014) GMPE for the conditions:
    No style of faulting - "Global" Q model - California basin term
    """
    GSIM_CLASS = bssa.BooreEtAl2014CaliforniaBasinNoSOF

    # File containing results for the mean
    MEAN_FILE = "BSSA2014/BSSA_2014_CALIFORNIA_NOSOF_MEAN.csv"
    # File containing results for the total standard deviation
    STD_FILE = "BSSA2014/BSSA_2014_CALIFORNIA_NOSOF_TOTAL_STD.csv"
    # File containing results for the inter-event standard deviation
    INTER_FILE = "BSSA2014/BSSA_2014_CALIFORNIA_NOSOF_INTER_STD.csv"
    # File containing results for the intra-event standard deviation
    INTRA_FILE = "BSSA2014/BSSA_2014_CALIFORNIA_NOSOF_INTRA_STD.csv"


class BooreEtAl2014HighQCaliforniaBasinNoSOFTestCase(BooreEtAl2014TestCase):
    """
    Tests the Boore et al. (2014) GMPE for the conditions:
    No style of faulting - High Q model - California basin term
    """
    GSIM_CLASS = bssa.BooreEtAl2014HighQCaliforniaBasinNoSOF

    # File containing results for the mean
    MEAN_FILE = "BSSA2014/BSSA_2014_HIGHQ_CALIFORNIA_NOSOF_MEAN.csv"
    # File containing results for the total standard deviation
    STD_FILE = "BSSA2014/BSSA_2014_HIGHQ_CALIFORNIA_NOSOF_TOTAL_STD.csv"
    # File containing results for the inter-event standard deviation
    INTER_FILE = "BSSA2014/BSSA_2014_HIGHQ_CALIFORNIA_NOSOF_INTER_STD.csv"
    # File containing results for the intra-event standard deviation
    INTRA_FILE = "BSSA2014/BSSA_2014_HIGHQ_CALIFORNIA_NOSOF_INTRA_STD.csv"


class BooreEtAl2014LowQCaliforniaBasinNoSOFTestCase(BooreEtAl2014TestCase):
    """
    Tests the Boore et al. (2014) GMPE for the conditions:
    No style of faulting - Low Q model - California basin term
    """
    GSIM_CLASS = bssa.BooreEtAl2014LowQCaliforniaBasinNoSOF

    # File containing results for the mean
    MEAN_FILE = "BSSA2014/BSSA_2014_LOWQ_CALIFORNIA_NOSOF_MEAN.csv"
    # File containing results for the total standard deviation
    STD_FILE = "BSSA2014/BSSA_2014_LOWQ_CALIFORNIA_NOSOF_TOTAL_STD.csv"
    # File containing results for the inter-event standard deviation
    INTER_FILE = "BSSA2014/BSSA_2014_LOWQ_CALIFORNIA_NOSOF_INTER_STD.csv"
    # File containing results for the intra-event standard deviation
    INTRA_FILE = "BSSA2014/BSSA_2014_LOWQ_CALIFORNIA_NOSOF_INTRA_STD.csv"


class BooreEtAl2014JapanBasinNoSOFTestCase(BooreEtAl2014TestCase):
    """
    Tests the Boore et al. (2014) GMPE for the conditions:
    No style of faulting - "Global" Q model - Japan basin term
    """
    GSIM_CLASS = bssa.BooreEtAl2014JapanBasinNoSOF

    # File containing results for the mean
    MEAN_FILE = "BSSA2014/BSSA_2014_JAPAN_NOSOF_MEAN.csv"
    # File containing results for the total standard deviation
    STD_FILE = "BSSA2014/BSSA_2014_JAPAN_NOSOF_TOTAL_STD.csv"
    # File containing results for the inter-event standard deviation
    INTER_FILE = "BSSA2014/BSSA_2014_JAPAN_NOSOF_INTER_STD.csv"
    # File containing results for the intra-event standard deviation
    INTRA_FILE = "BSSA2014/BSSA_2014_JAPAN_NOSOF_INTRA_STD.csv"


class BooreEtAl2014HighQJapanBasinNoSOFTestCase(BooreEtAl2014TestCase):
    """
    Tests the Boore et al. (2014) GMPE for the conditions:
    No style of faulting - High Q model - Japan basin term
    """
    GSIM_CLASS = bssa.BooreEtAl2014HighQJapanBasinNoSOF

    # File containing results for the mean
    MEAN_FILE = "BSSA2014/BSSA_2014_HIGHQ_JAPAN_NOSOF_MEAN.csv"
    # File containing results for the total standard deviation
    STD_FILE = "BSSA2014/BSSA_2014_HIGHQ_JAPAN_NOSOF_TOTAL_STD.csv"
    # File containing results for the inter-event standard deviation
    INTER_FILE = "BSSA2014/BSSA_2014_HIGHQ_JAPAN_NOSOF_INTER_STD.csv"
    # File containing results for the intra-event standard deviation
    INTRA_FILE = "BSSA2014/BSSA_2014_HIGHQ_JAPAN_NOSOF_INTRA_STD.csv"


class BooreEtAl2014LowQJapanBasinNoSOFTestCase(BooreEtAl2014TestCase):
    """
    Tests the Boore et al. (2014) GMPE for the conditions:
    No style of faulting - Low Q model - Japan basin term
    """
    GSIM_CLASS = bssa.BooreEtAl2014LowQJapanBasinNoSOF

    # File containing results for the mean
    MEAN_FILE = "BSSA2014/BSSA_2014_LOWQ_JAPAN_NOSOF_MEAN.csv"
    # File containing results for the total standard deviation
    STD_FILE = "BSSA2014/BSSA_2014_LOWQ_JAPAN_NOSOF_TOTAL_STD.csv"
    # File containing results for the inter-event standard deviation
    INTER_FILE = "BSSA2014/BSSA_2014_LOWQ_JAPAN_NOSOF_INTER_STD.csv"
    # File containing results for the intra-event standard deviation
    INTRA_FILE = "BSSA2014/BSSA_2014_LOWQ_JAPAN_NOSOF_INTRA_STD.csv"
