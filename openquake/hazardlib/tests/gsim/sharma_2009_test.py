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

"""
Module
:mod:`openquake.hazardlib.gsim.sharma_2009_test`
defines
:class:`SharmaEtAl2009TestCase`
for testing of
:class:`openquake.hazardlib.gsim.sharma_2009.SharmaEtAl2009`
"""

import warnings
import numpy as np

from openquake.hazardlib import gsim
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.gsim.sharma_2009 import SharmaEtAl2009


class SharmaEtAl2009TestCase(BaseGSIMTestCase):
    """
    Test data were obtained via personal communications with the
    lead author in the form of an Excel spreadsheet. The most
    significant modification required to obtain the ``MEAN_FILE``
    was to convert from m/s^2 to g. Results were also verified
    against the published versions of Figures 6-9, digitized using
    http://arohatgi.info/WebPlotDigitizer/ app/. Agreement was
    excellent at 0.04 s for all magitudes, distances, mechanisms,
    and site conditions (Figure 6). For other periods (Figures 7-9)
    the results diverged, up to about 20%. Finally, in personal
    communication with the lead author, alternative versions of
    Figures 7-9 were provided which visually match both this
    implementation and the author-generated ``MEAN_FILE`` well.

    There is no plot of residuals as a function of frequency, so
    there's absolutely nothing to verify that against. That said,
    sigma provided is a simple lookup per spectral acceleration
    period.
    """

    GSIM_CLASS = SharmaEtAl2009
    MEAN_FILE = 'SDBK09/SDBK09_MEAN.csv'
    SIGMA_FILE = 'SDBK09/SDBK09_STD_TOTAL.csv'
    TOL_PERCENT = 1e-5

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

    def test_warning(self):
        """
        Warning should be thrown for normal faulting
        """

        rctx = gsim.base.RuptureContext()
        sctx = gsim.base.SitesContext()
        dctx = gsim.base.DistancesContext()

        # set reasonable default values
        gmpe = self.GSIM_CLASS()
        rctx.mag = np.array([6.5])
        dctx.rjb = np.array([100.])
        sctx.vs30 = np.array([2000.])
        im_type = sorted(gmpe.COEFFS.sa_coeffs.keys())[0]
        std_types = list(gmpe.DEFINED_FOR_STANDARD_DEVIATION_TYPES)

        # set critical value to trigger warning
        rctx.rake = np.array([-90.])

        with warnings.catch_warnings(record=True) as warning_stream:
            warnings.simplefilter('always')

            mean = gmpe.get_mean_and_stddevs(
                sctx, rctx, dctx, im_type, std_types)[0]

            # confirm type and content of warning
            assert len(warning_stream) == 1
            assert issubclass(warning_stream[-1].category, UserWarning)
            assert 'not supported' in str(warning_stream[-1].message).lower()
