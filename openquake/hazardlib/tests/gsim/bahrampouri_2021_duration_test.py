# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2023 GEM Foundation
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

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.gsim.bahrampouri_2021_duration import (
    BahrampouriEtAldm2021Asc, BahrampouriEtAldm2021SInter,
    BahrampouriEtAldm2021SSlab)

# Discrepency percentages to be applied to all tests
MEAN_DISCREP = 0.1


class BahrampouriEtAl2021RSDTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BahrampouriEtAldm2021Asc
    # File containing the results for the Mean
    MEAN_FILE = "BMG20/BMG20_D_ASC_mean.csv"

    def test_all(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=MEAN_DISCREP)


class BahrampouriEtAl2021RSDInterTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BahrampouriEtAldm2021SInter
    # File containing the results for the Mean
    MEAN_FILE = "BMG20/BMG20_D_SInter_mean.csv"

    def test_all(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=MEAN_DISCREP)


class BahrampouriEtAl2021RSDSlabTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BahrampouriEtAldm2021SSlab
    # File containing the results for the Mean
    MEAN_FILE = "BMG20/BMG20_D_SSlab_mean.csv"

    def test_all(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=MEAN_DISCREP)
