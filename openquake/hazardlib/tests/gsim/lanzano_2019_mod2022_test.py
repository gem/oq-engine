# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2020 GEM Foundation
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
#

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.gsim.lanzano_2019 import (
    LanzanoEtAl2019_RJB_OMO_RefRock)


class LanzanoEtAl2019_RJB_OMO_RefRock_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = LanzanoEtAl2019_RJB_OMO_RefRock

    # Tables provided by original authors
    MEAN_FILE = "LAN2019/ITA18_MOD22_RJB_MEAN.csv"
    STD_FILE = "LAN2019/ITA18_MOD22_RJB_STD.csv"

    def test_all(self):
        self.check(self.MEAN_FILE, self.STD_FILE, max_discrep_percentage=0.1)

class LanzanoEtAl2019_RJB_OMO_RefRock_kappa0_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = LanzanoEtAl2019_RJB_OMO_RefRock

    MEAN_FILE = "LAN2019/ITA18_MOD22_RJB_MEAN_kappa0.csv"
    STD_FILE = "LAN2019/ITA18_MOD22_RJB_STD_kappa0.csv"

    def test_kappa0_init(self):
        self.check(self.MEAN_FILE, self.STD_FILE, max_discrep_percentage=0.1,
                   kappa0=0.025)
