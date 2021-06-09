# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2021 GEM Foundation
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
Implements the tests for the Ameri (2014) GMPE. Tests tables based on author's
original implementation
"""
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.gsim.ameri_2014 import Ameri2014Rjb


# Discrepancy percentages to be applied to all tests
MEAN_DISCREP = 0.01
STDDEV_DISCREP = 0.01


class Ameri2014TestCase(BaseGSIMTestCase):
    """
    Tests the Ameri (2014) GMPE for the case in which Joyner-Boore
    distance is the preferred distance metric, and standard deviation
    is provided using the homoskedastic formulation
    """
    GSIM_CLASS = Ameri2014Rjb
    # File containing the results for the Mean
    MEAN_FILE = "ameri14/Ameri_2014_mean.csv"
    # File contaning the results for the Total Standard Deviation
    STD_FILE = "ameri14/Ameri_2014_total_stddev.csv"
    # File contaning the results for the Inter-Event Standard Deviation
    INTER_FILE = "ameri14/Ameri_2014_inter_event_stddev.csv"
    # File contaning the results for the Intra-Event Standard Deviation
    INTRA_FILE = "ameri14/Ameri_2014_intra_event_stddev.csv"

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
