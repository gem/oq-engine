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

from openquake.hazardlib.gsim.dowrickrhoades_2005 import (
    DowrickRhoades2005Asc,
    DowrickRhoades2005SInter,
    DowrickRhoades2005SSlab,
    DowrickRhoades2005Volc)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Test data generated from MS Excel implementation from G. McVerry
# filename: NZSAallTmagwgtcorrected.xls (supplied 11 September 2014)


class DowrickRhoades2005AscTestCase(BaseGSIMTestCase):
    GSIM_CLASS = DowrickRhoades2005Asc

    def test_all(self):
        self.check('DOWRICKRHOADES2005/DowrickRhoades2005Asc.csv',
                   max_discrep_percentage=0.1)


class DowrickRhoades2005SInterTestCase(BaseGSIMTestCase):
    GSIM_CLASS = DowrickRhoades2005SInter

    def test_all(self):
        self.check('DOWRICKRHOADES2005/DowrickRhoades2005SInter.csv',
                   max_discrep_percentage=0.1)


class DowrickRhoades2005SSlabTestCase(BaseGSIMTestCase):
    GSIM_CLASS = DowrickRhoades2005SSlab

    def test_all(self):
        self.check('DOWRICKRHOADES2005/DowrickRhoades2005SSlab.csv',
                   max_discrep_percentage=0.1)


class DowrickRhoades2005VolcTestCase(BaseGSIMTestCase):
    GSIM_CLASS = DowrickRhoades2005Volc

    def test_all(self):
        self.check('DOWRICKRHOADES2005/DowrickRhoades2005Volc.csv',
                   max_discrep_percentage=0.1)
