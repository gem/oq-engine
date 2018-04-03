# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2018 GEM Foundation
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

from openquake.hazardlib.gsim.zhao_2016 import (
    ZhaoEtAl2016Asc,
    ZhaoEtAl2016AscSiteSigma,
    ZhaoEtAl2016UpperMantle,
    ZhaoEtAl2016UpperMantleSiteSigma,
    ZhaoEtAl2016SInter,
    ZhaoEtAl2016SInterSiteSigma,
    ZhaoEtAl2016SSlab,
    ZhaoEtAl2016SSlabSiteSigma)

# Test data generated from Fortran implementation provided by John Zhao
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Set maximum discrepancy to 0.1%
MAX_DISC = 0.1


# Active shallow crust
class ZhaoEtAl2016AscTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ZhaoEtAl2016Asc

    def test_mean(self):
        self.check('zhao16/zhao_crust_mean.csv',
                   max_discrep_percentage=MAX_DISC)

    def test_std_intra(self):
        self.check('zhao16/zhao_crust_intra_event.csv',
                   max_discrep_percentage=MAX_DISC)

    def test_std_inter(self):
        self.check('zhao16/zhao_crust_inter_event.csv',
                   max_discrep_percentage=MAX_DISC)

    def test_std_total(self):
        self.check('zhao16/zhao_crust_total_sigma.csv',
                   max_discrep_percentage=MAX_DISC)


class ZhaoEtAl2016AscSiteSigmaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ZhaoEtAl2016AscSiteSigma

    # Inter-event standard deviation unchanged from main case - but checking
    def test_std_inter(self):
        self.check('zhao16/zhao_crust_inter_event.csv',
                   max_discrep_percentage=MAX_DISC)

    def test_std_intra(self):
        self.check('zhao16/zhao_crust_intra_event_site.csv',
                   max_discrep_percentage=MAX_DISC)

    def test_std_total(self):
        self.check('zhao16/zhao_crust_total_sigma_site.csv',
                   max_discrep_percentage=MAX_DISC)


# Upper Mantle
class ZhaoEtAl2016UpperMantleTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ZhaoEtAl2016UpperMantle

    def test_mean(self):
        self.check('zhao16/zhao_upper_mantle_mean.csv',
                   max_discrep_percentage=MAX_DISC)

    def test_std_intra(self):
        self.check('zhao16/zhao_upper_mantle_intra_event.csv',
                   max_discrep_percentage=MAX_DISC)

    def test_std_inter(self):
        self.check('zhao16/zhao_upper_mantle_inter_event.csv',
                   max_discrep_percentage=MAX_DISC)

    def test_std_total(self):
        self.check('zhao16/zhao_upper_mantle_total_sigma.csv',
                   max_discrep_percentage=MAX_DISC)


class ZhaoEtAl2016UpperMantleSiteSigmaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ZhaoEtAl2016UpperMantleSiteSigma

    def test_std_inter(self):
        self.check('zhao16/zhao_upper_mantle_inter_event.csv',
                   max_discrep_percentage=MAX_DISC)

    def test_std_intra(self):
        self.check('zhao16/zhao_upper_mantle_intra_event_site.csv',
                   max_discrep_percentage=MAX_DISC)

    def test_std_total(self):
        self.check('zhao16/zhao_upper_mantle_total_sigma_site.csv',
                   max_discrep_percentage=MAX_DISC)


# Subduction Interface
class ZhaoEtAl2016SInterTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ZhaoEtAl2016SInter

    def test_mean(self):
        self.check('zhao16/zhao_subduction_interface_mean.csv',
                   max_discrep_percentage=MAX_DISC)

    def test_std_intra(self):
        self.check('zhao16/zhao_subduction_interface_intra_event.csv',
                   max_discrep_percentage=MAX_DISC)

    def test_std_inter(self):
        self.check('zhao16/zhao_subduction_interface_inter_event.csv',
                   max_discrep_percentage=MAX_DISC)

    def test_std_total(self):
        self.check('zhao16/zhao_subduction_interface_total_sigma.csv',
                   max_discrep_percentage=MAX_DISC)


class ZhaoEtAl2016SInterSiteSigmaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ZhaoEtAl2016SInterSiteSigma

    # Inter-event standard deviation unchanged from main case - but checking
    def test_std_inter(self):
        self.check('zhao16/zhao_subduction_interface_inter_event.csv',
                   max_discrep_percentage=MAX_DISC)

    def test_std_intra(self):
        self.check('zhao16/zhao_subduction_interface_intra_event_site.csv',
                   max_discrep_percentage=MAX_DISC)

    def test_std_total(self):
        self.check('zhao16/zhao_subduction_interface_total_sigma_site.csv',
                   max_discrep_percentage=MAX_DISC)


# Subduction In-slab
class ZhaoEtAl2016SSlabTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ZhaoEtAl2016SSlab

    # Some coefficient rounding errors on very low numbers, increasing
    # tolerable discrepancy
    def test_mean(self):
        self.check('zhao16/zhao_subduction_inslab_mean.csv',
                   max_discrep_percentage=0.3)

    def test_std_intra(self):
        self.check('zhao16/zhao_subduction_inslab_intra_event.csv',
                   max_discrep_percentage=MAX_DISC)

    def test_std_inter(self):
        self.check('zhao16/zhao_subduction_inslab_inter_event.csv',
                   max_discrep_percentage=MAX_DISC)

    def test_std_total(self):
        self.check('zhao16/zhao_subduction_inslab_total_sigma.csv',
                   max_discrep_percentage=MAX_DISC)


class ZhaoEtAl2016SSlabSiteSigmaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ZhaoEtAl2016SSlabSiteSigma

    def test_std_inter(self):
        self.check('zhao16/zhao_subduction_inslab_inter_event.csv',
                   max_discrep_percentage=MAX_DISC)

    def test_std_intra(self):
        self.check('zhao16/zhao_subduction_inslab_intra_event_site.csv',
                   max_discrep_percentage=0.3)

    def test_std_total(self):
        self.check('zhao16/zhao_subduction_inslab_total_sigma_site.csv',
                   max_discrep_percentage=0.3)
