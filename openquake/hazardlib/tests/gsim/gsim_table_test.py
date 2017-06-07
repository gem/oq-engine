# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2017 GEM Foundation
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

import os
import tempfile
import unittest

import h5py
import numpy as np
from scipy.interpolate import interp1d

from openquake.hazardlib import const
from openquake.hazardlib.gsim.gsim_table import (
    GMPETable, AmplificationTable, hdf_arrays_to_dict)
from openquake.hazardlib.gsim.base import (
    RuptureContext, SitesContext, DistancesContext)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib import imt as imt_module


BASE_DATA_PATH = os.path.join(os.path.dirname(__file__),
                              "data",
                              "gsimtables")


def midpoint(low, high, point=0.5):
    """
    Returns the logarithmic midpoint between two value
    """
    return 10.0 ** (point * (np.log10(low) + np.log10(high)))


class HDFArraysToDictTestCase(unittest.TestCase):
    """
    Tests the conversion of a group containing a set of datasets(array) into
    a dictionary
    """
    def setUp(self):
        fd, self.fname = tempfile.mkstemp(suffix='.hdf5')
        os.close(fd)
        self.hdf5 = h5py.File(self.fname)
        self.group = self.hdf5.create_group("TestGroup")
        dset1 = self.group.create_dataset("DSET1", (3, 3), dtype="f")
        dset1[:] = np.zeros([3, 3])
        dset2 = self.group.create_dataset("DSET2", (3, 3), dtype="f")
        dset2[:] = np.ones([3, 3])

    def test_array_conversion(self):
        """
        Tests the simple array conversion
        """
        # Setup two
        expected_dset1 = np.zeros([3, 3])
        expected_dset2 = np.ones([3, 3])
        output_dict = hdf_arrays_to_dict(self.group)
        assert isinstance(output_dict, dict)
        self.assertIn("DSET1", output_dict)
        self.assertIn("DSET2", output_dict)
        np.testing.assert_array_almost_equal(output_dict["DSET1"],
                                             expected_dset1)
        np.testing.assert_array_almost_equal(output_dict["DSET2"],
                                             expected_dset2)

    def tearDown(self):
        """
        Close and delete the hdf5 file
        """
        self.hdf5.close()
        os.remove(self.fname)


class AmplificationTableSiteTestCase(unittest.TestCase):
    """
    Tests the amplification tables for a site parameter
    """
    TABLE_FILE = os.path.join(BASE_DATA_PATH, "model_amplification_site.hdf5")
    IDX = 0

    def setUp(self):
        """
        Open the hdf5 file
        """
        self.hdf5 = h5py.File(self.TABLE_FILE)
        self.amp_table = AmplificationTable(self.hdf5["Amplification"],
                                            self.hdf5["Mw"][:],
                                            self.hdf5["Distances"][:])

    def test_instantiation(self):
        """
        Tests the setup and loading of data from file to memory
        """

        # Check setup
        # 1. Shape
        self.assertTupleEqual(self.amp_table.shape, (10, 3, 5, 2))
        # 2. Parameter
        self.assertEqual(self.amp_table.parameter, "vs30")
        # 3. Element
        self.assertEqual(self.amp_table.element, "Sites")
        # 4. Interpolation values
        np.testing.assert_array_almost_equal(self.amp_table.values,
                                             np.array([400.0, 1000.0]))
        # 5. Periods
        np.testing.assert_array_almost_equal(self.amp_table.periods,
                                             np.array([0.1, 0.5, 1.0]))
        # 6. Means and Standard Deviations
        expected_mean, expected_sigma = self._build_mean_and_stddev_table()
        for key in self.amp_table.mean:
            np.testing.assert_array_almost_equal(self.amp_table.mean[key],
                                                 expected_mean[key])
            np.testing.assert_array_almost_equal(
                self.amp_table.sigma["Total"][key],
                expected_sigma["Total"][key])

    def _build_mean_and_stddev_table(self):
        """
        Builds the expected mean and standard deviation tables
        """
        expected_means = {
            "PGA": np.ones([10, 1, 5, 2]),
            "PGV": np.ones([10, 1, 5, 2]),
            "SA": np.ones([10, 3, 5, 2])
            }
        # For second level revise values
        expected_means["PGA"][:, :, :, self.IDX] *= 1.5
        expected_means["PGV"][:, :, :, self.IDX] *= 0.5
        expected_means["SA"][:, 0, :, self.IDX] *= 1.5
        expected_means["SA"][:, 1, :, self.IDX] *= 2.0
        expected_means["SA"][:, 2, :, self.IDX] *= 0.5
        expected_sigma = {const.StdDev.TOTAL: {
            "PGA": np.ones([10, 1, 5, 2]),
            "PGV": np.ones([10, 1, 5, 2]),
            "SA": np.ones([10, 3, 5, 2])
            }}
        expected_sigma[const.StdDev.TOTAL]["PGA"][:, :, :, self.IDX] *= 0.8
        expected_sigma[const.StdDev.TOTAL]["PGV"][:, :, :, self.IDX] *= 0.8
        expected_sigma[const.StdDev.TOTAL]["SA"][:, :, :, self.IDX] *= 0.8
        return expected_means, expected_sigma

    def test_get_set(self):
        """
        Test that the set function operates correctly
        """
        self.assertSetEqual(self.amp_table.get_set(), {"vs30"})

    def test_get_mean_table(self, idx=0):
        """
        Test the retrieval of the mean amplification tables for a given
        magnitude and IMT
        """
        rctx = RuptureContext()
        rctx.mag = 6.0
        # PGA
        expected_table = np.ones([10, 2])
        expected_table[:, self.IDX] *= 1.5
        np.testing.assert_array_almost_equal(
            self.amp_table.get_mean_table(imt_module.PGA(), rctx),
            expected_table)
        # SA
        expected_table[:, self.IDX] = 2.0 * np.ones(10)
        np.testing.assert_array_almost_equal(
            self.amp_table.get_mean_table(imt_module.SA(0.5), rctx),
            expected_table)
        # SA (period interpolation)
        interpolator = interp1d(np.log10(self.amp_table.periods),
                                np.log10(np.array([1.5, 2.0, 0.5])))
        period = 0.3
        expected_table[:, self.IDX] = (
            10.0 ** interpolator(np.log10(period))) * np.ones(10.)
        np.testing.assert_array_almost_equal(
            self.amp_table.get_mean_table(imt_module.SA(period), rctx),
            expected_table)

    def test_get_sigma_table(self):
        """
        Test the retrieval of the standard deviation modification tables
        for a given magnitude and IMT
        """
        rctx = RuptureContext()
        rctx.mag = 6.0
        # PGA
        expected_table = np.ones([10, 2])
        expected_table[:, self.IDX] *= 0.8
        stddevs = ["Total"]
        pga_table = self.amp_table.get_sigma_tables(imt_module.PGA(),
                                                    rctx,
                                                    stddevs)[0]
        np.testing.assert_array_almost_equal(pga_table, expected_table)
        # SA (for coverage)
        sa_table = self.amp_table.get_sigma_tables(imt_module.SA(0.3),
                                                   rctx,
                                                   stddevs)[0]
        np.testing.assert_array_almost_equal(sa_table, expected_table)

    def test_get_amplification_factors(self):
        """
        Tests the amplification tables
        """
        rctx = RuptureContext()
        rctx.mag = 6.0
        dctx = DistancesContext()
        # Takes distances at the values found in the table (not checking
        # distance interpolation)
        dctx.rjb = np.copy(self.amp_table.distances[:, 0, 0])
        # Test Vs30 is 700.0 m/s midpoint between the 400 m/s and 1000 m/s
        # specified in the table
        sctx = SitesContext()
        sctx.vs30 = 700.0 * np.ones_like(dctx.rjb)
        stddevs = [const.StdDev.TOTAL]
        expected_mean = np.ones_like(dctx.rjb)
        expected_sigma = np.ones_like(dctx.rjb)
        # Check PGA and PGV
        mean_amp, sigma_amp = self.amp_table.get_amplification_factors(
            imt_module.PGA(), sctx, rctx, dctx.rjb, stddevs)
        np.testing.assert_array_almost_equal(
            mean_amp,
            midpoint(1.0, 1.5) * expected_mean)
        np.testing.assert_array_almost_equal(
            sigma_amp[0],
            0.9 * expected_mean)
        mean_amp, sigma_amp = self.amp_table.get_amplification_factors(
            imt_module.PGV(), sctx, rctx, dctx.rjb, stddevs)
        np.testing.assert_array_almost_equal(
            mean_amp,
            midpoint(1.0, 0.5) * expected_mean)
        np.testing.assert_array_almost_equal(
            sigma_amp[0],
            0.9 * expected_mean)
        # Sa (0.5)
        mean_amp, sigma_amp = self.amp_table.get_amplification_factors(
            imt_module.SA(0.5), sctx, rctx, dctx.rjb, stddevs)
        np.testing.assert_array_almost_equal(
            mean_amp,
            midpoint(1.0, 2.0) * expected_mean)
        np.testing.assert_array_almost_equal(
            sigma_amp[0],
            0.9 * expected_mean)

    def tearDown(self):
        """
        Close the hdf5 file
        """
        self.hdf5.close()


class AmplificationTableRuptureTestCase(AmplificationTableSiteTestCase):
    """
    Test case for the amplification table when applied to a rupture specific
    parameter
    """
    TABLE_FILE = os.path.join(BASE_DATA_PATH, "model_amplification_rake.hdf5")
    IDX = 1

    def test_instantiation(self):
        """
        Tests the setup and loading of data from file to memory
        """

        # Check setup
        # 1. Shape
        self.assertTupleEqual(self.amp_table.shape, (10, 3, 5, 2))
        # 2. Parameter
        self.assertEqual(self.amp_table.parameter, "rake")
        # 3. Element
        self.assertEqual(self.amp_table.element, "Rupture")
        # 4. Interpolation values
        np.testing.assert_array_almost_equal(self.amp_table.values,
                                             np.array([0.0, 90.0]))
        # 5. Periods
        np.testing.assert_array_almost_equal(self.amp_table.periods,
                                             np.array([0.1, 0.5, 1.0]))
        # 6. Means and Standard Deviations
        expected_mean, expected_sigma = self._build_mean_and_stddev_table()
        for key in self.amp_table.mean:
            np.testing.assert_array_almost_equal(self.amp_table.mean[key],
                                                 expected_mean[key])
            np.testing.assert_array_almost_equal(
                self.amp_table.sigma["Total"][key],
                expected_sigma["Total"][key])

    def test_get_amplification_factors(self):
        """
        Tests the amplification tables
        """
        rctx = RuptureContext()
        rctx.rake = 45.0
        rctx.mag = 6.0
        dctx = DistancesContext()
        # Takes distances at the values found in the table (not checking
        # distance interpolation)
        dctx.rjb = np.copy(self.amp_table.distances[:, 0, 0])
        # Test Vs30 is 700.0 m/s midpoint between the 400 m/s and 1000 m/s
        # specified in the table
        sctx = SitesContext()
        stddevs = [const.StdDev.TOTAL]
        expected_mean = np.ones_like(dctx.rjb)
        # Check PGA and PGV
        mean_amp, sigma_amp = self.amp_table.get_amplification_factors(
            imt_module.PGA(), sctx, rctx, dctx.rjb, stddevs)
        np.testing.assert_array_almost_equal(
            mean_amp,
            midpoint(1.0, 1.5) * expected_mean)
        np.testing.assert_array_almost_equal(
            sigma_amp[0],
            0.9 * expected_mean)
        mean_amp, sigma_amp = self.amp_table.get_amplification_factors(
            imt_module.PGV(), sctx, rctx, dctx.rjb, stddevs)
        np.testing.assert_array_almost_equal(
            mean_amp,
            midpoint(1.0, 0.5) * expected_mean)
        np.testing.assert_array_almost_equal(
            sigma_amp[0],
            0.9 * expected_mean)
        # Sa (0.5)
        mean_amp, sigma_amp = self.amp_table.get_amplification_factors(
            imt_module.SA(0.5), sctx, rctx, dctx.rjb, stddevs)
        np.testing.assert_array_almost_equal(
            mean_amp,
            midpoint(1.0, 2.0) * expected_mean)
        np.testing.assert_array_almost_equal(
            sigma_amp[0],
            0.9 * expected_mean)

    def test_get_set(self):
        """
        Test that the set function operates correctly
        """
        self.assertSetEqual(self.amp_table.get_set(), set(("rake",)))


class AmplificationTableBadTestCase(unittest.TestCase):
    """
    Tests the instantiation of the amplification table if a non-supported
    parameter is used
    """
    TABLE_FILE = os.path.join(BASE_DATA_PATH, "bad_table_parameter.hdf5")
    IDX = 0

    def setUp(self):
        """
        Open the hdf5 file
        """
        self.hdf5 = h5py.File(self.TABLE_FILE)

    def test_unsupported_parameter(self):
        """
        Tests instantiation with a bad input
        """
        with self.assertRaises(ValueError) as ve:
            AmplificationTable(self.hdf5["Amplification"], None, None)
        self.assertEqual(str(ve.exception),
                         "Amplification parameter Bad Value not recognised!")

    def tearDown(self):
        """
        Close the file
        """
        self.hdf5.close()


class GSIMTableGoodTestCase(unittest.TestCase):
    """
    Verifies the correct execution of a GMPE Table
    """
    TABLE_FILE = os.path.join(BASE_DATA_PATH, "good_dummy_table.hdf5")

    def setUp(self):
        """
        Opens the hdf5 file
        """
        self.hdf5 = h5py.File(self.TABLE_FILE)

    def test_correct_instantiation(self):
        """
        Verify that the data is loaded successfully
        """
        gsim = GMPETable(gmpe_table=self.TABLE_FILE)
        np.testing.assert_array_almost_equal(gsim.distances,
                                             self.hdf5["Distances"][:])
        np.testing.assert_array_almost_equal(gsim.m_w,
                                             self.hdf5["Mw"][:])
        self.assertEqual(gsim.distance_type, "rjb")
        self.assertSetEqual(gsim.REQUIRES_SITES_PARAMETERS, set(("vs30",)))
        self.assertSetEqual(gsim.REQUIRES_DISTANCES, set(("rjb",)))
        self.assertSetEqual(
            gsim.DEFINED_FOR_INTENSITY_MEASURE_TYPES,
            set((imt_module.PGA, imt_module.PGV, imt_module.SA)))
        self.assertSetEqual(gsim.DEFINED_FOR_STANDARD_DEVIATION_TYPES,
                            set((const.StdDev.TOTAL,)))
        # Verify correctly parsed IMLs and standard deviations
        for iml in ["PGA", "PGV", "SA", "T"]:
            np.testing.assert_array_almost_equal(
                gsim.imls[iml],
                self.hdf5["IMLs/" + iml][:])
            np.testing.assert_array_almost_equal(
                gsim.stddevs["Total"][iml],
                self.hdf5["Total/" + iml][:])

    def test_instantiation_without_file(self):
        """
        Tests the case when the GMPE table file is missing
        """
        with self.assertRaises(IOError) as ioe:
            GMPETable(gmpe_table=None)
        self.assertEqual(str(ioe.exception),
                         "GMPE Table Not Defined!")

        with self.assertRaises(IOError) as ioe:
            GMPETable(gmpe_table='/do/not/exists/table.hdf5')
        self.assertEqual(str(ioe.exception),
                         "Missing file '/do/not/exists/table.hdf5'")

    def test_retreival_tables_good_no_interp(self):
        """
        Tests the retreival of the IML tables for 'good' conditions without
        applying magnitude interpolations
        """
        gsim = GMPETable(gmpe_table=self.TABLE_FILE)
        # PGA
        np.testing.assert_array_almost_equal(
            gsim._return_tables(6.0, imt_module.PGA(), "IMLs"),
            np.array([2., 1., 0.5]))
        # PGV
        np.testing.assert_array_almost_equal(
            gsim._return_tables(6.0, imt_module.PGV(), "IMLs"),
            np.array([20., 10., 5.]),
            5)
        # SA(1.0)
        np.testing.assert_array_almost_equal(
            gsim._return_tables(6.0, imt_module.SA(1.0), "IMLs"),
            np.array([2.0, 1., 0.5]))
        # Also for standard deviations
        np.testing.assert_array_almost_equal(
            gsim._return_tables(6.0, imt_module.PGA(), "Total"),
            0.5 * np.ones(3))
        np.testing.assert_array_almost_equal(
            gsim._return_tables(6.0, imt_module.SA(1.0), "Total"),
            0.8 * np.ones(3))

    def test_retreival_tables_good_interp(self):
        """
        Tests the retreival of the IML tables for 'good' conditions with
        magnitude interpolations
        """
        gsim = GMPETable(gmpe_table=self.TABLE_FILE)
        expected_table_pgv = np.array([midpoint(20., 40.),
                                       midpoint(10., 20.),
                                       midpoint(5., 10.)])
        np.testing.assert_array_almost_equal(
            gsim._return_tables(6.5, imt_module.PGV(), "IMLs"),
            expected_table_pgv,
            5)
        expected_table_sa1 = np.array([midpoint(2., 4.),
                                       midpoint(1., 2.),
                                       midpoint(0.5, 1.)])
        np.testing.assert_array_almost_equal(
            gsim._return_tables(6.5, imt_module.SA(1.0), "IMLs"),
            expected_table_sa1)

    def test_retreival_tables_outside_mag_range(self):
        """
        Tests that an error is raised when inputting a magnitude value
        outside the supported range
        """
        gsim = GMPETable(gmpe_table=self.TABLE_FILE)
        with self.assertRaises(ValueError) as ve:
            gsim._return_tables(4.5, imt_module.PGA(), "IMLs")
        self.assertEqual(
            str(ve.exception),
            "Magnitude 4.50 outside of supported range (5.00 to 7.00)")

    def test_retreival_tables_outside_period_range(self):
        """
        Tests that an error is raised when inputting a period value
        outside the supported range
        """
        gsim = GMPETable(gmpe_table=self.TABLE_FILE)
        with self.assertRaises(ValueError) as ve:
            gsim._return_tables(6.0, imt_module.SA(2.5), "IMLs")
        self.assertEqual(
            str(ve.exception),
            "Spectral period 2.500 outside of valid range (0.100 to 2.000)")

    def test_get_mean_and_stddevs_good(self):
        """
        Tests the full execution of the GMPE tables for valid data
        """
        gsim = GMPETable(gmpe_table=self.TABLE_FILE)
        rctx = RuptureContext()
        rctx.mag = 6.0
        dctx = DistancesContext()
        # Test values at the given distances and those outside range
        dctx.rjb = np.array([0.5, 1.0, 10.0, 100.0, 500.0])
        sctx = SitesContext()
        sctx.vs30 = 1000. * np.ones(5)
        stddevs = [const.StdDev.TOTAL]
        expected_mean = np.array([2.0, 2.0, 1.0, 0.5, 1.0E-20])
        expected_sigma = 0.25 * np.ones(5)
        # PGA
        mean, sigma = gsim.get_mean_and_stddevs(sctx, rctx, dctx,
                                                imt_module.PGA(),
                                                stddevs)
        np.testing.assert_array_almost_equal(np.exp(mean), expected_mean, 5)
        np.testing.assert_array_almost_equal(sigma[0], expected_sigma, 5)
        # SA
        mean, sigma = gsim.get_mean_and_stddevs(sctx, rctx, dctx,
                                                imt_module.SA(1.0),
                                                stddevs)
        np.testing.assert_array_almost_equal(np.exp(mean), expected_mean, 5)
        np.testing.assert_array_almost_equal(sigma[0], 0.4 * np.ones(5), 5)
        # PGV
        mean, sigma = gsim.get_mean_and_stddevs(sctx, rctx, dctx,
                                                imt_module.PGV(),
                                                stddevs)
        np.testing.assert_array_almost_equal(np.exp(mean),
                                             10. * expected_mean,
                                             5)
        np.testing.assert_array_almost_equal(sigma[0], expected_sigma, 5)

    def test_get_mean_and_stddevs_good_amplified(self):
        """
        Tests the full execution of the GMPE tables for valid data with
        amplification
        """
        gsim = GMPETable(gmpe_table=self.TABLE_FILE)
        rctx = RuptureContext()
        rctx.mag = 6.0
        dctx = DistancesContext()
        # Test values at the given distances and those outside range
        dctx.rjb = np.array([0.5, 1.0, 10.0, 100.0, 500.0])
        sctx = SitesContext()
        sctx.vs30 = 100. * np.ones(5)
        stddevs = [const.StdDev.TOTAL]
        expected_mean = np.array([20., 20., 10., 5., 1.0E-19])
        expected_sigma = 0.25 * np.ones(5)
        # PGA
        mean, sigma = gsim.get_mean_and_stddevs(sctx, rctx, dctx,
                                                imt_module.PGA(),
                                                stddevs)
        np.testing.assert_array_almost_equal(np.exp(mean), expected_mean, 5)
        np.testing.assert_array_almost_equal(sigma[0], expected_sigma, 5)
        # SA
        mean, sigma = gsim.get_mean_and_stddevs(sctx, rctx, dctx,
                                                imt_module.SA(1.0),
                                                stddevs)
        np.testing.assert_array_almost_equal(np.exp(mean), expected_mean, 5)
        np.testing.assert_array_almost_equal(sigma[0], 0.4 * np.ones(5), 5)

    def test_get_mean_stddevs_unsupported_stddev(self):
        """
        Tests the execution of the GMPE with an unsupported standard deviation
        type
        """
        gsim = GMPETable(gmpe_table=self.TABLE_FILE)
        rctx = RuptureContext()
        rctx.mag = 6.0
        dctx = DistancesContext()
        # Test values at the given distances and those outside range
        dctx.rjb = np.array([0.5, 1.0, 10.0, 100.0, 500.0])
        sctx = SitesContext()
        sctx.vs30 = 1000. * np.ones(5)
        stddevs = [const.StdDev.TOTAL, const.StdDev.INTER_EVENT]
        with self.assertRaises(ValueError) as ve:
            gsim.get_mean_and_stddevs(sctx, rctx, dctx, imt_module.PGA(),
                                      stddevs)
        self.assertEqual(str(ve.exception),
                         "Standard Deviation type Inter event not supported")

    def tearDown(self):
        """
        Close the hdf5 file
        """
        self.hdf5.close()


class GSIMTableTestCaseMultiStdDev(unittest.TestCase):
    """
    Tests the instantiation of the GSIM table class in the case when
    i. Multiple Standard Deviations are specified
    ii. An unrecognised IMT is input
    """
    TABLE_FILE = os.path.join(BASE_DATA_PATH,
                              "good_dummy_table_multi_stddev.hdf5")

    def test_instantiation(self):
        """
        Runs both instantiation checks
        The table file contains data for Inter and intra event standard
        deviation, as well as an IMT that is not recognised by OpenQuake
        """
        gsim = GMPETable(gmpe_table=self.TABLE_FILE)
        expected_stddev_set = set((const.StdDev.TOTAL,
                                   const.StdDev.INTER_EVENT,
                                   const.StdDev.INTRA_EVENT))
        self.assertSetEqual(gsim.DEFINED_FOR_STANDARD_DEVIATION_TYPES,
                            expected_stddev_set)
        expected_imt_set = set((imt_module.PGA,
                                imt_module.PGV,
                                imt_module.SA))
        self.assertSetEqual(gsim.DEFINED_FOR_INTENSITY_MEASURE_TYPES,
                            expected_imt_set)


class GSIMTableTestCaseRupture(unittest.TestCase):
    """
    Tests the case when the amplification is based on a rupture parameter
    """
    TABLE_FILE = os.path.join(BASE_DATA_PATH,
                              "good_dummy_table_rake.hdf5")

    def test_instantiation(self):
        """
        Tests instantiation of class
        """
        gsim = GMPETable(gmpe_table=self.TABLE_FILE)
        expected_rupture_set = set(("mag", "rake"))
        self.assertSetEqual(gsim.REQUIRES_RUPTURE_PARAMETERS,
                            expected_rupture_set)
        self.assertEqual(gsim.amplification.parameter, "rake")
        self.assertEqual(gsim.amplification.element, "Rupture")
        self.assertSetEqual(gsim.REQUIRES_SITES_PARAMETERS, set())

    def test_get_mean_and_stddevs_good(self):
        """
        Tests the full execution of the GMPE tables for valid data
        """
        gsim = GMPETable(gmpe_table=self.TABLE_FILE)
        rctx = RuptureContext()
        rctx.mag = 6.0
        rctx.rake = 90.0
        dctx = DistancesContext()
        # Test values at the given distances and those outside range
        dctx.rjb = np.array([0.5, 1.0, 10.0, 100.0, 500.0])
        sctx = SitesContext()
        stddevs = [const.StdDev.TOTAL]
        expected_mean = np.array([20.0, 20.0, 10.0, 5.0, 1.0E-19])
        # PGA
        mean, sigma = gsim.get_mean_and_stddevs(sctx, rctx, dctx,
                                                imt_module.PGA(),
                                                stddevs)
        np.testing.assert_array_almost_equal(np.exp(mean), expected_mean, 5)
        np.testing.assert_array_almost_equal(sigma[0], 0.25 * np.ones(5), 5)
        # SA
        mean, sigma = gsim.get_mean_and_stddevs(sctx, rctx, dctx,
                                                imt_module.SA(1.0),
                                                stddevs)
        np.testing.assert_array_almost_equal(np.exp(mean), expected_mean, 5)
        np.testing.assert_array_almost_equal(sigma[0], 0.4 * np.ones(5), 5)


class GSIMTableTestCaseBadFile(unittest.TestCase):
    """
    Tests the case when the hdf5 file contains spectral accelerations but
    is missing the periods
    """
    TABLE_FILE = os.path.join(BASE_DATA_PATH,
                              "missing_periods.hdf5")

    def test_missing_periods(self):
        """
        Tests missing period information
        """
        with self.assertRaises(ValueError) as ve:
            GMPETable(gmpe_table=self.TABLE_FILE)
        self.assertEqual(str(ve.exception),
                         "Spectral Acceleration must be accompanied by periods"
                         )


class GSIMTableTestCaseNoAmplification(unittest.TestCase):
    """
    Tests the simple case in which no amplification is applied
    """
    TABLE_FILE = os.path.join(BASE_DATA_PATH,
                              "good_dummy_table_noamp.hdf5")

    def test_instantiation(self):
        """
        Tests instantiation without amplification
        """
        gsim = GMPETable(gmpe_table=self.TABLE_FILE)
        self.assertIsNone(gsim.amplification)
        self.assertSetEqual(gsim.REQUIRES_SITES_PARAMETERS, set(()))
        self.assertSetEqual(gsim.REQUIRES_RUPTURE_PARAMETERS, set(("mag",)))

    def test_get_mean_and_stddevs(self):
        """
        Tests mean and standard deviations without amplification
        """
        gsim = GMPETable(gmpe_table=self.TABLE_FILE)
        rctx = RuptureContext()
        rctx.mag = 6.0
        dctx = DistancesContext()
        # Test values at the given distances and those outside range
        dctx.rjb = np.array([0.5, 1.0, 10.0, 100.0, 500.0])
        sctx = SitesContext()
        stddevs = [const.StdDev.TOTAL]
        expected_mean = np.array([2.0, 2.0, 1.0, 0.5, 1.0E-20])
        # PGA
        mean, sigma = gsim.get_mean_and_stddevs(sctx, rctx, dctx,
                                                imt_module.PGA(),
                                                stddevs)
        np.testing.assert_array_almost_equal(np.exp(mean), expected_mean, 5)
        np.testing.assert_array_almost_equal(sigma[0], 0.5 * np.ones(5), 5)
        # SA
        mean, sigma = gsim.get_mean_and_stddevs(sctx, rctx, dctx,
                                                imt_module.SA(1.0),
                                                stddevs)
        np.testing.assert_array_almost_equal(np.exp(mean), expected_mean, 5)
        np.testing.assert_array_almost_equal(sigma[0], 0.8 * np.ones(5), 5)
        # PGV
        mean, sigma = gsim.get_mean_and_stddevs(sctx, rctx, dctx,
                                                imt_module.PGV(),
                                                stddevs)
        np.testing.assert_array_almost_equal(np.exp(mean),
                                             10. * expected_mean,
                                             5)
        np.testing.assert_array_almost_equal(sigma[0], 0.5 * np.ones(5), 5)


class GSIMTableQATestCase(BaseGSIMTestCase):
    """
    Quality Assurance test case with real data taken from the
    2015 Canadian National Seismic Hazard Map
    """
    GSIM_CLASS = GMPETable
    MEAN_FILE = "gsimtables/Wcrust_rjb_med_MEAN.csv"
    STD_TOTAL_FILE = "gsimtables/Wcrust_rjb_med_TOTAL.csv"

    def setUp(self):
        self.GSIM_CLASS.GMPE_TABLE = os.path.join(BASE_DATA_PATH,
                                                  "Wcrust_rjb_med.hdf5")

    def test_mean(self):
        self.check(self.MEAN_FILE, max_discrep_percentage=0.7)

    def test_std_total(self):
        self.check(self.STD_TOTAL_FILE, max_discrep_percentage=0.7)

    def tearDown(self):
        self.GSIM_CLASS.GMPE_TABLE = None
