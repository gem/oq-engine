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
from openquake.hazardlib.gsim.atkinson_boore_2003 import (
    AtkinsonBoore2003SInter,  AtkinsonBoore2003SSlab,
    AtkinsonBoore2003SSlabCascadiaNSHMP2008
)

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

import numpy

# Test data generated from OpenSHA implementation

class AtkinsonBoore2003SInterTestCase(BaseGSIMTestCase):
    GSIM_CLASS = AtkinsonBoore2003SInter

    def test_mean(self):
        self.check('AB03/AB03SInter_MEAN.csv',
                    max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('AB03/AB03SInter_STD_TOTAL.csv',
                    max_discrep_percentage=0.1)

    def test_std_intra(self):
        self.check('AB03/AB03SInter_STD_INTRA.csv',
                    max_discrep_percentage=0.1)

    def test_std_inter(self):
        self.check('AB03/AB03SInter_STD_INTER.csv',
                    max_discrep_percentage=0.1)

class AtkinsonBoore2003SSlabTestCase(BaseGSIMTestCase):
    GSIM_CLASS = AtkinsonBoore2003SSlab

    def test_mean(self):
        self.check('AB03/AB03SSlab_MEAN.csv',
                    max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('AB03/AB03SSlab_STD_TOTAL.csv',
                    max_discrep_percentage=0.1)

    def test_std_intra(self):
        self.check('AB03/AB03SSlab_STD_INTRA.csv',
                    max_discrep_percentage=0.1)

    def test_std_inter(self):
        self.check('AB03/AB03SSlab_STD_INTER.csv',
                    max_discrep_percentage=0.1)


class AtkinsonBoore2003SSlabCascadiaNSHMP2008TestCase(BaseGSIMTestCase):
    GSIM_CLASS = AtkinsonBoore2003SSlabCascadiaNSHMP2008

    def test_mean(self):
        self.check('AB03/AB03SSlabCascadiaNSHMP_MEAN.csv',
                    max_discrep_percentage=0.2)

    def test_std_total(self):
        self.check('AB03/AB03SSlabCascadiaNSHMP_STD_TOTAL.csv',
                    max_discrep_percentage=0.1)
