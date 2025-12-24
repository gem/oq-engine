# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2021 GEM Foundation
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
Implements the tests for the set of GMM classes included within the GMM
of Scala and co-authors (2025). Test tables were created by an excel spreadsheet
that calculates expected values provided by the original authors.
"""
from openquake.hazardlib.gsim.scala_2025 import (Scala2025CampiFlegrei_repi,
                                                Scala2025CampiFlegrei_rhypo)

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Discrepancy percentages to be applied to all tests


class Scala2025CampiFlegrei_repiTestCase(BaseGSIMTestCase):
    """
    Tests the Scala 2025 GMM using Mw and Repi as covariates.
    """
    GSIM_CLASS = Scala2025CampiFlegrei_repi
    # File containing the results for the Mean
    MEAN_FILE = "SCALA25/Scala2025repi_MEAN.csv"
    # File contaning the results for the Total Standard Deviation
    STD_FILE = "SCALA25/Scala2025repi_STD_TOTAL.csv"

    def test_all(self):
        self.check(self.MEAN_FILE, self.STD_FILE,
                   max_discrep_percentage=0.1)


class Scala2025CampiFlegrei_rhypoTestCase(BaseGSIMTestCase):
    """
    Tests the Scala 2025 GMM using Mw and Rhypo as covariates.
    """
    GSIM_CLASS = Scala2025CampiFlegrei_rhypo
    MEAN_FILE = "SCALA25/Scala2025rhypo_MEAN.csv"
    STD_FILE = "SCALA25/Scala2025rhypo_STD_TOTAL.csv"

    def test_all(self):
        self.check(self.MEAN_FILE, self.STD_FILE,
                   max_discrep_percentage=0.1)
