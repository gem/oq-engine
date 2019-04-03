# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2019 GEM Foundation
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
"""
"""

import os
import openquake.hazardlib.gsim.can15.nbcc2015_aa13 as aa13
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# A discrepancy of 0.1 % is tolerated
MAX_DISC = 0.1


class NBCC2015_AA13_activecrustFRjb_low_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = aa13.NBCC2015_AA13_activecrustFRjb_low
    FNAME = 'NBCC2015_AA13_activecrustFRjb_low_MEAN.csv'
    MEAN_FILE = os.path.join('CAN15', 'nbcc2015_aa13', FNAME)

    def test_mean(self):
        self.check(self.MEAN_FILE,
                   max_discrep_percentage=MAX_DISC)


class NBCC2015_AA13_inslab30_low_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = aa13.NBCC2015_AA13_inslab30_low
    FNAME = 'NBCC2015_AA13_inslab30_low_MEAN.csv'
    MEAN_FILE = os.path.join('CAN15', 'nbcc2015_aa13', FNAME)

    def test_mean(self):
        self.check(self.MEAN_FILE,
                   max_discrep_percentage=MAX_DISC)


class NBCC2015_AA13_stablecrust_central_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = aa13.NBCC2015_AA13_stablecrust_central
    FNAME = 'NBCC2015_AA13_stablecrust_central_MEAN.csv'
    MEAN_FILE = os.path.join('CAN15', 'nbcc2015_aa13', FNAME)

    def test_mean(self):
        self.check(self.MEAN_FILE,
                   max_discrep_percentage=MAX_DISC)
