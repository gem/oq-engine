# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2019 GEM Foundation
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

from openquake.hazardlib.gsim.skarlatoudis_2013 import (
    SkarlatoudisEtAlSSlab2013)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class SkarlatoudisEtAlSSlab2013TestCase(BaseGSIMTestCase):
    """
    Tests the Skarlatoudis et al. (2013) model for subduction
    intraslab earthquakes
    """
    GSIM_CLASS = SkarlatoudisEtAlSSlab2013
    MEAN_FILE = "SKARL13/SKARL13_SSLAB_CENTRAL_MEAN.csv"
    TOTAL_FILE = "SKARL13/SKARL13_SSLAB_CENTRAL_STDDEV_TOTAL.csv"
    INTER_FILE = "SKARL13/SKARL13_SSLAB_CENTRAL_STDDEV_INTER.csv"
    INTRA_FILE = "SKARL13/SKARL13_SSLAB_CENTRAL_STDDEV_INTRA.csv"

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
