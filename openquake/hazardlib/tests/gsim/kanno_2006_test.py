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
:mod:`openquake.hazardlib.gsim.kanno_2006`
defines
:class:`Kanno2006ShallowTestCase`
:class:`Kanno2006DeepTestCase`
:class:`Kanno2006ShallowNortheastJapanTestCase`
:class:`Kanno2006DeepNortheastJapanTestCase`
for testing of
:class:`openquake.hazardlib.gsim.kanno_2006.Kanno2006Shallow`
and subclasses of same.
"""

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

from openquake.hazardlib.gsim.raghukanth_iyengar_2007 import (
    Kanno2006Shallow,
    Kanno2006Deep,
    Kanno2006ShallowNortheastJapan,
    Kanno2006DeepNortheastJapan,
)


class Kanno2006ShallowTestCase(BaseGSIMTestCase):
    """
    Mean value data obtained by digitizing Figure 5 using
    http://arohatgi.info/WebPlotDigitizer/app/ .
    """

    GSIM_CLASS = Kanno2006Shallow
    MEAN_FILE = 'KNMF06/KNMF06_S_MEAN.csv'
    SIGMA_FILE = 'KNMF06/KNMF06_S_STD_TOTAL.csv'
    TOL_PERCENT = 1.

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


class Kanno2006DeepTestCase(Kanno2006ShallowTestCase):
    # pylint: disable=too-few-public-methods
    """
    Mean bedrock motions obtained by digitizing Figure 3 using
    http://arohatgi.info/WebPlotDigitizer/app/ .
    """

    GSIM_CLASS = Kanno2006Deep
    MEAN_FILE = 'KNMF06/KNMF06_D_MEAN.csv'
    SIGMA_FILE = 'KNMF06/KNMF06_D_STD_TOTAL.csv'


class Kanno2006ShallowNortheastJapanTestCase(Kanno2006ShallowTestCase):
    # pylint: disable=too-few-public-methods
    """
    Mean bedrock motions obtained by digitizing Figure 3 using
    http://arohatgi.info/WebPlotDigitizer/app/ .
    """

    GSIM_CLASS = Kanno2006ShallowNortheastJapan
    MEAN_FILE = 'KNMF06/KNMF06_S_NE_MEAN.csv'
    SIGMA_FILE = 'KNMF06/KNMF06_S_NE_STD_TOTAL.csv'


class Kanno2006DeepNortheastJapanTestCase(Kanno2006ShallowTestCase):
    # pylint: disable=too-few-public-methods
    """
    Mean bedrock motions obtained by digitizing Figure 3 using
    http://arohatgi.info/WebPlotDigitizer/app/ .
    """

    GSIM_CLASS = Kanno2006DeepNortheastJapan
    MEAN_FILE = 'KNMF06/KNMF06_WC_MEAN.csv'
    SIGMA_FILE = 'KNMF06/KNMF06_WC_STD_TOTAL.csv'
