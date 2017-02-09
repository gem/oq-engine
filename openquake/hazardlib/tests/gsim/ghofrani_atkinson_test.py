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
Implements the set of tests for the Ghofrani & Atkinson (2014) Subduction
Interface GMPE

Test data are generated from tables supplied by Gail Atkinson
(2015, personal communication)
"""
from openquake.hazardlib.gsim.ghofrani_atkinson_2014 import (
    GhofraniAtkinson2014,
    GhofraniAtkinson2014Cascadia,
    GhofraniAtkinson2014Upper,
    GhofraniAtkinson2014Lower,
    GhofraniAtkinson2014CascadiaUpper,
    GhofraniAtkinson2014CascadiaLower)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


# Discrepency percentages to be applied to all tests
MEAN_DISCREP = 0.1
STDDEV_DISCREP = 0.1


class GhofraniAtkinson2014TestCase(BaseGSIMTestCase):
    """
    Implements the test case for the Ghorfrani & Atkinson (2014) GMPE for the
    default condition
    """
    GSIM_CLASS = GhofraniAtkinson2014

    # File for the mean results
    MEAN_FILE = "GA2014/GA2014_MEAN.csv"
    # File for the total standard deviation
    STD_FILE = "GA2014/GA2014_TOTAL.csv"
    # File for the inter-event standard deviation
    INTER_FILE = "GA2014/GA2014_INTER.csv"
    # File for the intra-event standard deviation
    INTRA_FILE = "GA2014/GA2014_INTRA.csv"

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


class GhofraniAtkinson2014CascadiaTestCase(GhofraniAtkinson2014TestCase):
    """
    Implements the test case for the Ghorfrani & Atkinson (2014) GMPE for with
    the adjustment for Cascadia
    """
    GSIM_CLASS = GhofraniAtkinson2014Cascadia
    MEAN_FILE = "GA2014/GA2014_CASCADIA_MEAN.csv"
    STD_FILE = "GA2014/GA2014_CASCADIA_TOTAL.csv"
    INTER_FILE = "GA2014/GA2014_CASCADIA_INTER.csv"
    INTRA_FILE = "GA2014/GA2014_CASCADIA_INTRA.csv"


class GhofraniAtkinson2014UpperTestCase(GhofraniAtkinson2014TestCase):
    """
    Implements the test case for the Ghorfrani & Atkinson (2014) GMPE for the
    "upper" epistemic uncertainty case
    """
    GSIM_CLASS = GhofraniAtkinson2014Upper
    MEAN_FILE = "GA2014/GA2014_UPPER_MEAN.csv"
    STD_FILE = "GA2014/GA2014_UPPER_TOTAL.csv"
    INTER_FILE = "GA2014/GA2014_UPPER_INTER.csv"
    INTRA_FILE = "GA2014/GA2014_UPPER_INTRA.csv"


class GhofraniAtkinson2014LowerTestCase(GhofraniAtkinson2014TestCase):
    """
    Implements the test case for the Ghorfrani & Atkinson (2014) GMPE for the
    "lower" epistemic uncertainty case
    """
    GSIM_CLASS = GhofraniAtkinson2014Lower
    MEAN_FILE = "GA2014/GA2014_LOWER_MEAN.csv"
    STD_FILE = "GA2014/GA2014_LOWER_TOTAL.csv"
    INTER_FILE = "GA2014/GA2014_LOWER_INTER.csv"
    INTRA_FILE = "GA2014/GA2014_LOWER_INTRA.csv"


class GhofraniAtkinson2014CascadiaUpperTestCase(GhofraniAtkinson2014TestCase):
    """
    Implements the test case for the Ghorfrani & Atkinson (2014) GMPE with the
    adjustment for Cascadia and the "upper" epistemic uncertainty case
    """
    GSIM_CLASS = GhofraniAtkinson2014CascadiaUpper
    MEAN_FILE = "GA2014/GA2014_CASCADIA_UPPER_MEAN.csv"
    STD_FILE = "GA2014/GA2014_CASCADIA_UPPER_TOTAL.csv"
    INTER_FILE = "GA2014/GA2014_CASCADIA_UPPER_INTER.csv"
    INTRA_FILE = "GA2014/GA2014_CASCADIA_UPPER_INTRA.csv"


class GhofraniAtkinson2014CascadiaLowerTestCase(GhofraniAtkinson2014TestCase):
    """
    Implements the test case for the Ghorfrani & Atkinson (2014) GMPE with the
    adjustment for Cascadia and the "lower" epistemic uncertainty case
    """
    GSIM_CLASS = GhofraniAtkinson2014CascadiaLower
    MEAN_FILE = "GA2014/GA2014_CASCADIA_LOWER_MEAN.csv"
    STD_FILE = "GA2014/GA2014_CASCADIA_LOWER_TOTAL.csv"
    INTER_FILE = "GA2014/GA2014_CASCADIA_LOWER_INTER.csv"
    INTRA_FILE = "GA2014/GA2014_CASCADIA_LOWER_INTRA.csv"
