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

from openquake.hazardlib.gsim.yu_2013 import (YuEtAl2013Ms, YuEtAl2013MsTibet,
                                              YuEtAl2013MsEastern,
                                              YuEtAl2013MsStable)


from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class YuEtAl2013ActiveTestCase(BaseGSIMTestCase):
    GSIM_CLASS = YuEtAl2013Ms

    def test_mean(self):
        self.check('YU2013/yu_2013_mean_active.csv',
                   max_discrep_percentage=0.4)

    def test_std_total(self):
        self.check('YU2013/yu_2013_stddev_active.csv',
                   max_discrep_percentage=0.1)


class YuEtAl2013TibetTestCase(BaseGSIMTestCase):
    GSIM_CLASS = YuEtAl2013MsTibet

    def test_mean(self):
        self.check('YU2013/yu_2013_mean_tibetan.csv',
                   max_discrep_percentage=0.4)

    def test_std_total(self):
        self.check('YU2013/yu_2013_stddev_tibetan.csv',
                   max_discrep_percentage=0.1)


class YuEtAl2013EasternTestCase(BaseGSIMTestCase):
    GSIM_CLASS = YuEtAl2013MsEastern

    def test_mean(self):
        self.check('YU2013/yu_2013_mean_eastern.csv',
                   max_discrep_percentage=0.4)

    def test_std_total(self):
        self.check('YU2013/yu_2013_stddev_eastern.csv',
                   max_discrep_percentage=0.1)


class YuEtAl2013StableTestCase(BaseGSIMTestCase):
    GSIM_CLASS = YuEtAl2013MsStable

    def test_mean(self):
        self.check('YU2013/yu_2013_mean_stable.csv',
                   max_discrep_percentage=0.4)

    def test_std_total(self):
        self.check('YU2013/yu_2013_stddev_stable.csv',
                   max_discrep_percentage=0.1)
