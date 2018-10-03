#
# Copyright (C) 2014-2018 GEM Foundation
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
from openquake.hazardlib.gsim.can15.eastern import (EasternCan15Mid,
                                                    EasternCan15Upp,
                                                    EasternCan15Low)


class EasternCan15LowTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EasternCan15Low

    def test_mean(self):
        self.check('CAN15/GMPEt_ENA_low.csv',
                   max_discrep_percentage=170.)


class EasternCan15HighTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EasternCan15Upp

    def test_mean(self):
        self.check('CAN15/GMPEt_ENA_high.csv',
                   max_discrep_percentage=170.)


class EasternCan15MidTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EasternCan15Mid

    def test_mean(self):
        self.check('CAN15/GMPEt_ENA_med.csv',
                   max_discrep_percentage=100.)
