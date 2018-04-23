# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2018 GEM Foundation
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

from openquake.hazardlib.gsim.munson_thurber_1997 import MunsonThurber1997

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class MunsonThurber1997TestCase(BaseGSIMTestCase):
    GSIM_CLASS = MunsonThurber1997

    # Test data were taken from Table 5 of Munson and Thurber (1997)
    # (some decimals are added manually, due to lack of precision)
    # Standard deviation is a fixed value

    def test_mean(self):
        self.check('MT97/MT97_MEAN.csv', max_discrep_percentage=0.6)

    def test_std_total(self):
        self.check('MT97/MT97_STD_TOTAL.csv', max_discrep_percentage=0.1)
