# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2017 GEM Foundation
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

from openquake.hazardlib.gsim.atkinson_macias_2009 import AtkinsonMacias2009
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class AtkinsonMacias2009TestCase(BaseGSIMTestCase):
    GSIM_CLASS = AtkinsonMacias2009

    # Verification tables provided by G. M. Atkinson
    
    def test_mean(self):
        # Some minor discrepancies tests do not pass at 0.5 % or lower
        self.check('AM09/ATKINSON_MACIAS_2009_MEAN.csv',
                   max_discrep_percentage=0.6)

    def test_std_total(self):
        self.check('AM09/ATKINSON_MACIAS_2009_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)
