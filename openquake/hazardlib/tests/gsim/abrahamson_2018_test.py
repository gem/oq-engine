# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2018 GEM Foundation
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

from openquake.hazardlib.gsim.abrahamson_2018 import (
    AbrahamsonEtAl2018SInter,
    AbrahamsonEtAl2018SInterHigh,
    AbrahamsonEtAl2018SInterLow,
    AbrahamsonEtAl2018SInterCascadia,
    AbrahamsonEtAl2018SInterCentralAmerica,
    AbrahamsonEtAl2018SInterJapan,
    AbrahamsonEtAl2018SInterNewZealand,
    AbrahamsonEtAl2018SInterSouthAmerica,
    AbrahamsonEtAl2018SInterTaiwan,
    AbrahamsonEtAl2018SSlab,
    AbrahamsonEtAl2018SSlabHigh,
    AbrahamsonEtAl2018SSlabLow,
    AbrahamsonEtAl2018SSlabCascadia,
    AbrahamsonEtAl2018SSlabCentralAmerica,
    AbrahamsonEtAl2018SSlabJapan,
    AbrahamsonEtAl2018SSlabNewZealand,
    AbrahamsonEtAl2018SSlabSouthAmerica,
    AbrahamsonEtAl2018SSlabTaiwan)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class AbrahamsonEtAl2018SInterTestCase(BaseGSIMTestCase):
    GSIM_CLASS = AbrahamsonEtAl2018SInter
    MEAN_FILE = ""

    def test_mean(self):
        self.check(self.MEAN_FILE,
                   max_discrep_percentage=0.1)


class AbrahamsonEtAl2018SigmaTestCase(AbrahamsonEtAl2018SInterTestCase):
    # Same standard deviation model is applied to all models - only test this
    # once
    GSIM_CLASS = AbrahamsonEtAl2018SInter
    TOTAL_FILE = ""
    INTER_FILE = ""
    INTRA_FILE = ""

    def test_mean(self):
        pass

    def test_std_total(self):
        self.check(self.TOTAL_FILE,
                   max_discrep_percentage=0.1)

    def test_std_inter(self):

        self.check(self.INTER_FILE,
                   max_discrep_percentage=0.1)

    def test_std_intra(self):
        self.check(self.INTRA_FILE,
                   max_discrep_percentage=0.1)


class AbrahamsonEtAl2018SInterLowTestCase(AbrahamsonEtAl2018SInterTestCase):
    GSIM_CLASS = AbrahamsonEtAl2018SInterLow
    MEAN_FILE = ""


class AbrahamsonEtAl2018SInterHighTestCase(AbrahamsonEtAl2018SInterTestCase):
    GSIM_CLASS = AbrahamsonEtAl2018SInterHigh
    MEAN_FILE = ""


class AbrahamsonEtAl2018SSlabTestCase(AbrahamsonEtAl2018SInterTestCase):
    GSIM_CLASS = AbrahamsonEtAl2018SSlab
    MEAN_FILE = ""


class AbrahamsonEtAl2018SSlabLowTestCase(AbrahamsonEtAl2018SInterTestCase):
    GSIM_CLASS = AbrahamsonEtAl2018SSlabLow
    MEAN_FILE = ""


class AbrahamsonEtAl2018SSlabHighTestCase(AbrahamsonEtAl2018SInterTestCase):
    GSIM_CLASS = AbrahamsonEtAl2018SSlabHigh
    MEAN_FILE = ""


class AbrahamsonEtAl2018SInterCascadiaTestCase(
        AbrahamsonEtAl2018SInterTestCase):
    GSIM_CLASS = AbrahamsonEtAl2018SInterCascadia
    MEAN_FILE = ""


class AbrahamsonEtAl2018SInterCentralAmericaTestCase(
        AbrahamsonEtAl2018SInterTestCase):
    GSIM_CLASS = AbrahamsonEtAl2018SInterCentralAmerica
    MEAN_FILE = ""


class AbrahamsonEtAl2018SInterJapanTestCase(
        AbrahamsonEtAl2018SInterTestCase):
    GSIM_CLASS = AbrahamsonEtAl2018SInterJapan
    MEAN_FILE = ""


class AbrahamsonEtAl2018SInterNewZealandTestCase(
        AbrahamsonEtAl2018SInterTestCase):
    GSIM_CLASS = AbrahamsonEtAl2018SInterNewZealand
    MEAN_FILE = ""


class AbrahamsonEtAl2018SInterSouthAmericaTestCase(
        AbrahamsonEtAl2018SInterTestCase):
    GSIM_CLASS = AbrahamsonEtAl2018SInterSouthAmerica
    MEAN_FILE = ""


class AbrahamsonEtAl2018SInterTaiwanTestCase(
        AbrahamsonEtAl2018SInterTestCase):
    GSIM_CLASS = AbrahamsonEtAl2018SInterTaiwan
    MEAN_FILE = ""


class AbrahamsonEtAl2018SSlabCascadiaTestCase(
        AbrahamsonEtAl2018SInterTestCase):
    GSIM_CLASS = AbrahamsonEtAl2018SSlabCascadia
    MEAN_FILE = ""


class AbrahamsonEtAl2018SSlabCentralAmericaTestCase(
        AbrahamsonEtAl2018SInterTestCase):
    GSIM_CLASS = AbrahamsonEtAl2018SSlabCentralAmerica
    MEAN_FILE = ""


class AbrahamsonEtAl2018SSlabJapanTestCase(
        AbrahamsonEtAl2018SInterTestCase):
    GSIM_CLASS = AbrahamsonEtAl2018SSlabJapan
    MEAN_FILE = ""


class AbrahamsonEtAl2018SSlabNewZealandTestCase(
        AbrahamsonEtAl2018SInterTestCase):
    GSIM_CLASS = AbrahamsonEtAl2018SSlabNewZealand
    MEAN_FILE = ""


class AbrahamsonEtAl2018SSlabSouthAmericaTestCase(
        AbrahamsonEtAl2018SInterTestCase):
    GSIM_CLASS = AbrahamsonEtAl2018SSlabSouthAmerica
    MEAN_FILE = ""


class AbrahamsonEtAl2018SSlabTaiwanTestCase(
        AbrahamsonEtAl2018SInterTestCase):
    GSIM_CLASS = AbrahamsonEtAl2018SSlabTaiwan
    MEAN_FILE = ""
