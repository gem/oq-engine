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
"""
Test case for the Central and Eastern US (CEUS) models used in the 2019
National Seismic Hazard Map. Tests generated from test tables adopted in USGS
NSHMP software:
https://github.com/usgs/nshmp-haz/tree/master/src/gov/usgs/earthquake/nshmp/gmm/tables
"""
import unittest
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
import openquake.hazardlib.gsim.usgs_ceus_2019 as ceus

# Standard Deviation Models Test Case

MAX_DISCREP = 0.01

class NGAEastUSGSCEUSUncertaintyEPRITestCase(BaseGSIMTestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSeedPEER_EX

    def test_std_intra(self):
        self.check("usgs_ceus_2019/USGS_CEUS_EPRI_INTRA_EVENT_STDDEV.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   sigma_model="EPRI")

    def test_std_inter(self):
        self.check("usgs_ceus_2019/USGS_CEUS_EPRI_INTER_EVENT_STDDEV.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   sigma_model="EPRI")

    def test_std_total(self):
        self.check("usgs_ceus_2019/USGS_CEUS_EPRI_TOTAL_STDDEV.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   sigma_model="EPRI")


class NGAEastUSGSCEUSUncertaintyPANELTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSeedPEER_EX

    def test_std_intra(self):
        self.check("usgs_ceus_2019/USGS_CEUS_PANEL_INTRA_EVENT_STDDEV.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   sigma_model="PANEL")

    def test_std_inter(self):
        self.check("usgs_ceus_2019/USGS_CEUS_PANEL_INTER_EVENT_STDDEV.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   sigma_model="PANEL")

    def test_std_total(self):
        self.check("usgs_ceus_2019/USGS_CEUS_PANEL_TOTAL_STDDEV.csv",
                   max_discrep_percentage=MAX_DISCREP,
                   sigma_model="PANEL")


class UnsupportedSigmaModelTestCase(unittest.TestCase):
    """
    Class to test that the correct error is raised when an unsupported
    aleatory uncertainty model is input
    """
    def setUp(self):
        self.gsim = ceus.NGAEastUSGSSeedPEER_EX

    def test_unsupported_sigma_model(self):
        with self.assertRaises(ValueError) as ve:
            self.gsim(sigma_model="XYZ")
        self.assertEqual(
            str(ve.exception),
            "USGS CEUS Sigma Model XYZ not supported")


# Site Amplification Test Cases
class NGAEastUSGSCEUSSiteAmpMedianTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSeedPEER_EX
    MEAN_FILE = "usgs_ceus_2019/NGAEAST_SITE_MEDIAN_MEAN.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=MAX_DISCREP)


class NGAEastUSGSCEUSSiteAmpPlus1SigmaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSeedPEER_EX
    MEAN_FILE = "usgs_ceus_2019/NGAEAST_SITE_PLUS1EPSILON_MEAN.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=MAX_DISCREP,
                   site_epsilon=1.0)


class NGAEastUSGSCEUSSiteAmpMinus1SigmaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSeedPEER_EX
    MEAN_FILE = "usgs_ceus_2019/NGAEAST_SITE_MINUS1EPSILON_MEAN.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=MAX_DISCREP,
                   site_epsilon=-1.0)

# Mean models Test Cases

class NGAEastUSGSSeedSP15TestCase(BaseGSIMTestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSeedSP15
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSeedSP15_MEAN.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=MAX_DISCREP)


class NGAEastUSGSSeed1CCSPTestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSeed1CCSP
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSeed1CCSP_MEAN.csv"


class NGAEastUSGSSeed2CVSPTestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSeed2CVSP
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSeed2CVSP_MEAN.csv"


class NGAEastUSGSSeed1CVSPTestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSeed1CVSP
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSeed1CVSP_MEAN.csv"


class NGAEastUSGSSeed2CCSPTestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSeed2CCSP
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSeed2CCSP_MEAN.csv"


class NGAEastUSGSSeedGrazierTestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSeedGrazier
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSeedGrazier_MEAN.csv"


class NGAEastUSGSSeedB_ab95TestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSeedB_ab95
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSeedB_ab95_MEAN.csv"


class NGAEastUSGSSeedB_sgd02TestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSeedB_sgd02
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSeedB_sgd02_MEAN.csv"


class NGAEastUSGSSeedB_a04TestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSeedB_a04
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSeedB_a04_MEAN.csv"


class NGAEastUSGSSeedB_bs11TestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSeedB_bs11
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSeedB_bs11_MEAN.csv"


class NGAEastUSGSSeedB_ab14TestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSeedB_ab14
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSeedB_ab14_MEAN.csv"


class NGAEastUSGSSeedHA15TestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSeedHA15
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSeedHA15_MEAN.csv"


class NGAEastUSGSSeedPEER_EXTestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSeedPEER_EX
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSeedPEER_EX_MEAN.csv"


class NGAEastUSGSSeedPEER_GPTestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSeedPEER_GP
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSeedPEER_GP_MEAN.csv"


class NGAEastUSGSSeedGrazier16TestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSeedGrazier16
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSeedGrazier16_MEAN.csv"


class NGAEastUSGSSeedGrazier17TestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSeedGrazier17
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSeedGrazier17_MEAN.csv"


class NGAEastUSGSSeedFrankelTestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSeedFrankel
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSeedFrankel_MEAN.csv"


class NGAEastUSGSSeedYA15TestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSeedYA15
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSeedYA15_MEAN.csv"


class NGAEastUSGSSeedPZCT15_M1SSTestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSeedPZCT15_M1SS
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSeedPZCT15_M1SS_MEAN.csv"


class NGAEastUSGSSeedPZCT15_M2ESTestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSeedPZCT15_M2ES
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSeedPZCT15_M2ES_MEAN.csv"


class NGAEastUSGSSammons1TestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSammons1
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSammons1_MEAN.csv"


class NGAEastUSGSSammons2TestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSammons2
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSammons2_MEAN.csv"


class NGAEastUSGSSammons3TestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSammons3
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSammons3_MEAN.csv"


class NGAEastUSGSSammons4TestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSammons4
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSammons4_MEAN.csv"


class NGAEastUSGSSammons5TestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSammons5
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSammons5_MEAN.csv"


class NGAEastUSGSSammons6TestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSammons6
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSammons6_MEAN.csv"


class NGAEastUSGSSammons7TestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSammons7
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSammons7_MEAN.csv"


class NGAEastUSGSSammons8TestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSammons8
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSammons8_MEAN.csv"


class NGAEastUSGSSammons9TestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSammons9
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSammons9_MEAN.csv"


class NGAEastUSGSSammons10TestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSammons10
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSammons10_MEAN.csv"


class NGAEastUSGSSammons11TestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSammons11
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSammons11_MEAN.csv"


class NGAEastUSGSSammons12TestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSammons12
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSammons12_MEAN.csv"


class NGAEastUSGSSammons13TestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSammons13
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSammons13_MEAN.csv"


class NGAEastUSGSSammons14TestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSammons14
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSammons14_MEAN.csv"


class NGAEastUSGSSammons15TestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSammons15
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSammons15_MEAN.csv"


class NGAEastUSGSSammons16TestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSammons16
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSammons16_MEAN.csv"


class NGAEastUSGSSammons17TestCase(NGAEastUSGSSeedSP15TestCase):
    GSIM_CLASS = ceus.NGAEastUSGSSammons17
    MEAN_FILE = "usgs_ceus_2019/NGAEastUSGSSammons17_MEAN.csv"

