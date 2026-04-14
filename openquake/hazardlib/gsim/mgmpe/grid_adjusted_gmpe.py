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
from openquake.hazardlib.gsim.base import GMPE, registry


def load_residual_grids(hdf5_path):
    """
    Load the hdf5 residual grids into a dict with three keys:

    * grids: nested dict of {imt_str: {term: {cell_id: val}, ...}}
    
    * h3_res: sorted (coarsest to finest) list of h3 resolutions,
      derived automatically from the cell IDs in the grids
    
    * res_terms: dict mapping each term name to a sub-dict with location
      (hypo or site), sig_comp_modified (tau, phi, or sig), and
      sigma_adjustment (sub, add, or none; default none)

    :param hdf5_path:
        Path to the hdf5 containing the grid-based adjustments
    """
    grids = {}
    resolutions = set()
    with h5py.File(hdf5_path, "r") as hf:
        res_terms = json.loads(hf.attrs["res_terms"])
        for term in res_terms:
            for imt_str in hf[term]:
                if imt_str not in grids:
                    grids[imt_str] = {} # No adjustment for given IMT
                grp = hf[term][imt_str]
                cell_ids = grp["cell_id"][:].astype(str)
                resolutions.update( # Get h3 resolution
                    h3.get_resolution(c) for c in cell_ids)
                grids[imt_str][term] = dict(zip(
                    cell_ids, grp[term][:]))
                grids[imt_str][f"{term}_std"] = dict(zip(
                    cell_ids, grp[f"{term}_std"][:]))
                
    return {"grids": grids,
            "h3_res": sorted(resolutions), # Coarsest to finest h3 res
            "res_terms": res_terms}


def grid_lookup(mean_dict, std_dict, lats, lons, h3_res):
    """
    For each (lat, lon) pair resolve the h3 cell at successively finer
    resolutions and return the gridded adjustment and its uncertainty
    for the given residual term. Locations that fall outside all grid
    cells receive a correction of zero.

    :param mean_dict:
        {cell_id: adjustment_value} for a single correction term and given imt
    :param std_dict:
        {cell_id: std_value} for a single correction term and given imt
    :param lats:
        Array of latitudes (either hypo or site lats, depending on term)
    :param lons:
        Array of longitudes (either hypo or site lons, depending on term)
    :param h3_res:
        Sorted list of h3 resolution levels (coarse to fine)
    :returns:
        (adjustment_vals, std_vals) arrays of shape (len(lats),)
    """
    # Set arrays
    n = len(lats)
    mean_vals = np.zeros(n, dtype=np.float32)
    std_vals = np.zeros(n, dtype=np.float32)
    found = np.zeros(n, dtype=bool)

    # Go over the h3 resolutions from coarsest to finest
    for res in h3_res:
        if found.all():
            # Stop once all locations have been found
            break
        for i in np.where(~found)[0]:
            # Make a h3 cell
            cell = h3.latlng_to_cell(float(lats[i]), float(lons[i]), res)
            if cell in mean_dict:
                # Assign mean and std dev of given term to the cell
                mean_vals[i] = mean_dict[cell]
                std_vals[i] = std_dict[cell]
                found[i] = True

    return mean_vals, std_vals


def _apply_grid_corrections(grid_data, ctx, imt,
                            mean, sig, tau, phi):
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
    entry = grid_data["grids"].get(str(imt))
    
    # Check if no data
    if entry is None:
        return 
    
    # Apply each correction
    for term, cfg in grid_data["res_terms"].items():

        # Skip if this term has no data for the given IMT
        if term not in entry:
            continue

        # The term can be selected based on hypo or site location
        if cfg["location"] == "hypo":
            # Hypo location-based
            lats, lons = ctx.hypo_lat, ctx.hypo_lon
        else:
            # Site location-based
            lats, lons = ctx.lat, ctx.lon

        # Get the adjustments
        delta_mean, delta_std =\
              grid_lookup(
                  entry[term], entry[f"{term}_std"],
                  lats, lons, grid_data["h3_res"]
                  )
        
        # Apply adjustment to mean prediction
        mean += delta_mean

        # Skip sigma adjustment if configured as "none"
        sig_action = cfg.get("sigma_adjustment", "none")
        if sig_action == "none":
            continue

        # Apply adjustment to required component of GMM sigma
        sign = -1 if sig_action == "sub" else 1
        sig_comp = cfg["sig_comp_modified"]
        if sig_comp == "tau":
            # Adjust tau and recompute total sigma too accordingly
            tau[:] = np.sqrt(tau ** 2 + sign * delta_std ** 2)
            sig[:] = np.sqrt(tau ** 2 + phi ** 2)
        elif sig_comp == "phi":
            # Adjust phi and recompute total sigma too accordingly
            phi[:] = np.sqrt(phi ** 2 + sign * delta_std ** 2)
            sig[:] = np.sqrt(tau ** 2 + phi ** 2)
        else:
            # Adjust total sigma
            assert sig_comp == "sig"
            sig[:] = np.sqrt(sig ** 2 + sign * delta_std ** 2)


class GridAdjustedGMPE(GMPE):
    """
    A GSIM class that applies spatially-varying corrections stored in
    a hdf5 file of h3-gridded residual terms to the underlying GMM.

    The hdf5 file contains a root-level attribute that configures the
    adjustment behaviour:

    * res_terms: A JSON-encoded dict mapping each top-level group name
      to a sub-dict with two three keys:

      * location: How to resolve the correction spatially, with each look-up
         resolving the location to a h3 cell, searching from coarse to fine. If
         a location falls outside all grid cells the correction is zero:

        * hypo - Use the rupture hypocentre (ctx.hypo_lat, ctx.hypo_lon)

        * site - Use the site location (ctx.lat, ctx.lon)

      * sig_comp_modified: Which std-dev component to adjust for the given
        residual term:
        
        * tau = Adjust inter-event std dev

        * phi = Adjust intra-event std dev
        
        * sig = Adjust total std dev

      * sigma_adjustment (optional, default "none"): Whether to subtract or add
        the std-dev delta, or skip the sigma adjustment entirely:

        * none = Skip sigma adjustment (only apply mean correction)

        * sub = Subtract variance (reduce sigma)

        * add = Add variance (inflate sigma)

    The h3 grid cell resolution can vary (i.e., densify) or be constant.

    A "real" example of this hdf5 can be found in the unit tests
    associated with this mgmpe module:
    oq-engine\openquake\hazardlib\tests\gsim\mgmpe\data\test_grid_adjustments.hdf5

    A use case (from XML) can be found in the classical QA tests:
    oq-engine\openquake\qa_tests_data\classical\case_11\grid_adjustments.hdf5

    :param gmpe_name:
        The underlying GMM to apply the grid-based adjustments too.
    :param grid_hdf5_file:
        Path to the hdf5 file with gridded adjustments.
    """
    # Req Params — set from underlying GMM via set_parameters()
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

        # Add hypo lon/lat to required GSIM params to retain it in ctx
        if any(cfg["location"] == "hypo"
               for cfg in self.grid_data["res_terms"].values()):
            self.REQUIRES_RUPTURE_PARAMETERS = frozenset(
                self.REQUIRES_RUPTURE_PARAMETERS | {'hypo_lat', 'hypo_lon'})

        # Add lat/lon to required site params for site-based lookups
        if any(cfg["location"] == "site"
               for cfg in self.grid_data["res_terms"].values()):
            self.REQUIRES_SITES_PARAMETERS = frozenset(
                self.REQUIRES_SITES_PARAMETERS | {'lat', 'lon'})

        # Ensure inter/intra-event std devs are computed by the base GSIM
        if any(cfg["sig_comp_modified"] in ("tau", "phi")
               and cfg.get("sigma_adjustment", "none") != "none"
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
            _apply_grid_corrections(self.grid_data, ctx, imt,
                                    mean[m], sig[m], tau[m], phi[m])