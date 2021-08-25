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


class BooreEtAl2020TestCase(BaseGSIMTestCase):
    """
    Tests the Boore et al. (2020) GMPE for the "global {default}" condition:
    Style of faulting included - No basin term
    """
    GSIM_CLASS = bssa.BooreEtAl2020

    def test_all(self):
        self.check("BOORE20/BooreEtAl2020.csv", max_discrep_percentage=2.)
