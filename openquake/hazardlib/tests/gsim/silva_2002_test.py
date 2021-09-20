# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2021 GEM Foundation
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

from openquake.hazardlib.gsim.silva_2002 import (
    SilvaEtAl2002MblgAB1987NSHMP2008,
    SilvaEtAl2002MblgJ1996NSHMP2008,
    SilvaEtAl2002MwNSHMP2008,
    SilvaEtAl2002DoubleCornerSaturation,
    SilvaEtAl2002SingleCornerSaturation)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Test data generated from subroutine 'getSilva' in hazgridXnga2.f


class SilvaEtAl2002MblgAB1987NSHMP2008TestCase(BaseGSIMTestCase):
    GSIM_CLASS = SilvaEtAl2002MblgAB1987NSHMP2008

    def test_mean(self):
        self.check('SILVA02/SILVA02MblgAB1987NSHMP_MEAN.csv',
                   max_discrep_percentage=0.4)

    def test_std_total(self):
        self.check('SILVA02/SILVA02MblgAB1987NSHMP_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)


class SilvaEtAl2002MblgJ1996NSHMP2008TestCase(BaseGSIMTestCase):
    GSIM_CLASS = SilvaEtAl2002MblgJ1996NSHMP2008

    def test_mean(self):
        self.check('SILVA02/SILVA02MblgJ1996NSHMP_MEAN.csv',
                   max_discrep_percentage=0.4)


class SilvaEtAl2002MwNSHMP2008TestCase(BaseGSIMTestCase):
    GSIM_CLASS = SilvaEtAl2002MwNSHMP2008

    def test_mean(self):
        self.check('SILVA02/SILVA02MwNSHMP_MEAN.csv',
                   max_discrep_percentage=0.4)

# Test data obtained by from haz43


class SilvaEtAl2002DoubleCornerSaturationTestCase(BaseGSIMTestCase):
    """
    We use a tolerance higher than usual since the coefficients in the
    code used to generate the verification tables are slightly different
    than the ones published in the 2002 report. Sigma values are also
    different and therefore not independently tested.
    """
    GSIM_CLASS = SilvaEtAl2002DoubleCornerSaturation

    def test_mean(self):
        self.check('SILVA02/SilvaEtAl2002DoubleCornerSaturation_MEAN.csv',
                   max_discrep_percentage=2.)


class SilvaEtAl2002SingleCornerSaturationTestCase(BaseGSIMTestCase):
    GSIM_CLASS = SilvaEtAl2002SingleCornerSaturation

    def test_mean(self):
        self.check('SILVA02/SilvaEtAl2002SingleCornerSaturation_MEAN.csv',
                   max_discrep_percentage=4.)
