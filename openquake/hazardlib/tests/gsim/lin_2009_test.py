# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2017 GEM Foundation
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

from openquake.hazardlib.gsim.lin_2009 import Lin2009, Lin2009AdjustedSigma
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class Lin2009TestCase(BaseGSIMTestCase):
    GSIM_CLASS = Lin2009

    # Test data were obtained from a Fortran implementation
    # provided by the authors.

    def test_mean(self):
        self.check('LIN2009/Lin2009_MEAN.csv',
                   max_discrep_percentage=0.5)

    def test_std_total(self):
        self.check('LIN2009/Lin2009_TOTAL_STDDEV.csv',
                   max_discrep_percentage=0.5)


class Lin2009AdjustedSigmaTestCase(BaseGSIMTestCase):
    GSIM_CLASS = Lin2009AdjustedSigma

    # Test data were obtained from a Fortran implementation
    # provided by the authors with sigma coefficients modified from
    # Table 7 of Cheng et al. (2013):
    # C. -T. Cheng, P. -S. Hsieh, P. -S. Lin, Y. -T. Yen, C. -H. Chan (2013)
    # Probability Seismic Hazard Mapping of Taiwan

    def test_std_total(self):
        self.check('LIN2009/Lin2009AdjustedSigma_TOTAL_STDDEV.csv',
                   max_discrep_percentage=0.5)
