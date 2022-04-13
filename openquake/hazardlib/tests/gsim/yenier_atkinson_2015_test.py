# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2021 GEM Foundation
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

import numpy as np
from openquake.hazardlib.gsim.yenier_atkinson_2015 import (
    YenierAtkinson2015BSSA)
from openquake.hazardlib.imt import PGA
from openquake.hazardlib.contexts import get_mean_stds
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class YenierAtkinson2015BSSA(BaseGSIMTestCase):

    GSIM_CLASS = YenierAtkinson2015BSSA

    def test_mean(self):
        # no error if truncation_level=0
        self.check('YA15/ya15_mean_cena.csv', max_discrep_percentage=0.3,
                   truncation_level=0)

    def test_error(self):
        dt = [('hypo_depth', '<f8'), ('mag', '<f8'), ('vs30', '<f8'),
              ('rrup', '<f8'), ('sids', '<u4')]
        ctx = np.array(
            [(10., 4., 760., 1.00, 0),
             (10., 4., 760., 1.26, 1)], dt).view(np.recarray)
        gsim = self.GSIM_CLASS()

        with self.assertRaises(ValueError):  # Total StdDev is zero
            get_mean_stds(gsim, ctx, [PGA()], truncation_level=3)
