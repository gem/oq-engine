# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2021 GEM Foundation
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

from openquake.hazardlib.gsim.sadigh_1997 import SadighEtAl1997

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.gsim.base import RuptureContext
from openquake.hazardlib.imt import PGA
from openquake.hazardlib.const import StdDev

import numpy


class SadighEtAl1997TestCase(BaseGSIMTestCase):
    GSIM_CLASS = SadighEtAl1997
    # test data was generated using opensha implementation of GMPE.
    # NB: the deep_soil methods are untested!

    def test_mean_rock(self):
        self.check('SADIGH97/SADIGH1997_ROCK_MEAN.csv',
                   max_discrep_percentage=0.4)

    def test_total_stddev_rock(self):
        self.check('SADIGH97/SADIGH1997_ROCK_STD_TOTAL.csv',
                   max_discrep_percentage=1e-10)

    def test_mean_soil(self):
        self.check('SADIGH97/SADIGH1997_SOIL_MEAN.csv',
                   max_discrep_percentage=0.5)

    def test_total_stddev_soil(self):
        self.check('SADIGH97/SADIGH1997_SOIL_STD_TOTAL.csv',
                   max_discrep_percentage=1e-10)

    def test_mag_greater_8pt5(self):
        gmpe = SadighEtAl1997()
        ctx = RuptureContext()
        ctx.rake = 0.0
        ctx.rrup = numpy.array([0., 1.])
        ctx.vs30 = numpy.array([800., 800.])
        ctx.mag = 9.0
        mean_rock_9, _ = gmpe.get_mean_and_stddevs(
            ctx, ctx, ctx, PGA(), [StdDev.TOTAL])
        ctx.mag = 8.5
        mean_rock_8pt5, _ = gmpe.get_mean_and_stddevs(
            ctx, ctx, ctx, PGA(), [StdDev.TOTAL])
        numpy.testing.assert_allclose(mean_rock_9, mean_rock_8pt5)

        ctx.vs30 = numpy.array([300., 300.])
        ctx.mag = 9.0
        mean_soil_9, _ = gmpe.get_mean_and_stddevs(
            ctx, ctx, ctx, PGA(), [StdDev.TOTAL])
        ctx.mag = 8.5
        mean_soil_8pt5, _ = gmpe.get_mean_and_stddevs(
            ctx, ctx, ctx, PGA(), [StdDev.TOTAL])
        numpy.testing.assert_allclose(mean_soil_9, mean_soil_8pt5)
