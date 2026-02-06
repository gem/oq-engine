# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2026 GEM Foundation
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

from openquake.hazardlib.gsim.frankel_1996 import (
    FrankelEtAl1996MblgAB1987NSHMP2008,
    FrankelEtAl1996MblgJ1996NSHMP2008,
    FrankelEtAl1996MwNSHMP2008)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.imt import SA
from openquake.hazardlib.contexts import RuptureContext, simple_cmaker

import numpy

# Test data generated from subroutine 'getFEA' in hazgridXnga2.f Fortran code


class FrankelEtAl1996MblgAB1987NSHMP2008TestCase(BaseGSIMTestCase):
    GSIM_CLASS = FrankelEtAl1996MblgAB1987NSHMP2008

    def test_all(self):
        self.check('FRANKEL1996/FRANKEL96MblgAB1987_MEAN.csv',
                   'FRANKEL1996/FRANKEL96MblgAB1987_STD_TOTAL.csv',
                   max_discrep_percentage=1.9,
                   std_discrep_percentage=0.1)

    def test_non_supported_imt(self):
        ctx = RuptureContext()
        self.assertRaises(
            ValueError,
            self.GSIM_CLASS().compute,
            ctx, [SA(period=0.45)], 0, 0, 0, 0)

    def test_mag_dist_outside_range(self):
        ctx = RuptureContext()
        # rupture with Mw = 3 (Mblg=2.9434938048208452) at rhypo = 1 must give
        # same mean as rupture with Mw = 4.4 (Mblg=4.8927897867183798) at
        # rhypo = 10
        ctx.mag = 2.9434938048208452
        ctx.rhypo = ctx.rrup = numpy.array([1])
        ctx.sids = [0]
        cmaker1 = simple_cmaker([self.GSIM_CLASS()], ["SA(0.1)"])

        out_mw3_d1 = cmaker1.get_mean_stds(
            [cmaker1.recarray([ctx])])[:, 0, 0, :]

        ctx.mag = 4.8927897867183798
        ctx.rhypo = numpy.array([10])

        out_mw4pt4_d10 = cmaker1.get_mean_stds(
            [cmaker1.recarray([ctx])])[:, 0, 0, :]

        self.assertAlmostEqual(float(out_mw3_d1[0]), float(out_mw4pt4_d10[0]))

        # rupture with Mw = 9 (Mblg = 8.2093636421088814) at rhypo = 1500 km
        # must give same mean as rupture with Mw = 8.2
        # (Mblg = 7.752253535347597) at rhypo = 1000
        ctx.mag = 8.2093636421088814
        ctx.rhypo = ctx.rrup = numpy.array([1500.])

        cmaker2 = simple_cmaker([self.GSIM_CLASS()], ["SA(0.1)"])
        
        out_mw9_d1500 = cmaker2.get_mean_stds(
            [cmaker2.recarray([ctx])])[:, 0, 0, :]

        ctx.mag = 7.752253535347597
        ctx.rhypo = numpy.array([1000.])

        out_mw8pt2_d1000 = cmaker2.get_mean_stds(
            [cmaker2.recarray([ctx])])[:, 0, 0, :]

        self.assertAlmostEqual(out_mw9_d1500[0], out_mw8pt2_d1000[0])

    def test_dist_not_in_increasing_order(self):
        ctx = RuptureContext()
        ctx.mag = 5.
        ctx.sids = [0, 1]
        ctx.rhypo = ctx.rrup = numpy.array([150, 100])
        cmaker = simple_cmaker([self.GSIM_CLASS()], ["SA(0.1)"])
        out_150_100 = cmaker.get_mean_stds(
            [cmaker.recarray([ctx])])[:, 0, 0, :]

        ctx.rhypo = numpy.array([100, 150])
        out_100_150 = cmaker.get_mean_stds(
            [cmaker.recarray([ctx])])[:, 0, 0, :]
        
        self.assertAlmostEqual(out_150_100[0][1], out_100_150[0][0])
        self.assertAlmostEqual(out_150_100[0][0], out_100_150[0][1])


class FrankelEtAl1996MblgJ1996NSHMP2008TestCase(BaseGSIMTestCase):
    GSIM_CLASS = FrankelEtAl1996MblgJ1996NSHMP2008

    def test_mean(self):
        self.check('FRANKEL1996/FRANKEL96MblgJ1996_MEAN.csv',
                   'FRANKEL1996/FRANKEL96MblgJ1996_STD_TOTAL.csv',
                   max_discrep_percentage=2.0,
                   std_discrep_percentage=0.1)


class FrankelEtAl1996MwNSHMP2008TestCase(BaseGSIMTestCase):
    GSIM_CLASS = FrankelEtAl1996MwNSHMP2008

    def test_all(self):
        self.check('FRANKEL1996/FRANKEL96Mw_MEAN.csv',
                   'FRANKEL1996/FRANKEL96Mw_STD_TOTAL.csv',
                   max_discrep_percentage=1.8,
                   std_discrep_percentage=0.1)
