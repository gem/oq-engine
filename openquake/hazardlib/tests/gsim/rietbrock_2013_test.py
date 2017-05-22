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
Implements the test cases for the Rietbrock et al (2013) GMPE
Test data created using the Fortran implementation provided by
Ben Edwards
"""

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.gsim.rietbrock_2013 import (
    RietbrockEtAl2013SelfSimilar,
    RietbrockEtAl2013MagDependent)

# Discrepency percentages to be applied to all tests
# Mean value discrepency increased due to floating point
# mismatch at values very close to zero
MEAN_DISCREP = 0.5
STDDEV_DISCREP = 0.2


class RietbrockEtAl2013SelfSimilarTestCase(BaseGSIMTestCase):
    """
    Implements the test case the "self-similar" implementation"""
    GSIM_CLASS = RietbrockEtAl2013SelfSimilar

    # File containing the mean data
    MEAN_FILE = "RIET2013/REA2013_SelfSimilar_Mean.csv"
    # File containing the total standard deviation test data
    STD_FILE = "RIET2013/REA2013_SelfSimilar_TotalStddev.csv"

    # File containing the inter-event standard deviation test data
    INTER_FILE = "RIET2013/REA2013_SelfSimilar_InterStddev.csv"

    # File containing the inter-event standard deviation test data
    INTRA_FILE = "RIET2013/REA2013_SelfSimilar_IntraStddev.csv"

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


class RietbrockEtAl2013MagDependentTestCase(
        RietbrockEtAl2013SelfSimilarTestCase):
    """
    Implements the test case the "self-similar" implementation
    """
    GSIM_CLASS = RietbrockEtAl2013MagDependent

    # File containing the mean data
    MEAN_FILE = "RIET2013/REA2013_MagDependent_Mean.csv"
    # File containing the total standard deviation test data
    STD_FILE = "RIET2013/REA2013_MagDependent_TotalStddev.csv"

    # File containing the inter-event standard deviation test data
    INTER_FILE = "RIET2013/REA2013_MagDependent_InterStddev.csv"

    # File containing the inter-event standard deviation test data
    INTRA_FILE = "RIET2013/REA2013_MagDependent_IntraStddev.csv"
