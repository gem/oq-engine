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
Implements the tests for the set of GMPE classes included within the GMPE
of Ramadan et al (2023). Test tables were created by an excel spreadsheet
that calculates expected values provided by the original authors.
"""
from openquake.hazardlib.gsim.ramadan_2023 import (RamadanEtAl2023shallow, RamadanEtAl2023deep)

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Discrepancy percentages to be applied to all tests


class RamadanEtAl2023shallowTestCase(BaseGSIMTestCase):
    """
    Tests the Ramadan et al (2023) GMPE for the case of shallow events.
    """
    GSIM_CLASS = RamadanEtAl2023shallow
    # File containing the results for the Mean
    MEAN_FILE = "RLS23/RLS23shallow_MEAN.csv"
    # File contaning the results for the Total Standard Deviation
    STD_FILE = "RLS23/RLS23shallow_STD_TOTAL.csv"

    def test_all(self):
        self.check(self.MEAN_FILE, self.STD_FILE,
                   max_discrep_percentage=0.1)


class RamadanEtAl2023deepTestCase(BaseGSIMTestCase):
    """
    Tests the Ramadan et al (2023) GMPE for the case of deep events.
    """
    GSIM_CLASS = RamadanEtAl2023deep
    MEAN_FILE = "RLS23/RLS23deep_MEAN.csv"
    STD_FILE = "RLS23/RLS23deep_STD_TOTAL.csv"

    def test_all(self):
        self.check(self.MEAN_FILE, self.STD_FILE,
                   max_discrep_percentage=0.1)
