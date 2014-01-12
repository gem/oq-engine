# The Hazard Library
# Copyright (C) 2014 GEM Foundation
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

from openquake.hazardlib.gsim.boore_atkinson_2011 import BooreAtkinson2011
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class BooreAtkinson2011TestCase(BaseGSIMTestCase):
    GSIM_CLASS = BooreAtkinson2011

    # Test data created using the code available on the website of
    # D. Boore - http://daveboore.com/ (checked on 2014.01.08)
    # Code name: nga08_gm_tmr.for

    def test_mean_normal(self):
        self.check('BA11/BA11_MEDIAN.csv',
                   max_discrep_percentage=0.8)
