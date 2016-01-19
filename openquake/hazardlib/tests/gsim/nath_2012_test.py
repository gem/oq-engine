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
:mod:`openquake.hazardlib.gsim.nath_2012_test`
defines
:class:`NathEtAl2012LowerTestCase`
:class:`NathEtAl2012UpperTestCase`
for testing of
:class:`openquake.hazardlib.gsim.nath_2012.NathEtAl2012Lower`
and subclasses of same.
"""

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

from openquake.hazardlib.gsim.nath_2012 import (
    NathEtAl2012Lower,
    NathEtAl2012Upper,
)


class NathEtAl2012LowerTestCase(BaseGSIMTestCase):
    """
    Mean value data obtained by digitizing Figure 5 using
    http://arohatgi.info/WebPlotDigitizer/app/ .
    """

    GSIM_CLASS = NathEtAl2012Lower
    MEAN_FILE = 'NTMN12/NTMN12_L_MEAN.csv'
    SIGMA_FILE = 'NTMN12/NTMN12_L_TOTAL_STDDEV.csv'
    TOL_PERCENT = 4.

    def test_mean(self):
        """
        Ensure that means match reference dataset.
        """
        self.check(self.MEAN_FILE, max_discrep_percentage=self.TOL_PERCENT)

    def test_std_total(self):
        """
        Ensure that standard deviations match reference dataset.
        """
        self.check(self.SIGMA_FILE, max_discrep_percentage=self.TOL_PERCENT)


class NathEtAl2012UpperTestCase(NathEtAl2012LowerTestCase):
    # pylint: disable=too-few-public-methods
    """
    Mean bedrock motions obtained by digitizing Figure 3 using
    http://arohatgi.info/WebPlotDigitizer/app/ .
    """

    GSIM_CLASS = NathEtAl2012Upper
    MEAN_FILE = 'NTMN12/NTMN12_U_MEAN.csv'
    SIGMA_FILE = 'NTMN12/NTMN12_U_TOTAL_STDDEV.csv'
