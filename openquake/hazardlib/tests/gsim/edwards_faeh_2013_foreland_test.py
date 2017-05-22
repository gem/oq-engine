# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2017 GEM Foundation
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

from openquake.hazardlib.gsim.edwards_fah_2013f import (
    EdwardsFah2013Foreland10Bars,
    EdwardsFah2013Foreland20Bars,
    EdwardsFah2013Foreland30Bars,
    EdwardsFah2013Foreland50Bars,
    EdwardsFah2013Foreland60Bars,
    EdwardsFah2013Foreland75Bars,
    EdwardsFah2013Foreland90Bars,
    EdwardsFah2013Foreland120Bars)

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class EdwardsFah2013Foreland10BarsTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Foreland10Bars

    def test_mean(self):
        self.check('EF13f/for_sd10_table.csv',
                   max_discrep_percentage=0.55)

    def test_std_total(self):
        self.check('EF13f/ef_2013_phis_ss_embeded.csv',
                   max_discrep_percentage=0.80)


class EdwardsFah2013Foreland20BarsTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Foreland20Bars

    def test_mean(self):
        self.check('EF13f/for_sd20_table.csv',
                   max_discrep_percentage=0.55)

    def test_std_total(self):
        self.check('EF13f/ef_2013_phis_ss_embeded.csv',
                   max_discrep_percentage=0.80)


class EdwardsFah2013Foreland30BarsTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Foreland30Bars

    def test_mean(self):
        self.check('EF13f/for_sd30_table.csv',
                   max_discrep_percentage=0.55)

    def test_std_total(self):
        self.check('EF13f/ef_2013_phis_ss_embeded.csv',
                   max_discrep_percentage=0.80)


class EdwardsFah2013Foreland50BarsTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Foreland50Bars

    def test_mean(self):
        self.check('EF13f/for_sd50_table.csv',
                   max_discrep_percentage=0.55)

    def test_std_total(self):
        self.check('EF13f/ef_2013_phis_ss_embeded.csv',
                   max_discrep_percentage=0.80)


class EdwardsFah2013Foreland60BarsTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Foreland60Bars

    def test_mean(self):
        self.check('EF13f/for_sd60_table.csv',
                   max_discrep_percentage=0.55)

    def test_std_total(self):
        self.check('EF13f/ef_2013_phis_ss_embeded.csv',
                   max_discrep_percentage=0.80)


class EdwardsFah2013Foreland75BarsTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Foreland75Bars

    def test_mean(self):
        self.check('EF13f/for_sd75_table.csv',
                   max_discrep_percentage=0.55)

    def test_std_total(self):
        self.check('EF13f/ef_2013_phis_ss_embeded.csv',
                   max_discrep_percentage=0.80)


class EdwardsFah2013Foreland90BarsTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Foreland90Bars

    def test_mean(self):
        self.check('EF13f/for_sd90_table.csv',
                   max_discrep_percentage=0.55)

    def test_std_total(self):
        self.check('EF13f/ef_2013_phis_ss_embeded.csv',
                   max_discrep_percentage=0.80)


class EdwardsFah2013Foreland120BarsTestCase(BaseGSIMTestCase):
    GSIM_CLASS = EdwardsFah2013Foreland120Bars

    def test_mean(self):
        self.check('EF13f/for_sd120_table.csv',
                   max_discrep_percentage=0.55)

    def test_std_total(self):
        self.check('EF13f/ef_2013_phis_ss_embeded.csv',
                   max_discrep_percentage=0.80)