# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2021 GEM Foundation
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

from openquake.hazardlib.gsim.gulerce_abrahamson_2011 import \
                        GulerceAbrahamson2011, GulerceAbrahamson2011Vert

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

class GulreceAbrahamson2011TestCase(BaseGSIMTestCase):
    """
    Tests the GMPE for the mean V/H ratios.
    Mean value data obtained by digitizing Figures 7 to 10 using
    https://apps.automeris.io/wpd/ .

    PGA1100 for Figures 7 and 8 are assumed.
    """
    GSIM_CLASS = GulerceAbrahamson2011

    def test_mean_Fig_7_8(self):
        self.check('GA11/GA11_Fig_7_8_MEAN.csv',
                   max_discrep_percentage=4.)
    def test_mean_Fig_9_10(self):
        self.check('GA11/GA11_Fig_9_10_MEAN.csv',
                   max_discrep_percentage=0.5)

class GulreceAbrahamson2011VertTestCase(BaseGSIMTestCase):
    """
    Tests the GMPE applied to horizontal models. Data derived from respective
    horizontal model tests.
    """
    GSIM_CLASS = GulerceAbrahamson2011Vert

    def test_mean_GA11_AS08(self):
        self.check('GA11/GA11_AS08_MEAN.csv',
                   max_discrep_percentage=0.1,
                   gmpe_name='AbrahamsonSilva2008')
    def test_mean_GA11_BA08(self):
        self.check('GA11/GA11_BA08_MEDIAN_SS.csv',
                   max_discrep_percentage=0.6,
                   gmpe_name='BooreAtkinson2008')
