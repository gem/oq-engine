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

from openquake.hazardlib.gsim.ghasemi_2009 import (GhasemiEtAl2009)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class Ghasemi2009TestCase(BaseGSIMTestCase):
    GSIM_CLASS = GhasemiEtAl2009

    # Tables created from Ecxel calculation file of the proposed model 

    def test_all(self):
        self.check('Ghasemi09.csv',
                   max_discrep_percentage=0.1)

