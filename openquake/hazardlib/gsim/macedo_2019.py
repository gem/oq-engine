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
from openquake.hazardlib.gsim.base import GMPE


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


def get_mean_conditional_ia(
    C: dict,
    ctx: np.recarray,
    base_preds: dict
) -> np.ndarray:
    """
    Returns the Arias Intensity (Equation 2)
    """
    return (C["c1"] + C["c2"] * np.log(ctx.vs30) +
            C["c3"] * ctx.mag + C["c4"] * base_preds["PGA"]['mean'] +
            C["c5"] * base_preds["SA(1.0)"]['mean'])


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


def get_sig(
    C: dict,
    kind: str,
    rho_pga_sa1: float,
    base_preds: dict
    ):
    """
    Returns sigma, tau and phi arrays for Arias Intensity
    """
    sigma_ia_cond = 0.36 if kind == "sinter" else 0.33

    # Gets the total standard deviation
    sigma = get_stddev_component(C,
                                 sigma_ia_cond,
                                 base_preds["PGA"]['sig'],
                                 base_preds["SA(1.0)"]['sig'],
                                 rho_pga_sa1)
    
    # If provided by the conditioning ground motion, get the between-event standard deviation
    if np.any(base_preds["PGA"]["tau"] >= 0.0) or np.any(base_preds["SA(1.0)"]["tau"] > 0.0):
        tau = get_stddev_component(
            C,
            np.sqrt(C["tau"]**2 + C["tau_region"]**2),
            base_preds["PGA"]["tau"],
            base_preds["SA(1.0)"]["tau"],
            rho_pga_sa1)
    else:
        tau = 0.0
    
    # If provided by the conditioning ground motion, get the within-event standard deviation
    if np.any(base_preds["PGA"]["phi"] >= 0.0) or np.any(base_preds["SA(1.0)"]["phi"] > 0.0):
        phi = get_stddev_component(
            C,
            C["phi"],
            base_preds["PGA"]["phi"],
            base_preds["SA(1.0)"]["phi"],
            rho_pga_sa1
            )
    else:
        phi = 0.0

    return sigma, tau, phi


class MacedoEtAl2019SInter(GMPE):
    """
    Implementation of a conditional GMPE of Macedo, Abrahamson & Bray (2019)
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
    REQUIRES_RUPTURE_PARAMETERS = {"mag"}
    REQUIRES_DISTANCES = {'rrup'}

    # Subduction interface
    kind = "sinter"

    # Conditional upon PGA and SA(1.0)
    REQUIRES_IMTS = [PGA(), SA(1.0)] # NOTE: This is ESSENTIAL for a conditional GMPE's
                                     # implementation in OQ given we use ModifiableGMPE
                                     # to manage them (we need this info as a class att
                                     # to be available in the mgmpe imt-checks)

    # GMPE not verified against an independent implementation
    non_verified = True

    # Conditional GMPE
    conditional = True

    def __init__(self, region: str="Global", rho_pga_sa1: float=0.52):
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

        NOTE: the underlying "base" GSIM is specified within ModifiableGMPE (as the
        GMPE upon which the predictions are conditioned), and therefore the base GMPE
        does not have to be specified within the instantation of this GMPE. Please see
        oq-engine/openquake/qa_test_data/classical/case_90/conditional_gmpes.xml for
        an example of conditional GMPEs specified within ModifiableGMPE.
        """
        # Check that the region is one of those supported
        assert region in ("Global", "Japan", "Taiwan", "South America",
                          "New Zealand"),\
            "Region %s not recognised for Macedo et al (2019) GMPE" % region
        self.region = region
        self.rho_pga_sa1 = rho_pga_sa1

    def compute(self, ctx: np.recarray, base_preds: dict):
        """
        Compute method for conditional GMPE applied within ModifiableGMPE.

        :param base_preds: Dictionary where each key is a string of an IMT
                           and each value is a sub-dictionary. Each subdict
                           has keys of "mean", "sigma", "tau" and "phi", with
                           the values representing those computed using the
                           underlying GMM (i.e. the values the conditional GMPE's
                           values will be conditioned upon). This dictionary is
                           built within the ModifiableGMPE's compute method.
        """
        C = CONSTANTS[self.kind][self.region]

        mean_ia = get_mean_conditional_ia(C, ctx, base_preds)

        sigma_ia, tau_ia, phi_ia = get_sig(C, self.kind, self.rho_pga_sa1, base_preds)
        
        return mean_ia, sigma_ia, tau_ia, phi_ia


class MacedoEtAl2019SSlab(MacedoEtAl2019SInter):
    """
    Macedo et al. (2019) GMPE for application to subduction in-slab earthquakes
    """
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB
    kind = "sslab"
