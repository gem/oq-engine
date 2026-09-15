# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024-2026 Yen-Shin Chen, OGS
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Moss and Ross (2011) primary surface fault displacement model.
"""

import numpy as np
from scipy.stats import beta
from scipy.stats import gamma
from scipy.stats import norm
from scipy.stats import weibull_min

from openquake.pfd.params import check_choice
from openquake.pfd.primary_surf_displ.base import BasePrimarySurfDispl


class MossRoss2011PrimaryFD(BasePrimarySurfDispl):
    """
    Model of Moss and Ross (2011) for exceedance probabilities of primary
    surface fault displacement thresholds.

    The implementation restores the historical model that was removed during
    the May 2025 vectorization cleanup, while returning the current standard
    shape: ``(n_displacements, n_sites)``.

    The conditional AD/MD log10-normal distribution is integrated over a
    truncation range of ``mean ± n_sigma·sigma`` (in log10 space), consistent
    with the other primary FD models (Takao 2013, Youngs 2003). The truncation
    level ``n_sigma`` defaults to 3 and may be overridden from the logic tree
    via ``[MossRoss2011PrimaryFD] n_sigma = <value>``.

    Model contract: DISPLACEMENT_DEFINITION = "principal",
    DISPLACEMENT_COMPONENT = "vertical" -- Moss & Ross (2011, BSSA 101)
    regress principal reverse-fault displacement measured as vertical
    separation (their D/AD, D/MD data are vertical offsets on the principal
    scarp); component per the reverse-fault convention summarised in
    Valentini et al. (2025, Rev. Geophys.) Table 4.
    """

    DISPLACEMENT_DEFINITION = "principal"
    DISPLACEMENT_COMPONENT = "vertical"

    _ACCEPTED_DISP_TYPES = frozenset(["AD", "MD"])
    _N_INTEGRATION = 1000

    def __init__(self, n_sigma=3.0, norm_disp_type=None):
        """
        :param n_sigma: truncation half-width of the AD/MD distribution.
        :param norm_disp_type: optional normalization type pinned by the
            logic-tree branch ('AD' or 'MD'); ``None`` defers to the
            ``get_prob`` call.
        """
        super().__init__()
        self.n_sigma = float(n_sigma)
        if self.n_sigma <= 0.0:
            raise ValueError(f"n_sigma must be positive; got {self.n_sigma}")
        self.norm_disp_type = check_choice(
            type(self).__name__, "norm_disp_type", norm_disp_type,
            frozenset(["AD", "MD"]), canon=lambda v: str(v).upper())

    def _truncation_grid(self, mean, sigma):
        """
        Log-spaced integration grid spanning ``mean ± n_sigma·sigma`` in
        log10 space (the truncation range of the AD/MD distribution).
        """
        lower = 10 ** (mean - self.n_sigma * sigma)
        upper = 10 ** (mean + self.n_sigma * sigma)
        return np.logspace(np.log10(lower), np.log10(upper), self._N_INTEGRATION)

    def get_prob(self, d, X_L_ratio, mag, norm_disp_type=None):
        """
        Return probability of exceeding primary displacement threshold(s).

        :param d:
            Target displacement in meters, scalar or ``(n_displacements,)``.
        :param X_L_ratio:
            Along-strike position ratio, scalar or ``(n_sites,)``.
        :param mag:
            Earthquake magnitude, scalar.
        :param norm_disp_type:
            Normalization displacement type: ``"AD"`` or ``"MD"``.
        :returns:
            Exceedance probabilities with shape ``(n_displacements, n_sites)``.
        """
        if norm_disp_type is None:
            norm_disp_type = self.norm_disp_type
        if norm_disp_type is None:
            raise ValueError(
                f"{type(self).__name__}: norm_disp_type must be given either "
                f"in the logic-tree branch or at call time")
        if norm_disp_type not in self._ACCEPTED_DISP_TYPES:
            raise ValueError(
                f"Invalid displacement type '{norm_disp_type}'. Accepted values are: "
                f"{', '.join(sorted(self._ACCEPTED_DISP_TYPES))}"
            )
        if not np.isscalar(mag):
            raise ValueError("mag must be a scalar value")

        d_arr = np.atleast_1d(d).astype(float)
        x_l = np.atleast_1d(X_L_ratio).astype(float)

        if np.any(d_arr <= 0.0):
            raise ValueError("d must be positive")

        r = x_l - np.floor(x_l)
        x_fold = 0.5 - np.abs(r - 0.5)

        # Build the integration support over the AD/MD truncation range so that
        # the convolution support and the normalization denominator (in
        # ``_normalized_log10_weights``) span the same ``mean ± n_sigma·sigma``.
        if norm_disp_type == "AD":
            mean = -2.2192 + 0.3244 * mag
            sigma = 0.17
        else:
            mean = -3.1971 + 0.5102 * mag
            sigma = 0.31

        integration_displacements = self._truncation_grid(mean, sigma)
        norm_ratio = d_arr[:, np.newaxis] / integration_displacements[np.newaxis, :]

        if norm_disp_type == "AD":
            mag_weights = self.get_prob_avg_displacement(integration_displacements, mag)
            out = np.zeros((d_arr.size, x_fold.size), dtype=float)
            for idx, x_l_site in enumerate(x_fold):
                out[:, idx] = np.dot(
                    self.get_prob_D_AD(norm_ratio, x_l_site),
                    mag_weights,
                )
            return out

        mag_weights = self.get_prob_max_displacement(integration_displacements, mag)
        out = np.zeros((d_arr.size, x_fold.size), dtype=float)
        for idx, x_l_site in enumerate(x_fold):
            out[:, idx] = np.dot(
                self.get_prob_D_MD(norm_ratio, x_l_site),
                mag_weights,
            )
        return out

    def get_prob_D_AD(self, D_AD, X_L_ratio, variant="gamma"):
        """
        Probability of exceeding normalized displacement D/AD.

        Moss and Ross (2011) present two source-defined distributions on
        D/AD (their Eqs. 6 and 7); both pass goodness-of-fit equally well.

        :param variant: ``"gamma"`` (Eq. 7, default; matches the historical
            implementation) or ``"weibull"`` (Eq. 6).
        """
        self._check_folded_x_l(X_L_ratio)
        v = str(variant).strip().lower()
        if v == "gamma":
            # Moss and Ross (2011) Eq. 7.
            a = np.exp(-30.4 * X_L_ratio**3 + 19.9 * X_L_ratio**2
                       - 2.29 * X_L_ratio + 0.574)
            b = np.exp(50.3 * X_L_ratio**3 - 34.6 * X_L_ratio**2
                       + 6.6 * X_L_ratio - 1.05)
            return gamma.sf(D_AD, a, loc=0, scale=b)
        if v == "weibull":
            # Moss and Ross (2011) Eq. 6.
            k = np.exp(-31.8 * X_L_ratio**3 + 21.5 * X_L_ratio**2
                       - 3.32 * X_L_ratio + 0.431)
            lam = np.exp(17.2 * X_L_ratio**3 - 12.8 * X_L_ratio**2
                         + 3.99 * X_L_ratio - 0.38)
            return weibull_min.sf(D_AD, c=k, scale=lam)
        raise ValueError(
            f"Unknown variant '{variant}'. Accepted: 'gamma', 'weibull'.")

    def get_prob_avg_displacement(self, target_ad, mag):
        """
        Normalized probability mass for average displacement in meters.
        """
        avg_displacement = -2.2192 + 0.3244 * mag
        sigma = 0.17
        return self._normalized_log10_weights(target_ad, avg_displacement, sigma)

    def get_prob_D_MD(self, D_MD, X_L_ratio):
        """
        Probability of exceeding normalized displacement D/MD.

        The beta shape parameters are the linear regressions published in
        Moss and Ross (2011): alpha = 0.901(x/L) + 0.713 and
        beta = -1.86(x/L) + 1.74 (unlike the D/AD gamma/Weibull parameters,
        these are not exponentiated). Both remain positive over the folded
        domain 0 <= x/L <= 0.5.
        """
        self._check_folded_x_l(X_L_ratio)

        a = 0.901 * X_L_ratio + 0.713
        b = -1.86 * X_L_ratio + 1.74
        return beta.sf(D_MD, a, b)

    def get_prob_max_displacement(self, target_md, mag):
        """
        Normalized probability mass for maximum displacement in meters.
        """
        max_displacement = -3.1971 + 0.5102 * mag
        sigma = 0.31
        return self._normalized_log10_weights(target_md, max_displacement, sigma)

    @staticmethod
    def _check_folded_x_l(X_L_ratio):
        tol = 1e-12
        if np.any((X_L_ratio < -tol) | (X_L_ratio > 0.5 + tol)):
            raise ValueError("X_L_ratio must be folded between 0 and 0.5")

    def _normalized_log10_weights(self, target_displacement, mean, sigma):
        target_displacement = np.atleast_1d(target_displacement).astype(float)
        if np.any(target_displacement <= 0.0):
            raise ValueError("target displacement values must be positive")

        prob = norm.pdf(np.log10(target_displacement), loc=mean, scale=sigma)
        grid_prob = norm.pdf(
            np.log10(self._truncation_grid(mean, sigma)),
            loc=mean,
            scale=sigma,
        )
        return prob / np.sum(grid_prob)
