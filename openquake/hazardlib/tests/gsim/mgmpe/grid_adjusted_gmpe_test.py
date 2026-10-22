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
import shutil
import tempfile
import unittest

import h5py
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
# Test file uses replacement adjustment method on tau (scalar, IMT-varying)
# and subtract adjustment method on phi (per-cell dS2S + scalar adj_per_km,
# both IMT-varying), with h3 resolutions of 2, 3, 4
GRID_HDF5 = os.path.join(DATA_DIR, "test_grid_adjustments.hdf5")

# Test inputs
BASE, GRID = 0, 1 # Integers of results for original vs modified GSIM
BASE_GSIM = "AkkarEtAlRjb2014"
IMTS = ["PGA", "SA(0.5)", "SA(1.0)"]
LATS = np.array([0.0, 10.0, 20.0, 40.0])
LONS = np.array([0.0, 10.0, 20.0, 40.0])
DP = 4

# Per-IMT mean arrays
DL2L_MEAN_PER_CELL = [
    np.array([0.05, 0.10, 0.15, 0.20]),  # PGA
    np.array([0.04, 0.08, 0.12, 0.16]),  # SA(0.5)
    np.array([0.03, 0.06, 0.09, 0.12]),  # SA(1.0)
]
DS2S_MEAN_PER_CELL = [
    np.array([-0.10, -0.15, -0.20, -0.25]),  # PGA
    np.array([-0.08, -0.12, -0.16, -0.20]),  # SA(0.5)
    np.array([-0.06, -0.09, -0.12, -0.15]),  # SA(1.0)
]

# Scalar dL2L sigma per IMT
DL2L_SIG = [0.04, 0.03, 0.02]  # PGA, SA(0.5), SA(1.0)

# Per-cell dS2S sigma array per IMT
DS2S_SIG_PER_CELL = [
    np.array([0.04, 0.06, 0.08, 0.10]),  # PGA
    np.array([0.03, 0.05, 0.07, 0.08]),  # SA(0.5)
    np.array([0.03, 0.04, 0.05, 0.06]),  # SA(1.0)
]

# Scalar adj_per_km sigma per IMT
ATT_SIG = [0.00112, 0.00148, 0.00158]  # PGA, SA(0.5), SA(1.0)

EXPECTED_PATH_ADJ = [
    np.array([0., 1.15658587, 2.2321576, 1.21456404]),  # PGA
    np.array([0., 1.18827316, 2.0120857, 1.33602045]),  # SA(0.5)
    np.array([0., 0.83971303, 2.13784103, 0.91092302]), # SA(1.0)
]

# Per-IMT expected mean diff: hypo always in cell 0 for dL2L, sites vary
EXPECTED_MEAN_DIFFS = [
    DL2L_MEAN_PER_CELL[m][0] +
    DS2S_MEAN_PER_CELL[m] +
    EXPECTED_PATH_ADJ[m] for m in range(len(IMTS))
]

# Per-cell SE of the mean for each term/IMT, matching the datasets
# written to test_grid_adjustments.hdf5
DL2L_SE_PER_CELL = [
    np.array([0.010, 0.015, 0.020, 0.025]),  # PGA
    np.array([0.008, 0.012, 0.016, 0.020]),  # SA(0.5)
    np.array([0.006, 0.009, 0.012, 0.015]),  # SA(1.0)
]
DS2S_SE_PER_CELL = [
    np.array([0.020, 0.025, 0.030, 0.035]),  # PGA
    np.array([0.016, 0.020, 0.024, 0.028]),  # SA(0.5)
    np.array([0.012, 0.015, 0.018, 0.021]),  # SA(1.0)
]
EXPECTED_PATH_SE_ADJ = [
    np.array([0., 0.115658587, 0.22321576, 0.121456404]),  # PGA
    np.array([0., 0.118827316, 0.20120857, 0.133602045]),  # SA(0.5)
    np.array([0., 0.083971303, 0.213784103, 0.091092302]), # SA(1.0)
]


class GridAdjustedGMPETest(unittest.TestCase):

    def _get_mean_stds(self, imts, epsilons=None):
        # Compute the mean and std devs from grid adjusted GMM and base GMM
        base = valid.gsim(BASE_GSIM)
        adj = GridAdjustedGMPE(gmpe_name=BASE_GSIM, grid_hdf5_file=GRID_HDF5,
                               epsilons=epsilons)
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
        # Check correct values returned when searching loaded grid for
        # both a hypo-based term (dL2L) and a site-based term (dS2S)
        gd = load_residual_grids(GRID_HDF5)
        mu_dl2l = grid_lookup(
            gd["grids"]["PGA"]["dL2L"]["mean"],
            LATS, LONS, gd["h3_res"])
        aae(mu_dl2l, DL2L_MEAN_PER_CELL[0], decimal=DP)
        mu_ds2s = grid_lookup(
            gd["grids"]["PGA"]["dS2S"]["mean"],
            LATS, LONS, gd["h3_res"])
        aae(mu_ds2s, DS2S_MEAN_PER_CELL[0], decimal=DP)
        # Check that zero is returned for out-of-bounds coords
        mu = grid_lookup(
            gd["grids"]["PGA"]["dL2L"]["mean"],
            np.array([-80.0]), np.array([170.0]), gd["h3_res"])
        aae(mu, 0.0)

    def test_raytrace_path_adj(self):
        # Check raytracing for all IMTs
        gd = load_residual_grids(GRID_HDF5)
        for m, imt in enumerate(IMTS):
            adjs = raytrace_path_adj(
                gd["raytrace_grids"]["adj_per_km"][imt],
                np.zeros(len(LONS)), np.zeros(len(LATS)),
                LONS, LATS, gd["h3_res"],
            )
            aae(adjs, EXPECTED_PATH_ADJ[m], decimal=DP)

    def test_mean_and_sigma(self):
        # Check expected values
        mea, sig, tau, phi = self._get_mean_stds(IMTS)
        for m in range(len(IMTS)):
            aae(mea[GRID, m] - mea[BASE, m], EXPECTED_MEAN_DIFFS[m],
                decimal=DP)
            # dL2L uses "replace" with scalar, IMT-specific sigma
            aae(tau[GRID, m],
                np.full(len(LATS), DL2L_SIG[m]), decimal=DP)
            # phi: subtract per-cell dS2S sigma (site-varying) and scalar
            # adj_per_km sigma, both IMT-specific
            aae(phi[GRID, m],
                np.sqrt(phi[BASE, m] ** 2 - DS2S_SIG_PER_CELL[m] ** 2
                        - ATT_SIG[m] ** 2), decimal=DP)
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

    def test_epsilons_shift_mean_by_eps_times_se(self):
        # Non-zero epsilon must shift the mean by epsilon * mean_se for
        # each term. Hypo is at origin so dL2L always picks cell 0;
        # dS2S and dP2P use per-site/per-path SE values from the HDF5
        for eps in [-1.732, 1.0, 1.732]:
            eps_dict = {"dL2L": eps, "dS2S": eps, "adj_per_km": eps}
            mea, *_ = self._get_mean_stds(IMTS, epsilons=eps_dict)
            mea_cen, *_ = self._get_mean_stds(IMTS)
            for m in range(len(IMTS)):
                expected_shift = eps * (
                    DL2L_SE_PER_CELL[m][0]
                    + DS2S_SE_PER_CELL[m]
                    + EXPECTED_PATH_SE_ADJ[m])
                aae(mea[GRID, m] - mea_cen[GRID, m], expected_shift,
                    decimal=DP)

    def test_epsilons_missing_se_raises(self):
        # Non-zero epsilon for a term whose mean_se dataset is absent
        # must raise rather than silently falling back to the central
        with tempfile.TemporaryDirectory() as td:
            stripped = os.path.join(td, "no_se.hdf5")
            shutil.copy(GRID_HDF5, stripped)
            with h5py.File(stripped, "a") as hf:
                for term in ("dL2L", "dS2S", "adj_per_km"):
                    for imt_str in hf[term]:
                        key = f"{term}_mean_se"
                        if key in hf[term][imt_str]:
                            del hf[term][imt_str][key]
            base = valid.gsim(BASE_GSIM)
            adj = GridAdjustedGMPE(gmpe_name=BASE_GSIM,
                                   grid_hdf5_file=stripped,
                                   epsilons={"dL2L": 1.0})
            cmaker = simple_cmaker([base, adj], ["PGA"])
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
            with self.assertRaises(ValueError):
                cmaker.get_mean_stds([ctx])

    def test_epsilons_unknown_term_raises(self):
        # Unknown term names must raise rather than silently default
        with self.assertRaises(ValueError):
            GridAdjustedGMPE(gmpe_name=BASE_GSIM, grid_hdf5_file=GRID_HDF5,
                             epsilons={"dL2L": 1.0, "nope": 0.5})
