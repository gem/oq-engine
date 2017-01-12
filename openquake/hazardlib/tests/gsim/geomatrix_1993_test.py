# The Hazard Library
# Copyright (C) 2014-2017 GEM Foundation
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
from openquake.hazardlib.gsim.geomatrix_1993 import Geomatrix1993SSlabNSHMP2008

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Test data generated from subroutine 'getGeom' in hazgridXnga2.f


class Geomatrix1993SSlabNSHMP2008TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Geomatrix1993SSlabNSHMP2008

    def test_mean(self):
        self.check('GEO93/GEO93NSHMP_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('GEO93/GEO93NSHMP_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)
