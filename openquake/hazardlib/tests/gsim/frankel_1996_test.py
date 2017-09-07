# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
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
    FrankelEtAl1996MwNSHMP2008
)

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.const import StdDev
from openquake.hazardlib.imt import SA
from openquake.hazardlib.gsim.base import (
    SitesContext, RuptureContext, DistancesContext
)

import numpy

# Test data generated from subroutine 'getFEA' in hazgridXnga2.f Fortran code


class FrankelEtAl1996MblgAB1987NSHMP2008TestCase(BaseGSIMTestCase):
    GSIM_CLASS = FrankelEtAl1996MblgAB1987NSHMP2008

    def test_mean(self):
        self.check('FRANKEL1996/FRANKEL96MblgAB1987_MEAN.csv',
                   max_discrep_percentage=1.9)

    def test_std_total(self):
        self.check('FRANKEL1996/FRANKEL96MblgAB1987_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)

    def test_non_supported_imt(self):
        args = [
            object(), object(), object(), SA(period=0.45, damping=5),
            [StdDev.TOTAL]
        ]
        self.assertRaises(
            ValueError,
            self.GSIM_CLASS().get_mean_and_stddevs,
            *args
        )

    def test_mag_dist_outside_range(self):
        sctx = SitesContext()
        rctx = RuptureContext()
        dctx = DistancesContext()

        # rupture with Mw = 3 (Mblg=2.9434938048208452) at rhypo = 1 must give
        # same mean as rupture with Mw = 4.4 (Mblg=4.8927897867183798) at
        # rhypo = 10
        rctx.mag = 2.9434938048208452
        dctx.rhypo = numpy.array([1])
        mean_mw3_d1, _ = self.GSIM_CLASS().get_mean_and_stddevs(
            sctx, rctx, dctx, SA(0.1, 5), [StdDev.TOTAL]
        )

        rctx.mag = 4.8927897867183798
        dctx.rhypo = numpy.array([10])
        mean_mw4pt4_d10, _ = self.GSIM_CLASS().get_mean_and_stddevs(
            sctx, rctx, dctx, SA(0.1, 5), [StdDev.TOTAL]
        )

        self.assertAlmostEqual(float(mean_mw3_d1), float(mean_mw4pt4_d10))

        # rupture with Mw = 9 (Mblg = 8.2093636421088814) at rhypo = 1500 km
        # must give same mean as rupture with Mw = 8.2
        # (Mblg = 7.752253535347597) at rhypo = 1000
        rctx.mag = 8.2093636421088814
        dctx.rhypo = numpy.array([1500.])
        mean_mw9_d1500, _ = self.GSIM_CLASS().get_mean_and_stddevs(
            sctx, rctx, dctx, SA(0.1, 5), [StdDev.TOTAL]
        )

        rctx.mag = 7.752253535347597
        dctx.rhypo = numpy.array([1000.])
        mean_mw8pt2_d1000, _ = self.GSIM_CLASS().get_mean_and_stddevs(
            sctx, rctx, dctx, SA(0.1, 5), [StdDev.TOTAL]
        )

        self.assertAlmostEqual(mean_mw9_d1500, mean_mw8pt2_d1000)

    def test_dist_not_in_increasing_order(self):
        sctx = SitesContext()
        rctx = RuptureContext()
        dctx = DistancesContext()

        rctx.mag = 5.
        dctx.rhypo = numpy.array([150, 100])
        mean_150_100, _ = self.GSIM_CLASS().get_mean_and_stddevs(
            sctx, rctx, dctx, SA(0.1, 5), [StdDev.TOTAL]
        )

        dctx.rhypo = numpy.array([100, 150])
        mean_100_150, _ = self.GSIM_CLASS().get_mean_and_stddevs(
            sctx, rctx, dctx, SA(0.1, 5), [StdDev.TOTAL]
        )
        self.assertAlmostEqual(mean_150_100[1], mean_100_150[0])
        self.assertAlmostEqual(mean_150_100[0], mean_100_150[1])


class FrankelEtAl1996MblgJ1996NSHMP2008TestCase(BaseGSIMTestCase):
    GSIM_CLASS = FrankelEtAl1996MblgJ1996NSHMP2008

    def test_mean(self):
        self.check('FRANKEL1996/FRANKEL96MblgJ1996_MEAN.csv',
                   max_discrep_percentage=2.0)

    def test_std_total(self):
        self.check('FRANKEL1996/FRANKEL96MblgJ1996_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)


class FrankelEtAl1996MwNSHMP2008TestCase(BaseGSIMTestCase):
    GSIM_CLASS = FrankelEtAl1996MwNSHMP2008

    def test_mean(self):
        self.check('FRANKEL1996/FRANKEL96Mw_MEAN.csv',
                   max_discrep_percentage=1.8)

    def test_std_total(self):
        self.check('FRANKEL1996/FRANKEL96Mw_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)
