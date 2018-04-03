# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2018 GEM Foundation
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
Implements the tests for the GMPE of Afshari & Stewart (2016) for significant
duration

Test data generated from source code provided within the SCEC Broadband
platform
"""
from openquake.hazardlib.gsim.afshari_stewart_2016 import AfshariStewart2016,\
    AfshariStewart2016Japan
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Discrepency percentages to be applied to tests
# Small differences in coefficients from the SCEC BBP implementation in the
# style-of-faulting term lead to a tolerable discrepency at small magnitudes
MEAN_DISCREP = 3.0 
STDDEV_DISCREP = 0.1


class AfshariStewart2016TestCase(BaseGSIMTestCase):
    GSIM_CLASS = AfshariStewart2016
    # File containing the results for the Mean
    MEAN_FILE = "as16/AS16_RSD_MEAN.csv"
    # File contaning the results for the Total Standard Deviation
    STD_FILE = "as16/AS16_RSD_TOTAL_STDDEV.csv"
    # File contaning the results for the Inter-Event Standard Deviation
    INTER_FILE = "as16/AS16_RSD_INTER_EVENT_STDDEV.csv"
    # File contaning the results for the Intra-Event Standard Deviation
    INTRA_FILE = "as16/AS16_RSD_INTRA_EVENT_STDDEV.csv"

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


class AfshariStewart2016JapanTestCase(BaseGSIMTestCase):
    GSIM_CLASS = AfshariStewart2016Japan
    # File containing the results for the Mean
    MEAN_FILE = "as16/AS16_RSD_JAPAN_MEAN.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE,
                   max_discrep_percentage=MEAN_DISCREP)

