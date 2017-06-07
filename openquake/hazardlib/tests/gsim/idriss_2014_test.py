# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2017 GEM Foundation
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

from openquake.hazardlib.gsim.idriss_2014 import Idriss2014
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Test data generated using the Matlab implementation created by Yue Hua,
# Stanford University, available from
# http://web.stanford.edu/~bakerjw/GMPEs/I_2014_nga.m


class Idriss2014TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Idriss2014

    def test_mean(self):
        self.check("IDRISS14/IDRISS_2014_MEAN.csv",
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check("IDRISS14/IDRISS_2014_TOTAL_STD.csv",
                   max_discrep_percentage=0.1)
