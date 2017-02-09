# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
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

from openquake.hazardlib.gsim.berge_thierry_2003 import \
    BergeThierryEtAl2003SIGMA
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# test data generated from hazardlib implementation. Test data from
# original authors are needed for more robust testing


class BergeThierryEtAl2003SIGMATestCase(BaseGSIMTestCase):
    GSIM_CLASS = BergeThierryEtAl2003SIGMA

    def test_mean(self):
        self.check('B03/BergeThierryEtAl2003SIGMA_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('B03/BergeThierryEtAl2003SIGMA_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)
