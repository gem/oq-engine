# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2023 GEM Foundation
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

from openquake.hazardlib.gsim.atkinson_boore_2006 import (
    AtkinsonBoore2006, AtkinsonBoore2006Modified2011)
from openquake.hazardlib.gsim.base import RuptureContext
from openquake.hazardlib.imt import PGA
from openquake.hazardlib.const import StdDev

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

import numpy


class AtkinsonBoore2006TestCase(BaseGSIMTestCase):
    GSIM_CLASS = AtkinsonBoore2006

    # Test data generated from Fortran implementation
    # of Dave Boore (http://www.daveboore.com/pubs_online.html)

    def test_mean1(self):
        self.check('AB06/AB06_MEAN.csv',
                   max_discrep_percentage=0.9)

    def test_std_total1(self):
        self.check('AB06/AB06_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)

    def test_zero_distance(self):
        # test the calculation in case of zero rrup distance (for rrup=0
        # the equations have a singularity). In this case the
        # method should return values equal to the ones obtained by
        # replacing 0 values with 1
        ctx = RuptureContext()
        ctx.sids = [0, 1]
        ctx.vs30 = numpy.array([500.0, 2500.0])
        ctx.mag = 5.0
        ctx.src_id = 0
        ctx.rup_id = 0
        ctx.rrup = numpy.array([0.0, 0.2])
        mean_0, stds_0 = self.GSIM_CLASS().get_mean_and_stddevs(
            ctx, ctx, ctx, PGA(), [StdDev.TOTAL])
        ctx.rrup = numpy.array([1.0, 0.2])
        mean_01, stds_01 = self.GSIM_CLASS().get_mean_and_stddevs(
            ctx, ctx, ctx, PGA(), [StdDev.TOTAL])
        numpy.testing.assert_array_equal(mean_0, mean_01)
        numpy.testing.assert_array_equal(stds_0, stds_01)

    # Test data generated from subroutine getAB06 in hazgridXnga2.f

    def test_mean2(self):
        self.check('AB06/AB06MblgAB1987NSHMP140bar_MEAN.csv',
                   max_discrep_percentage=2.1, mag_eq="Mblg87")

    def test_std_total2(self):
        self.check('AB06/AB06MblgAB1987NSHMP140bar_STD_TOTAL.csv',
                   max_discrep_percentage=0.1, mag_eq="Mblg87")

    def test_mean3(self):
        self.check('AB06/AB06MblgJ1996NSHMP140bar_MEAN.csv',
                   max_discrep_percentage=2.2, mag_eq="Mblg96")

    def test_mean4(self):
        self.check('AB06/AB06MwNSHMP140bar_MEAN.csv',
                   max_discrep_percentage=1.9, mag_eq="Mw")

    def test_mean5(self):
        self.check('AB06/AB06MblgAB1987NSHMP200bar_MEAN.csv',
                   max_discrep_percentage=2.1, mag_eq="Mblg87",
                   scale_fac=0.5146)

    # change in stress drop does not affect standard deviation
    def test_std_total5(self):
        self.check('AB06/AB06MblgAB1987NSHMP140bar_STD_TOTAL.csv',
                   max_discrep_percentage=0.1, mag_eq="Mblg87",
                   scale_fac=0.5146)

    def test_mean6(self):
        self.check('AB06/AB06MblgJ1996NSHMP200bar_MEAN.csv',
                   max_discrep_percentage=2.2, mag_eq="Mblg96",
                   scale_fac=0.5146)

    def test_mean7(self):
        self.check('AB06/AB06MwNSHMP200bar_MEAN.csv',
                   max_discrep_percentage=1.9, mag_eq="Mw",
                   scale_fac=0.5146)


class AtkinsonBoore2006Modified2011TestCase(BaseGSIMTestCase):
    GSIM_CLASS = AtkinsonBoore2006Modified2011

    # Test data provided by David M. Boore

    def test_mean(self):
        self.check('AB06/AB06_UPDATE2011_MEAN.csv',
                   max_discrep_percentage=1.0)
