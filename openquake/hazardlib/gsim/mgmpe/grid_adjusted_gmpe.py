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
Depth is not used in this path integral. The following sketch uses boxes
only to illustrate cell membership; actual H3 cells are not rectangular::

    site                                             hypocentre
      S---o---o---o---o---o---o---o---o---o---o---o---H
      |       cell A      |     cell B    | no stored cell |
      |    value a/km     |   value b/km  |    value 0     |

    adjustment = spacing_km * (number_in_A * a + number_in_B * b)

1. Discretise the arc into NPTS=100 equally spaced points, including both
   endpoints. Coordinates are calculated in float64. Successive angles
   use sine/cosine angle addition to avoid repeated trigonometric calls.
   The distance between the first two points gives the spacing in km.

2. Resolve each sample to a cell row with a cached Lookup. When several
   H3 resolutions are present, the finest stored matching cell wins;
   if none matches, the sample contributes zero. There is no interpolation
   between cells. The lookup follows this decision tree::

       sample longitude, latitude
                   |
             raster available? ---- no ------------------+
                   | yes                                |
          outside raster? -------- yes ---> no cell      |
                   | no                                 |
          read pixel's cell row                          |
                   |                                    |
          pixel subdivided? ------- yes ---> read subpixel
                   | no                          |       |
                   +-----------------------------+       |
                   |                                    |
          row ambiguous? --------- yes -----------------+
                   | no                                 |
          return row or no cell                H3 finest to coarsest
                                                        |
                                               skip masked-out levels
                                                        |
                                               first match or no cell

3. Build lookups lazily and share them across terms/IMTs having the same
   ordered cells. Per-resolution masks mark 0.1-degree boxes that may
   intersect a stored cell. Cell bounds include a 0.1-degree margin;
   unsafe bounds (low H3 resolutions or polar cells) disable masking and
   raster lookup, so resolution uses H3 directly.

   The path raster normally divides each mask box into 5 x 5 pixels
   (0.02 degrees); its resolution is reduced to respect the base raster
   pixel limit. A pixel receives a cell row only when its four corners
   resolve identically, including agreement on no cell. Otherwise it is
   subdivided into 4 x 4 subpixels. Subpixels use the same corner test;
   remaining ambiguities fall back to H3 at the sample's coordinates.

   This corner test is an approximation: a cell boundary can enter a
   pixel or subpixel without changing any corner's resolved row. Such an
   intersection can be missed. The raster does not guarantee exact cell
   membership near boundaries; the H3 fallback itself resolves membership
   without this raster approximation.

4. Accumulate all fields sharing the path grid (mean and optional mean SE)
   together in float32, in sample order, then multiply by the float64
   spacing. Every sample, including each endpoint, receives the full
   spacing weight. This is the existing discrete sum, not a trapezoidal
   rule or an exact integration of the length inside each cell.

Hypocentre and site terms use one coordinate lookup per context rather
than tracing a path. They use the masks and H3 fallback without the
approximate cell raster.
"""
import json
import os
import hashlib
import ctypes
from collections import namedtuple
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

    * lookups: {(cell_ids_bytes, raster): lookup} - the structures used to
      resolve points into cells (see _build_lookup), i.e. the lat/lon boxes
      where the points may hit a cell, per h3 resolution, used to skip the
      lookups which would miss, and for the path-based terms a raster of
      the cells. They are shared by the terms/IMTs with the same cells; the
      dict starts empty and is filled for the grids actually used.

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
            "lookups": {}, # Filled on first use by _resolve_adjs
            "sig_scalars": sig_scalars,
            "h3_res": sorted(resolutions), # Coarsest to finest h3 res
            "res_terms": res_terms}


# {SHA256 content digest: grid_data}, shared by GridAdjustedGMPE instances
# reading identical files, including copies extracted from saved logic trees.
# Values contain the correction grids, sigma scalars, term metadata and
# lazily filled lookups. For the SAM job, two files occupy about 8 MB after
# loading, plus 20 MB for the lookups (shared by all 26 IMTs, mostly the
# rasters for the path-based terms). These sizes are
# per process; the cache has no size limit and retains distinct file contents
# until the process exits, so larger grids or more files can use much more.
_GRID_CACHE = {}


# Avoid hashing the same file for every branch. The stat signature
# invalidates the digest when a file changes; only small metadata is cached.
@lru_cache(maxsize=128)
def _grid_digest(path, stamp):
    with open(path, 'rb') as f:
        return hashlib.file_digest(f, 'sha256').digest()


def get_residual_grids(hdf5_path):
    """
    Same as load_residual_grids, but identical file contents are loaded
    only once per process, even from different paths. The result is shared
    between callers, which must not modify it (except for the lazily filled
    lookups).

    :param hdf5_path:
        Path to the hdf5 containing the grid-based adjustments.
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
MAX_GRID_CELLS = 1 << 31

# Each mask box is split in RASTER_FACTOR x RASTER_FACTOR pixels of the
# raster of the cell rows used by the path lookups (0.02 degrees), unless
# the raster would exceed RASTER_MAX_PIXELS (4 bytes each); the AMBIGUOUS
# pixels, crossed by a cell boundary, are split in SUBFACTOR x SUBFACTOR
# sub-pixels, and the AMBIGUOUS sub-pixels are resolved with h3
RASTER_FACTOR = 5
RASTER_MAX_PIXELS = 1 << 23
SUBFACTOR = 4
AMBIGUOUS = -2


# For each h3 resolution, a lat/lon raster flagging the boxes which may
# contain points of a stored cell of that resolution, i.e. the boxes
# overlapping the bounding box of the cell vertices enlarged by the margin.
# Points in a box not flagged cannot be in a stored cell, so their h3
# lookups would miss and can be skipped; returns the mask origins and raster,
# with candidate_mask None if the margin is not guaranteed to be enough
def _build_masks(grid, h3_res):
    boxes = []  # (resolution index, lat1, lat2, lon1, lon2)
    for cell in grid:
        cell = h3.str_to_int(cell) if isinstance(cell, str) else cell
        res = h3_int.get_resolution(cell)
        if res not in h3_res:  # never looked up
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
    # With the current step, margin and latitude limit, at most about
    # 93 MB per term/IMT: 16 resolutions * 1603 * 3603 one-byte bools.
    # The rectangle includes empty areas between stored cells.
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

# Lookup structures shared by Python and the compiled functions
Lookup = namedtuple("Lookup", "lon_origin lat_origin candidate_mask step "
                    "raster subrasters cells")
_LOOKUP = types.NamedTuple((
    types.float64, types.float64, types.boolean[:, :, ::1], types.float64,
    types.int32[:, ::1], types.int32[:, :, ::1], types.uint64[::1]), Lookup)


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


# Row of the stored cell containing the point according to the raster of
# a lookup (see _build_lookup), or -1 if there is none, or AMBIGUOUS if
# the point is in an AMBIGUOUS sub-pixel or there is no raster, i.e. h3 is
# needed (see _h3_row). The raster covers all the mask boxes, so points
# outside it are in no cell. This is called for each point and must be
# cheap, so it takes few arguments and no h3 arguments.
@compile(types.int64(
    types.float64, types.float64, types.float64, types.float64,
    types.float64, types.int32[:, :], types.int32[:, :, :]))
def _raster_row(lon, lat, lon_origin, lat_origin, step, raster, subrasters):
    if not raster.size:
        return AMBIGUOUS
    yf = (lat - lat_origin) / step
    xf = (lon - lon_origin) / step
    i, j = int(np.floor(yf)), int(np.floor(xf))
    if i < 0 or i >= raster.shape[0] or j < 0 or j >= raster.shape[1]:
        return -1
    row = raster[i, j]
    if row < AMBIGUOUS:  # pixel split in sub-pixels
        sub = subrasters[AMBIGUOUS - 1 - row]
        n = sub.shape[0]
        row = sub[min(int((yf - i) * n), n - 1),
                  min(int((xf - j) * n), n - 1)]
    return row


# Row of the stored cell containing the (finite) point, or -1 if there is
# none, resolving the cell finest-to-coarsest with h3 and skipping the
# resolutions excluded by the masks of a lookup. A mask with zero
# resolutions disables the filtering for unsafe cell bounds.
# The Cython function uses Python objects to check for errors and so needs
# the GIL, which is fine since `compile` does not release it.
@compile(types.int64(
    types.float64, types.float64, types.float64, types.float64,
    types.boolean[:, :, :], types.int64[:], _INDEX, typeof(_H3_CELL)))
def _h3_row(lon, lat, lon_origin, lat_origin, candidate_mask, h3_res, index,
            cell_func):
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
        if cell == 1:  # not a valid H3 index: the error value
            raise ValueError('H3 cell lookup failed')
        if cell in index:
            return index[cell]
    return -1


# Raster of nlat x nlon pixels of `step` degrees starting at lon0, lat0:
# the row of a pixel is the row of its four corners if they agree,
# otherwise AMBIGUOUS. This is approximate only when a cell boundary enters
# a pixel without containing any of its corners, which is rare and affects
# tiny areas for pixels much smaller than the cells.
@compile(types.int32[:, :](
    types.float64, types.float64, types.float64, types.int64, types.int64,
    _LOOKUP, types.int64[:], _INDEX, typeof(_H3_CELL)))
def _corner_raster(lon0, lat0, step, nlat, nlon, lookup, h3_res, index,
                   cell_func):
    lon_origin, lat_origin = lookup.lon_origin, lookup.lat_origin
    candidate_mask = lookup.candidate_mask
    raster = np.empty((nlat, nlon), np.int32)
    prev = np.empty(nlon + 1, np.int64)  # rows at the previous corners
    corners = np.empty(nlon + 1, np.int64)
    for i in range(nlat + 1):
        lat = lat0 + i * step
        for j in range(nlon + 1):
            corners[j] = _h3_row(lon0 + j * step, lat, lon_origin,
                                 lat_origin, candidate_mask, h3_res, index,
                                 cell_func)
        if i:
            for j in range(nlon):
                row = prev[j]
                if (prev[j + 1] == row and corners[j] == row and
                        corners[j + 1] == row):
                    raster[i - 1, j] = row
                else:
                    raster[i - 1, j] = AMBIGUOUS
        prev, corners = corners, prev
    return raster


# Raster of the rows in the boxes of the masks, subdivided in factor x factor
# pixels; the AMBIGUOUS pixels are split in SUBFACTOR x SUBFACTOR sub-pixels,
# so that only the AMBIGUOUS sub-pixels need h3. A split pixel stores
# AMBIGUOUS - 1 - k, where k is the index of its subraster.
@compile(types.Tuple((types.int32[:, :], types.int32[:, :, :]))(
    _LOOKUP, types.int64, types.int64[:], typeof(_H3_CELL)))
def _build_raster(lookup, factor, h3_res, cell_func):
    lon_origin, lat_origin = lookup.lon_origin, lookup.lat_origin
    candidate_mask, step = lookup.candidate_mask, lookup.step
    index = _cell_index(lookup.cells)
    raster = _corner_raster(
        lon_origin, lat_origin, step, candidate_mask.shape[1] * factor,
        candidate_mask.shape[2] * factor, lookup, h3_res, index, cell_func)
    ii, jj = np.nonzero(raster == AMBIGUOUS)
    subrasters = np.empty((len(ii), SUBFACTOR, SUBFACTOR), np.int32)
    for k in range(len(ii)):
        i, j = ii[k], jj[k]
        subrasters[k] = _corner_raster(
            lon_origin + j * step, lat_origin + i * step, step / SUBFACTOR,
            SUBFACTOR, SUBFACTOR, lookup, h3_res, index, cell_func)
        raster[i, j] = AMBIGUOUS - 1 - k
    return raster, subrasters


def _build_lookup(grid, cells, h3_res, raster=True):
    """
    Build the structure used to resolve points into rows of the cells,
    i.e. a tuple (lon_origin, lat_origin, candidate_mask, step, raster,
    subrasters, cells). The candidate_mask comes from _build_masks;
    the raster has pixels of `step` degrees (possibly an empty raster).

    :param grid: {cell_id: value}
    :param cells: the cell IDs of the grid as an array of uint64
    :param h3_res: sorted list of h3 resolutions (coarse to fine)
    :param raster: if False, do not build the raster (exact lookups)
    """
    no_raster = np.zeros((0, 0), np.int32)
    no_sub = np.zeros((0, 0, 0), np.int32)
    lon_origin, lat_origin, candidate_mask = _build_masks(grid, list(h3_res))
    if candidate_mask is None:  # unsafe masks: always use h3
        return Lookup(0., 0., np.zeros((0, 0, 0), bool), MASK_STEP, no_raster,
                      no_sub, cells)
    nboxes = candidate_mask.shape[1] * candidate_mask.shape[2]
    # reduce the raster resolution if there are too many pixels
    factor = min(RASTER_FACTOR,
                 int(np.sqrt(RASTER_MAX_PIXELS / max(nboxes, 1))))
    if not raster or nboxes == 0 or factor < 1:
        return Lookup(lon_origin, lat_origin, candidate_mask, MASK_STEP,
                      no_raster, no_sub, cells)
    lookup = Lookup(lon_origin, lat_origin, candidate_mask, MASK_STEP / factor,
                    no_raster, no_sub, cells)
    raster, subrasters = _build_raster(
        lookup, factor, np.array(h3_res, np.int64), _H3_CELL)
    return lookup._replace(raster=raster, subrasters=subrasters)


# Lookup structure for the cells of a grid, built on first use and
# shared by the terms and IMTs with the same cells (in the same order)
def _get_lookup(grid_data, grid, raster=True):
    cells = _cell_array(grid)
    cache = grid_data.setdefault("lookups", {})
    key = cells.tobytes(), raster
    if key not in cache:
        cache[key] = _build_lookup(grid, cells, grid_data["h3_res"], raster)
    return cache[key]


# Great-circle distance in km, as in geodetic_distance
@compile('f8(f8, f8, f8, f8)')
def _distance(lon1, lat1, lon2, lat2):
    lon1, lat1 = np.radians(lon1), np.radians(lat1)
    lon2, lat2 = np.radians(lon2), np.radians(lat2)
    arr = np.sin((lat1 - lat2) / 2.0) ** 2.0
    arr += np.cos(lat1) * np.cos(lat2) * np.sin((lon1 - lon2) / 2.0) ** 2.0
    # rounding could exceed 1 for antipodal points: avoid NaNs
    return 2 * EARTH_RADIUS * np.arcsin(np.sqrt(min(arr, 1.)))


# Azimuth in degrees from point 1 to point 2, as in geodetic.azimuth
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


# Discretise each great-circle path from a site to its hypocentre in npts
# points, keeping the original endpoints, as npoints_between does, and sum
# the values (shape (F, C)) of the stored cells containing the points;
# the sums are accumulated in float32, in sample order. Also return the
# distance between consecutive points, as in the original algorithm.
@compile(types.Tuple((types.float32[:, :], types.float64[:]))(
    types.float64[:], types.float64[:], types.float64[:], types.float64[:],
    types.int64, _LOOKUP, types.int64[:],
    types.float32[:, :], typeof(_H3_CELL)))
def _trace_paths(slons, slats, hlons, hlats, npts, lookup, h3_res, values,
                 cell_func):
    lon_origin, lat_origin = lookup.lon_origin, lookup.lat_origin
    candidate_mask, step = lookup.candidate_mask, lookup.step
    raster, subrasters = lookup.raster, lookup.subrasters
    index = _cell_index(lookup.cells)
    sums = np.zeros((len(values), len(slons)), np.float32)
    spacing = np.zeros(len(slons))
    # the endpoints are finite (NaN hypocenters are rejected by the parsers
    # and NaN sites by SiteCollection.check_nan) and so are the points
    for p in range(len(slons)):
        lon1, lat1, lon2, lat2 = slons[p], slats[p], hlons[p], hlats[p]
        # see npoints_towards
        dstep = (_distance(lon1, lat1, lon2, lat2) / EARTH_RADIUS) / (
            npts - 1)
        tc = np.radians(360 - _azimuth(lon1, lat1, lon2, lat2))
        sin_tc, cos_tc = np.sin(tc), np.cos(tc)
        rlon, rlat = np.radians(lon1), np.radians(lat1)
        sin_lat, cos_lat = np.sin(rlat), np.cos(rlat)
        # sin and cos of k * dstep by angle addition, saving two calls
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
                # rounding can exceed 1 on paths over a pole: avoid NaNs
                sin_lats = min(1., max(-1., sin_lats))
                lat = np.degrees(np.arcsin(sin_lats))
                dlon = np.arctan2(sin_tc * sin_d * cos_lat,
                                  cos_d - sin_lat * sin_lats)
                lon = np.degrees((rlon - dlon + np.pi) % (2 * np.pi) - np.pi)
            if k == 1:
                spacing[p] = _distance(lon1, lat1, lon, lat)
            row = _raster_row(lon, lat, lon_origin, lat_origin, step,
                              raster, subrasters)
            if row == AMBIGUOUS:
                row = _h3_row(lon, lat, lon_origin, lat_origin,
                              candidate_mask, h3_res, index, cell_func)
            if row >= 0:
                for f in range(len(values)):
                    sums[f, p] += values[f, row]
    return sums, spacing


# Resolve all fields on the same path grid with one raytrace per path.
# The lookup (see _build_lookup) is built if not given.
def _raytrace_path_adjs(grids, hypo_lons, hypo_lats, site_lons, site_lats,
                        h3_res, lookup=None):
    reference_grid = grids["mean"]
    if lookup is None:
        lookup = _build_lookup(
            reference_grid, _cell_array(reference_grid), h3_res)
    cells = lookup.cells
    values = np.zeros((len(grids), len(cells)), np.float32)
    for f, grid in enumerate(grids.values()):
        values[f] = [grid[cell] for cell in reference_grid]
    sums, spacing = _trace_paths(
        _f8(site_lons), _f8(site_lats), _f8(hypo_lons), _f8(hypo_lats),
        NPTS, lookup, np.array(h3_res, np.int64), values, _H3_CELL)
    # Get the cumulative correction based on distance traversed per
    # grid cell; points with no stored cell contribute zero
    return {key: sums[f] * spacing for f, key in enumerate(grids)}


# Rows of the stored cells containing the points (-1 if none)
@compile(types.int64[:](
    types.float64[:], types.float64[:], _LOOKUP, types.int64[:],
    typeof(_H3_CELL)))
def _lookup_rows(lons, lats, lookup, h3_res, cell_func):
    lon_origin, lat_origin = lookup.lon_origin, lookup.lat_origin
    candidate_mask, step = lookup.candidate_mask, lookup.step
    raster, subrasters = lookup.raster, lookup.subrasters
    index = _cell_index(lookup.cells)
    rows = np.empty(len(lons), np.int64)
    for i in range(len(lons)):  # finite points, as in _trace_paths
        row = _raster_row(lons[i], lats[i], lon_origin, lat_origin, step,
                          raster, subrasters)
        if row == AMBIGUOUS:
            row = _h3_row(lons[i], lats[i], lon_origin, lat_origin,
                          candidate_mask, h3_res, index, cell_func)
        rows[i] = row
    return rows


def grid_lookup(grids, lats, lons, h3_res, lookup=None):
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
    :param lookup:
        Lookup structure for the cells (see _build_lookup); if not given,
        an exact one (without raster) is built
    :returns:
        {key: adjustment_vals}, each array of shape (len(lats),)
    """
    # Mean, SE and optional per-cell sigma share the same stored cell IDs.
    reference_grid = grids["mean"]
    if lookup is None:
        lookup = _build_lookup(
            reference_grid, _cell_array(reference_grid), h3_res, raster=False)
    rows = _lookup_rows(_f8(lons), _f8(lats), lookup,
                        np.array(h3_res, np.int64), _H3_CELL)
    found = rows >= 0
    values = {}
    for key, grid in grids.items():
        vals = np.array([grid[cell] for cell in reference_grid], float)
        values[key] = np.zeros(len(rows))
        values[key][found] = vals[rows[found]]
    return values


# Contiguous float64 array, as required by the compiled functions
def _f8(arr):
    return np.ascontiguousarray(arr, np.float64).reshape(-1)


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
def _resolve_adjs(grid_data, cfg, term, imt, ctx, gra_mon=nullcontext()):
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
        lookup = _get_lookup(grid_data, grid)
        # The ContextMaker owns the monitor; standalone GSIMs need none.
        with gra_mon:
            return _raytrace_path_adjs(
                grids, ctx.hypo_lon, ctx.hypo_lat, ctx.lon, ctx.lat,
                grid_data["h3_res"], lookup)

    # Hypo/site terms are stored as cell_id -> value dicts; their lookups
    # are exact (no raster), since there is one point per context
    entry = grid_data["grids"].get(imt, {}).get(term, {})
    if not entry:
        return {}
    lats, lons = ((ctx.hypo_lat, ctx.hypo_lon) if cfg["location"] == "hypo"
                  else (ctx.lat, ctx.lon))
    lookup = _get_lookup(grid_data, entry["mean"], raster=False)
    return grid_lookup(entry, lats, lons, grid_data["h3_res"], lookup)


def compute_central(gsim, ctx, imts, mean, sig, tau, phi,
                    gra_mon=nullcontext()):
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
    :param gra_mon:
        Optional ray-tracing monitor owned by the ContextMaker.
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
            adjs = _resolve_adjs(grid_data, cfg, term, str(imt), ctx, gra_mon)
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

        # Load grid-based corrections from the hdf5; they are shared with
        # the other instances reading the same file. Like GMPETable, keep
        # the loaded data when pickling: extracted files may be gone.
        self.grid_data = get_residual_grids(grid_hdf5_file)

        # Per-ray path cap (in natural-log units).
        # None = no cap; compute() clips the per-branch total after lookup.
        if path_cap is not None and path_cap <= 0:
            raise ValueError(
                f"path_cap must be positive (natural-log units) or None, "
                f"got {path_cap!r}.")
        self.path_cap = path_cap

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
