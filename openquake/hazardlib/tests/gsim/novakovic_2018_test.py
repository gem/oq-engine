# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2022 GEM Foundation
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

from openquake.hazardlib.gsim.novakovic_2018 import (
    NovakovicEtAl2018)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Verification tables created using the .xls spreadsheet provided as an
# elctronic supplement to the BSSA paper


class NovakovicEtAl2018Test(BaseGSIMTestCase):
    GSIM_CLASS = NovakovicEtAl2018

    def test_mean(self):
        self.check('NEA18/NEA18_MEAN.csv', max_discrep_percentage=2.0)
