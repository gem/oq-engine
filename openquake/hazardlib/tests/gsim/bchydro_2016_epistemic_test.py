# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2020 GEM Foundation
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
    BCHydroSERASInter, BCHydroSERASInterHigh, BCHydroSERASInterLow,
    BCHydroSERASSlab, BCHydroSERASSlabHigh, BCHydroSERASSlabLow,
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

class BCHydroSERASInterCentralTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BCHydroSERASInter

    def test_mean(self):
        self.check("sera_bchydro/BCHydroSERA_SINTER_CENTRAL_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP)


class BCHydroSERASInterLowTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BCHydroSERASInterLow

    def test_mean(self):
        self.check("sera_bchydro/BCHydroSERA_SINTER_LOWER_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP)


class BCHydroSERASInterHighTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BCHydroSERASInterHigh

    def test_mean(self):
        self.check("sera_bchydro/BCHydroSERA_SINTER_UPPER_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP)


class BCHydroSERASInterFastTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BCHydroSERASInter

    def test_mean(self):
        self.check("sera_bchydro/BCHydroSERA_SINTER_FAST_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   theta6_adjustment=-0.0015)


class BCHydroSERASInterHighSigmaMuTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BCHydroSERASInter

    def test_mean(self):
        self.check("sera_bchydro/BCHydroSERA_SINTER_HIGH_SIGMA_MU_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   sigma_mu_epsilon=1.0)


class BCHydroSERASInterLinearFABATaperTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BCHydroSERASInter

    def test_mean(self):
        self.check("sera_bchydro/BCHydroSERA_SINTER_LINEAR_FABA_TAPER_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   faba_taper_model="Linear", width=100.)


class BCHydroSERASInterSFuncFABATaperTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BCHydroSERASInter

    def test_mean(self):
        self.check("sera_bchydro/BCHydroSERA_SINTER_SFUNC_FABA_TAPER_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   faba_taper_model="SFunc", a=-100.0, b=100.0)


class BCHydroSERASInterGaussianFABATaperTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BCHydroSERASInter

    def test_mean(self):
        self.check("sera_bchydro/BCHydroSERA_SINTER_GAUSSIAN_FABA_TAPER_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   faba_taper_model="Gaussian", sigma=30.0, a=-100.0, b=100.0)

# Subduction Slab


class BCHydroSERASSlabCentralTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BCHydroSERASSlab

    def test_mean(self):
        self.check("sera_bchydro/BCHydroSERA_SSLAB_CENTRAL_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP)


class BCHydroSERASSlabLowTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BCHydroSERASSlabLow

    def test_mean(self):
        self.check("sera_bchydro/BCHydroSERA_SSLAB_LOWER_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP)


class BCHydroSERASSlabHighTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BCHydroSERASSlabHigh

    def test_mean(self):
        self.check("sera_bchydro/BCHydroSERA_SSLAB_UPPER_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP)


class BCHydroSERASSlabFastTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BCHydroSERASSlab

    def test_mean(self):
        self.check("sera_bchydro/BCHydroSERA_SSLAB_FAST_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   theta6_adjustment=-0.0015)


class BCHydroSERASSlabHighSigmaMuTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BCHydroSERASSlab

    def test_mean(self):
        self.check("sera_bchydro/BCHydroSERA_SSLAB_HIGH_SIGMA_MU_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   sigma_mu_epsilon=1.0)


class BCHydroSERASSlabLinearFABATaperTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BCHydroSERASSlab

    def test_mean(self):
        self.check("sera_bchydro/BCHydroSERA_SSLAB_LINEAR_FABA_TAPER_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   faba_taper_model="Linear", width=100.)


class BCHydroSERASSlabSFuncFABATaperTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BCHydroSERASSlab

    def test_mean(self):
        self.check("sera_bchydro/BCHydroSERA_SSLAB_SFUNC_FABA_TAPER_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   faba_taper_model="SFunc", a=-100.0, b=100.0)


class BCHydroSERASSlabGaussianFABATaperTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BCHydroSERASSlab

    def test_mean(self):
        self.check("sera_bchydro/BCHydroSERA_SSLAB_GAUSSIAN_FABA_TAPER_MEAN.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   faba_taper_model="Gaussian", sigma=30.0, a=-100.0, b=100.0)
