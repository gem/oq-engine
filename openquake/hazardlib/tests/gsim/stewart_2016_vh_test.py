# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2023 GEM Foundation
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
Implements the set of tests for the SBSA15b (V/H) GMPE

Test data are generated from the FORTRAN implementations provided by
David M. Boore (Jul, 2014) in his website:
http://www.daveboore.com/pubs_online/sbsa15_gm_tmr_programs_and_sample_files.zip
and http://www.daveboore.com/pubs_online/bssa14_gm_tmr_programs_and_sample_files.zip
and supplementary material for referenced Earthquake Spectra paper by
Bozorgnia and Campbell for V/H standard deviations.

Input test cases based on SBSA15 GMPE tests
"""
import openquake.hazardlib.gsim.stewart_2016_vh as SBSAb
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

# Test Case A:
#   Every combination of the following is asserted for the test suite:
#     IMT = {Sa(0.010, 0.020, 0.022, 0.025, 0.029, 0.030, 0.032, 0.035, 0.036,
#               0.040, 0.042, 0.044, 0.045, 0.046, 0.048, 0.050, 0.055, 0.060,
#               0.065, 0.067, 0.070, 0.075, 0.080, 0.085, 0.090, 0.095, 0.100,
#               0.110, 0.120, 0.130, 0.133, 0.140, 0.150, 0.160, 0.170, 0.180,
#               0.190, 0.200, 0.220, 0.240, 0.250, 0.260, 0.280, 0.290, 0.300,
#               0.320, 0.340, 0.350, 0.360, 0.380, 0.400, 0.420, 0.440, 0.450,
#               0.460, 0.480, 0.500, 0.550, 0.600, 0.650, 0.667, 0.700, 0.750,
#               0.800, 0.850, 0.900, 0.950, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6,
#               1.7, 1.8, 1.9, 2.0, 2.2, 2.4, 2.5, 2.6, 2.8, 3.0, 3.2, 3.4,
#               3.5, 3.6, 3.8, 4.0, 4.2, 4.4, 4.6, 4.8, 5.0, 5.5, 6.0, 6.5,
#               7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0)}
#       M =     {3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 8.5}
#       rake =  {0, -90, 90}
#               + another set of test cases for unspecified rake
#       Rjb =   {20.0}
#       Vs30 =  {200, 760}
# Test Case B:
#   Every combination of the following is asserted for the test suite:
#     IMT = {pgv, pga, Sa(0.1), Sa(0.2), Sa(1.0), Sa(3.0), Sa(10.0)}
#       M =     {4.0, 5.0, 6.0, 7.0, 8.0, 8.5}
#       rake =  {0, -90, 90}
#               + special set of test cases for unspecified rake
#       Rjb =   {0.10, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.17, 0.19, 0.20,
#                0.22, 0.23, 0.25, 0.27, 0.29, 0.32, 0.34, 0.37, 0.40, 0.43,
#                0.46, 0.50, 0.54, 0.58, 0.63, 0.68, 0.74, 0.80, 0.86, 0.93,
#                1.00, 1.08, 1.17, 1.26, 1.36, 1.47, 1.59, 1.71, 1.85, 2.00,
#                2.16, 2.33, 2.51, 2.72, 2.93, 3.17, 3.42, 3.69, 3.99, 4.30,
#                4.65, 5.02, 5.42, 5.85, 6.32, 6.82, 7.37, 7.95, 8.59, 9.27,
#                10.0, 10.8, 11.7, 12.6, 13.6, 14.7, 15.9, 17.1, 18.5, 20.0,
#                21.6, 23.3, 25.2, 27.2, 29.3, 31.7, 34.2, 36.9, 39.9, 43.1,
#                46.5, 50.2, 54.2, 58.6, 63.2, 68.3, 73.7, 79.6, 86.0, 92.8,
#                100, 108, 117, 126, 136, 147, 159, 172, 185, 200}
#       Vs30 =  {760}

# Discrepency percentages to be applied to all tests
MEAN_DISCREP = 0.5
STDDEV_DISCREP = 0.1


class StewartEtAl2016VHTestCaseA(BaseGSIMTestCase):
    """
    Tests the Stewart et al. (2016) V/H GMPE for the "global {default}"
    conditions: Style of faulting included - "Global" Q model
    """
    GSIM_CLASS = SBSAb.StewartEtAl2016VH

    # File containing results for the mean
    MEAN_FILE = "SBSA15b/SBSA15b_CAL_PERIOD_MEAN.csv"
    # File containing results for the total standard deviation
    STD_FILE = "SBSA15b/SBSA15b_CAL_PERIOD_TOTAL_STD.csv"
    # File containing results for the inter-event standard deviation
    INTER_FILE = "SBSA15b/SBSA15b_CAL_PERIOD_INTER_STD.csv"
    # File containing results for the intra-event standard deviation
    INTRA_FILE = "SBSA15b/SBSA15b_CAL_PERIOD_INTRA_STD.csv"

    def test_all(self):
        self.check(self.MEAN_FILE, self.STD_FILE,
                   self.INTER_FILE, self.INTRA_FILE,
                   max_discrep_percentage=MEAN_DISCREP,
                   std_discrep_percentage=STDDEV_DISCREP)


class StewartEtAl2016VHTestCaseB(StewartEtAl2016VHTestCaseA):
    """
    Tests the Stewart et al. (2016) V/H GMPE for the "global {default}"
    conditions: Style of faulting included - "Global" Q model
    """
    GSIM_CLASS = SBSAb.StewartEtAl2016VH

    # File containing results for the mean
    MEAN_FILE = "SBSA15b/SBSA15b_CAL_RJB_MEAN.csv"
    # File containing results for the total standard deviation
    STD_FILE = "SBSA15b/SBSA15b_CAL_RJB_TOTAL_STD.csv"
    # File containing results for the inter-event standard deviation
    INTER_FILE = "SBSA15b/SBSA15b_CAL_RJB_INTER_STD.csv"
    # File containing results for the intra-event standard deviation
    INTRA_FILE = "SBSA15b/SBSA15b_CAL_RJB_INTRA_STD.csv"


class StewartEtAl2016RegCHNVHTestCaseA(StewartEtAl2016VHTestCaseA):
    """
    Tests the Stewart et al. (2016) V/H GMPE for the conditions:
    Style of faulting included - High Q (China)
    """
    GSIM_CLASS = SBSAb.StewartEtAl2016RegCHNVH

    # File containing results for the mean
    MEAN_FILE = "SBSA15b/SBSA15b_CHN_PERIOD_MEAN.csv"
    # File containing results for the total standard deviation
    STD_FILE = "SBSA15b/SBSA15b_CHN_PERIOD_TOTAL_STD.csv"
    # File containing results for the inter-event standard deviation
    INTER_FILE = "SBSA15b/SBSA15b_CHN_PERIOD_INTER_STD.csv"
    # File containing results for the intra-event standard deviation
    INTRA_FILE = "SBSA15b/SBSA15b_CHN_PERIOD_INTRA_STD.csv"


class StewartEtAl2016RegCHNVHTestCaseB(StewartEtAl2016VHTestCaseA):
    """
    Tests the Stewart et al. (2016) V/H GMPE for the conditions:
    Style of faulting included - High Q (China)
    """
    GSIM_CLASS = SBSAb.StewartEtAl2016RegCHNVH

    # File containing results for the mean
    MEAN_FILE = "SBSA15b/SBSA15b_CHN_RJB_MEAN.csv"
    # File containing results for the total standard deviation
    STD_FILE = "SBSA15b/SBSA15b_CHN_RJB_TOTAL_STD.csv"
    # File containing results for the inter-event standard deviation
    INTER_FILE = "SBSA15b/SBSA15b_CHN_RJB_INTER_STD.csv"
    # File containing results for the intra-event standard deviation
    INTRA_FILE = "SBSA15b/SBSA15b_CHN_RJB_INTRA_STD.csv"


class StewartEtAl2016RegJPNVHTestCaseA(StewartEtAl2016VHTestCaseA):
    """
    Tests the Stewart et al. (2016) V/H GMPE for the conditions:
    Style of faulting included - Low Q (Japan)
    """
    GSIM_CLASS = SBSAb.StewartEtAl2016RegJPNVH

    # File containing results for the mean
    MEAN_FILE = "SBSA15b/SBSA15b_JPN_PERIOD_MEAN.csv"
    # File containing results for the total standard deviation
    STD_FILE = "SBSA15b/SBSA15b_JPN_PERIOD_TOTAL_STD.csv"
    # File containing results for the inter-event standard deviation
    INTER_FILE = "SBSA15b/SBSA15b_JPN_PERIOD_INTER_STD.csv"
    # File containing results for the intra-event standard deviation
    INTRA_FILE = "SBSA15b/SBSA15b_JPN_PERIOD_INTRA_STD.csv"


class StewartEtAl2016RegJPNVHTestCaseB(StewartEtAl2016VHTestCaseA):
    """
    Tests the Stewart et al. (2016) V/H GMPE for the conditions:
    Style of faulting included - Low Q (Japan)
    """
    GSIM_CLASS = SBSAb.StewartEtAl2016RegJPNVH

    # File containing results for the mean
    MEAN_FILE = "SBSA15b/SBSA15b_JPN_RJB_MEAN.csv"
    # File containing results for the total standard deviation
    STD_FILE = "SBSA15b/SBSA15b_JPN_RJB_TOTAL_STD.csv"
    # File containing results for the inter-event standard deviation
    INTER_FILE = "SBSA15b/SBSA15b_JPN_RJB_INTER_STD.csv"
    # File containing results for the intra-event standard deviation
    INTRA_FILE = "SBSA15b/SBSA15b_JPN_RJB_INTRA_STD.csv"

# //////////////////////////////////////////////////////////////////////////
# ---------------------- Excluding Style-of-faulting-----------------------
# //////////////////////////////////////////////////////////////////////////


class StewartEtAl2016NoSOFVHTestCaseA(StewartEtAl2016VHTestCaseA):
    """
    Tests the Stewart et al. (2016) V/H GMPE for the conditions:
    No style of faulting - "Global" Q model
    """
    GSIM_CLASS = SBSAb.StewartEtAl2016NoSOFVH

    # File containing results for the mean
    MEAN_FILE = "SBSA15b/SBSA15b_CAL_PERIOD_MEAN_NOSOF.csv"
    # File containing results for the total standard deviation
    STD_FILE = "SBSA15b/SBSA15b_CAL_PERIOD_TOTAL_STD_NOSOF.csv"
    # File containing results for the inter-event standard deviation
    INTER_FILE = "SBSA15b/SBSA15b_CAL_PERIOD_INTER_STD_NOSOF.csv"
    # File containing results for the intra-event standard deviation
    INTRA_FILE = "SBSA15b/SBSA15b_CAL_PERIOD_INTRA_STD_NOSOF.csv"


class StewartEtAl2016NoSOFVHTestCaseB(StewartEtAl2016VHTestCaseA):
    """
    Tests the Stewart et al. (2016) V/H GMPE for the conditions:
    No style of faulting - "Global" Q model
    """
    GSIM_CLASS = SBSAb.StewartEtAl2016NoSOFVH

    # File containing results for the mean
    MEAN_FILE = "SBSA15b/SBSA15b_CAL_RJB_MEAN_NOSOF.csv"
    # File containing results for the total standard deviation
    STD_FILE = "SBSA15b/SBSA15b_CAL_RJB_TOTAL_STD_NOSOF.csv"
    # File containing results for the inter-event standard deviation
    INTER_FILE = "SBSA15b/SBSA15b_CAL_RJB_INTER_STD_NOSOF.csv"
    # File containing results for the intra-event standard deviation
    INTRA_FILE = "SBSA15b/SBSA15b_CAL_RJB_INTRA_STD_NOSOF.csv"


class StewartEtAl2016RegCHNNoSOFVHTestCaseA(StewartEtAl2016VHTestCaseA):
    """
    Tests the Stewart et al. (2016) V/H GMPE for the conditions:
    No style of faulting - High Q (China)
    """
    GSIM_CLASS = SBSAb.StewartEtAl2016RegCHNNoSOFVH

    # File containing results for the mean
    MEAN_FILE = "SBSA15b/SBSA15b_CHN_PERIOD_MEAN_NOSOF.csv"
    # File containing results for the total standard deviation
    STD_FILE = "SBSA15b/SBSA15b_CHN_PERIOD_TOTAL_STD_NOSOF.csv"
    # File containing results for the inter-event standard deviation
    INTER_FILE = "SBSA15b/SBSA15b_CHN_PERIOD_INTER_STD_NOSOF.csv"
    # File containing results for the intra-event standard deviation
    INTRA_FILE = "SBSA15b/SBSA15b_CHN_PERIOD_INTRA_STD_NOSOF.csv"


class StewartEtAl2016RegCHNNoSOFVHTestCaseB(StewartEtAl2016VHTestCaseA):
    """
    Tests the Stewart et al. (2016) V/H GMPE for the conditions:
    No style of faulting - High Q (China)
    """
    GSIM_CLASS = SBSAb.StewartEtAl2016RegCHNNoSOFVH

    # File containing results for the mean
    MEAN_FILE = "SBSA15b/SBSA15b_CHN_RJB_MEAN_NOSOF.csv"
    # File containing results for the total standard deviation
    STD_FILE = "SBSA15b/SBSA15b_CHN_RJB_TOTAL_STD_NOSOF.csv"
    # File containing results for the inter-event standard deviation
    INTER_FILE = "SBSA15b/SBSA15b_CHN_RJB_INTER_STD_NOSOF.csv"
    # File containing results for the intra-event standard deviation
    INTRA_FILE = "SBSA15b/SBSA15b_CHN_RJB_INTRA_STD_NOSOF.csv"


class StewartEtAl2016RegJPNNoSOFVHTestCaseA(StewartEtAl2016VHTestCaseA):
    """
    Tests the Stewart et al. (2016) V/H GMPE for the conditions:
    No style of faulting - Low Q (Japan)
    """
    GSIM_CLASS = SBSAb.StewartEtAl2016RegJPNNoSOFVH

    # File containing results for the mean
    MEAN_FILE = "SBSA15b/SBSA15b_JPN_PERIOD_MEAN_NOSOF.csv"
    # File containing results for the total standard deviation
    STD_FILE = "SBSA15b/SBSA15b_JPN_PERIOD_TOTAL_STD_NOSOF.csv"
    # File containing results for the inter-event standard deviation
    INTER_FILE = "SBSA15b/SBSA15b_JPN_PERIOD_INTER_STD_NOSOF.csv"
    # File containing results for the intra-event standard deviation
    INTRA_FILE = "SBSA15b/SBSA15b_JPN_PERIOD_INTRA_STD_NOSOF.csv"


class StewartEtAl2016RegJPNNoSOFVHTestCaseB(StewartEtAl2016VHTestCaseA):
    """
    Tests the Stewart et al. (2016) V/H GMPE for the conditions:
    No style of faulting - Low Q (Japan)
    """
    GSIM_CLASS = SBSAb.StewartEtAl2016RegJPNNoSOFVH

    # File containing results for the mean
    MEAN_FILE = "SBSA15b/SBSA15b_JPN_RJB_MEAN_NOSOF.csv"
    # File containing results for the total standard deviation
    STD_FILE = "SBSA15b/SBSA15b_JPN_RJB_TOTAL_STD_NOSOF.csv"
    # File containing results for the inter-event standard deviation
    INTER_FILE = "SBSA15b/SBSA15b_JPN_RJB_INTER_STD_NOSOF.csv"
    # File containing results for the intra-event standard deviation
    INTRA_FILE = "SBSA15b/SBSA15b_JPN_RJB_INTRA_STD_NOSOF.csv"
