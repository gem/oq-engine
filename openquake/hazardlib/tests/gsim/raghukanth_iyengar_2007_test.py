# The Hazard Library
# Copyright (C) 2012-2017 GEM Foundation
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
:mod:`openquake.hazardlib.gsim.raghukanth_iyengar_2007_test`
defines
:class:`RaghukanthIyengar2007TestCase`
:class:`RaghukanthIyengar2007KoynaWarnaTestCase`
:class:`RaghukanthIyengar2007SouthernTestCase`
:class:`RaghukanthIyengar2007WesternCentralTestCase`
for testing of
:class:`openquake.hazardlib.gsim.raghukanth_iyengar_2007.RaghukanthIyengar2007`
and subclasses of same.
"""

import warnings
import numpy as np

from openquake.hazardlib import gsim
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

from openquake.hazardlib.gsim.raghukanth_iyengar_2007 import (
    RaghukanthIyengar2007,
    RaghukanthIyengar2007KoynaWarna,
    RaghukanthIyengar2007Southern,
    RaghukanthIyengar2007WesternCentral,
)


class RaghukanthIyengar2007TestCase(BaseGSIMTestCase):
    """
    Mean value data obtained by digitizing Figure 5 using
    http://arohatgi.info/WebPlotDigitizer/app/ .
    """

    GSIM_CLASS = RaghukanthIyengar2007
    MEAN_FILE = 'RAIY07/RAIY07_PI_MEAN.csv'
    SIGMA_FILE = 'RAIY07/RAIY07_PI_STD_TOTAL.csv'
    TOL_PERCENT = 11.

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
        Warning should be thrown for any vs30 below limit for NEHRP class D.
        """

        rctx = gsim.base.RuptureContext()
        sctx = gsim.base.SitesContext()
        dctx = gsim.base.DistancesContext()

        # set reasonable default values
        gmpe = self.GSIM_CLASS()
        rctx.mag = np.array([6.5])
        dctx.rhypo = np.array([100.])
        im_type = sorted(gmpe.COEFFS_BEDROCK.sa_coeffs.keys())[0]
        std_types = list(gmpe.DEFINED_FOR_STANDARD_DEVIATION_TYPES)

        # set critical value to trigger warning
        sctx.vs30 = np.array([170.])

        with warnings.catch_warnings(record=True) as warning_stream:
            warnings.simplefilter('always')

            mean = gmpe.get_mean_and_stddevs(
                sctx, rctx, dctx, im_type, std_types)[0]

            # confirm type and content of warning
            assert len(warning_stream) == 1
            assert issubclass(warning_stream[-1].category, UserWarning)
            assert 'not supported' in str(warning_stream[-1].message).lower()
            assert np.all(np.isnan(mean))


class RaghukanthIyengar2007KoynaWarnaTestCase(RaghukanthIyengar2007TestCase):
    """
    Mean bedrock motions obtained by digitizing Figure 3 using
    http://arohatgi.info/WebPlotDigitizer/app/ .
    """

    GSIM_CLASS = RaghukanthIyengar2007KoynaWarna
    MEAN_FILE = 'RAIY07/RAIY07_KW_MEAN.csv'
    SIGMA_FILE = 'RAIY07/RAIY07_KW_STD_TOTAL.csv'
    TOL_PERCENT = 1.5


class RaghukanthIyengar2007SouthernTestCase(RaghukanthIyengar2007TestCase):
    """
    Mean bedrock motions obtained by digitizing Figure 3 using
    http://arohatgi.info/WebPlotDigitizer/app/ .
    """

    GSIM_CLASS = RaghukanthIyengar2007Southern
    MEAN_FILE = 'RAIY07/RAIY07_SI_MEAN.csv'
    SIGMA_FILE = 'RAIY07/RAIY07_SI_STD_TOTAL.csv'
    TOL_PERCENT = 10.


class RaghukanthIyengar2007WesternCentralTestCase(
        RaghukanthIyengar2007TestCase):
    """
    Mean bedrock motions obtained by digitizing Figure 3 using
    http://arohatgi.info/WebPlotDigitizer/app/ .
    """

    GSIM_CLASS = RaghukanthIyengar2007WesternCentral
    MEAN_FILE = 'RAIY07/RAIY07_WC_MEAN.csv'
    SIGMA_FILE = 'RAIY07/RAIY07_WC_STD_TOTAL.csv'
    TOL_PERCENT = 2.
