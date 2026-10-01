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

# CoeffsTable treats PGA as SA at this period during log-period interpolation,
# and only allows that fallback when the smallest tabulated SA period is
# no larger than PGA_ANCHOR_MAX_SA.
PGA_ANCHOR_PERIOD = 0.01
PGA_ANCHOR_MAX_SA = 0.05


### Centralised handler for per-record interpolation failures ###
def _handle_interp_failure(term, imt, reason, **context):
    """
    Single hook for every per-record case where GridAdjustedGMPE
    produces an adjustment at the target IMT for a record that is
    only partially covered by the stored grids (covered at some
    stored periods but not at the target, or covered at some
    periods with pairs that cannot bracket the target). Partial
    coverage distorts the spectral shape, so it is treated as an
    interpolation failure.

    A record that is *uniformly* uncovered (no cell at any stored
    period of the term) is not routed here - it legitimately gets
    zero adjustment, leaving the spectrum uniformly ergodic.

    Currently every call raises; keeping all call sites routed
    through this one function is deliberate so the policy (raise vs
    nearest-neighbour fallback vs per-reason dispatch) can be
    changed in one place without touching the call sites.
    """
    details = ", ".join(f"{k}={v}" for k, v in context.items())
    raise ValueError(
        f"GridAdjustedGMPE failed to interpolate term {term!r} at "
        f"{imt}: {reason}" + (f" [{details}]" if details else ""))


def _site_covered_at_any_period(grids, term, key, lat, lon,
                                h3_res, stored_periods):
    """
    True iff ``(lat, lon)`` falls inside a stored cell for ``term`` /
    ``key`` at at least one of ``stored_periods``. Used to tell a
    partially covered site (covered somewhere, missing here) from a
    uniformly uncovered site (nowhere in the grid for this term).
    """
    for p_str in stored_periods:
        d = grids.get(p_str, {}).get(term, {}).get(key)
        if d is None:
            continue
        for res in reversed(h3_res):
            if h3.latlng_to_cell(lat, lon, res) in d:
                return True
    return False


### Helpers for log-period interpolation at target IMT ###
def _check_in_range(imt, stored_imt_strs, term):
    """
    Raise ValueError if the target IMT period is outside the range in
    which log-period interpolation can produce a value for this term.

    PGA counts as SA at PGA_ANCHOR_PERIOD only when the smallest stored
    SA period is <= PGA_ANCHOR_MAX_SA (same gate as CoeffsTable's
    PGA-anchored fallback). Otherwise the lower bound is the smallest
    stored SA period.

    PGA and other non-SA IMTs (PGV, PGD, IA, CAV...) cannot be produced
    by log-period interpolation and must be stored directly. PGA is only
    used as the low-period anchor for SA interpolation, not interpolated
    itself; the other non-SA IMTs have no meaningful period axis.
    """
    if not imt.string.startswith("SA("):
        raise ValueError(
            f"Cannot interpolate {imt} for term '{term}': only SA IMTs "
            f"can be filled in by log-period interpolation; PGA and "
            f"other non-SA IMTs must be provided directly in the HDF5.")

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
            return  # Target sits inside the stored SA range

    # Target sits below the smallest stored SA. PGA can anchor the interp
    # by standing in for SA(0.01), but only when PGA is stored, target >=
    # 0.01s, and the smallest stored SA is <= 0.05s (otherwise the gap is
    # too wide to interpolate through) - same logic as in CoeffsTable.
    fallback_ok = (has_pga and p >= PGA_ANCHOR_PERIOD
                   and sa_periods and sa_periods[0] <= PGA_ANCHOR_MAX_SA)
    if not fallback_ok:
        raise ValueError(
            f"Cannot interpolate {imt} for term '{term}': target period "
            f"{p}s below the interpolable range (need PGA plus a stored "
            f"SA period at <= {PGA_ANCHOR_MAX_SA}s to anchor against).")


def _log_period_interp(target_period, pairs):
    """
    Linear log-period interpolation at ``target_period`` of a sorted list
    of ``(period_in_seconds, value)`` pairs. Returns ``None`` if the
    target period cannot be bracketed below and above by entries in
    ``pairs``.
    """
    below = None
    above = None
    for p, v in pairs:
        if p == target_period:
            return v
        if p < target_period:
            below = (p, v)
        else:
            above = (p, v)
            break
    if below is None or above is None:
        return None
    ratio = ((math.log(target_period) - math.log(below[0])) /
             (math.log(above[0]) - math.log(below[0])))
    return below[1] + ratio * (above[1] - below[1])


def _periods_in_seconds(imt_strs):
    """
    Convert each stored IMT string to its period in seconds for log-period
    interp. PGA is mapped to PGA_ANCHOR_PERIOD; non-SA/non-PGA IMTs are
    skipped (they have no meaningful period axis).
    """
    return {s: (PGA_ANCHOR_PERIOD if s == "PGA" else imt_from_string(s).period)
            for s in imt_strs if s == "PGA" or s.startswith("SA(")}


def _bracket_failure_reason(target_period, pairs, per_period_vals, i):
    """
    Precise reason why :func:`_log_period_interp` returned ``None``
    for record ``i``. Three cases:

    * target above the record's local max SA period - extrapolation.
    * target below the record's local min SA period and PGA is stored
      at this record but the smallest local SA period exceeds
      ``PGA_ANCHOR_MAX_SA``, so PGA cannot anchor the interpolation.
    * target below the record's local min SA period and no PGA is
      available at this record - extrapolation.
    """
    if target_period > pairs[-1][0]:
        return (f"target period {target_period}s above record's local "
                f"max SA period ({pairs[-1][0]}s): extrapolation")
    pga_arr = per_period_vals.get("PGA")
    pga_at_record = pga_arr is not None and not np.isnan(pga_arr[i])
    smallest_sa = pairs[0][0]
    if pga_at_record and smallest_sa > PGA_ANCHOR_MAX_SA:
        return (f"PGA is stored at this record but the smallest local "
                f"SA period ({smallest_sa}s) exceeds the PGA anchor "
                f"gap (<= {PGA_ANCHOR_MAX_SA}s), so PGA cannot anchor "
                f"the interp at target {target_period}s")
    return (f"target period {target_period}s below record's local min "
            f"SA period ({smallest_sa}s) with no usable PGA anchor: "
            f"extrapolation")


def _record_pairs(per_period_vals, periods_sec, i):
    """
    Pull row ``i`` from each per-period value array. Return a sorted
    ``[(period_in_seconds, value)]`` list with NaN rows dropped. PGA is
    kept only if the smallest surviving SA period in the row is
    <= PGA_ANCHOR_MAX_SA (same gate as CoeffsTable's PGA anchor).
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
    Per-term CoeffsTable of scalar per-IMT sigmas, or None if this term
    has no scalar sigma stored. Queried at compute time to log-period
    interpolate the scalar sigma to any target IMT.
    """
    rows = {imt_from_string(s): {"sig": float(sig_scalars[s][term])}
            for s in sig_scalars if term in sig_scalars[s]}
    return CoeffsTable.fromdict(rows) if rows else None


### Helpers for compute-time spatial lookup and ray-tracing ###

def grid_lookup(grid_dict, lats, lons, h3_res, default=0.0):
    """
    Point-in-cell lookup with a finest -> coarsest fallback. Locations
    outside every stored cell receive ``default`` (0.0 by default, which
    treats "no cell" as "no adjustment"; pass ``np.nan`` to distinguish
    "no cell" from a stored zero value).

    :param grid_dict:
        {cell_id: value} for one term and one IMT (and one of mean or sig).
    :param lats:
        Array of latitudes (hypocentre or site, depending on the term).
    :param lons:
        Array of longitudes.
    :param h3_res:
        Sorted list of h3 resolution levels (coarsest first).
    :param default:
        Fill value for locations where no containing cell is found at any
        stored resolution.
    """
    n = len(lats)
    vals = np.full(n, default, dtype=float)
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

def _hypo_site_coords(cfg, ctx):
    """Return (lats, lons) from ``ctx`` for a hypo/site term's lookup."""
    if cfg["location"] == "hypo":
        return ctx.hypo_lat, ctx.hypo_lon
    return ctx.lat, ctx.lon


def _per_site_log_interp(grids, term, key, target_imt, lats, lons,
                         h3_res, stored_periods):
    """
    Per-site log-period interp. For each stored period of the term, do a
    finest-containing-cell spatial lookup (via :func:`grid_lookup` with
    ``NaN`` as the no-cell sentinel). Then, per site, assemble the
    (period, value) list from the lookups and log-period interpolate at
    the target IMT.

    A site with no containing cell at any stored period is uniformly
    uncovered for this term and legitimately gets 0 (spectrum stays
    uniformly ergodic at that site). A site that is covered at some
    periods but has pairs that cannot bracket the target is partially
    covered - adjusting it would distort the spectral shape - and is
    routed through :func:`_handle_interp_failure`.
    """
    # 1) Per stored period: pull per-site value with NaN for "no cell".
    per_period_vals = {}
    for p_str in stored_periods:
        term_at_p = grids.get(p_str, {}).get(term, {})
        if key not in term_at_p:
            continue
        per_period_vals[p_str] = grid_lookup(
            term_at_p[key], lats, lons, h3_res, default=np.nan)

    periods_sec = _periods_in_seconds(per_period_vals.keys())
    target_period = target_imt.period

    # 2) Per site: build the (period, value) pairs for *this* site from
    #    whichever stored periods had a containing cell here, then
    #    log-period interp at the target IMT.
    n = len(lats)
    out = np.zeros(n)
    for i in range(n):
        pairs = _record_pairs(per_period_vals, periods_sec, i)
        if not pairs:
            continue  # uniformly uncovered site: 0 is the right answer
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
                        stored_periods):
    """
    Per-ray log-period interp for a path term. For each stored period,
    ray-trace through the path grid at that period to get a per-ray
    scalar. Then, per ray, log-period interp those scalars at the target
    IMT.

    Rays that don't cross any stored cell at a given period get a 0
    accumulation at that period (same as the current path semantics);
    0 therefore counts as a legitimate interp anchor, not a sentinel.
    A ray with no per-period pairs at all is treated as uniformly
    uncovered (gets 0). Pairs that exist but cannot bracket the
    target IMT are partial coverage - the spectral shape would be
    distorted - and are routed through :func:`_handle_interp_failure`.
    """
    # 1) Per stored period: ray-trace to get a per-ray accumulated value.
    per_period_vals = {}
    for p_str in stored_periods:
        grid = raytrace_grids_term.get(p_str)
        if grid is None:
            continue
        per_period_vals[p_str] = raytrace_path_adj(
            grid, ctx.hypo_lon, ctx.hypo_lat, ctx.lon, ctx.lat)

    periods_sec = _periods_in_seconds(per_period_vals.keys())
    target_period = target_imt.period

    # 2) Per ray: interp the per-period scalars at the target IMT.
    #    _record_pairs drops NaN rows, but ray-trace never produces NaN,
    #    so every stored period contributes a pair for every ray.
    n = len(ctx.hypo_lon)
    out = np.zeros(n)
    for i in range(n):
        pairs = _record_pairs(per_period_vals, periods_sec, i)
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
    Spatial lookup at a directly-stored target IMT. A record missing
    from the direct grid is checked against the term's other stored
    periods: if any of them covers it, the record is partially
    covered and routes through :func:`_handle_interp_failure`;
    otherwise the record is uniformly uncovered and silently takes 0.
    """
    vals = grid_lookup(direct_grid, lats, lons, h3_res, default=np.nan)
    missing = np.where(np.isnan(vals))[0]
    for i in missing:
        if _site_covered_at_any_period(
                grids, term, key, lats[i], lons[i],
                h3_res, stored_periods):
            _handle_interp_failure(
                term, imt,
                "record missing at target IMT but covered at other "
                "stored periods (partial coverage)",
                key=key, site_index=int(i),
                lat=float(lats[i]), lon=float(lons[i]))
    # Uniformly uncovered records: NaN -> 0 (ergodic default).
    vals[np.isnan(vals)] = 0.0
    return vals


def _hypo_site_mean_adj(grid_data, term, cfg, imt, ctx, stored_periods):
    """Per-site mean adjustment for one hypo/site term at target IMT."""
    lats, lons = _hypo_site_coords(cfg, ctx)
    h3_res = grid_data["h3_res"]
    # Fast path: target IMT is stored directly; no interp needed.
    direct = grid_data["grids"].get(
        imt.string, {}).get(term, {}).get("mean")
    if direct is not None:
        return _direct_lookup_or_fail(
            direct, lats, lons, h3_res, term, imt, "mean",
            grid_data["grids"], stored_periods)
    # Interp path: per-site log-period interp over per-period lookups.
    return _per_site_log_interp(
        grid_data["grids"], term, "mean", imt,
        lats, lons, h3_res, stored_periods)


def _path_mean_adj(grid_data, term, imt, ctx, stored_periods):
    """Per-ray mean adjustment for one path term at target IMT."""
    raytrace_grids_term = grid_data["raytrace_grids"].get(term, {})
    # Fast path: target IMT is stored directly; ray-trace that grid.
    direct = raytrace_grids_term.get(imt.string)
    if direct is not None:
        return raytrace_path_adj(
            direct, ctx.hypo_lon, ctx.hypo_lat, ctx.lon, ctx.lat)
    # Interp path: per-ray log-period interp over per-period ray-traces.
    return _per_ray_log_interp(
        raytrace_grids_term, term, imt, ctx, stored_periods)


def _sigma_adj(grid_data, term, cfg, imt, ctx, stored_periods):
    """
    Return the per-record sigma adjustment values for one term at the
    target IMT. Sigma may be stored as:

    * A scalar per IMT (one value per term per IMT) - log-period
      interpolated via the term-level ``scalar_sig_tables`` CoeffsTable.
    * Per cell - looked up spatially per record and log-period
      interpolated per record, same way as the mean.
    """
    # Scalar per-IMT sigma: single CoeffsTable interp (not spatial).
    if term in grid_data["scalar_sig_tables"]:
        return float(grid_data["scalar_sig_tables"][term][imt]["sig"])

    # Per-cell sigma (hypo/site only; path per-cell sigma is rejected
    # at load time).
    lats, lons = _hypo_site_coords(cfg, ctx)
    h3_res = grid_data["h3_res"]
    direct = grid_data["grids"].get(
        imt.string, {}).get(term, {}).get("sig")
    if direct is not None:
        return _direct_lookup_or_fail(
            direct, lats, lons, h3_res, term, imt, "sig",
            grid_data["grids"], stored_periods)
    return _per_site_log_interp(
        grid_data["grids"], term, "sig", imt,
        lats, lons, h3_res, stored_periods)


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


def _apply_one_term(grid_data, term, cfg, imt, ctx, mean, sig, tau, phi):
    """
    Apply the mean (and optional sigma) adjustment for a single term at
    target IMT. Per-record (per-site or per-ray) assembly: at each
    stored period, do the spatial lookup / ray-trace to get a per-record
    value for *this* record's location; then log-period interp those
    per-period values at the target IMT.
    """
    stored_periods = grid_data["stored_periods"][term]
    if not stored_periods:
        return

    # Term-level range check (only when the target IMT is not stored):
    # if the target period sits outside the term's overall interpolable
    # range, every record would get 0, which is almost certainly a user
    # error; raise instead.
    if imt.string not in stored_periods:
        _check_in_range(imt, stored_periods, term)

    # Mean adjustment: path uses per-ray interp, hypo/site uses per-site.
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
    Apply every stored term to the compute() outputs for a single target
    IMT. Each term is handled per-record: the mean and sigma adjustments
    at a given site/ray are assembled from per-period finest-containing-
    cell lookups and log-period interpolated at the target IMT.

    Raises ValueError when the target IMT is outside the interpolable
    range of any configured term (see :func:`_check_in_range`).
    """
    for term, cfg in grid_data["res_terms"].items():
        _apply_one_term(
            grid_data, term, cfg, imt, ctx, mean, sig, tau, phi)


### Helpers for ensuring GMM can actually be adjusted ###
def _validate_res_terms(res_terms, defined_stddev_types):
    """
    Rejects invalid location target types for the adjustment and refuse
    to modify tau/phi for a GMM that lacks tau and phi sigma components.
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
    Extend the required rupture / site parameter sets required for the
    modification of the underlying GMM based on which location lookups
    the "res_terms" use.
    """
    locations = {cfg["location"] for cfg in res_terms.values()}
    rup = current_rup
    site = current_site
    if locations & {"hypo", "path"}:
        rup = frozenset(rup | {"hypo_lat", "hypo_lon"})
    if locations & {"site", "path"}:
        site = frozenset(site | {"lat", "lon"})

    return rup, site


### Helpers for loading adjustments from the HDF5 ###
def load_residual_grids(hdf5_path):
    """
    Read the HDF5 of gridded adjustments and return the dict that
    :class:`GridAdjustedGMPE` uses during ``compute()``.

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
                            check and by the per-record interp loop
    """
    grids = {}
    raytrace_grids = {}
    sig_scalars = {}
    resolutions = set()

    # Read every (term, IMT) group in the hdf5 file into plain per-cell dicts.
    with h5py.File(hdf5_path, "r") as hf:
        res_terms = json.loads(hf.attrs["res_terms"])
        for term, cfg in res_terms.items():
            for imt_str in hf[term]:
                _load_one_term_per_imt(
                    hf[term][imt_str], term, imt_str, cfg,
                    grids, raytrace_grids, sig_scalars, resolutions)

    # Per-term CoeffsTable for scalar per-IMT sigmas (log-period interpolable
    # to any target IMT without needing a spatial lookup).
    scalar_sig_tables = {}
    for term in res_terms:
        ct = _build_scalar_sig_ct(sig_scalars, term)
        if ct is not None:
            scalar_sig_tables[term] = ct

    # Per-term sorted list of stored IMT strings. Used by the term-level
    # extrapolation guard and by the per-record interp loop to decide which
    # IMTs to assemble (period, value) pairs from.
    stored_periods = {}
    for term, cfg in res_terms.items():
        if cfg["location"] == "path":
            imt_strs = list(raytrace_grids.get(term, {}))
        else:
            imt_strs = [s for s, td in grids.items() if term in td]
        stored_periods[term] = sorted(
            imt_strs, key=lambda s: imt_from_string(s).period)

    return {
        "grids": grids,
        "raytrace_grids": raytrace_grids,
        "sig_scalars": sig_scalars,
        "h3_res": sorted(resolutions),
        "res_terms": res_terms,
        "scalar_sig_tables": scalar_sig_tables,
        "stored_periods": stored_periods,
    }


def _load_one_term_per_imt(grp, term, imt_str, cfg,
                           grids, raytrace_grids, sig_scalars, resolutions):
    """
    Load the mean adjustment (and optional sigma) for given IMT stored in
    one HDF5 group into dicts.
    """
    location = cfg["location"]
    sig_action = cfg.get("sig_adjustment", "none")

    # Cell IDs and mean values must/should always be present; collect the
    # h3 resolution of every stored cell for the spatial fallback
    cell_ids = grp["cell_id"][:].astype(str)
    mean_vals = grp[term][:]
    resolutions.update(h3.get_resolution(c) for c in cell_ids)

    # Path terms need OQ polygons ready for ray-tracing; hypo/site terms
    # just need a {cell_id -> mean} dict for the point-in-cell h3 lookup
    if location == "path":
        raytrace_grids.setdefault(term, {})[imt_str] = _build_raytrace_grid(
            cell_ids, mean_vals)
    else:
        grids.setdefault(imt_str, {})[term] = {
            "mean": dict(zip(cell_ids, mean_vals))}

    if sig_action != "none":
        # Need the sigma adjustments too then
        _load_sigma(grp, term, imt_str, location, cell_ids, grids, sig_scalars)


def _load_sigma(grp, term, imt_str, location, cell_ids, grids, sig_scalars):
    """
    Read the sigma adjustment for one (term, IMT). Sigma is stored either
    as a scalar HDF5 group attribute or as a per-cell dataset - never
    both.

    NOTE: Per-cell sigma lookup is not supported currently for path-based
    terms and an error is raised here if this is present in the loaded HDF5.
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
        sig_scalars.setdefault(imt_str, {})[term] = val
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


class GridAdjustedGMPE(GMPE):
    """
    A GSIM class that adds spatially-varying corrections stored in a
    HDF5 file of h3-gridded residual terms on top of any underlying GMM
    (which in theory is your backbone model used to compute these residual
    terms).

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

    Useful info:

    * The set of terms is not fixed - the user is free to include only
      the ones they need (and thus include only those in the HDF5 they
      provide).

    * Corrections are stored per term per IMT. When the target IMT is
      not directly stored, each record (site for hypo/site terms, ray
      for path terms) is handled independently:

        1. For every stored period of the term, the record's
           finest-containing-cell value is pulled (via the
           coarsest->finest spatial fallback) or, for a path term, the
           ray is traced through that period's grid to produce a per-ray
           scalar.
        2. The resulting (period, value) list is log-period interpolated
           at the target IMT to give the record's final adjustment.

      Because the per-period lookup is driven by the record's location,
      a record can use the finest available spatial resolution *at each
      stored period* independently - cells at different h3 resolutions
      can contribute to the same record's interpolation if that is what
      the data supports.

    * Extrapolation beyond the term's overall stored period range raises
      a value-error. PGA counts as SA at 0.01 s for the lower bound only
      when the smallest stored SA period is <= 0.05 s (same gate as
      :class:`CoeffsTable`'s PGA-anchored fallback); otherwise a target
      IMT below the smallest stored SA period is rejected. A record whose
      locally available (period, value) list cannot bracket the target
      silently gets 0 (no adjustment at that record).

    * The h3 grid cell resolution can vary over IMT because the
      calibration data may vary with period. The per-record interp above
      handles this naturally: at each period the lookup returns whatever
      the finest containing cell happens to be for that record at that
      period.

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
                self.REQUIRES_SITES_PARAMETERS)
                )

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        # Get the base-GMM outputs, then add the grid
        # corrections on top for each requested IMT
        self.gmpe.compute(ctx, imts, mean, sig, tau, phi)
        for m, imt in enumerate(imts):
            _apply_grid_corrections(
                self.grid_data, ctx, imt, mean[m], sig[m], tau[m], phi[m]
                )
