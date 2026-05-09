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
import h5py
import h3
import numpy as np

from openquake.hazardlib import const
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.polygon import Polygon
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.geodetic import npoints_between, distance
from openquake.hazardlib.gsim.base import GMPE, registry


def load_sigma_for_term(
        grp, term, imt_str, location,
        sig_action, cell_ids, sig_grids, sig_scalars
        ):
    """
    Load the sigma adjustment for one term/IMT group into
    sig_grids (per-cell) OR sig_scalars (scalar).
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
    if has_sig_dataset:
        if location == "path":
            # Raise an error if requesting per-cell sigma
            # adjustment with a path-based term
            raise ValueError(
                f"Per-cell sigma is not currently supported for "
                f"path-based terms (term '{term}'). Use a "
                f"scalar adjustment instead.")
        sig_vals = grp[sig_key][:]
        if np.any(sig_vals < 0):
            raise ValueError(
                f"Negative _sig value found for term "
                f"'{term}' and IMT '{imt_str}'")
        sig_grids[imt_str][term] = dict(zip(cell_ids, sig_vals))
    else:
        sig_scalar = grp.attrs[sig_key]
        if sig_scalar < 0:
            raise ValueError(
                f"Negative _sig value found for term "
                f"'{term}' and IMT '{imt_str}'")
        sig_scalars[imt_str][term] = sig_scalar


def build_raytrace_grid(cell_ids, mean_vals):
    """
    Build the OQ polygon grid for one path-based term/IMT.

    Returns {cell_id: (Polygon, per_km_adj_value)}.
    """
    val_dict = dict(zip(cell_ids, mean_vals))
    imt_pgns = {}
    for cid in cell_ids:
        pnts = [Point(pnt[0], pnt[1])
                for pnt in h3.cell_to_boundary(cid)]
        # Store (OQ pgn, per km adjustment value) together
        imt_pgns[cid] = (Polygon(pnts), val_dict[cid])

    return imt_pgns


def load_residual_grids(hdf5_path):
    """
    Load the hdf5 residual grids into a dict with six keys:

    * grids: nested dict of {imt_str: {term: {cell_id: mean}, ...}} for
      hypo/site-based terms only which use h3 cells.

    * path_pgns: {term: {imt_str: {cell_id: (oq_pgn, val)}, ...}} - OQ pgn
      grids for path-based terms (used in raytracing), stored per term per
      IMT (cell sets can differ across IMTs and across terms).

    * sig_scalars: {imt_str: {term: float}} - one sigma adjustment scalar
      per term per IMT. Populated when sig_adjustment is not "none" and the
      sigma is given as a scalar adjustment (group attribute "{term}_sig").

    * sig_grids: {imt_str: {term: {cell_id: float}}} - per-cell sigma
      adjustment values for hypo/site-based terms. Populated when
      sig_adjustment is not "none" and the sigma is given as a dataset named
      "{term}_sig" in the IMT group. Per-cell sigma adjustments for path terms
      are not supported currently.

      NOTE: sig_scalars and sig_grids are mutually exclusive for each term/IMT
      so providing both raises an error.

    * h3_res: sorted (coarsest to finest) list of h3 resolutions, derived
      automatically from the cell IDs in the grids. Used in hypo-based,
      site-based, and per-cell sigma adjustments.

    * res_terms: dict mapping each term name to a sub-dict with three keys:

      - location (required): how to resolve the correction spatially;
        one of "hypo", "site", or "path".

      - sig_adjustment (optional, default "none"): the action to apply
        to the GMM sigma component - "sub", "add", "replace", or "none".
        When not "none", a sigma value must be provided in the HDF5 for
        each IMT group as either a scalar group attribute "{term}_sig" or
        a per-cell dataset of the same name. Providing both raises an
        error. Per-cell sigma is not supported currently for path-based terms.

      - sig_comp_modified (required when sig_adjustment is not "none"):
        which sigma component to modify - "tau", "phi", or "sig".

    :param hdf5_path:
        Path to the hdf5 containing the grid-based adjustments.
    """
    grids = {}
    path_pgns = {}
    sig_scalars = {}
    sig_grids = {}
    resolutions = set()
    with h5py.File(hdf5_path, "r") as hf:
        res_terms = json.loads(hf.attrs["res_terms"])
        for term in res_terms: # e.g. dS2S
            location = res_terms[term]["location"]
            sig_action = res_terms[term].get("sig_adjustment", "none")
            for imt_str in hf[term]: # e.g. SA(0.5)

                # Set stores if not already present
                grids.setdefault(imt_str, {})
                sig_scalars.setdefault(imt_str, {})
                sig_grids.setdefault(imt_str, {})
                
                # Get group and the mean adj values
                grp = hf[term][imt_str]
                mean_vals = grp[term][:]

                # Collect h3 resolutions for this term/IMT
                cell_ids = grp["cell_id"][:].astype(str)
                resolutions.update(h3.get_resolution(c) for c in cell_ids)

                # If required get sigma adjustment
                if sig_action != "none":
                    load_sigma_for_term(
                        grp, term, imt_str, location,
                        sig_action, cell_ids, sig_grids, sig_scalars
                        )

                # If path-based build OQ pgn grid for this term/IMT (keep
                # different grid per IMT in case varies with IMT as well)
                if location == "path":
                    path_pgns.setdefault(term, {})
                    # Build the h3 grid in OQ pgns
                    path_pgns[term][imt_str
                                    ] = build_raytrace_grid(cell_ids, mean_vals)
                else:
                    # Hypo/site based correction - store per cell mean adj
                    grids[imt_str][term] = dict(zip(cell_ids, mean_vals))

    return {"grids": grids,
            "path_pgns": path_pgns,
            "sig_scalars": sig_scalars,
            "sig_grids": sig_grids,
            "h3_res": sorted(resolutions), # Coarsest to finest h3 res
            "res_terms": res_terms}


def raytrace_path_adj(grid, hypo_lons, hypo_lats, site_lons, site_lats):
    """
    For each epicentre-to-site path (travel path) apply an adjustment based
    on the distance traversed through each (h3) grid cell. A conventional example
    would be if the user had a grid with an attenuation rate per km within each
    grid cell. The function will compute the distance through that cell, and
    retrieve a correction proportional to this distance to mean ground-motion.

    :param grid:
        {cell_id: (oq_pgn, per_km_adj_value)} for a single term and given imt
    :param hypo_lons:
        Array of hypocentre longitudes
    :param hypo_lats:
        Array of hypocentre latitudes
    :param site_lons:
        Array of site longitudes
    :param site_lats:
        Array of site latitudes
    :returns:
        adjustment_vals array of shape (len(hypo_lons),)
    """
    # Set some stores
    n_paths = len(hypo_lons)
    ra_per_path = np.zeros(n_paths)

    for idx_path in range(n_paths): # Iterate over the paths

        # Discretize the line
        dsct_line = npoints_between(
            site_lons[idx_path], site_lats[idx_path], 0.,
            hypo_lons[idx_path], hypo_lats[idx_path], 0.,
            100, # npoints
        )

        # Create mesh of discretized line
        mesh = Mesh(dsct_line[0], dsct_line[1])

        # Distance between consecutive discretised points along the path
        line_spacing = distance(
            mesh.lons[0], mesh.lats[0], 0.,
            mesh.lons[1], mesh.lats[1], 0.
        )

        # Get the cumulative correction based on distance traversed per
        # grid cell and the associated distance-based adjustment terms
        adj = 0.0
        for pgn, dba in grid.values(): # Iter over OQ pgns rep. of h3 cells

            # Adj = N points intersecting zone * spacing * per-km adjustment
            adj += np.count_nonzero(pgn.intersects(mesh)) * line_spacing * dba

        # Store the total cumulative adjustment for the term
        ra_per_path[idx_path] = adj

    return ra_per_path


def grid_lookup(grid_dict, lats, lons, h3_res):
    """
    For each (lat, lon) pair resolve the h3 cell starting at the finest
    h3 resolution and falling back to coarser resolutions, returning the
    mean adjustment for the given residual term. Locations that fall
    outside all grid cells receive a correction of zero.

    :param grid_dict:
        {cell_id: mean_adjustment_value} for a single correction term and IMT
    :param lats:
        Array of latitudes (either hypo or site lats, depending on term)
    :param lons:
        Array of longitudes (either hypo or site lons, depending on term)
    :param h3_res:
        Sorted list of h3 resolution levels (coarse to fine)
    :returns:
        mean_vals array of shape (len(lats),)
    """
    # Set arrays
    n = len(lats)
    mean_vals = np.zeros(n)
    found = np.zeros(n, dtype=bool)

    # Go over the h3 resolutions from finest to coarsest,
    # skipping locations already resolved at a finer level
    for res in reversed(h3_res):
        if found.all():
            break
        for i in np.where(~found)[0]:
            # Make a h3 cell for given hypo or site
            cell = h3.latlng_to_cell(lats[i], lons[i], res)
            if cell in grid_dict:
                # Assign mean adjustment of given term to the cell
                mean_vals[i] = grid_dict[cell]
                found[i] = True

    return mean_vals


def _adjust_sigma(grid_data, imt, term, cfg, ctx,
                  sig_action, sig, tau, phi):
    """
    Resolve the sigma adjustment value for this term/IMT, then apply
    it to the specified component.

    NOTE: Only one of sig_grids/sig_scalars dicts can be populated per
    term/IMT - this is enfored when loading the grid cells.
    """
    # Resolve sigma values - per-cell grid or scalar
    sig_grid = grid_data["sig_grids"].get(imt, {}).get(term)
    if sig_grid is not None:
        if cfg["location"] == "hypo":
            s_lats, s_lons = ctx.hypo_lat, ctx.hypo_lon
        else:
            s_lats, s_lons = ctx.lat, ctx.lon
        # Per-cell so look up the sigma adjustment value
        sig_vals = grid_lookup(
            sig_grid, s_lats, s_lons, grid_data["h3_res"])
    else:
        # Just a scalar adjustment
        sig_vals = grid_data["sig_scalars"].get(imt, {}).get(term)

    # Get the component to modify
    sig_comp = cfg["sig_comp_modified"]

    # And make the required adjustment to this component
    if sig_action == "replace":
        if sig_comp == "tau":
            # Adjust tau
            tau[:] = sig_vals
            # Recompute total sigma accordingly
            sig[:] = np.sqrt(tau ** 2 + phi ** 2)
        elif sig_comp == "phi":
            # Adjust phi
            phi[:] = sig_vals
            # Recompute total sigma accordingly
            sig[:] = np.sqrt(tau ** 2 + phi ** 2)
        else:
            # Adjust total sigma
            sig[:] = sig_vals
    else:
        sign = -1 if sig_action == "sub" else 1
        if sig_comp == "tau":
            # Adjust tau
            tau[:] = np.sqrt(tau ** 2 + sign * sig_vals ** 2)
            # Recompute total sigma accordingly
            sig[:] = np.sqrt(tau ** 2 + phi ** 2)
        elif sig_comp == "phi":
            # Adjust phi
            phi[:] = np.sqrt(phi ** 2 + sign * sig_vals ** 2)
            # Recompute total sigma accordingly
            sig[:] = np.sqrt(tau ** 2 + phi ** 2)
        else:
            # Adjust total sigma
            sig[:] = np.sqrt(sig ** 2 + sign * sig_vals ** 2)


def _apply_grid_corrections(grid_data, ctx, imt, mean, sig, tau, phi):
    """
    Look up and apply corrections defined in the hdf5. The mean
    adjustment is always added.

    :param grid_data:
        Dict returned by load_residual_grids
    :param ctx:
        A ctx object recarray
    :param imt:
        An IMT class instance
    :param mean:
        Mean predictions (standard 1d numpy array from compute)
    :param sig:
        Sigma (standard 1d numpy array from compute)
    :param tau:
        Tau (standard 1d numpy array from compute)
    :param phi:
        Phi (standard 1d numpy array from compute)
    """
    # Get adjustment data for given imt
    entry = grid_data["grids"].get(imt)
    
    # Check if no data
    if entry is None:
        return 
    
    # Apply each correction
    for term, cfg in grid_data["res_terms"].items():
        # Example of (term, cfg):
        # term = 'dL2L'
        # cfg = {'location': "hypo", sig_adjustment: "add", sig_comp_modified: "tau"}

        # Check sigma adjustment configuration
        sig_action = cfg.get("sig_adjustment", "none")

        # The term can be selected based on hypo or site location or both
        if cfg["location"] == "path":
            # Travel path based (ray-tracing)
            if term not in grid_data["path_pgns"] or imt not in grid_data["path_pgns"][term]:
                # Skip if this term has no data for the given IMT
                continue
            mean_adj = raytrace_path_adj(
                grid_data["path_pgns"][term][imt], # Grid of OQ pgns + adjs
                ctx.hypo_lon, ctx.hypo_lat,
                ctx.lon, ctx.lat,
                )
        else:
            # Skip if this term has no data for the given IMT
            if term not in entry:
                continue

            if cfg["location"] == "hypo":
                # Hypo location-based
                lats, lons = ctx.hypo_lat, ctx.hypo_lon
            else:
                # Site location-based
                lats, lons = ctx.lat, ctx.lon

            # Get a grid-cell lookup-based mean adjustment
            mean_adj = grid_lookup(
                entry[term], lats, lons, grid_data["h3_res"])

        # Apply adjustment to mean prediction
        mean += mean_adj

        # Skip sigma adjustment if not configured for this term
        if sig_action == "none":
            continue

        # Apply sigma adjustment to required component
        _adjust_sigma(
            grid_data, imt, term, cfg, ctx, sig_action, sig, tau, phi)


class GridAdjustedGMPE(GMPE):
    """
    A GSIM class that applies spatially-varying corrections stored in
    a hdf5 file of h3-gridded residual terms to the underlying GMM.

    The hdf5 file contains a root-level attribute that configures the
    adjustment behaviour:

    * res_terms: A JSON-encoded dict mapping each top-level group name (each key
      is a corrective term e.g. dL2L) to a sub-dict with one mandatory key:

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

        * A scalar adjustment (group attribute "{term}_sig") - one value applied
          uniformly across all hypocentres or sites.

        * A dataset named "{term}_sig" - one value per h3 cell, looked up
          spatially in the same way as the mean adjustment (hypo or site
          location; not supported yet for path-based terms).
          
        NOTE: Providing both a scalar adjustment and a cell-by-cell adjustment
        raises an error - you must select one or the other for each correction.

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

    NOTE: The corrective terms (each key in the res_terms dict) are not fixed - the
    user can specify as they wish (e.g. they may wish to only include dS2S).
    
    NOTE: Corrections are stored per IMT in the HDF5. If an IMT group is missing
    for a given term, no correction is applied for that IMT (no error is raised).

    NOTE: The h3 grid cell resolution can vary (i.e., densify) or be constant.

    NOTE: The h3 cell IDs (i.e. the grids) are on an IMT-by-IMT basis because the
    availability of data used to derive the corrections might vary with period.

    A "real" example of this hdf5 structure can be found in the unit tests
    associated with this mgmpe module:
    oq-engine/openquake/hazardlib/tests/gsim/mgmpe/data/test_grid_adjustments.hdf5

    A use case (from XML) can be found in the classical QA tests (there is 
    also a readme visualising the hdf5 information):
    oq-engine/openquake/qa_tests_data/classical/case_11/grid_adjustments.hdf5

    :param gmpe_name:
        The underlying GMM to apply the grid-based adjustments to.

    :param grid_hdf5_file:
        Path to the hdf5 file with gridded adjustments.
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

    def __init__(self, gmpe_name, grid_hdf5_file, **kwargs):
        
        # Instantiate the underlying GMM
        self.gmpe = registry[gmpe_name](**kwargs)
        self.set_parameters()

        # Load grid-based corrections from the hdf5
        self.grid_data = load_residual_grids(grid_hdf5_file)

        # Check for any invalid 'location' assignments in res_terms
        if any(cfg['location'] not in ['hypo', 'site', 'path'] for
               cfg in self.grid_data["res_terms"].values()):
            raise ValueError(
                "An invalid location type has been specified for one or more "
                "of the adjustment terms (must be 'hypo', 'site' or 'path'.")

        # Add hypo lon/lat to required GSIM rup params for hypo-based lookups
        if any(cfg["location"] in ["hypo", "path"]
               for cfg in self.grid_data["res_terms"].values()):
            self.REQUIRES_RUPTURE_PARAMETERS = frozenset(
                self.REQUIRES_RUPTURE_PARAMETERS | {'hypo_lat', 'hypo_lon'})

        # Add site lat/lon to required GSIM site params for site-based lookups
        if any(cfg["location"] in ["site", "path"]
               for cfg in self.grid_data["res_terms"].values()):
            self.REQUIRES_SITES_PARAMETERS = frozenset(
                self.REQUIRES_SITES_PARAMETERS | {'lat', 'lon'})

        # Ensure inter/intra-event std devs are computed by the base GSIM
        if any(cfg.get("sig_adjustment", "none") != "none"
               and cfg.get("sig_comp_modified") in ("tau", "phi")
               for cfg in self.grid_data["res_terms"].values()):
            required = {const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}
            # Raise error if not a random-effects GSIM
            if not required.issubset(self.DEFINED_FOR_STANDARD_DEVIATION_TYPES):
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
        # Compute original mean
        self.gmpe.compute(ctx, imts, mean, sig, tau, phi)
        
        # Apply grid-based corrections
        for m, imt in enumerate(imts):
            _apply_grid_corrections(self.grid_data, ctx, str(imt),
                                    mean[m], sig[m], tau[m], phi[m])