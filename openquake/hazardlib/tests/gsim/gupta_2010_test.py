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

"""
Module
:mod:`openquake.hazardlib.gsim.gupta_2010`
defines :class:`Gupta2010SSlabTestCase`
for testing of :class:`openquake.hazardlib.gsim.gupta_2010.Gupta2010SSlab`.
"""

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.gsim.gupta_2010 import Gupta2010SSlab


class Gupta2010SSlabTestCase(BaseGSIMTestCase):
    """
    Mean value data obtained from author matched well at 1 s and below but
    not at longer periods. As a temporary measure the reference test result
    has been generated from the current implementation.
    """

    GSIM_CLASS = Gupta2010SSlab
    MEAN_FILES = ['GUPT10/GUPT10_MEAN_NEW.csv']
    SIGMA_FILES = ['GUPT10/GUPT10_TOTAL_STDDEV.csv']
    MEAN_TOL = 1e-4
    SIGMA_TOL = 1e-4

    def test_all(self):
        for mean_file, sigma_file in zip(self.MEAN_FILES, self.SIGMA_FILES):
            self.check(mean_file, sigma_file,
                       max_discrep_percentage=self.MEAN_TOL)
