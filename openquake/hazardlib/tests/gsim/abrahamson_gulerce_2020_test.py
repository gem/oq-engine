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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Test suite for the Abrahamson & Gulerce (2020) NGA Subduction GMPEs. 

All test tables are generated from Fortran code provided by
Professor Abrahamson
"""

from openquake.hazardlib.gsim.abrahamson_gulerce_2020 import (
    AbrahamsonGulerce2020SInter, AbrahamsonGulerce2020SSlab)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


# Interface - Global
class AbrahamsonGulerce2020SInterTestCase(BaseGSIMTestCase):
    GSIM_CLASS = AbrahamsonGulerce2020SInter
    MEAN_FILE = "ag2020/AG2020_INTERFACE_GLO__MEAN.csv"
    TOTAL_FILE = "ag2020/AG2020_INTERFACE_GLO__TOTAL_STDDEV.csv"
    INTER_FILE = "ag2020/AG2020_INTERFACE_GLO__INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "ag2020/AG2020_INTERFACE_GLO__INTRA_EVENT_STDDEV.csv"
    REG = "GLO"
    ADJ = False
    SIGMA_MU_EPSILON = 0.0

    def test_all(self):
        self.check(self.MEAN_FILE,
                   self.TOTAL_FILE,
                   self.INTER_FILE,
                   self.INTRA_FILE,
                   max_discrep_percentage=0.1,
                   region=self.REG, apply_usa_adjustment=self.ADJ,
                   sigma_mu_epsilon=self.SIGMA_MU_EPSILON)


# Non-ergodic sigma test case
class AbrahamsonGulerce2020SInterNonergodicTestCase(BaseGSIMTestCase):
    GSIM_CLASS = AbrahamsonGulerce2020SInter
    TOTAL_FILE = "ag2020/AG2020_INTERFACE_GLO__NONERGODIC_TOTAL_STDDEV.csv"
    INTRA_FILE =\
        "ag2020/AG2020_INTERFACE_GLO__NONERGODIC_INTRA_EVENT_STDDEV.csv"

    def test_all(self):
        self.check(self.TOTAL_FILE,
                   self.INTRA_FILE,
                   max_discrep_percentage=0.1,
                   ergodic=False)


# Interface - Alaska
class AbrahamsonGulerce2020SInterAlaskaTestCase(
        AbrahamsonGulerce2020SInterTestCase):
    GSIM_CLASS = AbrahamsonGulerce2020SInter
    MEAN_FILE = "ag2020/AG2020_INTERFACE_USA_AK__MEAN.csv"
    TOTAL_FILE = "ag2020/AG2020_INTERFACE_USA_AK__TOTAL_STDDEV.csv"
    INTER_FILE = "ag2020/AG2020_INTERFACE_USA_AK__INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "ag2020/AG2020_INTERFACE_USA_AK__INTRA_EVENT_STDDEV.csv"
    REG = "USA-AK"


# Interface - Alaska (with adjustment)
class AbrahamsonGulerce2020SInterAlaskaAdjustTestCase(
        AbrahamsonGulerce2020SInterTestCase):
    GSIM_CLASS = AbrahamsonGulerce2020SInter
    MEAN_FILE = "ag2020/AG2020_INTERFACE_USA_AK_Adjust_MEAN.csv"
    TOTAL_FILE = "ag2020/AG2020_INTERFACE_USA_AK_Adjust_TOTAL_STDDEV.csv"
    INTER_FILE = "ag2020/AG2020_INTERFACE_USA_AK_Adjust_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "ag2020/AG2020_INTERFACE_USA_AK_Adjust_INTRA_EVENT_STDDEV.csv"
    REG = "USA-AK"
    ADJ = True


# Interface - Cascadia
class AbrahamsonGulerce2020SInterCascadiaTestCase(
        AbrahamsonGulerce2020SInterTestCase):
    GSIM_CLASS = AbrahamsonGulerce2020SInter
    MEAN_FILE = "ag2020/AG2020_INTERFACE_CAS__MEAN.csv"
    TOTAL_FILE = "ag2020/AG2020_INTERFACE_CAS__TOTAL_STDDEV.csv"
    INTER_FILE = "ag2020/AG2020_INTERFACE_CAS__INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "ag2020/AG2020_INTERFACE_CAS__INTRA_EVENT_STDDEV.csv"
    REG = "CAS"


# Interface - Cascadia (with adjustment)
class AbrahamsonGulerce2020SInterCascadiaAdjustTestCase(
        AbrahamsonGulerce2020SInterTestCase):
    GSIM_CLASS = AbrahamsonGulerce2020SInter
    MEAN_FILE = "ag2020/AG2020_INTERFACE_CAS_Adjust_MEAN.csv"
    TOTAL_FILE = "ag2020/AG2020_INTERFACE_CAS_Adjust_TOTAL_STDDEV.csv"
    INTER_FILE = "ag2020/AG2020_INTERFACE_CAS_Adjust_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "ag2020/AG2020_INTERFACE_CAS_Adjust_INTRA_EVENT_STDDEV.csv"
    REG = "CAS"
    ADJ = True


# Interface - Central America & Mexico
class AbrahamsonGulerce2020SInterCAMTestCase(
        AbrahamsonGulerce2020SInterTestCase):
    GSIM_CLASS = AbrahamsonGulerce2020SInter
    MEAN_FILE = "ag2020/AG2020_INTERFACE_CAM__MEAN.csv"
    TOTAL_FILE = "ag2020/AG2020_INTERFACE_CAM__TOTAL_STDDEV.csv"
    INTER_FILE = "ag2020/AG2020_INTERFACE_CAM__INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "ag2020/AG2020_INTERFACE_CAM__INTRA_EVENT_STDDEV.csv"
    REG = "CAM"


# Interface - Japan
class AbrahamsonGulerce2020SInterJapanTestCase(
        AbrahamsonGulerce2020SInterTestCase):
    GSIM_CLASS = AbrahamsonGulerce2020SInter
    MEAN_FILE = "ag2020/AG2020_INTERFACE_JPN__MEAN.csv"
    TOTAL_FILE = "ag2020/AG2020_INTERFACE_JPN__TOTAL_STDDEV.csv"
    INTER_FILE = "ag2020/AG2020_INTERFACE_JPN__INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "ag2020/AG2020_INTERFACE_JPN__INTRA_EVENT_STDDEV.csv"
    REG = "JPN"


# Interface - New Zealand
class AbrahamsonGulerce2020SInterNewZealandTestCase(
        AbrahamsonGulerce2020SInterTestCase):
    GSIM_CLASS = AbrahamsonGulerce2020SInter
    MEAN_FILE = "ag2020/AG2020_INTERFACE_NZL__MEAN.csv"
    TOTAL_FILE = "ag2020/AG2020_INTERFACE_NZL__TOTAL_STDDEV.csv"
    INTER_FILE = "ag2020/AG2020_INTERFACE_NZL__INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "ag2020/AG2020_INTERFACE_NZL__INTRA_EVENT_STDDEV.csv"
    REG = "NZL"


# Interface - South America
class AbrahamsonGulerce2020SInterSouthAmericaTestCase(
        AbrahamsonGulerce2020SInterTestCase):
    GSIM_CLASS = AbrahamsonGulerce2020SInter
    MEAN_FILE = "ag2020/AG2020_INTERFACE_SAM__MEAN.csv"
    TOTAL_FILE = "ag2020/AG2020_INTERFACE_SAM__TOTAL_STDDEV.csv"
    INTER_FILE = "ag2020/AG2020_INTERFACE_SAM__INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "ag2020/AG2020_INTERFACE_SAM__INTRA_EVENT_STDDEV.csv"
    REG = "SAM"


# Interface - Taiwan
class AbrahamsonGulerce2020SInterTaiwanTestCase(
        AbrahamsonGulerce2020SInterTestCase):
    GSIM_CLASS = AbrahamsonGulerce2020SInter
    MEAN_FILE = "ag2020/AG2020_INTERFACE_TWN__MEAN.csv"
    TOTAL_FILE = "ag2020/AG2020_INTERFACE_TWN__TOTAL_STDDEV.csv"
    INTER_FILE = "ag2020/AG2020_INTERFACE_TWN__INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "ag2020/AG2020_INTERFACE_TWN__INTRA_EVENT_STDDEV.csv"
    REG = "TWN"


# ----------------------------------------------------------------------------
# -------------------------  Inslab Models  ----------------------------------
# ----------------------------------------------------------------------------

# In-slab - Global
class AbrahamsonGulerce2020SSlabTestCase(AbrahamsonGulerce2020SInterTestCase):
    GSIM_CLASS = AbrahamsonGulerce2020SSlab
    MEAN_FILE = "ag2020/AG2020_INSLAB_GLO__MEAN.csv"
    TOTAL_FILE = "ag2020/AG2020_INSLAB_GLO__TOTAL_STDDEV.csv"
    INTER_FILE = "ag2020/AG2020_INSLAB_GLO__INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "ag2020/AG2020_INSLAB_GLO__INTRA_EVENT_STDDEV.csv"
    REG = "GLO"


# In-slab - Alaska
class AbrahamsonGulerce2020SSlabAlaskaTestCase(
        AbrahamsonGulerce2020SInterTestCase):
    GSIM_CLASS = AbrahamsonGulerce2020SSlab
    MEAN_FILE = "ag2020/AG2020_INSLAB_USA_AK__MEAN.csv"
    TOTAL_FILE = "ag2020/AG2020_INSLAB_USA_AK__TOTAL_STDDEV.csv"
    INTER_FILE = "ag2020/AG2020_INSLAB_USA_AK__INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "ag2020/AG2020_INSLAB_USA_AK__INTRA_EVENT_STDDEV.csv"
    REG = "USA-AK"


# In-slab - Alaska (with adjustment)
class AbrahamsonGulerce2020SSlabAlaskaAdjustTestCase(
        AbrahamsonGulerce2020SInterTestCase):
    GSIM_CLASS = AbrahamsonGulerce2020SSlab
    MEAN_FILE = "ag2020/AG2020_INSLAB_USA_AK_Adjust_MEAN.csv"
    TOTAL_FILE = "ag2020/AG2020_INSLAB_USA_AK_Adjust_TOTAL_STDDEV.csv"
    INTER_FILE = "ag2020/AG2020_INSLAB_USA_AK_Adjust_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "ag2020/AG2020_INSLAB_USA_AK_Adjust_INTRA_EVENT_STDDEV.csv"
    REG = "USA-AK"
    ADJ = True


# In-slab - Cascadia
class AbrahamsonGulerce2020SSlabCascadiaTestCase(
        AbrahamsonGulerce2020SInterTestCase):
    GSIM_CLASS = AbrahamsonGulerce2020SSlab
    MEAN_FILE = "ag2020/AG2020_INSLAB_CAS__MEAN.csv"
    TOTAL_FILE = "ag2020/AG2020_INSLAB_CAS__TOTAL_STDDEV.csv"
    INTER_FILE = "ag2020/AG2020_INSLAB_CAS__INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "ag2020/AG2020_INSLAB_CAS__INTRA_EVENT_STDDEV.csv"
    REG = "CAS"


# In-slab - Cascadia (with adjustment)
class AbrahamsonGulerce2020SSlabCascadiaAdjustTestCase(
        AbrahamsonGulerce2020SInterTestCase):
    GSIM_CLASS = AbrahamsonGulerce2020SSlab
    MEAN_FILE = "ag2020/AG2020_INSLAB_CAS_Adjust_MEAN.csv"
    TOTAL_FILE = "ag2020/AG2020_INSLAB_CAS_Adjust_TOTAL_STDDEV.csv"
    INTER_FILE = "ag2020/AG2020_INSLAB_CAS_Adjust_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "ag2020/AG2020_INSLAB_CAS_Adjust_INTRA_EVENT_STDDEV.csv"
    REG = "CAS"
    ADJ = True


# In-slab - Central America & Mexico
class AbrahamsonGulerce2020SSlabCAMTestCase(
        AbrahamsonGulerce2020SInterTestCase):
    GSIM_CLASS = AbrahamsonGulerce2020SSlab
    MEAN_FILE = "ag2020/AG2020_INSLAB_CAM__MEAN.csv"
    TOTAL_FILE = "ag2020/AG2020_INSLAB_CAM__TOTAL_STDDEV.csv"
    INTER_FILE = "ag2020/AG2020_INSLAB_CAM__INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "ag2020/AG2020_INSLAB_CAM__INTRA_EVENT_STDDEV.csv"
    REG = "CAM"


# In-slab - Japan
class AbrahamsonGulerce2020SSlabJapanTestCase(
        AbrahamsonGulerce2020SInterTestCase):
    GSIM_CLASS = AbrahamsonGulerce2020SSlab
    MEAN_FILE = "ag2020/AG2020_INSLAB_JPN__MEAN.csv"
    TOTAL_FILE = "ag2020/AG2020_INSLAB_JPN__TOTAL_STDDEV.csv"
    INTER_FILE = "ag2020/AG2020_INSLAB_JPN__INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "ag2020/AG2020_INSLAB_JPN__INTRA_EVENT_STDDEV.csv"
    REG = "JPN"


# In-slab - New Zealand
class AbrahamsonGulerce2020SSlabNewZealandTestCase(
        AbrahamsonGulerce2020SInterTestCase):
    GSIM_CLASS = AbrahamsonGulerce2020SSlab
    MEAN_FILE = "ag2020/AG2020_INSLAB_NZL__MEAN.csv"
    TOTAL_FILE = "ag2020/AG2020_INSLAB_NZL__TOTAL_STDDEV.csv"
    INTER_FILE = "ag2020/AG2020_INSLAB_NZL__INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "ag2020/AG2020_INSLAB_NZL__INTRA_EVENT_STDDEV.csv"
    REG = "NZL"


# In-slab - South America
class AbrahamsonGulerce2020SSlabSouthAmericaTestCase(
        AbrahamsonGulerce2020SInterTestCase):
    GSIM_CLASS = AbrahamsonGulerce2020SSlab
    MEAN_FILE = "ag2020/AG2020_INSLAB_SAM__MEAN.csv"
    TOTAL_FILE = "ag2020/AG2020_INSLAB_SAM__TOTAL_STDDEV.csv"
    INTER_FILE = "ag2020/AG2020_INSLAB_SAM__INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "ag2020/AG2020_INSLAB_SAM__INTRA_EVENT_STDDEV.csv"
    REG = "SAM"


# In-slab - Taiwan
class AbrahamsonGulerce2020SSlabTaiwanTestCase(
        AbrahamsonGulerce2020SInterTestCase):
    GSIM_CLASS = AbrahamsonGulerce2020SSlab
    MEAN_FILE = "ag2020/AG2020_INSLAB_TWN__MEAN.csv"
    TOTAL_FILE = "ag2020/AG2020_INSLAB_TWN__TOTAL_STDDEV.csv"
    INTER_FILE = "ag2020/AG2020_INSLAB_TWN__INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "ag2020/AG2020_INSLAB_TWN__INTRA_EVENT_STDDEV.csv"
    REG = "TWN"

