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
import math
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

# PGA stands in for SA at "PGA_ANCHOR_PERIOD" during log-period interp,
# but only when the smallest stored SA period is <= PGA_ANCHOR_MAX_SA
PGA_ANCHOR_PERIOD = 0.01
PGA_ANCHOR_MAX_SA = 0.05


### Centralised handler for per-ctx-row interpolation failures ###
def _handle_interp_failure(term, imt, reason, **context):
    """
    Single hook for every per-ctx-row case where an adjustment at the
    target IMT would distort the spectral shape (partial coverage).
    """
    # Uniformly uncovered ctx rows are not routed here; they get 0 so
    # the spectrum stays uniformly ergodic at that ctx row
    details = ", ".join(f"{k}={v}" for k, v in context.items())
    raise ValueError(
        f"GridAdjustedGMPE failed to interpolate term {term!r} at "
        f"{imt}: {reason}" + (f" [{details}]" if details else ""))


def _loc_covered_at_any_period(grids, term, key, lat, lon,
                               h3_res, stored_periods):
    """
    True if (lat, lon) sits inside a stored cell for term / key
    at any of stored_periods.
    """
    for p_str in stored_periods:
        d = grids[p_str][term].get(key)
        if d is None:
            continue
        for res in reversed(h3_res):
            if h3.latlng_to_cell(lat, lon, res) in d:
                return True
    return False


### Helpers for log-period interpolation at target IMT ###
def _check_in_range(imt, term_period_info, term):
    """
    Raise ValueError if the target IMT is outside the overall
    log-period interpolable range of this term.
    """
    # Can only interp SA
    if not imt.string.startswith("SA("):
        raise ValueError(
            f"Cannot interpolate {imt} for term '{term}': only SA IMTs "
            f"can be filled in by log-period interpolation; PGA and "
            f"other non-SA IMTs must be provided directly in the HDF5.")

    # Get teh period info already parsed from the hdf5
    has_pga = term_period_info["has_pga"]
    sa_periods = term_period_info["sa_periods"]

    # Get period and check if we can interpolate
    p = imt.period
    if sa_periods:
        if p > sa_periods[-1]:
            raise ValueError(
                f"Cannot interpolate {imt} for term '{term}': target "
                f"period {p}s above stored SA range "
                f"(max {sa_periods[-1]}s)."
                )
        if p >= sa_periods[0]:
            return  # Target period sits inside the stored SA range

    # Below the smallest stored SA: PGA may anchor the interp, but only
    # if PGA is stored and the smallest SA is <= PGA_ANCHOR_MAX_SA also
    fallback_ok = (has_pga and p >= PGA_ANCHOR_PERIOD
                   and sa_periods and sa_periods[0] <= PGA_ANCHOR_MAX_SA)
    if not fallback_ok:
        raise ValueError(
            f"Cannot interpolate {imt} for term '{term}': target period "
            f"{p}s below the interpolable range (need PGA plus a stored "
            f"SA period at <= {PGA_ANCHOR_MAX_SA}s to anchor against)."
            )


def _log_period_interp(target_period, pairs):
    """
    Linear log-period interpolation at target_period over sorted
    (period, value) in "pairs". Returns None if target_period cannot
    be bracketed below and above.
    """
    below = None
    above = None
    # Iterate over the stored 
    for p, v in pairs:
        # Exact match: only fires when the target is SA(0.01) and
        # PGA sits in pairs as the lower log(T) anchor at 0.01s;
        # the anchor's value is the answer at the target period
        if p == target_period:
            return v
        # Pair sits below the target period
        if p < target_period:
            below = (p, v)
        # Pair sits above the target period
        else:
            above = (p, v)
            break

    # No anchor on one side -> cannot bracket -> unbracketed
    if below is None or above is None:
        return None
    
    # Linear interp in log(period) between the two anchor "pairs
    ratio = ((math.log(target_period) - math.log(below[0])) /
             (math.log(above[0]) - math.log(below[0])))
    
    return below[1] + ratio * (above[1] - below[1])


def _bracket_failure_reason(target_period, pairs, per_period_vals, i):
    """
    Classify why _log_period_interp returned None for ctx row i. It can
    be because target period is above-range, PGA stored but anchor gap
    too wide, or because target period is below-range.
    """
    if target_period > pairs[-1][0]:
        return (f"target period {target_period}s above ctx row's local "
                f"max SA period ({pairs[-1][0]}s): extrapolation")

    pga_arr = per_period_vals.get("PGA")
    pga_at_row = pga_arr is not None and not np.isnan(pga_arr[i])
    smallest_sa = pairs[0][0]

    if pga_at_row and smallest_sa > PGA_ANCHOR_MAX_SA:
        return (f"PGA is stored at this ctx row but the smallest local "
                f"SA period ({smallest_sa}s) exceeds the PGA anchor "
                f"gap (<= {PGA_ANCHOR_MAX_SA}s), so PGA cannot anchor "
                f"the interp at target {target_period}s")

    return (f"target period {target_period}s below ctx row's local min "
            f"SA period ({smallest_sa}s) with no usable PGA anchor: "
            f"extrapolation")


def _ctx_row_pairs(per_period_vals, periods_sec, i):
    """
    Row i (i.e., ctx[i]) of each per-period array as a sorted
    (period, value) list - e.g. [(0.1, 0.2), (0.2, 0.25)] where
    position 0 is SA(0.1) and position 1 is SA(0.2) for some term
    e.g. dL2L.
    
    PGA is only permitted as the anchor when the smallest retrieved
    period at the row is <= PGA_ANCHOR_MAX_SA of 0.05 seconds (like
    in CoeffsTable).
    """
    pga_val = None
    sa_pairs = []
    
    for p_str, arr in per_period_vals.items():
        v = arr[i]
        if np.isnan(v):
            continue
        if p_str == "PGA":
            pga_val = float(v)
        else:
            sa_pairs.append((periods_sec[p_str], float(v)))
    
    sa_pairs.sort()

    if (pga_val is not None and sa_pairs
            and sa_pairs[0][0] <= PGA_ANCHOR_MAX_SA):
        return [(PGA_ANCHOR_PERIOD, pga_val)] + sa_pairs
    
    return sa_pairs


### Helpers for scalar per-IMT sigma interpolation ###
def _build_scalar_sig_ct(sig_scalars, term):
    """
    Per-term CoeffsTable of scalar per-IMT sigmas, or None if "term"
    has no scalar sigma stored.
    """
    rows = {imt_from_string(s): {"sig": float(sig_scalars[s][term])}
            for s in sig_scalars if term in sig_scalars[s]}
    return CoeffsTable.fromdict(rows) if rows else None


### Helpers for compute-time spatial lookup and ray-tracing ###

def grid_lookup(grid_dict, lats, lons, h3_res, default=0.0):
    """
    Point-in-cell lookup over grid_dict with a finest-to-coarsest
    fallback; locations outside every stored cell receive default.
    """
    n = len(lats)
    vals = np.full(n, default, dtype=float)
    found = np.zeros(n, dtype=bool)

    # Finest-first: once resolved at a finer resolution the location stays there
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
    Per (hypo, site) pair: accumulate the per-km adjustment along the
    portion of the ray inside each stored polygon of "grid".
    """
    n_paths = len(hypo_lons)
    adjustments = np.zeros(n_paths)

    for i in range(n_paths):
        # 100 equally-spaced samples along the site-hypo ray
        line = npoints_between(
            site_lons[i], site_lats[i], 0.0,
            hypo_lons[i], hypo_lats[i], 0.0, 100)
        mesh = Mesh(line[0], line[1])
        # km between consecutive samples (constant since equally-spaced)
        spacing = distance(
            mesh.lons[0], mesh.lats[0], 0.0,
            mesh.lons[1], mesh.lats[1], 0.0)

        # Per cell: (samples inside cell) * spacing approximates the ray
        # length in km inside that cell; * per_km gives its contribution
        total = 0.0
        for polygon, per_km in grid.values():
            total += (np.count_nonzero(polygon.intersects(mesh))
                      * spacing * per_km)
        adjustments[i] = total

    return adjustments


### Helpers for compute-time correction assembly ###

def _hypo_site_coords(cfg, ctx):
    """
    Return (lats, lons) from ctx for a hypo/site term's lookup.
    """
    if cfg["location"] == "hypo":
        return ctx.hypo_lat, ctx.hypo_lon
    return ctx.lat, ctx.lon


def _per_loc_log_interp(grids, term, key, target_imt, lats, lons,
                        h3_res, stored_periods, periods_sec):
    """
    Per-location log-period interp over per-period finest-cell lookups;
    uniform misses stay 0, partial-coverage bracket fails raise.
    """
    # Per stored period: per-location value with NaN meaning "no cell here"
    per_period_vals = {}
    for p_str in stored_periods:
        term_at_p = grids[p_str][term]
        if key not in term_at_p:
            continue
        per_period_vals[p_str] = grid_lookup(
            term_at_p[key], lats, lons, h3_res, default=np.nan)

    target_period = target_imt.period

    # Per location: assemble local (period, value) pairs and interp at target IMT
    n = len(lats)
    out = np.zeros(n)
    for i in range(n):
        pairs = _ctx_row_pairs(per_period_vals, periods_sec, i)
        if not pairs:
            continue  # uniformly uncovered location: 0 is the right answer
        val = _log_period_interp(target_period, pairs)
        if val is None:
            _handle_interp_failure(
                term, target_imt,
                _bracket_failure_reason(
                    target_period, pairs, per_period_vals, i),
                key=key, site_index=i,
                available_periods=[p for p, _ in pairs])
        out[i] = val
    return out


def _per_ray_log_interp(raytrace_grids_term, term, target_imt, ctx,
                        stored_periods, periods_sec):
    """
    Per-ray log-period interp over per-period ray-traces;
    uniform misses stay 0, partial-coverage bracket fails raise.
    """
    # Per stored period: per-ray accumulated value from the path grid
    per_period_vals = {}
    for p_str in stored_periods:
        per_period_vals[p_str] = raytrace_path_adj(
            raytrace_grids_term[p_str],
            ctx.hypo_lon, ctx.hypo_lat, ctx.lon, ctx.lat)

    target_period = target_imt.period

    # Per ray: interp per-period scalars at target IMT; a ray through
    # no cells returns 0 at that period (legitimate anchor, not NaN)
    n = len(ctx.hypo_lon)
    out = np.zeros(n)
    for i in range(n):
        pairs = _ctx_row_pairs(per_period_vals, periods_sec, i)
        if not pairs:
            continue  # uniformly uncovered ray: 0 is the right answer
        val = _log_period_interp(target_period, pairs)
        if val is None:
            _handle_interp_failure(
                term, target_imt,
                _bracket_failure_reason(
                    target_period, pairs, per_period_vals, i),
                ray_index=i,
                available_periods=[p for p, _ in pairs])
        out[i] = val
    return out


def _direct_lookup_or_fail(direct_grid, lats, lons, h3_res,
                           term, imt, key, grids, stored_periods):
    """
    Direct-IMT lookup; partial-coverage misses raise via
    _handle_interp_failure and uniform-coverage misses silently take 0.
    """
    vals = grid_lookup(direct_grid, lats, lons, h3_res, default=np.nan)
    missing = np.where(np.isnan(vals))[0]
    for i in missing:
        if _loc_covered_at_any_period(
                grids, term, key, lats[i], lons[i],
                h3_res, stored_periods):
            _handle_interp_failure( #TODO
                term, imt,
                "ctx row missing at target IMT but covered at other "
                "stored periods (partial coverage)",
                key=key, site_index=int(i),
                lat=float(lats[i]), lon=float(lons[i]))
    # Uniformly uncovered ctx rows: NaN -> 0 (ergodic default)
    vals[np.isnan(vals)] = 0.0
    return vals


def _hypo_site_mean_adj(grid_data, term, cfg, imt, ctx, stored_periods):
    """
    Per-location mean adjustment for one hypo/site term at target IMT.
    """
    lats, lons = _hypo_site_coords(cfg, ctx)
    h3_res = grid_data["h3_res"]
    term_period_info = grid_data["period_info"][term]
    # Fast path: target IMT is stored directly, no interp needed
    direct = grid_data["grids"].get(
        imt.string, {}).get(term, {}).get("mean")
    if direct is not None:
        return _direct_lookup_or_fail(
            direct, lats, lons, h3_res, term, imt, "mean",
            grid_data["grids"], stored_periods)
    # Interp path: per-location log-period interp over per-period lookups
    return _per_loc_log_interp(
        grid_data["grids"], term, "mean", imt,
        lats, lons, h3_res, stored_periods, term_period_info["periods_sec"])


def _path_mean_adj(grid_data, term, imt, ctx, stored_periods):
    """
    Per-ray mean adjustment for one path term at target IMT.
    """
    raytrace_grids_term = grid_data["raytrace_grids"][term]
    term_period_info = grid_data["period_info"][term]

    direct = raytrace_grids_term.get(imt.string)
    if direct is not None:
        # Target IMT is stored directly, ray-trace that grid
        return raytrace_path_adj(
            direct, ctx.hypo_lon, ctx.hypo_lat, ctx.lon, ctx.lat)
    
    # Per-ray log-period interp over per-period ray-traces
    return _per_ray_log_interp(
        raytrace_grids_term, term, imt, ctx, stored_periods,
        term_period_info["periods_sec"])


def _sigma_adj(grid_data, term, cfg, imt, ctx, stored_periods):
    """
    Per-ctx row sigma adjustment for one term at target IMT; scalar
    per-IMT sigmas use the term's CoeffsTable, per-cell goes spatial.
    """
    # Scalar per-IMT sigma: single CoeffsTable interp (not spatial)
    if term in grid_data["scalar_sig_tables"]:
        return float(grid_data["scalar_sig_tables"][term][imt]["sig"])

    # Per-cell sigma (hypo/site only; path per-cell not permitted)
    lats, lons = _hypo_site_coords(cfg, ctx)
    h3_res = grid_data["h3_res"]
    term_period_info = grid_data["period_info"][term]
    direct = grid_data["grids"].get(imt.string, {}).get(term, {}).get("sig")
    
    if direct is not None:
        return _direct_lookup_or_fail(
            direct, lats, lons, h3_res, term, imt, "sig",
            grid_data["grids"], stored_periods
            )
    
    return _per_loc_log_interp(
        grid_data["grids"], term, "sig", imt,
        lats, lons, h3_res, stored_periods, term_period_info["periods_sec"]
        )


def _apply_sigma(action, comp, adj, sig, tau, phi):
    """
    Modify the sigma component "comp" in place with "action" in
    {"replace", "sub", "add"}; recompute total "sig" if "comp"
    was tau/phi.
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


def _apply_term(grid_data, term, cfg, imt, ctx, mean, sig, tau, phi):
    """
    Apply the mean (and optional sigma) adjustment for a single term
    for given IMT, assembled per ctx row from the per-period lookups.
    """
    stored_periods = grid_data["stored_periods"][term]

    # Check it's possible to interpolate a non-present IMT
    if imt.string not in stored_periods:
        _check_in_range(imt, grid_data["period_info"][term], term)

    # Path uses per-ray interp, hypo/site uses per-location
    if cfg["location"] == "path":
        mean += _path_mean_adj(grid_data, term, imt, ctx, stored_periods)
    else:
        mean += _hypo_site_mean_adj(
            grid_data, term, cfg, imt, ctx, stored_periods)

    sig_action = cfg.get("sig_adjustment", "none")
    if sig_action == "none":
        return
    adj = _sigma_adj(grid_data, term, cfg, imt, ctx, stored_periods)
    _apply_sigma(sig_action, cfg["sig_comp_modified"], adj, sig, tau, phi)


def _apply_grid_corrections(grid_data, ctx, imt, mean, sig, tau, phi):
    """
    Apply every stored adjustment term to the "compute()" outputs
    for given IMT.
    """
    for term, cfg in grid_data["res_terms"].items():
        _apply_term(
            grid_data, term, cfg, imt, ctx, mean, sig, tau, phi)


### Helpers for setting up the GridAdjustedGMPE ###
def _validate_res_terms(res_terms, defined_stddev_types):
    """
    Reject invalid "location" targets for each "term" and refuse
    tau/phi adjustments on a GMM that has no tau/phi components.
    """
    valid_targets = ("hypo", "site", "path")
    needs_random_effects = False
    for cfg in res_terms.values():
        if cfg["location"] not in valid_targets:
            raise ValueError(
                f"Invalid location {cfg['location']!r}; must be one "
                f"of {valid_targets}.")
        if (cfg.get("sig_adjustment", "none") != "none"
                and cfg.get("sig_comp_modified") in ("tau", "phi")):
            needs_random_effects = True

    if needs_random_effects:
        required = {const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}
        if not required.issubset(defined_stddev_types):
            raise ValueError(
                "Adjustments to tau and/or phi were configured but the "
                "underlying GSIM does not have tau/phi sigma components.")


def _extend_required_parameters(res_terms, current_rup, current_site):
    """
    Extend the rupture/site parameter sets based on which "location"
    lookups the "res_terms" use (hypo/site/path).

    e.g., a GMM might lack "hypo_lon" and "hypo_lat" which are required
    and otherwise they will not propagate into the "ctx" recarray used.
    """
    locations = {cfg["location"] for cfg in res_terms.values()}
    rup = current_rup
    site = current_site
    if locations & {"hypo", "path"}:
        rup = frozenset(rup | {"hypo_lat", "hypo_lon"})
    if locations & {"site", "path"}:
        site = frozenset(site | {"lat", "lon"})   
    return rup, site


def load_residual_grids(hdf5_path):
    """
    Read the HDF5 of gridded adjustments and return the dict that
    "GridAdjustedGMPE" uses during compute method.

    Keys in the returned dict:

    * "grids"             - {imt_str: {term: {"mean": {cell_id: val},
                                              "sig":  {cell_id: val}}}}
                            for hypo/site terms; "sig" present only when
                            per-cell sigma is stored

    * "raytrace_grids"    - {term: {imt_str: {cell_id: (Polygon, val)}}}
                            for path adjustments

    * "sig_scalars"       - {imt_str: {term: float}} scalar per-IMT sigmas

    * "h3_res"            - sorted list of h3 resolutions found across all
                            stored cells (coarsest first)

    * "res_terms"         - the JSON config from the HDF5 root attribute

    * "scalar_sig_tables" - {term: CoeffsTable} one CoeffsTable per term
                            for the scalar per-IMT sigmas, log-period
                            interpolated to any target IMT at compute time

    * "stored_periods"    - {term: sorted list of IMT strings at which the
                            term is stored}, used by the term-level range
                            check and by the per-ctx-row interp loop
    """
    # Set some stores
    grids = {}
    raytrace_grids = {}
    sig_scalars = {}
    resolutions = set()

    # Read every (term, IMT) group in the HDF5 into plain per-cell dicts
    with h5py.File(hdf5_path, "r") as hf:
        res_terms = json.loads(hf.attrs["res_terms"])
        for term, cfg in res_terms.items():
            for imt_str in hf[term]:
                _load_one_term_per_imt(
                    hf[term][imt_str], term, imt_str, cfg,
                    grids, raytrace_grids, sig_scalars, resolutions)

    # Per-term CoeffsTable for scalar per-IMT sigmas (log-period
    # interpolatable to any target IMT without a spatial lookup)
    scalar_sig_tables = {}
    for term in res_terms:
        ct = _build_scalar_sig_ct(sig_scalars, term)
        if ct is not None:
            scalar_sig_tables[term] = ct

    # Per-term sorted list of stored IMT strings
    stored_periods = {}
    for term, cfg in res_terms.items():
        # Get the IMTs for the term's given correction type
        if cfg["location"] == "path":
            imt_strs = list(raytrace_grids.get(term, {}))
        else:
            imt_strs = [s for s, td in grids.items() if term in td]
        if not imt_strs:
            raise ValueError(
                f"Term '{term}' is declared in 'res_terms' but no IMT "
                f"groups are stored for it in {hdf5_path!r}; provide at "
                f"least one IMT group (an explicit zero mean adjustment "
                f"if no adjustment is desired for it) OR remove the term "
                f"from the 'res_terms' group."
                )
        # Store them for given term in dict of stored periods
        stored_periods[term] = sorted(
            imt_strs, key=lambda s: imt_from_string(s).period)

    # Parse the IMT info stored in the hdf5
    period_info = {}
    for term, imt_strs in stored_periods.items():
        period_info[term] = {
            "has_pga": "PGA" in imt_strs,
            "sa_periods": sorted(
                imt_from_string(s).period for s in imt_strs if s != "PGA"),
            "periods_sec": {
                s: (PGA_ANCHOR_PERIOD if s == "PGA" 
                    else imt_from_string(s).period)
                for s in imt_strs if s == "PGA" or s.startswith("SA(")
            },
        }

    return {
        "grids": grids,
        "raytrace_grids": raytrace_grids,
        "sig_scalars": sig_scalars,
        "h3_res": sorted(resolutions),
        "res_terms": res_terms,
        "scalar_sig_tables": scalar_sig_tables,
        "stored_periods": stored_periods,
        "period_info": period_info,
    }


def _load_one_term_per_imt(grp, term, imt_str, cfg,
                           grids, raytrace_grids, sig_scalars, resolutions):
    """
    Load the mean (and optional sigma) for one (term, IMT) group
    from the HDF5 into the shared dicts.
    """
    location = cfg["location"]
    sig_action = cfg.get("sig_adjustment", "none")

    # Cell IDs and mean values should always be present; also collect
    # the h3 resolution of every stored cell for the spatial fallback
    cell_ids = grp["cell_id"][:].astype(str)
    mean_vals = grp[term][:]
    resolutions.update(h3.get_resolution(c) for c in cell_ids)

    # Path terms need OQ polygons for ray-tracing; hypo/site terms just
    # need a {cell_id -> mean} dict for the point-in-cell lookup
    if location == "path":
        raytrace_grids.setdefault(term, {})[imt_str] = _build_raytrace_grid(
            cell_ids, mean_vals)
    else:
        grids.setdefault(imt_str, {})[term] = {
            "mean": dict(zip(cell_ids, mean_vals))}

    if sig_action != "none":
        _load_sigma(grp, term, imt_str, location, cell_ids, grids, sig_scalars)


def _load_sigma(grp, term, imt_str, location, cell_ids, grids, sig_scalars):
    """
    Read the sigma for one (term, IMT); either a scalar group attribute
    or a per-cell dataset keyed by "{term}_sig" (but never both).
    """
    sig_key = f"{term}_sig"
    scalar_sig = sig_key in grp.attrs
    per_cell_sig = sig_key in grp

    # Reject having both a scalar attribute and a per-cell dataset
    if scalar_sig and per_cell_sig:
        raise ValueError(
            f"Both scalar attribute and dataset '{sig_key}' found for "
            f"term '{term}', IMT '{imt_str}'; provide exactly one.")

    # Need the sigma to be present at this IMT if an adjustment is set
    if not (scalar_sig or per_cell_sig):
        raise ValueError(
            f"Sigma adjustment requested for term '{term}' but "
            f"'{sig_key}' is missing for this IMT '{imt_str}'.")

    # Scalar sigma: non-negative check then store and return
    if scalar_sig:
        val = float(grp.attrs[sig_key])
        if val < 0:
            raise ValueError(
                f"Negative sigma for term '{term}', IMT '{imt_str}'.")
        sig_scalars.setdefault(imt_str, {})[term] = val
        return

    # Only per-cell sigma can be reaching here; reject it for path terms
    if location == "path":
        raise ValueError(
            f"Per-cell sigma is not supported for path terms "
            f"(term '{term}'); use a scalar attribute instead.")

    # Per-cell sigma: non-negative check across all cells, then store
    vals = grp[sig_key][:]
    if np.any(vals < 0):
        raise ValueError(
            f"Negative sigma value for term '{term}', IMT '{imt_str}'.")
    grids[imt_str][term]["sig"] = dict(zip(cell_ids, vals))


def _build_raytrace_grid(cell_ids, mean_vals):
    """
    Turn h3 cell IDs into (OQ Polygon, per-km value) pairs for ray-tracing.
    """
    grid = {}
    for cid, val in zip(cell_ids, mean_vals):
        pnts = [Point(p[0], p[1]) for p in h3.cell_to_boundary(cid)]
        grid[cid] = (Polygon(pnts), float(val))
    return grid


class GridAdjustedGMPE(GMPE):
    """
    A GSIM class that adds spatially-varying corrections stored in a
    HDF5 file of h3-gridded residual terms on top of any underlying GMM
    (which in theory is your backbone model used to compute these
    residual terms).

    The HDF5 file has a root-level attribute "res_terms" that configures
    each corrective term (e.g. "dL2L", "dS2S", "att_per_km").

    Every term specifies:

    * "location" (required): how to resolve the correction spatially;
      the lookup starts at the finest h3 resolution and falls back to
      coarser resolutions:

        * "hypo" = use the rupture hypocentre ("ctx.hypo_lat", "ctx.hypo_lon")
        * "site" = use the site location ("ctx.lat", "ctx.lon")
        * "path" = ray-trace from hypocentre to site through the stored
           cells, accumulating a per-km adjustment along the way

    * "sig_adjustment" (optional, default "none"): what to do to the
      sigma component; when not "none", sigma must be provided for each
      IMT group of that term as either:

        * a scalar HDF5 group attribute keyed by "{term}_sig"

        OR

        * a HDF5 dataset (also keyed by "{term}_sig") giving one value
          per h3 cell (looked up spatially the same way as the mean).

          NOTE: per-cell sigma is not supported for path terms.

        Actions:

            * "none" = skip sigma adjustment (mean-only correction).
            * "sub" = subtract variance from the chosen component.
            * "add" = add variance to the chosen component.
            * "replace" = overwrite the chosen component with the value.

    * "sig_comp_modified" (required when "sig_adjustment" != "none") is
      the std-dev component to modify ("tau", "phi" or "sig").

    Useful info:

    * The set of terms is not fixed - the user is free to include only
      the ones they need (and thus include only those in the HDF5 they
      provide).

    * Corrections are stored per term per IMT; when the target IMT is
      not directly stored, each ctx row (site for hypo/site terms, ray
      for path terms) is handled independently:

        1. For every stored period of the term, the ctx row's
           finest-containing-cell value is pulled (via the
           coarsest->finest spatial fallback) or, for a path term, the
           ray is traced through that period's grid to produce a per-ray
           scalar.
        2. The resulting (period, value) list is log-period interpolated
           at the target IMT to give the ctx row's final adjustment.

      Because the per-period lookup is driven by the ctx row's location,
      a ctx row can use the finest available spatial resolution *at each
      stored period* independently - cells at different h3 resolutions
      can contribute to the same ctx row's interpolation if that is what
      the data supports.

    * Extrapolation beyond the term's overall stored period range raises
      a value-error; PGA counts as SA at 0.01 s for the lower bound only
      when the smallest stored SA period is <= 0.05 s (same gate as
      "CoeffsTable"'s PGA-anchored fallback), otherwise a target IMT
      below the smallest stored SA period is rejected.

    * A ctx row that is uniformly uncovered (no stored cell at any
      stored period of the term) silently gets 0 at every IMT so the
      spectrum stays uniformly ergodic at that ctx row; a ctx row that is
      partially covered (missing at the target but covered at other
      stored periods, or has local pairs that cannot bracket the
      target) is routed through "_handle_interp_failure" because
      adjusting it would distort the spectral shape.

    * The h3 grid cell resolution can vary over IMT because the
      calibration data may vary with period; the per-ctx-row interp
      above handles this naturally - at each period the lookup returns
      whatever the finest containing cell happens to be for that ctx row
      at that period.

    A real HDF5 example is used by the unit tests
    ("openquake/hazardlib/tests/gsim/mgmpe/data/test_grid_adjustments.hdf5")
    and by the classical QA test case_11
    ("openquake/qa_tests_data/classical/case_11/grid_adjustments.hdf5",
    including a README with visualisations of the grids)

    :param gmpe_name:
        Underlying GMM to which the grid-based adjustments are applied.

    :param grid_hdf5_file:
        Path to the HDF5 file with the gridded adjustments.
    """
    # Filled in by set_parameters() from the underlying GMM
    REQUIRES_SITES_PARAMETERS = set()
    REQUIRES_DISTANCES = set()
    REQUIRES_RUPTURE_PARAMETERS = set()
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = ""
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set()
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}
    DEFINED_FOR_TECTONIC_REGION_TYPE = ""
    DEFINED_FOR_REFERENCE_VELOCITY = None

    experimental = True  # GridAdjustedGMPE is not extensively tested yet

    def __init__(self, gmpe_name, grid_hdf5_file, **kwargs):
        # Wrap the underlying GMM and copy its declared parameters
        self.gmpe = registry[gmpe_name](**kwargs)
        self.set_parameters()

        # Load the HDF5 once at construction time
        self.grid_data = load_residual_grids(grid_hdf5_file)

        # Validate the config
        _validate_res_terms(
            self.grid_data["res_terms"],
            self.DEFINED_FOR_STANDARD_DEVIATION_TYPES)

        # Extend the required parameters if necessary
        self.REQUIRES_RUPTURE_PARAMETERS, self.REQUIRES_SITES_PARAMETERS = (
            _extend_required_parameters(
                self.grid_data["res_terms"],
                self.REQUIRES_RUPTURE_PARAMETERS,
                self.REQUIRES_SITES_PARAMETERS))

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See the superclass method
        ".base.GroundShakingIntensityModel.compute"
        """
        # Base-GMM outputs first, then add the grid corrections on top
        # for each requested IMT
        self.gmpe.compute(ctx, imts, mean, sig, tau, phi)
        for m, imt in enumerate(imts):
            _apply_grid_corrections(
                self.grid_data, ctx, imt, mean[m], sig[m], tau[m], phi[m])
