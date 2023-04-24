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

from openquake.hazardlib.gsim.hassani_atkinson_2018 import (
    HassaniAtkinson2018)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Verification tables created using the .xls spreadsheet provided as an
# electronic supplement to the BSSA paper


class HassaniAtkinson2018Test(BaseGSIMTestCase):
    GSIM_CLASS = HassaniAtkinson2018

    def test_mean(self):
        self.check('HA18/HA18_MEAN_K_0pt03s_Ds_20bar.csv',
                   max_discrep_percentage=0.1, kappa0=0.03, d_sigma=20)
