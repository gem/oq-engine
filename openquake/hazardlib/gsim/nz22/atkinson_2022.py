# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2025 GEM Foundation
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
Module exports :class:`Atkinson2022Crust`
               :class:`Atkinson2022SSlab`
               :class:`Atkinson2022SInter`
"""

from pathlib import Path

import numpy as np
from scipy.interpolate import interp1d

from openquake.hazardlib import const
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib.gsim.nz22.const import (
    periods_AG20,
    rho_Ws,
    rho_Bs,
    periods,
    theta7s,
    theta8s,
)
from openquake.hazardlib.imt import PGA, SA

Atk22_COEFFS = Path(
    Path(__file__).parent, "Atkinson22_coeffs_mod_v8b_sanjay_v2.csv"
)


def _fmag(suffix, C, mag):
    """
    ctx.magnitude factor
    """
    if suffix == "slab":
        # res = C['c0_' + suffix] + C['c1_' + suffix] * (mag - 6.0) + C['c2_' + suffix] * (mag - 6.0) ** 2
        # Modified as in RevisionsToBackbonev8 from Gail received on 21.06.2022.
        res = (
            C["c0_" + suffix]
            + C["c1_" + suffix] * mag
            + C["c2_" + suffix] * mag**2
        )
    else:
        res = C["c0_crust"] + C["c1_crust"] * mag + C["c2_crust"] * mag**2
    return res


def _fz_ha18(C, ctx):
    """
    Implements eq. 2,3,4,5 from page 5
    """
    # pseudo-depth

    # h = 10 ** (-0.1 + 0.2 * ctx.mag) The h term is modified after
    # receiving the modifications from Gail on Slack on 12.06.2022.  h
    # = 10 ** (0.3 + 0.11 * ctx.mag) Modified as in
    # RevisionsToBackbonev8 from Gail received on 21.06.2022. However,
    # there is a typo.
    h = 10 ** (-0.405 + 0.235 * ctx.mag)
    R = np.sqrt(ctx.rrup**2 + h**2)
    Rref = np.sqrt(1 + h**2)
    # The transition_distance
    Rt = 50
    # Geometrical spreading rates
    b1 = -1.3
    b2 = -0.5
    # Geometrical attenuation
    z = R**b1
    ratio = R / Rt
    z[R > Rt] = Rt**b1 * (ratio[R > Rt]) ** b2

    return np.log(z) + (C["b3"] + C["b4"] * ctx.mag) * np.log(R / Rref)


def _fgamma(suffix, C, ctx):
    if suffix == "crust":
        g1 = min(0.008, 0.005 + 0.0016 * np.log(C["f"]))
    elif suffix == "inter":
        g1 = min(0.006, 0.0045 + 0.0014 * np.log(C["f"]))
    else:
        g1 = min(0.005, 0.004 + 0.0012 * np.log(C["f"]))

    # a2 = max(0.002 + 0.0025 * np.log(max(C['f'], 35)), 0.0015)
    # a3 = 0.009 - 0.001 * np.log(max(C['f'], 35))
    # g2 = min(min(0.0065, a2), a3)

    gamma = np.zeros(ctx.rrup.shape)

    # gamma = -g1 * ctx.rrup + g2*(270.0 - np.clip(ctx.rrup, 270,
    # None)) Gail mentioned in personal communication (email
    # 13.06.2022) that now the modified F_gamma (see eq. 20-22 in
    # modifications posted on Salck 12.06.2022) does not include
    # gamma_2 term.
    gamma = -g1 * ctx.rrup
    return gamma


def _epistemic_adjustment_lower(C, ctx):
    # These are revised adjustments after Gail's post on slack 11th
    # May 2022 and in her revised report.  The lower branch adjustment
    # remains the same.  a = np.fmax(np.clip(0.5 - 0.1 *
    # np.log(ctx.rrup), 0.2, None), - 0.25 + 0.1 * np.log(ctx.rrup))
    # The following variable is after Gail's modifications received on
    # Slack 12.06.2022 The additional epistemic uncertainty for M>7
    # events was added in Gail's V8 modifications shared on 27.06.2022
    a = np.fmax(
        np.clip(0.6 - 0.13 * np.log(ctx.rrup), 0.3, None),
        -0.25 + 0.12 * np.log(ctx.rrup),
    )
    return np.clip(a, -np.inf, 0.5) + 0.15 * np.clip(ctx.mag - 7.0, 0, np.inf)


def _epistemic_adjustment_upper(C, ctx):
    # These are revised adjustments after Gail's post on slack 11th
    # May 2022 and in her revised report.  Only the upper brach is
    # modified.  a = np.fmax(np.clip(1.0 - 0.27 * np.log(ctx.rrup),
    # 0.2, None), - 0.25 + 0.1 * np.log(ctx.rrup)) The following
    # variable is after Modification from Gail recieved on Slack
    # 12.06.2022 The additional epistemic uncertainty for M>7 events
    # was added in Gail's V8 modifications shared on 27.06.2022
    a = np.fmax(
        np.clip(1.0 - 0.3 * np.log(ctx.rrup), 0.3, None),
        -0.25 + 0.12 * np.log(ctx.rrup),
    )
    return np.clip(a, -np.inf, 0.8) + 0.15 * np.clip(ctx.mag - 7.0, 0, np.inf)


def fs_SS14(C, pga_rock, ctx):
    # The site-term is implemnted from Seyhan and Stewart (2014; EQS).
    Vs_ref = 760.0
    flin = ctx.vs30 / Vs_ref
    flin[ctx.vs30 > C["Vc"]] = C["Vc"] / Vs_ref
    flin_func = C["c"] * np.log(flin)

    v_s = np.copy(ctx.vs30)
    v_s[ctx.vs30 > 760.0] = 760.0
    f_1 = 0.0
    f_3 = 0.1 * 981.0  # In Gail's model the GMM is in cm/s^2.
    # Nonlinear controlling parameter (equation 8)
    f_2 = C["f4"] * (np.exp(C["f5"] * (v_s - 360.0)) - np.exp(C["f5"] * 400.0))
    fnl = f_1 + f_2 * np.log((pga_rock + f_3) / f_3)
    return flin_func + fnl


def _get_pga_on_rock(suffix, C, ctx):
    pga_rock = np.exp(
        _fmag(suffix, C, ctx.mag) + _fz_ha18(C, ctx) + _fgamma(suffix, C, ctx)
    )
    return pga_rock


def get_stddevs(suffix, C):
    """
    Standard deviations given in COEFFS with suffix
    Between event standard deviations as Be_.
    Within event stdvs as We_.
    Total as sigma_.
    """
    intra_e_sigma = np.sqrt(C["We_" + suffix] ** 2 + C["phiS2S"] ** 2)
    return [C["sigma_" + suffix], C["Be_" + suffix], intra_e_sigma]


def get_nonlinear_stddevs(suffix, C, C_PGA, imt, pga_rock, vs30):
    """
    Get the nonlinear tau and phi terms for Gail's model. For this
    implementation, I using the between-event and within-event
    correlation from AG20. Note that the Gail's nonlinear soil
    response term is identical to Seyhan and Stewart (2014) model.
    """
    period = imt.period
    pgar = pga_rock / 981.0
    # Linear Tau
    tau_lin = C["Be_" + suffix] * np.ones(vs30.shape)
    tau_lin_pga = C_PGA["Be_" + suffix] * np.ones(vs30.shape)

    # Linear phi
    intra_e_sigma = np.sqrt(C["We_" + suffix] ** 2 + C["phiS2S"] ** 2)
    intra_e_sigma_pga = np.sqrt(
        C_PGA["We_" + suffix] ** 2 + C_PGA["phiS2S"] ** 2
    )
    phi_lin = intra_e_sigma * np.ones(vs30.shape)
    phi_lin_pga = intra_e_sigma_pga * np.ones(vs30.shape)

    # Assume that the site response variability is constant with period.
    phi_amp = 0.3
    phi_B = np.sqrt(phi_lin**2 - phi_amp**2)
    phi_B_pga = np.sqrt(phi_lin_pga**2 - phi_amp**2)
    rho_W_itp = interp1d(np.log(periods_AG20), rho_Ws)
    rho_B_itp = interp1d(np.log(periods_AG20), rho_Bs)
    if period < 0.01:
        rhoW = 1.0
        rhoB = 1.0
    else:
        rhoW = rho_W_itp(np.log(period))
        rhoB = rho_B_itp(np.log(period))

    f2 = C["f4"] * (
        np.exp(C["f5"] * (np.minimum(vs30, 760.0) - 360.0))
        - np.exp(C["f5"] * (760.0 - 360.0))
    )
    f3 = 0.1

    partial_f_pga = f2 * pgar / (pgar + f3)
    partial_f_pga = partial_f_pga * np.ones(vs30.shape)

    # nonlinear variance components
    phi2_NL = (
        phi_lin**2
        + partial_f_pga**2 * phi_B_pga**2
        + 2 * partial_f_pga * phi_B_pga * phi_B * rhoW
    )
    tau2_NL = (
        tau_lin**2
        + partial_f_pga**2 * tau_lin_pga**2
        + 2 * partial_f_pga * tau_lin_pga * tau_lin * rhoB
    )

    # return [partial_f_pga, np.sqrt(tau2_NL), np.sqrt(phi2_NL)]
    return [np.sqrt(tau2_NL + phi2_NL), np.sqrt(tau2_NL), np.sqrt(phi2_NL)]


def get_backarc_term(trt, imt, ctx):
    """
    The backarc correction factors to be applied with the ground motion prediction. In the NZ context, it is
    applied to only subduction intraslab events. It is essentially the correction factor taken from BC Hydro
    2016. Abrahamson et al. (2016) Earthquake Spectra. The correction is applied only for backarc sites as
    function of distance.
    """
    period = imt.period
    w_epi_factor = 1.008

    theta7_itp = interp1d(np.log(periods[1:]), theta7s[1:])
    theta8_itp = interp1d(np.log(periods[1:]), theta8s[1:])
    # Note that there is no correction for PGV. Hence, I make theta7 and theta8 as 0 for periods < 0.
    if period < 0:
        theta7 = 0.0
        theta8 = 0.0
    elif period >= 0 and period < 0.02:
        theta7 = 1.0988
        theta8 = -1.42
    else:
        theta7 = theta7_itp(np.log(period))
        theta8 = theta8_itp(np.log(period))

    dists = ctx.rrup

    if trt == const.TRT.SUBDUCTION_INTRASLAB:
        min_dist = 85.0
        backarc = np.bool_(ctx.backarc)
        f_faba = np.zeros_like(dists)
        fixed_dists = dists[backarc]
        fixed_dists[fixed_dists < min_dist] = min_dist
        f_faba[backarc] = theta7 + theta8 * np.log(fixed_dists / 40.0)
        return f_faba * w_epi_factor
    else:
        f_faba = np.zeros_like(dists)
        return f_faba


class Atkinson2022Crust(GMPE):
    """
    Implements Atkinson (2022) backbone model for New Zealand. For
    more info please refere to Gail Atkinson's NSHM report and linked
    revisions.
    """

    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are spectral acceleration,
    #: peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is the RotD50
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT,
    }

    REQUIRES_DISTANCES = {"rrup"}

    REQUIRES_RUPTURE_PARAMETERS = {"mag"}

    REQUIRES_SITES_PARAMETERS = {"vs30"}

    # define the epistemic uncertainities : Central/Lower/Upper

    REQUIRES_ATTRIBUTES = {"epistemic"}

    # define constant parameters
    suffix = "crust"

    def __init__(self, epistemic="Central", modified_sigma=False):
        """
        Aditional parameter for epistemic central,
        lower and upper bounds.
        """
        self.epistemic = epistemic
        self.modified_sigma = modified_sigma

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        trt = self.DEFINED_FOR_TECTONIC_REGION_TYPE
        C_PGA = self.COEFFS[PGA()]
        pga_rock = _get_pga_on_rock(self.suffix, C_PGA, ctx) * np.exp(
            get_backarc_term(trt, PGA(), ctx)
        )
        # Here the backarc term is applied as multiplication because the
        # pga_rock is in linear space not in log space

        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]

            # compute mean
            mean[m] = (
                _fmag(self.suffix, C, ctx.mag)
                + _fz_ha18(C, ctx)
                + _fgamma(self.suffix, C, ctx)
                + fs_SS14(C, pga_rock, ctx)
                + get_backarc_term(trt, imt, ctx)
            )

            mean[m] = mean[m] - np.log(981.0)  # Convert the cm/s^2 to g.

            # In her email and slack post Gail mentioned that her
            # upper and lower branches are as 1.28 times of the delta.
            # So as to represent 10th and 90th percentile.
            # Consequently, the weights have also changed to 0.3, 0.4,
            # 0.3.  The scale factor of 0.9 is applied based upon the
            # discussion that it accounts for the reduction in
            # epistemic uncertainty when no perfect correlation is
            # assumed between rupture scenarios. See the note of Peter
            # and Brendon on slack.
            epistemic_scale_factor = 0.893
            if self.epistemic.lower() == "lower":
                mean[m] = (
                    mean[m]
                    - _epistemic_adjustment_lower(C, ctx)
                    * 1.28155
                    * epistemic_scale_factor
                )

            elif self.epistemic.lower() == "upper":
                mean[m] = (
                    mean[m]
                    + _epistemic_adjustment_upper(C, ctx)
                    * 1.28155
                    * epistemic_scale_factor
                )
            else:
                mean[m] = mean[m]
            # Aleatory Uncertainty terms.
            if self.modified_sigma:
                sig[m], tau[m], phi[m] = get_nonlinear_stddevs(
                    self.suffix, C, C_PGA, imt, pga_rock, ctx.vs30
                )
            else:
                sig[m], tau[m], phi[m] = get_stddevs(self.suffix, C)

    # periods given by 1 / 10 ** COEFFS['f']
    with Atk22_COEFFS.open() as coefs_file:
        COEFFS = CoeffsTable(sa_damping=5, table=coefs_file.read())


class Atkinson2022SInter(Atkinson2022Crust):
    """
    Atkinson 2022 for Subduction Interface in NZ.
    """

    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    # constant table suffix
    suffix = "inter"
    # stress = 100


class Atkinson2022SSlab(Atkinson2022Crust):
    """
    Atkinson (2022) for Subduction IntraSlab in NZ.
    """

    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB

    # constant table suffix
    suffix = "slab"
    REQUIRES_SITES_PARAMETERS = {"vs30", "backarc"}