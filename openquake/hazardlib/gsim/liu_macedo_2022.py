# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2023 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.
"""
Module exports: :class:`LiuMacedo2022SInter`,
                :class:`LiuMacedo2022SSlab`,
                :class:`LiuMacedo2022M1SSlab`,
                :class:`LiuMacedo2022M1SInter`,
                :class:`LiuMacedo2022M2SSlab`,
                :class:`LiuMacedo2022M2SInter`,

"""

import numpy as np
from typing import Dict, List, Tuple
from openquake.hazardlib import const
from scipy.constants import g as gravity_acc
from openquake.hazardlib.imt import IMT, PGA, CAV, SA

from openquake.hazardlib.gsim.conditional_gmpe import ConditionalGMPE
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable

CONSTANTS = {
    "delta_Z": 1.0,
    "mag_ref": 6.0,
    "Vlin": 400,
    "k2": -1.311,
    "b": -1.186,
    "c": 1.88,
    "n": 1.18,
    "delta_M": 0.1,
}


def get_median_conditional_cav(
    C: Dict, ctx: np.recarray, imt: IMT, median_gms: np.recarray
) -> np.ndarray:
    """Returns the same CAV using eq 6 of pg 621 of Liu and Macedo (2022)"""
    assert str(imt) == "CAV"
    cav_est = (
        C["a0"]
        + C["a1"] * np.log(median_gms["PGA"])
        + C["a2"] * ctx.mag
        + C["a3"] * np.log(ctx.vs30)
        + C["a4"] * np.log(median_gms["SA(1.0)"])
    )
    return cav_est


def get_stddev_component(
    C: Dict, sig_cav_cond: float, sig_pga: float, sig_sa1: float, rho: float
) -> float:
    """Returns the standard deviation using Equation 6. Assume
    this can apply to all three components of stddev
    """
    return np.sqrt(
        sig_cav_cond**2.0
        + (sig_pga**2.0) * (C["a1"] ** 2.0)
        + (sig_sa1**2.0) * (C["a4"] ** 2.0)
        + (2.0 * (rho * sig_pga * sig_sa1 * C["a1"] * C["a4"]))
    )


def get_standard_deviations(
    C: Dict,
    kind: str,
    rho_pga_sa1: float,
    sigma_gms: np.recarray,
    tau_gms: np.recarray,
    phi_gms: np.recarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    # C: Dict, sigma_gms: np.recarray, tau_gms: np.recarray, phi_gms: np.recarray
    """Returns the total standard deviation and, if specified
    by the input ground motions, the between and within-event
    standard deviations
    """
    sigma_cav_cond = np.sqrt(C["phi"] ** 2 + C["tau"] ** 2)
    # Gets the total standard deviation
    sigma = get_stddev_component(
        C, sigma_cav_cond, sigma_gms["PGA"], sigma_gms["SA(1.0)"], rho_pga_sa1
    )
    if np.any(tau_gms["PGA"] >= 0.0) or np.any(tau_gms["SA(1.0)"] > 0.0):
        # If provided by the conditioning ground motion, get the
        # between-event standard deviation
        tau = get_stddev_component(
            C,
            C["tau"],
            tau_gms["PGA"],
            tau_gms["SA(1.0)"],
            rho_pga_sa1,
        )
    else:
        tau = 0.0
    if np.any(phi_gms["PGA"] >= 0.0) or np.any(phi_gms["SA(1.0)"] > 0.0):
        # If provided by the conditioning ground motion, get the
        # within-event standard deviation
        phi = get_stddev_component(
            C, C["phi"], phi_gms["PGA"], phi_gms["SA(1.0)"], rho_pga_sa1
        )
    else:
        phi = 0.0
    return sigma, tau, phi


class LiuMacedo2022SSlab(ConditionalGMPE):
    """Implementation of a conditional GMPE of Liu & Macedo (2022)
    for CAV, applied to subduction earthquakes.

    Liu C, Macedo J,  (2022) "New
    conditional, scenario-based, and non-conditional cumulative absolute velocity models
    for subduction tectonic settings", Bulletin of the
    Seismological Society of America, 38(1): 615 - 647

    """

    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {CAV, PGA, SA}

    # It is unclear to me if the CGMM is for a specific component of CAV
    # ; however it's fit using NGA-West2 data, which assumes
    # PGA are in terms of RotD50??XXX
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT,
    }

    REQUIRES_SITES_PARAMETERS = {"vs30"}
    REQUIRES_RUPTURE_PARAMETERS = {"mag"}
    REQUIRES_DISTANCES = set()

    # Conditional upon PGA and SA(1.0)
    REQUIRES_IMTS = {"PGA", "SA(1.0)"}
    kind = "sslab"

    # GMPE not verified against an independent implementation
    non_verified = True

    def __init__(self, rho_pga_sa1: float = 0.58, **kwargs):
        """
        Args:
            region: Region of application. CGMM is "Global" where it can be
            conditioned on a regional model
        """
        super().__init__(**kwargs)
        self.rho_pga_sa1 = rho_pga_sa1

    def compute(
        self,
        ctx: np.recarray,
        imts: List,
        median: np.ndarray,
        sig: np.ndarray,
        tau: np.ndarray,
        phi: np.ndarray,
    ):
        """Calculates the median CAV and the standard deviations"""
        median_gms, sigma_gms, tau_gms, phi_gms = self.get_conditioning_ground_motions(
            ctx
        )
        C = self.COEFFS[CAV()]
        conv_fact = np.log(1 / gravity_acc)
        for m, imt in enumerate(imts):
            print(imt)
            median[m] = get_median_conditional_cav(C, ctx, imt, median_gms) + conv_fact
            sigma_m, tau_m, phi_m = get_standard_deviations(
                C, self.kind, self.rho_pga_sa1, sigma_gms, tau_gms, phi_gms
            )
            sig[m] += sigma_m
            tau[m] += tau_m
            phi[m] += phi_m

    COEFFS = CoeffsTable(
        table="""\
    IMT                        a0                       a1                      a2                     a3                      a4                       tau                    phi
    cav          1.49527569785495	     0.634034503034039	     0.486760820059385	   -0.225785263110743       0.122811017817412	      0.172041167030289      0.253118162497303
    """,
    )


class LiuMacedo2022SInter(LiuMacedo2022SSlab):
    """Liu et al. (2022) GMPE for application to
    subduction in-slab earthquakes
    """

    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE
    kind = "sinter"

    COEFFS = CoeffsTable(
        table="""\
    IMT                       a0                        a1                      a2                     a3                      a4                       tau                    phi
    cav         2.37255633488692	     0.621298074524136	     0.406927200515368	   -0.273516501682321       0.141113076318144	      0.139819931314861      0.241389447657334
    """,
    )


def _lh(x, x0, a, b0, b1, delta):
    return a + b0 * (x - x0) + (b1 - b0) * delta * np.log(1 + np.exp((x - x0) / delta))


def _mag_m1(C, ctx):
    f_mag = _lh(
        ctx.mag,
        C["mag_B"],
        C["theta4"] * (C["mag_B"] - CONSTANTS["mag_ref"]),
        C["theta4"],
        C["theta5"],
        CONSTANTS["delta_M"],
    )
    return f_mag


def _geom_m1(C, ctx):
    f_geom = (C["theta2"] + C["theta3"] * ctx.mag) * (
        np.log(ctx.rrup + 10 ** (C["theta_nft1"] + C["theta_nft2"] * (ctx.mag - 6)))
    )
    return f_geom


def _depth_m1(C, ctx):
    return _lh(
        ctx.ztor,
        C["Z_B"] + C["delta_Z_B"],
        C["theta9"] * (C["Z_B"] + C["delta_Z_B"] - C["Z_ref"]),
        C["theta9"],
        C["theta10"],
        CONSTANTS["delta_Z"],
    )


def _attn_m1(C, ctx):
    return C["theta6"] * ctx.rrup


def get_median_values_M1(kind, C, ctx, a1100=None):

    if isinstance(a1100, np.ndarray):
        # Site model defined
        temp_vs30 = ctx.vs30
    else:
        # Default site
        temp_vs30 = 1100.0 * np.ones(len(ctx))

    f_mag = _mag_m1(C, ctx)
    f_geom = _geom_m1(C, ctx)
    f_depth = _depth_m1(C, ctx)
    f_site = _get_shallow_site_response_term(
        C, temp_vs30, a1100, C["theta7"], CONSTANTS["k2"]
    )
    f_attn = _attn_m1(C, ctx)

    median = C["theta1"] + f_mag + f_geom + f_depth + f_attn + f_site
    return median


def get_median_values_M2(kind, C, ctx, a1100=None):
    Fs = 0
    if kind == "slab":
        Fs = 1

    if isinstance(a1100, np.ndarray):
        # Site model defined
        temp_vs30 = ctx.vs30
    else:
        # Default site
        temp_vs30 = 1100.0 * np.ones(len(ctx))

    f_mag = C["a5"] * (ctx.mag - C["mag_B"]) + C["a13"] * (10 - ctx.mag) ** 2
    f_mag[ctx.mag <= C["mag_B"]] = (
        C["a4"] * (ctx.mag[ctx.mag <= C["mag_B"]] - C["mag_B"])
        + C["a13"] * (10 - ctx.mag[ctx.mag <= C["mag_B"]]) ** 2
    )

    f_site = _get_shallow_site_response_term(
        C, temp_vs30, a1100, C["a12"], CONSTANTS["b"]
    )

    f_ztor = np.full_like(f_site, C["a11"] * (100 - 60)) * Fs
    f_ztor[ctx.ztor <= 100] = C["a11"] * (ctx.ztor[ctx.ztor <= 100] - 60) * Fs

    median = (
        C["a1"]
        + C["a4"] * (7.5 - 7.8) * Fs
        + (C["a2"] + C["a14"] * Fs + C["a3"] * (ctx.mag - 7.8))
        * np.log(ctx.rrup + C["C4"] * np.exp(C["a9"] * ctx.mag - 6 * C["a9"]))
        + C["a6"] * ctx.rrup
        + C["a10"] * Fs
        + f_mag
        + f_ztor
        + f_site
    )
    return median


def _get_shallow_site_response_term(C, vs30, cav_rock, o_const_1, o_const_2):
    """
    Returns the shallow site response term defined in equations 17, 18 and
    19
    """
    vs_mod = vs30 / CONSTANTS["Vlin"]
    f_site_g = (o_const_1 + o_const_2 * CONSTANTS["n"]) * np.log(vs_mod)
    idx = vs30 < CONSTANTS["Vlin"]
    if np.any(idx):
        f_site_g[idx] = (
            o_const_1 * np.log(vs_mod[idx])
            - o_const_2 * np.log(cav_rock[idx] + CONSTANTS["c"])
            + o_const_2
            * np.log(cav_rock[idx] + CONSTANTS["c"] * (vs_mod[idx] ** CONSTANTS["n"]))
        )

    return f_site_g


class LiuMacedo2022M1SSlab(GMPE):

    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {CAV}
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    #: Supported standard deviation types are inter-event, intra-event
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT,
    }

    REQUIRES_SITES_PARAMETERS = {"vs30"}
    REQUIRES_RUPTURE_PARAMETERS = {"mag", "ztor"}
    REQUIRES_DISTANCES = {"rrup"}
    kind = "slab"

    def compute(self, ctx: np.recarray, imts, median, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        C_CAV = self.COEFFS[CAV()]
        # Get median and standard deviation of CAV on rock (Vs30 1100 m/s^2)
        cav1100 = np.exp(get_median_values_M1(self.kind, C_CAV, ctx))

        # Get median and standard deviation
        for m, imt in enumerate(imts):
            conv_fact = 0
            conv_fact2 = 0
            C = self.COEFFS[imt]

            # Get median and standard deviations for IMT
            median[m] = (
                get_median_values_M1(self.kind, C, ctx, cav1100)
                + conv_fact
                + conv_fact2
            )
            tau[m] = C["tau"]
            phi[m] = C["phi"]
            sig[m] = np.sqrt(C["tau"] ** 2 + C["phi"] ** 2)

    COEFFS = CoeffsTable(
        table="""\
    IMT      theta1            theta2           theta3          theta4        theta5          theta6           theta7        theta9   theta10        theta_nft1   theta_nft2   Z_ref  Z_B       delta_Z_B    mag_B       tau    phi
    cav         2.8      -1.244868758      0.028024475     1.563987271   0.747139186    -0.001999881      0.939084461   0.003009148         0       0.844321045  0.196390595      50   80     -0.00771224      7.6      0.32   0.57
    """,
    )


class LiuMacedo2022M1SInter(LiuMacedo2022M1SSlab):
    """Liu et al. (2022) GMPE for application to
    subduction in-slab earthquakes
    """

    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE
    kind = "sinter"
    COEFFS = CoeffsTable(
        table="""\
    IMT             theta1             theta2           theta3          theta4        theta5          theta6           theta7        theta9   theta10        theta_nft1   theta_nft2   Z_ref  Z_B       delta_Z_B    mag_B       tau    phi
    cav        1.963526293       -1.254378973      0.028024475     1.420617599   0.747139186    -0.001999881      0.939084461   0.025040951      0          0.844321045  0.196390595      15   30     0.105201075      7.9      0.32   0.57

    """,
    )


class LiuMacedo2022M2SSlab(GMPE):

    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {CAV}
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    #: Supported standard deviation types are inter-event, intra-event
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT,
    }

    REQUIRES_SITES_PARAMETERS = {"vs30"}
    REQUIRES_RUPTURE_PARAMETERS = {"mag", "ztor"}
    REQUIRES_DISTANCES = {"rrup"}
    kind = "slab"

    def compute(self, ctx: np.recarray, imts, median, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """

        C_CAV = self.COEFFS[CAV()]
        cav1100 = np.exp(get_median_values_M2(self.kind, C_CAV, ctx))

        # Get median and standard deviation
        for m, imt in enumerate(imts):
            conv_fact = 0
            conv_fact2 = 0

            C = self.COEFFS[imt]
            # Get median and standard deviations for IMT
            median[m] = (
                get_median_values_M2(self.kind, C, ctx, cav1100)
                + conv_fact
                + conv_fact2
            )
            tau[m] = C["tau"]
            phi[m] = C["phi"]
            sig[m] = np.sqrt(C["tau"] ** 2 + C["phi"] ** 2)

    COEFFS = CoeffsTable(
        table="""\
    IMT                a1                   a2                   a3                    a4                   a5                          a6                       a9                        a10                       a11                      a12                       a13                      a14       C4    mag_B                      tau                     phi
    cav 5.683074991752335   -1.166611231113404  0.02654321348219018    0.8693449770167709   0.5886472382336402      -0.0016714118261620763      0.08546533256839378         1.1388432991377258      0.005418097804478372        0.766775749186763      -0.07090743422359473     -0.11661127502264568       10      7.5      0.38099561590236064      0.5968277386018089
    """,
    )


class LiuMacedo2022M2SInter(LiuMacedo2022M2SSlab):
    """Liu et al. (2022) GMPE for application to
    subduction in-slab earthquakes
    """

    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE
    kind = "sinter"
    COEFFS = CoeffsTable(
        table="""\
    IMT                a1                   a2                   a3                    a4                   a5                          a6                       a9                        a10                       a11                      a12                       a13                      a14       C4    mag_B                      tau                     phi
    cav 5.683074991752335   -1.166611231113404  0.02654321348219018    0.8693449770167709   0.5886472382336402      -0.0016714118261620763      0.08546533256839378         1.1388432991377258      0.005418097804478372        0.766775749186763      -0.07090743422359473     -0.11661127502264568       10      7.8      0.38099561590236064      0.5968277386018089
    """,
    )
