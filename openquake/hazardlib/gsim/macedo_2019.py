# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2025 GEM Foundation
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
Module exports: :class:`MacedoEtAl2019SInter`,
                :class:`MacedoEtAl2019SSlab`
"""

import numpy as np
from openquake.hazardlib import const
from openquake.hazardlib.imt import IA, PGA, SA
from openquake.hazardlib.gsim.base import GMPE, registry
from openquake.hazardlib.contexts import get_mean_stds


# The Macedo et al. (2019) GMM is period-independent, so all constants
# can be set as a standard dictionary
CONSTANTS = {
    "sinter": {
        # Global from Table 1
        "Global": {
            "c1": 0.85, "c2": -0.36, "c3": 0.53, "c4": 1.54,
            "c5": 0.17, "phi": 0.30, "tau_region": 0.04, "tau": 0.18,
        },
        # Regional coefficients for Interface events from Table 2
        "Japan": {
            "c1": 0.98, "c2": -0.38, "c3": 0.53, "c4": 1.54,
            "c5": 0.17, "phi": 0.3, "tau_region": 0.0, "tau": 0.16,
        },
        "Taiwan": {
            "c1": 0.75, "c2": -0.35, "c3": 0.53, "c4": 1.54,
            "c5": 0.17, "phi": 0.27, "tau_region": 0.0, "tau": 0.15,
        },
        "South America": {
            "c1": 0.95, "c2": -0.36, "c3": 0.53, "c4": 1.54,
            "c5": 0.17, "phi": 0.32, "tau_region": 0.0, "tau": 0.19,
        },
        "New Zealand": {
            "c1": 0.82, "c2": -0.36, "c3": 0.53, "c4": 1.54,
            "c5": 0.17, "phi": 0.28, "tau_region": 0.0, "tau": 0.17,
        },
    },
    "sslab": {
        # Global from Table 1
        "Global": {
            "c1": -0.74, "c2": -0.24, "c3": 0.66, "c4": 1.58,
            "c5": 0.14, "phi": 0.28, "tau_region": 0.03, "tau": 0.16
        },
        # Regional coefficients for Interface events from Table 3
        "Japan": {
            "c1": -0.22, "c2": -0.32, "c3": 0.66, "c4": 1.58,
            "c5": 0.14, "phi": 0.26, "tau_region": 0.0, "tau": 0.15,
        },
        "Taiwan": {
            "c1": -1.02, "c2": -0.20, "c3": 0.66, "c4": 1.58,
            "c5": 0.14, "phi": 0.29, "tau_region": 0.0, "tau": 0.17,
        },
        "South America": {
            "c1": -0.75, "c2": -0.24, "c3": 0.66, "c4": 1.58,
            "c5": 0.14, "phi": 0.30, "tau_region": 0.0, "tau": 0.14,
        },
        "New Zealand": {
            "c1": -0.84, "c2": -0.22, "c3": 0.66, "c4": 1.58,
            "c5": 0.14, "phi": 0.3, "tau_region": 0.0, "tau": 0.13,
        },
    }
}


def get_mean_conditional_arias_intensity(
    C: dict,
    ctx: np.recarray,
    mean_gms: np.recarray
) -> np.ndarray:
    """
    Returns the Arias Intensity (Equation 2)
    """
    return (C["c1"] + C["c2"] * np.log(ctx.vs30) +
            C["c3"] * ctx.mag + C["c4"] * mean_gms["PGA"] +
            C["c5"] * mean_gms["SA(1.0)"])


def get_stddev_component(
    C: dict,
    sig_ia_cond: float,
    sig_pga: float,
    sig_sa1: float,
    rho: float
) -> float:
    """
    Returns the standard deviation using Equation 6. Assume
    this can apply to all three components of stddev
    """
    return np.sqrt(
        sig_ia_cond ** 2.0 +
        (sig_pga ** 2.0) * (C["c4"] ** 2.0) +
        (sig_sa1 ** 2.0) * (C["c5"] ** 2.0) +
        (2.0 * (rho * sig_pga * sig_sa1) * C["c4"] * C["c5"]))


def get_standard_deviations(
    C: dict,
    kind: str,
    rho_pga_sa1: float,
    sigma_gms: np.recarray,
    tau_gms: np.recarray,
    phi_gms: np.recarray):
    """
    Returns sigma, tau and phi arrays for Arias Intensity
    """
    sigma_ia_cond = 0.36 if kind == "sinter" else 0.33
    # Gets the total standard deviation
    sigma = get_stddev_component(C, sigma_ia_cond, sigma_gms["PGA"],
                                 sigma_gms["SA(1.0)"], rho_pga_sa1)
    if np.any(tau_gms["PGA"] >= 0.0) or np.any(tau_gms["SA(1.0)"] > 0.0):
        # If provided by the conditioning ground motion, get the
        # between-event standard deviation
        tau = get_stddev_component(
            C,
            np.sqrt(C["tau"]**2 + C["tau_region"]**2),
            tau_gms["PGA"],
            tau_gms["SA(1.0)"],
            rho_pga_sa1)
    else:
        tau = 0.0
    if np.any(phi_gms["PGA"] >= 0.0) or np.any(phi_gms["SA(1.0)"] > 0.0):
        # If provided by the conditioning ground motion, get the
        # within-event standard deviation
        phi = get_stddev_component(
            C, C["phi"], phi_gms["PGA"], phi_gms["SA(1.0)"], rho_pga_sa1)
    else:
        phi = 0.0
    return sigma, tau, phi


class MacedoEtAl2019SInter(GMPE):
    """Implementation of a conditional GMPE of Macedo, Abrahamson & Bray (2019)
    for Arias Intensity, applied to subduction interface earthquakes. This
    requires characterisation of the PGA and SA(1.0), in addition to magnitude
    and vs30, for defining Arias intensity, and propagates uncertainty
    accordingly. The model includes specific regionalisations for "Global"
    application (default), "Japan", "Taiwan", "New Zealand" and
    "South America", as well as a user customisable coefficient of correlation
    between PGA and SA(1.0).

    Macedo J, Abrahamson N, Bray JD (2019) "Arias Intensity Conditional
    Scaling Ground-Motion Models for Subduction Zones", Bulletin of the
    Seismological Society of America, 109(4): 1343 - 1357

    """
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {IA, PGA, SA}
    # It is unclear to me if the CGMM is for a specific component of Arias
    # Intensity; however it's fit using NGA Subduction data, which assumes
    # PGA and SA are in terms of RotD50
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}
    REQUIRES_SITES_PARAMETERS = {"vs30", "backarc"}
    REQUIRES_RUPTURE_PARAMETERS = {"mag", }
    REQUIRES_DISTANCES = {'rrup'}

    # Subduction interface
    kind = "sinter"

    # Conditional upon PGA and Sa (1.0 s)
    REQUIRES_IMTS = {PGA(), SA(1.0)}

    # GMPE not verified against an independent implementation
    non_verified = True

    def __init__(self, region: str="Global", rho_pga_sa1: float=0.52,
                 **gmpe_dict):
        """
        Args:
            region: Region of application. Must be either "Global" (default)
                    or one of "Japan", "Taiwan", "South America", "New Zealand"
            rho_pga_sa1: Coefficient of correlation in total standard deviation
                         between PGA and Sa (1.0 s). In the original paper this
                         is taken as 0.52, based on the cross-correlation model
                         of Baker & Jayaram (2008). The coefficient could be
                         configured by the user if they wish to adopt an
                         alternative cross-correlation model
            gmpe_dict: dictionary specifying the underlying GMPE
        """
        # check that the region is one of those supported
        assert region in ("Global", "Japan", "Taiwan", "South America",
                          "New Zealand"),\
            "Region %s not recognised for Macedo et al (2019) GMPE" % region
        self.region = region
        self.rho_pga_sa1 = rho_pga_sa1

        # instantiate the underlying gmpe
        [(gmpe_name, kw)] = gmpe_dict.pop('gmpe').items()
        self.gmpe = registry[gmpe_name](**kw)

    def compute(self, ctx: np.recarray, imts: list, mean: np.ndarray,
                sig: np.ndarray, tau: np.ndarray, phi: np.ndarray):
        """
        Calculates the mean Arias Intensity and the standard deviations
        """
        # NB: there is a single IMT, Arias Intensity, i.e. imts == [IA]
        me, si, ta, ph = get_mean_stds(
            self.gmpe, ctx, self.REQUIRES_IMTS, return_dicts=True)
        C = CONSTANTS[self.kind][self.region]
        mean[0] = get_mean_conditional_arias_intensity(C, ctx, me)
        sigma_m, tau_m, phi_m = get_standard_deviations(
            C, self.kind, self.rho_pga_sa1, si, ta, ph)
        sig[0] += sigma_m
        tau[0] += tau_m
        phi[0] += phi_m


class MacedoEtAl2019SSlab(MacedoEtAl2019SInter):
    """
    Macedo et al. (2019) GMPE for application to subduction in-slab earthquakes
    """
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB
    kind = "sslab"
