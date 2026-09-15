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
Module :mod:`openquake.pfd.secondary_surf_displ.takao2013` implements the
model of Takao et al. (2013) in :class:`Takao2013SecondaryFD`.

Supported Fault Styles: Reverse and Strike-slip

References
----------
Takao, M., Tsuchiyama, J., Annaka, T., & Kurita, T. (2013). Application of
probabilistic fault displacement hazard analysis in Japan. Journal of Japan
Association for Earthquake Engineering, 13(1), 17-36.
https://doi.org/10.5610/jaee.13.17
"""

import numpy as np
from scipy.stats import gamma, norm
from openquake.pfd.params import check_choice
from openquake.pfd.primary_surf_displ.base import BaseSecondarySurfDispl


class Takao2013SecondaryFD(BaseSecondarySurfDispl):
    """Distributed fault-displacement model of Takao et al. (2013).

    The distributed displacement DD is normalized by the maximum (PMD) or
    average (PAD) displacement of the principal fault. The 90% non-exceedance
    level decays exponentially with the closest distance r [km] from the
    principal fault (paper Eqs. 15-16):

        DD/PMD = 0.55 exp(-0.17 r)        DD/PAD = 1.9 exp(-0.17 r)

    Following Youngs et al. (2003), the conditional distribution of the
    normalized displacement is a gamma distribution with shape a = 2.5 whose
    scale b(r) is anchored so its 90th percentile equals the regression above
    (paper Eq. 17). PMD and PAD follow the paper's magnitude scaling
    (Eqs. 9-10), lognormal with the Wells & Coppersmith (1994) sigmas:

        log10(PMD) = -5.16 + 0.82 Mw  (sigma 0.42)
        log10(PAD) = -4.80 + 0.69 Mw  (sigma 0.36)

    The PMD/PAD lognormal is integrated over ``mean ± n_sigma·sigma`` (log10
    space); ``n_sigma`` defaults to 3 and may be overridden from the logic
    tree via ``[Takao2013SecondaryFD] n_sigma = <value>``.

    Model contract: DISPLACEMENT_DEFINITION = "distributed",
    DISPLACEMENT_COMPONENT = "net" -- distributed displacement normalised by
    the principal-fault PMD/PAD net-slip scaling (Takao et al. 2013, Eqs.
    15-17; component convention per Valentini et al. 2025, Rev. Geophys.,
    Table 4). Declared applicability: r up to 20 km (ibid., dataset range
    of the Eqs. 15-16 regressions).
    """

    DISPLACEMENT_DEFINITION = "distributed"
    DISPLACEMENT_COMPONENT = "net"

    APPLICABILITY_RANGE = {
        "r_max_km": 20.0,
        "source": "Valentini et al. (2025) Rev. Geophys. Table 4 "
                  "(Takao et al. 2013 dataset range)",
    }

    _N_INTEGRATION = 1000
    _GAMMA_SHAPE = 2.5

    # Coefficients of the 90% non-exceedance regressions (Eqs. 15-16) and of
    # the magnitude scaling of the normalizing displacement (Eqs. 9-10).
    _COEFFS = {
        "MD": {"c90": 0.55, "log_intercept": -5.16, "log_slope": 0.82,
               "sigma": 0.42},
        "AD": {"c90": 1.9, "log_intercept": -4.80, "log_slope": 0.69,
               "sigma": 0.36},
    }
    _DECAY = -0.17  # per km, shared by Eqs. 15 and 16

    def __init__(self, n_sigma=3.0, norm_disp_type=None):
        """
        :param n_sigma: truncation half-width of the AD/MD distribution.
        :param norm_disp_type: optional normalization type pinned by the
            logic-tree branch ('AD' or 'MD'); ``None`` defers to the
            ``get_prob`` call (legacy default: 'AD').
        """
        super().__init__()
        self.n_sigma = float(n_sigma)
        if self.n_sigma <= 0.0:
            raise ValueError(f"n_sigma must be positive; got {self.n_sigma}")
        self.norm_disp_type = check_choice(
            type(self).__name__, "norm_disp_type", norm_disp_type,
            frozenset(["AD", "MD"]), canon=lambda v: str(v).upper())
        # 90th percentile of the unit-scale gamma(a=2.5); dividing the
        # regression level by this anchors gamma.ppf(0.9) at the regression.
        self._p90_factor = float(gamma.ppf(0.90, self._GAMMA_SHAPE))

    def get_prob(self, d, mag, r, norm_disp_type=None):
        """
        Model of Takao et al. (2013) for the probability of exceeding
        threshold values of secondary (distributed) displacement [m]

        :param d: Target displacement in meters (array of shape (n_displacements,))
        :param mag: Earthquake magnitude (scalar)
        :param r: Closest distance from the principal fault trace in km
            (scalar or array of shape (n_sites,))
        :param norm_disp_type: Normalization displacement type, "AD" or "MD".
        :returns: Probability of exceeding the given displacement
            (shape (n_sites, n_displacements))
        """
        # Fall back to constructor-pinned value, then legacy default
        if norm_disp_type is None:
            norm_disp_type = (self.norm_disp_type
                              if self.norm_disp_type is not None else "AD")
        if norm_disp_type not in self._COEFFS:
            raise ValueError(
                f"Invalid norm_disp_type '{norm_disp_type}'. "
                f"Accepted values are: {', '.join(self._COEFFS)}"
            )
        coeffs = self._COEFFS[norm_disp_type]

        d = np.atleast_1d(np.asarray(d, dtype=float))
        r = np.atleast_1d(np.asarray(r, dtype=float))
        n_sites = r.shape[0]

        log_mean = coeffs["log_intercept"] + coeffs["log_slope"] * mag
        sigma = coeffs["sigma"]

        # Truncation bounds of the PMD/PAD lognormal in log10 space
        lower = 10 ** (log_mean - self.n_sigma * sigma)
        upper = 10 ** (log_mean + self.n_sigma * sigma)
        logspace_vals = np.logspace(np.log10(lower), np.log10(upper),
                                    self._N_INTEGRATION)

        # Normalized pdf weights of the truncated lognormal (Eq. 11 pattern)
        pdf = norm.pdf(np.log10(logspace_vals), loc=log_mean, scale=sigma)
        pdf /= pdf.sum()

        # Marginalize P(DD > d | r, PMD_or_PAD) over the PMD/PAD distribution
        # (Eq. 12 applied to the distributed case, as noted below Eq. 17)
        prob_exceeding_d = np.zeros((n_sites, d.shape[0]))
        for norm_disp, weight in zip(logspace_vals, pdf):
            prob_exceeding_d += weight * self.get_prob_norm_displ(
                d / norm_disp, r, norm_disp_type)

        return prob_exceeding_d

    def get_prob_norm_displ(self, DD_norm, r, norm_disp_type="AD"):
        """
        Conditional exceedance probability of the normalized distributed
        displacement DD/PMD or DD/PAD at distance r (paper Eq. 17).

        :param DD_norm: Normalized displacement (array of shape (n_displacements,))
        :param r: Closest distance from the principal fault trace in km
            (scalar or array of shape (n_sites,))
        :param norm_disp_type: Normalization displacement type, "AD" or "MD".
        :returns: Exceedance probability (shape (n_sites, n_displacements))
        """
        if norm_disp_type not in self._COEFFS:
            raise ValueError(
                f"Invalid norm_disp_type '{norm_disp_type}'. "
                f"Accepted values are: {', '.join(self._COEFFS)}"
            )
        DD_norm = np.atleast_1d(np.asarray(DD_norm, dtype=float))
        r = np.atleast_1d(np.asarray(r, dtype=float))

        level90 = self._COEFFS[norm_disp_type]["c90"] * np.exp(self._DECAY * r)
        b = level90 / self._p90_factor  # Shape (n_sites,)

        return gamma.sf(DD_norm[np.newaxis, :], self._GAMMA_SHAPE,
                        loc=0, scale=b[:, np.newaxis])
