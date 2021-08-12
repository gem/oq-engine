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
Test case for the Si et al (2020) NGA subduction model.

Test tables generated using R function as published as an electronic
appendix to the original PEER report
"""
from openquake.hazardlib.gsim.si_2020 import (SiEtAl2020SInter,
                                              SiEtAl2020SSlab)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


# Interface
class SiEtAl2020SInterTestCase(BaseGSIMTestCase):
    GSIM_CLASS = SiEtAl2020SInter
    MEAN_FILE = "si2020/SI2020_INTERFACE_MEAN.csv"
    TOTAL_FILE = "si2020/SI2020_INTERFACE_TOTAL_STDDEV.csv"
    INTER_FILE = "si2020/SI2020_INTERFACE_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "si2020/SI2020_INTERFACE_INTRA_EVENT_STDDEV.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check(self.TOTAL_FILE, max_discrep_percentage=0.1)

    def test_std_inter_event(self):
        self.check(self.INTER_FILE, max_discrep_percentage=0.1)

    def test_std_intra_event(self):
        self.check(self.INTRA_FILE, max_discrep_percentage=0.1)


# Intraslab
class SiEtAl2020SSlabTestCase(BaseGSIMTestCase):
    GSIM_CLASS = SiEtAl2020SSlab
    MEAN_FILE = "si2020/SI2020_INTRASLAB_MEAN.csv"
    TOTAL_FILE = "si2020/SI2020_INTRASLAB_TOTAL_STDDEV.csv"
    INTER_FILE = "si2020/SI2020_INTRASLAB_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "si2020/SI2020_INTRASLAB_INTRA_EVENT_STDDEV.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check(self.TOTAL_FILE, max_discrep_percentage=0.1)

    def test_std_inter_event(self):
        self.check(self.INTER_FILE, max_discrep_percentage=0.1)

    def test_std_intra_event(self):
        self.check(self.INTRA_FILE, max_discrep_percentage=0.1)
