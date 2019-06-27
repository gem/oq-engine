# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2019 GEM Foundation
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

from openquake.hazardlib.gsim.bchydro_2016_epistemic import (
    BCHydroSERASInter, BCHydroSERASInterHigh, BCHydroSERASInterLow,
    BCHydroSERASSlab, BCHydroSERASSlabHigh, BCHydroSERASSlabLow)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


MAX_DISCREP = 0.01


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
