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

from openquake.hazardlib.gsim.cauzzi_faccioli_2008 import CauzziFaccioli2008

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.gsim.base import (SitesContext, RuptureContext,
                                           DistancesContext)
from openquake.hazardlib.imt import PGA
from openquake.hazardlib.const import StdDev

import numpy

# Test data generated from OpenSHA implementation.

class CauzziFaccioli2008TestCase(BaseGSIMTestCase):
    GSIM_CLASS = CauzziFaccioli2008

    def test_mean(self):
        self.check('CF08/CF08_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std_total(self):
        self.check('CF08/CF08_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)

    def test_rhypo_smaller_than_15(self):
        # test the calculation in case of rhypo distances less than 15 km
        # (for rhypo=0 the distance term has a singularity). In this case the
        # method should return values equal to the ones obtained by clipping
        # distances at 15 km.
        sctx = SitesContext()
        rctx = RuptureContext()
        dctx = DistancesContext()
        setattr(sctx, 'vs30', numpy.array([800.0, 800.0, 800.0]))
        setattr(rctx, 'mag', 5.0)
        setattr(rctx, 'rake', 0.0)
        setattr(dctx, 'rhypo', numpy.array([0.0, 10.0, 16.0]))
        mean_0, stds_0 = self.GSIM_CLASS().get_mean_and_stddevs(
            sctx, rctx, dctx, PGA(), [StdDev.TOTAL])
        setattr(dctx, 'rhypo', numpy.array([15.0, 15.0, 16.0]))
        mean_15, stds_15 = self.GSIM_CLASS().get_mean_and_stddevs(
            sctx, rctx, dctx, PGA(), [StdDev.TOTAL])
        numpy.testing.assert_array_equal(mean_0, mean_15)
        numpy.testing.assert_array_equal(stds_0, stds_15)
