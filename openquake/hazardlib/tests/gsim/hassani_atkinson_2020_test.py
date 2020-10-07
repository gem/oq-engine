# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2020 GEM Foundation
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

from openquake.hazardlib.gsim.hassani_atkinson_2020 import (
    HassaniAtkinson2020SInter, HassaniAtkinson2020SSlab,
    HassaniAtkinson2020Asc)

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Tests developed using MATLAB code received 7 September 2020.


class HassaniAtkinson2020SInterTestCase(BaseGSIMTestCase):
    GSIM_CLASS = HassaniAtkinson2020SInter

    def test_mean(self):
        self.check('HA20/HassaniAtkinson2020SInter_MEAN.csv',
                   max_discrep_percentage=0.1)
