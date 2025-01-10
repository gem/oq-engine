# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2025 GEM Foundation
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
Module exports :class:`ESHM20Craton`
"""

import numpy as np
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable, add_alias
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib import const
from openquake.hazardlib.gsim.nga_east import (
    get_tau_at_quantile, get_phi_ss_at_quantile, TAU_EXECUTION, TAU_SETUP,
    PHI_SETUP, get_phi_ss, NGAEastGMPE, _get_f760, get_nonlinear_stddev,
    get_linear_stddev, _get_fv, get_fnl)
from openquake.hazardlib.gsim.usgs_ceus_2019 import get_stewart_2019_phis2s
from openquake.hazardlib.gsim.kotha_2020 import KothaEtAl2020ESHM20

CONSTANTS = {"Mref": 4.5, "Rref": 1., "Mh": 6.2, "h": 5.0}


def get_distance_term(C, mag, rrup):
    """
    Returns the distance attenuation factor
    """
    rval = np.sqrt(rrup ** 2. + CONSTANTS["h"] ** 2.)
    rref_val = np.sqrt(CONSTANTS["Rref"] ** 2. +
                       CONSTANTS["h"] ** 2.)

    f_r = (C["c1"] + C["c2"] * (mag - CONSTANTS["Mref"])) *\
        np.log(rval / rref_val) + (C["c3"] * (rval - rref_val) / 100.)
    return f_r


def get_hard_rock_mean(C, ctx):
    """
    Returns the mean and standard deviations for the reference very hard
    rock condition (Vs30 = 3000 m/s)
    """
    return get_magnitude_scaling(C, ctx.mag) + get_distance_term(
        C, ctx.mag, ctx.rrup)


def get_magnitude_scaling(C, mag):
    """
    Returns the magnitude scaling term
    """
    d_m = mag - CONSTANTS["Mh"]
    return np.where(mag <= CONSTANTS["Mh"],
                    C["e1"] + C["b1"] * d_m + C["b2"] * d_m ** 2.0,
                    C["e1"] + C["b3"] * d_m)


def get_site_amplification(site_epsilon, imt, pga_r, ctx):
    """
    Returns the sum of the linear (Stewart et al., 2019) and non-linear
    (Hashash et al., 2019) amplification terms
    """
    # Get the coefficients for the IMT
    C_LIN = NGAEastGMPE.COEFFS_LINEAR[imt]
    C_F760 = NGAEastGMPE.COEFFS_F760[imt]
    C_NL = NGAEastGMPE.COEFFS_NONLINEAR[imt]
    if str(imt).startswith("PGA"):
        period = 0.01
    elif str(imt).startswith("PGV"):
        period = 0.5
    else:
        period = imt.period
    # Get f760
    f760 = _get_f760(C_F760, ctx.vs30,
                     NGAEastGMPE.CONSTANTS)
    # Get the linear amplification factor
    f_lin = _get_fv(C_LIN, ctx.vs30, f760,
                    NGAEastGMPE.CONSTANTS)
    # Get the nonlinear amplification from Hashash et al., (2017)
    f_nl, f_rk = get_fnl(C_NL, pga_r, ctx.vs30, period)
    # Mean amplification
    ampl = f_lin + f_nl

    # If an epistemic uncertainty is required then retrieve the epistemic
    # sigma of both models and multiply by the input epsilon
    if site_epsilon:
        # In the case of the linear model sigma_f760 and sigma_fv are
        # assumed independent and the resulting sigma_flin is the root
        # sum of squares (SRSS)
        f760_stddev = _get_f760(C_F760, ctx.vs30,
                                NGAEastGMPE.CONSTANTS,
                                is_stddev=True)
        f_lin_stddev = np.sqrt(
            f760_stddev ** 2. + get_linear_stddev(
                C_LIN, ctx.vs30, NGAEastGMPE.CONSTANTS) ** 2)
        # Likewise, the epistemic uncertainty on the linear and nonlinear
        # model are assumed independent and the SRSS is taken
        f_nl_stddev = get_nonlinear_stddev(
            C_NL, ctx.vs30) * f_rk
        site_epistemic = np.sqrt(f_lin_stddev ** 2. + f_nl_stddev ** 2.)
        ampl += (site_epsilon * site_epistemic)
    return ampl


def get_stddevs(ergodic, tau_model, TAU, PHI_SS, imt, ctx):
    """
    Returns the standard deviations for either the ergodic or
    non-ergodic models
    """
    phi = get_phi_ss(imt, ctx.mag, PHI_SS)
    if ergodic:
        phi_s2s = get_stewart_2019_phis2s(imt, ctx.vs30)
        phi = np.sqrt(phi ** 2. + phi_s2s ** 2.)
    tau = TAU_EXECUTION[tau_model](imt, ctx.mag, TAU)
    sigma = np.sqrt(tau ** 2. + phi ** 2.)
    return [sigma, tau, phi]


class ESHM20Craton(GMPE):
    """
    Implements a scalable backbone GMPE for application to stable cratonic
    regions (primarily intended for cratonic Europe). The median ground motion
    is determined by fitting a parametric model to an extensive set of ground
    motion scenarios from the suite of NGA East ground motion models for 800
    m/s site class. The form of the parametric model is based on that of
    :class:`openquake.hazardlib.gsim.kotha_2019.KothaEtAl2019`, and the
    scaling in terms of the number of standard deviations of the epistemic
    uncertainty (sigma).

    The aleatory uncertainty model is that of Al Atik (2015), which is common
    to all NGA East ground motion models and configurable by the user.

    :param float epsilon:
        Number of standard deviations above or below the median to be applied
        to the epistemic uncertainty sigma

    :param str tau_model:
        Choice of model for the inter-event standard deviation (tau), selecting
        from "global" {default}, "cena" or "cena_constant"

    :param str phi_model:
        Choice of model for the single-station intra-event standard deviation
        (phi_ss), selecting from "global" {default}, "cena" or "cena_constant"

    :param TAU:
        Inter-event standard deviation model

    :param PHI_SS:
        Single-station standard deviation model

    :param PHI_S2SS:
        Station term for ergodic standard deviation model

    :param bool ergodic:
        True if an ergodic model is selected, False otherwise

    :param float tau_quantile:
        Epistemic uncertainty quantile for the inter-event standard
        deviation models. Float in the range 0 to 1, or None (mean value
        used)

    :param float phi_ss_quantile:
        Epistemic uncertainty quantile for the intra-event standard
        deviation models. Float in the range 0 to 1, or None (mean value
        used)

    :param float phi_s2ss_quantile:
        Epistemic uncertainty quantile for the site-to-site standard
        deviation models. Float in the range 0 to 1, or None (mean value
        used)

    :param float site_epsilon:
        Number of standard deviations above or below median for the uncertainty
        in the site amplification model
    """

    #: Supported tectonic region type is 'active shallow crust'
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.STABLE_CONTINENTAL

    #: The GMPE is defined only for PGA and SA
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is the geometric mean of two
    #: horizontal components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    #: Supported standard deviation types are inter-event, intra-event
    #: and total
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Median calibrated for Vs30 3000 m/s Vs30, no site term required Vs30
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Requires only magnitude
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is Rrup
    REQUIRES_DISTANCES = {'rrup'}

    #: Defined for a reference velocity of 3000 m/s
    DEFINED_FOR_REFERENCE_VELOCITY = 3000.0

    def __init__(self, epsilon=0, tau_model="global", phi_model="global",
                 ergodic=True, tau_quantile=None, phi_ss_quantile=None,
                 site_epsilon=0.):
        """
        Instantiates the class with additional terms controlling both the
        epistemic uncertainty in the median and the preferred aleatory
        uncertainty model ('global', 'cena_constant', 'cena'), and the quantile
        of the epistemic uncertainty model (float in the range 0 to 1, or None)
        """
        self.epsilon = epsilon
        self.tau_model = tau_model
        self.phi_model = phi_model
        self.ergodic = ergodic
        self.tau_quantile = tau_quantile
        self.phi_ss_quantile = phi_ss_quantile
        self.site_epsilon = site_epsilon
        self.PHI_S2SS = None
        # define the standard deviation model from the NGA East aleatory
        # uncertainty model according to the calibrations specified by the user
        # setup tau
        self.TAU = get_tau_at_quantile(TAU_SETUP[self.tau_model]["MEAN"],
                                       TAU_SETUP[self.tau_model]["STD"],
                                       self.tau_quantile)
        # setup phi
        self.PHI_SS = get_phi_ss_at_quantile(PHI_SETUP[self.phi_model],
                                             self.phi_ss_quantile)

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        Returns the mean and standard deviations
        """
        C_ROCK = self.COEFFS[PGA()]
        pga_r = get_hard_rock_mean(C_ROCK, ctx)
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            # Get the desired spectral acceleration on rock
            if imt.string != "PGA":
                # Calculate the ground motion at required spectral period for
                # the reference rock
                mean[m] = get_hard_rock_mean(C, ctx)
            else:
                # Avoid re-calculating PGA if that was already done!
                mean[m] = np.copy(pga_r)
            
            mean[m] += get_site_amplification(
                self.site_epsilon, imt, np.exp(pga_r), ctx)

            # Get standard deviation model
            sig[m], tau[m], phi[m] = get_stddevs(
                self.ergodic, self.tau_model, self.TAU, self.PHI_SS,
                imt, ctx)
            if self.epsilon:
                # If requested, apply epistemic uncertainty
                mean[m] += (self.epsilon * C["sigma_mu"])

    COEFFS = CoeffsTable(sa_damping=5, table="""\
    imt                    e1                 b1                    b2                  b3                  c1                   c2                    c3            sigma_mu
    pga     0.129433711217154  0.516399476752765   -0.1203218740054820   0.209372712495698   -1.49820100429001    0.220432033342701   -0.2193114966960720   0.467518017234970
    0.010   0.441910295918064  0.507166125004641   -0.1018797167490890   0.184282079939229   -1.56753763950638    0.222961320838036   -0.2173850863710700   0.424145087820724
    0.020   0.979123809125496  0.464490220614734   -0.1137734938103270   0.167233525048116   -1.62825571194736    0.226150925046427   -0.2441521749125150   0.453414267627762
    0.025   1.043340609418350  0.469670674909745   -0.1134508651616400   0.174065913292435   -1.60908830139611    0.224104272434454   -0.2576680445215000   0.456276006752802
    0.030   1.046568495683850  0.476295173341630   -0.1145295451766630   0.188789464775533   -1.57834523952911    0.220697857317202   -0.2700129055991920   0.442617576906802
    0.040   1.007663453495640  0.493809587666455   -0.1150108357853370   0.208535847120219   -1.52232244977795    0.215223039177726   -0.2874767187616130   0.432692547164462
    0.050   0.951568976547282  0.507030793387879   -0.1169997424043950   0.227662857289356   -1.47612267464663    0.210020976504110   -0.2982691158785990   0.436894676747672
    0.075   0.766898926868941  0.537817749890152   -0.1257930384357200   0.255897568366613   -1.39013641948231    0.198935495001160   -0.3062526875169160   0.445048551267241
    0.100   0.566921463821433  0.563265477669262   -0.1390887741365440   0.285966324295526   -1.32905052927637    0.189118846081288   -0.2963709612002850   0.445057073756783
    0.150   0.316925422496063  0.627617718350029   -0.1689678154012890   0.338414772067430   -1.25211993705245    0.167801937655424   -0.2665003749714420   0.408938323358624
    0.200   0.116888680130253  0.691136578143751   -0.1911386191534560   0.377390002770526   -1.20586644897371    0.154400113563626   -0.2365399916865360   0.396717600597790
    0.250  -0.043842379857700  0.744829702492645   -0.2085160327338160   0.406488784261977   -1.18352051545358    0.146981292282198   -0.2083030844596630   0.385803497323193
    0.300  -0.198476724421674  0.799805296458131   -0.2231548236155840   0.433865912912985   -1.16557023447139    0.140633373085703   -0.1797968441826460   0.386776049771811
    0.400  -0.441747369972888  0.897281226627442   -0.2422049150995460   0.483912433515021   -1.15156734492077    0.133979350791855   -0.1362509955087160   0.395064995993542
    0.500  -0.637444825872443  0.992673274984355   -0.2539089461326410   0.526938715295978   -1.14419843291335    0.129943753235505   -0.1121349311669610   0.416676943629526
    0.750  -1.032362404718110  1.237960033431780   -0.2483534410193260   0.613138137400433   -1.12728314803895    0.121478497518643   -0.0735664802614733   0.424883714950325
    1.000  -1.372802902796470  1.445803895497810   -0.2291157391507420   0.691619273496051   -1.10947364377839    0.116810841150476   -0.0583506072267647   0.435248946431388
    1.500  -1.888467249398300  1.730211169117530   -0.1937203497378370   0.805618949392974   -1.10238976578388    0.114304314269286   -0.0390002103787838   0.494395041361088
    2.000  -2.334523112985840  1.920451196131200   -0.1617462515371870   0.908051097334214   -1.09476613327876    0.113858927938807   -0.0296892844443899   0.529656872094865
    3.000  -3.034920080151080  2.146848246139110   -0.1148224554001390   1.085140635646810   -1.09084212215003    0.115716684506372   -0.0198059757373382   0.550851605706151
    4.000  -3.576616283968620  2.262687822224390   -0.0885264828734587   1.227765676724790   -1.09028991715414    0.117770415095847   -0.0135787505915478   0.547911773655132
    5.000  -4.022628827670580  2.318743563950980   -0.0777038034207444   1.346637420710540   -1.09024942151365    0.118983393877196   -0.0083301911092432   0.536941450716745
    7.500  -4.876430881706430  2.373219226144200   -0.0645988540118558   1.529692859278580   -1.10750011821578    0.131643152520841   -0.0000488890402107   0.531853282981450
    10.00  -5.489149076214530  2.381480607871230   -0.0633541563175792   1.620019767639500   -1.12740443208222    0.141291747206530    0.0059559626930461   0.560198970449326
    """)


# Add aliases for the ESHM20 adjustments to the Craton Model
# Define the adjustment factors for the 3- and 5-pnt Gaussian approximation
# according to Miller & Rice (1983)
MILLER_RICE_GAUSS_3PNT = [-1.732051, 0.0, 1.732051]
MILLER_RICE_GAUSS_5PNT = [-2.856970, -1.355630, 0.0, 1.355630, 2.856970]
STRESS_BRANCHES = ["VLow", "Low", "Mid", "High", "VHigh"]
SITE_BRANCHES = ["Low", "Mid", "High"]
# Get the 15 branch set of aliases
for stress, eps1 in zip(STRESS_BRANCHES, MILLER_RICE_GAUSS_5PNT):
    for site, eps2 in zip(SITE_BRANCHES, MILLER_RICE_GAUSS_3PNT):
        alias = "ESHM20Craton{:s}Stress{:s}Site".format(stress, site)
        add_alias(alias, ESHM20Craton, epsilon=eps1, site_epsilon=eps2)

# Add on the four branches of the KothaEtAl2020ESHM20 adjustments
add_alias(
    "ESHM20CratonShallowHighStressMidAtten",
    KothaEtAl2020ESHM20,
    sigma_mu_epsilon=1.732051
    )

add_alias(
    "ESHM20CratonShallowHighStressSlowAtten",
    KothaEtAl2020ESHM20,
    sigma_mu_epsilon=1.732051,
    c3_epsilon=1.732051
    )

add_alias(
    "ESHM20CratonShallowMidStressMidAtten",
    KothaEtAl2020ESHM20,
    )

add_alias(
    "ESHM20CratonShallowMidStressSlowAtten",
    KothaEtAl2020ESHM20,
    c3_epsilon=1.732051
    )
