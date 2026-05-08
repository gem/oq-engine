# The Hazard Library
# Copyright (C) 2012-2026 GEM Foundation
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
import os
import unittest
import numpy as np

from openquake.hazardlib import valid
from openquake.hazardlib.contexts import simple_cmaker
from openquake.hazardlib.gsim.mgmpe.grid_adjusted_gmpe import (
    GridAdjustedGMPE,
    grid_lookup,
    load_residual_grids,
    raytrace_path_adj,
)

aae = np.testing.assert_array_almost_equal

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
# Test file uses replacement adjustment method on tau and
# subtract adjustment method on phi, with h3 resolutions
# of 2, 3, 4
GRID_HDF5 = os.path.join(DATA_DIR, "test_grid_adjustments.hdf5")

# Test inputs
BASE, GRID = 0, 1 # Integers of results for original vs modified GSIM
BASE_GSIM = "AkkarEtAlRjb2014"
LATS = np.array([0.0, 10.0, 20.0, 40.0])
LONS = np.array([0.0, 10.0, 20.0, 40.0])
DP = 4

# Per-IMT mean arrays and scalar sigs
DL2L_MEANS = [
    np.array([0.05, 0.10, 0.15, 0.20]),  # PGA
    np.array([0.04, 0.08, 0.12, 0.16]),  # SA(0.5)
    np.array([0.03, 0.06, 0.09, 0.12]),  # SA(1.0)
]
DL2L_SIGS = [np.std(m) for m in DL2L_MEANS]

DS2S_MEANS = [
    np.array([-0.10, -0.15, -0.20, -0.25]),  # PGA
    np.array([-0.08, -0.12, -0.16, -0.20]),  # SA(0.5)
    np.array([-0.06, -0.09, -0.12, -0.15]),  # SA(1.0)
]
DS2S_SIGS = [np.std(m) for m in DS2S_MEANS]

ATT_PER_KM = np.array([0.005, 0.004, 0.003, 0.002])
ATT_SIG = np.std(ATT_PER_KM)  # Scalar phi_P2P - same for all IMTs

# Expected path adjustment per record
EXPECTED_PATH_ADJ = np.array([0., 1.15658587, 2.10640224, 1.03237941])

# Per-IMT expected mean diff: hypo always in first dL2L cell, sites vary
EXPECTED_MEAN_DIFFS = [
    DL2L_MEANS[m][0] + DS2S_MEANS[m] + EXPECTED_PATH_ADJ for m in range(3)
]


class GridAdjustedGMPETest(unittest.TestCase):

    def _get_mean_stds(self, imts):
        # Compute the mean and std devs from grid adjusted GMM and base GMM
        base = valid.gsim(BASE_GSIM)
        adj = GridAdjustedGMPE(gmpe_name=BASE_GSIM, grid_hdf5_file=GRID_HDF5)
        cmaker = simple_cmaker([base, adj], imts)
        ctx = cmaker.new_ctx(len(LATS))
        ctx.mag = 6.0
        ctx.rake = 0.0
        ctx.hypo_depth = 10.0
        ctx.vs30 = 760.0
        ctx.rrup = np.array([10.0, 20.0, 30.0, 50.0])
        ctx.rjb = np.array([10.0, 20.0, 30.0, 50.0])
        ctx.lat = LATS
        ctx.lon = LONS
        ctx.hypo_lat = 0.0
        ctx.hypo_lon = 0.0
        return cmaker.get_mean_stds([ctx])

    def test_grid_lookup(self):
        # Check correct values returned when searching loaded grid
        gd = load_residual_grids(GRID_HDF5)
        mu = grid_lookup(
            gd["grids"]["PGA"]["dL2L"],
            LATS, LONS, gd["h3_res"])
        aae(mu, DL2L_MEANS[0], decimal=DP)
        # Check that zero is returned for out-of-bounds coords
        mu = grid_lookup(
            gd["grids"]["PGA"]["dL2L"],
            np.array([-80.0]), np.array([170.0]), gd["h3_res"])
        aae(mu, 0.0)

    def test_raytrace_path_adj(self):
        # Check separately the raytracing
        gd = load_residual_grids(GRID_HDF5)
        path_grid = gd["path_pgns"]["att_per_km"]["PGA"]
        adjs = raytrace_path_adj(
            path_grid, # OQ polygons and adjustments
            np.zeros(len(LONS)), np.zeros(len(LATS)),
            LONS, LATS,
        )
        aae(adjs, EXPECTED_PATH_ADJ, decimal=DP)

    def test_mean_and_sigma(self):
        # Check expected values
        mea, sig, tau, phi = self._get_mean_stds(
            ["PGA", "SA(0.5)", "SA(1.0)"])
        for m in range(3):
            aae(mea[GRID, m] - mea[BASE, m], EXPECTED_MEAN_DIFFS[m],
                decimal=DP)
            # dL2L uses "replace" method so tau is scalar of DL2L_SIGS[m]
            aae(tau[GRID, m], np.full(len(LATS), DL2L_SIGS[m]), decimal=DP)
            aae(phi[GRID, m],
                np.sqrt(phi[BASE, m] ** 2 - DS2S_SIGS[m] ** 2
                        - ATT_SIG ** 2), decimal=DP)
            aae(sig[GRID, m],
                np.sqrt(tau[GRID, m] ** 2 + phi[GRID, m] ** 2), decimal=DP)

    def test_no_adjustment_for_missing_imt(self):
        # Check that no adjustment is applied to IMT without adjustments
        mea, sig, _, _ = self._get_mean_stds(["SA(3.0)"])
        aae(mea[BASE], mea[GRID])
        aae(sig[BASE], sig[GRID])

    def test_error_non_random_effects_base_gsim(self):
        # Check that cannot use specified adjs for tau/phi with non-random
        # effects GMM
        with self.assertRaises(ValueError):
            GridAdjustedGMPE(
                gmpe_name="Campbell2003", grid_hdf5_file=GRID_HDF5)
