# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2018 GEM Foundation
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
"""

"""
import os
import numpy as np
from openquake.hazardlib.gsim.nga_east import \
    DarraghEtAl2015NGAEast1CCSPTotalSigma
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.tests.gsim.check_gsim import check_gsim


class BaseNGAEastGSIMTestCase(BaseGSIMTestCase):
    """
    Modification of BaseGSIMTestCase to allow for the GSIM_CLASS attibute to
    be defined as an instantiated GSIM class
    """
    def check(self, filename, max_discrep_percentage):
        filename = os.path.join(self.BASE_DATA_PATH, filename)
        errors, stats, sctx, rctx, dctx, ctxs = check_gsim(
            self.GSIM_CLASS, open(filename), max_discrep_percentage)
        s_att = self.get_context_attributes(sctx)
        r_att = self.get_context_attributes(rctx)
        d_att = self.get_context_attributes(dctx)
        self.assertEqual(self.GSIM_CLASS.REQUIRES_SITES_PARAMETERS, s_att)
        self.assertEqual(self.GSIM_CLASS.REQUIRES_RUPTURE_PARAMETERS, r_att)
        self.assertEqual(self.GSIM_CLASS.REQUIRES_DISTANCES, d_att)
        self.assertTrue(
            np.all(ctxs),
            msg='Contexts objects have been changed by method '
                'get_mean_and_stddevs')
        if errors:
            raise AssertionError(stats)
        print()
        print(stats)


# Required the definition of a specific GMPE, doesn't matter which
DUMMY_GSIM = DarraghEtAl2015NGAEast1CCSPTotalSigma

# Maximum discrepancy is increased to 2 % to account for misprints and
# rounding errors in the tables used for the target values
MAX_DISC = 2.0


class NGAEastTotalSigmaGlobalErgodicLowTestCase(BaseNGAEastGSIMTestCase):
    GSIM_CLASS = DUMMY_GSIM(tau_model="global", phi_model="global",
                            phi_s2ss_model="cena", sigma_quantile=0.05)

    TOTAL_STDDEV_FILE = "nga_east_total_sigma_tables/GLOBAL_ERGODIC_LOW.csv"

    def test_total_stddev(self):
        self.check(self.TOTAL_STDDEV_FILE,
                   max_discrep_percentage=MAX_DISC)


class NGAEastTotalSigmaGlobalErgodicCentralTestCase(
        NGAEastTotalSigmaGlobalErgodicLowTestCase):
    GSIM_CLASS = DUMMY_GSIM(tau_model="global", phi_model="global",
                            phi_s2ss_model="cena", sigma_quantile=0.50)
    TOTAL_STDDEV_FILE = \
        "nga_east_total_sigma_tables/GLOBAL_ERGODIC_CENTRAL.csv"


class NGAEastTotalSigmaGlobalErgodicHighTestCase(
        NGAEastTotalSigmaGlobalErgodicLowTestCase):
    GSIM_CLASS = DUMMY_GSIM(tau_model="global", phi_model="global",
                            phi_s2ss_model="cena", sigma_quantile=0.95)
    TOTAL_STDDEV_FILE = "nga_east_total_sigma_tables/GLOBAL_ERGODIC_HIGH.csv"


# CENA Constant-phi Ergodic Model


class NGAEastTotalSigmaCENAFixedErgodicLowTestCase(
        NGAEastTotalSigmaGlobalErgodicLowTestCase):
    GSIM_CLASS = DUMMY_GSIM(tau_model="global", phi_model="cena_constant",
                            phi_s2ss_model="cena", sigma_quantile=0.05)
    TOTAL_STDDEV_FILE = "nga_east_total_sigma_tables/"\
        "CENA_CONSTANT_ERGODIC_LOW.csv"


class NGAEastTotalSigmaCENAFixedErgodicCentralTestCase(
        NGAEastTotalSigmaGlobalErgodicLowTestCase):
    GSIM_CLASS = DUMMY_GSIM(tau_model="global", phi_model="cena_constant",
                            phi_s2ss_model="cena", sigma_quantile=0.50)
    TOTAL_STDDEV_FILE = "nga_east_total_sigma_tables/"\
        "CENA_CONSTANT_ERGODIC_CENTRAL.csv"


class NGAEastTotalSigmaCENAFixedErgodicHighTestCase(
        NGAEastTotalSigmaGlobalErgodicLowTestCase):
    GSIM_CLASS = DUMMY_GSIM(tau_model="global", phi_model="cena_constant",
                            phi_s2ss_model="cena", sigma_quantile=0.95)
    TOTAL_STDDEV_FILE = "nga_east_total_sigma_tables/"\
        "CENA_CONSTANT_ERGODIC_HIGH.csv"


# CENA Model


class NGAEastTotalSigmaCENAErgodicLowTestCase(
        NGAEastTotalSigmaGlobalErgodicLowTestCase):
    GSIM_CLASS = DUMMY_GSIM(tau_model="global", phi_model="cena",
                            phi_s2ss_model="cena", sigma_quantile=0.05)
    TOTAL_STDDEV_FILE = "nga_east_total_sigma_tables/CENA_ERGODIC_LOW.csv"


class NGAEastTotalSigmaCENAErgodicCentralTestCase(
        NGAEastTotalSigmaGlobalErgodicLowTestCase):
    GSIM_CLASS = DUMMY_GSIM(tau_model="global", phi_model="cena",
                            phi_s2ss_model="cena", sigma_quantile=0.50)
    TOTAL_STDDEV_FILE = "nga_east_total_sigma_tables/CENA_ERGODIC_CENTRAL.csv"


class NGAEastTotalSigmaCENAErgodicHighTestCase(
        NGAEastTotalSigmaGlobalErgodicLowTestCase):
    GSIM_CLASS = DUMMY_GSIM(tau_model="global", phi_model="cena",
                            phi_s2ss_model="cena", sigma_quantile=0.95)
    TOTAL_STDDEV_FILE = "nga_east_total_sigma_tables/CENA_ERGODIC_HIGH.csv"


# Global Non-ergodic Model


class NGAEastTotalSigmaGlobalNonErgodicLowTestCase(
        NGAEastTotalSigmaGlobalErgodicLowTestCase):
    GSIM_CLASS = DUMMY_GSIM(tau_model="global", phi_model="global",
                            phi_s2ss_model=None, sigma_quantile=0.05)

    TOTAL_STDDEV_FILE = \
        "nga_east_total_sigma_tables/GLOBAL_NON_ERGODIC_LOW.csv"


class NGAEastTotalSigmaGlobalNonErgodicCentralTestCase(
        NGAEastTotalSigmaGlobalErgodicLowTestCase):
    GSIM_CLASS = DUMMY_GSIM(tau_model="global", phi_model="global",
                            phi_s2ss_model=None, sigma_quantile=0.50)
    TOTAL_STDDEV_FILE = "nga_east_total_sigma_tables/"\
        "GLOBAL_NON_ERGODIC_CENTRAL.csv"


class NGAEastTotalSigmaGlobalNonErgodicHighTestCase(
        NGAEastTotalSigmaGlobalErgodicLowTestCase):
    GSIM_CLASS = DUMMY_GSIM(tau_model="global", phi_model="global",
                            phi_s2ss_model=None, sigma_quantile=0.95)
    TOTAL_STDDEV_FILE = "nga_east_total_sigma_tables/"\
        "GLOBAL_NON_ERGODIC_HIGH.csv"


# CENA Constant-Phi Non-ergodic Model


class NGAEastTotalSigmaCENAFixedNonErgodicLowTestCase(
        NGAEastTotalSigmaGlobalErgodicLowTestCase):
    GSIM_CLASS = DUMMY_GSIM(tau_model="global", phi_model="cena_constant",
                            phi_s2ss_model=None, sigma_quantile=0.05)
    TOTAL_STDDEV_FILE = "nga_east_total_sigma_tables/"\
        "CENA_CONSTANT_NON_ERGODIC_LOW.csv"


class NGAEastTotalSigmaCENAFixedNonErgodicCentralTestCase(
        NGAEastTotalSigmaGlobalErgodicLowTestCase):
    GSIM_CLASS = DUMMY_GSIM(tau_model="global", phi_model="cena_constant",
                            phi_s2ss_model=None, sigma_quantile=0.50)
    TOTAL_STDDEV_FILE = "nga_east_total_sigma_tables/"\
        "CENA_CONSTANT_NON_ERGODIC_CENTRAL.csv"


class NGAEastTotalSigmaCENAFixedNonErgodicHighTestCase(
        NGAEastTotalSigmaGlobalErgodicLowTestCase):
    GSIM_CLASS = DUMMY_GSIM(tau_model="global", phi_model="cena_constant",
                            phi_s2ss_model=None, sigma_quantile=0.95)
    TOTAL_STDDEV_FILE = "nga_east_total_sigma_tables/"\
        "CENA_CONSTANT_NON_ERGODIC_HIGH.csv"


# CENA Non-ergodic Model


class NGAEastTotalSigmaCENANonErgodicLowTestCase(
        NGAEastTotalSigmaGlobalErgodicLowTestCase):
    GSIM_CLASS = DUMMY_GSIM(tau_model="global", phi_model="cena",
                            phi_s2ss_model=None, sigma_quantile=0.05)
    TOTAL_STDDEV_FILE = "nga_east_total_sigma_tables/CENA_NON_ERGODIC_LOW.csv"


class NGAEastTotalSigmaCENANonErgodicCentralTestCase(
        NGAEastTotalSigmaGlobalErgodicLowTestCase):
    GSIM_CLASS = DUMMY_GSIM(tau_model="global", phi_model="cena",
                            phi_s2ss_model=None, sigma_quantile=0.50)
    TOTAL_STDDEV_FILE = "nga_east_total_sigma_tables/"\
        "CENA_NON_ERGODIC_CENTRAL.csv"


class NGAEastTotalSigmaCENANonErgodicHighTestCase(
        NGAEastTotalSigmaGlobalErgodicLowTestCase):
    GSIM_CLASS = DUMMY_GSIM(tau_model="global", phi_model="cena",
                            phi_s2ss_model=None, sigma_quantile=0.95)
    TOTAL_STDDEV_FILE = "nga_east_total_sigma_tables/CENA_NON_ERGODIC_HIGH.csv"
