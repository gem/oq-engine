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
Module :mod:`openquake.hazardlib.gsim.mgmpe.grid_adjusted_gmpe` implements
:class:`~openquake.hazardlib.gsim.mgmpe.GridAdjustedGMPE`.

Ray tracing of path adjustments
------------------------------
Path terms store an adjustment per kilometre in H3 cells. For each
site/hypocentre pair, the algorithm samples the great-circle arc on the
Earth's surface, resolves each sample to a stored cell and sums its values.
Depth is not used in this path integral.

1. Discretise the arc into NPTS=100 equally spaced points, including both
   endpoints. Coordinates are calculated in float64. Successive angles
   use sine/cosine angle addition to avoid repeated trigonometric calls.
   The distance between the first two points gives the spacing in km.

2. Resolve each sample to a cell row using masks to skip H3 lookups for
   points outside stored cell bounding boxes. When several H3 resolutions
   are present, the finest stored matching cell wins; if none matches,
   the sample contributes zero.

3. Lookups (masks + cell index) are built lazily and shared across terms/IMTs
   having the same ordered cells.

4. All fields sharing the path grid (mean and optional mean SE) are
   accumulated together in float32, in sample order, then multiplied by
   the float64 spacing. Every sample, including each endpoint, receives
   the full spacing weight.
"""
import json
import os
import hashlib
import ctypes
from contextlib import nullcontext
from functools import lru_cache
import h5py
import h3
from h3.api import basic_int as h3_int
from h3._cy import latlng as h3_latlng
import numpy as np
from numba import types, typeof
from numba.typed import Dict

from openquake.hazardlib import const
from openquake.baselib.performance import compile
from openquake.hazardlib.geo.geodetic import EARTH_RADIUS
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
        raise ValueError(
            f"Both scalar adjustment and per-cell dataset '{sig_key}' "
            f"found for term '{term}', IMT '{imt_str}'. Provide only one.")
    if not has_sig_attr and not has_sig_dataset:
        raise ValueError(
            f"sig_adjustment '{sig_action}' requested for term '{term}' "
            f"but '{sig_key}' is missing for '{imt_str}'")
    if has_sig_dataset and location == "path":
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

    Returns {integer_cell_id: per_km_adj_value}, avoiding string conversion
    at each sample. Raytracing resolves each sample point to a stored cell
    with finest-to-coarsest fallback (see raytrace_path_adj).
    """
    return {h3.str_to_int(cell) if isinstance(cell, str) else cell: value
            for cell, value in zip(cell_ids, mean_vals)}


def load_residual_grids(hdf5_path):
    """
    Load the hdf5 residual grids into a dict with seven keys:

    * grids: nested dict of
      {imt_str: {term: {"mean":    {cell_id: float},
                        "sig":     {cell_id: float},
                        "mean_se": {cell_id: float}}, ...}}
      for hypo/site-based terms only.

    * raytrace_grids: {term: {imt_str: {cell_id: val}, ...}} - H3 cell-id
      lookups for path-based terms.

    * raytrace_se_grids: same structure as raytrace_grids but holding the
      per-cell SE on the mean for path-based terms.

    * lookups: {cells_bytes: lookup} - mask structures shared by terms/IMTs
      with the same cells; filled on first use.

    * sig_scalars: {imt_str: {term: float}} - scalar sigma adjustments.

    * h3_res: sorted (coarsest to finest) list of h3 resolutions.

    * res_terms: term metadata dict.
    """
    grids = {}
    raytrace_grids = {}
    raytrace_se_grids = {}
    sig_scalars = {}
    resolutions = set()
    with h5py.File(hdf5_path, "r") as hf:
        res_terms = json.loads(hf.attrs["res_terms"])
        for term in res_terms:
            location = res_terms[term]["location"]
            sig_action = res_terms[term].get("sig_adjustment", "none")
            for imt_str in hf[term]:
                grids.setdefault(imt_str, {})
                sig_scalars.setdefault(imt_str, {})
                grp = hf[term][imt_str]
                mean_vals = grp[term][:]
                cell_ids = grp["cell_id"][:].astype(str)
                resolutions.update(h3.get_resolution(c) for c in cell_ids)

                if location == "path":
                    raytrace_grids.setdefault(term, {})
                    raytrace_grids[term][imt_str] = \
                        build_raytrace_grid(cell_ids, mean_vals)
                else:
                    grids[imt_str][term] = {
                        "mean": dict(zip(cell_ids, mean_vals))}

                if sig_action != "none":
                    load_sigma_for_term(
                        grp, term, imt_str, location,
                        sig_action, cell_ids, grids, sig_scalars)

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
            "lookups": {},
            "sig_scalars": sig_scalars,
            "h3_res": sorted(resolutions),
            "res_terms": res_terms}


# {SHA256 content digest: grid_data}, shared by GridAdjustedGMPE instances
# reading identical files. For the SAM job, two files occupy about
# 8 MB after loading; lookups add ~1 MB (shared by all 26 IMTs).
_GRID_CACHE = {}


@lru_cache(maxsize=128)
def _grid_digest(path, stamp):
    with open(path, 'rb') as f:
        return hashlib.file_digest(f, 'sha256').digest()


def get_residual_grids(hdf5_path):
    """
    Same as load_residual_grids, but identical file contents are loaded
    only once per process. The result is shared between callers, which must
    not modify it (except for the lazily filled lookups).
    """
    path = os.path.abspath(hdf5_path)
    stat = os.stat(path)
    key = _grid_digest(
        path, (stat.st_mtime_ns, stat.st_ctime_ns, stat.st_size))
    if key not in _GRID_CACHE:
        _GRID_CACHE[key] = load_residual_grids(path)
    return _GRID_CACHE[key]


def raytrace_path_adj(grid, hypo_lons, hypo_lats, site_lons, site_lats,
                      h3_res):
    """
    For each epicentre-to-site path apply an adjustment based on the
    distance traversed through each H3 grid cell.

    :param grid: {cell_id: per_km_adj_value} for a single term and IMT
    :returns: adjustment_vals array of shape (len(hypo_lons),)
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
MAX_GRID_CELLS = 1 << 31


# For each h3 resolution, a lat/lon raster flagging the boxes which may
# contain points of a stored cell of that resolution, i.e. the boxes
# overlapping the bounding box of the cell vertices enlarged by the margin.
# Points in a box not flagged cannot be in a stored cell, so their h3
# lookups would miss and can be skipped; returns the mask origins and raster,
# with candidate_mask None if the margin is not guaranteed to be enough.
def _build_masks(grid, h3_res):
    boxes = []  # (resolution index, lat1, lat2, lon1, lon2)
    for cell in grid:
        cell = h3.str_to_int(cell) if isinstance(cell, str) else cell
        res = h3_int.get_resolution(cell)
        if res not in h3_res:
            continue
        bound = np.array(h3_int.cell_to_boundary(cell))
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
    lat_origin, lon_origin = arr[:, 1].min(), arr[:, 3].min()
    nlat = int(np.floor((arr[:, 2].max() - lat_origin) / MASK_STEP)) + 1
    nlon = int(np.floor((arr[:, 4].max() - lon_origin) / MASK_STEP)) + 1
    candidate_mask = np.zeros((len(h3_res), nlat, nlon), bool)
    for r, lat1, lat2, lon1, lon2 in boxes:
        i1, i2 = np.floor(
            (np.array([lat1, lat2]) - lat_origin) / MASK_STEP)
        j1, j2 = np.floor(
            (np.array([lon1, lon2]) - lon_origin) / MASK_STEP)
        candidate_mask[int(r), int(i1):int(i2) + 1,
                       int(j1):int(j2) + 1] = True
    return lon_origin, lat_origin, candidate_mask


# The C symbol latLngToCell is linked statically in the h3 extensions and
# is exported only by ELF/Mach-O builds, not by the MSVC ones on Windows.
# The portable way is the Cython C API: the capsule exported by h3._cy.latlng
# points to the C implementation of the cpdef function latlng_to_cell
# (degrees, resolution, skip_dispatch flag), which returns 1 on error.
# Pass the callable to Numba as an argument, so the compiled cache does not
# embed a process-specific function address.
_capsule_name = ctypes.PYFUNCTYPE(ctypes.c_char_p, ctypes.py_object)(
    ('PyCapsule_GetName', ctypes.pythonapi))
_capsule_pointer = ctypes.PYFUNCTYPE(
    ctypes.c_void_p, ctypes.py_object, ctypes.c_char_p)(
    ('PyCapsule_GetPointer', ctypes.pythonapi))
_capsule = h3_latlng.__pyx_capi__['latlng_to_cell']
_H3_CELL = ctypes.CFUNCTYPE(
    ctypes.c_uint64, ctypes.c_double, ctypes.c_double, ctypes.c_int,
    ctypes.c_int)(_capsule_pointer(_capsule, _capsule_name(_capsule)))


# Type of the {cell ID: row} dictionaries
_INDEX = types.DictType(types.uint64, types.int64)

# Lookup structure: masks + cell index for fast H3 resolution
# Using a class so it's picklable (numba Dict is not picklable)
class Lookup:
    __slots__ = ('lon_origin', 'lat_origin', 'candidate_mask',
                 '_cell_index', 'cells', '_index_dict',
                 'step', 'raster', 'subrasters')
    def __init__(self, **kwargs):
        self.lon_origin = kwargs.get('lon_origin', 0.)
        self.lat_origin = kwargs.get('lat_origin', 0.)
        self.candidate_mask = kwargs.get('candidate_mask',
                                         np.zeros((0, 0, 0), bool))
        self._cell_index = kwargs.get('cell_index')  # numba Dict (not picklable)
        self.cells = kwargs.get('cells')
        self._index_dict = None  # Python dict for pickling
        self.step = kwargs.get('step')
        self.raster = kwargs.get('raster')
        self.subrasters = kwargs.get('subrasters')
        if self._cell_index is None and self.cells is not None:
            self._cell_index = _cell_index(self.cells)
    @property
    def cell_index(self):
        """Lazily rebuild numba Dict after unpickling."""
        if self._cell_index is None and self._index_dict is not None:
            self._cell_index = _cell_index(self.cells)
        return self._cell_index
    def __getstate__(self):
        # Build a Python dict from the numba Dict for pickling
        if self._index_dict is None and self._cell_index is not None:
            self._index_dict = {k: v for k, v in self._cell_index.items()}
        return {'lon_origin': self.lon_origin,
                'lat_origin': self.lat_origin,
                'candidate_mask': self.candidate_mask,
                '_index_dict': self._index_dict,
                'cells': self.cells,
                'step': self.step,
                'raster': self.raster,
                'subrasters': self.subrasters}
    def __setstate__(self, state):
        self.lon_origin = state['lon_origin']
        self.lat_origin = state['lat_origin']
        self.candidate_mask = state['candidate_mask']
        self.cells = state['cells']
        self._index_dict = state['_index_dict']
        self.step = state.get('step')
        self.raster = state.get('raster')
        self.subrasters = state.get('subrasters')
        self._cell_index = None  # Rebuild lazily when needed


# Array of the integer cell IDs of a grid, in the order of the grid
def _cell_array(grid):
    if len(grid) > MAX_GRID_CELLS:
        raise ValueError(
            f'Adjustment grid has {len(grid):,} cells; '
            f'int32 row indices support at most {MAX_GRID_CELLS:,}')
    return np.array([h3.str_to_int(cell) if isinstance(cell, str) else cell
                     for cell in grid], np.uint64)


# {cell ID: row in cells}
@compile(_INDEX(types.uint64[:]))
def _cell_index(cells):
    index = Dict.empty(types.uint64, types.int64)
    for i, cell in enumerate(cells):
        index[cell] = i
    return index


# Build the lookup structure for a grid: masks + cell index
def _build_lookup(grid, cells, h3_res, raster=False):
    """
    Build (lon_origin, lat_origin, candidate_mask, cell_index, cells).
    Shared by terms/IMTs with the same cells.
    The raster parameter is kept for backward compatibility.
    """
    lon_origin, lat_origin, candidate_mask = _build_masks(grid, list(h3_res))
    if candidate_mask is None:
        # Unsafe bounds: no masking, direct H3 fallback
        return Lookup(lon_origin=0., lat_origin=0.,
                      candidate_mask=np.zeros((0, 0, 0), bool), cells=cells,
                      raster=np.zeros((0, 0), np.int32))
    index = _cell_index(cells)
    if raster:
        # For backward compatibility with test: create a dummy raster
        # since we no longer build actual rasters
        nlat = candidate_mask.shape[1]
        nlon = candidate_mask.shape[2]
        dummy_raster = np.zeros((nlat, nlon), np.int32)
        return Lookup(lon_origin=lon_origin, lat_origin=lat_origin,
                      candidate_mask=candidate_mask, cell_index=index,
                      cells=cells, raster=dummy_raster)
    return Lookup(lon_origin=lon_origin, lat_origin=lat_origin,
                  candidate_mask=candidate_mask, cell_index=index,
                  cells=cells, raster=np.zeros((0, 0), np.int32))


# Get or build lookup for a grid, shared by cell ID bytes
def _get_lookup(grid_data, grid):
    cells = _cell_array(grid)
    cache = grid_data.setdefault("lookups", {})
    key = cells.tobytes()
    if key not in cache:
        cache[key] = _build_lookup(grid, cells, grid_data["h3_res"])
    return cache[key]


# Great-circle distance in km
@compile('f8(f8, f8, f8, f8)')
def _distance(lon1, lat1, lon2, lat2):
    lon1, lat1 = np.radians(lon1), np.radians(lat1)
    lon2, lat2 = np.radians(lon2), np.radians(lat2)
    arr = np.sin((lat1 - lat2) / 2.0) ** 2.0
    arr += np.cos(lat1) * np.cos(lat2) * np.sin((lon1 - lon2) / 2.0) ** 2.0
    return 2 * EARTH_RADIUS * np.arcsin(np.sqrt(min(arr, 1.)))


# Azimuth in degrees from point 1 to point 2
@compile('f8(f8, f8, f8, f8)')
def _azimuth(lon1, lat1, lon2, lat2):
    lon1, lat1 = np.radians(lon1), np.radians(lat1)
    lon2, lat2 = np.radians(lon2), np.radians(lat2)
    cos_lat2 = np.cos(lat2)
    true_course = np.degrees(np.arctan2(
        np.sin(lon1 - lon2) * cos_lat2,
        np.cos(lat1) * np.sin(lat2)
        - np.sin(lat1) * cos_lat2 * np.cos(lon1 - lon2)))
    return (360 - true_course) % 360


# Resolve a point to a cell row using masks + H3 fallback
@compile(types.int64(
    types.float64, types.float64, types.float64, types.float64,
    types.boolean[:, :, :], types.int64[:], _INDEX, typeof(_H3_CELL)))
def _resolve_point(lon, lat, lon_origin, lat_origin, candidate_mask,
                   h3_res, index, cell_func):
    y, x = 0, 0
    if len(candidate_mask):
        y = int(np.floor((lat - lat_origin) / MASK_STEP))
        x = int(np.floor((lon - lon_origin) / MASK_STEP))
        if (y < 0 or y >= candidate_mask.shape[1] or
                x < 0 or x >= candidate_mask.shape[2]):
            return -1
    for r in range(len(h3_res) - 1, -1, -1):
        if len(candidate_mask) and not candidate_mask[r, y, x]:
            continue
        cell = cell_func(lat, lon, h3_res[r], 1)
        if cell == 1:
            raise ValueError('H3 cell lookup failed')
        if cell in index:
            return index[cell]
    return -1


# Discretise paths and accumulate adjustments for all fields
@compile(types.Tuple((types.float32[:, :], types.float64[:]))(
    types.float64[:], types.float64[:], types.float64[:], types.float64[:],
    types.int64, types.float64, types.float64,
    types.boolean[:, :, :], types.int64[:], _INDEX,
    types.float32[:, :], typeof(_H3_CELL)))
def _trace_paths(slons, slats, hlons, hlats, npts,
                 lon_origin, lat_origin, candidate_mask, h3_res, index,
                 values, cell_func):
    sums = np.zeros((len(values), len(slons)), np.float32)
    spacing = np.zeros(len(slons))
    for p in range(len(slons)):
        lon1, lat1, lon2, lat2 = slons[p], slats[p], hlons[p], hlats[p]
        dstep = (_distance(lon1, lat1, lon2, lat2) / EARTH_RADIUS) / (npts - 1)
        tc = np.radians(360 - _azimuth(lon1, lat1, lon2, lat2))
        sin_tc, cos_tc = np.sin(tc), np.cos(tc)
        rlon, rlat = np.radians(lon1), np.radians(lat1)
        sin_lat, cos_lat = np.sin(rlat), np.cos(rlat)
        sin_step, cos_step = np.sin(dstep), np.cos(dstep)
        sin_d, cos_d = 0., 1.
        for k in range(npts):
            if k == 0:
                lon, lat = lon1, lat1
            elif k == npts - 1:
                lon, lat = lon2, lat2
            else:
                sin_d, cos_d = (sin_d * cos_step + cos_d * sin_step,
                                cos_d * cos_step - sin_d * sin_step)
                sin_lats = sin_lat * cos_d + cos_lat * sin_d * cos_tc
                sin_lats = min(1., max(-1., sin_lats))
                lat = np.degrees(np.arcsin(sin_lats))
                dlon = np.arctan2(sin_tc * sin_d * cos_lat,
                                  cos_d - sin_lat * sin_lats)
                lon = np.degrees((rlon - dlon + np.pi) % (2 * np.pi) - np.pi)
            if k == 1:
                spacing[p] = _distance(lon1, lat1, lon, lat)
            row = _resolve_point(lon, lat, lon_origin, lat_origin,
                                 candidate_mask, h3_res, index, cell_func)
            if row >= 0:
                for f in range(len(values)):
                    sums[f, p] += values[f, row]
    return sums, spacing


# Resolve all fields on the same path grid with one raytrace per path
def _raytrace_path_adjs(grids, hypo_lons, hypo_lats, site_lons, site_lats,
                        h3_res, lookup=None):
    reference_grid = grids["mean"]
    if lookup is None:
        lookup = _build_lookup(reference_grid, _cell_array(reference_grid), h3_res)
    lon_origin, lat_origin, candidate_mask, index, cells = (
        lookup.lon_origin, lookup.lat_origin, lookup.candidate_mask,
        lookup.cell_index, lookup.cells)
    values = np.zeros((len(grids), len(cells)), np.float32)
    for f, grid in enumerate(grids.values()):
        values[f] = [grid[cell] for cell in reference_grid]
    sums, spacing = _trace_paths(
        np.ascontiguousarray(site_lons, np.float64).reshape(-1),
        np.ascontiguousarray(site_lats, np.float64).reshape(-1),
        np.ascontiguousarray(hypo_lons, np.float64).reshape(-1),
        np.ascontiguousarray(hypo_lats, np.float64).reshape(-1),
        NPTS, lon_origin, lat_origin, candidate_mask,
        np.array(h3_res, np.int64), index, values, _H3_CELL)
    return {key: sums[f] * spacing for f, key in enumerate(grids)}


# Lookup rows for hypo/site terms (one point per context)
@compile(types.int64[:](
    types.float64[:], types.float64[:], types.float64, types.float64,
    types.boolean[:, :, :], types.int64[:], _INDEX, typeof(_H3_CELL)))
def _lookup_rows(lons, lats, lon_origin, lat_origin, candidate_mask,
                 h3_res, index, cell_func):
    rows = np.empty(len(lons), np.int64)
    for i in range(len(lons)):
        rows[i] = _resolve_point(lons[i], lats[i], lon_origin, lat_origin,
                                 candidate_mask, h3_res, index, cell_func)
    return rows


def grid_lookup(grids, lats, lons, h3_res, lookup=None):
    """
    Resolve (lat, lon) pairs to cell adjustments using finest-to-coarsest H3 fallback.
    """
    reference_grid = grids["mean"]
    if lookup is None:
        lookup = _build_lookup(reference_grid, _cell_array(reference_grid), h3_res)
    lon_origin, lat_origin, candidate_mask, index, cells = (
        lookup.lon_origin, lookup.lat_origin, lookup.candidate_mask,
        lookup.cell_index, lookup.cells)
    rows = _lookup_rows(
        np.ascontiguousarray(lons, np.float64).reshape(-1),
        np.ascontiguousarray(lats, np.float64).reshape(-1),
        lon_origin, lat_origin, candidate_mask,
        np.array(h3_res, np.int64), index, _H3_CELL)
    found = rows >= 0
    values = {}
    for key, grid in grids.items():
        vals = np.array([grid[cell] for cell in reference_grid], float)
        values[key] = np.zeros(len(rows))
        values[key][found] = vals[rows[found]]
    return values


def adjust_sigma(sig_vals, cfg, sig_action, sig, tau, phi):
    """
    Apply the resolved per-cell or scalar sigma adjustment to its component.
    """
    sig_comp = cfg["sig_comp_modified"]
    component = {"tau": tau, "phi": phi}.get(sig_comp, sig)
    if sig_action == "replace":
        component[:] = sig_vals
    else:
        sign = -1 if sig_action == "sub" else 1
        component[:] = np.sqrt(component ** 2 + sign * sig_vals ** 2)
    if sig_comp in ("tau", "phi"):
        sig[:] = np.sqrt(tau ** 2 + phi ** 2)


def _resolve_adjs(grid_data, cfg, term, imt, ctx, gra_mon=nullcontext()):
    if cfg["location"] == "path":
        grid = grid_data["raytrace_grids"].get(term, {}).get(imt)
        if grid is None:
            return {}
        grids = {"mean": grid}
        se_grid = grid_data["raytrace_se_grids"].get(term, {}).get(imt)
        if se_grid is not None:
            grids["mean_se"] = se_grid
        lookup = _get_lookup(grid_data, grid)
        with gra_mon:
            return _raytrace_path_adjs(
                grids, ctx.hypo_lon, ctx.hypo_lat, ctx.lon, ctx.lat,
                grid_data["h3_res"], lookup)

    entry = grid_data["grids"].get(imt, {}).get(term, {})
    if not entry:
        return {}
    lats, lons = ((ctx.hypo_lat, ctx.hypo_lon) if cfg["location"] == "hypo"
                  else (ctx.lat, ctx.lon))
    lookup = _get_lookup(grid_data, entry["mean"])
    return grid_lookup(entry, lats, lons, grid_data["h3_res"], lookup)


def compute_central(gsim, ctx, imts, mean, sig, tau, phi,
                    gra_mon=nullcontext()):
    """
    Compute the backbone and the central grid corrections.
    """
    grid_data = gsim.grid_data
    gsim.gmpe.compute(ctx, imts, mean, sig, tau, phi)
    resolved = {}
    for m, imt in enumerate(imts):
        for term, cfg in grid_data["res_terms"].items():
            adjs = _resolve_adjs(grid_data, cfg, term, str(imt), ctx, gra_mon)
            mean_adj, se_adj = adjs.get("mean"), adjs.get("mean_se")
            if mean_adj is None:
                continue
            resolved[m, term] = mean_adj, se_adj
            mean[m] += mean_adj
            sig_action = cfg.get("sig_adjustment", "none")
            if sig_action != "none":
                scalars = grid_data["sig_scalars"].get(str(imt), {})
                sig_vals = adjs.get("sig", scalars.get(term))
                adjust_sigma(sig_vals, cfg, sig_action,
                             sig[m], tau[m], phi[m])
    return resolved


def apply_epsilons(gsim, resolved, imts, mean):
    """
    Add this branch's eps * mean_se shift to the central mean.
    """
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

      * location: How to resolve the correction spatially:

        * hypo = Use the rupture hypocentre (ctx.hypo_lat, ctx.hypo_lon)

        * site = Use the site location (ctx.lat, ctx.lon)

        * path = Use raytracing to apply a travel path effect

      * sig_adjustment (optional, default "none"): Whether to adjust the
        corresponding GMM sigma component.

      * sig_comp_modified (required when sig_adjustment is not "none"): Which
        std-dev component to adjust - "tau", "phi", or "sig".

    An optional per-cell dataset "{term}_mean_se" may also be present in
    each IMT group for a term. This is the SE on the fitted central
    mean adjustment, resolved alongside the central mean and only applied
    when a non-zero epsilon is supplied for that term via "epsilons".

    :param gmpe_name: The underlying GMM to apply the grid-based adjustments to.
    :param grid_hdf5_file: Path to the hdf5 file with gridded adjustments.
    :param epsilons: Optional dict of per-term epsilons.
    :param path_cap: Optional per-branch cap (nat-log units) on the path term.
    """
    REQUIRES_SITES_PARAMETERS = set()
    REQUIRES_DISTANCES = set()
    REQUIRES_RUPTURE_PARAMETERS = set()
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = ""
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set()
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}
    DEFINED_FOR_TECTONIC_REGION_TYPE = ""
    DEFINED_FOR_REFERENCE_VELOCITY = None

    experimental = True

    def __init__(self, gmpe_name, grid_hdf5_file, epsilons=None,
                 path_cap=None, **kwargs):

        self.gmpe = registry[gmpe_name](**kwargs)
        self.set_parameters()

        self.grid_data = get_residual_grids(grid_hdf5_file)

        if path_cap is not None and path_cap <= 0:
            raise ValueError(
                f"path_cap must be positive (natural-log units) or None, "
                f"got {path_cap!r}.")
        self.path_cap = path_cap

        self.central_key = (
            os.fspath(grid_hdf5_file), type(self.gmpe).__name__,
            repr(tuple(self.gmpe.kwargs.items())))

        self.epsilons = epsilons or {}
        unknown = set(self.epsilons) - set(self.grid_data["res_terms"])
        if unknown:
            raise ValueError(
                f"Unknown term(s) in epsilons: {sorted(unknown)}. "
                f"Known terms: {sorted(self.grid_data['res_terms'])}.")

        locations = {cfg["location"]
                     for cfg in self.grid_data["res_terms"].values()}
        invalid = locations - {"hypo", "site", "path"}
        if invalid:
            raise ValueError(
                f"Invalid location type(s) {sorted(invalid)} in res_terms "
                f"(must be 'hypo', 'site' or 'path').")
        if locations & {"hypo", "path"}:
            self.REQUIRES_RUPTURE_PARAMETERS = frozenset(
                self.REQUIRES_RUPTURE_PARAMETERS | {'hypo_lat', 'hypo_lon'})
        if locations & {"site", "path"}:
            self.REQUIRES_SITES_PARAMETERS = frozenset(
                self.REQUIRES_SITES_PARAMETERS | {'lat', 'lon'})

        if any(cfg.get("sig_adjustment", "none") != "none"
               and cfg.get("sig_comp_modified") in ("tau", "phi")
               for cfg in self.grid_data["res_terms"].values()):
            required = {const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}
            if not required.issubset(
                    self.DEFINED_FOR_STANDARD_DEVIATION_TYPES):
                raise ValueError(
                    "Adjustments to tau and/or phi have been specified "
                    "but the underlying GSIM does not support "
                    "random-effects residuals.")

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        resolved = compute_central(self, ctx, imts, mean, sig, tau, phi)
        apply_epsilons(self, resolved, imts, mean)