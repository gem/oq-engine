# The Hazard Library
# Copyright (C) 2015-2023 GEM Foundation
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

from openquake.hazardlib.gsim.atkinson_2015 import (Atkinson2015,
                                                    Atkinson2015AltDistSat)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class Atkinson2015TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Atkinson2015

    # Tables generated from the implemtation by Jack Baker and Emily Mangold
    # from the Baker Research Group
    # https://github.com/bakerjw/GMMs/blob/master/gmms/a_2015_active.m

    def test_all(self):
        self.check('ATKINSON2015/ATKINSON2015_MEAN.csv',
                   'ATKINSON2015/ATKINSON2015_STD_INTRA.csv',
                   'ATKINSON2015/ATKINSON2015_STD_INTER.csv',
                   'ATKINSON2015/ATKINSON2015_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)
        
class Atkinson2015AltDistSatTestCase(BaseGSIMTestCase):
    GSIM_CLASS = Atkinson2015AltDistSat
    
    # Tables modified from those directly provided by Gail Atkinson on
    # https://www.inducedseismicity.ca/wp-content/uploads/2015/01/A15GMPErev2.xlsx
    # to use the published model (i.e. using the coefficients in Table 2 of
    # Atkinson, 2015) but with the alternative effective depth function
    # provided on page 984

    def test_alt(self):
        self.check('ATKINSON2015/A15_ALT_MEAN.csv',
                   'ATKINSON2015/A15_ALT_STD_INTRA.csv',
                   'ATKINSON2015/A15_ALT_STD_INTER.csv',
                   'ATKINSON2015/A15_ALT_STD_TOTAL.csv',
                   max_discrep_percentage=3.0)