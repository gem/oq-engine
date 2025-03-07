# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2023 GEM Foundation
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
Module exports: :class:`MacedoEtAl2021`,
"""

import numpy as np

from typing import Dict, List, Tuple
from openquake.hazardlib import const
from openquake.hazardlib.imt import IMT, PGA, CAV
from openquake.hazardlib.gsim.conditional_gmpe import ConditionalGMPE

CONSTANTS = {
    # From Table 1
    "c1": 1.79,
    "c2": np.sqrt(0.4541),
    "c3": 0.57,
    "c4": -0.47,
    "c5": -0.0026,
    "c6": 0.17,
    "phi": 0.26,
    "tau": 0.17,
}


def get_mean_conditional_cav(
    C: Dict, ctx: np.recarray, imt: IMT, mean_gms: np.recarray
) -> np.ndarray:
    """Returns the CAV using eq 12 of pg 163 of Macedo et al. (2021)"""
    assert str(imt) == "CAV"

    # compute FHW
    FHW = np.zeros_like(ctx.rx)
    FHW[ctx.rx > 0] = 1

    # compute t1
    t1 = np.full_like(ctx.rx, 60 / 45)
    t1[ctx.dip > 30] = (90 - ctx.dip[ctx.dip > 30]) / 45

    # compute t2
    t2 = np.full_like(ctx.rx, 1 + 0.2 * (ctx.mag - 6.5) - 0.8
                      * (ctx.mag - 6.5) ** 2)
    t2[ctx.mag >= 6.5] = 1
    t2[ctx.mag < 5.5] = 0

    # compute t5
    t5 = np.zeros_like(ctx.rx)
    t5[ctx.rjb < 15] = 1 - ctx.rjb[ctx.rjb < 15] / 15

    return (
        C["c1"]
        + C["c2"] * np.log(mean_gms["PGA"])
        + C["c3"] * ctx.mag
        + C["c4"] * np.log(ctx.vs30)
        + C["c5"] * np.log(ctx.rrup)
        + C["c6"] * FHW * t1 * t2 * t5
    )


def get_stddev_component(
    C: Dict,
    sig_ia_cond: float,
    sig_pga: float,
) -> float:
    """Returns the standard deviation using Equation 16 of Macedo et al. (2021). Assume
    this can apply to all three types (tau, phi, sigma) of stddev?XXX
    """
    return np.sqrt(sig_ia_cond**2.0 + (sig_pga**2.0) * (C["c2"] ** 2.0))


def get_standard_deviations(
    C: Dict, sigma_gms: np.recarray, tau_gms: np.recarray, phi_gms: np.recarray
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Returns the total standard deviation and, if specified
    by the input ground motions, the between and within-event
    standard deviations

    Note we are not confident in the details of this fn
    """
    sigma_pga = sigma_gms["PGA"]
    sigma_cav_cond = np.sqrt(C["phi"] ** 2 + C["tau"] ** 2)
    # Gets the total standard deviation
    sigma = get_stddev_component(C, sigma_cav_cond, sigma_pga)

    if np.any(tau_gms["PGA"] >= 0.0):
        # If provided by the conditioning ground motion, get the
        # between-event standard deviation
        tau = get_stddev_component(C, C["tau"], tau_gms["PGA"])
    else:
        tau = 0.0
    if np.any(phi_gms["PGA"] >= 0.0):
        # If provided by the conditioning ground motion, get the
        # within-event standard deviation
        phi = get_stddev_component(C, C["phi"], phi_gms["PGA"])
    else:
        phi = 0.0
    return sigma, tau, phi


class MacedoEtAl2021(ConditionalGMPE):
    """Implementation of a conditional GMPE of Macedo, Abrahamson & Liu (2021)
    for CAV, applied to shallow crustal earthquakes. This
    requires characterisation of the PGA, in addition to magnitude,
    vs30, rrup, dip and rjb for defining CAV, and propagates uncertainty
    accordingly.

    Macedo J, Abrahamson N, Liu C (2021) "New
    scenario-based cumulative absolute velocity models
    for shallow crustal tectonic settings", Bulletin of the
    Seismological Society of America, 111(1): 157 - 172

    """

    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {CAV, PGA}

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
    REQUIRES_RUPTURE_PARAMETERS = {"mag", "dip"}
    REQUIRES_DISTANCES = {"rx", "rrup", "rjb"}

    # Conditional upon PGA
    REQUIRES_IMTS = {"PGA"}

    # GMPE not verified against an independent implementation
    non_verified = True

    def __init__(self, **kwargs):
        """
        Args:
            region: Region of application. CGMM is "Global" where it can be
            conditioned on a regional model
        """
        super().__init__(**kwargs)

    def compute(
        self,
        ctx: np.recarray,
        imts: List,
        mean: np.ndarray,
        sig: np.ndarray,
        tau: np.ndarray,
        phi: np.ndarray,
    ):
        """Calculates the mean CAV and the standard deviations"""
        mean_gms, sigma_gms, tau_gms, phi_gms = self.get_conditioning_ground_motions(
            ctx
        )
        C = CONSTANTS
        # convert from cm/s to g-s
        gfact = 9.81
        conv_fact = np.log(1 / gfact)
        for m, imt in enumerate(imts):
            mean[m] = get_mean_conditional_cav(C, ctx, imt, mean_gms) \
                                                + conv_fact
            sigma_m, tau_m, phi_m = get_standard_deviations(
                C, sigma_gms, tau_gms, phi_gms
            )
            sig[m] += sigma_m
            tau[m] += tau_m
            phi[m] += phi_m
