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
import pickle
import shutil
import tempfile
import unittest
from unittest import mock
from pathlib import Path
import h5py
import numpy as np

from openquake.hazardlib import valid
from openquake.hazardlib.contexts import simple_cmaker
from openquake.hazardlib.gsim.mgmpe import grid_adjusted_gmpe as mod
from openquake.hazardlib.gsim.mgmpe.grid_adjusted_gmpe import (
    GridAdjustedGMPE,
    grid_lookup,
    load_residual_grids,
    raytrace_path_adj,
)
from openquake.hazardlib.gsim.mgmpe.modifiable_gmpe import ModifiableGMPE

aae = np.testing.assert_array_almost_equal

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
# Test file uses replacement adjustment method on tau (per-cell dL2L_sig,
# IMT-varying) and subtract adjustment method on phi (per-cell dS2S_sig
# + per-cell adj_per_km_sig summed along the ray with distance-squared
# weights, both IMT-varying), with h3 resolutions of 2, 3, 4
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

# Per-cell dL2L sigma array per IMT
DL2L_SIG_PER_CELL = [
    np.array([0.04, 0.05, 0.06, 0.07], dtype=np.float32),  # PGA
    np.array([0.03, 0.04, 0.05, 0.06], dtype=np.float32),  # SA(0.5)
    np.array([0.02, 0.03, 0.04, 0.05], dtype=np.float32),  # SA(1.0)
]

# Per-cell dS2S sigma array per IMT
DS2S_SIG_PER_CELL = [
    np.array([0.04, 0.06, 0.08, 0.10]),  # PGA
    np.array([0.03, 0.05, 0.07, 0.08]),  # SA(0.5)
    np.array([0.03, 0.04, 0.05, 0.06]),  # SA(1.0)
]

# Per-cell adj_per_km sigma array per IMT (non-uniform, in log units per km)
ATT_SIG_PER_CELL = [
    np.array([0.001,  0.0015, 0.002,  0.0025], dtype=np.float32),  # PGA
    np.array([0.0012, 0.0018, 0.0024, 0.003],  dtype=np.float32),  # SA(0.5)
    np.array([0.001,  0.002,  0.003,  0.004],  dtype=np.float32),  # SA(1.0)
]

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

    ### HELPERS ###
    def _make_ctx(self, cmaker, **overrides):
        # Build the shared test context, allowing scenario-specific values.
        defaults = dict(mag=6.0, rake=0.0, hypo_depth=10.0, vs30=760.0,
                        rrup=np.array([10.0, 20.0, 30.0, 50.0]),
                        rjb=np.array([10.0, 20.0, 30.0, 50.0]),
                        lat=LATS, lon=LONS, hypo_lat=0.0, hypo_lon=0.0)
        defaults.update(overrides)
        ctx = cmaker.new_ctx(len(LATS))
        for k, v in defaults.items():
            setattr(ctx, k, v)
        return ctx

    def _get_mean_stds(self, imts, epsilons=None, path_cap=None):
        # Compute the mean and std devs from grid adjusted GMM and base GMM
        base = valid.gsim(BASE_GSIM)
        adj = GridAdjustedGMPE(gmpe_name=BASE_GSIM, grid_hdf5_file=GRID_HDF5,
                               epsilons=epsilons, path_cap=path_cap)
        cmaker = simple_cmaker([base, adj], imts)
        return cmaker.get_mean_stds([self._make_ctx(cmaker)])

    ### BASIC TESTS
    def test_grid_lookup(self):
        # Check correct values returned when searching loaded grid for
        # both a hypo-based term (dL2L) and a site-based term (dS2S)
        gd = load_residual_grids(GRID_HDF5)
        mu_dl2l = grid_lookup(
            gd["grids"]["PGA"]["dL2L"],
            LATS, LONS, gd["h3_res"])
        aae(mu_dl2l["mean"], DL2L_MEAN_PER_CELL[0], decimal=DP)
        mu_ds2s = grid_lookup(
            gd["grids"]["PGA"]["dS2S"],
            LATS, LONS, gd["h3_res"])
        aae(mu_ds2s["mean"], DS2S_MEAN_PER_CELL[0], decimal=DP)
        # Check that zero is returned for out-of-bounds coords
        mu = grid_lookup(
            gd["grids"]["PGA"]["dL2L"],
            np.array([-80.0]), np.array([170.0]), gd["h3_res"])
        for vals in mu.values():
            aae(vals, 0.0)

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

    def test_raytrace_masks_are_exact(self):
        # The h3 lookups skipped thanks to the masks must all be misses,
        # so the results must be identical to the ones without masks
        gd = load_residual_grids(GRID_HDF5)
        rng = np.random.default_rng(42)
        slo, sla, hlo, hla = rng.uniform(-5., 45., (4, 300))
        nomask = (0., 0., None)
        for imt in IMTS:
            grids = {"mean": gd["raytrace_grids"]["adj_per_km"][imt]}
            masks = mod._build_masks(grids["mean"], gd["h3_res"])
            exp = mod._raytrace_path_adjs(
                grids, hlo, hla, slo, sla, gd["h3_res"], nomask)["mean"]
            got = mod._raytrace_path_adjs(
                grids, hlo, hla, slo, sla, gd["h3_res"], masks)["mean"]
            self.assertGreater(np.count_nonzero(exp), 0)
            np.testing.assert_array_equal(got, exp)

    def test_mean_and_sigma(self):
        # Check expected values
        mea, sig, tau, phi = self._get_mean_stds(IMTS)
        gd = load_residual_grids(GRID_HDF5)
        for m in range(len(IMTS)):
            # Per-record path sig^2 = Σ_c dist(r, c)^2 · sig_c^2. Pass
            # the pre-squared sig^2 grid under key "sig_sq" so the
            # raytrace sums it with distance-squared weights instead of
            # distance weights.
            path_sig_sq = mod._raytrace_path_adjs(
                {"mean": gd["raytrace_grids"]["adj_per_km"][IMTS[m]],
                 "sig_sq": gd["raytrace_sig_grids"]["adj_per_km"][IMTS[m]]},
                np.zeros(len(LONS)), np.zeros(len(LATS)),
                LONS, LATS, gd["h3_res"])["sig_sq"]
            path_sig = np.sqrt(np.maximum(0.0, path_sig_sq))
            aae(mea[GRID, m] - mea[BASE, m], EXPECTED_MEAN_DIFFS[m],
                decimal=DP)
            # dL2L uses "replace" with per-cell sig; hypo at origin -> cell 0
            aae(tau[GRID, m],
                np.full(len(LATS), DL2L_SIG_PER_CELL[m][0]), decimal=DP)
            # phi: subtract per-cell dS2S sigma (site-varying) and the
            # per-record path sig in quadrature
            aae(phi[GRID, m],
                np.sqrt(phi[BASE, m] ** 2 - DS2S_SIG_PER_CELL[m] ** 2
                        - path_sig ** 2), decimal=DP)
            aae(sig[GRID, m],
                np.sqrt(tau[GRID, m] ** 2 + phi[GRID, m] ** 2), decimal=DP)

    def test_sigma_actions_and_components(self):
        # Check all actions on every component, with scalar and cell values.
        # Expected variances start from sig=5, tau=3, phi=4 and adjustment=1.
        variances = {
            ("replace", "sig"): [1, 9, 16],
            ("replace", "tau"): [17, 1, 16],
            ("replace", "phi"): [10, 9, 1],
            ("add", "sig"): [26, 9, 16],
            ("add", "tau"): [26, 10, 16],
            ("add", "phi"): [26, 9, 17],
            ("sub", "sig"): [24, 9, 16],
            ("sub", "tau"): [24, 8, 16],
            ("sub", "phi"): [24, 9, 15]}
        for scalar in (True, False):
            scale = np.ones(2) if scalar else np.array([1., 2.])
            values = 1. if scalar else scale
            for (action, component), expected in variances.items():
                with self.subTest(scalar=scalar, action=action,
                                  component=component):
                    out = np.array([5., 3., 4.])[:, None] * scale
                    mod.adjust_sigma(values, {"sig_comp_modified": component},
                                     action, *out)
                    np.testing.assert_allclose(
                        out, np.sqrt(expected)[:, None] * scale)

    def test_resolved_adjustments(self):
        # Check the combined mean, SE and per-cell sigma against expected
        # fixture values for every term/IMT, including integrated path SE.
        gd = load_residual_grids(GRID_HDF5)
        ctx = np.rec.fromarrays(
            [np.zeros(len(LATS)), np.zeros(len(LONS)), LATS, LONS],
            names="hypo_lat,hypo_lon,lat,lon")
        for m, imt in enumerate(IMTS):
            # Per-record path sig^2 = Σ_c dist(r, c)^2 · sig_c^2
            path_sig_sq = mod._raytrace_path_adjs(
                {"mean": gd["raytrace_grids"]["adj_per_km"][imt],
                 "sig_sq": gd["raytrace_sig_grids"]["adj_per_km"][imt]},
                np.zeros(len(LONS)), np.zeros(len(LATS)),
                LONS, LATS, gd["h3_res"])["sig_sq"]
            expected = {
                "dL2L": {
                    "mean": np.full(len(LATS), DL2L_MEAN_PER_CELL[m][0]),
                    "mean_se": np.full(len(LATS), DL2L_SE_PER_CELL[m][0]),
                    "sig": np.full(len(LATS), DL2L_SIG_PER_CELL[m][0])},
                "dS2S": {"mean": DS2S_MEAN_PER_CELL[m],
                         "mean_se": DS2S_SE_PER_CELL[m],
                         "sig": DS2S_SIG_PER_CELL[m]},
                "adj_per_km": {"mean": EXPECTED_PATH_ADJ[m],
                               "mean_se": EXPECTED_PATH_SE_ADJ[m],
                               "sig_sq": path_sig_sq}}
            for term, values in expected.items():
                adjs = mod._resolve_adjs(
                    gd, gd["res_terms"][term], term, imt, ctx)
                self.assertEqual(adjs.keys(), values.keys())
                for key, value in values.items():
                    aae(adjs[key], value, decimal=DP)

    def test_shared_lookup_fallback_and_zero_mean(self):
        # A zero mean in a fine cell still selects its SE/sigma; a nearby
        # point falls back to the parent, and an uncovered point gets zero.
        fine = mod.h3.latlng_to_cell(10.0, 20.0, 4)
        parent = mod.h3.cell_to_parent(fine, 2)
        sibling = next(cell for cell in mod.h3.cell_to_children(parent, 4)
                       if cell != fine)
        lats, lons = np.array([
            mod.h3.cell_to_latlng(fine), mod.h3.cell_to_latlng(sibling),
            (-80.0, 170.0)]).T
        grids = {"mean": {fine: 0.0, parent: 1.0},
                 "mean_se": {fine: 0.1, parent: 0.2},
                 "sig": {fine: 0.3, parent: 0.4}}
        adjs = grid_lookup(grids, lats, lons, [2, 3, 4])
        aae(adjs["mean"], [0.0, 1.0, 0.0])
        aae(adjs["mean_se"], [0.1, 0.2, 0.0])
        aae(adjs["sig"], [0.3, 0.4, 0.0])

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

    def test_path_cap_clips_per_branch_total(self):
        # Per-branch cap bounds (central + eps*SE) on path. Covers both
        # the eps=0 central-only case and the eps!=0 branch case
        cap = 0.5
        for eps in (0.0, 1.732):
            eps_dict = {"dL2L": 0.0, "dS2S": 0.0, "adj_per_km": eps}
            mea, *_ = self._get_mean_stds(
                IMTS, epsilons=eps_dict, path_cap=cap)
            base_mea, *_ = self._get_mean_stds(IMTS)
            for m in range(len(IMTS)):
                capped_total = np.clip(
                    EXPECTED_PATH_ADJ[m] + eps * EXPECTED_PATH_SE_ADJ[m],
                    -cap, cap)
                expected_diff = (DL2L_MEAN_PER_CELL[m][0]
                                 + DS2S_MEAN_PER_CELL[m] + capped_total)
                aae(mea[GRID, m] - base_mea[BASE, m], expected_diff,
                    decimal=DP)

    def test_path_cap_is_a_noop_when_non_binding(self):
        # None, or any cap above the largest uncapped total, must leave
        # the mean identical to the uncapped run
        eps_dict = {"dL2L": 0.0, "dS2S": 0.0, "adj_per_km": 1.732}
        mea_ref, *_ = self._get_mean_stds(IMTS, epsilons=eps_dict)
        for cap in (None, 10.0):
            mea, *_ = self._get_mean_stds(
                IMTS, epsilons=eps_dict, path_cap=cap)
            # cap != None takes a different arithmetic path (adds
            # capped_total - mean_adj) so rounding differs at ~1e-16
            np.testing.assert_array_almost_equal(mea, mea_ref, decimal=14)

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
            central = GridAdjustedGMPE(
                gmpe_name=BASE_GSIM, grid_hdf5_file=stripped)
            central_cm = simple_cmaker([base, central], IMTS)
            out = central_cm.get_mean_stds([self._make_ctx(central_cm)])
            aae(out, self._get_mean_stds(IMTS))
            adj = GridAdjustedGMPE(gmpe_name=BASE_GSIM,
                                   grid_hdf5_file=stripped,
                                   epsilons={"dL2L": 1.0})
            cmaker = simple_cmaker([base, adj], ["PGA"])
            with self.assertRaises(ValueError):
                cmaker.get_mean_stds([self._make_ctx(cmaker)])

    def test_epsilons_unknown_term_raises(self):
        # Unknown term names must raise rather than silently default
        with self.assertRaises(ValueError):
            GridAdjustedGMPE(gmpe_name=BASE_GSIM, grid_hdf5_file=GRID_HDF5,
                             epsilons={"dL2L": 1.0, "nope": 0.5})

    def test_pathlib_grid_file(self):
        # A pathlib filename must give the same results as a string
        # filename (sanity check for usage outside of engine calcs)
        adj = GridAdjustedGMPE(gmpe_name=BASE_GSIM,
                               grid_hdf5_file=Path(GRID_HDF5))
        cmaker = simple_cmaker([valid.gsim(BASE_GSIM), adj], IMTS)
        out = cmaker.get_mean_stds([self._make_ctx(cmaker)])
        aae(out, self._get_mean_stds(IMTS))

    def test_grids_shared_and_pickled(self):
        # Like GMPETable, pickling preserves the loaded grids and their
        # sharing, even after the extracted HDF5 file has been deleted.
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, 'adjustments.hdf5')
            shutil.copy(GRID_HDF5, path)
            gsims = [GridAdjustedGMPE(gmpe_name=BASE_GSIM,
                                      grid_hdf5_file=path,
                                      epsilons={"dL2L": eps})
                     for eps in (-1., 1.)]
            self.assertIs(gsims[0].grid_data, gsims[1].grid_data)
            data = pickle.dumps(gsims)
        with mock.patch.object(mod, 'get_residual_grids',
                               side_effect=AssertionError('Reopened grids')):
            restored = pickle.loads(data)
        self.assertIs(restored[0].grid_data, restored[1].grid_data)
        new = restored[1]
        cmaker = simple_cmaker([valid.gsim(BASE_GSIM), gsims[1]], IMTS)
        ctx = self._make_ctx(cmaker)
        expected = cmaker.get_mean_stds([ctx])
        cmaker = simple_cmaker([valid.gsim(BASE_GSIM), new], IMTS)
        np.testing.assert_array_equal(
            cmaker.get_mean_stds([self._make_ctx(cmaker)]), expected)

    ### SHARING OF THE CENTRAL PART TESTS ###
    def test_grid_replacement(self):
        # A new instance must use the updated HDF5 at the same path, while
        # the original instance retains its loaded grid
        with tempfile.TemporaryDirectory() as td:
            grid_path = os.path.join(td, "adjustments.hdf5")
            shutil.copy(GRID_HDF5, grid_path)
            kwargs = dict(gmpe_name=BASE_GSIM, grid_hdf5_file=grid_path)
            first = GridAdjustedGMPE(**kwargs)
            cmaker = simple_cmaker([first], ["PGA"])
            ctx = cmaker.recarray([self._make_ctx(cmaker)])

            def _compute(gsim):
                out = np.zeros((4, len(cmaker.imts), len(ctx)))
                gsim.compute(ctx, cmaker.imts, *out)
                return out

            before = _compute(first)
            with h5py.File(grid_path, "a") as hf:
                dataset = hf["dL2L"]["PGA"]["dL2L"]
                dataset[:] = dataset[:] + 0.5
            after = _compute(GridAdjustedGMPE(**kwargs))
            aae(after[0] - before[0], 0.5)
            np.testing.assert_array_equal(after[1:], before[1:])
            np.testing.assert_array_equal(_compute(first), before)

    def test_shared_vs_separate_equivalence(self):
        # Shared (27 adj GSIMs in one cmaker, central part computed once)
        # must match separate (each adj in its own cmaker) across all 27
        # epsilon combos
        levels = [-1.732, 0.0, 1.732]
        combos = [{"dL2L": a, "dS2S": b, "adj_per_km": c}
                  for a in levels for b in levels for c in levels]

        base = valid.gsim(BASE_GSIM)
        reference = []
        for eps in combos:
            adj = GridAdjustedGMPE(gmpe_name=BASE_GSIM,
                                   grid_hdf5_file=GRID_HDF5, epsilons=eps)
            cm = simple_cmaker([base, adj], IMTS)
            reference.append(cm.get_mean_stds([self._make_ctx(cm)]))

        adjs = [GridAdjustedGMPE(gmpe_name=BASE_GSIM,
                                 grid_hdf5_file=GRID_HDF5, epsilons=eps)
                for eps in combos]
        cm = simple_cmaker([base] + adjs, IMTS)
        with mock.patch.object(mod, "compute_central",
                               side_effect=mod.compute_central) as central:
            shared = cm.get_mean_stds([self._make_ctx(cm)])
        # The central part is computed once for all 27 adj GSIMs
        self.assertEqual(central.call_count, 1)
        # Ray tracing is monitored once per IMT, not once per branch.
        self.assertEqual(cm.gra_mon.counts, len(IMTS))
        self.assertIn(cm.gra_mon, cm.monitor.children)
        for i, eps in enumerate(combos):
            for name_i, name in enumerate(("mean", "sig", "tau", "phi")):
                np.testing.assert_array_equal(
                    reference[i][name_i, 1], shared[name_i, 1 + i],
                    err_msg=f"{name} mismatch for epsilons={eps}")

    def test_sharing_preserves_backbone_adjustment_order(self):
        # Sharing must preserve the effect of backbone adjustment order
        steps = [("add_between_within_stds", {"with_betw_ratio": 1.0}),
                 ("set_between_epsilon", {"epsilon_tau": 1.0})]
        gsims = [GridAdjustedGMPE(
            gmpe_name="ModifiableGMPE", grid_hdf5_file=GRID_HDF5,
            gmpe={BASE_GSIM: {}}, **dict(order))
            for order in (steps, steps[::-1])]
        separate = []
        for gsim in gsims:
            cmaker = simple_cmaker([gsim], ["PGA"])
            out = cmaker.get_mean_stds([self._make_ctx(cmaker)])
            separate.append(out[:, 0])
        self.assertFalse(np.array_equal(separate[0][0], separate[1][0]))
        cmaker = simple_cmaker(gsims, ["PGA"])
        shared = cmaker.get_mean_stds([self._make_ctx(cmaker)])
        for i, expected in enumerate(separate):
            np.testing.assert_array_equal(shared[:, i], expected)

    def test_wrapped_in_modifiable_gmpe(self):
        # A GridAdjustedGMPE wrapped by ModifiableGMPE is computed via its
        # compute method and must give the same results
        wrapper = ModifiableGMPE(gmpe={"GridAdjustedGMPE": {
            "gmpe_name": BASE_GSIM, "grid_hdf5_file": GRID_HDF5}})
        base = valid.gsim(BASE_GSIM)
        cmaker = simple_cmaker([base, wrapper], IMTS)
        out = cmaker.get_mean_stds([self._make_ctx(cmaker)])
        aae(out, self._get_mean_stds(IMTS))

    def test_path_cap_differs_across_cap_values(self):
        # Different caps on the same ctx share the central part but still
        # produce distinct means (clip is applied in apply_epsilons)
        base = valid.gsim(BASE_GSIM)
        tight = GridAdjustedGMPE(gmpe_name=BASE_GSIM,
                                 grid_hdf5_file=GRID_HDF5, path_cap=0.5)
        loose = GridAdjustedGMPE(gmpe_name=BASE_GSIM,
                                 grid_hdf5_file=GRID_HDF5, path_cap=10.0)
        self.assertEqual(tight.central_key, loose.central_key)
        cmaker = simple_cmaker([base, tight, loose], IMTS)
        out = cmaker.get_mean_stds([self._make_ctx(cmaker)])
        # Different caps must produce different mean predictions
        self.assertFalse(np.array_equal(out[0, 1], out[0, 2]))
