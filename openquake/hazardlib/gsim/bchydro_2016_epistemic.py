# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2018 GEM Foundation
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

import numpy as np
from scipy.special import erf
from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib.gsim.abrahamson_2015 import (
    AbrahamsonEtAl2015SInter, AbrahamsonEtAl2015SInterLow,
    AbrahamsonEtAl2015SInterHigh, AbrahamsonEtAl2015SSlab,
    AbrahamsonEtAl2015SSlabLow, AbrahamsonEtAl2015SSlabHigh)


# Total epistemic uncertainty factors from Abrahamson et al. (2018)
BCHYDRO_SIGMA_MU = CoeffsTable(sa_damping=5, table="""
    imt     SIGMA_MU_SINTER    SIGMA_MU_SSLAB
    pga                 0.3              0.50
    0.010               0.3              0.50
    0.020               0.3              0.50
    0.030               0.3              0.50
    0.050               0.3              0.50
    0.075               0.3              0.50
    0.100               0.3              0.50
    0.150               0.3              0.50
    0.200               0.3              0.50
    0.250               0.3              0.46
    0.300               0.3              0.42
    0.400               0.3              0.38
    0.500               0.3              0.34
    0.600               0.3              0.30
    0.750               0.3              0.30
    1.000               0.3              0.30
    1.500               0.3              0.30
    2.000               0.3              0.30
    2.500               0.3              0.30
    3.000               0.3              0.30
    4.000               0.3              0.30
    5.000               0.3              0.30
    6.000               0.3              0.30
    7.500               0.3              0.30
    10.00               0.3              0.30
    """)


def get_stress_factor(imt, slab=False):
    """
    Returns the stress adjustment factor for the BC Hydro GMPE according to
    Abrahamson et al. (2018)
    """
    if slab:
        sigma_mu = BCHYDRO_SIGMA_MU[imt]["SIGMA_MU_SSLAB"]
    else:
        sigma_mu = BCHYDRO_SIGMA_MU[imt]["SIGMA_MU_SINTER"]
    return sigma_mu / 1.65


class FABATaperStep(object):
    """
    General class for a tapering function, in this case
    a step function such that the backarc scaling term takes 0 for
    forearc sites (negative backarc distance), and 1 for backarc sites
    (positive backarc distance)
    """
    def __init__(self, **kwargs):
        """
        Instantiates the class with any required arguments controlling the
        shape of the taper (none in the case of the current step taper). As
        the range of possible parameters take different meanings and default
        values in the subclasses of the function an indefinite set of inputs
        (**kwargs) is used rather than an explicit parameter list. The
        definition of parameters used within each subclass can be found in the
        respective subclass documentation strings.
        """
        pass

    def __call__(self, x):
        """
        :param numpy.ndarray x:
            Independent variable.

        Returns
        -------
        :param numpy.ndarray y:
            Backarc scaling term
        """
        y = np.zeros(x.shape)
        y[x > 0.0] = 1.
        return y


class FABATaperSFunc(FABATaperStep):
    """
    Implements tapering of x according to a S-function
    (Named such because of its S-like shape.)

    :param float a:
        'ceiling', where the function begins falling from 1.
    :param float b:
        'floor', where the function reaches zero.
    """
    def __init__(self, **kwargs):
        super().__init__()
        self.a = kwargs.get("a", 0.0)
        self.b = kwargs.get("b", 0.0)
        # a must be less than or equal to b
        assert self.a <= self.b

    def __call__(self, x):
        """
        Returns
        -------
        :param numpy.ndarray y:
            Backarc scaling term
        """
        y = np.ones(x.shape)
        idx = x <= self.a
        y[idx] = 0

        idx = np.logical_and(self.a <= x, x <= (self.a + self.b) / 2.)
        y[idx] = 2. * ((x[idx] - self.a) / (self.b - self.a)) ** 2.

        idx = np.logical_and((self.a + self.b) / 2. <= x, x <= self.b)
        y[idx] = 1 - 2. * ((x[idx] - self.b) / (self.b - self.a)) ** 2.
        return y


class FABATaperLinear(FABATaperStep):
    """
    Implements a tapering of x according to a linear function
    with a fixed distance and a midpoint (y = 0.5) at x = 0

    :param float width:
        Distance (km) across which x tapers to 0
    """
    def __init__(self, **kwargs):
        super().__init__()
        self.width = kwargs.get("width", 1.0)
        # width must be greater than 0
        assert self.width > 0.0

    def __call__(self, x):
        """
        Returns
        -------
        :param numpy.ndarray y:
            Backarc scaling term
        """
        upper = self.width / 2.
        lower = -self.width / 2.
        y = (x - lower) / (upper - lower)
        y[x > upper] = 1.
        y[x < lower] = 0.
        return y


class FABATaperSigmoid(FABATaperStep):
    """
    Implements tapering of x according to a sigmoid function
    (Note that this only tends to 1, 0 it does not reach it)

    :param float c: Bandwidth in km of the sigmoid function
    """
    def __init__(self, **kwargs):
        super().__init__()
        self.c = kwargs.get("c", 1.0)
        # sigmoid function bandwidth must be greater than zero
        assert self.c > 0.

    def __call__(self, x):
        """
        Returns
        -------
        :param numpy.ndarray y:
            Backarc scaling term
        """
        return 1. / (1. + np.exp(-(1. / self.c) * x))


# Get Gaussian cdf of a standard normal distribution
phix = lambda x: 0.5 * (1.0 + erf(x / np.sqrt(2.)))


class FABATaperGaussian(FABATaperStep):
    """
    Implements tapering of x according to a truncated Gaussian function

    :param float sigma:
        Bandwidth of function (according to a Gaussian standard deviation)
    :param float a:
        Initiation point of tapering (km)
    :param float b:
        Termination point of tapering (km)
    """
    def __init__(self, **kwargs):

        super().__init__()
        self.sigma = kwargs.get("sigma", 1.0)
        a = kwargs.get("a", -np.inf)
        b = kwargs.get("b", np.inf)
        # Gaussian sigma must be positive non-zero and upper bound must be
        # greater than or equal to the lower bound
        assert self.sigma > 0
        assert b >= a
        self.phi_a = phix(a / self.sigma)
        self.phi_diff = phix(b / self.sigma) - self.phi_a

    def __call__(self, x):
        """
        Returns
        -------
        :param numpy.ndarray y:
            Backarc scaling term
        """
        y = (phix(x / self.sigma) - self.phi_a) / self.phi_diff
        y[y < 0.] = 0.
        y[y > 1.] = 1.
        return y


FABA_ALL_MODELS = {
    "Step": FABATaperStep,
    "Linear": FABATaperLinear,
    "SFunc": FABATaperSFunc,
    "Sigmoid": FABATaperSigmoid,
    "Gaussian": FABATaperGaussian
}


class BCHydroESHM20SInter(AbrahamsonEtAl2015SInter):
    """
    ESHM20 adjustment of the BC Hydro GMPE for subduction interface events with
    theta6 calibrated to Mediterranean data.

    Introduces several configurable parameters:

    :param float theta6_adjustment:
        The amount to increase or decrease the theta6 - should be +0.0015 (for
        slower attenuation) and -0.0015 (for faster attenuation)

    :param float sigma_mu_epsilon:
        The number of standard deviations above or below the mean to apply the
        statistical uncertainty sigma_mu term.

    :param faba_model:
        Choice of model for the forearc/backarc tapering function, choice of
        {"Step", "Linear", "SFunc", "Sigmoid", "Gaussian"}

    Depending on the choice of taper model, additional parameters may be passed
    """
    experimental = True

    # Requires Vs30 and distance to the volcanic front
    REQUIRES_SITES_PARAMETERS = set(('vs30', 'xvf'))

    def __init__(self, **kwargs):
        super().__init__(ergodic=kwargs.get("ergodic", True), **kwargs)
        self.theta6_adj = kwargs.get("theta6_adjustment", 0.0)
        self.sigma_mu_epsilon = kwargs.get("sigma_mu_epsilon", 0.0)
        faba_type = kwargs.get("faba_taper_model", "Step")
        self.faba_model = FABA_ALL_MODELS[faba_type](**kwargs)

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        Returns mean and stddevs applying the statistical uncertainty if
        needed
        """
        mean, stddevs = super().get_mean_and_stddevs(sites, rup, dists, imt,
                                                     stddev_types)
        if self.sigma_mu_epsilon:
            sigma_mu = get_stress_factor(imt, slab=False)
            return mean + (sigma_mu * self.sigma_mu_epsilon), stddevs
        else:
            return mean, stddevs

    def _compute_distance_term(self, C, mag, dists):
        """
        Computes the distance scaling term, as contained within equation (1)
        """
        return (C['theta2'] + self.CONSTS['theta3'] * (mag - 7.8)) *\
            np.log(dists.rrup + self.CONSTS['c4'] * np.exp((mag - 6.) *
                   self.CONSTS['theta9'])) +\
            ((self.theta6_adj + C['theta6']) * dists.rrup)

    def _compute_forearc_backarc_term(self, C, sites, dists):
        """
        Computes the forearc/backarc scaling term given by equation (4)
        """
        max_dist = np.copy(dists.rrup)
        max_dist[max_dist < 100.0] = 100.0
        f_faba = C['theta15'] + (C['theta16'] * np.log(max_dist / 40.0))
        return f_faba * self.faba_model(-sites.xvf)

    COEFFS = CoeffsTable(sa_damping=5, table="""\
    imt          vlin        b   theta1    theta2        theta6    theta7    theta8  theta10  theta11   theta12   theta13   theta14  theta15   theta16      phi     tau   sigma  sigma_ss
    pga      865.1000  -1.1860   4.2203   -1.3500   -0.00721467    1.0988   -1.4200   3.1200   0.0130    0.9800   -0.0135   -0.4000   0.9969   -1.0000   0.6000  0.4300  0.7400    0.6000
    0.0200   865.1000  -1.1860   4.2203   -1.3500   -0.00719296    1.0988   -1.4200   3.1200   0.0130    0.9800   -0.0135   -0.4000   0.9969   -1.0000   0.6000  0.4300  0.7400    0.6000
    0.0500  1053.5000  -1.3460   4.5371   -1.4000   -0.00712619    1.2536   -1.6500   3.3700   0.0130    1.2880   -0.0138   -0.4000   1.1030   -1.1800   0.6000  0.4300  0.7400    0.6000
    0.0750  1085.7000  -1.4710   5.0733   -1.4500   -0.00701600    1.4175   -1.8000   3.3700   0.0130    1.4830   -0.0142   -0.4000   1.2732   -1.3600   0.6000  0.4300  0.7400    0.6000
    0.1000  1032.5000  -1.6240   5.2892   -1.4500   -0.00687258    1.3997   -1.8000   3.3300   0.0130    1.6130   -0.0145   -0.4000   1.3042   -1.3600   0.6000  0.4300  0.7400    0.6000
    0.1500   877.6000  -1.9310   5.4563   -1.4500   -0.00671633    1.3582   -1.6900   3.2500   0.0130    1.8820   -0.0153   -0.4000   1.2600   -1.3000   0.6000  0.4300  0.7400    0.6000
    0.2000   748.2000  -2.1880   5.2684   -1.4000   -0.00657867    1.1648   -1.4900   3.0300   0.0129    2.0760   -0.0162   -0.3500   1.2230   -1.2500   0.6000  0.4300  0.7400    0.6000
    0.2500   654.3000  -2.3810   5.0594   -1.3500   -0.00648602    0.9940   -1.3000   2.8000   0.0129    2.2480   -0.0172   -0.3100   1.1600   -1.1700   0.6000  0.4300  0.7400    0.6000
    0.3000   587.1000  -2.5180   4.7945   -1.2800   -0.00643709    0.8821   -1.1800   2.5900   0.0128    2.3480   -0.0183   -0.2800   1.0500   -1.0600   0.6000  0.4300  0.7400    0.6000
    0.4000   503.0000  -2.6570   4.4644   -1.1800   -0.00639138    0.7046   -0.9800   2.2000   0.0127    2.4270   -0.0206   -0.2300   0.8000   -0.7800   0.6000  0.4300  0.7400    0.6000
    0.5000   456.6000  -2.6690   4.0181   -1.0800   -0.00629147    0.5799   -0.8200   1.9200   0.0125    2.3990   -0.0231   -0.1900   0.6620   -0.6200   0.6000  0.4300  0.7400    0.6000
    0.6000   430.3000  -2.5990   3.6055   -0.9900   -0.00609857    0.5021   -0.7000   1.7000   0.0124    2.2730   -0.0256   -0.1600   0.5800   -0.5000   0.6000  0.4300  0.7400    0.6000
    0.7500   410.5000  -2.4010   3.2174   -0.9100   -0.00581454    0.3687   -0.5400   1.4200   0.0120    1.9930   -0.0296   -0.1200   0.4800   -0.3400   0.6000  0.4300  0.7400    0.6000
    1.0000   400.0000  -1.9550   2.7981   -0.8500   -0.00548905    0.1746   -0.3400   1.1000   0.0114    1.4700   -0.0363   -0.0700   0.3300   -0.1400   0.6000  0.4300  0.7400    0.6000
    1.5000   400.0000  -1.0250   2.0123   -0.7700   -0.00520499   -0.0820   -0.0500   0.7000   0.0100    0.4080   -0.0493    0.0000   0.3100    0.0000   0.6000  0.4300  0.7400    0.6000
    2.0000   400.0000  -0.2990   1.4128   -0.7100   -0.00505022   -0.2821    0.1200   0.7000   0.0085   -0.4010   -0.0610    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    2.5000   400.0000   0.0000   0.9976   -0.6700   -0.00507967   -0.4108    0.2500   0.7000   0.0069   -0.7230   -0.0711    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    3.0000   400.0000   0.0000   0.6443   -0.6400   -0.00529221   -0.4466    0.3000   0.7000   0.0054   -0.6730   -0.0798    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    4.0000   400.0000   0.0000   0.0657   -0.5800   -0.00564790   -0.4344    0.3000   0.7000   0.0027   -0.6270   -0.0935    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    5.0000   400.0000   0.0000  -0.4624   -0.5400   -0.00607621   -0.4368    0.3000   0.7000   0.0005   -0.5960   -0.0980    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    6.0000   400.0000   0.0000  -0.9809   -0.5000   -0.00647922   -0.4586    0.3000   0.7000  -0.0013   -0.5660   -0.0980    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    7.5000   400.0000   0.0000  -1.6017   -0.4600   -0.00676355   -0.4433    0.3000   0.7000  -0.0033   -0.5280   -0.0980    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    10.0000  400.0000   0.0000  -2.2937   -0.4000   -0.00686566   -0.4828    0.3000   0.7000  -0.0060   -0.5040   -0.0980    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    """)


class BCHydroESHM20SInterLow(AbrahamsonEtAl2015SInterLow):
    """
    ESHM20 Adjustment of the BC Hydro GMPE for subduction interface events
    with theta6 calibrated to Mediterranean data, for the low magnitude
    scaling branch.
    """
    experimental = True
    # Requires Vs30 and distance to the volcanic front
    REQUIRES_SITES_PARAMETERS = set(('vs30', 'xvf'))

    def __init__(self, **kwargs):
        super().__init__(ergodic=kwargs.get("ergodic", True), **kwargs)
        self.theta6_adj = kwargs.get("theta6_adjustment", 0.0)
        self.sigma_mu_epsilon = kwargs.get("sigma_mu_epsilon", 0.0)
        faba_type = kwargs.get("faba_taper_model", "Step")
        self.faba_model = FABA_ALL_MODELS[faba_type](**kwargs)

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        Returns mean and stddevs applying the statistical uncertainty if
        needed
        """
        mean, stddevs = super().get_mean_and_stddevs(sites, rup, dists, imt,
                                                     stddev_types)
        if self.sigma_mu_epsilon:
            sigma_mu = get_stress_factor(imt, slab=False)
            return mean + (sigma_mu * self.sigma_mu_epsilon), stddevs
        else:
            return mean, stddevs

    def _compute_distance_term(self, C, mag, dists):
        """
        Computes the distance scaling term, as contained within equation (1)
        """
        return (C['theta2'] + self.CONSTS['theta3'] * (mag - 7.8)) *\
            np.log(dists.rrup + self.CONSTS['c4'] * np.exp((mag - 6.) *
                   self.CONSTS['theta9'])) +\
            ((self.theta6_adj + C['theta6']) * dists.rrup)

    def _compute_forearc_backarc_term(self, C, sites, dists):
        """
        Computes the forearc/backarc scaling term given by equation (4)
        """
        max_dist = np.copy(dists.rrup)
        max_dist[max_dist < 100.0] = 100.0
        f_faba = C['theta15'] + (C['theta16'] * np.log(max_dist / 40.0))
        return f_faba * self.faba_model(-sites.xvf)

    COEFFS = CoeffsTable(sa_damping=5, table="""\
    imt          vlin        b   theta1    theta2        theta6    theta7    theta8  theta10  theta11   theta12   theta13   theta14  theta15   theta16      phi     tau   sigma  sigma_ss
    pga      865.1000  -1.1860   4.2203   -1.3500   -0.00721467    1.0988   -1.4200   3.1200   0.0130    0.9800   -0.0135   -0.4000   0.9969   -1.0000   0.6000  0.4300  0.7400    0.6000
    0.0200   865.1000  -1.1860   4.2203   -1.3500   -0.00719296    1.0988   -1.4200   3.1200   0.0130    0.9800   -0.0135   -0.4000   0.9969   -1.0000   0.6000  0.4300  0.7400    0.6000
    0.0500  1053.5000  -1.3460   4.5371   -1.4000   -0.00712619    1.2536   -1.6500   3.3700   0.0130    1.2880   -0.0138   -0.4000   1.1030   -1.1800   0.6000  0.4300  0.7400    0.6000
    0.0750  1085.7000  -1.4710   5.0733   -1.4500   -0.00701600    1.4175   -1.8000   3.3700   0.0130    1.4830   -0.0142   -0.4000   1.2732   -1.3600   0.6000  0.4300  0.7400    0.6000
    0.1000  1032.5000  -1.6240   5.2892   -1.4500   -0.00687258    1.3997   -1.8000   3.3300   0.0130    1.6130   -0.0145   -0.4000   1.3042   -1.3600   0.6000  0.4300  0.7400    0.6000
    0.1500   877.6000  -1.9310   5.4563   -1.4500   -0.00671633    1.3582   -1.6900   3.2500   0.0130    1.8820   -0.0153   -0.4000   1.2600   -1.3000   0.6000  0.4300  0.7400    0.6000
    0.2000   748.2000  -2.1880   5.2684   -1.4000   -0.00657867    1.1648   -1.4900   3.0300   0.0129    2.0760   -0.0162   -0.3500   1.2230   -1.2500   0.6000  0.4300  0.7400    0.6000
    0.2500   654.3000  -2.3810   5.0594   -1.3500   -0.00648602    0.9940   -1.3000   2.8000   0.0129    2.2480   -0.0172   -0.3100   1.1600   -1.1700   0.6000  0.4300  0.7400    0.6000
    0.3000   587.1000  -2.5180   4.7945   -1.2800   -0.00643709    0.8821   -1.1800   2.5900   0.0128    2.3480   -0.0183   -0.2800   1.0500   -1.0600   0.6000  0.4300  0.7400    0.6000
    0.4000   503.0000  -2.6570   4.4644   -1.1800   -0.00639138    0.7046   -0.9800   2.2000   0.0127    2.4270   -0.0206   -0.2300   0.8000   -0.7800   0.6000  0.4300  0.7400    0.6000
    0.5000   456.6000  -2.6690   4.0181   -1.0800   -0.00629147    0.5799   -0.8200   1.9200   0.0125    2.3990   -0.0231   -0.1900   0.6620   -0.6200   0.6000  0.4300  0.7400    0.6000
    0.6000   430.3000  -2.5990   3.6055   -0.9900   -0.00609857    0.5021   -0.7000   1.7000   0.0124    2.2730   -0.0256   -0.1600   0.5800   -0.5000   0.6000  0.4300  0.7400    0.6000
    0.7500   410.5000  -2.4010   3.2174   -0.9100   -0.00581454    0.3687   -0.5400   1.4200   0.0120    1.9930   -0.0296   -0.1200   0.4800   -0.3400   0.6000  0.4300  0.7400    0.6000
    1.0000   400.0000  -1.9550   2.7981   -0.8500   -0.00548905    0.1746   -0.3400   1.1000   0.0114    1.4700   -0.0363   -0.0700   0.3300   -0.1400   0.6000  0.4300  0.7400    0.6000
    1.5000   400.0000  -1.0250   2.0123   -0.7700   -0.00520499   -0.0820   -0.0500   0.7000   0.0100    0.4080   -0.0493    0.0000   0.3100    0.0000   0.6000  0.4300  0.7400    0.6000
    2.0000   400.0000  -0.2990   1.4128   -0.7100   -0.00505022   -0.2821    0.1200   0.7000   0.0085   -0.4010   -0.0610    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    2.5000   400.0000   0.0000   0.9976   -0.6700   -0.00507967   -0.4108    0.2500   0.7000   0.0069   -0.7230   -0.0711    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    3.0000   400.0000   0.0000   0.6443   -0.6400   -0.00529221   -0.4466    0.3000   0.7000   0.0054   -0.6730   -0.0798    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    4.0000   400.0000   0.0000   0.0657   -0.5800   -0.00564790   -0.4344    0.3000   0.7000   0.0027   -0.6270   -0.0935    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    5.0000   400.0000   0.0000  -0.4624   -0.5400   -0.00607621   -0.4368    0.3000   0.7000   0.0005   -0.5960   -0.0980    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    6.0000   400.0000   0.0000  -0.9809   -0.5000   -0.00647922   -0.4586    0.3000   0.7000  -0.0013   -0.5660   -0.0980    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    7.5000   400.0000   0.0000  -1.6017   -0.4600   -0.00676355   -0.4433    0.3000   0.7000  -0.0033   -0.5280   -0.0980    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    10.0000  400.0000   0.0000  -2.2937   -0.4000   -0.00686566   -0.4828    0.3000   0.7000  -0.0060   -0.5040   -0.0980    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    """)


class BCHydroESHM20SInterHigh(AbrahamsonEtAl2015SInterHigh):
    """
    ESHM20 adjustment of the BC Hydro GMPE for subduction interface events
    with theta6 calibrated to Mediterranean data, for the high
    magnitude scaling branch.
    """

    experimental = True

    # Requires Vs30 and distance to the volcanic front
    REQUIRES_SITES_PARAMETERS = set(('vs30', 'xvf'))

    def __init__(self, **kwargs):
        super().__init__(ergodic=kwargs.get("ergodic", True), **kwargs)
        self.theta6_adj = kwargs.get("theta6_adjustment", 0.0)
        self.sigma_mu_epsilon = kwargs.get("sigma_mu_epsilon", 0.0)
        faba_type = kwargs.get("faba_taper_model", "Step")
        self.faba_model = FABA_ALL_MODELS[faba_type](**kwargs)

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        Returns mean and stddevs applying the statistical uncertainty if
        needed
        """
        mean, stddevs = super().get_mean_and_stddevs(sites, rup, dists, imt,
                                                     stddev_types)
        if self.sigma_mu_epsilon:
            sigma_mu = get_stress_factor(imt, slab=False)
            return mean + (sigma_mu * self.sigma_mu_epsilon), stddevs
        else:
            return mean, stddevs

    def _compute_distance_term(self, C, mag, dists):
        """
        Computes the distance scaling term, as contained within equation (1)
        """
        return (C['theta2'] + self.CONSTS['theta3'] * (mag - 7.8)) *\
            np.log(dists.rrup + self.CONSTS['c4'] * np.exp((mag - 6.) *
                   self.CONSTS['theta9'])) +\
            ((self.theta6_adj + C['theta6']) * dists.rrup)

    def _compute_forearc_backarc_term(self, C, sites, dists):
        """
        Computes the forearc/backarc scaling term given by equation (4)
        """
        max_dist = np.copy(dists.rrup)
        max_dist[max_dist < 100.0] = 100.0
        f_faba = C['theta15'] + (C['theta16'] * np.log(max_dist / 40.0))
        return f_faba * self.faba_model(-sites.xvf)

    COEFFS = CoeffsTable(sa_damping=5, table="""\
    imt          vlin        b   theta1    theta2        theta6    theta7    theta8  theta10  theta11   theta12   theta13   theta14  theta15   theta16      phi     tau   sigma  sigma_ss
    pga      865.1000  -1.1860   4.2203   -1.3500   -0.00721467    1.0988   -1.4200   3.1200   0.0130    0.9800   -0.0135   -0.4000   0.9969   -1.0000   0.6000  0.4300  0.7400    0.6000
    0.0200   865.1000  -1.1860   4.2203   -1.3500   -0.00719296    1.0988   -1.4200   3.1200   0.0130    0.9800   -0.0135   -0.4000   0.9969   -1.0000   0.6000  0.4300  0.7400    0.6000
    0.0500  1053.5000  -1.3460   4.5371   -1.4000   -0.00712619    1.2536   -1.6500   3.3700   0.0130    1.2880   -0.0138   -0.4000   1.1030   -1.1800   0.6000  0.4300  0.7400    0.6000
    0.0750  1085.7000  -1.4710   5.0733   -1.4500   -0.00701600    1.4175   -1.8000   3.3700   0.0130    1.4830   -0.0142   -0.4000   1.2732   -1.3600   0.6000  0.4300  0.7400    0.6000
    0.1000  1032.5000  -1.6240   5.2892   -1.4500   -0.00687258    1.3997   -1.8000   3.3300   0.0130    1.6130   -0.0145   -0.4000   1.3042   -1.3600   0.6000  0.4300  0.7400    0.6000
    0.1500   877.6000  -1.9310   5.4563   -1.4500   -0.00671633    1.3582   -1.6900   3.2500   0.0130    1.8820   -0.0153   -0.4000   1.2600   -1.3000   0.6000  0.4300  0.7400    0.6000
    0.2000   748.2000  -2.1880   5.2684   -1.4000   -0.00657867    1.1648   -1.4900   3.0300   0.0129    2.0760   -0.0162   -0.3500   1.2230   -1.2500   0.6000  0.4300  0.7400    0.6000
    0.2500   654.3000  -2.3810   5.0594   -1.3500   -0.00648602    0.9940   -1.3000   2.8000   0.0129    2.2480   -0.0172   -0.3100   1.1600   -1.1700   0.6000  0.4300  0.7400    0.6000
    0.3000   587.1000  -2.5180   4.7945   -1.2800   -0.00643709    0.8821   -1.1800   2.5900   0.0128    2.3480   -0.0183   -0.2800   1.0500   -1.0600   0.6000  0.4300  0.7400    0.6000
    0.4000   503.0000  -2.6570   4.4644   -1.1800   -0.00639138    0.7046   -0.9800   2.2000   0.0127    2.4270   -0.0206   -0.2300   0.8000   -0.7800   0.6000  0.4300  0.7400    0.6000
    0.5000   456.6000  -2.6690   4.0181   -1.0800   -0.00629147    0.5799   -0.8200   1.9200   0.0125    2.3990   -0.0231   -0.1900   0.6620   -0.6200   0.6000  0.4300  0.7400    0.6000
    0.6000   430.3000  -2.5990   3.6055   -0.9900   -0.00609857    0.5021   -0.7000   1.7000   0.0124    2.2730   -0.0256   -0.1600   0.5800   -0.5000   0.6000  0.4300  0.7400    0.6000
    0.7500   410.5000  -2.4010   3.2174   -0.9100   -0.00581454    0.3687   -0.5400   1.4200   0.0120    1.9930   -0.0296   -0.1200   0.4800   -0.3400   0.6000  0.4300  0.7400    0.6000
    1.0000   400.0000  -1.9550   2.7981   -0.8500   -0.00548905    0.1746   -0.3400   1.1000   0.0114    1.4700   -0.0363   -0.0700   0.3300   -0.1400   0.6000  0.4300  0.7400    0.6000
    1.5000   400.0000  -1.0250   2.0123   -0.7700   -0.00520499   -0.0820   -0.0500   0.7000   0.0100    0.4080   -0.0493    0.0000   0.3100    0.0000   0.6000  0.4300  0.7400    0.6000
    2.0000   400.0000  -0.2990   1.4128   -0.7100   -0.00505022   -0.2821    0.1200   0.7000   0.0085   -0.4010   -0.0610    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    2.5000   400.0000   0.0000   0.9976   -0.6700   -0.00507967   -0.4108    0.2500   0.7000   0.0069   -0.7230   -0.0711    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    3.0000   400.0000   0.0000   0.6443   -0.6400   -0.00529221   -0.4466    0.3000   0.7000   0.0054   -0.6730   -0.0798    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    4.0000   400.0000   0.0000   0.0657   -0.5800   -0.00564790   -0.4344    0.3000   0.7000   0.0027   -0.6270   -0.0935    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    5.0000   400.0000   0.0000  -0.4624   -0.5400   -0.00607621   -0.4368    0.3000   0.7000   0.0005   -0.5960   -0.0980    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    6.0000   400.0000   0.0000  -0.9809   -0.5000   -0.00647922   -0.4586    0.3000   0.7000  -0.0013   -0.5660   -0.0980    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    7.5000   400.0000   0.0000  -1.6017   -0.4600   -0.00676355   -0.4433    0.3000   0.7000  -0.0033   -0.5280   -0.0980    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    10.0000  400.0000   0.0000  -2.2937   -0.4000   -0.00686566   -0.4828    0.3000   0.7000  -0.0060   -0.5040   -0.0980    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    """)


class BCHydroESHM20SSlab(AbrahamsonEtAl2015SSlab):
    """
    ESHM20 adjustment of the BC Hydro GMPE for subduction in-slab events with
    theta6 calibrated to Mediterranean data.

    Introduces two configurable parameters:

    a6_adjustment - the amount to increase or decrease the theta6 (should be
    +0.0015 (for slower attenuation) and -0.0015 (for faster attenuation)

    sigma_mu_epsilon - number of standard deviations above or below the mean
    to apply the statistical uncertainty sigma_mu term.
    """

    experimental = True

    # Requires Vs30 and distance to the volcanic front
    REQUIRES_SITES_PARAMETERS = set(('vs30', 'xvf'))

    def __init__(self, **kwargs):
        super().__init__(ergodic=kwargs.get("ergodic", True), **kwargs)
        self.theta6_adj = kwargs.get("theta6_adjustment", 0.0)
        self.sigma_mu_epsilon = kwargs.get("sigma_mu_epsilon", 0.0)
        faba_type = kwargs.get("faba_taper_model", "Step")
        self.faba_model = FABA_ALL_MODELS[faba_type](**kwargs)

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        Returns mean and stddevs applying the statistical uncertainty if
        needed
        """
        mean, stddevs = super().get_mean_and_stddevs(sites, rup, dists, imt,
                                                     stddev_types)
        if self.sigma_mu_epsilon:
            sigma_mu = get_stress_factor(imt, slab=True)
            return mean + (sigma_mu * self.sigma_mu_epsilon), stddevs
        else:
            return mean, stddevs

    def _compute_distance_term(self, C, mag, dists):
        """
        Computes the distance scaling term, as contained within equation (1)
        """
        return ((C['theta2'] + C['theta14'] + self.CONSTS['theta3'] *
                (mag - 7.8)) * np.log(dists.rhypo + self.CONSTS['c4'] *
                np.exp((mag - 6.) * self.CONSTS['theta9'])) +
                ((self.theta6_adj + C['theta6']) * dists.rhypo)) + C["theta10"]

    def _compute_forearc_backarc_term(self, C, sites, dists):
        """
        Computes the forearc/backarc scaling term given by equation (4).
        """
        max_dist = np.copy(dists.rhypo)
        max_dist[max_dist < 85.0] = 85.0
        f_faba = C['theta7'] + (C['theta8'] * np.log(max_dist / 40.0))
        return f_faba * self.faba_model(-sites.xvf)

    COEFFS = CoeffsTable(sa_damping=5, table="""\
    imt          vlin        b   theta1    theta2        theta6    theta7    theta8  theta10  theta11   theta12   theta13   theta14  theta15   theta16      phi     tau   sigma  sigma_ss
    pga      865.1000  -1.1860   4.2203   -1.3500   -0.00278801    1.0988   -1.4200   3.1200   0.0130    0.9800   -0.0135   -0.4000   0.9969   -1.0000   0.6000  0.4300  0.7400    0.6000
    0.0200   865.1000  -1.1860   4.2203   -1.3500   -0.00275821    1.0988   -1.4200   3.1200   0.0130    0.9800   -0.0135   -0.4000   0.9969   -1.0000   0.6000  0.4300  0.7400    0.6000
    0.0500  1053.5000  -1.3460   4.5371   -1.4000   -0.00268517    1.2536   -1.6500   3.3700   0.0130    1.2880   -0.0138   -0.4000   1.1030   -1.1800   0.6000  0.4300  0.7400    0.6000
    0.0750  1085.7000  -1.4710   5.0733   -1.4500   -0.00261360    1.4175   -1.8000   3.3700   0.0130    1.4830   -0.0142   -0.4000   1.2732   -1.3600   0.6000  0.4300  0.7400    0.6000
    0.1000  1032.5000  -1.6240   5.2892   -1.4500   -0.00259240    1.3997   -1.8000   3.3300   0.0130    1.6130   -0.0145   -0.4000   1.3042   -1.3600   0.6000  0.4300  0.7400    0.6000
    0.1500   877.6000  -1.9310   5.4563   -1.4500   -0.00264688    1.3582   -1.6900   3.2500   0.0130    1.8820   -0.0153   -0.4000   1.2600   -1.3000   0.6000  0.4300  0.7400    0.6000
    0.2000   748.2000  -2.1880   5.2684   -1.4000   -0.00277703    1.1648   -1.4900   3.0300   0.0129    2.0760   -0.0162   -0.3500   1.2230   -1.2500   0.6000  0.4300  0.7400    0.6000
    0.2500   654.3000  -2.3810   5.0594   -1.3500   -0.00296427    0.9940   -1.3000   2.8000   0.0129    2.2480   -0.0172   -0.3100   1.1600   -1.1700   0.6000  0.4300  0.7400    0.6000
    0.3000   587.1000  -2.5180   4.7945   -1.2800   -0.00318216    0.8821   -1.1800   2.5900   0.0128    2.3480   -0.0183   -0.2800   1.0500   -1.0600   0.6000  0.4300  0.7400    0.6000
    0.4000   503.0000  -2.6570   4.4644   -1.1800   -0.00340820    0.7046   -0.9800   2.2000   0.0127    2.4270   -0.0206   -0.2300   0.8000   -0.7800   0.6000  0.4300  0.7400    0.6000
    0.5000   456.6000  -2.6690   4.0181   -1.0800   -0.00363798    0.5799   -0.8200   1.9200   0.0125    2.3990   -0.0231   -0.1900   0.6620   -0.6200   0.6000  0.4300  0.7400    0.6000
    0.6000   430.3000  -2.5990   3.6055   -0.9900   -0.00388267    0.5021   -0.7000   1.7000   0.0124    2.2730   -0.0256   -0.1600   0.5800   -0.5000   0.6000  0.4300  0.7400    0.6000
    0.7500   410.5000  -2.4010   3.2174   -0.9100   -0.00415403    0.3687   -0.5400   1.4200   0.0120    1.9930   -0.0296   -0.1200   0.4800   -0.3400   0.6000  0.4300  0.7400    0.6000
    1.0000   400.0000  -1.9550   2.7981   -0.8500   -0.00445479    0.1746   -0.3400   1.1000   0.0114    1.4700   -0.0363   -0.0700   0.3300   -0.1400   0.6000  0.4300  0.7400    0.6000
    1.5000   400.0000  -1.0250   2.0123   -0.7700   -0.00478084   -0.0820   -0.0500   0.7000   0.0100    0.4080   -0.0493    0.0000   0.3100    0.0000   0.6000  0.4300  0.7400    0.6000
    2.0000   400.0000  -0.2990   1.4128   -0.7100   -0.00513159   -0.2821    0.1200   0.7000   0.0085   -0.4010   -0.0610    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    2.5000   400.0000   0.0000   0.9976   -0.6700   -0.00550694   -0.4108    0.2500   0.7000   0.0069   -0.7230   -0.0711    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    3.0000   400.0000   0.0000   0.6443   -0.6400   -0.00590809   -0.4466    0.3000   0.7000   0.0054   -0.6730   -0.0798    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    4.0000   400.0000   0.0000   0.0657   -0.5800   -0.00634283   -0.4344    0.3000   0.7000   0.0027   -0.6270   -0.0935    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    5.0000   400.0000   0.0000  -0.4624   -0.5400   -0.00680074   -0.4368    0.3000   0.7000   0.0005   -0.5960   -0.0980    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    6.0000   400.0000   0.0000  -0.9809   -0.5000   -0.00722208   -0.4586    0.3000   0.7000  -0.0013   -0.5660   -0.0980    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    7.5000   400.0000   0.0000  -1.6017   -0.4600   -0.00752097   -0.4433    0.3000   0.7000  -0.0033   -0.5280   -0.0980    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    10.0000  400.0000   0.0000  -2.2937   -0.4000   -0.00762908   -0.4828    0.3000   0.7000  -0.0060   -0.5040   -0.0980    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    """)


class BCHydroESHM20SSlabLow(AbrahamsonEtAl2015SSlabLow):
    """
    ESHM20 adjustment of the BC Hydro GMPE for subduction in-slab events
    with theta6 calibrated to Mediterranean data, for the low magnitude
    scaling branch.
    """

    experimental = True

    # Requires Vs30 and distance to the volcanic front
    REQUIRES_SITES_PARAMETERS = set(('vs30', 'xvf'))

    def __init__(self, **kwargs):
        super().__init__(ergodic=kwargs.get("ergodic", True), **kwargs)
        self.theta6_adj = kwargs.get("theta6_adjustment", 0.0)
        self.sigma_mu_epsilon = kwargs.get("sigma_mu_epsilon", 0.0)
        faba_type = kwargs.get("faba_taper_model", "Step")
        self.faba_model = FABA_ALL_MODELS[faba_type](**kwargs)

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        Returns mean and stddevs applying the statistical uncertainty if
        needed
        """
        mean, stddevs = super().get_mean_and_stddevs(sites, rup, dists, imt,
                                                     stddev_types)
        if self.sigma_mu_epsilon:
            sigma_mu = get_stress_factor(imt, slab=True)
            return mean + (sigma_mu * self.sigma_mu_epsilon), stddevs
        else:
            return mean, stddevs

    def _compute_distance_term(self, C, mag, dists):
        """
        Computes the distance scaling term, as contained within equation (1)
        """
        return ((C['theta2'] + C['theta14'] + self.CONSTS['theta3'] *
                (mag - 7.8)) * np.log(dists.rhypo + self.CONSTS['c4'] *
                np.exp((mag - 6.) * self.CONSTS['theta9'])) +
                ((self.theta6_adj + C['theta6']) * dists.rhypo)) + C["theta10"]

    def _compute_forearc_backarc_term(self, C, sites, dists):
        """
        Computes the forearc/backarc scaling term given by equation (4).
        """
        max_dist = np.copy(dists.rhypo)
        max_dist[max_dist < 85.0] = 85.0
        f_faba = C['theta7'] + (C['theta8'] * np.log(max_dist / 40.0))
        return f_faba * self.faba_model(-sites.xvf)

    COEFFS = CoeffsTable(sa_damping=5, table="""\
    imt          vlin        b   theta1    theta2        theta6    theta7    theta8  theta10  theta11   theta12   theta13   theta14  theta15   theta16      phi     tau   sigma  sigma_ss
    pga      865.1000  -1.1860   4.2203   -1.3500   -0.00278801    1.0988   -1.4200   3.1200   0.0130    0.9800   -0.0135   -0.4000   0.9969   -1.0000   0.6000  0.4300  0.7400    0.6000
    0.0200   865.1000  -1.1860   4.2203   -1.3500   -0.00275821    1.0988   -1.4200   3.1200   0.0130    0.9800   -0.0135   -0.4000   0.9969   -1.0000   0.6000  0.4300  0.7400    0.6000
    0.0500  1053.5000  -1.3460   4.5371   -1.4000   -0.00268517    1.2536   -1.6500   3.3700   0.0130    1.2880   -0.0138   -0.4000   1.1030   -1.1800   0.6000  0.4300  0.7400    0.6000
    0.0750  1085.7000  -1.4710   5.0733   -1.4500   -0.00261360    1.4175   -1.8000   3.3700   0.0130    1.4830   -0.0142   -0.4000   1.2732   -1.3600   0.6000  0.4300  0.7400    0.6000
    0.1000  1032.5000  -1.6240   5.2892   -1.4500   -0.00259240    1.3997   -1.8000   3.3300   0.0130    1.6130   -0.0145   -0.4000   1.3042   -1.3600   0.6000  0.4300  0.7400    0.6000
    0.1500   877.6000  -1.9310   5.4563   -1.4500   -0.00264688    1.3582   -1.6900   3.2500   0.0130    1.8820   -0.0153   -0.4000   1.2600   -1.3000   0.6000  0.4300  0.7400    0.6000
    0.2000   748.2000  -2.1880   5.2684   -1.4000   -0.00277703    1.1648   -1.4900   3.0300   0.0129    2.0760   -0.0162   -0.3500   1.2230   -1.2500   0.6000  0.4300  0.7400    0.6000
    0.2500   654.3000  -2.3810   5.0594   -1.3500   -0.00296427    0.9940   -1.3000   2.8000   0.0129    2.2480   -0.0172   -0.3100   1.1600   -1.1700   0.6000  0.4300  0.7400    0.6000
    0.3000   587.1000  -2.5180   4.7945   -1.2800   -0.00318216    0.8821   -1.1800   2.5900   0.0128    2.3480   -0.0183   -0.2800   1.0500   -1.0600   0.6000  0.4300  0.7400    0.6000
    0.4000   503.0000  -2.6570   4.4644   -1.1800   -0.00340820    0.7046   -0.9800   2.2000   0.0127    2.4270   -0.0206   -0.2300   0.8000   -0.7800   0.6000  0.4300  0.7400    0.6000
    0.5000   456.6000  -2.6690   4.0181   -1.0800   -0.00363798    0.5799   -0.8200   1.9200   0.0125    2.3990   -0.0231   -0.1900   0.6620   -0.6200   0.6000  0.4300  0.7400    0.6000
    0.6000   430.3000  -2.5990   3.6055   -0.9900   -0.00388267    0.5021   -0.7000   1.7000   0.0124    2.2730   -0.0256   -0.1600   0.5800   -0.5000   0.6000  0.4300  0.7400    0.6000
    0.7500   410.5000  -2.4010   3.2174   -0.9100   -0.00415403    0.3687   -0.5400   1.4200   0.0120    1.9930   -0.0296   -0.1200   0.4800   -0.3400   0.6000  0.4300  0.7400    0.6000
    1.0000   400.0000  -1.9550   2.7981   -0.8500   -0.00445479    0.1746   -0.3400   1.1000   0.0114    1.4700   -0.0363   -0.0700   0.3300   -0.1400   0.6000  0.4300  0.7400    0.6000
    1.5000   400.0000  -1.0250   2.0123   -0.7700   -0.00478084   -0.0820   -0.0500   0.7000   0.0100    0.4080   -0.0493    0.0000   0.3100    0.0000   0.6000  0.4300  0.7400    0.6000
    2.0000   400.0000  -0.2990   1.4128   -0.7100   -0.00513159   -0.2821    0.1200   0.7000   0.0085   -0.4010   -0.0610    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    2.5000   400.0000   0.0000   0.9976   -0.6700   -0.00550694   -0.4108    0.2500   0.7000   0.0069   -0.7230   -0.0711    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    3.0000   400.0000   0.0000   0.6443   -0.6400   -0.00590809   -0.4466    0.3000   0.7000   0.0054   -0.6730   -0.0798    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    4.0000   400.0000   0.0000   0.0657   -0.5800   -0.00634283   -0.4344    0.3000   0.7000   0.0027   -0.6270   -0.0935    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    5.0000   400.0000   0.0000  -0.4624   -0.5400   -0.00680074   -0.4368    0.3000   0.7000   0.0005   -0.5960   -0.0980    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    6.0000   400.0000   0.0000  -0.9809   -0.5000   -0.00722208   -0.4586    0.3000   0.7000  -0.0013   -0.5660   -0.0980    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    7.5000   400.0000   0.0000  -1.6017   -0.4600   -0.00752097   -0.4433    0.3000   0.7000  -0.0033   -0.5280   -0.0980    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    10.0000  400.0000   0.0000  -2.2937   -0.4000   -0.00762908   -0.4828    0.3000   0.7000  -0.0060   -0.5040   -0.0980    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    """)


class BCHydroESHM20SSlabHigh(AbrahamsonEtAl2015SSlabHigh):
    """
    ESHM20 adjustment of the BC Hydro GMPE for subduction interface events
    with theta6 calibrated to Mediterranean data, for the high magnitude
    scaling branch.
    """

    experimental = True

    # Requires Vs30 and distance to the volcanic front
    REQUIRES_SITES_PARAMETERS = set(('vs30', 'xvf'))

    def __init__(self, **kwargs):
        super().__init__(ergodic=kwargs.get("ergodic", True), **kwargs)
        self.theta6_adj = kwargs.get("theta6_adjustment", 0.0)
        self.sigma_mu_epsilon = kwargs.get("sigma_mu_epsilon", 0.0)
        faba_type = kwargs.get("faba_taper_model", "Step")
        self.faba_model = FABA_ALL_MODELS[faba_type](**kwargs)

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        Returns mean and stddevs applying the statistical uncertainty if
        needed
        """
        mean, stddevs = super().get_mean_and_stddevs(sites, rup, dists, imt,
                                                     stddev_types)
        if self.sigma_mu_epsilon:
            sigma_mu = get_stress_factor(imt, slab=True)
            return mean + (sigma_mu * self.sigma_mu_epsilon), stddevs
        else:
            return mean, stddevs

    def _compute_distance_term(self, C, mag, dists):
        """
        Computes the distance scaling term, as contained within equation (1)
        """
        return ((C['theta2'] + C['theta14'] + self.CONSTS['theta3'] *
                (mag - 7.8)) * np.log(dists.rhypo + self.CONSTS['c4'] *
                np.exp((mag - 6.) * self.CONSTS['theta9'])) +
                ((self.theta6_adj + C['theta6']) * dists.rhypo)) + C["theta10"]

    def _compute_forearc_backarc_term(self, C, sites, dists):
        """
        Computes the forearc/backarc scaling term given by equation (4).
        """
        max_dist = np.copy(dists.rhypo)
        max_dist[max_dist < 85.0] = 85.0
        f_faba = C['theta7'] + (C['theta8'] * np.log(max_dist / 40.0))
        return f_faba * self.faba_model(-sites.xvf)

    COEFFS = CoeffsTable(sa_damping=5, table="""\
    imt          vlin        b   theta1    theta2        theta6    theta7    theta8  theta10  theta11   theta12   theta13   theta14  theta15   theta16      phi     tau   sigma  sigma_ss
    pga      865.1000  -1.1860   4.2203   -1.3500   -0.00278801    1.0988   -1.4200   3.1200   0.0130    0.9800   -0.0135   -0.4000   0.9969   -1.0000   0.6000  0.4300  0.7400    0.6000
    0.0200   865.1000  -1.1860   4.2203   -1.3500   -0.00275821    1.0988   -1.4200   3.1200   0.0130    0.9800   -0.0135   -0.4000   0.9969   -1.0000   0.6000  0.4300  0.7400    0.6000
    0.0500  1053.5000  -1.3460   4.5371   -1.4000   -0.00268517    1.2536   -1.6500   3.3700   0.0130    1.2880   -0.0138   -0.4000   1.1030   -1.1800   0.6000  0.4300  0.7400    0.6000
    0.0750  1085.7000  -1.4710   5.0733   -1.4500   -0.00261360    1.4175   -1.8000   3.3700   0.0130    1.4830   -0.0142   -0.4000   1.2732   -1.3600   0.6000  0.4300  0.7400    0.6000
    0.1000  1032.5000  -1.6240   5.2892   -1.4500   -0.00259240    1.3997   -1.8000   3.3300   0.0130    1.6130   -0.0145   -0.4000   1.3042   -1.3600   0.6000  0.4300  0.7400    0.6000
    0.1500   877.6000  -1.9310   5.4563   -1.4500   -0.00264688    1.3582   -1.6900   3.2500   0.0130    1.8820   -0.0153   -0.4000   1.2600   -1.3000   0.6000  0.4300  0.7400    0.6000
    0.2000   748.2000  -2.1880   5.2684   -1.4000   -0.00277703    1.1648   -1.4900   3.0300   0.0129    2.0760   -0.0162   -0.3500   1.2230   -1.2500   0.6000  0.4300  0.7400    0.6000
    0.2500   654.3000  -2.3810   5.0594   -1.3500   -0.00296427    0.9940   -1.3000   2.8000   0.0129    2.2480   -0.0172   -0.3100   1.1600   -1.1700   0.6000  0.4300  0.7400    0.6000
    0.3000   587.1000  -2.5180   4.7945   -1.2800   -0.00318216    0.8821   -1.1800   2.5900   0.0128    2.3480   -0.0183   -0.2800   1.0500   -1.0600   0.6000  0.4300  0.7400    0.6000
    0.4000   503.0000  -2.6570   4.4644   -1.1800   -0.00340820    0.7046   -0.9800   2.2000   0.0127    2.4270   -0.0206   -0.2300   0.8000   -0.7800   0.6000  0.4300  0.7400    0.6000
    0.5000   456.6000  -2.6690   4.0181   -1.0800   -0.00363798    0.5799   -0.8200   1.9200   0.0125    2.3990   -0.0231   -0.1900   0.6620   -0.6200   0.6000  0.4300  0.7400    0.6000
    0.6000   430.3000  -2.5990   3.6055   -0.9900   -0.00388267    0.5021   -0.7000   1.7000   0.0124    2.2730   -0.0256   -0.1600   0.5800   -0.5000   0.6000  0.4300  0.7400    0.6000
    0.7500   410.5000  -2.4010   3.2174   -0.9100   -0.00415403    0.3687   -0.5400   1.4200   0.0120    1.9930   -0.0296   -0.1200   0.4800   -0.3400   0.6000  0.4300  0.7400    0.6000
    1.0000   400.0000  -1.9550   2.7981   -0.8500   -0.00445479    0.1746   -0.3400   1.1000   0.0114    1.4700   -0.0363   -0.0700   0.3300   -0.1400   0.6000  0.4300  0.7400    0.6000
    1.5000   400.0000  -1.0250   2.0123   -0.7700   -0.00478084   -0.0820   -0.0500   0.7000   0.0100    0.4080   -0.0493    0.0000   0.3100    0.0000   0.6000  0.4300  0.7400    0.6000
    2.0000   400.0000  -0.2990   1.4128   -0.7100   -0.00513159   -0.2821    0.1200   0.7000   0.0085   -0.4010   -0.0610    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    2.5000   400.0000   0.0000   0.9976   -0.6700   -0.00550694   -0.4108    0.2500   0.7000   0.0069   -0.7230   -0.0711    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    3.0000   400.0000   0.0000   0.6443   -0.6400   -0.00590809   -0.4466    0.3000   0.7000   0.0054   -0.6730   -0.0798    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    4.0000   400.0000   0.0000   0.0657   -0.5800   -0.00634283   -0.4344    0.3000   0.7000   0.0027   -0.6270   -0.0935    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    5.0000   400.0000   0.0000  -0.4624   -0.5400   -0.00680074   -0.4368    0.3000   0.7000   0.0005   -0.5960   -0.0980    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    6.0000   400.0000   0.0000  -0.9809   -0.5000   -0.00722208   -0.4586    0.3000   0.7000  -0.0013   -0.5660   -0.0980    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    7.5000   400.0000   0.0000  -1.6017   -0.4600   -0.00752097   -0.4433    0.3000   0.7000  -0.0033   -0.5280   -0.0980    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    10.0000  400.0000   0.0000  -2.2937   -0.4000   -0.00762908   -0.4828    0.3000   0.7000  -0.0060   -0.5040   -0.0980    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    """)
