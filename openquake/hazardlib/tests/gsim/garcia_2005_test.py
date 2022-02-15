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

from openquake.hazardlib.gsim.garcia_2005 import (
    GarciaEtAl2005SSlab, GarciaEtAl2005SSlabVert)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class GarciaEtAl2005SSlabTestCase(BaseGSIMTestCase):
    GSIM_CLASS = GarciaEtAl2005SSlab

    # Test data generated from Fortran implementation
    # provided by Daniel Garcia

    def test_all(self):
        self.check('GarciaEtAl2005SSlab.csv',
                   max_discrep_percentage=0.2,
                   std_discrep_percentage=0.1)


class GarciaEtAl2005SSlabVertTestCase(BaseGSIMTestCase):
    GSIM_CLASS = GarciaEtAl2005SSlabVert

    # Test data generated from Fortran implementation
    # provided by Daniel Garcia

    def test_all(self):
        self.check('GarciaEtAl2005SSlabVert.csv',
                   max_discrep_percentage=0.2,
                   std_discrep_percentage=0.1)
