# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024-2026 Yen-Shin Chen, OGS
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""
Module :mod:`openquake.pfd.secondary_surf_displ.youngs2003` implements the
model of Youngs et al. (2003) in :class:`Youngs2003SecondaryFD`.
"""

import numpy as np
from scipy.stats import gamma, norm
from openquake.pfd.params import check_choice, check_style
from openquake.pfd.primary_surf_displ.base import BaseSecondarySurfDispl


class Youngs2003SecondaryFD(BaseSecondarySurfDispl):
    """Distributed fault-displacement model of Youngs et al. (2003).

    
    Youngs, R.R., et al. (2003). A methodology for probabilistic fault
    displacement hazard analysis (PFDHA). Earthquake Spectra, 19(1), 191-219.

    Model contract: DISPLACEMENT_DEFINITION = "distributed",
    DISPLACEMENT_COMPONENT = "vertical" -- distributed (off-fault) vertical
    separation of normal-faulting earthquakes, normalised by the principal
    maximum displacement (Youngs et al. 2003; Sarmiento et al. 2025 Table 1
    component convention as for YEA03). Declared applicability: r up to
    15 km from the principal fault (dataset range summarised in Valentini
    et al. 2025, Rev. Geophys., Table 4).
    """

    DISPLACEMENT_DEFINITION = "distributed"
    DISPLACEMENT_COMPONENT = "vertical"

    APPLICABILITY_RANGE = {
        "r_max_km": 15.0,
        "source": "Valentini et al. (2025) Rev. Geophys. Table 4 "
                  "(Youngs et al. 2003 dataset range)",
    }

    # Constants for Wells & Coppersmith (1994) formulas for normal faulting
    _WC94_MD_INTERCEPT = -5.90
    _WC94_MD_SLOPE = 0.89
    _WC94_MD_SIGMA = 0.38

    _D_TRUNCATION = 3.0  # ±3 sigma for truncation
    _NUM_INTEGRATION_POINTS = 100
    _ACCEPTED_PERCENTILES = {"85", "95", 85, 95}
    _GAMMA_SHAPE = 2.5  # Shape parameter 'a' for gamma distribution

    # Scaling factors for different percentiles
    _PERCENTILE_SCALING = {
        "85": 4.058,
        "95": 5.535,
        85: 4.058,
        95: 5.535
    }

    def __init__(self, percentile=None, style=None):
        """
        :param percentile: optional hanging-wall percentile curve pinned by
            the logic-tree branch ('85' or '95'; integers accepted);
            ``None`` defers to the ``get_prob`` call (legacy default: '85').
        :param style: optional faulting style declared by the logic-tree
            branch. The Youngs et al. (2003) secondary displacement
            regressions carry no style selector, so the value does not
            change the numbers; it is stored (validated against the global
            style vocabulary) as a declaration of the branch context.
        """
        self.percentile = check_choice(
            type(self).__name__, "percentile", percentile,
            frozenset(["85", "95"]), canon=str)
        self.style = check_style(type(self).__name__, style)
        # Pre-calculate common values
        self._norm_pdf_cache = {}

    def get_prob(self, d, mag, rx, r, percentile=None):
        """
        Model of Youngs et al. (2003) for the probability of exceeding
        threshold values of secondary displacement [m]

        :param d: Target displacement in meters (array of shape (n_displacements,))
        :param mag: Earthquake magnitude (scalar)
        :param rx: Distance from the closest rupture (scalar or array of shape (n_sites,))
        :param r: Distance from the rupture trace (scalar or array of shape (n_sites,))
        :param percentile: The percentile used in calculations ("85" or "95")
        :returns: Probability of exceeding the given displacement (shape (n_sites, n_displacements))
        """
        # Fall back to constructor-pinned value, then legacy default
        if percentile is None:
            percentile = (self.percentile
                          if self.percentile is not None else "85")
        # Validate percentile
        if percentile not in self._ACCEPTED_PERCENTILES:
            raise ValueError(
                f"Invalid percentile '{percentile}'. Accepted values are: {', '.join(self._ACCEPTED_PERCENTILES)}"
            )

        # Ensure inputs are arrays
        d = np.asarray(d)  # Shape (n_displacements,)
        rx = np.asarray(rx)  # Shape (n_sites,) or scalar
        r = np.asarray(r)  # Shape (n_sites,) or scalar
        if rx.ndim == 0:
            rx = np.array([rx])
        if r.ndim == 0:
            r = np.array([r])
        n_sites = rx.shape[0]

        # Calculate log-normal distribution parameters
        log_mean = self._WC94_MD_INTERCEPT + self._WC94_MD_SLOPE * mag
        sigma = self._WC94_MD_SIGMA

        # Calculate truncation range for integration
        lower = 10 ** (log_mean - self._D_TRUNCATION * sigma)
        upper = 10 ** (log_mean + self._D_TRUNCATION * sigma)

        # Use logarithmic spacing for the numerical integration
        logspace_vals = np.logspace(np.log10(lower), np.log10(upper), self._NUM_INTEGRATION_POINTS)

        # Initialize output array
        prob_exceeding_d = np.zeros((n_sites, d.shape[0]))  # Shape (n_sites, n_displacements)

        # Calculate probabilities for each max displacement
        for max_disp in logspace_vals:
            D_MD = d / max_disp  # Shape (n_displacements,)
            prob_D_MD = self.get_prob_D_MD(D_MD, rx, r, percentile)  # Shape (n_sites, n_displacements)
            prob_max_disp = self.get_prob_max_displacement(max_disp, mag)  # Scalar
            prob_exceeding_d += prob_D_MD * prob_max_disp

        return prob_exceeding_d

    def get_prob_D_MD(self, D_MD, rx, r, percentile="85"):
        """
        Model of Youngs et al. (2003) for the probability of normalized displacement

        :param D_MD: Normalized displacement (D/Max_D) (array of shape (n_displacements,))
        :param rx: Distance from the closest rupture (scalar or array of shape (n_sites,))
        :param r: Distance from the rupture trace (scalar or array of shape (n_sites,))
        :param percentile: The percentile used for scaling ("85" or "95")
        :returns: Probability of exceeding 'norm_disp' (shape (n_sites, n_displacements))
        """
        # Validate percentile
        if percentile not in self._ACCEPTED_PERCENTILES:
            raise ValueError(
                f"Invalid percentile '{percentile}'. Accepted values are: {', '.join(self._ACCEPTED_PERCENTILES)}"
            )

        # Ensure inputs are arrays
        D_MD = np.asarray(D_MD)  # Shape (n_displacements,)
        rx = np.asarray(rx)  # Shape (n_sites,) or scalar
        r = np.asarray(r)  # Shape (n_sites,) or scalar
        if rx.ndim == 0:
            rx = np.array([rx])
        if r.ndim == 0:
            r = np.array([r])

        # Calculate the scaling factor based on distance and rupture position
        x = np.where(rx > 0., 0.35 * np.exp(-0.091 * r), 0.16 * np.exp(-0.137 * r))  # Shape (n_sites,)

        # Calculate gamma distribution parameters
        a = self._GAMMA_SHAPE
        b = x / self._PERCENTILE_SCALING[percentile]  # Shape (n_sites,)

        # Compute survival function for each site and displacement
        # Reshape arrays for broadcasting: D_MD (1, n_displacements), b (n_sites, 1)
        D_MD = D_MD[np.newaxis, :]  # Shape (1, n_displacements)
        b = b[:, np.newaxis]  # Shape (n_sites, 1)
        return gamma.sf(D_MD, a, loc=0, scale=b)  # Shape (n_sites, n_displacements)

    def get_prob_max_displacement(self, target_md, mag):
        """
        Calculate the log-normal pdf of maximum displacement based on magnitude
        using Wells and Coppersmith (1994) for normal faulting

        :param target_md: Maximum displacement in meters
        :param mag: Earthquake magnitude
        :returns: Probability of maximum displacement
        """
        # Create a cache key
        cache_key = round(mag, 2)

        if cache_key in self._norm_pdf_cache:
            log_mean, log_max_disp, sigma, norm_factor = self._norm_pdf_cache[cache_key]
        else:
            # Calculate parameters
            log_mean = self._WC94_MD_INTERCEPT + self._WC94_MD_SLOPE * mag
            log_max_disp = np.log10(10 ** log_mean)  # This simplifies to log_mean but kept for clarity
            sigma = self._WC94_MD_SIGMA

            # Calculate normalization factor
            lower = 10 ** (log_mean - self._D_TRUNCATION * sigma)
            upper = 10 ** (log_mean + self._D_TRUNCATION * sigma)
            logspace_vals = np.logspace(np.log10(lower), np.log10(upper), self._NUM_INTEGRATION_POINTS)
            prob = norm.pdf(np.log10(logspace_vals), loc=log_max_disp, scale=sigma)
            norm_factor = np.sum(prob)

            # Store in cache
            self._norm_pdf_cache[cache_key] = (log_mean, log_max_disp, sigma, norm_factor)

        # Calculate probability
        prob_max_displacement = norm.pdf(np.log10(target_md), loc=log_max_disp, scale=sigma)
        return prob_max_displacement / norm_factor