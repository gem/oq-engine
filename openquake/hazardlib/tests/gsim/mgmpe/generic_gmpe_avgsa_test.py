# The Hazard Library
# Copyright (C) 2012-2023 GEM Foundation
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

import unittest
from openquake.hazardlib import gsim
from openquake.hazardlib.gsim.mgmpe.generic_gmpe_avgsa import GenericGmpeAvgSA
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase


class GenericGmpeAvgSATestCase(unittest.TestCase):
    """
    Testing instantiation and usage of the GenericGmpeAvgSA class
    """

    def test_calculation_Akkar_valueerror(self):
        # Testing not supported periods
        avg_periods = [0.05, 0.15, 1.0, 2.0, 4.1]
        with self.assertRaises(ValueError) as ve:
            gsim.mgmpe.generic_gmpe_avgsa.GenericGmpeAvgSA(
                gmpe_name='AkkarEtAlRepi2014',
                avg_periods=avg_periods,
                corr_func='akkar')
        self.assertEqual(str(ve.exception),
                         "'avg_periods' contains values outside of the range "
                         "supported by the Akkar et al. (2014) correlation "
                         "model")


class GenericGMPEAvgSaTablesTestCaseAkkar(BaseGSIMTestCase):
    """
    Conventional GMPE test case for Akkar correlation table
    """
    GSIM_CLASS = GenericGmpeAvgSA

    def test_all(self):
        self.check(
            'generic_avgsa/GENERIC_GMPE_AVGSA_AKKAR_MEAN.csv',
            'generic_avgsa/GENERIC_GMPE_AVGSA_AKKAR_TOTAL_STDDEV.csv',
            max_discrep_percentage=0.1,
            gmpe_name="BooreAtkinson2008",
            avg_periods=[0.05, 0.15, 1.0, 2.0, 4.0],
            corr_func="akkar")


class GenericGMPEAvgSaTablesTestCaseBakerJayaram(BaseGSIMTestCase):
    """
    Conventional GMPE test case for Baker & Jayaram correlation model
    """
    GSIM_CLASS = GenericGmpeAvgSA

    def test_all(self):
        self.check(
            'generic_avgsa/GENERIC_GMPE_AVGSA_BAKER_JAYARAM_MEAN.csv',
            'generic_avgsa/GENERIC_GMPE_AVGSA_BAKER_JAYARAM_TOTAL_STDDEV.csv',
            max_discrep_percentage=0.1,
            gmpe_name="BooreAtkinson2008",
            avg_periods=[0.05, 0.15, 1.0, 2.0, 4.0],
            corr_func="baker_jayaram")
