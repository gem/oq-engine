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
from types import SimpleNamespace
import numpy as np

from openquake.hazardlib.imt import PGA
from openquake.hazardlib.gsim.morikawa_fujiwara_2013 import (
        MorikawaFujiwara2013Crustal,
        MorikawaFujiwara2013SubInterfaceNE,
        MorikawaFujiwara2013SubSlabSW,
        MorikawaFujiwara2013SubSlabNE,
        MorikawaFujiwara2013CrustalNIED,
        MorikawaFujiwara2013SubInterfaceNIED,
        MorikawaFujiwara2013SubSlabNIED,
        _get_basin_term,
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
                         1500., 1700., 400., 600., 800.])
        z1pt4 = np.array([-999., -999., -999., -999., -999., -999., -999.,
                          -999., -999., -999., 250., 500., 1000.])
        expected = np.array([535.76, 497.52, 406.40, 281.95, 139.77,
                             47.45, 39.27, 10.95, 2.03, 1.00,
                             250., 500., 1000.])
        out = _infer_z1pt4_from_vs30(vs30, z1pt4.copy(), z1pt4 == -999)
        np.testing.assert_allclose(out, expected, atol=1e-2)


class MorikawaFujiwara2013MissingZ1pt4Test(unittest.TestCase):
    """
    Regression test: when reference_depth_to_1pt4km_per_sec is omitted
    from the job file, ctx.z1pt4 is NaN (not -999), and the basin term
    previously returned NaN - silently zeroing the hazard. compute() must
    now raise ValueError in that case.
    """
    def _ctx(self, z1pt4_vals):
        n = len(z1pt4_vals)
        return SimpleNamespace(
            z1pt4=np.asarray(z1pt4_vals, dtype=float),
            vs30=np.full(n, 760.),
            mag=np.full(n, 6.0),
            rrup=np.full(n, 50.),
            hypo_depth=np.full(n, 10.),
            lon=np.full(n, 140.),
            lat=np.full(n, 36.))

    def test_nan_z1pt4_raises(self):
        gmm = MorikawaFujiwara2013Crustal()
        imts = [PGA()]
        n = 3
        mean = np.zeros((1, n))
        sig = np.zeros((1, n))
        expected = (
            "MorikawaFujiwara2013 requires z1pt4 for every site. "
            "Supply it in the site model, set "
            "reference_depth_to_1pt4km_per_sec in the job file, or "
            "set reference_depth_to_1pt4km_per_sec = -999 to use "
            "GEM's Vs30-based z1pt4 estimate.")
        with self.assertRaises(ValueError) as cm:
            gmm.compute(self._ctx([760., np.nan, -999.]),
                        imts, mean, sig, None, None)
        self.assertEqual(str(cm.exception), expected)

    def test_minus999_still_triggers_inference(self):
        # -999 means use GEM's Vs30-based z1pt4 and must still work
        C = MorikawaFujiwara2013Crustal.COEFFS[PGA()]
        bt = _get_basin_term(C, self._ctx([-999., -999., -999.]))
        np.testing.assert_allclose(bt, [0.04433789] * 3, atol=1e-6)
