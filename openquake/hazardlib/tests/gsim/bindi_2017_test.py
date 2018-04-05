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
Implements the tests for the set of GMPE classes included within the
GMPE of Bindi et al (2017)

Test data generated from source code provided by D. Bindi
"""
from openquake.hazardlib.gsim.bindi_2017 import (BindiEtAl2017Rjb,
                                                 BindiEtAl2017Rhypo)

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Discrepency percentages to be applied to all tests
MEAN_DISCREP = 0.1
STDDEV_DISCREP = 0.1


class BindiEtAl2017RjbTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BindiEtAl2017Rjb
    # File containing the results for the Mean
    MEAN_FILE = "bindi2017/BINDI_2017_RJB_MEAN.csv"
    # File contaning the results for the Total Standard Deviation
    STD_FILE = "bindi2017/BINDI_2017_RJB_TOTAL_STDDEV.csv"
    # File contaning the results for the Inter-Event Standard Deviation
    INTER_FILE = "bindi2017/BINDI_2017_RJB_INTER_EVENT_STDDEV.csv"
    # File contaning the results for the Intra-Event Standard Deviation
    INTRA_FILE = "bindi2017/BINDI_2017_RJB_INTRA_EVENT_STDDEV.csv"

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


class BindiEtAl2017RhypoTestCase(BindiEtAl2017RjbTestCase):
    GSIM_CLASS = BindiEtAl2017Rhypo
    # File containing the results for the Mean
    MEAN_FILE = "bindi2017/BINDI_2017_RHYPO_MEAN.csv"
    # File contaning the results for the Total Standard Deviation
    STD_FILE = "bindi2017/BINDI_2017_RHYPO_TOTAL_STDDEV.csv"
    # File contaning the results for the Inter-Event Standard Deviation
    INTER_FILE = "bindi2017/BINDI_2017_RHYPO_INTER_EVENT_STDDEV.csv"
    # File contaning the results for the Intra-Event Standard Deviation
    INTRA_FILE = "bindi2017/BINDI_2017_RHYPO_INTRA_EVENT_STDDEV.csv"
