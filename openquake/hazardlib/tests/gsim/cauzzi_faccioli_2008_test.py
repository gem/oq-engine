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

from openquake.hazardlib.gsim.cauzzi_faccioli_2008 import (
    CauzziFaccioli2008, FaccioliEtAl2010)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.gsim.base import RuptureContext
from openquake.hazardlib.imt import PGA
from openquake.hazardlib.const import StdDev

import numpy

# Test data generated from OpenSHA implementation.


class CauzziFaccioli2008TestCase(BaseGSIMTestCase):
    GSIM_CLASS = CauzziFaccioli2008

    def test_all(self):
        self.check('CF08/CF08_MEAN.csv',
                   'CF08/CF08_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)

    def test_rhypo_smaller_than_15(self):
        # test the calculation in case of rhypo distances less than 15 km
        # (for rhypo=0 the distance term has a singularity). In this case the
        # method should return values equal to the ones obtained by clipping
        # distances at 15 km.
        ctx = RuptureContext()
        ctx.rup_id = 0
        ctx.sids = [0, 1, 2]
        ctx.vs30 = numpy.array([800.0, 800.0, 800.0])
        ctx.mag = 5.0
        ctx.rake = 0
        ctx.occurrence_rate = .0001
        ctx.rhypo = numpy.array([0.0, 10.0, 16.0])
        ctx.rrup = numpy.array([0.0, 10.0, 17.0])
        mean_0, stds_0 = self.GSIM_CLASS().get_mean_and_stddevs(
            ctx, ctx, ctx, PGA(), [StdDev.TOTAL])
        mean_15, stds_15 = self.GSIM_CLASS().get_mean_and_stddevs(
            ctx, ctx, ctx, PGA(), [StdDev.TOTAL])
        numpy.testing.assert_array_equal(mean_0, mean_15)
        numpy.testing.assert_array_equal(stds_0, stds_15)


class FaccioliEtAl2010TestCase(BaseGSIMTestCase):
    GSIM_CLASS = FaccioliEtAl2010

    def test_all(self):
        self.check('F10/F10_MEAN.csv',
                   'F10/F10_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)
