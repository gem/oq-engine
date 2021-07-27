# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2021 GEM Foundation
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
Test case for the Kuehn et a (2020) GA subduction model.
Test tables generated using R function as published at
github page (https://github.com/nikuehn/KBCG20)
"""
from openquake.hazardlib.gsim.kuehn_2020 import (KuehnEtAl2020SInter,
                                                 KuehnEtAl2020SSlab)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


# Interface
class KuehnEtAl2020SInterTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KuehnEtAl2020SInter
    MEAN_FILE = "kuehn2020/KUEHN2020_INTERFACE_GLOBAL_MEAN.csv"
    TOTAL_FILE = "kuehn2020/KUEHN2020_INTERFACE_GLOBAL_TOTAL_STDDEV.csv"
    INTER_FILE = "kuehn2020/KUEHN2020_INTERFACE_GLOBAL_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "kuehn2020/KUEHN2020_INTERFACE_GLOBAL_INTRA_EVENT_STDDEV.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check(self.TOTAL_FILE, max_discrep_percentage=0.1)

    def test_std_inter_event(self):
        self.check(self.INTER_FILE, max_discrep_percentage=0.1)

    def test_std_intra_event(self):
        self.check(self.INTRA_FILE, max_discrep_percentage=0.1)

    def test_mean_mb1(self):
        self.check("kuehn2020/KUEHN2020_INTERFACE_GLOBAL_Mb7.7_MEAN.csv",
                   max_discrep_percentage=0.1, m_b=7.7)

    def test_mean_mb2(self):
        self.check("kuehn2020/KUEHN2020_INTERFACE_GLOBAL_Mb8.1_MEAN.csv",
                   max_discrep_percentage=0.1, m_b=8.1)

    def test_mean_eps1(self):
        self.check("kuehn2020/KUEHN2020_INTERFACE_GLOBAL_epsilon1_MEAN.csv",
                   max_discrep_percentage=0.1, sigma_mu_epsilon=1)

    def test_mean_eps2(self):
        self.check("kuehn2020/KUEHN2020_INTERFACE_GLOBAL_epsilon-1_MEAN.csv",
                   max_discrep_percentage=0.1, sigma_mu_epsilon=-1)


# Interface Alaska
class KuehnEtAl2020SInterAlaskaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KuehnEtAl2020SInter
    MEAN_FILE = "kuehn2020/KUEHN2020_INTERFACE_ALASKA_MEAN.csv"
    TOTAL_FILE = "kuehn2020/KUEHN2020_INTERFACE_ALASKA_TOTAL_STDDEV.csv"
    INTER_FILE = "kuehn2020/KUEHN2020_INTERFACE_ALASKA_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "kuehn2020/KUEHN2020_INTERFACE_ALASKA_INTRA_EVENT_STDDEV.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1, region="USA-AK")

    def test_std_total(self):
        self.check(self.TOTAL_FILE, max_discrep_percentage=0.1,
                   region="USA-AK")

    def test_std_inter_event(self):
        self.check(self.INTER_FILE, max_discrep_percentage=0.1,
                   region="USA-AK")

    def test_std_intra_event(self):
        self.check(self.INTRA_FILE, max_discrep_percentage=0.1,
                   region="USA-AK")


# Interface Cascadia
class KuehnEtAl2020SInterCascadiaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KuehnEtAl2020SInter
    MEAN_FILE = "kuehn2020/KUEHN2020_INTERFACE_CASCADIA_MEAN.csv"
    TOTAL_FILE = "kuehn2020/KUEHN2020_INTERFACE_CASCADIA_TOTAL_STDDEV.csv"
    INTER_FILE = \
        "kuehn2020/KUEHN2020_INTERFACE_CASCADIA_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = \
        "kuehn2020/KUEHN2020_INTERFACE_CASCADIA_INTRA_EVENT_STDDEV.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1, region="CAS")

    def test_std_total(self):
        self.check(self.TOTAL_FILE, max_discrep_percentage=0.1, region="CAS")

    def test_std_inter_event(self):
        self.check(self.INTER_FILE, max_discrep_percentage=0.1, region="CAS")

    def test_std_intra_event(self):
        self.check(self.INTRA_FILE, max_discrep_percentage=0.1, region="CAS")


# Interface Central America and Mexico
class KuehnEtAl2020SInterCentralAmericaMexicoTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KuehnEtAl2020SInter
    MEAN_FILE = "kuehn2020/KUEHN2020_INTERFACE_CAM_MEAN.csv"
    TOTAL_FILE = "kuehn2020/KUEHN2020_INTERFACE_CAM_TOTAL_STDDEV.csv"
    INTER_FILE = "kuehn2020/KUEHN2020_INTERFACE_CAM_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "kuehn2020/KUEHN2020_INTERFACE_CAM_INTRA_EVENT_STDDEV.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1, region="CAM")

    def test_std_total(self):
        self.check(self.TOTAL_FILE, max_discrep_percentage=0.1, region="CAM")

    def test_std_inter_event(self):
        self.check(self.INTER_FILE, max_discrep_percentage=0.1, region="CAM")

    def test_std_intra_event(self):
        self.check(self.INTRA_FILE, max_discrep_percentage=0.1, region="CAM")


# Interface Japan
class KuehnEtAl2020SInterJapanTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KuehnEtAl2020SInter
    MEAN_FILE = "kuehn2020/KUEHN2020_INTERFACE_JAPAN_MEAN.csv"
    TOTAL_FILE = "kuehn2020/KUEHN2020_INTERFACE_JAPAN_TOTAL_STDDEV.csv"
    INTER_FILE = "kuehn2020/KUEHN2020_INTERFACE_JAPAN_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "kuehn2020/KUEHN2020_INTERFACE_JAPAN_INTRA_EVENT_STDDEV.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1, region="JPN")

    def test_std_total(self):
        self.check(self.TOTAL_FILE, max_discrep_percentage=0.1, region="JPN",)

    def test_std_inter_event(self):
        self.check(self.INTER_FILE, max_discrep_percentage=0.1, region="JPN")

    def test_std_intra_event(self):
        self.check(self.INTRA_FILE, max_discrep_percentage=0.1, region="JPN")


# Interface New Zealand
class KuehnEtAl2020SInterNewZealandTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KuehnEtAl2020SInter
    MEAN_FILE = "kuehn2020/KUEHN2020_INTERFACE_NEWZEALAND_MEAN.csv"
    TOTAL_FILE = "kuehn2020/KUEHN2020_INTERFACE_NEWZEALAND_TOTAL_STDDEV.csv"
    INTER_FILE = \
        "kuehn2020/KUEHN2020_INTERFACE_NEWZEALAND_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = \
        "kuehn2020/KUEHN2020_INTERFACE_NEWZEALAND_INTRA_EVENT_STDDEV.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1, region="NZL")

    def test_std_total(self):
        self.check(self.TOTAL_FILE, max_discrep_percentage=0.1, region="NZL")

    def test_std_inter_event(self):
        self.check(self.INTER_FILE, max_discrep_percentage=0.1, region="NZL")

    def test_std_intra_event(self):
        self.check(self.INTRA_FILE, max_discrep_percentage=0.1, region="NZL")


# Interface South America
class KuehnEtAl2020SInterSouthAmericaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KuehnEtAl2020SInter
    MEAN_FILE = "kuehn2020/KUEHN2020_INTERFACE_SOUTHAMERICA_MEAN.csv"
    TOTAL_FILE = "kuehn2020/KUEHN2020_INTERFACE_SOUTHAMERICA_TOTAL_STDDEV.csv"
    INTER_FILE = \
        "kuehn2020/KUEHN2020_INTERFACE_SOUTHAMERICA_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = \
        "kuehn2020/KUEHN2020_INTERFACE_SOUTHAMERICA_INTRA_EVENT_STDDEV.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1, region="SAM")

    def test_std_total(self):
        self.check(self.TOTAL_FILE, max_discrep_percentage=0.1, region="SAM")

    def test_std_inter_event(self):
        self.check(self.INTER_FILE, max_discrep_percentage=0.1, region="SAM")

    def test_std_intra_event(self):
        self.check(self.INTRA_FILE, max_discrep_percentage=0.1, region="SAM")


# Interface Taiwan
class KuehnEtAl2020SInterTaiwanTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KuehnEtAl2020SInter
    MEAN_FILE = "kuehn2020/KUEHN2020_INTERFACE_TAIWAN_MEAN.csv"
    TOTAL_FILE = "kuehn2020/KUEHN2020_INTERFACE_TAIWAN_TOTAL_STDDEV.csv"
    INTER_FILE = "kuehn2020/KUEHN2020_INTERFACE_TAIWAN_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "kuehn2020/KUEHN2020_INTERFACE_TAIWAN_INTRA_EVENT_STDDEV.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1, region="TWN")

    def test_std_total(self):
        self.check(self.TOTAL_FILE, max_discrep_percentage=0.1, region="TWN")

    def test_std_inter_event(self):
        self.check(self.INTER_FILE, max_discrep_percentage=0.1, region="TWN")

    def test_std_intra_event(self):
        self.check(self.INTRA_FILE, max_discrep_percentage=0.1, region="TWN")


# Inslab
class KuehnEtAl2020SSlabTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KuehnEtAl2020SSlab
    MEAN_FILE = "kuehn2020/KUEHN2020_INSLAB_GLOBAL_MEAN.csv"
    TOTAL_FILE = "kuehn2020/KUEHN2020_INSLAB_GLOBAL_TOTAL_STDDEV.csv"
    INTER_FILE = "kuehn2020/KUEHN2020_INSLAB_GLOBAL_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "kuehn2020/KUEHN2020_INSLAB_GLOBAL_INTRA_EVENT_STDDEV.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check(self.TOTAL_FILE, max_discrep_percentage=0.1)

    def test_std_inter_event(self):
        self.check(self.INTER_FILE, max_discrep_percentage=0.1)

    def test_std_intra_event(self):
        self.check(self.INTRA_FILE, max_discrep_percentage=0.1)

    def test_mean_mb1(self):
        self.check("kuehn2020/KUEHN2020_INSLAB_GLOBAL_Mb7.4_MEAN.csv",
                   max_discrep_percentage=0.1, m_b=7.4)

    def test_mean_mb2(self):
        self.check("kuehn2020/KUEHN2020_INSLAB_GLOBAL_Mb7.8_MEAN.csv",
                   max_discrep_percentage=0.1, m_b=7.8)

    def test_mean_eps1(self):
        self.check("kuehn2020/KUEHN2020_INSLAB_GLOBAL_epsilon1_MEAN.csv",
                   max_discrep_percentage=0.1, sigma_mu_epsilon=1)

    def test_mean_eps2(self):
        self.check("kuehn2020/KUEHN2020_INSLAB_GLOBAL_epsilon-1_MEAN.csv",
                   max_discrep_percentage=0.1, sigma_mu_epsilon=-1)


# Intraslab Alaska
class KuehnEtAl2020SSlabAlaskaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KuehnEtAl2020SSlab
    MEAN_FILE = "kuehn2020/KUEHN2020_INSLAB_ALASKA_MEAN.csv"
    TOTAL_FILE = "kuehn2020/KUEHN2020_INSLAB_ALASKA_TOTAL_STDDEV.csv"
    INTER_FILE = "kuehn2020/KUEHN2020_INSLAB_ALASKA_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "kuehn2020/KUEHN2020_INSLAB_ALASKA_INTRA_EVENT_STDDEV.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1, region="USA-AK")

    def test_std_total(self):
        self.check(self.TOTAL_FILE, max_discrep_percentage=0.1,
                   region="USA-AK")

    def test_std_inter_event(self):
        self.check(self.INTER_FILE, max_discrep_percentage=0.1,
                   region="USA-AK")

    def test_std_intra_event(self):
        self.check(self.INTRA_FILE, max_discrep_percentage=0.1,
                   region="USA-AK")


# Intraslab Cascadia
class KuehnEtAl2020SSlabCascadiaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KuehnEtAl2020SSlab
    MEAN_FILE = "kuehn2020/KUEHN2020_INSLAB_CASCADIA_MEAN.csv"
    TOTAL_FILE = "kuehn2020/KUEHN2020_INSLAB_CASCADIA_TOTAL_STDDEV.csv"
    INTER_FILE = "kuehn2020/KUEHN2020_INSLAB_CASCADIA_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "kuehn2020/KUEHN2020_INSLAB_CASCADIA_INTRA_EVENT_STDDEV.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1, region="CAS")

    def test_std_total(self):
        self.check(self.TOTAL_FILE, max_discrep_percentage=0.1, region="CAS")

    def test_std_inter_event(self):
        self.check(self.INTER_FILE, max_discrep_percentage=0.1, region="CAS")

    def test_std_intra_event(self):
        self.check(self.INTRA_FILE, max_discrep_percentage=0.1, region="CAS")


# Inslab Central America and Mexico
class KuehnEtAl2020SSlabCentralAmericaMexicoTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KuehnEtAl2020SSlab
    MEAN_FILE = "kuehn2020/KUEHN2020_INSLAB_CAM_MEAN.csv"
    TOTAL_FILE = "kuehn2020/KUEHN2020_INSLAB_CAM_TOTAL_STDDEV.csv"
    INTER_FILE = "kuehn2020/KUEHN2020_INSLAB_CAM_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "kuehn2020/KUEHN2020_INSLAB_CAM_INTRA_EVENT_STDDEV.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1, region="CAM")

    def test_std_total(self):
        self.check(self.TOTAL_FILE, max_discrep_percentage=0.1, region="CAM")

    def test_std_inter_event(self):
        self.check(self.INTER_FILE, max_discrep_percentage=0.1, region="CAM")

    def test_std_intra_event(self):
        self.check(self.INTRA_FILE, max_discrep_percentage=0.1, region="CAM")


# Inslab Japan
class KuehnEtAl2020SSlabJapanTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KuehnEtAl2020SSlab
    MEAN_FILE = "kuehn2020/KUEHN2020_INSLAB_JAPAN_MEAN.csv"
    TOTAL_FILE = "kuehn2020/KUEHN2020_INSLAB_JAPAN_TOTAL_STDDEV.csv"
    INTER_FILE = "kuehn2020/KUEHN2020_INSLAB_JAPAN_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "kuehn2020/KUEHN2020_INSLAB_JAPAN_INTRA_EVENT_STDDEV.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1, region="JPN")

    def test_std_total(self):
        self.check(self.TOTAL_FILE, max_discrep_percentage=0.1, region="JPN")

    def test_std_inter_event(self):
        self.check(self.INTER_FILE, max_discrep_percentage=0.1, region="JPN")

    def test_std_intra_event(self):
        self.check(self.INTRA_FILE, max_discrep_percentage=0.1, region="JPN")


# Inslab New Zealand
class KuehnEtAl2020SSlabNewZealandTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KuehnEtAl2020SSlab
    MEAN_FILE = "kuehn2020/KUEHN2020_INSLAB_NEWZEALAND_MEAN.csv"
    TOTAL_FILE = "kuehn2020/KUEHN2020_INSLAB_NEWZEALAND_TOTAL_STDDEV.csv"
    INTER_FILE = "kuehn2020/KUEHN2020_INSLAB_NEWZEALAND_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "kuehn2020/KUEHN2020_INSLAB_NEWZEALAND_INTRA_EVENT_STDDEV.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1, region="NZL")

    def test_std_total(self):
        self.check(self.TOTAL_FILE, max_discrep_percentage=0.1, region="NZL")

    def test_std_inter_event(self):
        self.check(self.INTER_FILE, max_discrep_percentage=0.1, region="NZL")

    def test_std_intra_event(self):
        self.check(self.INTRA_FILE, max_discrep_percentage=0.1, region="NZL")


# Inslab South America
class KuehnEtAl2020SSlabSouthAmericaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KuehnEtAl2020SSlab
    MEAN_FILE = "kuehn2020/KUEHN2020_INSLAB_SOUTHAMERICA_MEAN.csv"
    TOTAL_FILE = "kuehn2020/KUEHN2020_INSLAB_SOUTHAMERICA_TOTAL_STDDEV.csv"
    INTER_FILE = \
        "kuehn2020/KUEHN2020_INSLAB_SOUTHAMERICA_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = \
        "kuehn2020/KUEHN2020_INSLAB_SOUTHAMERICA_INTRA_EVENT_STDDEV.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1, region="SAM")

    def test_std_total(self):
        self.check(self.TOTAL_FILE, max_discrep_percentage=0.1, region="SAM")

    def test_std_inter_event(self):
        self.check(self.INTER_FILE, max_discrep_percentage=0.1, region="SAM")

    def test_std_intra_event(self):
        self.check(self.INTRA_FILE, max_discrep_percentage=0.1, region="SAM")


# Intraslab Taiwan
class KuehnEtAl2020SSlabTaiwanTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KuehnEtAl2020SSlab
    MEAN_FILE = "kuehn2020/KUEHN2020_INSLAB_TAIWAN_MEAN.csv"
    TOTAL_FILE = "kuehn2020/KUEHN2020_INSLAB_TAIWAN_TOTAL_STDDEV.csv"
    INTER_FILE = "kuehn2020/KUEHN2020_INSLAB_TAIWAN_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "kuehn2020/KUEHN2020_INSLAB_TAIWAN_INTRA_EVENT_STDDEV.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1, region="TWN")

    def test_std_total(self):
        self.check(self.TOTAL_FILE, max_discrep_percentage=0.1, region="TWN")

    def test_std_inter_event(self):
        self.check(self.INTER_FILE, max_discrep_percentage=0.1, region="TWN")

    def test_std_intra_event(self):
        self.check(self.INTRA_FILE, max_discrep_percentage=0.1, region="TWN")
