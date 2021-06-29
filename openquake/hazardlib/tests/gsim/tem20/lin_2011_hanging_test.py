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

import os
from openquake.hazardlib.gsim.tem20.lin_2011_hanging import Lin2011hanging
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Test data provided by Jia-Cian Gao (TEM) on June 9, 2021

BASE_PATH = os.path.dirname(__file__)
BASE_PATH_DATA = os.path.join(BASE_PATH, '..', 'data', 'tem20')


class LinEtAl2011HanginwallCase(BaseGSIMTestCase):
    GSIM_CLASS = Lin2011hanging

    def test_mean(self):
        self.check(os.path.join(BASE_PATH_DATA, 'Lin2011_MEAN_hanging.csv'),
                   max_discrep_percentage=0.1)

    def test_total_std(self):
        self.check(os.path.join(BASE_PATH_DATA,
                                'Lin2011_TOTAL_STDDEV_hanging.csv'),
                   max_discrep_percentage=0.1)
