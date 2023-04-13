# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2023 GEM Foundation
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

import os
from openquake.hazardlib.gsim.tem20.lin_2011 import Lin2011foot
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Test data provided by Jia-Cian Gao (TEM) on June 9, 2021 - Revised and
# updated by M. Pagani on July 16, 2021
# Values of std compared against the ones published.

BASE_PATH = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_PATH, '..', 'data', 'tem20')


class LinEtAl2011FootWallCase(BaseGSIMTestCase):
    GSIM_CLASS = Lin2011foot

    def test_all(self):
        self.check(os.path.join(DATA_PATH, 'lin2011_mean_fw.csv'),
                   os.path.join(DATA_PATH, 'lin2011_std_fw.csv'),
                   max_discrep_percentage=0.1)
