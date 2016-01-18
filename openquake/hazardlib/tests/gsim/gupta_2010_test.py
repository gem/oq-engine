# The Hazard Library
# Copyright (C) 2012-2014, GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Module
:mod:`openquake.hazardlib.gsim.gupta_2010`
defines
:class:`Gupta2010SSlabTestCase`
for testing of
:class:`openquake.hazardlib.gsim.gupta_2010.Gupta2010SSlab`
and subclasses of same.
"""

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

from openquake.hazardlib.gsim.gupta_2010 import (
    Gupta2010SSlab,
)


class Gupta2010SSlabTestCase(BaseGSIMTestCase):
    """
    Mean value data obtained by digitizing figures using
    http://arohatgi.info/WebPlotDigitizer/app/ .
    """

    GSIM_CLASS = Gupta2010SSlab
    MEAN_FILES = ['GUPT10/GUPT10_MEAN.csv']
    SIGMA_FILES = ['GUPT10/GUPT10_TOTAL_STDDEV.csv']
    MEAN_TOL = 1.
    SIGMA_TOL = 0.1

    def test_mean(self):
        """
        Ensure that means match reference dataset.
        """
        for mean_file in self.MEAN_FILES:
            self.check(mean_file, max_discrep_percentage=self.MEAN_TOL)

#    def test_std_total(self):
#        """
#        Ensure that standard deviations match reference dataset.
#        """
#        for sigma_file in self.SIGMA_FILES:
#            self.check(sigma_file, max_discrep_percentage=self.SIGMA_TOL)
