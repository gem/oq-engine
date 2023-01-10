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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
from openquake.hazardlib.gsim.eshm20_craton import ESHM20Craton
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


MAX_DISCREP = 0.01


class ESHM20CratonTestCaseMean(BaseGSIMTestCase):
    GSIM_CLASS = ESHM20Craton

    def test_eman(self):
        self.check(
            "eshm20_craton/ESHM20_CRATON_MEAN_MEDIAN_MODEL.csv",
            "eshm20_craton/ESHM20_CRATON_TOTAL_STDDEV_NONERGODIC.csv",
            max_discrep_percentage=MAX_DISCREP,
            ergodic=False)


class ESHM20CratonTestCasePlus1Sigma(BaseGSIMTestCase):
    GSIM_CLASS = ESHM20Craton

    def test_mean(self):
        self.check(
            "eshm20_craton/ESHM20_CRATON_MEAN_PLUS1SIGMA_MODEL.csv",
            max_discrep_percentage=MAX_DISCREP,
            epsilon=1.0)


class ESHM20CratonErgodicTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ESHM20Craton

    def test_std_total(self):
        self.check(
            "eshm20_craton/ESHM20_CRATON_TOTAL_STDDEV_ERGODIC.csv",
            max_discrep_percentage=MAX_DISCREP,
            ergodic=True)
