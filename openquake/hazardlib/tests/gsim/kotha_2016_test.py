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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from openquake.hazardlib.gsim.kotha_2016 import (KothaEtAl2016Italy,
                                                 KothaEtAl2016Other,
                                                 KothaEtAl2016Turkey)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


MAX_DISCREP = 0.1


class KothaEtAl2016ItalyTestCase(BaseGSIMTestCase):
    """
    Test tables generated from spreadsheet provided by authors
    """
    GSIM_CLASS = KothaEtAl2016Italy

    def test_mean(self):
        self.check("kotha16/KOTHA16_ITALY_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP)

    def test_std_intra(self):
        self.check("kotha16/KOTHA16_INTRA_STDDEV.csv",
                   max_discrep_percentage=MAX_DISCREP)


    def test_std_inter(self):
        self.check("kotha16/KOTHA16_INTER_STDDEV.csv",
                   max_discrep_percentage=MAX_DISCREP)

    def test_std_total(self):
        self.check("kotha16/KOTHA16_TOTAL_STDDEV.csv",
                   max_discrep_percentage=MAX_DISCREP)


class KothaEtAl2016TurkeyTestCase(BaseGSIMTestCase):
    """
    Test tables generated from spreadsheet provided by authors
    """
    GSIM_CLASS = KothaEtAl2016Turkey

    def test_mean(self):
        self.check("kotha16/KOTHA16_TURKEY_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP)


class KothaEtAl2016OtherTestCase(BaseGSIMTestCase):
    """
    Test tables generated from spreadsheet provided by authors
    """
    GSIM_CLASS = KothaEtAl2016Other

    def test_mean(self):
        self.check("kotha16/KOTHA16_OTHER_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP)
