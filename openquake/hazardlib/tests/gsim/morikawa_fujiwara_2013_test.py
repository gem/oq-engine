# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2021 GEM Foundation
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
from openquake.hazardlib.gsim.morikawa_fujiwara_2013 import (
        MorikawaFujiwara2013Crustal,
        MorikawaFujiwara2013SubInterfaceNE,
        MorikawaFujiwara2013SubSlabSW,
        MorikawaFujiwara2013SubSlabNE)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class MorikawaFujiwara2013CrustalTest(BaseGSIMTestCase):
    GSIM_CLASS = MorikawaFujiwara2013Crustal

    def test_all(self):
        self.check('MF13/mean_crustal.csv',
                   max_discrep_percentage=0.1)

    def test_sigma(self):
        self.check('MF13/total_std_crustal.csv',
                   max_discrep_percentage=0.1)


class MorikawaFujiwara2013InterfaceTest(BaseGSIMTestCase):
    GSIM_CLASS = MorikawaFujiwara2013SubInterfaceNE

    def test_all(self):
        self.check('MF13/mean_interface_NE.csv',
                   max_discrep_percentage=0.25)


class MorikawaFujiwara2013IntraSlabTest(BaseGSIMTestCase):
    GSIM_CLASS = MorikawaFujiwara2013SubSlabNE

    def test_all(self):
        self.check('MF13/mean_intraslab_NE.csv',
                   max_discrep_percentage=0.2)


class MorikawaFujiwara2013IntraSlabSWTest(BaseGSIMTestCase):
    GSIM_CLASS = MorikawaFujiwara2013SubSlabSW

    def test_all(self):
        self.check('MF13/mean_intraslab_SW.csv',
                   max_discrep_percentage=0.3)
