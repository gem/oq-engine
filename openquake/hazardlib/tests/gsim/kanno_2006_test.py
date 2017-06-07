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

"""
Module
:mod:`openquake.hazardlib.gsim.kanno_2006`
defines
:class:`Kanno2006ShallowTestCase`
:class:`Kanno2006DeepTestCase`
for testing of
:class:`openquake.hazardlib.gsim.kanno_2006.Kanno2006Shallow`
and subclasses of same.
"""

from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

from openquake.hazardlib.gsim.kanno_2006 import (
    Kanno2006Shallow,
    Kanno2006Deep
)


class Kanno2006ShallowTestCase(BaseGSIMTestCase):
    """
    Mean value data obtained by digitizing figures using
    http://arohatgi.info/WebPlotDigitizer/app/ .
    """

    GSIM_CLASS = Kanno2006Shallow
    MEAN_FILES = ['KNMF06/KNMF06_S_MEAN_FIG4.csv',
                  'KNMF06/KNMF06_S_MEAN_FIG5.csv']
    SIGMA_FILES = ['KNMF06/KNMF06_S_TOTAL_STDDEV_FIG4.csv',
                   'KNMF06/KNMF06_S_TOTAL_STDDEV_FIG5.csv']
    MEAN_TOL = 0.15
    SIGMA_TOL = 0.1

    def test_mean(self):
        """
        Ensure that means match reference dataset.
        """
        for mean_file in self.MEAN_FILES:
            self.check(mean_file, max_discrep_percentage=self.MEAN_TOL)

    def test_std_total(self):
        """
        Ensure that standard deviations match reference dataset.
        """
        for sigma_file in self.SIGMA_FILES:
            self.check(sigma_file, max_discrep_percentage=self.SIGMA_TOL)


class Kanno2006DeepTestCase(Kanno2006ShallowTestCase):
    # pylint: disable=too-few-public-methods
    """
    Mean bedrock motions obtained by digitizing figures using
    http://arohatgi.info/WebPlotDigitizer/app/ .
    """

    GSIM_CLASS = Kanno2006Deep
    MEAN_FILES = ['KNMF06/KNMF06_D_MEAN_FIG5.csv',
                  'KNMF06/KNMF06_D_MEAN_FIG5.csv']
    SIGMA_FILES = ['KNMF06/KNMF06_D_TOTAL_STDDEV_FIG4.csv',
                   'KNMF06/KNMF06_D_TOTAL_STDDEV_FIG5.csv']
