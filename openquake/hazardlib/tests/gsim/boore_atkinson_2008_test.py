# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2018 GEM Foundation
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

from openquake.hazardlib.gsim.boore_atkinson_2008 import (BooreAtkinson2008,
                                                          Atkinson2010Hawaii)

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class BooreAtkinson2008TestCase(BaseGSIMTestCase):
    GSIM_CLASS = BooreAtkinson2008

    # Test data were adapted from OpenSHA test tables.
    # Extra tables for inter and intra event standard deviations
    # were generated from the OpenSHA implementation.

    def test_mean_normal(self):
        self.check('NGA/BA08/BA08_MEDIAN_NM.csv',
                   max_discrep_percentage=0.6)

    def test_mean_reverse(self):
        self.check('NGA/BA08/BA08_MEDIAN_RV.csv',
                   max_discrep_percentage=0.6)

    def test_mean_strike_slip(self):
        self.check('NGA/BA08/BA08_MEDIAN_SS.csv',
                   max_discrep_percentage=0.6)

    def test_std_intra(self):
        self.check('NGA/BA08/BA08_STD_INTRA.csv',
                   max_discrep_percentage=0.1)

    def test_std_inter(self):
        self.check('NGA/BA08/BA08_STD_INTER.csv',
                   max_discrep_percentage=0.1)

    def test_std_total_strike_slip(self):
        self.check('NGA/BA08/BA08_SIGTM_SS.csv',
                   max_discrep_percentage=0.1)


class Atkinson2010HawaiiTestCase(BaseGSIMTestCase):
    GSIM_CLASS = Atkinson2010Hawaii

    # Test data were kindly provided by Gail Atkinson
    # (Note that it is here used a modified version of the table
    # to get rid of distances less than 1km)

    def test_mean(self):
        self.check('NGA/BA08/A10H_MEDIAN_1KM.csv',
                   max_discrep_percentage=0.6)

    def test_std_total(self):
        self.check('NGA/BA08/A10H_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)
