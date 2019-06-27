# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2019 GEM Foundation
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
Module exports :class:`NGAEastBaseGMPE`,
               :class:`NGAEastGMPE`,
               :class:`NGAEastBaseGMPETotalSigma`,
               :class:`NGAEastGMPETotalSigma`,
               :class:`Boore2015NGAEastA04`,
               :class:`Boore2015NGAEastA04TotalSigma`,
               :class:`Boore2015NGAEastAB14`,
               :class:`Boore2015NGAEastAB14TotalSigma`,
               :class:`Boore2015NGAEastAB95`,
               :class:`Boore2015NGAEastAB95TotalSigma`,
               :class:`Boore2015NGAEastBCA10D`,
               :class:`Boore2015NGAEastBCA10DTotalSigma`,
               :class:`Boore2015NGAEastBS11`,
               :class:`Boore2015NGAEastBS11TotalSigma`,
               :class:`Boore2015NGAEastSGD02`,
               :class:`Boore2015NGAEastSGD02TotalSigma`,
               :class:`DarraghEtAl2015NGAEast1CCSP`,
               :class:`DarraghEtAl2015NGAEast1CCSPTotalSigma`,
               :class:`DarraghEtAl2015NGAEast1CVSP`,
               :class:`DarraghEtAl2015NGAEast1CVSPTotalSigma`,
               :class:`DarraghEtAl2015NGAEast2CCSP`,
               :class:`DarraghEtAl2015NGAEast2CCSPTotalSigma`,
               :class:`DarraghEtAl2015NGAEast2CVSP`,
               :class:`DarraghEtAl2015NGAEast2CVSPTotalSigma`,
               :class:`YenierAtkinson2015NGAEast`,
               :class:`YenierAtkinson2015NGAEastTotalSigma`,
               :class:`PezeschkEtAl2015NGAEastM1SS`,
               :class:`PezeschkEtAl2015NGAEastM1SSTotalSigma`,
               :class:`PezeschkEtAl2015NGAEastM2ES`,
               :class:`PezeschkEtAl2015NGAEastM2ESTotalSigma`,
               :class:`Frankel2015NGAEast`,
               :class:`Frankel2015NGAEastTotalSigma`,
               :class:`ShahjoueiPezeschk2015NGAEast`,
               :class:`ShahjoueiPezeschk2015NGAEastTotalSigma`,
               :class:`AlNomanCramer2015NGAEast`,
               :class:`AlNomanCramer2015NGAEastTotalSigma`,
               :class:`Graizer2015NGAEast`,
               :class:`Graizer2015NGAEastTotalSigma`,
               :class:`HassaniAtkinson2015NGAEast`,
               :class:`HassaniAtkinson2015NGAEastTotalSigma`,
               :class:`HollenbackEtAl2015NGAEastGP`,
               :class:`HollenbackEtAl2015NGAEastGPTotalSigma`,
               :class:`HollenbackEtAl2015NGAEastEX`,
               :class:`HollenbackEtAl2015NGAEastEXTotalSigma`
"""
import os
import numpy as np
from copy import deepcopy
from scipy.stats import chi2
from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib.gsim.gmpe_table import GMPETable
from openquake.hazardlib import const


# Common interpolation function
def ITPL(mag, tu, tl, ml, f):
    return tl + (tu - tl) * ((mag - ml) / f)


def _scaling(mean_tau, sd_tau2):
    """
    Returns the chi-2 scaling factor from the mean and variance of the
    uncertainty model, as reported in equation 5.4 of Al Atik (2015)
    """
    return (sd_tau2 ** 2.) / (2.0 * mean_tau ** 2.)


def _dof(mean_tau, sd_tau2):
    """
    Returns the degrees of freedom for the chi-2 distribution from the mean and
    variance of the uncertainty model, as reported in equation 5.5 of Al Atik
    (2015)
    """
    return (2.0 * mean_tau ** 4.) / (sd_tau2 ** 2.)


def _at_percentile(tau, var_tau, percentile):
    """
    Returns the value of the inverse chi-2 distribution at the given
    percentile from the mean and variance of the uncertainty model, as
    reported in equations 5.1 - 5.3 of Al Atik (2015)
    """
    assert (percentile >= 0.0) and (percentile <= 1.0)
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
    if imt.name == "PGV":
        C = params["PGV"]
    else:
        C = params["SA"]
    if mag > 6.5:
        return C["tau4"]
    elif (mag > 5.5) and (mag <= 6.5):
        return ITPL(mag, C["tau4"], C["tau3"], 5.5, 1.0)
    elif (mag > 5.0) and (mag <= 5.5):
        return ITPL(mag, C["tau3"], C["tau2"], 5.0, 0.5)
    elif (mag > 4.5) and (mag <= 5.0):
        return ITPL(mag, C["tau2"], C["tau1"], 4.5, 0.5)
    else:
        return C["tau1"]


def cena_constant_tau(imt, mag, params):
    """
    Returns the inter-event tau for the constant tau case
    """
    if imt.name == "PGV":
        return params["PGV"]["tau"]
    else:
        return params["SA"]["tau"]


def cena_tau(imt, mag, params):
    """
    Returns the inter-event standard deviation, tau, for the CENA case
    """
    if imt.name == "PGV":
        C = params["PGV"]
    else:
        C = params["SA"]
    if mag > 6.5:
        return C["tau3"]
    elif (mag > 5.5) and (mag <= 6.5):
        return ITPL(mag, C["tau3"], C["tau2"], 5.5, 1.0)
    elif (mag > 5.0) and (mag <= 5.5):
        return ITPL(mag, C["tau2"], C["tau1"], 5.0, 0.5)
    else:
        return C["tau1"]


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
                                    quantile)
                }
    return CoeffsTable(sa_damping=5., table=coeffs)


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
    return CoeffsTable(sa_damping=5., table=coeffs)


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
    if mag <= 5.0:
        phi = C["a"]
    elif mag > 6.5:
        phi = C["b"]
    else:
        phi = C["a"] + (mag - 5.0) * ((C["b"] - C["a"]) / 1.5)
    return phi


class NGAEastBaseGMPE(GMPETable):
    """
    A generalised base class for the implementation of a GMPE in which the
    mean values are determined from tables (input by the user) and the standard
    deviation model taken from Al Atik (2015). Should be common to all
    NGA East ground motion models.

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
    """
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set((const.StdDev.TOTAL,
                                                const.StdDev.INTER_EVENT,
                                                const.StdDev.INTRA_EVENT))

    def __init__(self, gmpe_table, tau_model="global", phi_model="global",
                 phi_s2ss_model=None, tau_quantile=None,
                 phi_ss_quantile=None, phi_s2ss_quantile=None):
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
        self._setup_standard_deviations(fle=None)
        super().__init__(gmpe_table=gmpe_table)

    def _setup_standard_deviations(self, fle):
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

    def get_mean_and_stddevs(self, sctx, rctx, dctx, imt, stddev_types):
        """
        Returns the mean and standard deviations
        """
        # Return Distance Tables
        imls = self._return_tables(rctx.mag, imt, "IMLs")
        # Get distance vector for the given magnitude
        idx = np.searchsorted(self.m_w, rctx.mag)
        dists = self.distances[:, 0, idx - 1]
        # Get mean and standard deviations
        mean = self._get_mean(imls, dctx, dists)
        nsites = getattr(dctx, self.distance_type).shape
        stddevs = self.get_stddevs(rctx.mag, imt, stddev_types, nsites)
        if self.amplification:
            # Apply amplification
            mean_amp, sigma_amp = self.amplification.get_amplification_factors(
                imt,
                sctx,
                rctx,
                getattr(dctx, self.distance_type),
                stddev_types)
            mean = np.log(mean) + np.log(mean_amp)
            for iloc in range(len(stddev_types)):
                stddevs[iloc] *= sigma_amp[iloc]
            return mean, stddevs
        else:
            return np.log(mean), stddevs

    def get_stddevs(self, mag, imt, stddev_types, num_sites):
        """
        Returns the standard deviations for either the ergodic or
        non-ergodic models
        """
        tau = self._get_tau(imt, mag)
        phi = self._get_phi(imt, mag)
        sigma = np.sqrt(tau ** 2. + phi ** 2.)
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(sigma + np.zeros(num_sites))
            elif stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(phi + np.zeros(num_sites))
            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(tau + np.zeros(num_sites))
        return stddevs

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


# For the total standard deviation model the magnitude boundaries depend on
# the model selected
MAG_LIMS_KEYS = {
    "cena": {"mag": [5.0, 5.5, 6.5], "keys": ["tau1", "tau2", "tau3"]},
    "cena_constant": {"mag": [np.inf], "keys": ["tau"]},
    "global": {"mag": [4.5, 5.0, 5.5, 6.5],
               "keys": ["tau1", "tau2", "tau3", "tau4"]}
    }


class NGAEastGMPE(NGAEastBaseGMPE):
    """
    For the "core" NGA East set the table is provided in the code in a
    subdirectory fixed to the path of the present file. The GMPE table option
    is therefore no longer needed
    """
    NGA_EAST_TABLE = ""

    def __init__(self, tau_model="global", phi_model="global",
                 phi_s2ss_model=None, tau_quantile=None,
                 phi_ss_quantile=None, phi_s2ss_quantile=None):
        if not self.NGA_EAST_TABLE:
            raise NotImplementedError("NGA East Fixed-Table GMPE requires "
                                      "input table")
        super().__init__(
            gmpe_table=self.NGA_EAST_TABLE,
            tau_model=tau_model, phi_model=phi_model,
            phi_s2ss_model=phi_s2ss_model, tau_quantile=tau_quantile,
            phi_ss_quantile=phi_ss_quantile,
            phi_s2ss_quantile=phi_s2ss_quantile)


class NGAEastBaseGMPETotalSigma(NGAEastBaseGMPE):
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
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set((const.StdDev.TOTAL,))

    def __init__(self, gmpe_table, tau_model="global", phi_model="global",
                 phi_s2ss_model=None, sigma_quantile=None):
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
        super().__init__(gmpe_table=gmpe_table,
                         tau_model=tau_model, phi_model=phi_model,
                         phi_s2ss_model=phi_s2ss_model, tau_quantile=None,
                         phi_ss_quantile=None, phi_s2ss_quantile=None)
        # Upon instantiation the TAU, PHI_SS, and PHI_S2SS objects contain
        # the mean values
        self.SIGMA = None
        self.magnitude_limits = []
        self.tau_keys = []
        self._get_sigma_at_quantile(sigma_quantile)

    def get_stddevs(self, mag, imt, stddev_types, num_sites):
        """
        Returns the total standard deviation
        """
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                sigma = self._get_total_sigma(imt, mag)
                stddevs.append(sigma + np.zeros(num_sites))
        return stddevs

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
                PHI_S2SS_MODEL[self.phi_s2ss_model].non_sa_coeffs.keys())
            imt_list += \
                list(PHI_S2SS_MODEL[self.phi_s2ss_model].sa_coeffs.keys())
        else:
            imt_list = phi_std.keys()
        phi_std = CoeffsTable(sa_damping=5, table=phi_std)
        tau_bar, tau_std = self._get_tau_vector(self.TAU, tau_std, imt_list)
        phi_bar, phi_std = self._get_phi_vector(self.PHI_SS, phi_std, imt_list)
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
                    sigma[imt][new_key] =\
                        _at_percentile(sigma_bar, sigma_std, sigma_quantile)
                else:
                    sigma[imt][new_key] = sigma_bar
                self.tau_keys[i] = new_key
        self.SIGMA = CoeffsTable(sa_damping=5, table=sigma)

    def _get_tau_vector(self, tau_mean, tau_std, imt_list):
        """
        Gets the vector of mean and variance of tau values corresponding to
        the specific model and returns them as dictionaries
        """
        self.magnitude_limits = MAG_LIMS_KEYS[self.tau_model]["mag"]
        self.tau_keys = MAG_LIMS_KEYS[self.tau_model]["keys"]
        t_bar = {}
        t_std = {}
        for imt in imt_list:
            t_bar[imt] = []
            t_std[imt] = []
            for mag, key in zip(self.magnitude_limits, self.tau_keys):
                t_bar[imt].append(
                    TAU_EXECUTION[self.tau_model](imt, mag, tau_mean))
                t_std[imt].append(
                    TAU_EXECUTION[self.tau_model](imt, mag, tau_std))
        return t_bar, t_std

    def _get_phi_vector(self, phi_mean, phi_std, imt_list):
        """
        Gets the vector of mean and variance of phi values corresponding to
        the specific model and returns them as dictionaries
        """
        p_bar = {}
        p_std = {}

        for imt in imt_list:
            p_bar[imt] = []
            p_std[imt] = []
            for mag in self.magnitude_limits:
                phi_ss_mean = get_phi_ss(imt, mag, phi_mean)
                phi_ss_std = get_phi_ss(imt, mag, phi_std)
                if self.ergodic:
                    # Add on the phi_s2ss term according to Eqs. 5.15 and 5.16
                    # of Al Atik (2015)
                    phi_ss_mean = np.sqrt(
                        phi_ss_mean ** 2. +
                        PHI_S2SS_MODEL[self.phi_s2ss_model][imt]["mean"] ** 2.
                        )
                    phi_ss_std = np.sqrt(
                        phi_ss_std ** 2. +
                        PHI_S2SS_MODEL[self.phi_s2ss_model][imt]["var"] ** 2.
                        )
                p_bar[imt].append(phi_ss_mean)
                p_std[imt].append(phi_ss_std)
        return p_bar, p_std

    def _get_total_sigma(self, imt, mag):
        """
        Returns the estimated total standard deviation for a given intensity
        measure type and magnitude
        """
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


class NGAEastGMPETotalSigma(NGAEastBaseGMPETotalSigma):
    """
    Subclass of the :class:`NGAEastBaseGMPETotalSigma` for the cases when the
    GMPE table is fixed. This forms the main base-class for the total sigma
    version of the core set of NGA East models
    """
    NGA_EAST_TABLE = ""

    def __init__(self, tau_model="global", phi_model="global",
                 phi_s2ss_model=None, sigma_quantile=None):
        """
        Instantiates the GMPE without the hdf5 table fort the median values
        """
        if not self.NGA_EAST_TABLE:
            raise NotImplementedError("NGA East Fixed-Table GMPE requires "
                                      "input table")
        super().__init__(
            self.NGA_EAST_TABLE, tau_model=tau_model, phi_model=phi_model,
            phi_s2ss_model=phi_s2ss_model, sigma_quantile=sigma_quantile)


# /////////////////////////////////////////////////////////////////////////////
# Now to start adding the actual NGA East GMPEs
# /////////////////////////////////////////////////////////////////////////////
BASE_PATH = os.path.join(os.path.dirname(__file__), "nga_east_tables")


# Boore (2015) suite


class Boore2015NGAEastA04(NGAEastGMPE):
    """
    Boore (2015) NGA East GMPE using the Atkinson (2004) attenuation model

    Boore, DM (2015) "Point-Source Stochastic-Method Simulations of
    Ground Motions for the PEER NGA-East Project", in "NGA-East: Median
    Ground Motion Models for the Central and Eastern North America Region",
    PEER Report 2015/04, Pacific Earthquake Engineering Research Center
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_BOORE_A04_J15_Adjusted.hdf5")


class Boore2015NGAEastA04TotalSigma(NGAEastGMPETotalSigma):
    """
    Boore (2015) NGA East GMPE using the Atkinson (2004) attenuation model
    for use with the total sigma aleatory uncertainty model
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_BOORE_A04_J15_Adjusted.hdf5")


class Boore2015NGAEastAB14(NGAEastGMPE):
    """
    Boore (2015) NGA East GMPE using the Atkinson & Boore (2014) attenuation
    model
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_BOORE_AB14_J15_Adjusted.hdf5")


class Boore2015NGAEastAB14TotalSigma(NGAEastGMPETotalSigma):
    """
    Boore (2015) NGA East GMPE using the Atkinson & Boore (2014) attenuation
    model for use with the total sigma aleatory uncertainty model
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_BOORE_AB14_J15_Adjusted.hdf5")


class Boore2015NGAEastAB95(NGAEastGMPE):
    """
    Boore (2015) NGA East GMPE using the Atkinson & Boore (1995) attenuation
    model
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_BOORE_AB95_J15_Adjusted.hdf5")


class Boore2015NGAEastAB95TotalSigma(NGAEastGMPETotalSigma):
    """
    Boore (2015) NGA East GMPE using the Atkinson & Boore (1995) attenuation
    model for use with the total sigma aleatory uncertainty model
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_BOORE_AB95_J15_Adjusted.hdf5")


class Boore2015NGAEastBCA10D(NGAEastGMPE):
    """
    Boore (2015) NGA East GMPE using the Boore et al (2010) attenuation
    model
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_BOORE_BCA10D_J15_Adjusted.hdf5")


class Boore2015NGAEastBCA10DTotalSigma(NGAEastGMPETotalSigma):
    """
    Boore (2015) NGA East GMPE using the Boore et al (2010) attenuation
    model for use with the total sigma aleatory uncertainty model
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_BOORE_BCA10D_J15_Adjusted.hdf5")


class Boore2015NGAEastBS11(NGAEastGMPE):
    """
    Boore (2015) NGA East GMPE using the Boatwright and Seekins (2011)
    attenuation model
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_BOORE_BS11_J15_Adjusted.hdf5")


class Boore2015NGAEastBS11TotalSigma(NGAEastGMPETotalSigma):
    """
    Boore (2015) NGA East GMPE using the Boatwright and Seekins (2011)
    attenuation model for use with the total sigma aleatory uncertainty model
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_BOORE_BS11_J15_Adjusted.hdf5")


class Boore2015NGAEastSGD02(NGAEastGMPE):
    """
    Boore (2015) NGA East GMPE using the Silva et al (2002) attenuation model
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_BOORE_SGD02_J15_Adjusted.hdf5")


class Boore2015NGAEastSGD02TotalSigma(NGAEastGMPETotalSigma):
    """
    Boore (2015) NGA East GMPE using the Silva et al (2002) attenuation model
    for use with the total sigma aleatory uncertainty model
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_BOORE_SGD02_J15_Adjusted.hdf5")


# Darragh, Abrahamson, Silva and Gregor (2015) suite

class DarraghEtAl2015NGAEast1CCSP(NGAEastGMPE):
    """
    NGA East model of Darragh et al. (2015) adopting the single-corner
    constant stress parameter (1CCSP)

    Darragh, RB, Abrahamson, NA, Wilva, WJ, Gregor, N (2015) "Development of
    Hard Rock Ground Motion Models for Region 2 of Central and Eastern
    North America" in ...
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_DARRAGH_1CCSP.hdf5")


class DarraghEtAl2015NGAEast1CCSPTotalSigma(NGAEastGMPETotalSigma):
    """
    NGA East model of Darragh et al. (2015) adopting the single-corner
    constant stress parameter (1CCSP) for use with the total sigma aleatory
    uncertainty model
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_DARRAGH_1CCSP.hdf5")


class DarraghEtAl2015NGAEast1CVSP(NGAEastGMPE):
    """
    NGA East model of Darragh et al. (2015) adopting the single-corner
    variable stress parameter (1CVSP)
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_DARRAGH_1CVSP.hdf5")


class DarraghEtAl2015NGAEast1CVSPTotalSigma(NGAEastGMPETotalSigma):
    """
    NGA East model of Darragh et al. (2015) adopting the single-corner
    variable stress parameter (1CVSP) for use with the total sigma aleatory
    uncertainty model
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_DARRAGH_1CVSP.hdf5")


class DarraghEtAl2015NGAEast2CCSP(NGAEastGMPE):
    """
    NGA East model of Darragh et al. (2015) adopting the two-corner
    constant stress parameter (2CCSP)
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_DARRAGH_2CCSP.hdf5")


class DarraghEtAl2015NGAEast2CCSPTotalSigma(NGAEastGMPETotalSigma):
    """
    NGA East model of Darragh et al. (2015) adopting the two-corner
    constant stress parameter (2CCSP) for use with the total sigma aleatory
    uncertainty model
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_DARRAGH_2CCSP.hdf5")


class DarraghEtAl2015NGAEast2CVSP(NGAEastGMPE):
    """
    NGA East model of Darragh et al. (2015) adopting the two-corner
    variable stress parameter (1CVSP)
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_DARRAGH_2CVSP.hdf5")


class DarraghEtAl2015NGAEast2CVSPTotalSigma(NGAEastGMPETotalSigma):
    """
    NGA East model of Darragh et al. (2015) adopting the two-corner
    variable stress parameter (2CVSP) for use with the total sigma aleatory
    uncertainty model
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_DARRAGH_2CVSP.hdf5")

# Yenier & Atkinson (2015)


class YenierAtkinson2015NGAEast(NGAEastGMPE):
    """
    NGA East Model of Yenier & Atkinson (2015)
    Yenier, E and Atkinson, GA (2015) "Regionally-Adjustable Generic Ground-
    Motion Prediction Equation based on Equivalent Point-Source Simulations:
    Application to Central and Eastern North America" in PEER 2015/04, Chapter
    4
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_YENIER_ATKINSON.hdf5")


class YenierAtkinson2015NGAEastTotalSigma(NGAEastGMPETotalSigma):
    """
    NGA East Model of Yenier & Atkinson (2015) for use with the total sigma
    aleatory uncertainty model
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_YENIER_ATKINSON.hdf5")


# Pezeschk et al. (2015)


class PezeschkEtAl2015NGAEastM1SS(NGAEastGMPE):
    """
    NGA East Model of Pezeschk et al (2015) for the large-M simulation scaling

    Pezeschk, S., Zandieh, A., Campbell, KW and Tavakoli B (2015) "Ground-
    Motion Prediction Equations for Eastern North America using a Hybrid
    Empirical Method" in PEER 2015/04, Chapter 5
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_PEZESCHK_M1SS.hdf5")


class PezeschkEtAl2015NGAEastM1SSTotalSigma(NGAEastGMPETotalSigma):
    """
    NGA East Model of Pezeschk et al (2015) for the large-M simulation scaling
    for use with the total sigma aleatory uncertainty model
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_PEZESCHK_M1SS.hdf5")


class PezeschkEtAl2015NGAEastM2ES(NGAEastGMPE):
    """
    NGA East Model of Pezeschk et al (2015) for the large-M empirical scaling
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_PEZESCHK_M2ES.hdf5")


class PezeschkEtAl2015NGAEastM2ESTotalSigma(NGAEastGMPETotalSigma):
    """
    NGA East Model of Pezeschk et al (2015) for the large-M empirical scaling
    for use with the total sigma aleatory uncertainty model
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_PEZESCHK_M2ES.hdf5")

# Frankel (2015)


class Frankel2015NGAEast(NGAEastGMPE):
    """
    NGA East Model of Frankel (2015) for application to Central & Eastern
    United States

    Frankel, A (2015) "Ground-Motion Predictions for Eastern North American
    Earthquakes Using Hybrid Broadband Seismograms from Finite-Fault
    Simulation with Constant Stress-Drop Scaling" in PEER 2015/04, Chapter 6
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_FRANKEL_J15.hdf5")


class Frankel2015NGAEastTotalSigma(NGAEastGMPETotalSigma):
    """
    NGA East Model of Frankel (2015) for application to Central & Eastern
    United States for use with the total sigma aleatory uncertainty model
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_FRANKEL_J15.hdf5")

# Shahjouei & Pezeschk (2015)


class ShahjoueiPezeschk2015NGAEast(NGAEastGMPE):
    """
    NGA East Model of Shahjouei & Pezeschk (2015) for application to Central &
    Eastern United States

    Shajouei, A and Pezeschk, S (2015) "Hybrid Empirical Ground-Motion Model
    for Central and Eastern North America using Hybrid Broadband Simulations
    and NGA-West2 GMPEs" in PEER 2015/04, Chapter 7
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_SHAHJOUEI_PEZESCHK.hdf5")


class ShahjoueiPezeschk2015NGAEastTotalSigma(NGAEastGMPETotalSigma):
    """
    NGA East Model of Shahjouei & Pezeschk (2015) for application to Central &
    Eastern United States, for use with the total sigma aleatory uncertainty
    model
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_SHAHJOUEI_PEZESCHK.hdf5")

# Al Noman and Cramer (2015)


class AlNomanCramer2015NGAEast(NGAEastGMPE):
    """
    NGA East Model of Al Noman & Cramer (2015) for application to Central &
    Eastern United States

    Al Noman & Cramer (2015) "Empirical Ground-Motion Prediction Equations for
    Eastern North America" in PEER 2015/04, Chapter 8
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_ALNOMAN_CRAMER.hdf5")


class AlNomanCramer2015NGAEastTotalSigma(NGAEastGMPETotalSigma):
    """
    NGA East Model of Al Noman & Cramer (2015) for application to Central &
    Eastern United States, for use with the total sigma aleatory uncertainty
    model
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_ALNOMAN_CRAMER.hdf5")

# Graizer (2015)


class Graizer2015NGAEast(NGAEastGMPE):
    """
    NGA East Model of Graizer (2015) for application to Central & Eastern
    United States

    Graizer, V (2015) "Ground-Motion Prediction Equations for the Central and
    Eastern United States" in PEER 2015/04, Chapter 9
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_GRAIZER.hdf5")


class Graizer2015NGAEastTotalSigma(NGAEastGMPETotalSigma):
    """
    NGA East Model of Graizer (2015) for application to Central & Eastern
    United States, for use with the total sigma aleatory uncertainty
    model
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_GRAIZER.hdf5")

# Hassani & Atkinson (2015)


class HassaniAtkinson2015NGAEast(NGAEastGMPE):
    """
    NGA East Model of Hassani & Atkinson (2015) for application to Central &
    Eastern United States

    Hassani, B & Atkinson, GA (2015) "Referenced Empirical Ground-Motion Model
    for Eastern North America" in PEER 2015/04, Chapter 10
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_HASSANI_ATKINSON.hdf5")


class HassaniAtkinson2015NGAEastTotalSigma(NGAEastGMPETotalSigma):
    """
    NGA East Model of Hassani & Atkinson (2015) for application to Central &
    Eastern United States, for use with the total sigma aleatory uncertainty
    model
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_HASSANI_ATKINSON.hdf5")

# Hollenback et al. (2015)


class HollenbackEtAl2015NGAEastGP(NGAEastGMPE):
    """
    NGA East Model of Hollenback et al (2015) for application to Central &
    Eastern United States using the GP Finite-Fault model

    Hollenback, J, Keuhn, N, Goulet, CA and Abrahamson, NA (2015) "PEER NGA-
    East Median Ground Motion Models" in PEER 2015/04, Chapter 11
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_PEER_GP.hdf5")


class HollenbackEtAl2015NGAEastGPTotalSigma(NGAEastGMPETotalSigma):
    """
    NGA East Model of Hollenback et al (2015) for application to Central &
    Eastern United States, for use with the total sigma aleatory uncertainty
    model
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_PEER_GP.hdf5")


class HollenbackEtAl2015NGAEastEX(NGAEastGMPE):
    """
    NGA East Model of Hollenback et al (2015) for application to Central &
    Eastern United States using the EXSIM Finite-Fault model

    Hollenback, J, Keuhn, N, Goulet, CA and Abrahamson, NA (2015) "PEER NGA-
    East Median Ground Motion Models" in PEER 2015/04, Chapter 11
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_PEER_EX.hdf5")


class HollenbackEtAl2015NGAEastEXTotalSigma(NGAEastGMPETotalSigma):
    """
    NGA East Model of Hollenback et al (2015) for application to Central &
    Eastern United States, for use with the total sigma aleatory uncertainty
    model
    """
    NGA_EAST_TABLE = os.path.join(BASE_PATH,
                                  "NGAEast_PEER_EX.hdf5")
