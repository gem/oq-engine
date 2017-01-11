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

from openquake.hazardlib.gsim.zhao_2006 import (ZhaoEtAl2006Asc,
                                                ZhaoEtAl2006SInter,
                                                ZhaoEtAl2006SSlab,
                                                ZhaoEtAl2006SInterNSHMP2008,
                                                ZhaoEtAl2006SSlabNSHMP2014,
                                                ZhaoEtAl2006SInterCascadia,
                                                ZhaoEtAl2006SSlabCascadia)
from openquake.hazardlib.gsim.base import (SitesContext, RuptureContext,
                                           DistancesContext)
from openquake.hazardlib.imt import PGA
from openquake.hazardlib.const import StdDev

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

import numpy

# Test data generated from Fortran implementation
# provided by John Zhao
# For the case Vs30 > 1100, test data have been
# generated from Matlab implementation taken from:
# http://www.stanford.edu/~bakerjw/Epsilon/Zhao_2006.m
# (this because the original code provided by Zhao
# does not include this case, even if it is described
# in the original paper)


class ZhaoEtAl2006AscTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ZhaoEtAl2006Asc

    def test_mean(self):
        self.check('ZHAO06/Z06Asc_MEAN.csv',
                   max_discrep_percentage=0.4)

    def test_std_intra(self):
        self.check('ZHAO06/Z06Asc_STD_INTRA.csv',
                   max_discrep_percentage=0.1)

    def test_std_inter(self):
        self.check('ZHAO06/Z06Asc_STD_INTER.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('ZHAO06/Z06Asc_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)

    def test_mean_vs30_greater_than_1100(self):
        self.check('ZHAO06/Z06Asc_MEAN_Vs30_1200.csv',
                   max_discrep_percentage=0.4)


class ZhaoEtAl2006SInterTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ZhaoEtAl2006SInter

    def test_mean(self):
        self.check('ZHAO06/Z06SInter_MEAN.csv',
                   max_discrep_percentage=0.4)

    def test_std_intra(self):
        self.check('ZHAO06/Z06SInter_STD_INTRA.csv',
                   max_discrep_percentage=0.1)

    def test_std_inter(self):
        self.check('ZHAO06/Z06SInter_STD_INTER.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('ZHAO06/Z06SInter_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)

    def test_mean_vs30_greater_than_1100(self):
        self.check('ZHAO06/Z06SInter_MEAN_Vs30_1200.csv',
                   max_discrep_percentage=0.4)


class ZhaoEtAl2006SSlabTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ZhaoEtAl2006SSlab

    def test_mean(self):
        self.check('ZHAO06/Z06SSlab_MEAN.csv',
                   max_discrep_percentage=0.4)

    def test_std_intra(self):
        self.check('ZHAO06/Z06SSlab_STD_INTRA.csv',
                   max_discrep_percentage=0.1)

    def test_std_inter(self):
        self.check('ZHAO06/Z06SSlab_STD_INTER.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('ZHAO06/Z06SSlab_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)

    def test_mean_vs30_greater_than_1100(self):
        self.check('ZHAO06/Z06SSlab_MEAN_Vs30_1200.csv',
                   max_discrep_percentage=0.4)

    def test_zero_distance(self):
        # test the calculation in case of zero rrup distance (for rrup=0
        # the slab correction term has a singularity). In this case the
        # method should return values equal to the ones obtained by
        # replacing 0 values with 0.1
        sctx = SitesContext()
        rctx = RuptureContext()
        dctx = DistancesContext()
        setattr(sctx, 'vs30', numpy.array([800.0, 800.0]))
        setattr(rctx, 'mag', 5.0)
        setattr(rctx, 'rake', 0.0)
        setattr(rctx, 'hypo_depth', 0.0)
        setattr(dctx, 'rrup', numpy.array([0.0, 0.2]))
        mean_0, stds_0 = self.GSIM_CLASS().get_mean_and_stddevs(
            sctx, rctx, dctx, PGA(), [StdDev.TOTAL])
        setattr(dctx, 'rrup', numpy.array([0.1, 0.2]))
        mean_01, stds_01 = self.GSIM_CLASS().get_mean_and_stddevs(
            sctx, rctx, dctx, PGA(), [StdDev.TOTAL])
        numpy.testing.assert_array_equal(mean_0, mean_01)
        numpy.testing.assert_array_equal(stds_0, stds_01)


class ZhaoEtAl2006SInterNSHMP2008TestCase(BaseGSIMTestCase):
    GSIM_CLASS = ZhaoEtAl2006SInterNSHMP2008

    def test_mean(self):
        self.check('ZHAO06/Z06SInterNSHMP_MEAN.csv',
                   max_discrep_percentage=0.52)

    def test_std_total(self):
        self.check('ZHAO06/Z06SInterNSHMP_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)


class ZhaoEtAl2006SSlabNSHMP2014TestCase(BaseGSIMTestCase):
    GSIM_CLASS = ZhaoEtAl2006SSlabNSHMP2014

    def test_mean(self):
        self.check('ZHAO06/ZHAO_SSLAB_NSHMP2014_MEAN.csv',
                   max_discrep_percentage=0.52)


class ZhaoEtal2006SInterCascadiaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ZhaoEtAl2006SInterCascadia

    def test_mean(self):
        self.check("ZHAO06/Z06_GSC_CASCADIA_SINTER_MEAN.csv",
                   max_discrep_percentage=0.1)


class ZhaoEtal2006SSlabCascadiaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = ZhaoEtAl2006SSlabCascadia

    def test_mean(self):
        self.check("ZHAO06/Z06_GSC_CASCADIA_SSLAB_MEAN.csv",
                   max_discrep_percentage=0.1)
