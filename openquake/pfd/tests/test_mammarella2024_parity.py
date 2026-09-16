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

# ruff: noqa: E402
"""
Unit tests: Mammarella2024 analytical parity

Analytical parity tests for Mammarella2024PrimarySR.

Purpose
-------
Provide an internal, reference-style computation of CPSR (same discretizations
and reallocation rules) to compare against the production implementation. This
acts as a fast, dependency-free backstop for numerical correctness and helps
catch subtle regressions when refactoring.

Notes
-----
- Tolerances allow for minor differences due to discrete normalization.
"""
import math
import numpy as np
import pytest


from openquake.pfd.primary_surf_rup.mammarella2024 import (
    Mammarella2024PrimarySR,
    TAB1,
    TAB2,
)


def _normal_pdf(x: np.ndarray, mu: float, sigma: float) -> np.ndarray:
    if sigma <= 0:
        out = np.zeros_like(x, dtype=float)
        if x.size:
            out[np.argmin(np.abs(x - mu))] = 1.0
        return out
    z = (x - mu) / sigma
    return np.exp(-0.5 * z * z) / (math.sqrt(2.0 * math.pi) * sigma)


def _get_tab1_params(msr: int, sof: int):
    mask = (TAB1[:, 0] == msr) & (TAB1[:, 1] == sof)
    idx = np.where(mask)[0]
    a, b, w_sigma = TAB1[idx[0], 2], TAB1[idx[0], 3], TAB1[idx[0], 4]
    return float(a), float(b), float(w_sigma)


def cpsr_reference(
    mag: float,
    MSR: int,
    style: str,
    HDD_str: str,
    dip_mu: float,
    dip_sigma: float,
    t_d: float,
    Zs_mu: float,
    Zs_sigma: float,
    t_z: float,
) -> float:
    # Map style to SoF code
    st = style.strip().lower()
    sof = {"normal": 3, "reverse": 4, "strike-slip": 5, "strike slip": 5}[st]
    a, b, W_sigma = _get_tab1_params(MSR, sof)
    hdd_mu, hdd_sigma = TAB2[HDD_str]

    # LogW grid ±1σ, 25 points, truncated normal weights normalized by sum
    if MSR in (0, 1):
        logw_mu = (mag - a) / b
    else:
        logw_mu = a + b * mag
    eps_w = 1.0 * W_sigma
    logw_grid = np.linspace(logw_mu - eps_w, logw_mu + eps_w, 25)
    mask = (logw_grid >= (logw_mu - eps_w)) & (logw_grid <= (logw_mu + eps_w))
    p_logw = np.zeros_like(logw_grid, dtype=float)
    p_logw[mask] = _normal_pdf(logw_grid[mask], logw_mu, W_sigma)
    s = p_logw.sum()
    if s > 0:
        p_logw /= s
    else:
        p_logw[:] = 1.0 / p_logw.size
    W = np.power(10.0, logw_grid)  # (Nw,)

    # Dip grid: MATLAB (mu - eps):(mu + eps) with unit step, but emulate our 100-point linspace for parity
    eps_dip = t_d * dip_sigma
    dip_grid = np.linspace(dip_mu - eps_dip, dip_mu + eps_dip, 100, dtype=float)
    if dip_grid.size == 0:
        dip_grid = np.array([dip_mu], dtype=float)
    p_dip = _normal_pdf(dip_grid, dip_mu, dip_sigma)
    p_dip /= p_dip.sum()

    # HDR uniform
    hdr_grid = np.arange(0.1, 1.0, 0.1)
    p_hdr = np.full_like(hdr_grid, 1.0 / hdr_grid.size, dtype=float)

    # Zs grid 0.5 km steps (same as model)
    eps_z = t_z * Zs_sigma
    zs_grid = np.arange(Zs_mu - eps_z, Zs_mu + eps_z + 0.25, 0.5, dtype=float)
    if zs_grid.size == 0:
        zs_grid = np.array([Zs_mu], dtype=float)
    p_zs = _normal_pdf(zs_grid, Zs_mu, Zs_sigma)
    p_zs /= p_zs.sum()

    # HDD ratio weights on r2 grid
    r2_grid = np.arange(0.1, 1.0, 0.1)
    p_hdd = _normal_pdf(r2_grid, hdd_mu, hdd_sigma)
    p_hdd /= p_hdd.sum()

    # Broadcast to 5D
    sin_dip = np.sin(np.deg2rad(dip_grid))  # (Nd,)
    Wz_2D = W[:, None] * sin_dip[None, :]   # (Nw,Nd)
    Wz = Wz_2D[:, :, None, None, None]
    Wtop = (Wz_2D[:, :, None] * hdr_grid[None, None, :])[:, :, :, None, None]
    Zs_b = zs_grid[None, None, None, :, None]
    Zhypo = Zs_b * r2_grid[None, None, None, None, :]

    Nw, Nd = Wz_2D.shape
    Nr = hdr_grid.size
    Nz = zs_grid.size
    Nrr = r2_grid.size

    Wz_full = np.broadcast_to(Wz, (Nw, Nd, Nr, Nz, Nrr))
    Wtop_full = np.broadcast_to(Wtop, (Nw, Nd, Nr, Nz, Nrr))
    Zs_full = np.broadcast_to(Zs_b, (Nw, Nd, Nr, Nz, Nrr))
    Zhypo_full = np.broadcast_to(Zhypo, (Nw, Nd, Nr, Nz, Nrr))

    # Reallocation
    NEW_HDR = np.broadcast_to(hdr_grid[None, None, :, None, None], (Nw, Nd, Nr, Nz, Nrr)).copy()
    NEW_Wz = Wz_full.copy()

    idx1 = Wz_full >= Zs_full
    NEW_Wz[idx1] = Zs_full[idx1]
    NEW_HDR[idx1] = np.broadcast_to(r2_grid[None, None, None, None, :], NEW_HDR.shape)[idx1]

    idx2 = (Wz_full - Wtop_full) >= (Zs_full - Zhypo_full)
    idx2 &= ~idx1
    Wz_safe = np.where(Wz_full != 0.0, Wz_full, np.finfo(float).eps)
    NEW_HDR[idx2] = (1.0 - ((Zs_full - Zhypo_full) / Wz_safe))[idx2]

    idx3 = (Wtop_full >= Zhypo_full) & (~idx1)
    NEW_HDR[idx3] = (Zhypo_full / Wz_safe)[idx3]

    NEW_Wtop = NEW_Wz * NEW_HDR
    SRC = NEW_Wtop >= Zhypo_full

    # Weights
    weights = (
        p_logw[:, None, None, None, None]
        * p_dip[None, :, None, None, None]
        * p_hdr[None, None, :, None, None]
        * p_zs[None, None, None, :, None]
        * p_hdd[None, None, None, None, :]
    )

    return float(np.sum(weights[SRC]))


@pytest.mark.parametrize(
    "Mw,MSR,style,HDD",
    [
        (6.5, 0, "reverse", "AGG_R"),
        (7.0, 1, "normal", "AGG_N"),
        (7.5, 2, "strike-slip", "AGG_S"),
    ],
)

def test_parity_against_cpsr_like(Mw, MSR, style, HDD):
    model = Mammarella2024PrimarySR()
    # Common parameters similar to authors' typical ranges
    params = dict(
        dip_mu=45.0,
        dip_sigma=10.0,
        t_d=2.0,
        Zs_mu=12.0,
        Zs_sigma=2.0,
        t_z=2.0,
    )
    p_ref = cpsr_reference(
        mag=Mw,
        MSR=MSR,
        style=style,
        HDD_str=HDD,
        dip_mu=params["dip_mu"],
        dip_sigma=params["dip_sigma"],
        t_d=params["t_d"],
        Zs_mu=params["Zs_mu"],
        Zs_sigma=params["Zs_sigma"],
        t_z=params["t_z"],
    )
    p_model = model.get_prob(
        mag=Mw,
        MSR=MSR,
        HDD_str=HDD,
        dip_mu=params["dip_mu"],
        dip_sigma=params["dip_sigma"],
        t_d=params["t_d"],
        Zs_sigma=params["Zs_sigma"],
        t_z=params["t_z"],
        style=style,
        seismothickness=params["Zs_mu"],
    )
    # Allow tolerance since reference approximates MATLAB truncnorm and uses equal shapes
    assert p_model == pytest.approx(p_ref, rel=2e-2, abs=2e-2)


@pytest.mark.parametrize("msr,cls_name,style", [
    (0, "Leonard2014_Interplate", "reverse"),
    (1, "Leonard2014_SCR", "normal"),
    (2, "Thingbaijam2017", "strike-slip"),
])
def test_width_model_instance_matches_msr(msr, cls_name, style):
    """A hazardlib width scalerel (instance or registered name) reproduces
    the TAB1/MSR width rows exactly (PR-2 of the oq-engine integration
    plan: consumers take scalerel instances, resolved via mag_scale_rel,
    instead of integer MSR codes)."""
    from openquake.hazardlib import valid

    model = Mammarella2024PrimarySR()
    params = dict(
        HDD_str="AGG_R",
        dip_mu=45.0,
        dip_sigma=10.0,
        t_d=2.0,
        Zs_mu=12.0,
        Zs_sigma=2.0,
        t_z=2.0,
    )
    p_msr = model.get_prob(mag=6.5, MSR=msr, style=style, **params)
    p_instance = model.get_prob(
        mag=6.5, width_model=valid.mag_scale_rel(cls_name),
        style=style, **params)
    p_name = model.get_prob(
        mag=6.5, width_model=cls_name, style=style, **params)
    assert p_instance == pytest.approx(p_msr, rel=1e-12, abs=1e-12)
    assert p_name == pytest.approx(p_msr, rel=1e-12, abs=1e-12)
