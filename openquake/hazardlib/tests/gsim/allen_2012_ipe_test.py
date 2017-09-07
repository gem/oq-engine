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

from openquake.hazardlib.gsim.allen_2012_ipe import (AllenEtAl2012,
                                                     AllenEtAl2012Rhypo)

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

import numpy

# Test data generated from independent Matlab implementation


class AllenEtAl2012TestCase(BaseGSIMTestCase):
    GSIM_CLASS = AllenEtAl2012
    MEAN_FILE = 'a12ipe/AWW_IPE_RRUP_MEAN.csv'
    SIGMA_FILE = 'a12ipe/AWW_IPE_RRUP_SIGMA.csv' 

    def test_mean(self):
        self.check(self.MEAN_FILE,
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check(self.SIGMA_FILE,
                   max_discrep_percentage=0.1)


class AllenEtAl2012RhypoTestCase(AllenEtAl2012TestCase):
    GSIM_CLASS = AllenEtAl2012Rhypo
    MEAN_FILE = 'a12ipe/AWW_IPE_RHYPO_MEAN.csv'
    SIGMA_FILE = 'a12ipe/AWW_IPE_RHYPO_SIGMA.csv' 
