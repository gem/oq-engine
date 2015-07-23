# The Hazard Library
# Copyright (C) 2015, GEM Foundation
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
Implements the set of tests for the NSHMP adjustments to the NGA West 2
Ground Motion Prediction Equations

Each of the test tables is generated from the original GMPE tables, which are
subsequently modified using the adjustment factors presented in the module
openquake.hazardlib.gsim.nshmp_2014
"""
import unittest
import numpy as np
from openquake.hazardlib.gsim.nshmp_2014 import (
    AbrahamsonEtAl2014NSHMPUpper,
    AbrahamsonEtAl2014NSHMPLower,
    BooreEtAl2014NSHMPUpper,
    BooreEtAl2014NSHMPLower,
    CampbellBozorgnia2014NSHMPUpper,
    CampbellBozorgnia2014NSHMPLower,
    ChiouYoungs2014NSHMPUpper,
    ChiouYoungs2014NSHMPLower,
    Idriss2014NSHMPUpper,
    Idriss2014NSHMPLower,
    nga_west2_epistemic_adjustment)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


# Discrepency percentages to be applied to all tests
MEAN_DISCREP = 0.1
STDDEV_DISCREP = 0.1


class AdjustmentFactorTestCase(unittest.TestCase):
    """
    Tests that the basic adjustment factors are being applied correctly
    """
    def setUp(self):
        """
        Instantiate with three distances
        """
        self.distance = np.array([5.0, 15.0, 50.0])

    def test_good_case(self):
        """
        Basic tests to ensure correct adjustment factors
        """
        # Magnitude < 6.0
        np.testing.assert_array_almost_equal(
            nga_west2_epistemic_adjustment(5.5, self.distance),
            np.array([0.37, 0.22, 0.22]))
        # 6.0 < Magnitude < 7.0
        np.testing.assert_array_almost_equal(
            nga_west2_epistemic_adjustment(6.5, self.distance),
            np.array([0.25, 0.23, 0.23]))
        # Magnitude > 7.0
        np.testing.assert_array_almost_equal(
            nga_west2_epistemic_adjustment(7.5, self.distance),
            np.array([0.40, 0.36, 0.33]))


class ASK14NSHMPUpperTestCase(BaseGSIMTestCase):
    """
    Implements the test case for the positive ('upper') epistemic adjustment
    of the Abrahamson et al. (2014) NGA West 2 GMPE - as adopted for the
    2014 US NSHMP
    """
    GSIM_CLASS = AbrahamsonEtAl2014NSHMPUpper

    # File for the mean results
    MEAN_FILE = "NSHMP2014/ASK14_NSHMP_UPPER_MEAN.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE,
                   max_discrep_percentage=MEAN_DISCREP)


class ASK14NSHMPLowerTestCase(ASK14NSHMPUpperTestCase):
    """
    Implements the test case for the negative ('lower') epistemic adjustment
    of the Abrahamson et al. (2014) NGA West 2 GMPE - as adopted for the
    2014 US NSHMP
    """
    GSIM_CLASS = AbrahamsonEtAl2014NSHMPLower
    MEAN_FILE = "NSHMP2014/ASK14_NSHMP_LOWER_MEAN.csv"


class BSSA14NSHMPUpperTestCase(ASK14NSHMPUpperTestCase):
    """
    Implements the test case for the positive ('upper') epistemic adjustment
    of the Boore et al. (2014) NGA West 2 GMPE - as adopted for the
    2014 US NSHMP
    """
    GSIM_CLASS = BooreEtAl2014NSHMPUpper
    MEAN_FILE = "NSHMP2014/BSSA14_NSHMP_UPPER_MEAN.csv"
    def test_mean(self):
        self.check(self.MEAN_FILE,
                   max_discrep_percentage=2.0)


class BSSA14NSHMPLowerTestCase(ASK14NSHMPUpperTestCase):
    """
    Implements the test case for the negative ('lower') epistemic adjustment
    of the Boore et al. (2014) NGA West 2 GMPE - as adopted for the
    2014 US NSHMP
    """
    GSIM_CLASS = BooreEtAl2014NSHMPLower
    MEAN_FILE = "NSHMP2014/BSSA14_NSHMP_LOWER_MEAN.csv"
    def test_mean(self):
        self.check(self.MEAN_FILE,
                   max_discrep_percentage=2.0)


class CB14NSHMPUpperTestCase(ASK14NSHMPUpperTestCase):
    """
    Implements the test case for the positive ('upper') epistemic adjustment
    of the Campbell & Bozorgnia (2014) NGA West 2 GMPE - as adopted for the
    2014 US NSHMP
    """
    GSIM_CLASS = CampbellBozorgnia2014NSHMPUpper
    MEAN_FILE = "NSHMP2014/CB14_NSHMP_UPPER_MEAN.csv"


class CB14NSHMPLowerTestCase(ASK14NSHMPUpperTestCase):
    """
    Implements the test case for the negative ('lower') epistemic adjustment
    of the Campbell & Bozorgnia (2014) NGA West 2 GMPE - as adopted for the
    2014 US NSHMP
    """
    GSIM_CLASS = CampbellBozorgnia2014NSHMPLower
    MEAN_FILE = "NSHMP2014/CB14_NSHMP_LOWER_MEAN.csv"


class CY14NSHMPUpperTestCase(ASK14NSHMPUpperTestCase):
    """
    Implements the test case for the positive ('upper') epistemic adjustment
    of the Chiou & Youngs (2014) NGA West 2 GMPE - as adopted for the
    2014 US NSHMP
    """
    GSIM_CLASS = ChiouYoungs2014NSHMPUpper
    MEAN_FILE = "NSHMP2014/CY14_NSHMP_UPPER_MEAN.csv"


class CY14NSHMPLowerTestCase(ASK14NSHMPUpperTestCase):
    """
    Implements the test case for the negative ('lower') epistemic adjustment
    of the Chiou & Youngs (2014) NGA West 2 GMPE - as adopted for the
    2014 US NSHMP
    """
    GSIM_CLASS = ChiouYoungs2014NSHMPLower
    MEAN_FILE = "NSHMP2014/CY14_NSHMP_LOWER_MEAN.csv"


class IDRISS14NSHMPUpperTestCase(ASK14NSHMPUpperTestCase):
    """
    Implements the test case for the positive ('upper') epistemic adjustment
    of the Idriss (2014) NGA West 2 GMPE - as adopted for the 2014 US NSHMP
    """
    GSIM_CLASS = Idriss2014NSHMPUpper
    MEAN_FILE = "NSHMP2014/IDRISS14_NSHMP_UPPER_MEAN.csv"


class IDRISS14NSHMPLowerTestCase(ASK14NSHMPUpperTestCase):
    """
    Implements the test case for the negative ('lower') epistemic adjustment
    of the Idriss (2014) NGA West 2 GMPE - as adopted for the 2014 US NSHMP
    """
    GSIM_CLASS = Idriss2014NSHMPLower
    MEAN_FILE = "NSHMP2014/IDRISS14_NSHMP_LOWER_MEAN.csv"
