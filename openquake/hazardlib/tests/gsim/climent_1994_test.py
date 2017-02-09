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

from openquake.hazardlib.gsim.climent_1994 import (
    ClimentEtAl1994
    )
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class ClimentEtAl1994TestCase(BaseGSIMTestCase):
    GSIM_CLASS = ClimentEtAl1994

    # All test data were generated using the Crisis/EXCEL tables provided by
    # Alvaro Climent.
    # The tables have been modified according to the oq-engine test format

    def test_mean_normal(self):
        self.check('CLI1994/CLI94_MEAN.csv',
                   max_discrep_percentage=0.015)

    def test_std_total(self):
        self.check('CLI1994/CLI94_TOTAL.csv',
                   max_discrep_percentage=0.010)
