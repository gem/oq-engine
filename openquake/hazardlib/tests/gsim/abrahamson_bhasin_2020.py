# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# 
# Copyright (C) 2025, GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
from openquake.hazardlib.gsim.abrahamson_bhasin_2020 import (
    AbrahamsonBhasin2020,
    AbrahamsonBhasin2020PGA,
    AbrahamsonBhasin2020SA1
    )
    
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class AbrahamsonBhasin2020TestCase(BaseGSIMTestCase):
    GSIM_CLASS = AbrahamsonBhasin2020

    def test_all(self):
        self.check('AB2020/General.csv',
                   max_discrep_percentage=0.2,
                   gmpe={'Lin2009': {}})
