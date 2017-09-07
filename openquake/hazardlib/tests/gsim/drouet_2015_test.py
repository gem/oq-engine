# The Hazard Library
# Copyright (C) 2015-2017 GEM Foundation
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
from openquake.hazardlib.gsim.drouet_2015_brazil import (
    DrouetBrazil2015,
    DrouetBrazil2015withDepth
    )
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

class DrouetEtAl2015TestCase(BaseGSIMTestCase):
    """
    Tests the implementation of the Drouet (2015) GMPE without hypocentral
    depth. Data from OpenQuake implementation by Stephane Drouet, 2015
    """
    GSIM_CLASS = DrouetBrazil2015
    MEAN_FILE = "drouet_2015/DROUET2015_MEAN.csv"
    TOTAL_FILE = "drouet_2015/DROUET2015_TOTAL.csv"
    INTER_FILE = "drouet_2015/DROUET2015_INTER_EVENT.csv"
    INTRA_FILE = "drouet_2015/DROUET2015_INTRA_EVENT.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE,
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check(self.TOTAL_FILE,
                   max_discrep_percentage=0.1)

    def test_std_inter(self):
        self.check(self.INTER_FILE,
                   max_discrep_percentage=0.1)

    def test_std_intra(self):
        self.check(self.INTRA_FILE,
                   max_discrep_percentage=0.1)

class DrouetEtAl2015withDepthTestCase(DrouetEtAl2015TestCase):
    """
    Tests the implementation of the Drouet (2015) GMPE including hypocentral
    depth. Data from OpenQuake implementation by Stephane Drouet, 2015
    """
    GSIM_CLASS = DrouetBrazil2015withDepth
    MEAN_FILE = "drouet_2015/DROUET2015_DEPTH_MEAN.csv"
    TOTAL_FILE = "drouet_2015/DROUET2015_DEPTH_TOTAL.csv"
    INTER_FILE = "drouet_2015/DROUET2015_DEPTH_INTER_EVENT.csv"
    INTRA_FILE = "drouet_2015/DROUET2015_DEPTH_INTRA_EVENT.csv"
