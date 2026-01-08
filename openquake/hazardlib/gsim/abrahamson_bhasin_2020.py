# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2025-2026 GEM Foundation
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
Module exports: :class:`AbrahamsonBhasin2020`,
                :class:`AbrahamsonBhasin2020PGA`,
                :class:`AbrahamsonBhasin2020SA1`,
"""

import numpy as np
from openquake.hazardlib import const
from openquake.hazardlib.imt import SA, PGV, PGA 
from openquake.hazardlib.gsim.base import GMPE, registry
from openquake.hazardlib.contexts import get_mean_stds

not_verified = True

# Abrahamson & Bhasin (2020) conditional PGV (horizontal component)
# coefficients (Table 3.2)
AB20_COEFFS = {
    "general": {
        "a1": 5.39, "a2": 0.799, "a3": 0.654, "a4": 0.479, "a5": -0.062,
        "a6": -0.359, "a7": -0.134, "a8": 0.023, "phi": 0.29, "tau": 0.16,
        "sigma": 0.33
    },
    "pga-based": {
        "a1": 4.77, "a2": 0.738, "a3": 0.484, "a4": 0.275, "a5": -0.036,
        "a6": -0.332, "a7": -0.44, "a8": 0.0, "phi_1": 0.32, "phi_2": 0.42,
        "tau_1": 0.12, "tau_2": 0.26, "sigma_1": 0.34, "sigma_2": 0.49,
    },
    "sa1_based": {
        "a1": 4.80, "a2": 0.82, "a3": 0.55, "a4": 0.27, "a5": 0.054,
        "a6": -0.382, "a7": -0.21, "a8": 0.0, "phi_1": 0.28, "phi_2": 0.38,
        "tau_1": 0.12, "tau_2": 0.17, "sigma_1": 0.30, "sigma_2": 0.42,
    }
}


M1 = 5.0
M2 = 7.0


def _get_tref(ctx):
    """
    Magnitude-dependent conditioning period Tref (Table 3.1).
    """
    mval = float(np.asarray(ctx.mag).flat[0])

    bins  = np.array([3.5, 4.5, 5.5, 6.5, 7.5, 8.5], dtype=float)
    trefs = np.array([0.20, 0.28, 0.40, 0.95, 1.40, 2.80], dtype=float)

    idx = np.searchsorted(bins, mval, side="left")
    return float(trefs[min(idx, len(trefs) - 1)])


def _get_trilinear_magnitude_term(ctx: np.recarray, C: dict):
    """Magnitude-dependent slope term f1(M) of ln(PSA(tref)). 
    (see eq. 3.8)

    """
    f1 = np.empty_like(ctx.mag, dtype=float)
    m1 = (ctx.mag < 5.0)
    m2 = (ctx.mag >= 5.0) & (ctx.mag <= 7.5)
    m3 = ~(m1 | m2)
    f1[m1] = C["a2"]
    f1[m2] = C["a2"] + (C["a3"] - C["a2"]) * (ctx.mag[m2] - 5.0) / 2.5
    f1[m3] = C["a3"]
    return f1


def _tri_linear_stdev_term(M: np.ndarray, stdev1: float, stdev2: float):
    """Tri-linear interpolation between used in pga- and sa1-based
    models. 
    (see eq. 3.9)

    """
    out = np.empty_like(M, dtype=float)
    m_lo = (M < M1)
    m_md = (M >= M1) & (M <= M2)
    m_hi = (M > M2)
    out[m_lo] = stdev1
    out[m_md] = stdev1 + (stdev2 - stdev1) * (M[m_md] - M1) / (M2 - M1)
    out[m_hi] = stdev2
    return out


def get_mean_conditional_pgv(
    C: dict, 
    ctx: np.recarray, 
    mean_gms: dict, 
    imt_key: str
    ):
  
    lnY = mean_gms[imt_key]
    f1  = _get_trilinear_magnitude_term(ctx, C)
    return (
        C["a1"]
        + f1 * lnY
        + C["a4"] * (ctx.mag - 6.0)
        + C["a5"] * (8.5 - ctx.mag) ** 2
        + C["a6"] * np.log(ctx.rrup + 5.0 * np.exp(0.4 * (ctx.mag - 6.0)))
        + (C["a7"] + C["a8"] * (ctx.mag - 5.0)) * np.log(ctx.vs30 / 425.0)
    )


def get_standard_deviations(
    C: dict, 
    ctx: np.recarray,
    sigma_gms: dict, 
    tau_gms: dict, 
    phi_gms: dict,
    imt_key: str):

    f1 = _get_trilinear_magnitude_term(ctx, C)
    sigma_cond = sigma_gms[imt_key]  
    if "sigma" in C:  # general model
        sigma_pgv = np.full_like(sigma_cond, C["sigma"], dtype=float)
        tau_pgv   = np.full_like(sigma_cond, C["tau"],   dtype=float)
        phi_pgv   = np.full_like(sigma_cond, C["phi"],   dtype=float)
    else:  # fixed-IMT variants
        M = np.asarray(ctx.mag, dtype=float)
        sigma_pgv = _tri_linear_stdev_term(M, C["sigma_1"], C["sigma_2"])
        tau_pgv   = _tri_linear_stdev_term(M, C["tau_1"],   C["tau_2"])
        phi_pgv   = _tri_linear_stdev_term(M, C["phi_1"],   C["phi_2"])

    tau_cond = tau_gms.get(imt_key)
    phi_cond = phi_gms.get(imt_key)

    sigma = np.sqrt((f1 * sigma_cond) ** 2 + sigma_pgv ** 2)
    tau   = np.sqrt((f1 * tau_cond)   ** 2 + tau_pgv   ** 2) if (tau_cond is not None and np.size(tau_cond) > 0) else tau_pgv
    phi   = np.sqrt((f1 * phi_cond)   ** 2 + phi_pgv   ** 2) if (phi_cond is not None and np.size(phi_cond) > 0) else phi_pgv
    return sigma, tau, phi


class AbrahamsonBhasin2020(GMPE):
    """Implementation of a conditional GMPE of Abrahamson & Bhasin (2020)
    for Peak Ground Velocity (PGV) applicable to active shallow crustal 
    earthquakes. This requires characterisation of the SA at reference 
    period (which is magnitude-dependent), in addition to magnitude and vs30, 
    to define PGV and propagate the associated uncertainty. It also includes 
    single-period SA variants (e.g., PGA and SA(1.0)), designed for use with 
    seismic design maps that typically provide SA values at only a few spectral 
    periods.
    
    Abrahamson N, Bhasin S (2020) "Conditional Ground-Motion Model for Peak Ground
    Velocity for Active Crustal Regions.", PEER Report 2020/05, Pacific Earthquake 
    Engineering Research Center Headquarters, University of California at Berkeley.
    (October 2010)

    """
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGV}
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT
    }
    REQUIRES_SITES_PARAMETERS = {"vs30"}
    REQUIRES_RUPTURE_PARAMETERS = {"mag"}
    REQUIRES_DISTANCES = {"rrup"}

    non_verified = True

    def __init__(self, kind: str = "general", **gmpe_dict):

        if kind not in AB20_COEFFS:
            raise ValueError(f"Unknown AB20 kind '{kind}'. Choose from {list(AB20_COEFFS)}")
        [(gmpe_name, kw)] = gmpe_dict.pop("gmpe").items()
        self.gmpe = registry[gmpe_name](**kw)
        self.c = AB20_COEFFS[kind]
        self.kind = kind
        self.last_tref = None

        for attr in ("REQUIRES_SITES_PARAMETERS", "REQUIRES_RUPTURE_PARAMETERS", "REQUIRES_DISTANCES"):
            setattr(self, attr,
                    set(getattr(self, attr, ())) | set(getattr(self.gmpe, attr, ())))

    def compute(self, ctx: np.recarray, imts: list,
                mean: np.ndarray, sig: np.ndarray,
                tau: np.ndarray, phi: np.ndarray):

        non_pgv = [(i, imt) for i, imt in enumerate(imts)
                   if str(imt) != "PGV"]

        if non_pgv:
            non_pgv_imts = [imt for _, imt in non_pgv]
            base_mean, base_sig, base_tau, base_phi = get_mean_stds(
                self.gmpe, ctx, non_pgv_imts
            )
            for j, (i, _) in enumerate(non_pgv):
                mean[i] = base_mean[j]
                sig[i]  = base_sig[j]
                tau[i]  = base_tau[j]
                phi[i]  = base_phi[j]

        for i, imt in enumerate(imts):
            if str(imt) != "PGV":
                continue

            if self.kind == "general":
                tref = _get_tref(ctx)
                self.last_tref = tref
                cond_imt = SA(tref)
            elif self.kind == "pga-based":
                cond_imt = PGA()
            else:
                cond_imt = SA(1.0)

            key = str(cond_imt)

            mean_gms, sigma_gms, tau_gms, phi_gms = get_mean_stds(
                self.gmpe, ctx, {cond_imt}, return_dicts=True
            )

            lnpgv = get_mean_conditional_pgv(self.c, ctx, mean_gms, key)
            sigma_pgv, tau_pgv, phi_pgv = get_standard_deviations(
                self.c, ctx,
                sigma_gms=sigma_gms,
                tau_gms=tau_gms,
                phi_gms=phi_gms,
                imt_key=key,
            )

            mean[i] = lnpgv
            sig[i]  = sigma_pgv
            tau[i]  = tau_pgv
            phi[i]  = phi_pgv


class AbrahamsonBhasin2020PGA(AbrahamsonBhasin2020):
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGV}

    def __init__(self, **gmpe_dict):
        super().__init__(kind="pga-based", **gmpe_dict)


class AbrahamsonBhasin2020SA1(AbrahamsonBhasin2020):
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGV}

    def __init__(self, **gmpe_dict):
        super().__init__(kind="sa1_based", **gmpe_dict)
