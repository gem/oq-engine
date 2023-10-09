# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2022 GEM Foundation
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

# Test data have been generated from the Python implementation available from the authors


from openquake.hazardlib.gsim.atkinson_2022 import Atkinson2022Crust, Atkinson2022SInter, Atkinson2022SSlab
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

#test case
class Atkinson2022CrustTestCase(BaseGSIMTestCase):
    """
    Test the default model. Here only the mean values are tested.
    """

    GSIM_CLASS = Atkinson2022Crust

    def test_all(self):
        self.check('ATKINSON2022/ATKINSON22_CRUST_CENTRAL_MEAN.csv',
                   max_discrep_percentage=0.5, epistemic = "Central")

    def test_all(self):
        self.check('ATKINSON2022/ATKINSON22_CRUST_LOWER_MEAN.csv',
                   max_discrep_percentage=0.5, epistemic = "Lower")

    def test_all(self):
        self.check('ATKINSON2022/ATKINSON22_CRUST_UPPER_MEAN.csv',
                       max_discrep_percentage=0.5, epistemic = "Upper")

class Atkinson2022SInterTestCase(BaseGSIMTestCase):
    """
    Test the default model. Here only the mean values are tested.
    """

    GSIM_CLASS = Atkinson2022SInter

    def test_all(self):
        self.check('ATKINSON2022/ATKINSON22_INTER_CENTRAL_MEAN.csv',
                   max_discrep_percentage=0.5, epistemic = "Central")

    def test_all(self):
        self.check('ATKINSON2022/ATKINSON22_INTER_LOWER_MEAN.csv',
                   max_discrep_percentage=0.5, epistemic = "Lower")

    def test_all(self):
        self.check('ATKINSON2022/ATKINSON22_INTER_UPPER_MEAN.csv',
                       max_discrep_percentage=0.5, epistemic = "Upper")

class Atkinson2022SSlabTestCase(BaseGSIMTestCase):
    """
    Test the default model. Here only the mean values are tested.
    """

    GSIM_CLASS = Atkinson2022SSlab

    def test_all(self):
        self.check('ATKINSON2022/ATKINSON22_SLAB_CENTRAL_MEAN.csv',
                   max_discrep_percentage=0.5, epistemic = "Central")

    def test_all(self):
        self.check('ATKINSON2022/ATKINSON22_SLAB_LOWER_MEAN.csv',
                   max_discrep_percentage=0.5, epistemic = "Lower")

    def test_all(self):
        self.check('ATKINSON2022/ATKINSON22_SLAB_UPPER_MEAN.csv',
                       max_discrep_percentage=0.5, epistemic = "Upper")
