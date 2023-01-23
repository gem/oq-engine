# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2023 GEM Foundation
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
Implements the tests for the set of GMPE classes included within the GMPE
of Tusa, Langer and Azzaro (2019). Test tables were created by an excel spreadsheet
that calculates expected values provided by the original authors.
"""
from openquake.hazardlib.gsim.tusa_langer_azzaro_2019 import (TusaLangerAzzaro2019_100b,
                                                       TusaLangerAzzaro2019_60b)


from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Discrepancy percentages to be applied to all tests
MEAN_DISCREP = 0.1
STDDEV_DISCREP = 0.1


class TusaLangerAzzaro2019_100bTestCase(BaseGSIMTestCase):
    """
    Tests the Tusa, Langer and Azzaro (2019) GMPE for shallow events and hypocentral 
    distance less than 100 km (TLA_100b).
    """
    GSIM_CLASS = TusaLangerAzzaro2019_100b
    # File containing the results for the Mean
    MEAN_FILE = "TLA19/TusaLangerAzzaro2019_100b_MEAN.csv"
    # File contaning the results for the Total Standard Deviation
    STD_FILE = "TLA19/TusaLangerAzzaro2019_100b_STD_TOTAL.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE,
                   max_discrep_percentage=MEAN_DISCREP)

    def test_std_total(self):
        self.check(self.STD_FILE,
                   max_discrep_percentage=STDDEV_DISCREP)


class TusaLangerAzzaro2019_60bTestCase(TusaLangerAzzaro2019_100bTestCase):
    """
    Tests the Tusa, Langer and Azzaro (2019) GMPE for shallow events and hypocentral 
    distance less than 60 km (TLA_60b).
    """
    GSIM_CLASS = TusaLangerAzzaro2019_60b
    MEAN_FILE = "TLA19/TusaLangerAzzaro2019_60b_MEAN.csv"
    STD_FILE = "TLA19/TusaLangerAzzaro2019_60b_STD_TOTAL.csv"

