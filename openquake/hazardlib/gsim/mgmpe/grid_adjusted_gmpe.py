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
:mod:`openquake.hazardlib.gsim.mgmpe.grid_adjusted_gmpe` implements
:class:`GridAdjustedGMPE`, a GSIM wrapper that adds spatially-varying
non-ergodic corrections stored in an HDF5 file on top of any underlying
GMM.
"""
import json
import h5py
import h3
import numpy as np

from openquake.hazardlib import const
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.polygon import Polygon
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.geodetic import npoints_between, distance
from openquake.hazardlib.gsim.base import GMPE, registry, CoeffsTable
from openquake.hazardlib.imt import from_string as imt_from_string

# CoeffsTable treats PGA as SA at this period during log-period interpolation,
# and only allows that fallback when the smallest tabulated SA period is
# no larger than PGA_ANCHOR_MAX_SA.
PGA_ANCHOR_PERIOD = 0.01
PGA_ANCHOR_MAX_SA = 0.05
VALID_TARGETS = ("hypo", "site", "path")


### Helpers for loading HDF5 ###

def load_residual_grids(hdf5_path):
    """
    Read the HDF5 of gridded adjustments and return the dict that
    :class:`GridAdjustedGMPE` uses during call to compute method.

    Keys in the returned dict:

    * "grids"             - {imt_str: {term: {"mean": {cell_id: val},
                                              "sig":  {cell_id: val}}}}
                            for hypo/site terms; "sig" present only when
                            per-cell sigma is configured

    * "raytrace_grids"    - {term: {imt_str: {cell_id: (Polygon, val)}}}
                            for path adjustments
                            
    * "sig_scalars"       - {imt_str: {term: float}} scalar per-IMT sigmas

    * "h3_res"            - sorted list of h3 resolutions found across all
                            stored cells (coarsest first)

    * "res_terms"         - the JSON config from the HDF5 root attribute

    * "cell_tables"       - per-cell CoeffsTables for hypo/site terms, used
                            at compute time to interpolate across IMTs

    * "path_tables"       - (Polygon, CoeffsTable) per path cell

    * "scalar_sig_tables" - one CoeffsTable per term for the scalar per-IMT
                            sigmas

    * "stored_periods"    - {term: sorted list of IMT strings at which the
                            term is stored}, used to prevent extrapolation
    """
    grids = {}
    raytrace_grids = {}
    sig_scalars = {}
    resolutions = set()

    # Read every (term, IMT) group in the hdf5 file into the plain per-cell dicts
    with h5py.File(hdf5_path, "r") as hf:
        res_terms = json.loads(hf.attrs["res_terms"])
        for term, cfg in res_terms.items():
            for imt_str in hf[term]:
                _load_one_term_imt(
                    hf[term][imt_str], term, imt_str, cfg,
                    grids, raytrace_grids, sig_scalars, resolutions
                    )

    # Build CoeffsTables so a compute-time query for a target IMT that is
    # not in the HDF5 can be answered by log-period interpolation.
    cell_tables, path_tables, scalar_sig_tables, stored_periods = (
        _build_interp_tables(grids, raytrace_grids, sig_scalars, res_terms))

    return {
        "grids": grids,
        "raytrace_grids": raytrace_grids,
        "sig_scalars": sig_scalars,
        "h3_res": sorted(resolutions),
        "res_terms": res_terms,
        "cell_tables": cell_tables,
        "path_tables": path_tables,
        "scalar_sig_tables": scalar_sig_tables,
        "stored_periods": stored_periods,
    }


def _load_one_term_imt(grp, term, imt_str, cfg,
                       grids, raytrace_grids, sig_scalars, resolutions):
    """
    Load the mean adjustment (and optional sigma) stored in one HDF5
    group into the caller-provided dicts.

    See "load_residuals_grids" docstring for description of each argument
    inputted into this.
    """
    # Get location-type
    location = cfg["location"]

    # Get sigma adjustment
    sig_action = cfg.get("sig_adjustment", "none")

    # Cell IDs and mean values must/should always be present; collect the
    # h3 resolution of every stored cell for the spatial fallback
    cell_ids = grp["cell_id"][:].astype(str)
    mean_vals = grp[term][:]
    resolutions.update(h3.get_resolution(c) for c in cell_ids)

    # Path terms need OQ polygons ready for ray-tracing; hypo/site terms
    # just need a {cell_id -> mean} dict for the point-in-cell h3 lookup
    grids.setdefault(imt_str, {})
    sig_scalars.setdefault(imt_str, {})
    if location == "path":
        raytrace_grids.setdefault(term, {})[imt_str] = _build_raytrace_grid(
            cell_ids, mean_vals)
    else:
        grids[imt_str][term] = {"mean": dict(zip(cell_ids, mean_vals))}

    if sig_action != "none":
        # Need the sigma adjustments too then
        _load_sigma(grp, term, imt_str, location, cell_ids, grids, sig_scalars)


def _load_sigma(grp, term, imt_str, location, cell_ids, grids, sig_scalars):
    """
    Read the sigma adjustment for one (term, IMT). Sigma is stored either
    as a scalar HDF5 group attribute or as a per-cell dataset - never
    both, and for path terms the per-cell option is NOT supported.
    """
    # Check present sigma adjustments
    sig_key = f"{term}_sig"
    scalar_sig = sig_key in grp.attrs
    per_cell_sig = sig_key in grp

    # Cannot have both per-cell and single scalar sigma adjustment for
    # a given term
    if scalar_sig and per_cell_sig:
        raise ValueError(
            f"Both scalar attribute and dataset '{sig_key}' found for "
            f"term '{term}', IMT '{imt_str}'; provide exactly one.")

    # And need to make sure sigma adjustment is available for given IMT too
    if not (scalar_sig or per_cell_sig):
        raise ValueError(
            f"Sigma adjustment requested for term '{term}' but "
            f"'{sig_key}' is missing for this IMT '{imt_str}'.")

    # If scalar sigma adjustment check not negative and update adjustment dict
    if scalar_sig:
        val = float(grp.attrs[sig_key])
        if val < 0:
            raise ValueError(
                f"Negative sigma for term '{term}', IMT '{imt_str}'.")
        sig_scalars[imt_str][term] = val
        # If it's scalar sigma (not per cell) then finish here
        return

    # Make sure no per-cell sigma requested for path-based adjustment 
    if location == "path":
        # By this point can only be per-cell adjustment so raise error
        raise ValueError(
            f"Per-cell sigma is not supported for path terms "
            f"(term '{term}'); use a scalar attribute instead."
            )

    # Make sure no negative sigma adjustment values over all cells
    vals = grp[sig_key][:]
    if np.any(vals < 0):
        raise ValueError(
            f"Negative sigma value for term '{term}', IMT '{imt_str}'.")
    
    grids[imt_str][term]["sig"] = dict(zip(cell_ids, vals))


def _build_raytrace_grid(cell_ids, mean_vals):
    """
    Turn a set of h3 cell IDs into (OQ Polygon, per-km value) pairs
    ready for ray-tracing.
    """
    grid = {}
    for cid, val in zip(cell_ids, mean_vals):
        pnts = [Point(p[0], p[1]) for p in h3.cell_to_boundary(cid)]
        grid[cid] = (Polygon(pnts), float(val))
    return grid


### Helpers for building the interpolation tables ###

def _build_interp_tables(grids, raytrace_grids, sig_scalars, res_terms):
    """
    Assemble the per-term stores used at compute time to interpolate
    across IMTs. Returns four dicts (see :func:`load_residual_grids`
    for the full description of each).
    """
    cell_tables, path_tables, scalar_sig_tables, stored_periods = (
        {}, {}, {}, {})

    for term, cfg in res_terms.items():
        # Mean-adjustment CoeffsTables (per-cell), and the list of IMTs at
        # which this term is stored.
        if cfg["location"] == "path":
            path_tables[term] = _build_path_ct(raytrace_grids.get(term, {}))
            imt_strs = list(raytrace_grids.get(term, {}))
        else:
            cell_tables[term] = _build_hypo_site_ct(grids, term)
            imt_strs = [s for s, td in grids.items() if term in td]

        # One CoeffsTable per term for the scalar sigmas (if any).
        sig_table = _build_scalar_sig_ct(sig_scalars, term)
        if sig_table is not None:
            scalar_sig_tables[term] = sig_table

        # Sort the IMTs by period for the extrapolation check.
        stored_periods[term] = sorted(
            imt_strs, key=lambda s: imt_from_string(s).period)

    return cell_tables, path_tables, scalar_sig_tables, stored_periods


def _build_hypo_site_ct(grids, term):
    """
    Per-cell CoeffsTable for a hypo/site term. Each table's rows are the
    IMTs where the cell has stored data; columns are ``mean`` and, if
    per-cell sigma was configured, ``sig``.
    """
    per_cell = {}
    for imt_str, term_dict in grids.items():
        if term not in term_dict:
            continue
        imt_obj = imt_from_string(imt_str)
        mean_dict = term_dict[term]["mean"]
        sig_dict = term_dict[term].get("sig") or {}
        for cell_id, mval in mean_dict.items():
            row = {"mean": float(mval)}
            if cell_id in sig_dict:
                row["sig"] = float(sig_dict[cell_id])
            per_cell.setdefault(cell_id, {})[imt_obj] = row
    return {cid: CoeffsTable.fromdict(rows)
            for cid, rows in per_cell.items()}


def _build_path_ct(term_raytrace_grids):
    """
    (Polygon, CoeffsTable) per path cell. The CoeffsTable holds one
    column (``mean``) indexed by the IMTs where the cell was stored.
    """
    per_cell = {}
    for imt_str, cell_dict in term_raytrace_grids.items():
        imt_obj = imt_from_string(imt_str)
        for cell_id, (pgn, val) in cell_dict.items():
            per_cell.setdefault(cell_id, (pgn, {}))[1][imt_obj] = {
                "mean": float(val)}
    return {cid: (pgn, CoeffsTable.fromdict(rows))
            for cid, (pgn, rows) in per_cell.items()}


def _build_scalar_sig_ct(sig_scalars, term):
    """
    Per-term CoeffsTable of scalar per-IMT sigmas, or None if this term
    has no scalar sigma stored.
    """
    rows = {imt_from_string(s): {"sig": float(sig_scalars[s][term])}
            for s in sig_scalars if term in sig_scalars[s]}
    return CoeffsTable.fromdict(rows) if rows else None


### Helpers for compute-time interpolation of missing IMTs ###
def _check_in_range(imt, stored_imt_strs, term):
    """
    Raise ValueError if the target IMT period is outside the range in
    which CoeffsTable can actually interpolate for this term.
    
    PGA counts as SA at PGA_ANCHOR_PERIOD only when the smallest stored
    SA period is <= PGA_ANCHOR_MAX_SA (which is when CoeffsTable's
    PGA-anchored fallback kicks in). Otherwise otherwise the lower bound
    is the smallest stored SA period.
    """
    if imt.string == "PGA":
        return

    has_pga = "PGA" in stored_imt_strs
    sa_periods = sorted(
        imt_from_string(s).period for s in stored_imt_strs if s != "PGA")
    p = imt.period

    if sa_periods:
        if p > sa_periods[-1]:
            raise ValueError(
                f"Cannot interpolate {imt} for term '{term}': target "
                f"period {p}s above stored SA range "
                f"(max {sa_periods[-1]}s).")
        if p >= sa_periods[0]:
            return  # Target sits inside the stored SA range.

    # Target is below the smallest stored SA period (or there are no SAs
    # at all). Only the PGA-anchored fallback can rescue that, and it
    # only kicks in when the smallest SA is <= PGA_ANCHOR_MAX_SA and the
    # target is >= PGA_ANCHOR_PERIOD.
    fallback_ok = (has_pga and p >= PGA_ANCHOR_PERIOD
                   and (not sa_periods or sa_periods[0] <= PGA_ANCHOR_MAX_SA))
    if not fallback_ok:
        raise ValueError(
            f"Cannot interpolate {imt} for term '{term}': target period "
            f"{p}s below the interpolable range (need SA at <= "
            f"{PGA_ANCHOR_MAX_SA}s or a stored SA period at <= {p}s).")


def _ensure_imt_available(grid_data, imt, imt_str):
    """
    Populate any missing per-term entries for given IMT by log-period
    interpolation of the CoeffsTable objects built at load time.
    
    Extrapolation raises a value-error.
    """
    for term, cfg in grid_data["res_terms"].items():
        stored = grid_data["stored_periods"].get(term, [])
        if not stored or imt_str in stored:
            continue

        _check_in_range(imt, stored, term)

        if cfg["location"] == "path":
            grid_data["raytrace_grids"][term][imt_str] = _interp_path(
                grid_data["path_tables"][term], imt)
        else:
            grid_data["grids"].setdefault(imt_str, {})[term] = (
                _interp_hypo_site(grid_data["cell_tables"][term], imt))

        if term in grid_data["scalar_sig_tables"]:
            grid_data["sig_scalars"].setdefault(imt_str, {})[term] = float(
                grid_data["scalar_sig_tables"][term][imt]["sig"])


def _interp_hypo_site(cell_tables, imt):
    """
    Build a hypo/site entry at the target IMT by log-period interpolating
    each cell's CoeffsTable. Cells that can't bracket the target are
    dropped; the compute-time spatial fallback then reaches for a
    coarser cell that survived.
    """
    has_sig = "sig" in next(iter(cell_tables.values())).rb.names
    means = {}
    sigs = {} if has_sig else None
    for cell_id, ct in cell_tables.items():
        try:
            rec = ct[imt]
        except (KeyError, ValueError):
            continue
        means[cell_id] = float(rec["mean"])
        if has_sig:
            sigs[cell_id] = float(rec["sig"])
    entry = {"mean": means}
    if has_sig:
        entry["sig"] = sigs
    return entry


def _interp_path(path_tables, imt):
    """
    Build a raytrace grid at the target IMT by log-period interpolating
    each path cell's per-km value. Cells that can't bracket the target
    are dropped from the resulting grid.
    """
    grid = {}
    for cell_id, (pgn, ct) in path_tables.items():
        try:
            grid[cell_id] = (pgn, float(ct[imt]["mean"]))
        except (KeyError, ValueError):
            continue
    return grid


### Helpers for compute-time spatial lookup and ray-tracing ###

def grid_lookup(grid_dict, lats, lons, h3_res):
    """
    Point-in-cell lookup with a finest -> coarsest fallback. Locations
    outside every stored cell receive a correction of zero.

    :param grid_dict:
        {cell_id: mean_adjustment_value} for one term and one IMT.
    :param lats:
        Array of latitudes (hypocentre or site, depending on the term).
    :param lons:
        Array of longitudes.
    :param h3_res:
        Sorted list of h3 resolution levels (coarsest first).
    """
    n = len(lats)
    vals = np.zeros(n)
    found = np.zeros(n, dtype=bool)

    # Once a site is resolved at a finer resolution it stays there.
    for res in reversed(h3_res):
        if found.all():
            break
        for i in np.where(~found)[0]:
            cell = h3.latlng_to_cell(lats[i], lons[i], res)
            if cell in grid_dict:
                vals[i] = grid_dict[cell]
                found[i] = True

    return vals


def raytrace_path_adj(grid, hypo_lons, hypo_lats, site_lons, site_lats):
    """
    For each (hypo, site) pair, accumulate a per-km adjustment over the
    portion of the path that lies inside each stored polygon.

    :param grid:
        {cell_id: (Polygon, per_km_value)} for one path term and one IMT.
    :param hypo_lons, hypo_lats, site_lons, site_lats:
        Matching arrays of hypocentre / site coordinates.
    :returns:
        Array of shape (len(hypo_lons),).
    """
    n_paths = len(hypo_lons)
    adjustments = np.zeros(n_paths)

    for i in range(n_paths):
        # Discretise the hypo -> site line into 100 points; the constant
        # spacing between consecutive points is the sampling step.
        line = npoints_between(
            site_lons[i], site_lats[i], 0.0,
            hypo_lons[i], hypo_lats[i], 0.0, 100)
        mesh = Mesh(line[0], line[1])
        spacing = distance(
            mesh.lons[0], mesh.lats[0], 0.0,
            mesh.lons[1], mesh.lats[1], 0.0)

        # Per cell: add (#discrete points inside) * spacing * per_km_value.
        total = 0.0
        for polygon, per_km in grid.values():
            total += (np.count_nonzero(polygon.intersects(mesh))
                      * spacing * per_km)
        adjustments[i] = total

    return adjustments


### Helpers for compute-time correction assembly ###

def _mean_adj_hypo_site(entry, cfg, ctx, h3_res):
    """Per-site mean adjustment for one hypo/site term."""
    if cfg["location"] == "hypo":
        lats, lons = ctx.hypo_lat, ctx.hypo_lon
    else:
        lats, lons = ctx.lat, ctx.lon
    return grid_lookup(entry["mean"], lats, lons, h3_res)


def _mean_adj_path(grid, ctx):
    """Per-rupture mean adjustment for one path term (via ray-tracing)."""
    return raytrace_path_adj(
        grid, ctx.hypo_lon, ctx.hypo_lat, ctx.lon, ctx.lat)


def _sigma_values(grid_data, term, cfg, imt_str, ctx):
    """
    Return the per-record sigma adjustment values for one term at
    ``imt_str``. Sigma may be stored per-cell (looked up spatially) or
    as a single scalar per IMT.
    """
    per_cell = grid_data["grids"].get(imt_str, {}).get(term, {}).get("sig")
    if per_cell is not None:
        if cfg["location"] == "hypo":
            lats, lons = ctx.hypo_lat, ctx.hypo_lon
        else:
            lats, lons = ctx.lat, ctx.lon
        return grid_lookup(per_cell, lats, lons, grid_data["h3_res"])
    return grid_data["sig_scalars"].get(imt_str, {}).get(term)


def _apply_sigma(action, comp, adj, sig, tau, phi):
    """
    Modify the requested sigma component in place. Actions:

    * ``replace`` - overwrite the component with the adjustment value.
    * ``sub``     - subtract the adjustment in quadrature.
    * ``add``     - add the adjustment in quadrature.

    When ``comp`` is ``tau`` or ``phi`` the total sigma is recomputed
    from them after the update.
    """
    components = {"tau": tau, "phi": phi, "sig": sig}
    target = components[comp]
    if action == "replace":
        target[:] = adj
    else:
        sign = -1 if action == "sub" else 1
        target[:] = np.sqrt(target ** 2 + sign * adj ** 2)
    if comp != "sig":
        sig[:] = np.sqrt(tau ** 2 + phi ** 2)


def _apply_one_term(grid_data, term, cfg, imt_str, ctx,
                    mean, sig, tau, phi):
    """Apply the mean (and optional sigma) adjustment for a single term."""
    if cfg["location"] == "path":
        grid = grid_data["raytrace_grids"].get(term, {}).get(imt_str)
        if grid is None:
            return
        mean += _mean_adj_path(grid, ctx)
    else:
        entry = grid_data["grids"].get(imt_str, {}).get(term)
        if entry is None:
            return
        mean += _mean_adj_hypo_site(entry, cfg, ctx, grid_data["h3_res"])

    sig_action = cfg.get("sig_adjustment", "none")
    if sig_action == "none":
        return
    adj = _sigma_values(grid_data, term, cfg, imt_str, ctx)
    _apply_sigma(sig_action, cfg["sig_comp_modified"], adj, sig, tau, phi)


def _apply_grid_corrections(grid_data, ctx, imt, mean, sig, tau, phi):
    """
    Apply every stored (or interpolated) term to the compute() outputs
    for a single target IMT. Raises ValueError on extrapolation.
    """
    # If this IMT isn't in the HDF5, fill it in by log-period interpolation
    # of the CoeffsTable objects built at load time for each term's cells (nb
    # we have per grid cell a CoeffTable by considering values it contains over
    # all the IMT-based adjustments available within it)
    _ensure_imt_available(grid_data, imt, str(imt))
    imt_str = str(imt)
    for term, cfg in grid_data["res_terms"].items():
        _apply_one_term(
            grid_data, term, cfg, imt_str, ctx, mean, sig, tau, phi)


### Helpers for checking/ensuring GMM can be adjusted ###
def _validate_res_terms(res_terms, defined_stddev_types):
    """
    Rejects invalid location target types for the adjustment and refuse
    to modify tau/phi for a GMM that lacks tau and phi sigma components.
    """
    needs_random_effects = False
    for cfg in res_terms.values():
        if cfg["location"] not in VALID_TARGETS:
            # Check it is hypocentre, site or path-based adjustment
            raise ValueError(
                f"Invalid location {cfg['location']!r}; must be one "
                f"of {VALID_TARGETS}.")
        if (cfg.get("sig_adjustment", "none") != "none"
                and cfg.get("sig_comp_modified") in ("tau", "phi")):
            # If sigma adjstment to tau/phi then set this True
            needs_random_effects = True

    if needs_random_effects:
        # If here we are adjusting tau/phi so check GMM has them 
        required = {const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}
        if not required.issubset(defined_stddev_types):
            raise ValueError(
                "Adjustments to tau and/or phi were configured but the "
                "underlying GSIM does not have tau/phi sigma components.")


def _extend_required_parameters(res_terms, current_rup, current_site):
    """
    Extend the required rupture / site parameter sets required for the
    modification of the underlying GMM based on which location lookups
    the "res_terms" use.
    """
    # Get the target types in the config
    locations = {cfg["location"] for cfg in res_terms.values()}
    rup = current_rup # Existing rup params in GMM
    site = current_site # Existing site params in GMM
    if locations & {"hypo", "path"}:
        # Add them for hypo-based or path-based
        rup = frozenset(rup | {"hypo_lat", "hypo_lon"})
    if locations & {"site", "path"}:
        # Add them for site-based or path based
        site = frozenset(site | {"lat", "lon"})

    return rup, site


class GridAdjustedGMPE(GMPE):
    """
    A GSIM class that adds spatially-varying corrections stored in a
    HDF5 file of h3-gridded residual terms on top of any underlying GMM
    (which in theory is your backbone model used to compute these residual
    terms).

    NOTE: This class/capability is highly experimental.

    The HDF5 file has a root-level attribute "res_terms" that configures each
    corrective term (e.g. "dL2L", "dS2S, "att_per_km").
    
    Every term specifies:

    * "location" (required): how to resolve the correction spatially. The
      lookup starts at the finest h3 resolution and falls back to coarser
      resolutions; locations outside all cells receive zero:

        * "hypo" = use the rupture hypocentre ("ctx.hypo_lat", "ctx.hypo_lon")
        * "site" = use the site location ("ctx.lat", "ctx.lon")
        * "path" = ray-trace from hypocentre to site through the stored cells,
           accumulating a per-km adjustment along the way

    * "sig_adjustment" (optional, default "none"): what to do to the sigma
      component. When not "none", sigma must be provided for each IMT group
      of that term as either:

        * a scalar HDF5 group attribute keyed by "{term}_sig"
        
        OR
        
        * a HDF5 dataset (also keyed by "{term}_sig") giving one value per h3
          cell (looked up spatially the same way as the mean) 
        
          NOTE: Per-cell sigma is not supported for path terms

        Actions:

            * "none" = skip sigma adjustment (mean-only correction)
            * "sub" = subtract variance from the chosen component
            * "add" = add variance to the chosen component
            * "replace" = overwrite the chosen component with the value

    * "sig_comp_modified" (required when "sig_adjustment" != "none") is the
      std-dev component to modify ("tau", "phi" or "sig").

    NOTE

    * The set of terms is not fixed - the user is free to include only
      the ones they need (and thus include only those in the HDF5 they
      provide).

    * Corrections are stored per term per IMT. When the target IMT is
      not stored, the mean and sigma corrections are filled in on the
      fly by log-period interpolation of :class:`CoeffsTable` objects
      built at load time.
      
    * Extrapolation beyond the stored period range raises a value-error.
      PGA counts as SA at 0.01 s for the lower bound only when the smallest
      stored SA period is <= 0.05 s (same as :class:`CoeffsTable`'s PGA
      anchored fallback); otherwise a target IMT below the smallest stored
      SA period is rejected. TODO: If a term has no stored data at all it is
      silently skipped for every target IMT.

    * The h3 grid cell resolution can vary over IMT because the
      calibration data may vary with period. When interpolating across
      IMTs, cells whose per-cell CoeffsTable cannot bracket the target
      IMT are dropped from the resulting grid at that IMT; the coarsest
      -> finest spatial fallback then resolves each site through a
      coarser cell when available.

    A real HDF5 example is used by the unit tests
    (``openquake/hazardlib/tests/gsim/mgmpe/data/test_grid_adjustments.hdf5``)
    and by the classical QA test case_11
    (``openquake/qa_tests_data/classical/case_11/grid_adjustments.hdf5``,
    including a README with visualisations of the grids).

    :param gmpe_name:
        Underlying GMM to which the grid-based adjustments are applied.
    :param grid_hdf5_file:
        Path to the HDF5 file with the gridded adjustments.
    """
    # Filled in by set_parameters() from the underlying GMM.
    REQUIRES_SITES_PARAMETERS = set()
    REQUIRES_DISTANCES = set()
    REQUIRES_RUPTURE_PARAMETERS = set()
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = ""
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set()
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}
    DEFINED_FOR_TECTONIC_REGION_TYPE = ""
    DEFINED_FOR_REFERENCE_VELOCITY = None

    experimental = True  # not extensively tested yet

    def __init__(self, gmpe_name, grid_hdf5_file, **kwargs):
        # Wrap the underlying GMM and copy its declared parameters
        self.gmpe = registry[gmpe_name](**kwargs)
        self.set_parameters()

        # Load the HDF5 once at construction time
        self.grid_data = load_residual_grids(grid_hdf5_file)

        # Validate the config and extend the required parameters
        _validate_res_terms(
            self.grid_data["res_terms"],
            self.DEFINED_FOR_STANDARD_DEVIATION_TYPES)
        
        self.REQUIRES_RUPTURE_PARAMETERS, self.REQUIRES_SITES_PARAMETERS = (
            _extend_required_parameters(
                self.grid_data["res_terms"],
                self.REQUIRES_RUPTURE_PARAMETERS,
                self.REQUIRES_SITES_PARAMETERS))

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>` for the input and
        result-value spec.
        """
        # Get the base-GMM outputs, then add the grid
        # corrections on top for each requested IMT
        self.gmpe.compute(ctx, imts, mean, sig, tau, phi)
        for m, imt in enumerate(imts):
            _apply_grid_corrections(
                self.grid_data, ctx, imt, mean[m], sig[m], tau[m], phi[m]
                )
