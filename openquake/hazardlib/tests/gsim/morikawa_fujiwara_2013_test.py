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
import unittest
import numpy as np

from openquake.hazardlib.gsim.morikawa_fujiwara_2013 import (
        MorikawaFujiwara2013Crustal,
        MorikawaFujiwara2013SubInterfaceNE,
        MorikawaFujiwara2013SubSlabSW,
        MorikawaFujiwara2013SubSlabNE,
        MorikawaFujiwara2013CrustalNIED,
        MorikawaFujiwara2013SubInterfaceNIED,
        MorikawaFujiwara2013SubSlabNIED,
        _infer_z1pt4_from_vs30)
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


class MorikawaFujiwara2013CrustalNIEDTest(BaseGSIMTestCase):
    GSIM_CLASS = MorikawaFujiwara2013CrustalNIED

    def test_sigma(self):
        self.check('MF13/total_std_crustal_nied.csv',
                   max_discrep_percentage=0.1)


class MorikawaFujiwara2013SubInterfaceNIEDTest(BaseGSIMTestCase):
    GSIM_CLASS = MorikawaFujiwara2013SubInterfaceNIED

    def test_sigma(self):
        self.check('MF13/total_std_interface_nied.csv',
                   max_discrep_percentage=0.1)


class MorikawaFujiwara2013SubSlabNIEDTest(BaseGSIMTestCase):
    GSIM_CLASS = MorikawaFujiwara2013SubSlabNIED

    def test_sigma(self):
        self.check('MF13/total_std_intraslab_nied.csv',
                   max_discrep_percentage=0.1)


class MorikawaFujiwara2013InferZ1pt4Test(unittest.TestCase):
    """
    Check that _infer_z1pt4_from_vs30 function (representing GEM's approach
    of fitting CY14's Japan variant Vs30 to z1pt4 equation to NIED data)
    returns the expected z1pt4 for each -999 site while leaving sites with a
    measured z1pt4 unchanged
    """
    def test_inferred_z1pt4_values(self):
        vs30 = np.array([150., 185., 260., 365., 530., 760., 800., 1080.,
                         1500., 400., 600., 800.])
        z1pt4 = np.array([-999., -999., -999., -999., -999., -999., -999.,
                          -999., -999., 250., 500., 1000.])
        expected = np.array([6.283, 6.209, 6.006, 5.641, 4.939, 3.859,
                             3.670, 2.393, 0.706, 250., 500., 1000.])
        out = _infer_z1pt4_from_vs30(vs30, z1pt4.copy(), z1pt4 == -999)
        np.testing.assert_allclose(out, expected, atol=1e-3)
