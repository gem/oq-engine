# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2017 GEM Foundation
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

from openquake.hazardlib.gsim.campbell_2003 import (
    Campbell2003,
    Campbell2003SHARE,
    Campbell2003MblgAB1987NSHMP2008,
    Campbell2003MblgJ1996NSHMP2008,
    Campbell2003MwNSHMP2008
)

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

import numpy

# Test data generated from OpenSHA implementation.

class Campbell2003TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Campbell2003

    def test_mean(self):
        self.check('C03/C03_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('C03/C03_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)


class Campbell2003SHARETestCase(BaseGSIMTestCase):
    GSIM_CLASS = Campbell2003SHARE

    def test_mean(self):
        self.check('C03/C03SHARE_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('C03/C03SHARE_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)


class Campbell2003MblgAB1987NSHMP2008TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Campbell2003MblgAB1987NSHMP2008

    # test data generated from ``subroutine getCampCEUS`` in ``hazgridXnga2.f``

    def test_mean(self):
        self.check('C03/C03MblgAB1987NSHMP2008_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('C03/C03MblgAB1987NSHMP2008_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)


class Campbell2003MblgJ1996NSHMP2008TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Campbell2003MblgJ1996NSHMP2008

    # test data generated from ``subroutine getCampCEUS`` in ``hazgridXnga2.f``

    def test_mean(self):
        self.check('C03/C03MblgJ1996NSHMP2008_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('C03/C03MblgJ1996NSHMP2008_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)


class Campbell2003MwNSHMP2008TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Campbell2003MwNSHMP2008

    # test data generated from ``subroutine getCampCEUS`` in ``hazgridXnga2.f``

    def test_mean(self):
        self.check('C03/C03MwNSHMP2008_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('C03/C03MwNSHMP2008_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)
