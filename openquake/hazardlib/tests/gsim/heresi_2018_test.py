# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
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

import openquake.hazardlib.gsim.heresi_2018 as hdm
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


# Discrepency percentages to be applied to all tests
MEAN_DISCREP = 0.1
STDDEV_DISCREP = 0.1


class HeresiEtAl2018TestCase(BaseGSIMTestCase):
    """
    Tests the Heresi et al. (2018) GMPE
    """
    GSIM_CLASS = hdm.HeresiEtAl2018

	# Tables created from Matlab code from the original authors

    # File containing results for the mean
    MEAN_FILE = "HDM2018/HDM_2018_MEAN.csv"
    # File containing results for the total standard deviation
    STD_FILE = "HDM2018/HDM_2018_TOTAL_STDDEV.csv"
    # File containing results for the inter-event standard deviation
    INTER_FILE = "HDM2018/HDM_2018_INTER_EVENT_STDDEV.csv"
    # File containing results for the intra-event standard deviation
    INTRA_FILE = "HDM2018/HDM_2018_INTRA_EVENT_STDDEV.csv"

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


