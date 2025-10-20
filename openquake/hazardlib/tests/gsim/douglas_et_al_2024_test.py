# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2025 GEM Foundation
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

from openquake.hazardlib.gsim.douglas_et_al_2024 import (
    Douglas_Et_Al_2024Rjb,
    Douglas_Et_Al_2024Rjb_3branch,
    Douglas_Et_Al_2024Rjb_5branch,
    Douglas_Et_Al_2024Rrup,
    Douglas_Et_Al_2024Rrup_3branch,
    Douglas_Et_Al_2024Rrup_5branch)

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Test data generated from OpenSHA implementation.

# Rjb 162-branch model
class DogulasEtAl24Rjb_b1_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Douglas_Et_Al_2024Rjb

    def test_all(self):
        self.check('DouglasEtAl24/Douglas_et_al_2024Rjb_b1_MEAN.csv',
                   'DouglasEtAl24/Douglas_et_al_2024Rjb_STD_TOTAL.csv',
                   max_discrep_percentage=0.1, branch=1)

class DogulasEtAl24Rjb_b99_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Douglas_Et_Al_2024Rjb

    def test_all(self):
        self.check('DouglasEtAl24/Douglas_et_al_2024Rjb_b99_MEAN.csv',
                   'DouglasEtAl24/Douglas_et_al_2024Rjb_STD_TOTAL.csv',
                   max_discrep_percentage=0.1, branch=99)

class DogulasEtAl24Rjb_b162_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Douglas_Et_Al_2024Rjb

    def test_all(self):
        self.check('DouglasEtAl24/Douglas_et_al_2024Rjb_b162_MEAN.csv',
                   'DouglasEtAl24/Douglas_et_al_2024Rjb_STD_TOTAL.csv',
                   max_discrep_percentage=0.1, branch=162)

# Rjb 5-branch model
class DogulasEtAl24Rjb5b_b1Original_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Douglas_Et_Al_2024Rjb_5branch

    def test_all(self):
        self.check('DouglasEtAl24/Douglas_et_al_2024Rjb_5branch_b1Original_MEAN.csv',
                   'DouglasEtAl24/Douglas_et_al_2024Rjb_STD_TOTAL.csv',
                   max_discrep_percentage=0.1, branch=1, weightopt='original')

class DogulasEtAl24Rjb5b_b3Original_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Douglas_Et_Al_2024Rjb_5branch

    def test_all(self):
        self.check('DouglasEtAl24/Douglas_et_al_2024Rjb_5branch_b3Original_MEAN.csv',
                   'DouglasEtAl24/Douglas_et_al_2024Rjb_STD_TOTAL.csv',
                   max_discrep_percentage=0.1, branch=3, weightopt='original')

class DogulasEtAl24Rjb5b_b5Original_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Douglas_Et_Al_2024Rjb_5branch

    def test_all(self):
        self.check('DouglasEtAl24/Douglas_et_al_2024Rjb_5branch_b5Original_MEAN.csv',
                   'DouglasEtAl24/Douglas_et_al_2024Rjb_STD_TOTAL.csv',
                   max_discrep_percentage=0.1, branch=5, weightopt='original')

class DogulasEtAl24Rjb5b_b1Updated_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Douglas_Et_Al_2024Rjb_5branch

    def test_all(self):
        self.check('DouglasEtAl24/Douglas_et_al_2024Rjb_5branch_b1Updated_MEAN.csv',
                   'DouglasEtAl24/Douglas_et_al_2024Rjb_STD_TOTAL.csv',
                   max_discrep_percentage=0.1, branch=1, weightopt='updated')

class DogulasEtAl24Rjb5b_b3Updated_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Douglas_Et_Al_2024Rjb_5branch

    def test_all(self):
        self.check('DouglasEtAl24/Douglas_et_al_2024Rjb_5branch_b3Updated_MEAN.csv',
                   'DouglasEtAl24/Douglas_et_al_2024Rjb_STD_TOTAL.csv',
                   max_discrep_percentage=0.1, branch=3, weightopt='updated')

class DogulasEtAl24Rjb5b_b5Updated_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Douglas_Et_Al_2024Rjb_5branch

    def test_all(self):
        self.check('DouglasEtAl24/Douglas_et_al_2024Rjb_5branch_b5Updated_MEAN.csv',
                   'DouglasEtAl24/Douglas_et_al_2024Rjb_STD_TOTAL.csv',
                   max_discrep_percentage=0.1, branch=5, weightopt='updated')

# Rjb 3-branch model
class DogulasEtAl24Rjb3b_b1Original_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Douglas_Et_Al_2024Rjb_3branch

    def test_all(self):
        self.check('DouglasEtAl24/Douglas_et_al_2024Rjb_3branch_b1Original_MEAN.csv',
                   'DouglasEtAl24/Douglas_et_al_2024Rjb_STD_TOTAL.csv',
                   max_discrep_percentage=0.1, branch=1, weightopt='original')

class DogulasEtAl24Rjb3b_b2Original_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Douglas_Et_Al_2024Rjb_3branch

    def test_all(self):
        self.check('DouglasEtAl24/Douglas_et_al_2024Rjb_3branch_b2Original_MEAN.csv',
                   'DouglasEtAl24/Douglas_et_al_2024Rjb_STD_TOTAL.csv',
                   max_discrep_percentage=0.1, branch=2, weightopt='original')

class DogulasEtAl24Rjb3b_b3Original_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Douglas_Et_Al_2024Rjb_3branch

    def test_all(self):
        self.check('DouglasEtAl24/Douglas_et_al_2024Rjb_3branch_b3Original_MEAN.csv',
                   'DouglasEtAl24/Douglas_et_al_2024Rjb_STD_TOTAL.csv',
                   max_discrep_percentage=0.1, branch=3, weightopt='original')

class DogulasEtAl24Rjb3b_b1Updated_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Douglas_Et_Al_2024Rjb_3branch

    def test_all(self):
        self.check('DouglasEtAl24/Douglas_et_al_2024Rjb_3branch_b1Updated_MEAN.csv',
                   'DouglasEtAl24/Douglas_et_al_2024Rjb_STD_TOTAL.csv',
                   max_discrep_percentage=0.1, branch=1, weightopt='updated')

class DogulasEtAl24Rjb3b_b2Updated_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Douglas_Et_Al_2024Rjb_3branch

    def test_all(self):
        self.check('DouglasEtAl24/Douglas_et_al_2024Rjb_3branch_b2Updated_MEAN.csv',
                   'DouglasEtAl24/Douglas_et_al_2024Rjb_STD_TOTAL.csv',
                   max_discrep_percentage=0.1, branch=2, weightopt='updated')

class DogulasEtAl24Rjb3b_b3Updated_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Douglas_Et_Al_2024Rjb_3branch

    def test_all(self):
        self.check('DouglasEtAl24/Douglas_et_al_2024Rjb_3branch_b3Updated_MEAN.csv',
                   'DouglasEtAl24/Douglas_et_al_2024Rjb_STD_TOTAL.csv',
                   max_discrep_percentage=0.1, branch=3, weightopt='updated')



## Rrup 162-branch model
class DogulasEtAl24Rrup_b10_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Douglas_Et_Al_2024Rrup

    def test_all(self):
        self.check('DouglasEtAl24/Douglas_et_al_2024Rrup_b10_MEAN.csv',
                   'DouglasEtAl24/Douglas_et_al_2024Rrup_STD_TOTAL.csv',
                   max_discrep_percentage=0.1, branch=10)

class DogulasEtAl24Rrup_b60_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Douglas_Et_Al_2024Rrup

    def test_all(self):
        self.check('DouglasEtAl24/Douglas_et_al_2024Rrup_b60_MEAN.csv',
                   'DouglasEtAl24/Douglas_et_al_2024Rrup_STD_TOTAL.csv',
                   max_discrep_percentage=0.1, branch=60)

class DogulasEtAl24Rrup_b100_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Douglas_Et_Al_2024Rrup

    def test_all(self):
        self.check('DouglasEtAl24/Douglas_et_al_2024Rrup_b100_MEAN.csv',
                   'DouglasEtAl24/Douglas_et_al_2024Rrup_STD_TOTAL.csv',
                   max_discrep_percentage=0.1, branch=100)

# Rrup 5-branch model
class DogulasEtAl24Rrup5b_b2Original_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Douglas_Et_Al_2024Rrup_5branch

    def test_all(self):
        self.check('DouglasEtAl24/Douglas_et_al_2024Rrup_5branch_b2Original_MEAN.csv',
                   'DouglasEtAl24/Douglas_et_al_2024Rrup_STD_TOTAL.csv',
                   max_discrep_percentage=0.1, branch=2, weightopt='original')

class DogulasEtAl24Rrup5b_b3Original_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Douglas_Et_Al_2024Rrup_5branch

    def test_all(self):
        self.check('DouglasEtAl24/Douglas_et_al_2024Rrup_5branch_b3Original_MEAN.csv',
                   'DouglasEtAl24/Douglas_et_al_2024Rrup_STD_TOTAL.csv',
                   max_discrep_percentage=0.1, branch=3, weightopt='original')

class DogulasEtAl24Rrup5b_b4Original_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Douglas_Et_Al_2024Rrup_5branch

    def test_all(self):
        self.check('DouglasEtAl24/Douglas_et_al_2024Rrup_5branch_b4Original_MEAN.csv',
                   'DouglasEtAl24/Douglas_et_al_2024Rrup_STD_TOTAL.csv',
                   max_discrep_percentage=0.1, branch=4, weightopt='original')

class DogulasEtAl24Rrup5b_b2Updated_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Douglas_Et_Al_2024Rrup_5branch

    def test_all(self):
        self.check('DouglasEtAl24/Douglas_et_al_2024Rrup_5branch_b2Updated_MEAN.csv',
                   'DouglasEtAl24/Douglas_et_al_2024Rrup_STD_TOTAL.csv',
                   max_discrep_percentage=0.1, branch=2, weightopt='updated')

class DogulasEtAl24Rrup5b_b3Updated_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Douglas_Et_Al_2024Rrup_5branch

    def test_all(self):
        self.check('DouglasEtAl24/Douglas_et_al_2024Rrup_5branch_b3Updated_MEAN.csv',
                   'DouglasEtAl24/Douglas_et_al_2024Rrup_STD_TOTAL.csv',
                   max_discrep_percentage=0.1, branch=3, weightopt='updated')

class DogulasEtAl24Rrup5b_b4Updated_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Douglas_Et_Al_2024Rrup_5branch

    def test_all(self):
        self.check('DouglasEtAl24/Douglas_et_al_2024Rrup_5branch_b4Updated_MEAN.csv',
                   'DouglasEtAl24/Douglas_et_al_2024Rrup_STD_TOTAL.csv',
                   max_discrep_percentage=0.1, branch=4, weightopt='updated')

# Rrup 3-branch model
class DogulasEtAl24Rrup3b_b1Original_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Douglas_Et_Al_2024Rrup_3branch

    def test_all(self):
        self.check('DouglasEtAl24/Douglas_et_al_2024Rrup_3branch_b1Original_MEAN.csv',
                   'DouglasEtAl24/Douglas_et_al_2024Rrup_STD_TOTAL.csv',
                   max_discrep_percentage=0.1, branch=1, weightopt='original')

class DogulasEtAl24Rrup3b_b2Original_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Douglas_Et_Al_2024Rrup_3branch

    def test_all(self):
        self.check('DouglasEtAl24/Douglas_et_al_2024Rrup_3branch_b2Original_MEAN.csv',
                   'DouglasEtAl24/Douglas_et_al_2024Rrup_STD_TOTAL.csv',
                   max_discrep_percentage=0.1, branch=2, weightopt='original')

class DogulasEtAl24Rrup3b_b3Original_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Douglas_Et_Al_2024Rrup_3branch

    def test_all(self):
        self.check('DouglasEtAl24/Douglas_et_al_2024Rrup_3branch_b3Original_MEAN.csv',
                   'DouglasEtAl24/Douglas_et_al_2024Rrup_STD_TOTAL.csv',
                   max_discrep_percentage=0.1, branch=3, weightopt='original')

class DogulasEtAl24Rrup3b_b1Updated_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Douglas_Et_Al_2024Rrup_3branch

    def test_all(self):
        self.check('DouglasEtAl24/Douglas_et_al_2024Rrup_3branch_b1Updated_MEAN.csv',
                   'DouglasEtAl24/Douglas_et_al_2024Rrup_STD_TOTAL.csv',
                   max_discrep_percentage=0.1, branch=1, weightopt='updated')

class DogulasEtAl24Rrup3b_b2Updated_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Douglas_Et_Al_2024Rrup_3branch

    def test_all(self):
        self.check('DouglasEtAl24/Douglas_et_al_2024Rrup_3branch_b2Updated_MEAN.csv',
                   'DouglasEtAl24/Douglas_et_al_2024Rrup_STD_TOTAL.csv',
                   max_discrep_percentage=0.1, branch=2, weightopt='updated')

class DogulasEtAl24Rrup3b_b3Updated_TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Douglas_Et_Al_2024Rrup_3branch

    def test_all(self):
        self.check('DouglasEtAl24/Douglas_et_al_2024Rrup_3branch_b3Updated_MEAN.csv',
                   'DouglasEtAl24/Douglas_et_al_2024Rrup_STD_TOTAL.csv',
                   max_discrep_percentage=0.1, branch=3, weightopt='updated')
