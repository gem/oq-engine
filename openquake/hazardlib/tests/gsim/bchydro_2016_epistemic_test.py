# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2023 GEM Foundation
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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>

import unittest
import numpy as np
from openquake.hazardlib.gsim.bchydro_2016_epistemic import (
    BCHydroESHM20SInter, BCHydroESHM20SInterHigh, BCHydroESHM20SInterLow,
    BCHydroESHM20SSlab, BCHydroESHM20SSlabHigh, BCHydroESHM20SSlabLow,
    FABATaperGaussian, FABATaperStep, FABATaperLinear, FABATaperSFunc,
    FABATaperSigmoid)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


MAX_DISCREP = 0.01


# Test the tapering functions
class FABATaperTestCase(unittest.TestCase):
    """
    Verifies the values in each of the FABA tapering objects
    """
    def setUp(self):
        self.x = np.array([-150., -100., -30., 0., 30., 100., 150.])

    def test_faba_step_taper(self):
        model = FABATaperStep()
        expected = np.array([0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0])
        np.testing.assert_array_almost_equal(model(self.x), expected, 7)

    def test_faba_linear_taper(self):
        model = FABATaperLinear(width=100.0)
        expected = np.array([0.000, 0.000, 0.200, 0.500, 0.800, 1.000, 1.000])
        np.testing.assert_array_almost_equal(model(self.x), expected, 7)

    def test_faba_sfunc_taper(self):
        model = FABATaperSFunc(a=-100., b=100.)
        expected = np.array([0.000, 0.000, 0.245, 0.500, 0.755, 1.000, 1.000])
        np.testing.assert_array_almost_equal(model(self.x), expected, 7)

    def test_faba_sigmoid_taper(self):
        model = FABATaperSigmoid(c=30.0)
        expected = np.array([0.006692851, 0.034445196, 0.268941421, 0.5,
                             0.731058579, 0.965554804, 0.993307149])
        np.testing.assert_array_almost_equal(model(self.x), expected, 7)

    def test_faba_sigmoid_gaussian(self):
        model = FABATaperGaussian(sigma=30., a=-100., b=100.)
        expected = np.array([0.0, 0.0, 0.158362087, 0.5,
                             0.841637913, 1.0, 1.0])
        np.testing.assert_array_almost_equal(model(self.x), expected, 7)


# Subduction Interface

class BCHydroESHM20SInterCentralTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BCHydroESHM20SInter

    def test_mean(self):
        self.check("eshm20_bchydro/BCHydroESHM20_SINTER_CENTRAL_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP)


class BCHydroESHM20SInterLowTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BCHydroESHM20SInterLow

    def test_mean(self):
        self.check("eshm20_bchydro/BCHydroESHM20_SINTER_LOWER_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP)


class BCHydroESHM20SInterHighTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BCHydroESHM20SInterHigh

    def test_mean(self):
        self.check("eshm20_bchydro/BCHydroESHM20_SINTER_UPPER_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP)


class BCHydroESHM20SInterFastTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BCHydroESHM20SInter

    def test_mean(self):
        self.check("eshm20_bchydro/BCHydroESHM20_SINTER_FAST_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   theta6_adjustment=-0.0015)


class BCHydroESHM20SInterHighSigmaMuTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BCHydroESHM20SInter

    def test_mean(self):
        self.check(
            "eshm20_bchydro/BCHydroESHM20_SINTER_HIGH_SIGMA_MU_MEAN.csv",
            max_discrep_percentage=MAX_DISCREP,
            sigma_mu_epsilon=1.0)


class BCHydroESHM20SInterLinearFABATaperTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BCHydroESHM20SInter

    def test_mean(self):
        self.check(
            "eshm20_bchydro/BCHydroESHM20_SINTER_LINEAR_FABA_TAPER_MEAN.csv",
            max_discrep_percentage=MAX_DISCREP,
            faba_taper_model="Linear", width=100.)


class BCHydroESHM20SInterSFuncFABATaperTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BCHydroESHM20SInter

    def test_mean(self):
        self.check(
            "eshm20_bchydro/BCHydroESHM20_SINTER_SFUNC_FABA_TAPER_MEAN.csv",
            max_discrep_percentage=MAX_DISCREP,
            faba_taper_model="SFunc", a=-100.0, b=100.0)


class BCHydroESHM20SInterGaussianFABATaperTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BCHydroESHM20SInter

    def test_mean(self):
        self.check(
            "eshm20_bchydro/BCHydroESHM20_SINTER_GAUSSIAN_FABA_TAPER_MEAN.csv",
            max_discrep_percentage=MAX_DISCREP,
            faba_taper_model="Gaussian", sigma=30.0, a=-100.0, b=100.0)

# Subduction Slab


class BCHydroESHM20SSlabCentralTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BCHydroESHM20SSlab

    def test_mean(self):
        self.check("eshm20_bchydro/BCHydroESHM20_SSLAB_CENTRAL_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP)


class BCHydroESHM20SSlabLowTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BCHydroESHM20SSlabLow

    def test_mean(self):
        self.check("eshm20_bchydro/BCHydroESHM20_SSLAB_LOWER_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP)


class BCHydroESHM20SSlabHighTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BCHydroESHM20SSlabHigh

    def test_mean(self):
        self.check("eshm20_bchydro/BCHydroESHM20_SSLAB_UPPER_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP)


class BCHydroESHM20SSlabFastTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BCHydroESHM20SSlab

    def test_mean(self):
        self.check("eshm20_bchydro/BCHydroESHM20_SSLAB_FAST_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   theta6_adjustment=-0.0015)


class BCHydroESHM20SSlabHighSigmaMuTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BCHydroESHM20SSlab

    def test_mean(self):
        self.check(
            "eshm20_bchydro/BCHydroESHM20_SSLAB_HIGH_SIGMA_MU_MEAN.csv",
            max_discrep_percentage=MAX_DISCREP,
            sigma_mu_epsilon=1.0)


class BCHydroESHM20SSlabLinearFABATaperTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BCHydroESHM20SSlab

    def test_mean(self):
        self.check(
            "eshm20_bchydro/BCHydroESHM20_SSLAB_LINEAR_FABA_TAPER_MEAN.csv",
            max_discrep_percentage=MAX_DISCREP,
            faba_taper_model="Linear", width=100.)


class BCHydroESHM20SSlabSFuncFABATaperTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BCHydroESHM20SSlab

    def test_mean(self):
        self.check(
            "eshm20_bchydro/BCHydroESHM20_SSLAB_SFUNC_FABA_TAPER_MEAN.csv",
            max_discrep_percentage=MAX_DISCREP,
            faba_taper_model="SFunc", a=-100.0, b=100.0)


class BCHydroESHM20SSlabGaussianFABATaperTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BCHydroESHM20SSlab

    def test_mean(self):
        self.check(
            "eshm20_bchydro/BCHydroESHM20_SSLAB_GAUSSIAN_FABA_TAPER_MEAN.csv",
            max_discrep_percentage=MAX_DISCREP,
            faba_taper_model="Gaussian", sigma=30.0, a=-100.0, b=100.0)
