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

    def test_std(self):
        self.check(self.TOTAL_FILE, self.INTER_FILE, self.INTRA_FILE,
                   max_discrep_percentage=0.1)

    def test_mean_mb1(self):
        self.check(
            "kuehn2020/KUEHN2020_INTERFACE_GLOBAL_Mb7.7_MEAN.csv",
            max_discrep_percentage=0.1, m_b=7.7)

    def test_mean_mb2(self):
        self.check(
            "kuehn2020/KUEHN2020_INTERFACE_GLOBAL_Mb8.1_MEAN.csv",
            max_discrep_percentage=0.1, m_b=8.1)

    def test_mean_eps1(self):
        self.check(
            "kuehn2020/KUEHN2020_INTERFACE_GLOBAL_epsilon1_MEAN.csv",
            max_discrep_percentage=0.1, sigma_mu_epsilon=1)

    def test_mean_eps2(self):
        self.check(
            "kuehn2020/KUEHN2020_INTERFACE_GLOBAL_epsilon-1_MEAN.csv",
            max_discrep_percentage=0.1, sigma_mu_epsilon=-1)


# Inslab
class KuehnEtAl2020SSlabTestCase(BaseGSIMTestCase):
    GSIM_CLASS = KuehnEtAl2020SSlab
    MEAN_FILE = "kuehn2020/KUEHN2020_INSLAB_GLOBAL_MEAN.csv"
    TOTAL_FILE = "kuehn2020/KUEHN2020_INSLAB_GLOBAL_TOTAL_STDDEV.csv"
    INTER_FILE = "kuehn2020/KUEHN2020_INSLAB_GLOBAL_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "kuehn2020/KUEHN2020_INSLAB_GLOBAL_INTRA_EVENT_STDDEV.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1)

    def test_std(self):
        self.check(self.TOTAL_FILE, self.INTER_FILE, self.INTRA_FILE,
                   max_discrep_percentage=0.1)

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


class KuehnEtAl2020RegionTestCase(BaseGSIMTestCase):
    FILES = [
        {
            "region": "USA-AK",
            "files": [
                "kuehn2020/KUEHN2020_{}_ALASKA_MEAN.csv",
                "kuehn2020/KUEHN2020_{}_ALASKA_TOTAL_STDDEV.csv",
                "kuehn2020/KUEHN2020_{}_ALASKA_INTER_EVENT_STDDEV.csv",
                "kuehn2020/KUEHN2020_{}_ALASKA_INTRA_EVENT_STDDEV.csv"],
            "sigma": "Origional",
        },
        {
            "region": "CAS",
            "files": [
                "kuehn2020/KUEHN2020_{}_CASCADIA_MEAN.csv",
                "kuehn2020/KUEHN2020_{}_CASCADIA_TOTAL_STDDEV.csv",
                "kuehn2020/KUEHN2020_{}_CASCADIA_INTER_EVENT_STDDEV.csv",
                "kuehn2020/KUEHN2020_{}_CASCADIA_INTRA_EVENT_STDDEV.csv"],
            "sigma": "Origional",
        },
        {
            "region": "CAM",
            "files": [
                "kuehn2020/KUEHN2020_{}_CAM_MEAN.csv",
                "kuehn2020/KUEHN2020_{}_CAM_TOTAL_STDDEV.csv",
                "kuehn2020/KUEHN2020_{}_CAM_INTER_EVENT_STDDEV.csv",
                "kuehn2020/KUEHN2020_{}_CAM_INTRA_EVENT_STDDEV.csv"],
            "sigma": "Origional",
        },
        {
            "region": "JPN",
            "files": [
                "kuehn2020/KUEHN2020_{}_JAPAN_MEAN.csv",
                "kuehn2020/KUEHN2020_{}_JAPAN_TOTAL_STDDEV.csv",
                "kuehn2020/KUEHN2020_{}_JAPAN_INTER_EVENT_STDDEV.csv",
                "kuehn2020/KUEHN2020_{}_JAPAN_INTRA_EVENT_STDDEV.csv"],
            "sigma": "Origional",
        },
        {
            "region": "NZL",
            "files": [
                "kuehn2020/KUEHN20_{}_NZL_GNS_MEAN.csv",
                "kuehn2020/KUEHN20_{}_NZL_GNS_TOTAL_STDDEV_ORIGINAL_SIGMA.csv"],
            "sigma": "Origional",
        },
        {
            "region": "NZL",
            "files": [
                "kuehn2020/KUEHN20_{}_NZL_GNS_MEAN.csv",
                "kuehn2020/KUEHN20_{}_NZL_GNS_TOTAL_STDDEV_MODIFIED_SIGMA.csv"],
            "sigma": "Modified",
        },
        {
            "region": "SAM",
           "files": [
                "kuehn2020/KUEHN2020_{}_SOUTHAMERICA_MEAN.csv",
                "kuehn2020/KUEHN2020_{}_SOUTHAMERICA_TOTAL_STDDEV.csv",
                "kuehn2020/KUEHN2020_{}_SOUTHAMERICA_INTER_EVENT_STDDEV.csv",
                "kuehn2020/KUEHN2020_{}_SOUTHAMERICA_INTRA_EVENT_STDDEV.csv"],
            "sigma": "Origional",
        },
        {
            "region": "TWN",
            "files": [
                "kuehn2020/KUEHN2020_{}_TAIWAN_MEAN.csv",
                "kuehn2020/KUEHN2020_{}_TAIWAN_TOTAL_STDDEV.csv",
                "kuehn2020/KUEHN2020_{}_TAIWAN_INTER_EVENT_STDDEV.csv",
                "kuehn2020/KUEHN2020_{}_TAIWAN_INTRA_EVENT_STDDEV.csv"],
            "sigma": "Origional",
        },
    ]

    def test_all(self):
        for gcls, trt in zip([KuehnEtAl2020SInter, KuehnEtAl2020SSlab],
                             ['INTERFACE', 'INSLAB']):
            self.GSIM_CLASS = gcls
            for test_case in self.FILES:
                region = test_case["region"]
                files = test_case["files"]
                sigma = test_case["sigma"]
                mean_file, *std_files = [f.format(trt) for f in files]
                self.check(mean_file,
                           max_discrep_percentage=0.03, region=region, which_sigma=sigma)
                self.check(*std_files,
                           max_discrep_percentage=0.03, region=region, which_sigma=sigma)
