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

from openquake.hazardlib.gsim.mcverry_2006 import (
    McVerry2006Asc,
    McVerry2006SInter,
    McVerry2006SSlab,
    McVerry2006Volc
)

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Test data generated from MS Excel implementation from G. McVerry
# filename: NZSAallTmagwgtcorrected.xls (supplied 11 September 2014)


class McVerry2006AscTestCase(BaseGSIMTestCase):
    GSIM_CLASS = McVerry2006Asc

    def test_mean(self):
        self.check('MCVERRY2006/McVerry2006Asc_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_intra(self):
        self.check('MCVERRY2006/McVerry2006Asc_STD_INTRA.csv',
                   max_discrep_percentage=0.1)

    def test_std_inter(self):
        self.check('MCVERRY2006/McVerry2006Asc_STD_INTER.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('MCVERRY2006/McVerry2006Asc_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)


class McVerry2006SInterTestCase(BaseGSIMTestCase):
    GSIM_CLASS = McVerry2006SInter

    def test_mean(self):
        self.check('MCVERRY2006/McVerry2006SInter_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_intra(self):
        self.check('MCVERRY2006/McVerry2006SInter_STD_INTRA.csv',
                   max_discrep_percentage=0.1)

    def test_std_inter(self):
        self.check('MCVERRY2006/McVerry2006SInter_STD_INTER.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('MCVERRY2006/McVerry2006SInter_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)


class McVerry2006SSlabTestCase(BaseGSIMTestCase):
    GSIM_CLASS = McVerry2006SSlab

    def test_mean(self):
        self.check('MCVERRY2006/McVerry2006SSlab_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_intra(self):
        self.check('MCVERRY2006/McVerry2006SSlab_STD_INTRA.csv',
                   max_discrep_percentage=0.1)

    def test_std_inter(self):
        self.check('MCVERRY2006/McVerry2006SSlab_STD_INTER.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('MCVERRY2006/McVerry2006SSlab_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)


class McVerry2006VolcTestCase(BaseGSIMTestCase):
    GSIM_CLASS = McVerry2006Volc

    def test_mean(self):
        self.check('MCVERRY2006/McVerry2006Volc_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_intra(self):
        self.check('MCVERRY2006/McVerry2006Volc_STD_INTRA.csv',
                   max_discrep_percentage=0.1)

    def test_std_inter(self):
        self.check('MCVERRY2006/McVerry2006Volc_STD_INTER.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('MCVERRY2006/McVerry2006Volc_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)
