# The Hazard Library
# Copyright (C) 2013-2017 GEM Foundation
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from openquake.hazardlib.gsim.hong_goda_2007 import HongGoda2007
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


MAX_DISCREP = 0.1


class HongGoda2007TestCase(BaseGSIMTestCase):
    """
    Test tables generated from implementation (circular). Verified against
    images in paper
    """
    GSIM_CLASS = HongGoda2007

    def test_mean(self):
        self.check("hg2007/HONG_GODA_2007_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP)

    def test_std_intra(self):
        self.check("hg2007/HONG_GODA_2007_INTRA_STDDEV.csv",
                   max_discrep_percentage=MAX_DISCREP)

    def test_std_inter(self):
        self.check("hg2007/HONG_GODA_2007_INTER_STDDEV.csv",
                   max_discrep_percentage=MAX_DISCREP)

    def test_std_total(self):
        self.check("hg2007/HONG_GODA_2007_TOTAL_STDDEV.csv",
                   max_discrep_percentage=MAX_DISCREP)
