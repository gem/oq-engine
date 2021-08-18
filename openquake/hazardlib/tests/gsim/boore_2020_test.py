# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2019 GEM Foundation
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
Implements the set of tests for the Boore,et al 2020 GMPE
Test data are generated from the Fortran implementation provided by
Efthimios Sokos (June, 2021)
"""
import openquake.hazardlib.gsim.boore_2020 as bssa
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Discrepency percentages to be applied to all tests
MEAN_DISCREP = 2.0
STDDEV_DISCREP = 2.0


class BooreEtAl2020TestCase(BaseGSIMTestCase):
    """
    Tests the Boore et al. (2020) GMPE for the "global {default}" condition:
    Style of faulting included - No basin term
    """
    GSIM_CLASS = bssa.BooreEtAl2020
    MEAN_FILE = "BOORE20/Boore_2020_mean.csv"
    STD_FILE = "BOORE20/Boore_2020_total_std.csv"
    INTER_FILE = "BOORE20/Boore_2020_inter_std.csv"
    INTRA_FILE = "BOORE20/Boore_2020_intra_std.csv"

    def test_all(self):
        self.check(self.MEAN_FILE,
                   self.INTER_FILE,
                   self.INTRA_FILE,
                   max_discrep_percentage=MEAN_DISCREP,
                   std_discrep_percentage=STDDEV_DISCREP)
