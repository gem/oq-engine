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
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""
Module :mod:`openquake.pfd.secondary_surf_displ.moss2022` implements
Moss et al. (2022) distributed (secondary) surface fault displacement model.

References
----------
Moss, R., Thompson, S., Kuo, C.-H., Younesi, K., and Baumont, D. (2022).
Reverse Fault PFDHA. Report GIRS-2022-05 (Revised 1/17/2024).
DOI: 10.34948/N3F595
"""
import numpy as np
from scipy import stats
from openquake.pfd.primary_surf_displ.base import BaseSecondarySurfDispl
from openquake.pfd.primary_surf_displ.moss2022 import SCALING, GAMMA_GLOBAL

# ── Table 5.7: median (50th pct) d/MD envelope ──────────────────────────
# Equation 5.8:  d/MD = c · exp(d · r_km)
ENVELOPE_50 = {
    'simple':  {'fw': {'c': 0.245, 'd': -0.18},
                'hw': {'c': 0.245, 'd': -0.34}},
    'complex': {'fw': {'c': 0.245, 'd': -0.09},
                'hw': {'c': 0.245, 'd': -0.015}},
}

# ── Table 5.8: 85th percentile d/MD envelope ────────────────────────────
# Equation 5.8:  d/MD = c · exp(d · r_km)
ENVELOPE_85 = {
    'simple':  {'fw': {'c': 0.68, 'd': -0.13},
                'hw': {'c': 0.43, 'd': -0.40}},
    'complex': {'fw': {'c': 0.68, 'd': -0.13},
                'hw': {'c': 0.43, 'd': -0.012}},
}


class Moss2022SecondaryFD(BaseSecondarySurfDispl):
    """
    Distributed (secondary) displacement exceedance model for reverse faults.

    Two methods:

    * ``'gamma'`` - Uses the global gamma distribution (Eqs 4.2–4.3) for the
      d/MD ratio, with its mean rescaled by the distance-dependent envelope
      (Eq. 5.8). Integrated over MD(M) uncertainty the same way as the
      primary FD model.
    * ``'envelope'`` - Deterministic: assumes d_secondary = MD × envelope(r),
      then integrates over MD uncertainty to obtain P(d > d₀).

    Distance ``r`` is received in **km** (adapter convention, matching
    ``ctx.r``).  Envelope Eq. 5.8 operates in km directly.

    Reference: GIRS-2022-05, Sections 5.3–5.4. DOI: 10.34948/N3F595

    Model contract: DISPLACEMENT_DEFINITION = "distributed",
    DISPLACEMENT_COMPONENT = "vertical" -- distributed reverse-fault
    displacement normalised by the principal MD/AD, from vertical-offset
    measurements (GIRS-2022-05 Section 5). No APPLICABILITY_RANGE is
    declared: the report documents its envelopes per Section 5 without a
    single distance limit comparable to the Valentini et al. (2025)
    Table 4 entries (report-specific validity).
    """

    DISPLACEMENT_DEFINITION = "distributed"
    DISPLACEMENT_COMPONENT = "vertical"

    def get_prob(self, d, mag, r, rx,
                 version="MD", completeness="complete",
                 sigma_type="recommended", faulting="simple",
                 percentile="85", method="gamma", gamma_a=None, **kwargs):
        """
        Parameters
        ----------
        d : array-like
            Displacement thresholds in metres.
        mag : float
            Moment magnitude (scalar).
        r : float or array-like
            Distance from principal fault in **km**.
        rx : float or array-like
            Signed cross-fault distance in km (positive = HW).
        version : str
            ``'MD'`` or ``'AD'``.
        completeness : str
            ``'complete'``, ``'incomplete'`` (MD only), or ``'all'``.
        sigma_type : str
            ``'recommended'`` or ``'regression'``.
        faulting : str
            ``'simple'`` or ``'complex'``.
        percentile : str
            ``'50'`` or ``'85'`` for the d/MD envelope.
        method : str
            ``'gamma'`` or ``'envelope'``.
        gamma_a : float, optional
            Override the global gamma shape parameter (defaults from
            ``GAMMA_GLOBAL``). Only affects the ``gamma`` method.

        Returns
        -------
        numpy.ndarray
            Shape (n_sites, n_displacements).
        """
        if "dataset" in kwargs:
            completeness = kwargs.pop("dataset")
        if "use_revised_sigma" in kwargs:
            sigma_type = (
                "recommended" if kwargs.pop("use_revised_sigma") else "regression"
            )
        if "gamma_a" in kwargs:
            gamma_a = kwargs.pop("gamma_a")
        # Legacy no-op hint (site side is determined by ``rx``).
        kwargs.pop("hw_fw", None)
        if kwargs:
            unexpected = ", ".join(sorted(kwargs))
            raise TypeError(
                f"Moss2022SecondaryFD.get_prob() got unexpected keyword arguments: {unexpected}"
            )

        ver = version.upper()
        if ver not in ('AD', 'MD'):
            raise ValueError(f"Invalid version '{version}'. Accept: AD, MD")

        comp = completeness.lower()
        valid_comp = (('complete', 'incomplete', 'all') if ver == 'MD'
                      else ('complete', 'all'))
        if comp not in valid_comp:
            raise ValueError(
                f"Invalid completeness '{completeness}' for '{ver}'. "
                f"Accept: {valid_comp}")

        st = sigma_type.lower()
        if st not in ('recommended', 'regression'):
            raise ValueError(
                f"Invalid sigma_type '{sigma_type}'. "
                "Accept: recommended, regression")

        fault_l = faulting.lower()
        if fault_l not in ('simple', 'complex'):
            raise ValueError(
                f"Invalid faulting '{faulting}'. Accept: simple, complex")

        pct = str(percentile)
        if pct not in ('50', '85'):
            raise ValueError(
                f"Invalid percentile '{percentile}'. Accept: 50, 85")
        env_table = ENVELOPE_50 if pct == '50' else ENVELOPE_85

        method_l = method.lower()
        if method_l not in ('gamma', 'envelope'):
            raise ValueError(
                f"Invalid method '{method}'. Accept: gamma, envelope")

        d_arr = np.atleast_1d(np.asarray(d, dtype=float))
        r_arr = np.atleast_1d(np.asarray(r, dtype=float))
        rx_arr = np.atleast_1d(np.asarray(rx, dtype=float))
        hw_mask = rx_arr >= 0

        n_sites = r_arr.shape[0]

        # ── Compute d/MD envelope at each site (r already in km) ──
        env = np.empty(n_sites, dtype=float)
        for side_label, mask in [('hw', hw_mask), ('fw', ~hw_mask)]:
            if not np.any(mask):
                continue
            ec = env_table[fault_l][side_label]
            env[mask] = ec['c'] * np.exp(ec['d'] * r_arr[mask])

        # ── Magnitude scaling (same Table 4.4 as primary FD) ──
        sc = SCALING[ver][comp]
        mu = sc['a'] + sc['b'] * mag
        sigma = (sc['s_rec']
                 if (st == 'recommended' and sc['s_rec'] is not None)
                 else sc['s'])

        if method_l == 'gamma':
            return self._gamma_method(
                d_arr, env, mu, sigma, ver, n_sites, gamma_shape=gamma_a)
        return self._envelope_method(d_arr, env, mu, sigma, n_sites)

    # ─────────────────────────────────────────────────────────────────────
    def _gamma_method(self, d_arr, env, mu, sigma, ver, n_sites, gamma_shape=None):
        """
        Gamma-distribution approach.

        At distance r the d/MD ratio follows gamma(shape, scale) where
        shape = global shape and scale = envelope(r) / shape, giving
        mean = envelope(r).  Integrated over log-normal MD uncertainty.
        """
        g = GAMMA_GLOBAL[ver]
        shape = float(gamma_shape) if gamma_shape is not None else g['a']
        # scale so that gamma mean = envelope value at each site
        site_scale = np.maximum(env / shape, 1e-30)

        dz = 0.1
        eps = np.arange(-6.0, 6.0 + dz / 2, dz)
        z = 10 ** (mu + eps * sigma)        # MD samples  (E,)
        p_eps = stats.norm.pdf(eps)          # weights     (E,)

        # y[e, disp, site] = d[disp] / MD[e]
        y = d_arr[None, :, None] / z[:, None, None]   # (E, D, 1)
        ss = site_scale[None, None, :]                 # (1, 1, S)

        cdf_mat = stats.gamma.cdf(y, a=shape, scale=ss)

        if ver == 'MD':
            c1 = stats.gamma.cdf(1.0, a=shape, scale=ss)
            cdf_mat = np.where(y > 1.0, 1.0, cdf_mat / c1)

        cdf = np.tensordot(p_eps, cdf_mat, axes=(0, 0)) * dz  # (D, S)
        prob = np.clip(1.0 - cdf, 0.0, 1.0)

        # Return (n_sites, n_disp)
        return prob.T.squeeze() if prob.ndim == 2 else prob.squeeze()

    # ─────────────────────────────────────────────────────────────────────
    def _envelope_method(self, d_arr, env, mu, sigma, n_sites):
        """
        Deterministic envelope: P(d > d₀) = P(MD · env(r) > d₀).

        Since log₁₀(MD) ~ N(μ, σ²), this reduces to a normal survival
        function on log₁₀(d₀ / env).
        """
        safe_env = np.maximum(env, 1e-30)
        # required_log_md[site, disp] = log10(d₀ / envelope)
        required_log_md = np.log10(
            d_arr[None, :] / safe_env[:, None])         # (S, D)
        prob = 1.0 - stats.norm.cdf(
            (required_log_md - mu) / sigma)
        return np.clip(prob, 0.0, 1.0).squeeze()
