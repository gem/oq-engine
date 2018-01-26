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
Implements the tests for the GMPE of Bommer et al. (2009) for significant
duration

Test data generated from source code provided by Cecilia Nievas
"""
from openquake.hazardlib.gsim.bommer_2009 import BommerEtAl2009RSD

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Discrepency percentages to be applied to all tests
MEAN_DISCREP = 0.1
STDDEV_DISCREP = 0.1


class BommerEtAl2009RSDTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BommerEtAl2009RSD
    # File containing the results for the Mean
    MEAN_FILE = "bommer09/BOMMER_2009_RSD_MEAN.csv"
    # File contaning the results for the Total Standard Deviation
    STD_FILE = "bommer09/BOMMER_2009_RSD_TOTAL_STDDEV.csv"
    # File contaning the results for the Inter-Event Standard Deviation
    INTER_FILE = "bommer09/BOMMER_2009_RSD_INTER_EVENT_STDDEV.csv"
    # File contaning the results for the Intra-Event Standard Deviation
    INTRA_FILE = "bommer09/BOMMER_2009_RSD_INTRA_EVENT_STDDEV.csv"

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
