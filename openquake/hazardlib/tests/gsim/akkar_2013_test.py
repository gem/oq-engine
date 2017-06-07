# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2017 GEM Foundation
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

from openquake.hazardlib.gsim.akkar_2013 import AkkarEtAl2013
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class AkkarEtAl2013TestCase(BaseGSIMTestCase):
    GSIM_CLASS = AkkarEtAl2013

    # Tables provided by original authors

    def test_mean(self):
        self.check('AKKAR13/AKKAR2013_MEAN.csv',
                    max_discrep_percentage=0.1)

    def test_std_intra(self):
        self.check('AKKAR13/AKKAR2013_STD_INTRA.csv',
                    max_discrep_percentage=0.1)

    def test_std_inter(self):
        self.check('AKKAR13/AKKAR2013_STD_INTER.csv',
                    max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('AKKAR13/AKKAR2013_STD_TOTAL.csv',
                    max_discrep_percentage=0.1)
