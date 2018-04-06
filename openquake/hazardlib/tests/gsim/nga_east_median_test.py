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
Test suite for NGA East GMPEs median value with pre-defined tables.

The median values are taken from Excel tables supplied as an electronic
appendix to:

PEER (2015) "NGA-East: Adjustments to Median Ground-Motion Models for Central
and Eastern North America", Pacific Earthquake Engineering Research Center,
Report Number 2015/08, University of California, Berkeley, August 2015
"""

import openquake.hazardlib.gsim.nga_east as neb
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


# A discrepancy of 0.1 % is tolerated
MAX_DISC = 0.1


# Boore (2015)


class Boore2015NGAEastA04TestCase(BaseGSIMTestCase):
    GSIM_CLASS = neb.Boore2015NGAEastA04
    MEAN_FILE = "nga_east_median_tables/NGAEast_BOORE_A04_J15_MEAN.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE,
                   max_discrep_percentage=MAX_DISC)


class Boore2015NGAEastA04TotalSigmaTestCase(Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.Boore2015NGAEastA04TotalSigma
    MEAN_FILE = "nga_east_median_tables/NGAEast_BOORE_A04_J15_MEAN.csv"


class Boore2015NGAEastAB14TestCase(Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.Boore2015NGAEastAB14
    MEAN_FILE = "nga_east_median_tables/NGAEast_BOORE_AB14_J15_MEAN.csv"


class Boore2015NGAEastAB14TotalSigmaTestCase(Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.Boore2015NGAEastAB14TotalSigma
    MEAN_FILE = "nga_east_median_tables/NGAEast_BOORE_AB14_J15_MEAN.csv"


class Boore2015NGAEastAB95TestCase(Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.Boore2015NGAEastAB95
    MEAN_FILE = "nga_east_median_tables/NGAEast_BOORE_AB95_J15_MEAN.csv"


class Boore2015NGAEastAB95TotalSigmaTestCase(Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.Boore2015NGAEastAB95TotalSigma
    MEAN_FILE = "nga_east_median_tables/NGAEast_BOORE_AB95_J15_MEAN.csv"


class Boore2015NGAEastBCA10DTestCase(Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.Boore2015NGAEastBCA10D
    MEAN_FILE = "nga_east_median_tables/NGAEast_BOORE_BCA10D_J15_MEAN.csv"


class Boore2015NGAEastBCA10DTotalSigmaTestCase(Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.Boore2015NGAEastBCA10DTotalSigma
    MEAN_FILE = "nga_east_median_tables/NGAEast_BOORE_BCA10D_J15_MEAN.csv"


class Boore2015NGAEastBS11TestCase(Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.Boore2015NGAEastBS11
    MEAN_FILE = "nga_east_median_tables/NGAEast_BOORE_BS11_J15_MEAN.csv"


class Boore2015NGAEastBS11TotalSigmaTestCase(Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.Boore2015NGAEastBS11TotalSigma
    MEAN_FILE = "nga_east_median_tables/NGAEast_BOORE_BS11_J15_MEAN.csv"


class Boore2015NGAEastSGD02TestCase(Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.Boore2015NGAEastSGD02
    MEAN_FILE = "nga_east_median_tables/NGAEast_BOORE_SGD02_J15_MEAN.csv"


class Boore2015NGAEastSGD02TotalSigmaTestCase(Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.Boore2015NGAEastSGD02TotalSigma
    MEAN_FILE = "nga_east_median_tables/NGAEast_BOORE_SGD02_J15_MEAN.csv"


# Darragh et al. (2015)


class DarraghEtAl2015NGAEast1CCSPTestCase(Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.DarraghEtAl2015NGAEast1CCSP
    MEAN_FILE = "nga_east_median_tables/NGAEast_DARRAGH_1CCSP_MEAN.csv"


class DarraghEtAl2015NGAEast1CCSPTotalSigmaTestCase(
        Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.DarraghEtAl2015NGAEast1CCSPTotalSigma
    MEAN_FILE = "nga_east_median_tables/NGAEast_DARRAGH_1CCSP_MEAN.csv"


class DarraghEtAl2015NGAEast1CVSPTestCase(Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.DarraghEtAl2015NGAEast1CVSP
    MEAN_FILE = "nga_east_median_tables/NGAEast_DARRAGH_1CVSP_MEAN.csv"


class DarraghEtAl2015NGAEast1CVSPTotalSigmaTestCase(
        Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.DarraghEtAl2015NGAEast1CVSPTotalSigma
    MEAN_FILE = "nga_east_median_tables/NGAEast_DARRAGH_1CVSP_MEAN.csv"


class DarraghEtAl2015NGAEast2CCSPTestCase(Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.DarraghEtAl2015NGAEast2CCSP
    MEAN_FILE = "nga_east_median_tables/NGAEast_DARRAGH_2CCSP_MEAN.csv"


class DarraghEtAl2015NGAEast2CCSPTotalSigmaTestCase(
        Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.DarraghEtAl2015NGAEast2CCSPTotalSigma
    MEAN_FILE = "nga_east_median_tables/NGAEast_DARRAGH_2CCSP_MEAN.csv"


class DarraghEtAl2015NGAEast2CVSPTestCase(Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.DarraghEtAl2015NGAEast2CVSP
    MEAN_FILE = "nga_east_median_tables/NGAEast_DARRAGH_2CVSP_MEAN.csv"


class DarraghEtAl2015NGAEast2CVSPTotalSigmaTestCase(
        Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.DarraghEtAl2015NGAEast2CVSPTotalSigma
    MEAN_FILE = "nga_east_median_tables/NGAEast_DARRAGH_2CVSP_MEAN.csv"


# Yenier & Atkinson (2015)


class YenierAtkinson2015NGAEastTestCase(Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.YenierAtkinson2015NGAEast
    MEAN_FILE = "nga_east_median_tables/NGAEast_YENIER_ATKINSON_MEAN.csv"


class YenierAtkinson2015NGAEastTotalSigmaTestCase(
        Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.YenierAtkinson2015NGAEastTotalSigma
    MEAN_FILE = "nga_east_median_tables/NGAEast_YENIER_ATKINSON_MEAN.csv"


# Pezeschk et al (2015)


class PezeschkEtAl2015NGAEastM1SSTestCase(Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.PezeschkEtAl2015NGAEastM1SS
    MEAN_FILE = "nga_east_median_tables/NGAEast_PEZESCHK_M1SS_MEAN.csv"


class PezeschkEtAl2015NGAEastM1SSTotalSigmaTestCase(
        Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.PezeschkEtAl2015NGAEastM1SSTotalSigma
    MEAN_FILE = "nga_east_median_tables/NGAEast_PEZESCHK_M1SS_MEAN.csv"


class PezeschkEtAl2015NGAEastM2ESTestCase(Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.PezeschkEtAl2015NGAEastM2ES
    MEAN_FILE = "nga_east_median_tables/NGAEast_PEZESCHK_M2ES_MEAN.csv"


class PezeschkEtAl2015NGAEastM2ESTotalSigmaTestCase(
        Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.PezeschkEtAl2015NGAEastM2ESTotalSigma
    MEAN_FILE = "nga_east_median_tables/NGAEast_PEZESCHK_M2ES_MEAN.csv"


# Frankel (2015)


class Frankel2015NGAEastTestCase(Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.Frankel2015NGAEast
    MEAN_FILE = "nga_east_median_tables/NGAEast_FRANKEL_J15_MEAN.csv"


class Frankel2015NGAEastTotalSigmaTestCase(Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.Frankel2015NGAEastTotalSigma
    MEAN_FILE = "nga_east_median_tables/NGAEast_FRANKEL_J15_MEAN.csv"


# Shahjouei & Pezeschk (2015)


class ShahjoueiPezeschk2015NGAEastTestCase(Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.ShahjoueiPezeschk2015NGAEast
    MEAN_FILE = "nga_east_median_tables/NGAEast_SHAHJOUEI_PEZESCHK_MEAN.csv"


class ShahjoueiPezeschk2015NGAEastTotalSigmaTestCase(
        Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.ShahjoueiPezeschk2015NGAEastTotalSigma
    MEAN_FILE = "nga_east_median_tables/NGAEast_SHAHJOUEI_PEZESCHK_MEAN.csv"


# Al Noman & Cramer (2015)


class AlNomanCramer2015NGAEastTestCase(Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.AlNomanCramer2015NGAEast
    MEAN_FILE = "nga_east_median_tables/NGAEast_ALNOMAN_CRAMER_MEAN.csv"


class AlNomanCramer2015NGAEastTotalSigmaTestCase(
        Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.AlNomanCramer2015NGAEastTotalSigma
    MEAN_FILE = "nga_east_median_tables/NGAEast_ALNOMAN_CRAMER_MEAN.csv"


# Gaizer (2015)


class Graizer2015NGAEastTestCase(Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.Graizer2015NGAEast
    MEAN_FILE = "nga_east_median_tables/NGAEast_GRAIZER_MEAN.csv"


class Graizer2015NGAEastTotalSigmaTestCase(
        Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.Graizer2015NGAEastTotalSigma
    MEAN_FILE = "nga_east_median_tables/NGAEast_GRAIZER_MEAN.csv"


# Hassani & Atkinson (2015)


class HassaniAtkinson2015NGAEastTestCase(Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.HassaniAtkinson2015NGAEast
    MEAN_FILE = "nga_east_median_tables/NGAEast_HASSANI_ATKINSON_MEAN.csv"


class HassaniAtkinson2015NGAEastTotalSigmaTestCase(
        Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.HassaniAtkinson2015NGAEastTotalSigma
    MEAN_FILE = "nga_east_median_tables/NGAEast_HASSANI_ATKINSON_MEAN.csv"


# Hollenback et al (2015)


class HollenbackEtAl2015NGAEastGPTestCase(Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.HollenbackEtAl2015NGAEastGP
    MEAN_FILE = "nga_east_median_tables/NGAEast_PEER_GP_MEAN.csv"


class HollenbackEtAl2015NGAEastGPTotalSigmaTestCase(
        Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.HollenbackEtAl2015NGAEastGPTotalSigma
    MEAN_FILE = "nga_east_median_tables/NGAEast_PEER_GP_MEAN.csv"


class HollenbackEtAl2015NGAEastEXTestCase(Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.HollenbackEtAl2015NGAEastEX
    MEAN_FILE = "nga_east_median_tables/NGAEast_PEER_EX_MEAN.csv"


class HollenbackEtAl2015NGAEastEXTotalSigmaTestCase(
        Boore2015NGAEastA04TestCase):
    GSIM_CLASS = neb.HollenbackEtAl2015NGAEastEXTotalSigma
    MEAN_FILE = "nga_east_median_tables/NGAEast_PEER_EX_MEAN.csv"
