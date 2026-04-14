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
)

aae = np.testing.assert_array_almost_equal

# Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
GRID_HDF5 = os.path.join(DATA_DIR, "test_grid_adjustments.hdf5")

# Test inputs
BASE, GRID = 0, 1 # Integers of results for original vs modified GSIM
BASE_GSIM = "AkkarEtAlRjb2014"
LATS = np.array([0.0, 10.0, 20.0, 40.0])
LONS = np.array([0.0, 10.0, 20.0, 40.0])
DP = 4

# Test hdf5 has per-cell values at h3 resolutions 2, 3, 4
# for PGA, SA(0.5) and SA(1.0)
DL2L_MEAN = np.array([0.05, 0.10, 0.15, 0.20])
DL2L_STD = np.array([0.02, 0.04, 0.06, 0.08])
DS2S_MEAN = np.array([-0.10, -0.15, -0.20, -0.25])
DS2S_STD = np.array([0.03, 0.05, 0.07, 0.09])


class GridAdjustedGMPETest(unittest.TestCase):

    def _get_mean_stds(self, imts):
        # Instantiate GMMs
        base = valid.gsim(BASE_GSIM) # Original GMM
        adj = GridAdjustedGMPE(gmpe_name=BASE_GSIM, grid_hdf5=GRID_HDF5)
        # Make ctx
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
        # Get predictions using original and adjusted GMM
        out = cmaker.get_mean_stds([ctx])
        return out
    
    def test_grid_lookup(self):
        # Load the grid data
        gd = load_residual_grids(GRID_HDF5)
        # Known locations return per-cell values
        mu, sd = grid_lookup(
            gd["grids"]["PGA"]["dL2L"],
            gd["grids"]["PGA"]["dL2L_std"],
            LATS, LONS, gd["h3_res"]
            )
        aae(mu, DL2L_MEAN, decimal=DP)
        aae(sd, DL2L_STD, decimal=DP)
        # Location outside all grid cells returns zero
        mu, sd = grid_lookup(
            gd["grids"]["PGA"]["dL2L"],
            gd["grids"]["PGA"]["dL2L_std"],
            np.array([-80.0]), np.array([170.0]), gd["h3_res"])
        aae(mu, 0.0)
        aae(sd, 0.0)

    ### GMM Adjustments ###
    def test_mean_and_sigma(self):
        # Check adjustments are working correctly for all 3 IMTs
        mea, sig, tau, phi = self._get_mean_stds(["PGA", "SA(0.5)", "SA(1.0)"])
        # dL2L uses hypo loc -> all sites get cell-0 value
        dl2l_mu = DL2L_MEAN[0]
        dl2l_sd = DL2L_STD[0]
        for m in range(3):
            # Mean shifted by dL2L (uniform) + dS2S (per-site)
            aae(mea[GRID, m] - mea[BASE, m],
                dl2l_mu + DS2S_MEAN, decimal=DP)
            # Tau reduced (dL2L sub, same for all sites)
            aae(tau[GRID, m],
                np.sqrt(tau[BASE, m] ** 2 - dl2l_sd ** 2), decimal=DP)
            # Phi reduced (dS2S sub, per-site)
            aae(phi[GRID, m],
                np.sqrt(phi[BASE, m] ** 2 - DS2S_STD ** 2), decimal=DP)
            # Sig recomputed from adjusted tau and phi
            aae(sig[GRID, m],
                np.sqrt(tau[GRID, m] ** 2 + phi[GRID, m] ** 2), decimal=DP)

    def test_no_adjustment_for_missing_imt(self):
        # Check no adjustment for IMT without corrections in hdf5
        mea, sig, _, _ = self._get_mean_stds(["SA(3.0)"])
        aae(mea[BASE], mea[GRID])
        aae(sig[BASE], sig[GRID])

    ### Check presence of required ctx attributes ###
    def test_hypo_loc_is_available(self):
        # Instantiate adjusted GMM
        adj = GridAdjustedGMPE(gmpe_name=BASE_GSIM, grid_hdf5=GRID_HDF5)
        # dL2L correction uses hypo location
        self.assertIn("hypo_lat", adj.REQUIRES_RUPTURE_PARAMETERS)
        self.assertIn("hypo_lon", adj.REQUIRES_RUPTURE_PARAMETERS)
        # dS2S correction uses site location
        self.assertIn("lat", adj.REQUIRES_SITES_PARAMETERS)
        self.assertIn("lon", adj.REQUIRES_SITES_PARAMETERS)

    ### Error cases ###
    def test_error_non_random_effects_base_gsim(self):
        with self.assertRaises(ValueError): # GSIM is not random-effects
            GridAdjustedGMPE(gmpe_name="Campbell2003", grid_hdf5=GRID_HDF5)
