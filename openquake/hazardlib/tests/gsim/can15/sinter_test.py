#
# Copyright (C) 2014-2023 GEM Foundation
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

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.gsim.can15.sinter import SInterCan15Mid


class SinterCan15TestCase(BaseGSIMTestCase):
    GSIM_CLASS = SInterCan15Mid

    def test_mean_upp(self):
        self.check('CAN15/GMPEtInterface_high_combo.csv',
                       max_discrep_percentage=100., sgn=+1)

    def test_mean_low(self):
        self.check('CAN15/GMPEtInterface_Low_combo.csv',
                       max_discrep_percentage=900., sgn=-1)

    def test_mean(self):
        self.check('CAN15/GMPEtInterface_med_combo.csv',
                       max_discrep_percentage=200.)
