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
Module :mod:`openquake.pfd.primary_surf_rup.mammarella2024` implements
Mammarella et al. (2024) primary surface-rupture probability (principal faulting)
as a first-class model.

References
----------
Mammarella, L., Visini, F., Boncio, P., Baize, S., Scotti, O., Beauval, C.,
Pace, B., & Thompson, S. (2024). Conditional probability of surface rupture:
a numerical approach for principal faulting. Earthquake Spectra.
https://doi.org/10.1177/87552930241293570

Notes
-----
- Vectorized re-implementation of the reference numerical (Monte Carlo style
  discrete-integration) procedure published with the paper.
- Probabilities are clipped to [0, 1].

API
---
Class: ``Mammarella2024PrimarySR``

get_prob(mag, MSR, HDD_str, dip_mu, dip_sigma, t_d, Zs_sigma, t_z,
         rake=None, style=None, seismothickness=None, Zs_mu=None) -> float | np.ndarray

Parameters
~~~~~~~~~~
- mag: float or array-like
    Moment magnitude Mw. Scalar returns scalar; vector returns ndarray of same length.
- rake: float, optional
    Rake angle in degrees. Style-of-faulting (SoF) is inferred via thresholds:
    normal if (-120, -60), reverse if (60, 120), strike-slip otherwise. Ignored if style is provided.
- style: str, optional
    Style-of-faulting string in {"normal", "reverse", "strike-slip"}. Used to set SoF if rake is not provided.
- seismothickness: float, optional
    Seismogenic thickness (km); used as Zs_mu if Zs_mu is not provided.
- Zs_mu: float, optional
    Mean seismogenic thickness (km). If omitted, falls back to seismothickness.
- MSR: int
    Magnitude scaling relation code in {0, 1, 2}. Required by Table 1.
- HDD_str: str
    Hypocentral depth distribution label. Must be one of keys in TAB2.
- dip_mu: float
    Mean dip (degrees).
- dip_sigma: float
    Standard deviation of dip (degrees).
- t_d: float
    Truncation in units of sigma for dip distribution.
- Zs_sigma: float
    Standard deviation of seismogenic thickness Zs (km).
- t_z: float
    Truncation in units of sigma for Zs distribution.

Returns
~~~~~~~
- float if input Mw is scalar, else np.ndarray with shape (n_mw,)

Behavior
~~~~~~~~
The algorithm integrates (discrete) joint weights over grids for LogW, dip, HDR,
Zseismo, and HDD ratio using truncated/normal/uniform priors, evaluating the
surface rupture condition as in the reference implementation. Broadcasting is used
to avoid large repeat/tile expansions. Final probability is the sum of joint
weights satisfying the condition.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import norm, truncnorm

from openquake.pfd.primary_surf_rup.base import BasePrimarySurfRup


# ---------------------------
# Constants and lookup tables
# ---------------------------

# Rupture-width magnitude scaling relation parameters by (MSR, SoF).
# columns: [MSR, SoF, a, b, W_sigma]
# MSR codes:
#   0 = Leonard (2014), interplate: m = a + 2.5*log10(W)
#       (a = 3.63 dip-slip, 3.88 strike-slip)
#   1 = Leonard (2014), stable continental region: same form
#       (a = 4.14 dip-slip, 4.22 strike-slip)
#   2 = Thingbaijam et al. (2017): log10(W) = a + b*m
#       (normal -0.829/0.323, reverse -1.669/0.435, strike-slip -0.543/0.261)
# SoF codes: 3 = normal, 4 = reverse, 5 = strike-slip.
TAB1 = np.array([
    [0, 3, 3.63, 2.5, 0.15],
    [0, 4, 3.63, 2.5, 0.15],
    [0, 5, 3.88, 2.5, 0.15],
    [1, 3, 4.14, 2.5, 0.15],
    [1, 4, 4.14, 2.5, 0.15],
    [1, 5, 4.22, 2.5, 0.15],
    [2, 3, -0.829, 0.323, 0.128],
    [2, 4, -1.669, 0.435, 0.087],
    [2, 5, -0.543, 0.261, 0.105],
], dtype=float)


# Table 2: HDD ratio parameters by label -> (mu, sigma)
TAB2 = {
    'ITA_N': (0.67, 0.21), 'GB_N': (0.64, 0.25), 'AGG_N': (0.65, 0.23),
    'ITA_R': (0.65, 0.24), 'TAI_R': (0.60, 0.25), 'JAP_R': (0.74, 0.20),
    'AGG_R': (0.66, 0.24), 'CA_S': (0.67, 0.21), 'NZ_S': (0.72, 0.21),
    'JAP_S': (0.79, 0.15), 'AGG_S': (0.70, 0.23),
}


# Discretization and truncation
class DISCRETIZATION:
    """Numerical discretization constants for the Mammarella et al. (2024) integration grid."""

    N_LOGW = 25
    N_DIP = 100
    HDR_GRID = np.arange(0.1, 1.0, 0.1)  # shape (9,)
    Z_STEP = 0.5  # km


# Truncations (multipliers of sigma)
T_W = 1.0  # for LogW


def _infer_sof_from_rake(rake_deg: float) -> int:
    """Map rake to SoF code consistent with user reference.

    Returns 3=normal, 4=reverse, 5=strike-slip.
    """
    if (-120.0 < rake_deg < -60.0):
        return 3
    if (60.0 < rake_deg < 120.0):
        return 4
    return 5


def _get_tab1_params(msr: int, sof: int) -> tuple[float, float, float]:
    mask = (TAB1[:, 0] == msr) & (TAB1[:, 1] == sof)
    idx = np.where(mask)[0]
    if idx.size == 0:
        # Fall back to first row (kept to mirror reference; validation covers msr)
        idx0 = 0
    else:
        idx0 = int(idx[0])
    a = float(TAB1[idx0, 2])
    b = float(TAB1[idx0, 3])
    w_sigma = float(TAB1[idx0, 4])
    return a, b, w_sigma


def _calc_LogW_mu_fn(msr: int, a: float, b: float):
    if msr in (0, 1):
        return lambda m: (m - a) / b
    if msr == 2:
        return lambda m: a + b * m
    raise ValueError("Invalid Magnitude Scaling Relation (MSR); expected 0, 1, or 2")


class Mammarella2024PrimarySR(BasePrimarySurfRup):
    """
    Probability of principal surface rupture after Mammarella et al. (2024).

    Parameters
    ----------
    mag : float or array-like
        Moment magnitude Mw. Scalar input returns a scalar, a vector returns an array.
    rake : float
        Rake in degrees. Style-of-faulting is inferred: normal (3) for (-120,-60),
        reverse (4) for (60,120), strike-slip (5) otherwise.
    seismothickness : float
        Seismogenic thickness Zs_mu (km).
    MSR : int
        Magnitude scaling relation code in {0, 1, 2}.
    HDD_str : str
        Hypocentral depth distribution label; must be a key of TAB2.
    dip_mu : float
        Mean dip (degrees).
    dip_sigma : float
        Standard deviation of dip (degrees).
    t_d : float
        Truncation factor for dip distribution (in sigma units).
    Zs_sigma : float
        Standard deviation of seismogenic thickness (km).
    t_z : float
        Truncation factor for Zs distribution (in sigma units).

    Returns
    -------
    float or np.ndarray
        Probability in [0, 1]. Scalar if mag is scalar, else shape (n_mw,).
    """

    def __init__(self, MSR=None, HDD_str=None, dip_mu=None, dip_sigma=None,
                 t_d=None, Zs_sigma=None, t_z=None, style=None,
                 seismothickness=None, Zs_mu=None):
        """
        Constructor-pinned model parameters, each defaulting to ``None``
        ("provide at call time instead"): the magnitude-scaling-relation
        index ``MSR`` (0, 1 or 2), the hypocentral-depth-distribution key
        ``HDD_str``, the dip prior ``dip_mu``/``dip_sigma`` with truncation
        ``t_d``, the seismogenic-thickness prior ``Zs_mu`` (alias
        ``seismothickness``)/``Zs_sigma`` with truncation ``t_z``, and the
        faulting ``style``. A pinned value is the fallback when the
        corresponding ``get_prob`` argument is not passed; an explicit
        call-time argument always wins (``dip_mu`` in particular normally
        comes from the rupture context unless pinned here).
        """
        super().__init__()
        if MSR is not None and int(MSR) not in (0, 1, 2):
            raise ValueError(
                f"{type(self).__name__}: MSR must be one of {{0, 1, 2}}; "
                f"got {MSR!r}")
        if HDD_str is not None and HDD_str not in TAB2:
            raise ValueError(
                f"{type(self).__name__}: invalid HDD_str {HDD_str!r}; "
                f"expected one of {sorted(TAB2.keys())}")
        self.MSR = None if MSR is None else int(MSR)
        self.HDD_str = HDD_str
        self.dip_mu = None if dip_mu is None else float(dip_mu)
        self.dip_sigma = None if dip_sigma is None else float(dip_sigma)
        self.t_d = None if t_d is None else float(t_d)
        self.Zs_sigma = None if Zs_sigma is None else float(Zs_sigma)
        self.t_z = None if t_z is None else float(t_z)
        self.style = style
        self.seismothickness = (None if seismothickness is None
                                else float(seismothickness))
        self.Zs_mu = None if Zs_mu is None else float(Zs_mu)

    def get_prob(self, mag, MSR=None, HDD_str=None,
                 dip_mu=None, dip_sigma=None, t_d=None, Zs_sigma=None,
                 t_z=None, rake=None, style=None, seismothickness=None,
                 Zs_mu=None):
        """Return the probability of principal surface rupture.

        See the class docstring for the full description of parameters
        (``mag``, ``MSR``, ``HDD_str``, dip and seismogenic-thickness
        distribution parameters) and the return value. Parameters left as
        ``None`` fall back to the values pinned at construction.
        """
        # Fall back to constructor-pinned values (call-time argument wins)
        MSR = self.MSR if MSR is None else MSR
        HDD_str = self.HDD_str if HDD_str is None else HDD_str
        dip_mu = self.dip_mu if dip_mu is None else dip_mu
        dip_sigma = self.dip_sigma if dip_sigma is None else dip_sigma
        t_d = self.t_d if t_d is None else t_d
        Zs_sigma = self.Zs_sigma if Zs_sigma is None else Zs_sigma
        t_z = self.t_z if t_z is None else t_z
        style = self.style if style is None else style
        seismothickness = (self.seismothickness if seismothickness is None
                           else seismothickness)
        Zs_mu = self.Zs_mu if Zs_mu is None else Zs_mu

        missing = [n for n, v in [("MSR", MSR), ("HDD_str", HDD_str),
                                  ("dip_mu", dip_mu), ("dip_sigma", dip_sigma),
                                  ("t_d", t_d), ("Zs_sigma", Zs_sigma),
                                  ("t_z", t_z)] if v is None]
        if missing:
            raise ValueError(
                f"{type(self).__name__}: missing required parameter(s) "
                f"{missing}; provide them in the logic-tree branch or at "
                f"call time")

        # Validate and prepare inputs
        msr = int(MSR)
        if msr not in (0, 1, 2):
            raise ValueError("MSR must be one of {0, 1, 2}")

        # Determine style of faulting code (SoF)
        if style is not None:
            style_str = str(style).strip().lower()
            if style_str in {"normal", "nm", "nmo"}:
                sof = 3
            elif style_str in {"reverse", "rv", "rvo", "thrust"}:
                sof = 4
            elif style_str in {"strike-slip", "ss"}:
                sof = 5
            else:
                raise ValueError(f"Invalid style '{style}'. Expected one of 'normal', 'reverse', 'strike-slip'")
        elif rake is not None:
            sof = _infer_sof_from_rake(float(rake))
        else:
            # Default to strike-slip if neither provided
            sof = 5

        if HDD_str not in TAB2:
            raise ValueError(f"Invalid HDD_str '{HDD_str}'. Expected one of {sorted(TAB2.keys())}")
        hdd_mu, hdd_sigma = map(float, TAB2[HDD_str])

        dip_mu = float(dip_mu)
        dip_sigma = float(dip_sigma)
        t_d = float(t_d)
        # Zs mean from explicit Zs_mu or fallback to seismothickness
        if Zs_mu is None and seismothickness is None:
            raise ValueError("Provide either Zs_mu or seismothickness for MammarellaEtAl2024PrimarySR")
        zs_mu = float(Zs_mu if Zs_mu is not None else seismothickness)
        zs_sigma = float(Zs_sigma)
        t_z = float(t_z)

        a, b, w_sigma = _get_tab1_params(msr, sof)
        logw_mu_fn = _calc_LogW_mu_fn(msr, a, b)

        # Grids
        # LogW ~ truncnorm centered at LogW_mu(m), +/- T_W * w_sigma
        # dip ~ normal truncated at +/- t_d * dip_sigma (discrete on N_DIP points)
        # HDR ~ uniform on [0.1, 0.9] stepping 0.1
        # Zseismo ~ normal truncated at +/- t_z * zs_sigma, step Z_STEP (km)
        r_hdr = DISCRETIZATION.HDR_GRID  # (n_r,)
        # HDD ratio discretization same support as HDR per reference (0.1..0.9)
        r_hdd = r_hdr

        m_arr = np.atleast_1d(np.asarray(mag, dtype=float))
        probs = np.empty(m_arr.shape, dtype=float)

        # Precompute dip grid and pdf weights (independent of Mw)
        dip_lower = dip_mu - t_d * dip_sigma
        dip_upper = dip_mu + t_d * dip_sigma
        dip_grid = np.linspace(dip_lower, dip_upper, DISCRETIZATION.N_DIP)
        dip_pdf = norm(loc=dip_mu, scale=dip_sigma).pdf(dip_grid)
        dip_w = dip_pdf / np.sum(dip_pdf) if np.any(dip_pdf) else np.zeros_like(dip_pdf)

        # Precompute HDR uniform weights
        hdr_w = np.full_like(r_hdr, 1.0 / r_hdr.size, dtype=float)
        # Precompute HDD ratio weights (discrete normalization)
        hdd_pdf = norm(loc=hdd_mu, scale=hdd_sigma).pdf(r_hdd)
        hdd_w = hdd_pdf / np.sum(hdd_pdf) if np.any(hdd_pdf) else np.zeros_like(hdd_pdf)

        # Zseismo grid depends on zs_mu, zs_sigma
        z_lower = zs_mu - t_z * zs_sigma
        z_upper = zs_mu + t_z * zs_sigma
        z_grid = np.arange(z_lower, z_upper + DISCRETIZATION.Z_STEP * 0.5, DISCRETIZATION.Z_STEP)
        z_pdf = norm(loc=zs_mu, scale=zs_sigma).pdf(z_grid)
        z_w = z_pdf / np.sum(z_pdf) if np.any(z_pdf) else np.zeros_like(z_pdf)

        # Iterate magnitudes (light loop; heavy vectorization inside)
        for i, m in enumerate(m_arr):
            # LogW discretization around mean
            logw_mu = float(logw_mu_fn(m))
            logw_min = logw_mu - T_W * w_sigma
            logw_max = logw_mu + T_W * w_sigma
            logw_grid = np.linspace(logw_min, logw_max, DISCRETIZATION.N_LOGW)
            a_trunc = (logw_min - logw_mu) / w_sigma  # -> -T_W
            b_trunc = (logw_max - logw_mu) / w_sigma  # -> +T_W
            # Use truncnorm.pdf over the linspace
            logw_pdf = truncnorm.pdf(logw_grid, a_trunc, b_trunc, loc=logw_mu, scale=w_sigma)
            logw_w = logw_pdf / np.sum(logw_pdf) if np.any(logw_pdf) else np.zeros_like(logw_pdf)
            W = np.power(10.0, logw_grid)  # km

            # Compute W_z = W * sin(dip)
            sin_dip = np.sin(np.deg2rad(dip_grid))  # (n_d,)
            W_z = W[:, None] * sin_dip[None, :]      # (n_w, n_d)

            # Combine W and dip weights -> outer product
            wd_w = logw_w[:, None] * dip_w[None, :]  # (n_w, n_d)

            # Introduce HDR: W_top = W_z * HDR
            w_hdr = wd_w[:, :, None] * hdr_w[None, None, :] # (n_w, n_d, n_r)

            # Tile Zseismo over (w,d,r) and combine weights
            Zs = z_grid[None, None, None, :]  # (1, 1, 1, n_z)
            w_zs = z_w[None, None, None, :]   # (1, 1, 1, n_z)

            # HDD ratio grid
            r_hdd_grid = r_hdd[None, None, None, None, :]  # (1,1,1,1,n_h)
            w_hdd = hdd_w[None, None, None, None, :]       # (1,1,1,1,n_h)

            # Broadcast shapes:
            # W_top: (n_w, n_d, n_r) -> (n_w, n_d, n_r, 1, 1)
            # Zs: (1, 1, 1, n_z)
            # r_hdd: (1, 1, 1, 1, n_h)
            # Expand Zs weights to 5D before multiplying
            w_all = w_hdr[:, :, :, None, None] * w_zs[:, :, :, :, None] * w_hdd  # (n_w,n_d,n_r,n_z,n_h)

            # Zhypo = Zseismo * HDD_ratio
            Z_hypo = Zs[:, :, :, :, None] * r_hdd_grid  # (1,1,1,n_z, n_h)

            # Reallocation rules (vectorized):
            # Start from NEW_HDR = HDR; NEW_Wz = W_z; but we have W_top already.
            # We need to apply the logic from reference code on the 5D broadcast.
            # Prepare baseline arrays via broadcasting
            W_z_b = W_z[:, :, None, None, None]         # (n_w,n_d,1,1,1)
            Zs_b = Zs                                   # (1,1,1,n_z)
            HDR_b = r_hdr[None, None, :, None, None]     # (1,1,n_r,1,1)

            # Conditions
            # Base condition (no r/h dims yet): (n_w, n_d, 1, n_z, 1)
            cond1_base = W_z_b >= Zs_b[:, :, :, :, None]
            # Broadcast to full shape including r and h
            n_w, n_d = W_z.shape
            n_r = r_hdr.size
            n_z = z_grid.size
            n_h = r_hdd.size
            cond1 = np.broadcast_to(cond1_base, (n_w, n_d, n_r, n_z, n_h))
            # Initialize NEW_HDR and NEW_Wz
            NEW_HDR = np.broadcast_to(HDR_b, (n_w, n_d, n_r, n_z, n_h)).astype(float)
            NEW_Wz = np.broadcast_to(W_z_b, (n_w, n_d, n_r, n_z, n_h)).astype(float)

            # If W_z >= Zseismo: NEW_Wz = Zseismo and NEW_HDR = HDD (CPSR.m idx1)
            NEW_Wz = np.where(cond1, Zs_b[:, :, :, :, None], NEW_Wz)
            NEW_HDR = np.where(cond1, np.broadcast_to(r_hdd_grid, (n_w, n_d, n_r, n_z, n_h)), NEW_HDR)

            # For remaining (not cond1): apply two more rules involving HDR and HDD
            # term_a = (Zseismo - Zhypo); term_b = (W_z - HDR*W_z)
            term_a = Zs_b[:, :, :, :, None] - Z_hypo
            term_b = W_z_b - (HDR_b * W_z_b)
            cond2 = (term_b >= term_a) & (~cond1)
            # NEW_HDR = 1 - ((Zseismo - Zhypo)/W_z)
            NEW_HDR = np.where(
                cond2,
                1.0 - (term_a / np.maximum(W_z_b, 1e-15)),
                NEW_HDR,
            )

            # cond3: (HDR*W_z >= Zhypo) & (~cond1)
            cond3 = ((HDR_b * W_z_b) >= Z_hypo) & (~cond1)
            # NEW_HDR = Zhypo / W_z
            NEW_HDR = np.where(
                cond3,
                (Z_hypo / np.maximum(W_z_b, 1e-15)),
                NEW_HDR,
            )

            NEW_Wtop = NEW_Wz * NEW_HDR

            # Surface rupture condition: NEW_Wtop >= Zhypo
            SRC = NEW_Wtop >= Z_hypo

            # Joint weights
            p_total = w_all
            # Sum over all cells satisfying SRC
            prob = float(np.sum(p_total[SRC]))
            probs[i] = np.clip(prob, 0.0, 1.0)

        return probs.item() if probs.size == 1 else probs


class MammarellaEtAl2024PrimarySR(Mammarella2024PrimarySR):
    """Alias of :class:`Mammarella2024PrimarySR` using the full author naming."""

    pass


