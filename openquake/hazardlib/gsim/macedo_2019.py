# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2023 GEM Foundation
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
Module exports :class:`MacedoEtAl2019SInter`,
               :class:`MacedoEtAl2019SSlab`
"""
from typing import Dict, List, Tuple
import numpy as np
from openquake.hazardlib import const
from openquake.hazardlib.imt import IMT, IA, PGA, SA, from_string
from openquake.hazardlib.gsim.base import ConditionalGMPE, add_alias



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
    C: Dict,
    ctx: np.recarray,
    imt: IMT,
    mean_gms: Dict
) -> np.ndarray:
    """Returns the Arias Intensity (Equation 2)
    """
    assert str(imt) == "IA"
    return C["c1"] + C["c2"] * np.log(ctx.vs30) +\
        C["c3"] * ctx.mag + C["c4"] * np.log(mean_gms["PGA"]) +\
        C["c5"] * np.log(mean_gms["SA(1.0)"])


def get_stddev_component(
    C: Dict,
    sig_ia_cond: float,
    sig_pga: float,
    sig_sa1: float,
    rho: float
) -> float:
    """Returns the standard deviation using Equation 6. Assume
    this can apply to all three components of stddev
    """
    return np.sqrt(
        sig_ia_cond ** 2.0 +
        (sig_pga ** 2.0) * (C["c4"] ** 2.0) +
        (sig_sa1 ** 2.0) * (C["c5"] ** 2.0) +
        (2.0 * (rho * sig_pga * sig_sa1) * C["c4"] * C["c5"])
    )
    

def get_standard_deviations(
    C: Dict,
    kind: str,
    rho_pga_sa1: float,
    sigma_gms: Dict,
    tau_gms: Dict,
    phi_gms: Dict
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Returns the total standard deviation and, if specified
    by the input ground motions, the between and within-event
    standard deviations
    """
    sigma_ia_cond = 0.36 if kind == "sinter" else 0.33
    # Gets the total standard deviation
    sigma = get_stddev_component(C, sigma_ia_cond, sigma_gms["PGA"],
                                 sigma_gms["SA(1.0)"], rho_pga_sa1)
    if tau_gms:
        # If provided by the conditioning ground motion, get the
        # between-event standard deviation
        tau = get_stddev_component(
            C, 
            np.sqrt(C["tau"] ** 2.0 + C["tau_region"] ** 2.0),
            tau_gms["PGA"],
            tau_gms["SA(1.0)"],
            rho_pga_sa1)
    else:
        tau = 0.0
    if phi_gms:
        # If provided by the conditioning ground motion, get the
        # within-event standard deviation
        phi = get_stddev_component(C, C["phi"], phi_gms["PGA"],
                                   phi_gms["SA(1.0)"], rho_pga_sa1)
    else:
        phi = 0.0
    return sigma, tau, phi
    

class MacedoEtAl2019SInter(ConditionalGMPE):
    """Prototype implementation of a conditional GMPE of
    Macedo, Abrahamson & Bray (2019) for Arias Intensity, applied to
    subduction interface earthquakes

    Macedo J, Abrahamson N, Bray JD (2019) "Arias Intensity Conditional
    Scaling Ground-Motion Models for Subduction Zones", Bulletin of the
    Seismological Society of America, 109(4): 1343 - 1357

    """
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {IA,}

    # It is unclear to me if the CGMM is for a specific component? Or is the
    # component associated with the input ctx.imt?
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT,
    }

    REQUIRES_SITES_PARAMETERS = {"vs30",}
    REQUIRES_RUPTURE_PARAMETERS = {"mag",}
    REQUIRES_DISTANCES = {}

    # Subduction interface
    kind = "sinter"

    # Conditional upon PGA and Sa (1.0 s)
    REQUIRES_IMTS = {"PGA", "SA(1.0)"}

    def __init__(
    self,
    region: str = "Global",
    rho_pga_sa1: float = 0.52, **kwargs
    ):
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
        """
        super().__init__(**kwargs)
        # Check that the region is one of those supported
        assert region in ("Global", "Japan", "Taiwan", "South America",
                          "New Zealand"),\
            "Region %s not recognised for Macedo et al (2019) GMPE" % region
        self.region = region
        self.rho_pga_sa1 = rho_pga_sa1

    def compute(
    self,
    ctx: np.recarray,
    imts: List, mean: np.ndarray,
    sig: np.ndarray,
    tau: np.ndarray,
    phi: np.ndarray):
        """Calculates the mean Arias Intensity and the standard deviations
        """
        mean_gms, sigma_gms, tau_gms, phi_gms =\
            self.get_conditioning_ground_motions(ctx)
        C = CONSTANTS[self.kind][self.region]
        for m, imt in enumerate(imts):
            mean[m] = get_mean_conditional_arias_intensity(
                C, ctx, imt, mean_gms)
            sigma_m, tau_m, phi_m = get_standard_deviations(
                C, self.kind, self.rho_pga_sa1, sigma_gms,
                tau_gms, phi_gms
            )
            sig[m] += sigma_m
            tau[m] += tau_m
            phi[m] += phi_m


class MacedoEtAl2019SSlab(MacedoEtAl2019SInter):
    """Macedo et al. (2019) GMPE for application to
    subduction in-slab earthquakes
    """
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB
    kind = "sslab"


# Create alias classes for the Macedo et al. (2019) regionalisations
for region_name in ["Japan", "Taiwan", "South America", "New Zealand"]:
    sinter_alias = "MacedoEtAl2019SInter{:s}".format(
        region_name.replace(" ", "")
        )
    sslab_alias = "MacedoEtAl2019SSlab{:s}".format(
        region_name.replace(" ", "")
        )
    add_alias(sinter_alias, MacedoEtAl2019SInter, region=region_name)
    add_alias(sslab_alias, MacedoEtAl2019SSlab, region=region_name)
