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
from openquake.hazardlib.gsim.macedo_2019 import MacedoEtAl2019SInter
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

REGIONS = 'Global', 'Japan', 'New Zealand', 'South America', 'Taiwan'


class MacedoEtAl2019SInterTestCase(BaseGSIMTestCase):
    GSIM_CLASS = MacedoEtAl2019SInter

    def test_all(self):
        for region in REGIONS:
            self.check(f'MACEDO2019/{region.replace(" ", "")}.csv',
                       max_discrep_percentage=0.2,
                       std_discrep_percentage=0.1,
                       region=region,
                       gmpe={'AbrahamsonEtAl2015SInter': {}})
