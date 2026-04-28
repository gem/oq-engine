# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2026 GEM Foundation
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

from openquake.hazardlib.gsim.abrahamson_silva_2008 import (
    AbrahamsonSilva2008BCHydro)
from openquake.hazardlib.gsim.boore_atkinson_2008 import (
    BooreAtkinson2008BCHydro)
from openquake.hazardlib.gsim.campbell_bozorgnia_2008 import (
    CampbellBozorgnia2008BCHydro)
from openquake.hazardlib.gsim.chiou_youngs_2008 import (
    ChiouYoungs2008BCHydro)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


TEST_DATA_BASE = 'NGA/bchydro_subclasses/'


# Circular unit tests with same tolerances as corresponding
# NGAWest-1 GMM tests


class AbrahamsonSilva2008BCHydroTestCase(BaseGSIMTestCase):
    GSIM_CLASS = AbrahamsonSilva2008BCHydro

    def test_mean_sigma_mu_minus1(self):
        self.check(TEST_DATA_BASE + 'AS08BCHydro_MEAN_sme_minus1.csv',
                   max_discrep_percentage=0.1,
                   single_stat_sigma=True, sigma_mu_epsilon=-1.)

    def test_mean_sigma_mu_zero(self):
        self.check(TEST_DATA_BASE + 'AS08BCHydro_MEAN_sme_zero.csv',
                   max_discrep_percentage=0.1,
                   single_stat_sigma=True, sigma_mu_epsilon=0.)

    def test_mean_sigma_mu_plus1(self):
        self.check(TEST_DATA_BASE + 'AS08BCHydro_MEAN_sme_plus1.csv',
                   max_discrep_percentage=0.1,
                   single_stat_sigma=True, sigma_mu_epsilon=1.)

    def test_total_stddev_single_st_sigma(self):
        self.check(TEST_DATA_BASE + 'AS08BCHydro_STD_TOTAL.csv',
                   max_discrep_percentage=0.1,
                   single_stat_sigma=True, sigma_mu_epsilon=0.)


class BooreAtkinson2008BCHydroTestCase(BaseGSIMTestCase):
    GSIM_CLASS = BooreAtkinson2008BCHydro

    def test_mean_sigma_mu_minus1(self):
        self.check(TEST_DATA_BASE + 'BA08BCHydro_MEAN_sme_minus1.csv',
                   max_discrep_percentage=0.6,
                   single_stat_sigma=True, sigma_mu_epsilon=-1.)

    def test_mean_sigma_mu_zero(self):
        self.check(TEST_DATA_BASE + 'BA08BCHydro_MEAN_sme_zero.csv',
                   max_discrep_percentage=0.6,
                   single_stat_sigma=True, sigma_mu_epsilon=0.)

    def test_mean_sigma_mu_plus1(self):
        self.check(TEST_DATA_BASE + 'BA08BCHydro_MEAN_sme_plus1.csv',
                   max_discrep_percentage=0.6,
                   single_stat_sigma=True, sigma_mu_epsilon=1.)

    def test_total_stddev_single_st_sigma(self):
        self.check(TEST_DATA_BASE + 'BA08BCHydro_STD_TOTAL.csv',
                   max_discrep_percentage=0.1,
                   single_stat_sigma=True, sigma_mu_epsilon=0.)


class CampbellBozorgnia2008BCHydroTestCase(BaseGSIMTestCase):
    GSIM_CLASS = CampbellBozorgnia2008BCHydro

    def test_mean_sigma_mu_minus1(self):
        self.check(TEST_DATA_BASE + 'CB08BCHydro_MEAN_sme_minus1.csv',
                   max_discrep_percentage=0.1,
                   single_stat_sigma=True, sigma_mu_epsilon=-1.)

    def test_mean_sigma_mu_zero(self):
        self.check(TEST_DATA_BASE + 'CB08BCHydro_MEAN_sme_zero.csv',
                   max_discrep_percentage=0.1,
                   single_stat_sigma=True, sigma_mu_epsilon=0.)

    def test_mean_sigma_mu_plus1(self):
        self.check(TEST_DATA_BASE + 'CB08BCHydro_MEAN_sme_plus1.csv',
                   max_discrep_percentage=0.1,
                   single_stat_sigma=True, sigma_mu_epsilon=1.)

    def test_total_stddev_single_st_sigma(self):
        self.check(TEST_DATA_BASE + 'CB08BCHydro_STD_TOTAL.csv',
                   max_discrep_percentage=0.1,
                   single_stat_sigma=True, sigma_mu_epsilon=0.)


class ChiouYoungs2008BCHydroTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ChiouYoungs2008BCHydro

    def test_mean_sigma_mu_minus1(self):
        self.check(TEST_DATA_BASE + 'CY08BCHydro_MEAN_sme_minus1.csv',
                   max_discrep_percentage=0.1,
                   single_stat_sigma=True, sigma_mu_epsilon=-1.)

    def test_mean_sigma_mu_zero(self):
        self.check(TEST_DATA_BASE + 'CY08BCHydro_MEAN_sme_zero.csv',
                   max_discrep_percentage=0.1,
                   single_stat_sigma=True, sigma_mu_epsilon=0.)

    def test_mean_sigma_mu_plus1(self):
        self.check(TEST_DATA_BASE + 'CY08BCHydro_MEAN_sme_plus1.csv',
                   max_discrep_percentage=0.1,
                   single_stat_sigma=True, sigma_mu_epsilon=1.)

    def test_total_stddev_single_st_sigma(self):
        self.check(TEST_DATA_BASE + 'CY08BCHydro_STD_TOTAL.csv',
                   max_discrep_percentage=0.1,
                   single_stat_sigma=True, sigma_mu_epsilon=0.)
