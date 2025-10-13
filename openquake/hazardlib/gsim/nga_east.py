# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2025 GEM Foundation
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
Module exports :class:`NGAEastGMPE` and :class:`NGAEastGMPETotalSigma`
"""
import io
import os
import numpy as np
from copy import deepcopy
from scipy.stats import chi2
from openquake.hazardlib.gsim.base import CoeffsTable, add_alias
from openquake.hazardlib.gsim.gmpe_table import GMPETable, _get_mean
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


# Common interpolation function
def ITPL(mag, tu, tl, ml, f):
    return tl + (tu - tl) * (mag - ml) / f


def _scaling(mean_tau, sd_tau2):
    """
    Returns the chi-2 scaling factor from the mean and variance of the
    uncertainty model, as reported in equation 5.4 of Al Atik (2015)
    """
    return sd_tau2 ** 2. / (2.0 * mean_tau ** 2.)


def _dof(mean_tau, sd_tau2):
    """
    Returns the degrees of freedom for the chi-2 distribution from the mean and
    variance of the uncertainty model, as reported in equation 5.5 of Al Atik
    (2015)
    """
    return 2.0 * mean_tau ** 4. / sd_tau2 ** 2.


def _at_percentile(tau, var_tau, percentile):
    """
    Returns the value of the inverse chi-2 distribution at the given
    percentile from the mean and variance of the uncertainty model, as
    reported in equations 5.1 - 5.3 of Al Atik (2015)
    """
    assert percentile >= 0.0 and percentile <= 1.0
    c_val = _scaling(tau, var_tau)
    k_val = _dof(tau, var_tau)
    return np.sqrt(c_val * chi2.ppf(percentile, df=k_val))


# Mean tau values from the global model - Table 5.1
GLOBAL_TAU_MEAN = {
    "PGV": {"tau1": 0.3733, "tau2": 0.3639, "tau3": 0.3434, "tau4": 0.3236},
    "SA": {"tau1": 0.4518, "tau2": 0.4270, "tau3": 0.3863, "tau4": 0.3508}
    }


# Standard deviation of tau values from the global model - Table 5.1
GLOBAL_TAU_SD = {
    "PGV": {"tau1": 0.0558, "tau2": 0.0554, "tau3": 0.0477, "tau4": 0.0449},
    "SA": {"tau1": 0.0671, "tau2": 0.0688, "tau3": 0.0661, "tau4": 0.0491}
}


# Mean tau values from the CENA constant-tau model
CENA_CONSTANT_TAU_MEAN = {"PGV": {"tau": 0.3441}, "SA": {"tau": 0.3695}}


# Standard deviation of tau values from CENA constant-tau model
CENA_CONSTANT_TAU_SD = {"PGV": {"tau": 0.0554}, "SA": {"tau": 0.0688}}


# Mean tau values from the CENA tau model
CENA_TAU_MEAN = {
    "PGV": {"tau1": 0.3477, "tau2": 0.3281, "tau3": 0.3092},
    "SA": {"tau1": 0.3730, "tau2": 0.3375, "tau3": 0.3064}
    }


# Standard deviation of tau values from the CENA tau model
CENA_TAU_SD = {
    "PGV": {"tau1": 0.0554, "tau2": 0.0477, "tau3": 0.0449},
    "SA": {"tau1": 0.0688, "tau2": 0.0661, "tau3": 0.0491}
    }


def global_tau(imt, mag, params):
    """
    'Global' model of inter-event variability, as presented in equation 5.6
    (p103)
    """
    if imt.string == "PGV":
        C = params["PGV"]
    else:
        C = params["SA"]
    tau = np.full_like(mag, C["tau1"])
    tau[mag > 6.5] = C["tau4"]
    idx = (mag > 5.5) & (mag <= 6.5)
    tau[idx] = ITPL(mag[idx], C["tau4"], C["tau3"], 5.5, 1.0)
    idx = (mag > 5.0) & (mag <= 5.5)
    tau[idx] = ITPL(mag[idx], C["tau3"], C["tau2"], 5.0, 0.5)
    idx = (mag > 4.5) & (mag <= 5.0)
    tau[idx] = ITPL(mag[idx], C["tau2"], C["tau1"], 4.5, 0.5)
    return tau


def cena_constant_tau(imt, mag, params):
    """
    Returns the inter-event tau for the constant tau case
    """
    if imt.string == "PGV":
        return params["PGV"]["tau"]
    else:
        return params["SA"]["tau"]


def cena_tau(imt, mag, params):
    """
    Returns the inter-event standard deviation, tau, for the CENA case
    """
    if imt.string == "PGV":
        C = params["PGV"]
    else:
        C = params["SA"]
    tau = np.full_like(mag, C["tau1"])
    tau[mag > 6.5] = C["tau3"]
    idx = (mag > 5.5) & (mag <= 6.5)
    tau[idx] = ITPL(mag[idx], C["tau3"], C["tau2"], 5.5, 1.0)
    idx = (mag > 5.0) & (mag <= 5.5)
    tau[idx] = ITPL(mag[idx], C["tau2"], C["tau1"], 5.0, 0.5)
    return tau


def get_tau_at_quantile(mean, stddev, quantile):
    """
    Returns the value of tau at a given quantile in the form of a dictionary
    organised by intensity measure
    """
    tau_model = {}
    for imt in mean:
        tau_model[imt] = {}
        for key in mean[imt]:
            if quantile is None:
                tau_model[imt][key] = mean[imt][key]
            else:
                tau_model[imt][key] = _at_percentile(mean[imt][key],
                                                     stddev[imt][key],
                                                     quantile)
    return tau_model


# Gather tau values into dictionary
TAU_SETUP = {
    "cena": {"MEAN": CENA_TAU_MEAN, "STD": CENA_TAU_SD},
    "cena_constant": {"MEAN": CENA_CONSTANT_TAU_MEAN,
                      "STD": CENA_CONSTANT_TAU_SD},
    "global": {"MEAN": GLOBAL_TAU_MEAN, "STD": GLOBAL_TAU_SD}
    }

# Gather tau model implementation functions into dictionary
TAU_EXECUTION = {
    "cena": cena_tau,
    "cena_constant": cena_constant_tau,
    "global": global_tau}


# Phi_ss coefficients for the global model
PHI_SS_GLOBAL = CoeffsTable(sa_damping=5., table="""\
imt     mean_a   var_a  mean_b  var_b
pgv     0.5034  0.0609  0.3585  0.0316
pga     0.5477  0.0731  0.3505  0.0412
0.010   0.5477  0.0731  0.3505  0.0412
0.020   0.5464  0.0727  0.3505  0.0416
0.030   0.5450  0.0723  0.3505  0.0419
0.040   0.5436  0.0720  0.3505  0.0422
0.050   0.5424  0.0716  0.3505  0.0425
0.075   0.5392  0.0707  0.3505  0.0432
0.100   0.5361  0.0699  0.3505  0.0439
0.150   0.5299  0.0682  0.3543  0.0453
0.200   0.5240  0.0666  0.3659  0.0465
0.250   0.5183  0.0651  0.3765  0.0476
0.300   0.5127  0.0637  0.3876  0.0486
0.400   0.5022  0.0611  0.4066  0.0503
0.500   0.4923  0.0586  0.4170  0.0515
0.750   0.4704  0.0535  0.4277  0.0526
1.000   0.4519  0.0495  0.4257  0.0508
1.500   0.4231  0.0439  0.4142  0.0433
2.000   0.4026  0.0405  0.4026  0.0396
3.000   0.3775  0.0371  0.3775  0.0366
4.000   0.3648  0.0358  0.3648  0.0358
5.000   0.3583  0.0353  0.3583  0.0356
7.500   0.3529  0.0350  0.3529  0.0355
10.00   0.3519  0.0350  0.3519  0.0355
""")


# Phi_ss coefficients for the CENA model
PHI_SS_CENA = CoeffsTable(sa_damping=5., table="""\
imt     mean_a   var_a  mean_b   var_b
pgv     0.5636  0.0807  0.4013  0.0468
pga     0.5192  0.0693  0.3323  0.0364
0.010   0.5192  0.0693  0.3323  0.0364
0.020   0.5192  0.0693  0.3331  0.0365
0.030   0.5192  0.0693  0.3339  0.0365
0.040   0.5192  0.0693  0.3348  0.0367
0.050   0.5192  0.0693  0.3355  0.0367
0.075   0.5192  0.0693  0.3375  0.0370
0.100   0.5192  0.0693  0.3395  0.0372
0.150   0.5192  0.0693  0.3471  0.0382
0.200   0.5192  0.0693  0.3625  0.0402
0.250   0.5192  0.0693  0.3772  0.0423
0.300   0.5192  0.0693  0.3925  0.0446
0.400   0.5192  0.0693  0.4204  0.0492
0.500   0.5192  0.0693  0.4398  0.0527
0.750   0.5192  0.0693  0.4721  0.0590
1.000   0.5192  0.0693  0.4892  0.0626
1.500   0.5192  0.0693  0.5082  0.0668
2.000   0.5192  0.0693  0.5192  0.0693
3.000   0.5192  0.0693  0.5192  0.0693
4.000   0.5192  0.0693  0.5192  0.0693
5.000   0.5192  0.0693  0.5192  0.0693
7.500   0.5192  0.0693  0.5192  0.0693
10.00   0.5192  0.0693  0.5192  0.0693
""")


# Phi_ss coefficients for the CENA constant-phi model
PHI_SS_CENA_CONSTANT = CoeffsTable(sa_damping=5., table="""\
imt     mean_a    var_a   mean_b   var_b
pgv     0.5507   0.0678   0.5507  0.0678
pga     0.5132   0.0675   0.5132  0.0675
0.010   0.5132   0.0675   0.5132  0.0675
10.00   0.5132   0.0675   0.5132  0.0675
""")


# Phi_s2ss coefficients for the CENA
PHI_S2SS_CENA = CoeffsTable(sa_damping=5., table="""\
imt       mean      var
pgv     0.4344   0.0200
pga     0.4608   0.0238
0.010   0.4608   0.0238
0.020   0.4617   0.0238
0.030   0.4700   0.0240
0.040   0.4871   0.0260
0.050   0.5250   0.0290
0.075   0.5800   0.0335
0.100   0.5930   0.0350
0.150   0.5714   0.0325
0.200   0.5368   0.0296
0.250   0.5058   0.0272
0.300   0.4805   0.0250
0.400   0.4440   0.0212
0.500   0.4197   0.0182
0.750   0.3849   0.0139
1.000   0.3667   0.0135
1.500   0.3481   0.0157
2.000   0.3387   0.0173
3.000   0.3292   0.0195
4.000   0.3245   0.0211
5.000   0.3216   0.0224
7.500   0.3178   0.0240
10.00   0.3159   0.0240
""")


def get_phi_ss_at_quantile(phi_model, quantile):
    """
    Returns the phi_ss values at the specified quantile as an instance of
    `class`:: openquake.hazardlib.gsim.base.CoeffsTable - applies to the
    magnitude-dependent cases
    """
    # Setup SA coeffs - the backward compatible Python 2.7 way
    coeffs = deepcopy(phi_model.sa_coeffs)
    coeffs.update(phi_model.non_sa_coeffs)
    for imt in coeffs:
        if quantile is None:
            coeffs[imt] = {"a": phi_model[imt]["mean_a"],
                           "b": phi_model[imt]["mean_b"]}
        else:
            coeffs[imt] = {
                "a": _at_percentile(phi_model[imt]["mean_a"],
                                    phi_model[imt]["var_a"],
                                    quantile),
                "b": _at_percentile(phi_model[imt]["mean_b"],
                                    phi_model[imt]["var_b"],
                                    quantile)}
    return CoeffsTable.fromdict(coeffs)


def get_phi_s2ss_at_quantile(phi_model, quantile):
    """
    Returns the phi_s2ss value for all periods at the specific quantile as
    an instance of `class`::openquake.hazardlib.gsim.base.CoeffsTable
    """
    # Setup SA coeffs - the backward compatible Python 2.7 way
    coeffs = deepcopy(phi_model.sa_coeffs)
    coeffs.update(phi_model.non_sa_coeffs)
    for imt in coeffs:
        if quantile is None:
            coeffs[imt] = {"phi_s2ss": phi_model[imt]["mean"]}
        else:
            coeffs[imt] = {"phi_s2ss": _at_percentile(phi_model[imt]["mean"],
                                                      phi_model[imt]["var"],
                                                      quantile)}
    return CoeffsTable.fromdict(coeffs)


# Gather the models to setup the phi_ss values for the given quantile
PHI_SETUP = {
    "cena": PHI_SS_CENA,
    "cena_constant": PHI_SS_CENA_CONSTANT,
    "global": PHI_SS_GLOBAL}


# Phi site-to-site model for th Central & Eastern US
PHI_S2SS_MODEL = {"cena": PHI_S2SS_CENA}


def get_phi_ss(imt, mag, params):
    """
    Returns the single station phi (or it's variance) for a given magnitude
    and intensity measure type according to equation 5.14 of Al Atik (2015)
    """
    C = params[imt]
    phi = C["a"] + (mag - 5.0) * (C["b"] - C["a"]) / 1.5
    phi[mag <= 5.0] = C["a"]
    phi[mag > 6.5] = C["b"]
    return phi


# ############################ helper functions ########################

def _get_f760(C_F760, vs30, CONSTANTS, is_stddev=False):
    """
    Returns very hard rock to hard rock (Vs30 760 m/s) adjustment factor
    taken as the Vs30-dependent weighted mean of two reference condition
    factors: for impedence and for gradient conditions. The weighting
    model is described by equations 5 - 7 of Stewart et al. (2019)
    """
    wimp = (CONSTANTS["wt1"] - CONSTANTS["wt2"]) *\
        (np.log(vs30 / CONSTANTS["vw2"]) /
         np.log(CONSTANTS["vw1"] / CONSTANTS["vw2"])) + CONSTANTS["wt2"]
    wimp[vs30 >= CONSTANTS["vw1"]] = CONSTANTS["wt1"]
    wimp[vs30 < CONSTANTS["vw2"]] = CONSTANTS["wt2"]
    wgr = 1.0 - wimp
    if is_stddev:
        return wimp * C_F760["f760is"] + wgr * C_F760["f760gs"]
    else:
        return wimp * C_F760["f760i"] + wgr * C_F760["f760g"]


def _get_fv(C_LIN, vs30s, f760, CONSTANTS):
    """
    Returns the Vs30-dependent component of the mean linear amplification
    model, as defined in equation 3 of Stewart et al. (2019)
    """
    const1 = C_LIN["c"] * np.log(C_LIN["v1"] / CONSTANTS["vref"])
    const2 = C_LIN["c"] * np.log(C_LIN["v2"] / CONSTANTS["vref"])
    f_v = C_LIN["c"] * np.log(vs30s / CONSTANTS["vref"])
    f_v[vs30s <= C_LIN["v1"]] = const1
    f_v[vs30s > C_LIN["v2"]] = const2
    idx = vs30s > CONSTANTS["vU"]
    if np.any(idx):
        const3 = np.log(3000. / CONSTANTS["vU"])
        f_v[idx] = const2 - (const2 + f760[idx]) *\
            (np.log(vs30s[idx] / CONSTANTS["vU"]) / const3)
    idx = vs30s >= 3000.
    if np.any(idx):
        f_v[idx] = -f760[idx]
    return f_v + f760


def get_fnl(C_NL, pga_rock, vs30, period, us23=None):
    """
    Returns the nonlinear mean amplification according to equation 2
    of Hashash et al. (2019)
    """
    if period <= 0.4:
        vref = 760.
    else:
        vref = 3000.
    f_nl = np.zeros(vs30.shape)
    f_rk = np.log((pga_rock + C_NL["f3"]) / C_NL["f3"])
    idx = vs30 < C_NL["Vc"]
    if np.any(idx):
        # f2 term of the mean nonlinear amplification model
        # according to equation 3 of Hashash et al., (2019)
        c_vs = np.copy(vs30[idx])
        c_vs[c_vs > vref] = vref
        if us23: # US 2023 NSHMP
            f_4 = C_NL["f4"] * 0.5 + C_NL["f4_mod"] * 0.5
        else:
            f_4 = C_NL["f4"]
        f_2 = f_4 * (np.exp(C_NL["f5"] * (c_vs - 360.)) -
                            np.exp(C_NL["f5"] * (vref - 360.)))
        f_nl[idx] = f_2 * f_rk[idx]
    return f_nl, f_rk


def get_linear_stddev(C_LIN, vs30, CONSTANTS):
    """
    Returns the standard deviation of the linear amplification function,
    as defined in equation 4 of Stewart et al., (2019)
    """
    sigma_v = C_LIN["sigma_vc"] + np.zeros(vs30.shape)
    idx = vs30 < C_LIN["vf"]
    if np.any(idx):
        dsig = C_LIN["sigma_L"] - C_LIN["sigma_vc"]
        d_v = (vs30[idx] - CONSTANTS["vL"]) /\
            (C_LIN["vf"] - CONSTANTS["vL"])
        sigma_v[idx] = C_LIN["sigma_L"] - (2. * dsig * d_v) +\
            dsig * (d_v ** 2.)
    idx = np.logical_and(vs30 > C_LIN["v2"], vs30 <= CONSTANTS["vU"])
    if np.any(idx):
        d_v = (vs30[idx] - C_LIN["v2"]) / (CONSTANTS["vU"] - C_LIN["v2"])
        sigma_v[idx] = C_LIN["sigma_vc"] + \
            (C_LIN["sigma_U"] - C_LIN["sigma_vc"]) * (d_v ** 2.)
    idx = vs30 >= CONSTANTS["vU"]
    if np.any(idx):
        sigma_v[idx] = C_LIN["sigma_U"] *\
            (1. - (np.log(vs30[idx] / CONSTANTS["vU"]) /
                   np.log(3000. / CONSTANTS["vU"])))
    sigma_v[vs30 > 3000.] = 0.0
    return sigma_v


def get_nonlinear_stddev(C_NL, vs30):
    """
    Returns the standard deviation of the nonlinear amplification function,
    as defined in equation 2.5 of Hashash et al. (2017)
    """
    sigma_f2 = np.zeros(vs30.shape)
    sigma_f2[vs30 < 300.] = C_NL["sigma_c"]
    idx = np.logical_and(vs30 >= 300, vs30 < 1000)
    if np.any(idx):
        sigma_f2[idx] = (-C_NL["sigma_c"] / np.log(1000. / 300.)) *\
            np.log(vs30[idx] / 300.) + C_NL["sigma_c"]
    return sigma_f2


def get_hard_rock_mean(self, mag, ctx, imt):
    """
    Returns the mean and standard deviations for the reference very hard
    rock condition (Vs30 = 3000 m/s)
    """
    # return Distance Tables
    imls = self.mean_table['%.2f' % mag, imt.string]
    # Get distance vector for the given magnitude
    idx = np.searchsorted(self.m_w, mag)
    dists = self.distances[:, 0, idx - 1]
    dst = getattr(ctx, self.distance_type)
    # get log(mean)
    return np.log(_get_mean(self.kind, imls, dst, dists))


def get_site_amplification(self, imt, pga_r, vs30s, us23=False):
    """
    Returns the sum of the linear (Stewart et al., 2019) and non-linear
    (Hashash et al., 2019) amplification terms
    """
    # Get the coefficients for the IMT
    C_LIN = COEFFS_LINEAR[imt]
    C_F760 = COEFFS_F760[imt]
    C_NL = COEFFS_NONLINEAR[imt]
    if str(imt).startswith("PGA"):
        period = 0.01
    elif str(imt).startswith("PGV"):
        period = 0.5
    else:
        period = imt.period
    # Get f760
    f760 = _get_f760(C_F760, vs30s, CONSTANTS)
    # Get the linear amplification factor
    f_lin = _get_fv(C_LIN, vs30s, f760, CONSTANTS)
    # Get the nonlinear amplification from Hashash et al., (2017)
    f_nl, f_rk = get_fnl(C_NL, pga_r, vs30s, period, us23)
    # Mean amplification
    ampl = f_lin + f_nl

    # If an epistemic uncertainty is required then retrieve the epistemic
    # sigma of both models and multiply by the input epsilon
    if self.site_epsilon:
        site_epistemic = get_site_amplification_sigma(
            self, vs30s, f_rk, C_LIN, C_F760, C_NL)
        ampl += self.site_epsilon * site_epistemic
    return ampl


def get_site_amplification_sigma(self, vs30s, f_rk, C_LIN, C_F760, C_NL):
    """
    Returns the epistemic uncertainty on the site amplification factor
    """
    # In the case of the linear model sigma_f760 and sigma_fv are
    # assumed independent and the resulting sigma_flin is the root
    # sum of squares (SRSS)
    f760_stddev = _get_f760(C_F760, vs30s,
                            CONSTANTS, is_stddev=True)
    f_lin_stddev = np.sqrt(
        f760_stddev ** 2. +
        get_linear_stddev(C_LIN, vs30s, CONSTANTS) ** 2)
    # Likewise, the epistemic uncertainty on the linear and nonlinear
    # model are assumed independent and the SRSS is taken
    f_nl_stddev = get_nonlinear_stddev(C_NL, vs30s) * f_rk
    return np.sqrt(f_lin_stddev ** 2. + f_nl_stddev ** 2.)


def get_stddevs(self, mag, imt):
    """
    Returns the standard deviations for either the ergodic or
    non-ergodic models
    """
    if self.__class__.__name__.endswith('TotalSigma'):
        return [_get_total_sigma(self, imt, mag), 0., 0.]

    tau = _get_tau(self, imt, mag)
    phi = _get_phi(self, imt, mag)
    sigma = np.sqrt(tau ** 2 + phi ** 2)
    return [sigma, tau, phi]


def _get_tau(self, imt, mag):
    """
    Returns the inter-event standard deviation (tau)
    """
    return TAU_EXECUTION[self.tau_model](imt, mag, self.TAU)


def _get_phi(self, imt, mag):
    """
    Returns the within-event standard deviation (phi)
    """
    phi = get_phi_ss(imt, mag, self.PHI_SS)
    if self.ergodic:
        C = self.PHI_S2SS[imt]
        phi = np.sqrt(phi ** 2. + C["phi_s2ss"] ** 2.)
    return phi


def get_mean_amp(self, mag, ctx, imt, u_adj=None, cstl=None):
    """
    Compute mean ground-motion.

    NOTE: If a non-zero cpa_term is computed we apply this adjustment
    post-application of the collapsed epistemic uncertainty site ampl
    model to replicate the USGS java code. Therefore the cpa_term adj
    is added to the collapsed site epi. uncertainty adjusted mean in
    the compute meth of the NGAEastUSGSGMPE class (usgs_ceus_2019.py).

    :param u_adj: Array containing the period-dependent bias
                  adjustment as required for the 2023 Conterminous
                  US NSHMP.

    :param cstl: Dictionary containing parameters required for the
                 computation of the Coastal Plains site amplification
                 model of Chapman and Guo (2021) as required for the
                 2023 Conterminous US NSHMP.
    """
    # Get the PGA on the reference rock condition
    if PGA in self.DEFINED_FOR_INTENSITY_MEASURE_TYPES:
        rock_imt = PGA()
    else:
        rock_imt = SA(0.01)
    pga_r = get_hard_rock_mean(self, mag, ctx, rock_imt)

    # Apply US 2023 period-dep bias adj if required
    if isinstance(u_adj, np.ndarray):
        pga_r += u_adj

    # Get the desired spectral acceleration on rock
    if imt.string != "PGA":
        # Calculate the ground motion at required spectral period for
        # the reference rock
        mean = get_hard_rock_mean(self, mag, ctx, imt)
        # Again apply US 2023 period-dep bias adj if required
        if isinstance(u_adj, np.ndarray):
            mean += u_adj
    else:
        # Avoid re-calculating PGA if that was already done!
        mean = np.copy(pga_r)

    # If applying US 2023 NSHMP bias adjustment OR Coastal Plains
    # site amp adjustment use the alternative f4 coeff (f4_mod)
    # for non-linear site term as within USGS' NGAEast java code
    if isinstance(cstl, dict) or isinstance(u_adj, np.ndarray):
        us23 = True
    else:
        us23 = False

    # Get site amplification
    amp = get_site_amplification(self, imt, np.exp(pga_r), ctx.vs30, us23)

    # Add the site term to the mean
    mean += amp

    # Get the Chapman and Guo (2021) Coastal Plains adjustment if req.
    if isinstance(cstl, dict) and isinstance(cstl['f_cpa'], np.ndarray):
        # Get site amp term with vs30 ref of 1000 m/s
        vs_cg21 = np.full(len(ctx.vs30), 1000.)
        amp_cpa = get_site_amplification(self, imt, np.exp(pga_r), vs_cg21)
        # Then compute adjustment per site
        cpa_term = cstl['f_cpa'] - amp_cpa * cstl['z_scale']
    else:
        cpa_term = np.full(len(ctx.vs30), 0.) # Turn off adjustment

    return mean, amp, pga_r, cpa_term


class NGAEastGMPE(GMPETable):
    """
    A generalised base class for the implementation of a GMPE in which the
    mean values are determined from tables (input by the user) and the standard
    deviation model taken from Al Atik (2015). Should be common to all
    NGA East ground motion models.

    The site amplification model is developed using the model described by
    Stewart et al. (2019) and Hashash et al. (2019). The model contains a
    linear and a non-linear component of amplification.

    The linear model is described in Stewart et al., (2017) and Stewart et al
    (2019), with the latter taken as the authoritative source where differences
    arise:

    Stewart, J. P., Parker, G. A., Harmon, J. A., Atkinson, G. A., Boore, D.
    M., Darragh, R. B., Silva, W. J. and Hashash, Y. M. A. (2017) "Expert Panel
    Recommendations for Ergodic Site Amplification in Central and Eastern
    North America", PEER Report No. 2017/04, Pacific Earthquake Engineering
    Research Center, University of California, Berkeley.

    Stewart, J. P., Parker, G. A., Atkinson, G. M., Boore, D. M., Hashash, Y.
    M. A. and Silva, W. J. (2019) "Ergodic Site Amplification Model for Central
    and Eastern North America", Earthquake Spectra, in press

    The nonlinear model is described in Hashash et al. (2017) and Hashash et
    al. (2019), with the latter taken as the authoritarive source where
    differences arise:

    Hashash, Y. M. A., Harmon, J. A., Ilhan, O., Parker, G. and Stewart, J. P.
    (2017), "Recommendation for Ergonic Nonlinear Site Amplification in
    Central and Eastern North America", PEER Report No. 2017/05, Pacific
    Earthquake Engineering Research Center, University of California, Berkeley.

    Hashash, Y. M. A., Ilhan, O., Harmon, J. A., Parker, G. A., Stewart, J. P.
    Rathje, E. M., Campbell, K. W., and Silva, W. J. (2019) "Nonlinear site
    amplification model for ergodic seismic hazard analysis in Central and
    Eastern North America", Earthquake Spectra, in press

    Note that the uncertainty provided in this model is treated as an
    epistemic rather than aleatory variable. As such there is no modification
    of the standard deviation model used for the bedrock case. The epistemic
    uncertainty can be added to the model by the user input site_epsilon term,
    which describes the number of standard deviations by which to multiply
    the epistemic uncertainty model, to then be added or subtracted from the
    median amplification model

    :param str tau_model:
        Choice of model for the inter-event standard deviation (tau), selecting
        from "global" {default}, "cena" or "cena_constant"

    :param str phi_model:
        Choice of model for the single-station intra-event standard deviation
        (phi_ss), selecting from "global" {default}, "cena" or "cena_constant"

    :param str phi_s2ss_model:
        Choice of station-term s2ss model. Can be either "cena" or None. When
        None is input then the non-ergodic model is used

    :param TAU:
        Inter-event standard deviation model

    :param PHI_SS:
        Single-station standard deviation model

    :param PHI_S2SS:
        Station term for ergodic standard deviation model

    :param bool ergodic:
        True if an ergodic model is selected, False otherwise

    :param float site_epsilon:
        Number of standard deviations above or below median for the uncertainty
        in the site amplification model
    """
    PATH = os.path.join(os.path.dirname(__file__), "nga_east_tables")
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}
    # Requires Vs30 only - common to all models
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    kind = "nga_east"

    def __init__(self, gmpe_table, tau_model="global", phi_model="global",
                 phi_s2ss_model=None, tau_quantile=None, phi_ss_quantile=None,
                 phi_s2ss_quantile=None, site_epsilon=None):
        """
        Instantiates the class with additional terms controlling which
        type of aleatory uncertainty model is preferred ('global',
        'cena_constant', 'cena'), and the quantile of the epistemic uncertainty
        model (float in the range 0 to 1).

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
        """
        self.tau_model = tau_model
        self.phi_model = phi_model
        self.phi_s2ss_model = phi_s2ss_model
        self.TAU = None
        self.PHI_SS = None
        self.PHI_S2SS = None
        if self.phi_s2ss_model:
            self.ergodic = True
        else:
            self.ergodic = False
        self.tau_quantile = tau_quantile
        self.phi_ss_quantile = phi_ss_quantile
        self.phi_s2ss_quantile = phi_s2ss_quantile
        if self.kind != 'usgs':
            # setup tau
            self.TAU = get_tau_at_quantile(TAU_SETUP[self.tau_model]["MEAN"],
                                           TAU_SETUP[self.tau_model]["STD"],
                                           self.tau_quantile)
            # setup phi
            self.PHI_SS = get_phi_ss_at_quantile(PHI_SETUP[self.phi_model],
                                                 self.phi_ss_quantile)
            # if required setup phis2ss
            if self.ergodic:
                self.PHI_S2SS = get_phi_s2ss_at_quantile(
                    PHI_S2SS_MODEL[self.phi_s2ss_model],
                    self.phi_s2ss_quantile)

        self.site_epsilon = site_epsilon
        if not isinstance(gmpe_table, io.BytesIO):  # real path name
            gmpe_table = os.path.join(self.PATH, os.path.basename(gmpe_table))
            assert os.path.exists(gmpe_table), gmpe_table
        super().__init__(gmpe_table)

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        Returns the mean and standard deviations
        """
        [mag] = np.unique(np.round(ctx.mag, 2))  # by construction
        for m, imt in enumerate(imts):
            mean[m], _, _, _ = get_mean_amp(self, mag, ctx, imt)
            # Get standard deviation model
            sig[m], tau[m], phi[m] = get_stddevs(self, ctx.mag, imt)





# For the total standard deviation model the magnitude boundaries depend on
# the model selected
MAG_LIMS_KEYS = {
    "cena": {"mag": [5.0, 5.5, 6.5], "keys": ["tau1", "tau2", "tau3"]},
    "cena_constant": {"mag": [np.inf], "keys": ["tau"]},
    "global": {"mag": [4.5, 5.0, 5.5, 6.5],
               "keys": ["tau1", "tau2", "tau3", "tau4"]}}


def _get_sigma_at_quantile(self, sigma_quantile):
    """
    Calculates the total standard deviation at the specified quantile
    """
    # Mean mean is found in self.TAU. Get the variance in tau
    tau_std = TAU_SETUP[self.tau_model]["STD"]
    # Mean phiss is found in self.PHI_SS. Get the variance in phi
    phi_std = deepcopy(self.PHI_SS.sa_coeffs)
    phi_std.update(self.PHI_SS.non_sa_coeffs)
    for key in phi_std:
        phi_std[key] = {"a": PHI_SETUP[self.phi_model][key]["var_a"],
                        "b": PHI_SETUP[self.phi_model][key]["var_b"]}
    if self.ergodic:
        # IMT list should be taken from the PHI_S2SS_MODEL
        imt_list = list(
            PHI_S2SS_MODEL[self.phi_s2ss_model].non_sa_coeffs)
        imt_list += list(PHI_S2SS_MODEL[self.phi_s2ss_model].sa_coeffs)
    else:
        imt_list = list(phi_std)
    phi_std = CoeffsTable.fromdict(phi_std)
    tau_bar, tau_std = _get_tau_vector(self, self.TAU, tau_std, imt_list)
    phi_bar, phi_std = _get_phi_vector(self, self.PHI_SS, phi_std, imt_list)
    sigma = {}
    # Calculate the total standard deviation
    for imt in imt_list:
        sigma[imt] = {}
        for i, key in enumerate(self.tau_keys):
            # Calculates the expected standard deviation
            sigma_bar = np.sqrt(tau_bar[imt][i] ** 2. +
                                phi_bar[imt][i] ** 2.)
            # Calculated the variance in the standard deviation
            sigma_std = np.sqrt(tau_std[imt][i] ** 2. +
                                phi_std[imt][i] ** 2.)
            # The keys swap from tau to sigma
            new_key = key.replace("tau", "sigma")
            if sigma_quantile is not None:
                sigma[imt][new_key] = _at_percentile(
                    sigma_bar, sigma_std, sigma_quantile)
            else:
                sigma[imt][new_key] = sigma_bar
            self.tau_keys[i] = new_key
    self.SIGMA = CoeffsTable.fromdict(sigma)


def _get_tau_vector(self, tau_mean, tau_std, imt_list):
    """
    Gets the vector of mean and variance of tau values corresponding to
    the specific model and returns them as dictionaries
    """
    self.magnitude_limits = np.array(MAG_LIMS_KEYS[self.tau_model]["mag"])
    self.tau_keys = MAG_LIMS_KEYS[self.tau_model]["keys"]
    t_bar = {}
    t_std = {}
    tau_model = TAU_EXECUTION[self.tau_model]
    for imt in imt_list:
        t_bar[imt] = tau_model(imt, self.magnitude_limits, tau_mean)
        t_std[imt] = tau_model(imt, self.magnitude_limits, tau_std)
    return t_bar, t_std


def _get_phi_vector(self, phi_mean, phi_std, imt_list):
    """
    Gets the vector of mean and variance of phi values corresponding to
    the specific model and returns them as dictionaries
    """
    p_bar = {}
    p_std = {}
    for imt in imt_list:
        p_bar[imt] = ss_mean = get_phi_ss(imt, self.magnitude_limits, phi_mean)
        p_std[imt] = ss_std = get_phi_ss(imt, self.magnitude_limits, phi_std)
        if self.ergodic:
            # Add on the phi_s2ss term according to Eqs. 5.15 and 5.16
            # of Al Atik (2015)
            ss_mean[:] = np.sqrt(
                ss_mean ** 2. +
                PHI_S2SS_MODEL[self.phi_s2ss_model][imt]["mean"] ** 2.)
            ss_std[:] = np.sqrt(
                ss_std ** 2. +
                PHI_S2SS_MODEL[self.phi_s2ss_model][imt]["var"] ** 2.)
    return p_bar, p_std


def _get_total_sigma(self, imt, mag):
    """
    Returns the estimated total standard deviation for a given intensity
    measure type and magnitude
    """
    [mag] = np.unique(np.round(mag, 2))  # by construction
    C = self.SIGMA[imt]
    if mag <= self.magnitude_limits[0]:
        # The CENA constant model is always returned here
        return C[self.tau_keys[0]]
    elif mag > self.magnitude_limits[-1]:
        return C[self.tau_keys[-1]]
    else:
        # Needs interpolation
        for i in range(len(self.tau_keys) - 1):
            l_m = self.magnitude_limits[i]
            u_m = self.magnitude_limits[i + 1]
            if mag > l_m and mag <= u_m:
                return ITPL(mag,
                            C[self.tau_keys[i + 1]],
                            C[self.tau_keys[i]],
                            l_m,
                            u_m - l_m)


class NGAEastGMPETotalSigma(NGAEastGMPE):
    """
    The Al Atik (2015) standard deviation model defines mean and quantiles
    for the inter- and intra-event residuals. However, it also defines
    separately a total standard deviation model with expectation and quantiles.
    As the inter- and intra-event quantile cannot be recovered unambiguously
    from the total standard deviation quantile this form of the model is
    defined only for total standard deviation. Most likely it is this form
    that would be used for seismic hazard analysis.

    :param SIGMA:
        Total standard deviation model at quantile

    :param list magnitude_limits:
        Magnitude limits corresponding to the selected standard deviation
        model

    :param list tau_keys:
        Keys for the tau values corresponding to the selected standard
        deviation model
    """
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    def __init__(self, gmpe_table, tau_model="global", phi_model="global",
                 phi_s2ss_model=None, tau_quantile=None, phi_ss_quantile=None,
                 phi_s2ss_quantile=None, site_epsilon=None,
                 sigma_quantile=None):
        """
        Instantiates the model call the BaseNGAEastModel to return the
        expected TAU, PHI_SS and PHI_S2SS values then uses these to
        calculate the expected total standard deviation and its variance
        according to equations 5.15, 5.16 and/or 5.18 and 5.19 of Al Atik
        (2015)

        :param float sigma_quantile:
            Quantile of the epistemic uncertainty model for the total
            standard deviation. Should be float between 0 and 1, or None (mean
            value taken)
        """
        super().__init__(gmpe_table, tau_model, phi_model,
                 phi_s2ss_model, tau_quantile, phi_ss_quantile,
                 phi_s2ss_quantile, site_epsilon)
        # Upon instantiation the TAU, PHI_SS, and PHI_S2SS objects contain
        # the mean values
        self.SIGMA = None
        self.magnitude_limits = []
        self.tau_keys = []
        _get_sigma_at_quantile(self, sigma_quantile)


# populate gsim_aliases for the NGA East GMPEs
lines = '''\
Boore2015NGAEastA04 BOORE_A04_J15
Boore2015NGAEastAB14 BOORE_AB14_J15
Boore2015NGAEastAB95 BOORE_AB95_J15
Boore2015NGAEastBCA10D BOORE_BCA10D_J15
Boore2015NGAEastBS11 BOORE_BS11_J15
Boore2015NGAEastSGD02 BOORE_SGD02_J15
DarraghEtAl2015NGAEast1CCSP DARRAGH_1CCSP
DarraghEtAl2015NGAEast1CVSP DARRAGH_1CVSP
DarraghEtAl2015NGAEast2CCSP DARRAGH_2CCSP
DarraghEtAl2015NGAEast2CVSP DARRAGH_2CVSP
YenierAtkinson2015NGAEast YENIER_ATKINSON
PezeschkEtAl2015NGAEastM1SS PEZESCHK_M1SS
PezeschkEtAl2015NGAEastM2ES PEZESCHK_M2ES
Frankel2015NGAEast FRANKEL_J15
ShahjoueiPezeschk2015NGAEast SHAHJOUEI_PEZESCHK
AlNomanCramer2015NGAEast ALNOMAN_CRAMER
Graizer2015NGAEast GRAIZER
HassaniAtkinson2015NGAEast HASSANI_ATKINSON
HollenbackEtAl2015NGAEastGP PEER_GP
HollenbackEtAl2015NGAEastEX PEER_EX
'''.splitlines()
for line in lines:
    alias, key = line.split()
    add_alias(alias, NGAEastGMPE,
              gmpe_table=f"NGAEast_{key}.hdf5")
    add_alias(alias + 'TotalSigma', NGAEastGMPETotalSigma,
              gmpe_table=f"NGAEast_{key}.hdf5")


# Coefficients for the linear model, taken from the electronic supplement
# to Stewart et al., (2017)
COEFFS_LINEAR = CoeffsTable(sa_damping=5, table="""\
imt           c      v1       v2      vf  sigma_vc  sigma_L  sigma_U
pgv      -0.449   331.0    760.0   314.0     0.251    0.306    0.334
pga      -0.290   319.0    760.0   345.0     0.300    0.345    0.480
0.010    -0.290   319.0    760.0   345.0     0.300    0.345    0.480
0.020    -0.303   319.0    760.0   343.0     0.290    0.336    0.479
0.030    -0.315   319.0    810.0   342.0     0.282    0.327    0.478
0.050    -0.344   319.0   1010.0   338.0     0.271    0.308    0.476
0.075    -0.348   319.0   1380.0   334.0     0.269    0.285    0.473
0.100    -0.372   317.0   1900.0   319.0     0.270    0.263    0.470
0.150    -0.385   302.0   1500.0   317.0     0.261    0.284    0.402
0.200    -0.403   279.0   1073.0   314.0     0.251    0.306    0.334
0.250    -0.417   250.0    945.0   282.0     0.238    0.291    0.357
0.300    -0.426   225.0    867.0   250.0     0.225    0.276    0.381
0.400    -0.452   217.0    843.0   250.0     0.225    0.275    0.381
0.500    -0.480   217.0    822.0   280.0     0.225    0.311    0.323
0.750    -0.510   227.0    814.0   280.0     0.225    0.330    0.310
1.000    -0.557   255.0    790.0   300.0     0.225    0.377    0.361
1.500    -0.574   276.0    805.0   300.0     0.242    0.405    0.375
2.000    -0.584   296.0    810.0   300.0     0.259    0.413    0.388
3.000    -0.588   312.0    820.0   313.0     0.306    0.410    0.551
4.000    -0.579   321.0    821.0   322.0     0.340    0.405    0.585
5.000    -0.558   324.0    825.0   325.0     0.340    0.409    0.587
7.500    -0.544   325.0    820.0   328.0     0.345    0.420    0.594
10.00    -0.507   325.0    820.0   330.0     0.350    0.440    0.600
""")

# Coefficients for the nonlinear model, taken from Table 2.1 of
# Hashash et al., (2017). The alternative f4 coefficients (f4_mod)
# are required for the US 2023 NSHMP and are taken from USGS repo:
# https://code.usgs.gov/ghsc/nshmp/nshmp-lib/-/blob/main/src/main/resources/gmm/coeffs/nga-east-usgs-siteamp.csv?ref_type=heads
COEFFS_NONLINEAR = CoeffsTable(sa_damping=5, table="""\
imt          f3         f4         f5     Vc   sigma_c  f4_mod
pgv     0.06089   -0.08344   -0.00667   2257.0   0.120  -0.08344
pga     0.07520   -0.43755   -0.00131   2990.0   0.120  -0.43755
0.010   0.07520   -0.43755   -0.00131   2990.0   0.120  -0.43755
0.020   0.05660   -0.41511   -0.00098   2990.0   0.120  -0.41511
0.030   0.10360   -0.49871   -0.00127   2990.0   0.120  -0.49871
0.050   0.16781   -0.58073   -0.00187   2990.0   0.120  -0.58073
0.075   0.17386   -0.53646   -0.00259   2990.0   0.120  -0.53646
0.100   0.15083   -0.44661   -0.00335   2990.0   0.120  -0.44661
0.150   0.14272   -0.38264   -0.00410   2335.0   0.120  -0.38264
0.200   0.12815   -0.30481   -0.00488   1533.0   0.120  -0.30481
0.250   0.13286   -0.27506   -0.00564   1318.0   0.135  -0.27506
0.300   0.13070   -0.22825   -0.00655   1152.0   0.150  -0.22825
0.400   0.09414   -0.11591   -0.00872   1018.0   0.150  -0.13060
0.500   0.09888   -0.07793   -0.01028    939.0   0.150  -0.09571
0.750   0.06101   -0.01780   -0.01456    835.0   0.125  -0.02909
1.000   0.04367   -0.00478   -0.01823    951.0   0.060  -0.01057
1.500   0.00480   -0.00086   -0.02000    882.0   0.050  -0.00253
2.000   0.00164   -0.00236   -0.01296    879.0   0.040  -0.00236
3.000   0.00746   -0.00626   -0.01043    894.0   0.040  -0.00626
4.000   0.00269   -0.00331   -0.01215    875.0   0.030  -0.00331
5.000   0.00242   -0.00256   -0.01325    856.0   0.020  -0.00256
7.500   0.04219   -0.00536   -0.01418    832.0   0.020  -0.00536
10.00   0.05329   -0.00631   -0.01403    837.0   0.020  -0.00631
    """)

# Note that the coefficient values at 0.1 s have been smoothed with respect
# to those needed in order to reproduce Figure 5 of Petersen et al. (2019)
# The original f760i was 0.674 +/- 0.366, and the values below are taken
# from the US NSHMP software
COEFFS_F760 = CoeffsTable(sa_damping=5, table="""\
imt       f760i     f760g   f760is   f760gs
pgv      0.3753     0.297    0.313    0.117
pga      0.1850     0.121    0.434    0.248
0.010    0.1850     0.121    0.434    0.248
0.020    0.1850     0.031    0.434    0.270
0.030    0.2240     0.000    0.404    0.229
0.050    0.3370     0.062    0.363    0.093
0.075    0.4750     0.211    0.322    0.102
0.100    0.5210     0.338    0.293    0.088
0.150    0.5860     0.470    0.253    0.066
0.200    0.4190     0.509    0.214    0.053
0.250    0.3320     0.509    0.177    0.052
0.300    0.2700     0.498    0.131    0.055
0.400    0.2090     0.473    0.112    0.060
0.500    0.1750     0.447    0.105    0.067
0.750    0.1270     0.386    0.138    0.077
1.000    0.0950     0.344    0.124    0.078
1.500    0.0830     0.289    0.112    0.081
2.000    0.0790     0.258    0.118    0.088
3.000    0.0730     0.233    0.111    0.100
4.000    0.0660     0.224    0.120    0.109
5.000    0.0640     0.220    0.108    0.115
7.500    0.0560     0.216    0.082    0.130
10.00    0.0530     0.218    0.069    0.137
""")

# Seven constants: vref, vL, vU, vw1, vw2, wt1 and wt2
CONSTANTS = {"vref": 760., "vL": 200., "vU": 2000.0,
             "vw1": 600.0, "vw2": 400.0, "wt1": 0.767, "wt2": 0.1}
