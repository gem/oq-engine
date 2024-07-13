# The Hazard Library
# Copyright (C) 2013-2023 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from openquake.hazardlib.gsim.ambraseys_2005 import (AmbraseysEtAl2005,
                                                   AmbraseysEtAl2005Vertical)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class AmbraseysEtAl2005TestCase(BaseGSIMTestCase):
    GSIM_CLASS = AmbraseysEtAl2005

    # Tables created using EZ-FRISK 

    def test_all(self):
        self.check('Am05/Am05_MEAN_ROCK_H.csv',
                   'Am05/Am05_MEAN_SOFT_H.csv',
                   'Am05/Am05_MEAN_STIF_H.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('Am05/Am05_STD_TOT_STIF_H.csv',
                   max_discrep_percentage=0.1)
        
class AmbraseysEtAl2005VerticalTestCase(BaseGSIMTestCase):
    GSIM_CLASS = AmbraseysEtAl2005Vertical

    # Tables created using EZ-FRISK 

    def test_all(self):
        self.check('Am05/Am05_MEAN_STIF_V.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('Am05/Am05_STD_TOT_STIF_V.csv',
                   max_discrep_percentage=0.1)