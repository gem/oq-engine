# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Module :mod:`openquake.fdha.primary_surf_displ.youngs2003` implements
the Youngs et al. (2003) model for the conditional probability of
exceeding principal surface fault displacement on normal faults.

Two classes are provided, corresponding to the two normalization
approaches described in the paper:

* :class:`Youngs2003PrimaryFD_AD` — displacement normalized by average
  displacement (D/AD), modelled with a **gamma distribution** whose
  parameters are functions of relative location x/L along the rupture.

* :class:`Youngs2003PrimaryFD_MD` — displacement normalized by maximum
  displacement (D/MD), modelled with a **beta distribution** whose
  parameters are functions of x/L.

Both classes convolve their respective profile distributions with
Wells and Coppersmith (1994) magnitude–displacement scaling relations
to produce the conditional probability of exceedance:

    P(D > d | m, x/L, Slip)

The convolution is performed via numerical integration over the
log-normal uncertainty in AD or MD (epsilon-based weighted sum).

The ``style`` parameter in :meth:`get_prob` selects which Wells &
Coppersmith (1994) regression subset to use:

- ``"all"``: WC94 coefficients for all faulting styles
- ``"normal"``: WC94 coefficients for normal faulting only

This choice represents **epistemic uncertainty** in the magnitude–
displacement scaling and can be assigned logic-tree weights.

PEP8-friendly aliases :meth:`Youngs2003PrimaryFD_AD.get_prob_d_ad` and
:meth:`Youngs2003PrimaryFD_MD.get_prob_d_md` call :meth:`get_prob` when
the normalization type should be explicit at the call site.

Profile distribution coefficients
---------------------------------
D/AD gamma distribution (Youngs et al., 2003, Appendix, Figure 7
lower panel; data from McCalpin and Slemmons, 1998, 11 normal
faulting earthquakes):

    a = exp(−0.193 + 1.628 × x/L)
    b = exp( 0.009 − 0.476 × x/L)

D/MD beta distribution (Youngs et al., 2003, Appendix, Figure 7
upper panel; data from McCalpin and Slemmons, 1998):

    a = exp(−0.705 + 1.138 × x/L)
    b = exp( 0.421 − 0.257 × x/L)

Both with 0 ≤ x/L ≤ 0.5 (symmetric about midpoint).

Wells & Coppersmith (1994) scaling coefficients
------------------------------------------------
log₁₀(D) = intercept + slope × M,  σ in log₁₀ units

AD, all styles:    intercept = −4.80, slope = 0.69, σ = 0.36
AD, normal:        intercept = −4.45, slope = 0.63, σ = 0.33
MD, all styles:    intercept = −5.46, slope = 0.82, σ = 0.42
MD, normal:        intercept = −5.90, slope = 0.89, σ = 0.38

References
----------
Youngs, R.R., et al. (2003). A methodology for probabilistic fault
    displacement hazard analysis (PFDHA). Earthquake Spectra, 19(1),
    191–219. doi:10.1193/1.1542891, Appendix pp. 25–26, Figures 7–8.

Wells, D.L. and Coppersmith, K.J. (1994). New empirical relationships
    among magnitude, rupture length, rupture width, rupture area, and
    surface displacement. Bulletin of the Seismological Society of
    America, 84, 974–1002, Table 2.
"""

import numpy as np
from scipy.stats import gamma, norm, beta
from openquake.fdha.primary_surf_displ.base import BasePrimarySurfDispl


# -----------------------------------------------------------------------
# Base class
# -----------------------------------------------------------------------
class _Youngs2003PrimaryFDBase(BasePrimarySurfDispl):
    """
    Base class for the Youngs et al. (2003) principal fault displacement
    model.  Subclasses define:

    * ``norm_disp_type``  — ``"AD"`` or ``"MD"``
    * ``_wc94_all``      — WC94 coefficients for all faulting styles
    * ``_wc94_normal``   — WC94 coefficients for normal faulting
    * ``_get_profile_params(x_l)`` — distribution parameters vs x/L
    * ``_compute_sf(y, alpha, beta_param)`` — survival function of the
      normalised displacement distribution
    """

    # Subclasses must override
    norm_disp_type = None
    _wc94_all = None
    _wc94_normal = None

    # Integration parameters
    # ±6 sigma truncation, step 0.1 in standard-normal space
    _n_eps = 6
    _dz = 0.1

    _accepted_styles = frozenset(["all", "normal"])

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _fold_x_l(x_l):
        """
        Fold x/L to [0, 0.5] by reflecting about the midpoint.

        The displacement profile is assumed symmetric about x/L = 0.5
        (Youngs et al., 2003, p. 9).  Values outside [0, 1] are first
        reduced modulo 1.
        """
        r = x_l - np.floor(x_l)
        return 0.5 - np.abs(r - 0.5)

    def _get_wc94_coeffs(self, style):
        """
        Return WC94 coefficient dict for the given faulting style.

        :param style:
            ``"all"`` or ``"normal"``
        :returns:
            dict with keys ``"intercept"``, ``"slope"``, ``"sigma"``
        """
        if style == "all":
            return self._wc94_all
        else:
            return self._wc94_normal

    def _get_profile_params(self, x_l):
        """
        Return (alpha, beta_param) arrays for the displacement profile
        distribution at the given folded x/L values.  Implemented by
        subclasses.
        """
        raise NotImplementedError

    def _compute_sf(self, y, alpha, beta_param):
        """
        Compute the survival function (1 − CDF) of the normalised
        displacement distribution for a single site.

        :param y:
            Normalised displacement values, shape ``(n_displacements, n_eps)``
        :param alpha:
            Shape parameter (scalar, for one site)
        :param beta_param:
            Scale/shape parameter (scalar, for one site)
        :returns:
            Survival function values, same shape as *y*
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_prob(self, d, x_l, mag, style="all"):
        """
        Conditional probability that principal fault displacement exceeds
        *d* metres, given magnitude *mag* and relative position *x/L*
        along the rupture.

        Computed by convolving the displacement profile distribution
        (D/AD or D/MD) with the Wells & Coppersmith (1994) log-normal
        distribution for AD or MD as a function of magnitude.

        Corresponds to P_kn(D > d | m, r, Slip) in Youngs et al. (2003),
        Equation 3, computed via numerical integration as shown in
        Figure 8.

        :param d:
            Target displacement(s) in metres.
            Scalar or array-like, shape ``(n_displacements,)``.
        :param x_l:
            Relative position along the rupture, x/L (0 = end, 0.5 =
            centre).  Values outside [0, 0.5] are folded by symmetry.
            Scalar or array-like, shape ``(n_sites,)``.
        :param mag:
            Earthquake moment magnitude (scalar).
        :param style:
            Wells & Coppersmith (1994) faulting style for magnitude–
            displacement scaling.  ``"all"`` (default) or ``"normal"``.
        :returns:
            Exceedance probability, shape ``(n_displacements, n_sites)``.
        """
        # --- Validate ---
        style_lower = (
            style.lower() if isinstance(style, str) else str(style).lower()
        )
        if style_lower not in self._accepted_styles:
            raise ValueError(
                "Invalid style '%s'. Accepted: %s"
                % (style, ", ".join(sorted(self._accepted_styles)))
            )
        if not np.isscalar(mag):
            raise ValueError("mag must be a scalar value")

        # --- Convert and fold ---
        d = np.atleast_1d(np.asarray(d, dtype=float))
        x_l = np.atleast_1d(np.asarray(x_l, dtype=float))
        x_l = self._fold_x_l(x_l)

        # --- WC94 scaling: log10(D) ~ N(mu, sigma^2) ---
        coeffs = self._get_wc94_coeffs(style_lower)
        mu = coeffs["intercept"] + coeffs["slope"] * mag
        sigma = coeffs["sigma"]

        # --- Profile distribution parameters ---
        alpha, beta_param = self._get_profile_params(x_l)

        # --- Epsilon grid for numerical integration ---
        epsilons = np.arange(
            -self._n_eps, self._n_eps + self._dz, self._dz
        )
        prob_eps = norm.pdf(epsilons)

        # --- WC94 displacement samples: D_norm(eps) ---
        z = np.power(10.0, mu + epsilons * sigma)  # (n_eps,)

        # --- Normalised displacement: d / D_norm ---
        y = d[:, np.newaxis] / z[np.newaxis, :]  # (n_disp, n_eps)

        # --- Integrate over epsilon for each site ---
        n_displacements = len(d)
        n_sites = len(x_l)
        prob_exceed = np.zeros((n_displacements, n_sites))

        for i_site in range(n_sites):
            sf = self._compute_sf(
                y, alpha[i_site], beta_param[i_site]
            )  # (n_disp, n_eps)
            prob_exceed[:, i_site] = np.dot(sf, prob_eps) * self._dz

        return prob_exceed

    def get_prob_normalized(self, d_norm, x_l):
        """
        Survival function of the normalised displacement profile
        distribution alone, without WC94 magnitude convolution.

        For the AD class this returns P(D/AD > d_norm | x/L) using the
        gamma distribution.  For the MD class it returns
        P(D/MD > d_norm | x/L) using the beta distribution.

        :param d_norm:
            Normalised displacement value(s).
            Scalar or array-like, broadcastable with *x_l*.
        :param x_l:
            Relative position along the rupture, x/L ∈ [0, 0.5].
            Scalar or array-like, broadcastable with *d_norm*.
        :returns:
            Exceedance probability, same shape as broadcast of
            *d_norm* and *x_l*.
        """
        d_norm = np.asarray(d_norm, dtype=float)
        x_l = np.asarray(x_l, dtype=float)

        tol = 1e-10
        if np.any((x_l < -tol) | (x_l > 0.5 + tol)):
            raise ValueError("x_l must be between 0 and 0.5")

        alpha, beta_param = self._get_profile_params(x_l)
        return self._compute_sf_broadcast(d_norm, alpha, beta_param)

    def _compute_sf_broadcast(self, d_norm, alpha, beta_param):
        """
        Broadcastable survival function for the normalised displacement.
        Implemented by subclasses.
        """
        raise NotImplementedError


# -----------------------------------------------------------------------
# AD class — gamma distribution
# -----------------------------------------------------------------------
class Youngs2003PrimaryFD_AD(_Youngs2003PrimaryFDBase):
    """
    Youngs et al. (2003) principal fault displacement model using
    **average displacement (AD)** normalization.

    The displacement profile D/AD is modelled with a **gamma
    distribution** whose parameters are functions of x/L:

        a = exp(−0.193 + 1.628 × x/L)
        b = exp( 0.009 − 0.476 × x/L)

    Source: Youngs et al. (2003), Appendix, "Coefficients for gamma
    distribution for D/AD shown on Figure 7"; McCalpin and Slemmons
    (1998), 11 normal faulting earthquakes.

    The AD scaling with magnitude uses Wells and Coppersmith (1994):

        log₁₀(AD) = intercept + slope × M

    Coefficients (WC94, Table 2A):
        All styles:    intercept = −4.80, slope = 0.69, σ = 0.36
        Normal:        intercept = −4.45, slope = 0.63, σ = 0.33
    """

    norm_disp_type = "AD"

    _wc94_all = {"intercept": -4.80, "slope": 0.69, "sigma": 0.36}
    _wc94_normal = {"intercept": -4.45, "slope": 0.63, "sigma": 0.33}

    # Gamma distribution profile coefficients
    # Youngs et al. (2003), Appendix, Figure 7 lower panel
    _profile_a_intercept = -0.193
    _profile_a_slope = 1.628
    _profile_b_intercept = 0.009
    _profile_b_slope = -0.476

    def _get_profile_params(self, x_l):
        """
        Gamma distribution parameters for D/AD as functions of x/L.

        :param x_l:
            Folded x/L array, shape ``(n_sites,)``.
        :returns:
            Tuple ``(alpha, beta_param)`` arrays, each shape
            ``(n_sites,)``.
        """
        alpha = np.exp(
            self._profile_a_intercept + self._profile_a_slope * x_l
        )
        beta_param = np.exp(
            self._profile_b_intercept + self._profile_b_slope * x_l
        )
        return alpha, beta_param

    def _compute_sf(self, y, alpha_site, beta_site):
        """
        Gamma survival function for D/AD.

        :param y:
            Normalised displacement, shape ``(n_disp, n_eps)``.
        :param alpha_site:
            Gamma shape parameter (scalar).
        :param beta_site:
            Gamma scale parameter (scalar).
        :returns:
            P(D/AD > y), shape ``(n_disp, n_eps)``.
        """
        return gamma.sf(y, alpha_site, loc=0, scale=beta_site)

    def _compute_sf_broadcast(self, d_norm, alpha, beta_param):
        """
        Broadcastable gamma survival function.

        :param d_norm:
            Normalised displacement value(s).
        :param alpha:
            Gamma shape parameter.
        :param beta_param:
            Gamma scale parameter.
        :returns:
            P(D/AD > d_norm), same shape as broadcast inputs.
        """
        return gamma.sf(d_norm, alpha, loc=0, scale=beta_param)

    def get_prob_d_ad(self, d, x_l, mag, style="all"):
        """
        Alias for :meth:`get_prob` for D/AD (average displacement).
        PEP8-friendly name when the normalization type should be explicit.
        """
        return self.get_prob(d, x_l, mag, style)


# -----------------------------------------------------------------------
# MD class — beta distribution
# -----------------------------------------------------------------------
class Youngs2003PrimaryFD_MD(_Youngs2003PrimaryFDBase):
    """
    Youngs et al. (2003) principal fault displacement model using
    **maximum displacement (MD)** normalization.

    The displacement profile D/MD is modelled with a **beta
    distribution** whose parameters are functions of x/L:

        a = exp(−0.705 + 1.138 × x/L)
        b = exp( 0.421 − 0.257 × x/L)

    Source: Youngs et al. (2003), Appendix, "Coefficients for beta
    distribution for D/MD shown on Figure 7"; McCalpin and Slemmons
    (1998), 11 normal faulting earthquakes.

    The MD scaling with magnitude uses Wells and Coppersmith (1994):

        log₁₀(MD) = intercept + slope × M

    Coefficients (WC94, Table 2B):
        All styles:    intercept = −5.46, slope = 0.82, σ = 0.42
        Normal:        intercept = −5.90, slope = 0.89, σ = 0.38

    Note: D/MD is bounded on [0, 1]. Values of D/MD > 1 are mapped to
    a CDF of 1.0 (probability of exceedance = 0). The CDF is also
    renormalized by CDF(1) to account for the truncation at D/MD = 1.
    """

    norm_disp_type = "MD"

    _wc94_all = {"intercept": -5.46, "slope": 0.82, "sigma": 0.42}
    _wc94_normal = {"intercept": -5.90, "slope": 0.89, "sigma": 0.38}

    # Beta distribution profile coefficients
    # Youngs et al. (2003), Appendix, Figure 7 upper panel
    _profile_a_intercept = -0.705
    _profile_a_slope = 1.138
    _profile_b_intercept = 0.421
    _profile_b_slope = -0.257

    def _get_profile_params(self, x_l):
        """
        Beta distribution parameters for D/MD as functions of x/L.

        :param x_l:
            Folded x/L array, shape ``(n_sites,)``.
        :returns:
            Tuple ``(alpha, beta_param)`` arrays, each shape
            ``(n_sites,)``.
        """
        alpha = np.exp(
            self._profile_a_intercept + self._profile_a_slope * x_l
        )
        beta_param = np.exp(
            self._profile_b_intercept + self._profile_b_slope * x_l
        )
        return alpha, beta_param

    def _compute_sf(self, y, alpha_site, beta_site):
        """
        Beta survival function for D/MD with truncation at 1.

        D/MD > 1 is physically impossible, so the exceedance probability
        is set to 0 for y >= 1.

        :param y:
            Normalised displacement, shape ``(n_disp, n_eps)``.
        :param alpha_site:
            Beta shape parameter *a* (scalar).
        :param beta_site:
            Beta shape parameter *b* (scalar).
        :returns:
            P(D/MD > y), shape ``(n_disp, n_eps)``.
        """
        sf = beta.sf(y, alpha_site, beta_site)
        return np.where(y >= 1.0, 0.0, sf)

    def _compute_sf_broadcast(self, d_norm, alpha, beta_param):
        """
        Broadcastable beta survival function with truncation at 1.

        :param d_norm:
            Normalised displacement value(s).
        :param alpha:
            Beta shape parameter *a*.
        :param beta_param:
            Beta shape parameter *b*.
        :returns:
            P(D/MD > d_norm), same shape as broadcast inputs.
        """
        sf = beta.sf(d_norm, alpha, beta_param)
        return np.where(d_norm >= 1.0, 0.0, sf)

    def get_prob_d_md(self, d, x_l, mag, style="all"):
        """
        Alias for :meth:`get_prob` for D/MD (maximum displacement).
        PEP8-friendly name when the normalization type should be explicit.
        """
        return self.get_prob(d, x_l, mag, style)