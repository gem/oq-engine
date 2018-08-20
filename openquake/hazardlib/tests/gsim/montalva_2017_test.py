# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2018 GEM Foundation
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

from openquake.hazardlib.gsim.montalva_2017 import (
    MontalvaEtAl2017SInter,
    MontalvaEtAl2017SSlab)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class MontalvaEtAl2017SInterTestCase(BaseGSIMTestCase):
    """
    Tests the Montalva et al. (2017) GMPE for subduction
    interface earthquakes
    """
    GSIM_CLASS = MontalvaEtAl2017SInter
    MEAN_FILE = "mont17/MONTALVA_SINTER_MEAN.csv"
    TOTAL_FILE = "mont17/MONTALVA_SINTER_TOTAL.csv"
    INTER_FILE = "mont17/MONTALVA_SINTER_INTER_EVENT.csv"
    INTRA_FILE = "mont17/MONTALVA_SINTER_INTRA_EVENT.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE,
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check(self.TOTAL_FILE,
                   max_discrep_percentage=0.1)

    def test_std_inter(self):
        self.check(self.INTER_FILE,
                   max_discrep_percentage=0.1)

    def test_std_intra(self):
        self.check(self.INTRA_FILE,
                   max_discrep_percentage=0.1)


class MontalvaEtAl2017SSlabTestCase(MontalvaEtAl2017SInterTestCase):
    """
    Tests the Montalva et al. (2017) GMPE for subduction inslab earthquakes
    """
    GSIM_CLASS = MontalvaEtAl2017SSlab
    MEAN_FILE = "mont17/MONTALVA_SSLAB_MEAN.csv"
    TOTAL_FILE = "mont17/MONTALVA_SSLAB_TOTAL.csv"
    INTER_FILE = "mont17/MONTALVA_SSLAB_INTER_EVENT.csv"
    INTRA_FILE = "mont17/MONTALVA_SSLAB_INTRA_EVENT.csv"
