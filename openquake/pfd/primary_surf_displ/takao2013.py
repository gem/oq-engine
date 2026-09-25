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
Module :mod:`openquake.pfd.primary_surf_displ.takao2013` implements the
model of Takao et al. (2013) in :class:`Takao2013PrimaryFD`.
"""

import numpy as np
from scipy.stats import gamma, norm, beta
from openquake.pfd.params import check_choice, check_style
from openquake.pfd.primary_surf_displ.base import BasePrimarySurfDispl



class Takao2013PrimaryFD(BasePrimarySurfDispl):
    """Principal fault-displacement model of Takao et al. (2013).

    Model of principal (reverse-faulting) fault displacement as a function of
    magnitude and normalized along-strike position.

    Takao, M., et al. (2013). Application of probabilistic fault displacement
    hazard analysis in Japan.

    The conditional AD/MD log10-normal distribution is integrated over a
    truncation range of ``mean ± n_sigma·sigma`` (in log10 space). The
    truncation level ``n_sigma`` defaults to 3 and may be overridden from the
    logic tree via ``[Takao2013PrimaryFD] n_sigma = <value>``.

    Model contract: DISPLACEMENT_DEFINITION = "principal",
    DISPLACEMENT_COMPONENT = "net" -- Takao et al. (2013, JAEE 13) model
    displacement on the principal fault only (their nu_p1 term, distributed
    faulting handled by the separate nu_d2 chain), normalised by the Wells &
    Coppersmith AD/MD which are net (resultant) slip measures; component per
    the summary in Valentini et al. (2025, Rev. Geophys.) Table 4.
    """

    DISPLACEMENT_DEFINITION = "principal"
    DISPLACEMENT_COMPONENT = "net"

    _N_INTEGRATION = 1000

    def __init__(self, n_sigma=3.0, norm_disp_type=None, style=None):
        """
        :param n_sigma: truncation half-width of the AD/MD distribution.
        :param norm_disp_type: optional normalization type pinned by the
            logic-tree branch ('AD' or 'MD'); ``None`` defers to the
            ``get_prob`` call.
        :param style: optional faulting style declared by the logic-tree
            branch. The Takao et al. (2013) regressions pool Japanese
            events in single equations, so the value does not change the
            numbers; it is stored (validated against the global style
            vocabulary) as a declaration of the branch context.
        """
        self.n_sigma = float(n_sigma)
        if self.n_sigma <= 0.0:
            raise ValueError(f"n_sigma must be positive; got {self.n_sigma}")
        self.norm_disp_type = check_choice(
            type(self).__name__, "norm_disp_type", norm_disp_type,
            frozenset(["AD", "MD"]), canon=lambda v: str(v).upper())
        self.style = check_style(type(self).__name__, style)

    def get_prob(self, d, X_L_ratio, mag, norm_disp_type=None):
        """
        Model of Takao et al. (2013) for the probability of exceeding
        threshold values of primary displacement [m]

        :param d:
            target displacement (scalar or array-like, shape (n_displacements,))
        :param X_L_ratio:
            Ratio of distance from the closest rupture end to the total rupture length
            (scalar or array-like, shape (n_sites,))
        :param mag:
            Earthquake magnitude (scalar)
        :param srl:
            Surface rupture length in km
        :param norm_disp_type:
            Normalization displacement type. Valid options are "AD" or "MD".
        :returns:
            Probability of exceeding target displacement (m), shape (n_displacements, n_sites).
        """
        # Define the accepted Normalization displacement types
        accepted_version = ["AD", "MD"]

        # Use Wells and Coppersmith 1994 law to estimate the surface rupture length (srl) in km
        srl = 10 ** (-2.86 + 0.63 * mag)
        # Validate the style
        if norm_disp_type is None:
            norm_disp_type = self.norm_disp_type
        if norm_disp_type is None:
            raise ValueError(
                f"{type(self).__name__}: norm_disp_type must be given either "
                f"in the logic-tree branch or at call time")
        if norm_disp_type not in accepted_version:
            raise ValueError(
                f"Invalid style '{norm_disp_type}'. Accepted values are: {', '.join(accepted_version)}"
            )

        # Convert inputs to numpy arrays
        d = np.atleast_1d(d)  # Shape (n_displacements,)
        X_L_ratio = np.atleast_1d(X_L_ratio)  # Shape (n_sites,)

        # Fold the raw along-strike position x/L in [0, 1] to the normalized
        # distance from the *closest* rupture end in [0, 0.5], which is what the
        # Takao et al. (2013) regression coefficients in get_prob_D_AD /
        # get_prob_D_MD are defined against (see the X_L_ratio docstring). Without
        # this fold the gamma mean would grow monotonically toward x/L = 1,
        # producing an unphysical along-strike ramp instead of a symmetric,
        # centre-peaked displacement profile. Mirrors Youngs2003PrimaryFD.
        r = X_L_ratio - np.floor(X_L_ratio)
        X_L_ratio = 0.5 - np.abs(r - 0.5)

        # Following the approach in Youngs2003, we need to establish truncation bounds
        if norm_disp_type == "AD":
            # Based on Wells and Coppersmith (1994) for average displacement
            log_mean = -4.80 + 0.69 * mag
            sigma = 0.36

        elif norm_disp_type == "MD":
            # Takao et al. (2013) Eq. 9: their refit of the Wells & Coppersmith
            # (1994) maximum-displacement relation (constant term 0.3 larger)
            log_mean = -5.16 + 0.82 * mag
            sigma = 0.42

        d_truncation = self.n_sigma  # ±n_sigma
        # Truncation bounds in log10 space
        lower = 10 ** (log_mean - d_truncation * sigma)
        upper = 10 ** (log_mean + d_truncation * sigma)

        # Use logspace values for numerical integration
        logspace_vals = np.logspace(np.log10(lower), np.log10(upper), self._N_INTEGRATION)

        # Initialize output array: (n_displacements, n_sites)
        n_displacements = len(d)
        n_sites = len(X_L_ratio)
        prob_exceeding_d = np.zeros((n_displacements, n_sites))

        # Vectorized integration over displacement values
        for disp in logspace_vals:
            D_NormD = d / disp  # Shape (n_displacements,)
            # Reshape for broadcasting: (n_displacements, 1) and (1, n_sites)
            D_NormD_reshaped = D_NormD[:, np.newaxis]  # Shape (n_displacements, 1)
            X_L_reshaped = X_L_ratio[np.newaxis, :]  # Shape (1, n_sites)

            if norm_disp_type == "AD":
                p3 = self.get_prob_D_AD(D_NormD_reshaped, X_L_reshaped, srl) * self.get_prob_avg_displacement(disp, mag)
                prob_exceeding_d += p3
            elif norm_disp_type == "MD":
                p3 = self.get_prob_D_MD(D_NormD_reshaped, X_L_reshaped, srl) * self.get_prob_max_displacement(disp, mag)
                prob_exceeding_d += p3

        return prob_exceeding_d


    def get_prob_D_AD(self, D_AD, x_L_ratio, srl):
        """
        Model of Takao et al. (2013) for the probability of normalized displacement

        :param D_AD:
            Normalized displacement (D/Avg_D)
        :param x_L_ratio:
            Ratio of distance from the closest rupture end to the total rupture length
        :param srl:
            Surface rupture length in km
        :returns:
            Probability of exceeding 'norm_disp'
        """

        if srl < 10:
            a = 1.53
            b = 0.58
        else:
            a = np.exp(0.7 + 0.34 * x_L_ratio)
            b = np.exp(-1.4 + 1.82 * x_L_ratio)

        return 1. - gamma.cdf(D_AD, a, loc=0, scale=b)

    def get_prob_avg_displacement(self, target_ad, mag: float) -> float:
        """
        Calculate the normalized normal pdf of log10(average displacement) based on magnitude
        using Wells and Coppersmith (1994) for all faulting

        :param target_ad: Average displacement in meters
        :param magnitude: Earthquake magnitude
        :returns: Probability of average displacement
        """
        # Based on Wells and Coppersmith (1994) for average displacement
        log_mean = -4.80 + 0.69 * mag
        sigma = 0.36
        d_truncation = self.n_sigma  # ±n_sigma

        # Truncation bounds in log10 space
        lower = 10 ** (log_mean - d_truncation * sigma)
        upper = 10 ** (log_mean + d_truncation * sigma)

        prob_avg_displacement = norm.pdf(np.log10(target_ad), loc=log_mean, scale=sigma)

        # Normalizing the distribution with the same truncation bounds
        logspace_vals = np.logspace(np.log10(lower), np.log10(upper), self._N_INTEGRATION)
        prob = norm.pdf(np.log10(logspace_vals), loc=log_mean, scale=sigma)
        normalization_factor = sum(prob)

        return prob_avg_displacement / normalization_factor


    def get_prob_D_MD(self, D_MD, x_L_ratio, srl):
        """
        Model of Takao et al. (2013) for the probability of normalized displacement

        :param D_MD:
            Normalized displacement (D/Max_D)
        :param x_L_ratio:
            Ratio of distance from the closest rupture end to the total rupture length
        :param srl:
            Surface rupture length in km
        :returns:
            Probability of exceeding 'norm_disp'
        """

        if srl < 10:
            a = 0.91
            b = 1.9
        else:
            a = np.exp(0.7 - 0.87 * x_L_ratio)
            b = np.exp(2.3 - 3.84 * x_L_ratio)

        return 1. - beta.cdf(D_MD, a, b)

    def get_prob_max_displacement(self, target_md, mag: float) -> float:
        """
        Calculate the log-normal pdf of maximum displacement based on magnitude
        using Wells and Coppersmith (1994) for all style of faultings

        :param target_md: Maximum displacement in meters
        :param magnitude: Earthquake magnitude
        :returns: Probability of maximum displacement
        """
        # Takao et al. (2013) Eq. 9: their refit of the Wells & Coppersmith
        # (1994) maximum-displacement relation (constant term 0.3 larger)
        log_mean = -5.16 + 0.82 * mag
        sigma = 0.42
        d_truncation = self.n_sigma  # ±n_sigma

        # Strike-slip
        #log_mean = -7.03 + 1.03 * mag
        #sigma = 0.34

        # Truncation bounds in log10 space
        lower = 10 ** (log_mean - d_truncation * sigma)
        upper = 10 ** (log_mean + d_truncation * sigma)

        prob_max_displacement = norm.pdf(np.log10(target_md), loc=log_mean, scale=sigma)

        # Normalizing the distribution with the same truncation bounds
        logspace_vals = np.logspace(np.log10(lower), np.log10(upper), self._N_INTEGRATION)
        prob = norm.pdf(np.log10(logspace_vals), loc=log_mean, scale=sigma)
        normalization_factor = sum(prob)

        return prob_max_displacement / normalization_factor