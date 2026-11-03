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

"""
Module :mod:`openquake.hazardlib.mgmpe.grid_adjusted_gmpe` implements
:class:`~openquake.hazardlib.mgmpe.GridAdjustedGMPE`
"""
import json
import os
import h5py
import h3
import numpy as np

from openquake.hazardlib import const
from openquake.hazardlib.geo.geodetic import npoints_between, distance
from openquake.hazardlib.gsim.base import GMPE, registry


def load_sigma_for_term(grp, term, imt_str, location, sig_action,
                        cell_ids, grids, sig_scalars):
    """
    Load the sigma adjustment for one term/IMT group into
    grids[imt_str][term]["sig"] (per-cell) OR sig_scalars (scalar).
    """
    sig_key = f"{term}_sig"
    has_sig_attr = sig_key in grp.attrs
    has_sig_dataset = sig_key in grp
    if has_sig_attr and has_sig_dataset:
        # Raise an error if requesting both scalar and per-cell
        raise ValueError(
            f"Both scalar adjustment and per-cell dataset '{sig_key}' "
            f"found for term '{term}', IMT '{imt_str}'. Provide only one.")
    if not has_sig_attr and not has_sig_dataset:
        # Raise an error if not specifiy scalar or per cell
        # but requested a sigma adjustment
        raise ValueError(
            f"sig_adjustment '{sig_action}' requested for term '{term}' "
            f"but '{sig_key}' is missing for '{imt_str}'")
    if has_sig_dataset and location == "path":
        # Raise an error if requesting per-cell sigma
        # adjustment with a path-based term
        raise ValueError(
            f"Per-cell sigma is not currently supported for "
            f"path-based terms (term '{term}'). Use a "
            f"scalar adjustment instead.")
    sig_vals = grp[sig_key][:] if has_sig_dataset else grp.attrs[sig_key]
    if np.any(sig_vals < 0):
        raise ValueError(
            f"Negative _sig value found for term "
            f"'{term}' and IMT '{imt_str}'")
    if has_sig_dataset:
        grids[imt_str][term]["sig"] = dict(zip(cell_ids, sig_vals))
    else:
        sig_scalars[imt_str][term] = sig_vals


def build_raytrace_grid(cell_ids, mean_vals):
    """
    Build the H3 cell-id lookup for one path-based term/IMT.

    Returns {cell_id: per_km_adj_value}. Raytracing resolves each sample
    point to a stored cell via h3.latlng_to_cell with finest-to-coarsest
    fallback (see raytrace_path_adj).
    """
    return dict(zip(cell_ids, mean_vals))


def load_residual_grids(hdf5_path):
    """
    Load the hdf5 residual grids into a dict with seven keys:

    * grids: nested dict of
      {imt_str: {term: {"mean":    {cell_id: float},
                        "sig":     {cell_id: float},
                        "mean_se": {cell_id: float}}, ...}}
      for hypo/site-based terms only. The "sig" key is present only when
      sig_adjustment is not "none" and the sigma is given as a per-cell
      dataset named "{term}_sig". The "mean_se" key is present only when
      the HDF5 includes a per-cell dataset "{term}_mean_se" (used by the
      epsilons kwarg of GridAdjustedGMPE). Per-cell sigma is not supported
      for path-based terms.

    * raytrace_grids: {term: {imt_str: {cell_id: val}, ...}} - H3 cell-id
      lookups for path-based terms (used in raytracing), stored per term
      per IMT (cell grids can differ across IMTs and across terms).

    * raytrace_se_grids: same structure as raytrace_grids but holding the
      per-cell SE on the mean for path-based terms. Populated only when
      the HDF5 includes a per-cell "{term}_mean_se" dataset.

    * raytrace_masks: {(term, imt_str): (lat0, lon0, mask)} - per h3
      resolution, the lat/lon boxes where the path points may hit a cell
      of raytrace_grids; used to skip the lookups which would miss. It
      starts empty and is filled for the terms/IMTs actually used.

    * sig_scalars: {imt_str: {term: float}} - one sigma adjustment scalar
      per term per IMT. Populated when sig_adjustment is not "none" and the
      sigma is given as a scalar adjustment (group attribute "{term}_sig").

      NOTE: sig_scalars and grids[imt][term]["sig"] are mutually exclusive
      for each term/IMT - the presence of both raises an error.

    * h3_res: sorted (coarsest to finest) list of h3 resolutions, derived
      automatically from the cell IDs in the grids.

    * res_terms: dict mapping each term name to a sub-dict with three keys:

      - location (required): how to resolve the correction spatially;
        one of "hypo", "site", or "path".

      - sig_adjustment (optional, default "none"): the action to apply
        to the GMM sigma component - "sub", "add", "replace", or "none".
        When not "none", a sigma value must be provided in the HDF5 for
        each IMT group as either a scalar group attribute "{term}_sig" or
        a per-cell dataset of the same name (see above). Per-cell sigma
        lookup is not supported currently for path-based terms.

      - sig_comp_modified (required when sig_adjustment is not "none"):
        which sigma component to modify - "tau", "phi", or "sig".

    :param hdf5_path:
        Path to the hdf5 containing the grid-based adjustments.
    """
    grids = {}
    raytrace_grids = {}
    raytrace_se_grids = {}
    sig_scalars = {}
    resolutions = set()
    with h5py.File(hdf5_path, "r") as hf:
        res_terms = json.loads(hf.attrs["res_terms"])
        for term in res_terms: # e.g. dS2S
            location = res_terms[term]["location"]
            sig_action = res_terms[term].get("sig_adjustment", "none")
            for imt_str in hf[term]: # e.g. SA(0.5)

                # Ensure per-IMT dicts exist in both stores so term entries
                # can be added below; either may stay empty for a given IMT
                # (e.g., grids for path-only IMTs, sig_scalars when no scalar
                # sigma applies)
                grids.setdefault(imt_str, {})
                sig_scalars.setdefault(imt_str, {})

                # Get group and the mean adj values
                grp = hf[term][imt_str]
                mean_vals = grp[term][:]

                # Collect h3 resolutions for this term/IMT
                cell_ids = grp["cell_id"][:].astype(str)
                resolutions.update(h3.get_resolution(c) for c in cell_ids)

                # If path-based build the raytrace lookup for this term/IMT
                # (per-IMT grid in case the grid varies with IMT as well)
                if location == "path":
                    raytrace_grids.setdefault(term, {})
                    raytrace_grids[term][imt_str] =\
                          build_raytrace_grid(cell_ids, mean_vals)
                else:
                    # Hypo/site based correction - store per cell mean adj
                    grids[imt_str][term] = {
                        "mean": dict(zip(cell_ids, mean_vals))}

                # If req get sigma adjustment and store in grids dict too
                if sig_action != "none":
                    load_sigma_for_term(
                        grp, term, imt_str, location,
                        sig_action, cell_ids, grids, sig_scalars)

                # Optional per-cell SE on the mean, only used when a
                # non-zero epsilon is set for the term
                se_key = f"{term}_mean_se"
                if se_key in grp:
                    se_vals = grp[se_key][:]
                    if np.any(se_vals < 0):
                        raise ValueError(
                            f"Negative '{se_key}' for term '{term}', "
                            f"IMT '{imt_str}'")
                    if location == "path":
                        raytrace_se_grids.setdefault(term, {})
                        raytrace_se_grids[term][imt_str] = \
                            build_raytrace_grid(cell_ids, se_vals)
                    else:
                        grids[imt_str][term]["mean_se"] = \
                            dict(zip(cell_ids, se_vals))

    return {"grids": grids,
            "raytrace_grids": raytrace_grids,
            "raytrace_se_grids": raytrace_se_grids,
            "raytrace_masks": {}, # Filled on first use by _resolve_adjs
            "sig_scalars": sig_scalars,
            "h3_res": sorted(resolutions), # Coarsest to finest h3 res
            "res_terms": res_terms}


def raytrace_path_adj(grid, hypo_lons, hypo_lats, site_lons, site_lats,
                      h3_res):
    """
    For each epicentre-to-site path (travel path) apply an adjustment based
    on the distance traversed through each (h3) grid cell. A conventional
    example would be if the user had a grid with an attenuation rate per km
    within each grid cell. The function will compute the distance through
    that cell, and retrieve a correction proportional to this distance to
    mean ground-motion.

    :param grid:
        {cell_id: per_km_adj_value} for a single term and given imt
    :param hypo_lons:
        Array of hypocentre longitudes
    :param hypo_lats:
        Array of hypocentre latitudes
    :param site_lons:
        Array of site longitudes
    :param site_lats:
        Array of site latitudes
    :param h3_res:
        Sorted list of h3 resolution levels (coarse to fine) present
        in the stored grid; iterated finest-to-coarsest at lookup.
    :returns:
        adjustment_vals array of shape (len(hypo_lons),)
    """
    return _raytrace_path_adjs(
        {"mean": grid}, hypo_lons, hypo_lats, site_lons, site_lats,
        h3_res)["mean"]


# Number of points used to discretise each path
NPTS = 100

# Margin in degrees around the vertices of a cell and step in degrees of
# the masks; for cells of resolution >= MASK_MIN_RES and latitudes within
# MASK_MAX_LAT the margin is larger than the bulge of the great-circle
# edges (under 0.07 degrees), otherwise the masks are not used
MASK_MARGIN = 0.1
MASK_STEP = 0.1
MASK_MIN_RES = 2
MASK_MAX_LAT = 80.


# For each h3 resolution, a lat/lon raster flagging the boxes which may
# contain points of a stored cell of that resolution, i.e. the boxes
# overlapping the bounding box of the cell vertices enlarged by the margin.
# Points in a box not flagged cannot be in a stored cell, so their h3
# lookups would miss and can be skipped; returns (lat0, lon0, mask), with
# mask None if the margin is not guaranteed to be enough
def _build_masks(grid, h3_res):
    boxes = []  # (resolution index, lat1, lat2, lon1, lon2)
    for cell in grid:
        res = h3.get_resolution(cell)
        if res not in h3_res:  # never looked up
            continue
        bound = np.array(h3.cell_to_boundary(cell))
        lats, lons = bound[:, 0], bound[:, 1]
        if res < MASK_MIN_RES or np.abs(lats).max() > MASK_MAX_LAT:
            return 0., 0., None
        if lons.max() - lons.min() > 180:  # across the antimeridian
            lons = np.array([-180., 180.])
        boxes.append((h3_res.index(res),
                      lats.min() - MASK_MARGIN, lats.max() + MASK_MARGIN,
                      lons.min() - MASK_MARGIN, lons.max() + MASK_MARGIN))
    if not boxes:
        return 0., 0., np.zeros((len(h3_res), 0, 0), bool)
    arr = np.array(boxes)
    lat0, lon0 = arr[:, 1].min(), arr[:, 3].min()
    nlat = int(np.floor((arr[:, 2].max() - lat0) / MASK_STEP)) + 1
    nlon = int(np.floor((arr[:, 4].max() - lon0) / MASK_STEP)) + 1
    # With the current step, margin and latitude limit, at most about
    # 93 MB per term/IMT: 16 resolutions * 1603 * 3603 one-byte bools.
    # The rectangle includes empty areas between stored cells.
    mask = np.zeros((len(h3_res), nlat, nlon), bool)
    for r, lat1, lat2, lon1, lon2 in boxes:
        i1, i2 = np.floor((np.array([lat1, lat2]) - lat0) / MASK_STEP)
        j1, j2 = np.floor((np.array([lon1, lon2]) - lon0) / MASK_STEP)
        mask[int(r), int(i1):int(i2) + 1, int(j1):int(j2) + 1] = True
    return lat0, lon0, mask


# Boolean array of shape (nres, len(lats)), True for the points which may
# be in a stored cell of the given resolution
def _candidates(masks, lats, lons, nres):
    lat0, lon0, mask = masks
    if mask is None:  # no filtering
        return np.ones((nres, len(lats)), bool)
    i = np.floor((lats - lat0) / MASK_STEP).astype(int)
    j = np.floor((lons - lon0) / MASK_STEP).astype(int)
    ok = (i >= 0) & (i < mask.shape[1]) & (j >= 0) & (j < mask.shape[2])
    out = np.zeros((len(mask), len(lats)), bool)
    out[:, ok] = mask[:, i[ok], j[ok]]
    return out


# Resolve all fields on the same path grid with one raytrace per path.
# The h3 lookups are performed only for the points which may be in a
# stored cell, according to the masks (see _build_masks), since the
# other lookups would miss: the result is the same.
def _raytrace_path_adjs(grids, hypo_lons, hypo_lats, site_lons, site_lats,
                        h3_res, masks=None):
    # Set some stores
    n_paths = len(hypo_lons)
    ra_per_path = {key: np.zeros(n_paths) for key in grids}
    reference_grid = grids["mean"]
    if masks is None:
        masks = _build_masks(reference_grid, h3_res)
    lons = np.zeros((n_paths, NPTS))
    lats = np.zeros((n_paths, NPTS))
    spacing = np.zeros(n_paths)

    for idx_path in range(n_paths): # Iterate over the paths

        # Discretise the line
        lons[idx_path], lats[idx_path], _ = npoints_between(
            site_lons[idx_path], site_lats[idx_path], 0.,
            hypo_lons[idx_path], hypo_lats[idx_path], 0., NPTS)

        # Distance between consecutive discretised points along the path
        spacing[idx_path] = distance(
            lons[idx_path, 0], lats[idx_path, 0], 0.,
            lons[idx_path, 1], lats[idx_path, 1], 0.)

    # Flag the (resolution, path, point) triples worth a lookup
    cand = _candidates(masks, lats.ravel(), lons.ravel(),
                       len(h3_res)).reshape(len(h3_res), n_paths, NPTS)
    fine_to_coarse = range(len(h3_res) - 1, -1, -1)

    # Get the cumulative correction based on distance traversed per
    # grid cell and the associated distance-based adjustment terms.
    # Each sample point resolves to one stored cell via finest-to-
    # coarsest h3 fallback; points with no stored cell contribute zero
    for idx_path in np.flatnonzero(cand.any(axis=(0, 2))):
        adj_sum = dict.fromkeys(grids, 0.0)
        pcand = cand[:, idx_path]
        for k in np.flatnonzero(pcand.any(axis=0)):
            for r in fine_to_coarse:
                if not pcand[r, k]:
                    continue
                cell = h3.latlng_to_cell(
                    lats[idx_path, k], lons[idx_path, k], h3_res[r])
                if cell in reference_grid:
                    for key, grid in grids.items():
                        adj_sum[key] += grid[cell]
                    break

        # Store the total cumulative adjustment for the term
        for key in grids:
            ra_per_path[key][idx_path] = adj_sum[key] * spacing[idx_path]

    return ra_per_path


def grid_lookup(grids, lats, lons, h3_res):
    """
    For each (lat, lon) pair resolve the h3 cell starting at the finest
    h3 resolution and falling back to coarser resolutions, returning the
    mean, SE and optional sigma adjustments for the given residual term.
    Locations outside all grid cells receive a correction of zero.

    :param grids:
        {key: {cell_id: value}} for one term/IMT, with a required "mean"
        key and optional "mean_se" and "sig" keys sharing its cell IDs.
    :param lats:
        Array of latitudes (either hypo or site lats, depending on term)
    :param lons:
        Array of longitudes (either hypo or site lons, depending on term)
    :param h3_res:
        Sorted list of h3 resolution levels (coarse to fine)
    :returns:
        {key: adjustment_vals}, each array of shape (len(lats),)
    """
    # Mean, SE and optional per-cell sigma share the same stored cell IDs.
    # Set arrays
    n = len(lats)
    values = {key: np.zeros(n) for key in grids}
    reference_grid = grids["mean"]
    found = np.zeros(n, dtype=bool)

    # Go over the h3 resolutions from finest to coarsest,
    # skipping locations already resolved at a finer level
    for res in reversed(h3_res):
        if found.all():
            break
        for i in np.where(~found)[0]:
            # Make a h3 cell for given hypo or site
            cell = h3.latlng_to_cell(lats[i], lons[i], res)
            if cell in reference_grid:
                # Assign each adjustment of the given term to the cell
                for key, grid in grids.items():
                    values[key][i] = grid[cell]
                found[i] = True

    return values


def adjust_sigma(sig_vals, cfg, sig_action, sig, tau, phi):
    """
    Apply the resolved per-cell or scalar sigma adjustment to its component.

    NOTE: Only one of grids[imt][term]["sig"]/sig_scalars can be populated
    per term/IMT - this is enforced when loading the grid cells.
    """
    # Get the component to modify: tau, phi or total sigma
    sig_comp = cfg["sig_comp_modified"]
    component = {"tau": tau, "phi": phi}.get(sig_comp, sig)

    # Adjust the selected component with the required action
    if sig_action == "replace":
        component[:] = sig_vals
    else:
        sign = -1 if sig_action == "sub" else 1
        component[:] = np.sqrt(component ** 2 + sign * sig_vals ** 2)

    # Recompute total sigma after adjusting tau or phi
    if sig_comp in ("tau", "phi"):
        sig[:] = np.sqrt(tau ** 2 + phi ** 2)


# Resolve central mean, optional SE and per-cell sigma in one spatial search.
def _resolve_adjs(grid_data, cfg, term, imt, ctx):
    # Path-based terms are stored in the raytrace grids. Mean / SE
    # are both returned uncapped here; the path_cap (if set) is applied
    # to the per-branch total (central + eps*SE) in compute()
    if cfg["location"] == "path":
        grid = grid_data["raytrace_grids"].get(term, {}).get(imt)
        if grid is None:
            return {}
        grids = {"mean": grid}
        se_grid = grid_data["raytrace_se_grids"].get(term, {}).get(imt)
        if se_grid is not None:
            grids["mean_se"] = se_grid
        cache = grid_data.setdefault("raytrace_masks", {})
        if (term, imt) not in cache:
            cache[term, imt] = _build_masks(grid, grid_data["h3_res"])
        masks = cache[term, imt]
        return _raytrace_path_adjs(
            grids, ctx.hypo_lon, ctx.hypo_lat, ctx.lon, ctx.lat,
            grid_data["h3_res"], masks)

    # Hypo/site terms are stored as cell_id -> value dicts
    entry = grid_data["grids"].get(imt, {}).get(term, {})
    if not entry:
        return {}
    lats, lons = ((ctx.hypo_lat, ctx.hypo_lon) if cfg["location"] == "hypo"
                  else (ctx.lat, ctx.lon))
    return grid_lookup(entry, lats, lons, grid_data["h3_res"])


def compute_central(gsim, ctx, imts, mean, sig, tau, phi):
    """
    Compute the backbone and the central grid corrections, i.e. the
    part of the result which is independent from the epsilons.

    :param gsim:
        GridAdjustedGMPE instance

    Fill the output arrays in place, applying central mean and configured
    sigma adjustments. Branch-specific epsilon * mean_se shifts and path
    caps are applied later by apply_epsilons.

    :param ctx:
        Context recarray with rupture, site and distance fields required
        by the backbone GMM and spatial correction lookups.
    :param imts:
        Sequence of IMT instances, in output array row order.
    :param mean:
        Mean output array of shape (len(imts), len(ctx)).
    :param sig:
        Total standard deviation output array, same shape as mean.
    :param tau:
        Inter-event standard deviation output array, same shape as mean.
    :param phi:
        Intra-event standard deviation output array, same shape as mean.
    :returns:
        A dict {(imt_index, term): (mean_adj, se_adj)} for terms with
        mean data. Each adjustment has shape (len(ctx),); se_adj is None
        when that term/IMT has no SE data.
    """
    grid_data = gsim.grid_data
    gsim.gmpe.compute(ctx, imts, mean, sig, tau, phi)
    resolved = {}
    for m, imt in enumerate(imts):
        # Apply each correction - example (term, cfg):
        #   term = 'dL2L'
        #   cfg  = {'location': 'hypo', 'sig_adjustment': 'sub',
        #           'sig_comp_modified': 'tau'}
        for term, cfg in grid_data["res_terms"].items():
            # Resolve central, SE and per-cell sigma together so each
            # branch only has to add its own eps * SE shift later
            adjs = _resolve_adjs(grid_data, cfg, term, str(imt), ctx)
            mean_adj, se_adj = adjs.get("mean"), adjs.get("mean_se")
            if mean_adj is None:
                # No central mean data for this term/IMT: skip correction
                continue
            resolved[m, term] = mean_adj, se_adj
            # Central mean and sigma adjustments do not depend on
            # epsilon, so they are added here
            mean[m] += mean_adj
            sig_action = cfg.get("sig_adjustment", "none")
            if sig_action != "none":
                # Resolve sigma values - per-cell grid or scalar.
                # Per-cell values share the mean lookup; otherwise
                # use the scalar
                scalars = grid_data["sig_scalars"].get(str(imt), {})
                sig_vals = adjs.get("sig", scalars.get(term))
                adjust_sigma(sig_vals, cfg, sig_action,
                             sig[m], tau[m], phi[m])
    return resolved


def apply_epsilons(gsim, resolved, imts, mean):
    """
    Add this branch's eps * mean_se shift to the central mean.

    :param gsim: GridAdjustedGMPE instance
    :param resolved: the dictionary returned by compute_central
    :param imts: sequence of IMT instances, in output array row order
    :param mean: central mean array of shape (len(imts), N)
    """
    # Terms with no mean data contributed nothing to the central mean
    # and are omitted from resolved. For path terms with path_cap set,
    # clip the per-branch total (central + eps*SE) so no single LT
    # realisation's path contribution can exceed the physical bound
    for (m, term), (mean_adj, se_adj) in resolved.items():
        eps = gsim.epsilons.get(term, 0.0)
        if eps != 0.0 and se_adj is None:
            raise ValueError(
                f"Non-zero epsilon requested for term '{term}' but "
                f"per-cell '{term}_mean_se' dataset is missing for "
                f"IMT '{imts[m]}'.")
        shift = eps * se_adj if eps != 0.0 else 0.0
        cfg = gsim.grid_data["res_terms"][term]
        if cfg["location"] == "path" and gsim.path_cap is not None:
            # mean_adj was already added uncapped in compute_central;
            # replace it with the capped (central + eps*SE) total
            shift = np.clip(mean_adj + shift,
                            -gsim.path_cap, gsim.path_cap) - mean_adj
        mean[m] += shift


class GridAdjustedGMPE(GMPE):
    """
    A GSIM class that applies spatially-varying corrections stored in
    a hdf5 file of h3-gridded residual terms to the underlying GMM.

    The hdf5 file contains a root-level attribute that configures the
    adjustment behaviour:

    * res_terms: A JSON-encoded dict mapping each top-level group name (each
      key is a corrective term e.g. dL2L) to a sub-dict with one mandatory key:

      * location: How to resolve the correction spatially, with each look-up
                  resolving the location to a h3 cell, searching from finest
                  to coarsest resolution. If a location falls outside all
                  grid cells then a correction of zero is applied:

        * hypo = Use the rupture hypocentre (ctx.hypo_lat, ctx.hypo_lon)

        * site = Use the site location (ctx.lat, ctx.lon)

        * path = Use raytracing to apply a travel path effect (e.g. an
                 attenuation rate per km per intersected grid cell)

      * sig_adjustment (optional, default "none"): Whether to adjust the
        corresponding GMM sigma component. When not "none", one of the
        following must be present in each IMT group for that term:

        * A scalar adjustment (group attribute "{term}_sig") - one value
          applied uniformly across all hypocentres or sites.

        * A dataset named "{term}_sig" - one value per h3 cell, looked up
          spatially in the same way as the mean adjustment (hypo or site
          location; not supported yet for path-based terms).

        NOTE: Providing both a scalar adjustment and a cell-by-cell adjustment
        raises an error - you must select exactly 1 for each sigma correction.

        Adjustment actions:

        * none = Skip sigma adjustment (only apply mean correction - in
                 this case no "{term}_sig" need be specified).

        * sub = Subtract variance from given sigma component (reduce sigma)

        * add = Add variance to given sigma component (inflate sigma)

        * replace = Use this value instead for given sigma component

      * sig_comp_modified (required when sig_adjustment is not "none"): Which
        std-dev component to adjust for the given residual term:

        * tau = Adjust inter-event std dev

        * phi = Adjust intra-event std dev

        * sig = Adjust total std dev

    An optional per-cell dataset "{term}_mean_se" may also be present in
    each IMT group for a term. This is the SE on the fitted central
    mean adjustment, resolved alongside the central mean and only applied
    when a non-zero epsilon is supplied for that term via "epsilons".

    NOTE: The corrective terms (each key in the res_terms dict) are not
    fixed - the user can specify as they wish (e.g. only include dS2S).

    NOTE: Corrections are stored per term per IMT in the HDF5. If an IMT
    group is missing for a given term, no correction is applied for that
    IMT (no error is raised).

    NOTE: The h3 grid cell resolution can vary (i.e., densify) or be constant.

    NOTE: The h3 cell IDs (i.e. the grids) are looked-up on an IMT-by-IMT
    basis because the availability of data used to derive the corrections
    might vary with period.

    A "real" example of this hdf5 structure can be found in the unit tests
    associated with this mgmpe module:
    openquake/hazardlib/tests/gsim/mgmpe/data/test_grid_adjustments.hdf5

    A use case (from XML) can be found in the classical QA tests (there is
    also a readme visualising the h3 grids stored in the hdf5):
    oq-engine/openquake/qa_tests_data/classical/case_11/grid_adjustments.hdf5

    :param gmpe_name:
        The underlying GMM to apply the grid-based adjustments to.

    :param grid_hdf5_file:
        Path to the hdf5 file with gridded adjustments.

    :param epsilons:
        Optional dict of per-term epsilons, e.g.
        {"dL2L": -1.732, "dS2S": 0.0, "adj_per_km": 1.732}. Each term's mean
        is shifted by epsilon * mean_se using the per-cell SE stored under
        "{term}_mean_se" in the HDF5. Terms not in the dict default to
        epsilon = 0 (central only, no shift). A non-zero epsilon raises an
        error if the matching SE dataset is missing.

    :param path_cap:
        Optional per-branch cap (nat-log units) on the stacked per-ray path
        term (central + eps * SE) only, clipped to [-path_cap, +path_cap].
        Hypo/site terms (dL2L, dS2S) are unaffected. Default None = no cap.
        A value of ln(2) ~ 0.693 bounds the multiplicative path factor at
        [0.5, 2.0] on every LT realisation. Useful for constraining long
        rays crossing many weakly-constrained cells, where the per-km
        shifts can stack into physically unrealistic path adjustments.
    """
    # Req Params - set from underlying GMM via set_parameters()
    REQUIRES_SITES_PARAMETERS = set()
    REQUIRES_DISTANCES = set()
    REQUIRES_RUPTURE_PARAMETERS = set()
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = ""
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set()
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}
    DEFINED_FOR_TECTONIC_REGION_TYPE = ""
    DEFINED_FOR_REFERENCE_VELOCITY = None

    experimental = True # It's not extensively tested yet

    def __init__(self, gmpe_name, grid_hdf5_file, epsilons=None,
                 path_cap=None, **kwargs):

        # Instantiate the underlying GMM
        self.gmpe = registry[gmpe_name](**kwargs)
        self.set_parameters()

        # Load grid-based corrections from the hdf5
        self.grid_data = load_residual_grids(grid_hdf5_file)

        # Per-ray path cap (in natural-log units), also exposed in grid_data.
        # None = no cap; compute() clips the per-branch total after lookup.
        if path_cap is not None and path_cap <= 0:
            raise ValueError(
                f"path_cap must be positive (natural-log units) or None, "
                f"got {path_cap!r}.")
        self.path_cap = path_cap
        self.grid_data["path_cap"] = path_cap

        # GridAdjustedGMPEs with the same central_key differ only by
        # epsilons and path_cap, so ContextMaker.get_mean_stds computes
        # their backbone and central grid adjustments only once
        self.central_key = (
            os.fspath(grid_hdf5_file), type(self.gmpe).__name__,
            repr(tuple(self.gmpe.kwargs.items())))

        # Per-term epsilons for epistemic SE shift (default 0.0 = central)
        self.epsilons = epsilons or {}
        unknown = set(self.epsilons) - set(self.grid_data["res_terms"])
        if unknown:
            # Reject typos rather than silently falling back to default
            raise ValueError(
                f"Unknown term(s) in epsilons: {sorted(unknown)}. "
                f"Known terms: {sorted(self.grid_data['res_terms'])}.")

        # Validate location assignments and expand the required
        # rupture/site parameter sets accordingly
        locations = {cfg["location"]
                     for cfg in self.grid_data["res_terms"].values()}
        invalid = locations - {"hypo", "site", "path"}
        if invalid:
            raise ValueError(
                f"Invalid location type(s) {sorted(invalid)} in res_terms "
                f"(must be 'hypo', 'site' or 'path').")
        # Add hypo lon/lat for hypo-based lookups and raytracing endpoints
        if locations & {"hypo", "path"}:
            self.REQUIRES_RUPTURE_PARAMETERS = frozenset(
                self.REQUIRES_RUPTURE_PARAMETERS | {'hypo_lat', 'hypo_lon'})
        # Add site lat/lon for site-based lookups and raytracing endpoints
        if locations & {"site", "path"}:
            self.REQUIRES_SITES_PARAMETERS = frozenset(
                self.REQUIRES_SITES_PARAMETERS | {'lat', 'lon'})

        # Ensure inter/intra-event std devs are computed by the base GSIM
        if any(cfg.get("sig_adjustment", "none") != "none"
               and cfg.get("sig_comp_modified") in ("tau", "phi")
               for cfg in self.grid_data["res_terms"].values()):
            required = {const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}
            # Raise error if not a random-effects GSIM
            if not required.issubset(
                    self.DEFINED_FOR_STANDARD_DEVIATION_TYPES):
                raise ValueError(
                    "Adjustments to tau and/or phi have been specified "
                    "but the underlying GSIM does not support "
                    "random-effects residuals.")

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        resolved = compute_central(self, ctx, imts, mean, sig, tau, phi)
        apply_epsilons(self, resolved, imts, mean)
