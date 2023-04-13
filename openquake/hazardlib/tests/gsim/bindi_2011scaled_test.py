# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2023 GEM Foundation
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

#
#
#
# Test tables elaboratated from data provided directly from the authors.
#

from openquake.hazardlib.gsim.bindi_2011scaled import BindiEtAl2011scaled
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class BindiEtAl2011scaledTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BindiEtAl2011scaled

    # Tables provided by original authors

    def test_all(self):
        self.check('BINDI2011scaled/BINDI2011scaled_MEAN.csv',
                   'BINDI2011scaled/BINDI2011scaled_STD_INTER.csv',
                   'BINDI2011scaled/BINDI2011scaled_STD_INTRA.csv',
                   'BINDI2011scaled/BINDI2011scaled_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)
