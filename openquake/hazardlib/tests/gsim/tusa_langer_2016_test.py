# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2017 GEM Foundation
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
of Tusa and Langer (2016). Test tables were created by an excel spreadsheet
that calculates expected values provided by the original authors.
"""
from openquake.hazardlib.gsim.tusa_langer_2016 import (TusaLanger2016RepiBA08SE,
                                                       TusaLanger2016RepiBA08DE,
                                                       TusaLanger2016RepiSP87SE,
                                                       TusaLanger2016RepiSP87DE,
                                                       TusaLanger2016Rhypo)


from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Discrepancy percentages to be applied to all tests
MEAN_DISCREP = 0.1
STDDEV_DISCREP = 0.1


class TusaLanger2016RepiBA08SETestCase(BaseGSIMTestCase):
    """
    Tests the Tusa and Langer (2016) GMPE for the case in which the BA08
    functional form is used, taking epicentral distance considering SE.
    """
    GSIM_CLASS = TusaLanger2016RepiBA08SE
    # File containing the results for the Mean
    MEAN_FILE = "TL16/TusaLanger2016BA08SE_MEAN.csv"
    # File contaning the results for the Total Standard Deviation
    STD_FILE = "TL16/TusaLanger2016BA08SE_STD_TOTAL.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE,
                   max_discrep_percentage=MEAN_DISCREP)

    def test_std_total(self):
        self.check(self.STD_FILE,
                   max_discrep_percentage=STDDEV_DISCREP)


class TusaLanger2016RepiBA08DETestCase(TusaLanger2016RepiBA08SETestCase):
    """
    Tests the Tusa and Langer (2016) GMPE for the case in which the BA08
    functional form is used, taking epicentral distance considering DE
    """
    GSIM_CLASS = TusaLanger2016RepiBA08DE
    MEAN_FILE = "TL16/TusaLanger2016BA08DE_MEAN.csv"
    STD_FILE = "TL16/TusaLanger2016BA08DE_STD_TOTAL.csv"


class TusaLanger2016RepiSP87SETestCase(TusaLanger2016RepiBA08SETestCase):
    """
    Tests the Tusa and Langer (2016) GMPE for the case in which the SP87
    functional form is used, taking taking epicentral distance considering SE
    """
    GSIM_CLASS = TusaLanger2016RepiSP87SE
    MEAN_FILE = "TL16/TusaLanger2016SP87SE_MEAN.csv"
    STD_FILE = "TL16/TusaLanger2016SP87SE_STD_TOTAL.csv"


class TusaLanger2016RepiSP87DETestCase(TusaLanger2016RepiBA08SETestCase):
    """
    Tests the Tusa and Langer (2016) GMPE for the case in which the SP87
    functional form is used, taking taking epicentral distance considering DE
    """
    GSIM_CLASS = TusaLanger2016RepiSP87DE
    MEAN_FILE = "TL16/TusaLanger2016SP87DE_MEAN.csv"
    STD_FILE = "TL16/TusaLanger2016SP87DE_STD_TOTAL.csv"


class TusaLanger2016RhypoBA08TestCase(TusaLanger2016RepiBA08SETestCase):
    """
    Tests the Tusa and Langer (2016) GMPE for the case in which the BA08
    functional form is used, taking hypocentral distance
    """
    GSIM_CLASS = TusaLanger2016Rhypo
    MEAN_FILE = "TL16/TusaLanger2016Rhypo_MEAN.csv"
    STD_FILE = "TL16/TusaLanger2016Rhypo_STD_TOTAL.csv"
