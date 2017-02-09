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
Implements the tests for the set of GMPE classes included within the
GMPE of Bindi et al (2014)
"""
from openquake.hazardlib.gsim.bindi_2014 import (BindiEtAl2014Rjb,
                                                 BindiEtAl2014RjbEC8,
                                                 BindiEtAl2014RjbEC8NoSOF,
                                                 BindiEtAl2014Rhyp,
                                                 BindiEtAl2014RhypEC8,
                                                 BindiEtAl2014RhypEC8NoSOF)

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Discrepency percentages to be applied to all tests
MEAN_DISCREP = 0.1
STDDEV_DISCREP = 0.1


class BindiEtAl2014RjbTestCase(BaseGSIMTestCase):
    """
    Tests the Bindi et al (2014) GMPE for the case in which Joyner-Boore
    distance is the preferred distance metric, style-of-faulting is required
    and site amplification uses a linear scaling model with Vs30
    """
    GSIM_CLASS = BindiEtAl2014Rjb
    # File containing the results for the Mean
    MEAN_FILE = "BINDI2014/B14_Rjb_Vs30_MEAN.csv"
    # File contaning the results for the Total Standard Deviation
    STD_FILE = "BINDI2014/B14_Rjb_Vs30_TOTAL_STD.csv"
    # File contaning the results for the Inter-Event Standard Deviation
    INTER_FILE = "BINDI2014/B14_Rjb_Vs30_INTER_STD.csv"
    # File contaning the results for the Intra-Event Standard Deviation
    INTRA_FILE = "BINDI2014/B14_Rjb_Vs30_INTRA_STD.csv"

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


class BindiEtAl2014RjbEC8TestCase(BindiEtAl2014RjbTestCase):
    """
    Tests the Bindi et al (2014) GMPE for the case in which Joyner-Boore
    distance is the preferred distance metric, style-of-faulting is NOT
    required and site amplification uses the Eurocode 8 classification
    """
    GSIM_CLASS = BindiEtAl2014RjbEC8
    MEAN_FILE = "BINDI2014/B14_Rjb_EC8_MEAN.csv"
    STD_FILE = "BINDI2014/B14_Rjb_EC8_TOTAL_STD.csv"
    INTER_FILE = "BINDI2014/B14_Rjb_EC8_INTER_STD.csv"
    INTRA_FILE = "BINDI2014/B14_Rjb_EC8_INTRA_STD.csv"


class BindiEtAl2014RjbEC8NoSOFTestCase(BindiEtAl2014RjbTestCase):
    """
    Tests the Bindi et al (2014) GMPE for the case in which Joyner-Boore
    distance is the preferred distance metric, style-of-faulting is required
    and site amplification uses the Eurocode 8 classification
    """
    GSIM_CLASS = BindiEtAl2014RjbEC8NoSOF
    MEAN_FILE = "BINDI2014/B14_Rjb_EC8_NoSOF_MEAN.csv"
    STD_FILE = "BINDI2014/B14_Rjb_EC8_NoSOF_TOTAL_STD.csv"
    INTER_FILE = "BINDI2014/B14_Rjb_EC8_NoSOF_INTER_STD.csv"
    INTRA_FILE = "BINDI2014/B14_Rjb_EC8_NoSOF_INTRA_STD.csv"


class BindiEtAl2014RhypTestCase(BindiEtAl2014RjbTestCase):
    """
    Tests the Bindi et al (2014) GMPE for the case in which hypocentral
    distance is the preferred distance metric, style-of-faulting is required
    and site amplification uses a linear scaling model with Vs30
    """
    GSIM_CLASS = BindiEtAl2014Rhyp
    MEAN_FILE = "BINDI2014/B14_Rhypo_Vs30_MEAN.csv"
    STD_FILE = "BINDI2014/B14_Rhypo_Vs30_TOTAL_STD.csv"
    INTER_FILE = "BINDI2014/B14_Rhypo_Vs30_INTER_STD.csv"
    INTRA_FILE = "BINDI2014/B14_Rhypo_Vs30_INTRA_STD.csv"


class BindiEtAl2014RhypEC8TestCase(BindiEtAl2014RjbTestCase):
    """
    Tests the Bindi et al (2014) GMPE for the case in which hypocentral
    distance is the preferred distance metric, style-of-faulting is required
    and site amplification uses the Eurocode 8 classification
    """
    GSIM_CLASS = BindiEtAl2014RhypEC8
    MEAN_FILE = "BINDI2014/B14_Rhypo_EC8_MEAN.csv"
    STD_FILE = "BINDI2014/B14_Rhypo_EC8_TOTAL_STD.csv"
    INTER_FILE = "BINDI2014/B14_Rhypo_EC8_INTER_STD.csv"
    INTRA_FILE = "BINDI2014/B14_Rhypo_EC8_INTRA_STD.csv"


class BindiEtAl2014RhypEC8NoSOFTestCase(BindiEtAl2014RjbTestCase):
    """
    Tests the Bindi et al (2014) GMPE for the case in which hypoccentral
    distance is the preferred distance metric, style-of-faulting is NOT
    required and site amplification uses the Eurocode 8 classification
    """
    GSIM_CLASS = BindiEtAl2014RhypEC8NoSOF
    MEAN_FILE = "BINDI2014/B14_Rhypo_EC8_NoSOF_MEAN.csv"
    STD_FILE = "BINDI2014/B14_Rhypo_EC8_NoSOF_TOTAL_STD.csv"
    INTER_FILE = "BINDI2014/B14_Rhypo_EC8_NoSOF_INTER_STD.csv"
    INTRA_FILE = "BINDI2014/B14_Rhypo_EC8_NoSOF_INTRA_STD.csv"
