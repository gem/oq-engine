# The Hazard Library
# Copyright (C) 2012 GEM Foundation
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
from openquake.hazardlib.gsim.tavakoli_pezeshk_2005 import \
    TavakoliPezeshk2005NSHMP2008

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class TavakoliPezeshk2005NSHMP20088TestCase(BaseGSIMTestCase):
    GSIM_CLASS = TavakoliPezeshk2005NSHMP2008

    def test_mean_normal(self):
        self.check('TP05/TP05usgs_MEAN.csv',
                   max_discrep_percentage=1.1)

    def test_std_total(self):
        self.check('TP05/TP05usgs_STD_TOT.csv',
                   max_discrep_percentage=0.5)
