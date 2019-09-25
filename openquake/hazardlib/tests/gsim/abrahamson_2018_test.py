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
    AbrahamsonEtAl2018SSlab,
    AbrahamsonEtAl2018SSlabHigh,
    AbrahamsonEtAl2018SSlabLow)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


# Interface
class AbrahamsonEtAl2018SInterTestCase(BaseGSIMTestCase):
    GSIM_CLASS = AbrahamsonEtAl2018SInter
    MEAN_FILE = "bchydro18/BCHYDRO2018_INTERFACE_MEAN_NO_ADJUST.csv"
    TOTAL_FILE = "bchydro18/BCHYDRO2018_INTERFACE_TOTAL_STDDEV.csv"
    INTER_FILE = "bchydro18/BCHYDRO2018_INTERFACE_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "bchydro18/BCHYDRO2018_INTERFACE_INTRA_EVENT_STDDEV.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check(self.TOTAL_FILE, max_discrep_percentage=0.1)

    def test_std_inter_event(self):
        self.check(self.INTER_FILE, max_discrep_percentage=0.1)

    def test_std_intra_event(self):
        self.check(self.INTRA_FILE, max_discrep_percentage=0.1)


class AbrahamsonEtAl2018SInterLowTestCase(AbrahamsonEtAl2018SInterTestCase):
    GSIM_CLASS = AbrahamsonEtAl2018SInterLow
    MEAN_FILE = "bchydro18/BCHYDRO2018_INTERFACE_MEAN_LOW_ADJUST.csv"


class AbrahamsonEtAl2018SInterHighTestCase(AbrahamsonEtAl2018SInterTestCase):
    GSIM_CLASS = AbrahamsonEtAl2018SInterHigh
    MEAN_FILE = "bchydro18/BCHYDRO2018_INTERFACE_MEAN_HIGH_ADJUST.csv"


# Inslab
class AbrahamsonEtAl2018SSlabTestCase(BaseGSIMTestCase):
    GSIM_CLASS = AbrahamsonEtAl2018SSlab
    MEAN_FILE = "bchydro18/BCHYDRO2018_INSLAB_MEAN_NO_ADJUST.csv"
    TOTAL_FILE = "bchydro18/BCHYDRO2018_INSLAB_TOTAL_STDDEV.csv"
    INTER_FILE = "bchydro18/BCHYDRO2018_INSLAB_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "bchydro18/BCHYDRO2018_INSLAB_INTRA_EVENT_STDDEV.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check(self.TOTAL_FILE, max_discrep_percentage=0.1)

    def test_std_inter_event(self):
        self.check(self.INTER_FILE, max_discrep_percentage=0.1)

    def test_std_intra_event(self):
        self.check(self.INTRA_FILE, max_discrep_percentage=0.1)


class AbrahamsonEtAl2018SSlabLowTestCase(AbrahamsonEtAl2018SSlabTestCase):
    GSIM_CLASS = AbrahamsonEtAl2018SSlabLow
    MEAN_FILE = "bchydro18/BCHYDRO2018_INSLAB_MEAN_LOW_ADJUST.csv"


class AbrahamsonEtAl2018SSlabHighTestCase(AbrahamsonEtAl2018SSlabTestCase):
    GSIM_CLASS = AbrahamsonEtAl2018SSlabHigh
    MEAN_FILE = "bchydro18/BCHYDRO2018_INSLAB_MEAN_HIGH_ADJUST.csv"
