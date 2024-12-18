# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2023 GEM Foundation
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

from openquake.hazardlib import const, contexts
from openquake.hazardlib.gsim.gmpe_table import (
    GMPETable, todict, _return_tables)
from openquake.hazardlib.contexts import RuptureContext
from openquake.hazardlib import imt as imt_module


BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "gsimtables")
GMPE_TABLE = os.path.join(BASE_DATA_PATH, "Wcrust_rjb_med.hdf5")


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
        self.hdf5 = h5py.File(self.fname, 'w')
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
        output_dict = todict(self.group)
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


class GSIMTableGoodTestCase(unittest.TestCase):
    """
    Verifies the correct execution of a GMPE Table
    """
    TABLE_FILE = os.path.join(BASE_DATA_PATH, "good_dummy_table.hdf5")

    def setUp(self):
        """
        Opens the hdf5 file
        """
        self.hdf5 = h5py.File(self.TABLE_FILE, 'r')

    def test_correct_instantiation(self):
        """
        Verify that the data is loaded successfully
        """
        gsim = GMPETable(gmpe_table=self.TABLE_FILE)
        np.testing.assert_array_almost_equal(
            gsim.distances, self.hdf5["Distances"][:])
        np.testing.assert_array_almost_equal(gsim.m_w, self.hdf5["Mw"][:])
        self.assertEqual(gsim.distance_type, "rjb")
        self.assertSetEqual(gsim.REQUIRES_SITES_PARAMETERS, set())
        self.assertSetEqual(gsim.REQUIRES_DISTANCES, {"rjb"})
        self.assertSetEqual(
            gsim.DEFINED_FOR_INTENSITY_MEASURE_TYPES,
            {imt_module.PGA, imt_module.PGV, imt_module.SA})
        self.assertSetEqual(gsim.DEFINED_FOR_STANDARD_DEVIATION_TYPES,
                            {const.StdDev.TOTAL})
        # Verify correctly parsed IMLs and standard deviations
        for iml in ["PGA", "PGV", "SA", "T"]:
            np.testing.assert_array_almost_equal(
                gsim.imls[iml], self.hdf5["IMLs/" + iml][:])
            np.testing.assert_array_almost_equal(
                gsim.stddev[iml], self.hdf5["Total/" + iml][:])

    def test_retreival_tables_good_no_interp(self):
        """
        Tests the retreival of the IML tables for 'good' conditions without
        applying magnitude interpolations
        """
        gsim = GMPETable(gmpe_table=self.TABLE_FILE)
        # PGA
        np.testing.assert_array_almost_equal(
            _return_tables(gsim, 6.0, imt_module.PGA(), "IMLs"),
            np.array([2., 1., 0.5]))
        # PGV
        np.testing.assert_array_almost_equal(
            _return_tables(gsim, 6.0, imt_module.PGV(), "IMLs"),
            np.array([20., 10., 5.]),
            5)
        # SA(1.0)
        np.testing.assert_array_almost_equal(
            _return_tables(gsim, 6.0, imt_module.SA(1.0), "IMLs"),
            np.array([2.0, 1., 0.5]))
        # Also for standard deviations
        np.testing.assert_array_almost_equal(
            _return_tables(gsim, 6.0, imt_module.PGA(), 'Total'),
            0.5 * np.ones(3))
        np.testing.assert_array_almost_equal(
            _return_tables(gsim, 6.0, imt_module.SA(1.0), 'Total'),
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
            _return_tables(gsim, 6.5, imt_module.PGV(), "IMLs"),
            expected_table_pgv,
            5)
        expected_table_sa1 = np.array([midpoint(2., 4.),
                                       midpoint(1., 2.),
                                       midpoint(0.5, 1.)])
        np.testing.assert_array_almost_equal(
            _return_tables(gsim, 6.5, imt_module.SA(1.0), "IMLs"),
            expected_table_sa1)

    def test_retreival_tables_outside_mag_range(self):
        """
        Tests that an error is raised when inputting a magnitude value
        outside the supported range
        """
        gsim = GMPETable(gmpe_table=self.TABLE_FILE)
        with self.assertRaises(ValueError) as ve:
            _return_tables(gsim, 4.5, imt_module.PGA(), "IMLs")
        self.assertEqual(
            str(ve.exception),
            'Magnitude 4.50 outside of supported range (5.00 to 7.00)')

    def test_retreival_tables_outside_period_range(self):
        """
        Tests that an error is raised when inputting a period value
        outside the supported range
        """
        gsim = GMPETable(gmpe_table=self.TABLE_FILE)
        with self.assertRaises(ValueError) as ve:
            _return_tables(gsim, 6.0, imt_module.SA(2.5), "IMLs")
        self.assertEqual(
            str(ve.exception),
            "Spectral period 2.500 outside of valid range (0.100 to 2.000)")

    def test_get_mean_and_stddevs_good(self):
        """
        Tests the full execution of the GMPE tables for valid data
        """
        gsim = GMPETable(gmpe_table=self.TABLE_FILE)
        ctx = RuptureContext()
        mags = ['6.00']
        ctx.mag = 6.0
        # Test values at the given distances and those outside range
        ctx.rjb = ctx.rrup = np.array([0.5, 1.0, 10.0, 100.0, 500.0])
        ctx.vs30 = 1000. * np.ones(5)
        ctx.sids = np.arange(5)
        expected_mean = np.array([2.0, 2.0, 1.0, 0.5, 1.0E-20])
        expected_sigma = 0.5 * np.ones(5)
        imts = [imt_module.PGA(), imt_module.SA(1.0), imt_module.PGV()]
        # PGA
        [mean], [sigma], _, _ = contexts.get_mean_stds(
            gsim, ctx, [imts[0]], mags=mags)
        np.testing.assert_array_almost_equal(np.exp(mean), expected_mean, 5)
        np.testing.assert_array_almost_equal(sigma, expected_sigma, 5)
        # SA
        [mean], [sigma], _, _ = contexts.get_mean_stds(
            gsim, ctx, [imts[1]], mags=mags)
        np.testing.assert_array_almost_equal(np.exp(mean), expected_mean, 5)
        np.testing.assert_array_almost_equal(sigma, 0.8 * np.ones(5), 5)
        # PGV
        [mean], [sigma], _, _ = contexts.get_mean_stds(
            gsim, ctx, [imts[2]], mags=mags)
        np.testing.assert_array_almost_equal(
            np.exp(mean), 10. * expected_mean, 5)
        np.testing.assert_array_almost_equal(sigma, expected_sigma, 5)

    def test_instantiation(self):
        """
        Runs both instantiation checks
        The table file contains data for Inter and intra event standard
        deviation, as well as an IMT that is not recognised by OpenQuake
        """
        gsim = GMPETable(gmpe_table=self.TABLE_FILE)
        self.assertSetEqual(gsim.DEFINED_FOR_STANDARD_DEVIATION_TYPES,
                            {const.StdDev.TOTAL})
        self.assertSetEqual(gsim.DEFINED_FOR_INTENSITY_MEASURE_TYPES,
                            {imt_module.PGA, imt_module.PGV, imt_module.SA})

    def tearDown(self):
        """
        Close the hdf5 file
        """
        self.hdf5.close()


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
            GMPETable(gmpe_table=self.TABLE_FILE).init()
        self.assertEqual(str(ve.exception),
                         "Spectral Acceleration must be accompanied by periods"
                         )
