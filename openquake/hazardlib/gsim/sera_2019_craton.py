# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2019 GEM Foundation
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
Module exports :class:`SERA2019Craton`
"""

import numpy as np
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib import const
from openquake.hazardlib.gsim.nga_east import (get_tau_at_quantile,
                                               get_phi_ss_at_quantile,
                                               TAU_EXECUTION, TAU_SETUP,
                                               PHI_S2SS_MODEL, PHI_SETUP,
                                               get_phi_ss)


#: Phi S2SS values for the global ergodic aleatory uncertainty model as
#: retrieved from the US NSHMP software
#: https://github.com/usgs/nshmp-haz/blob/master/src/gov/usgs/earthquake/nshmp/gmm/coeffs/nga-east-usgs-sigma-panel.csv
PHI_S2SS_GLOBAL = CoeffsTable(sa_damping=5, table="""\
imt      s2s1    s2s2
pga     0.533   0.566
0.010   0.533   0.566
0.020   0.537   0.577
0.030   0.542   0.598
0.040   0.562   0.638
0.050   0.583   0.653
0.075   0.619   0.633
0.100   0.623   0.590
0.150   0.603   0.532
0.200   0.578   0.461
0.250   0.554   0.396
0.300   0.527   0.373
0.400   0.491   0.339
0.500   0.472   0.305
0.750   0.432   0.273
1.000   0.431   0.257
1.500   0.424   0.247
2.000   0.423   0.239
3.000   0.418   0.230
4.000   0.412   0.221
5.000   0.404   0.214
7.500   0.378   0.201
10.00   0.319   0.193
""")


def get_phi_s2s(imt, vs30):
    """
    Implementation of the phi_S2S model for the ergodic aleatory uncertainty
    model of Eastern North America - as implemented in the US-NSHMP software
    https://github.com/usgs/nshmp-haz/blob/master/src/gov/usgs/earthquake/nshmp/gmm/NgaEastUsgs_2017.java
    """
    C = PHI_S2SS_GLOBAL[imt]
    phi_s2s = C["s2s1"] * np.ones(vs30.shape)
    idx = vs30 >= 1500.0
    if np.any(idx):
        phi_s2s[idx] = C["s2s2"]
    idx = np.logical_and(vs30 >= 1200., vs30 < 1500.)
    if np.any(vs30):
        phi_s2s[idx] = C["s2s1"] - ((C["s2s1"] - C["s2s2"]) /
                                    (1500. - 1200.)) * (vs30[idx] - 1200.0)
    return phi_s2s


class SERA2019Craton(GMPE):
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

    """
    experimental = True

    #: Supported tectonic region type is 'active shallow crust'
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.STABLE_CONTINENTAL

    #: The GMPE is defined only for PGA and SA
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        SA
    ])

    #: Supported intensity measure component is the geometric mean of two
    #: horizontal components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    #: Supported standard deviation types are inter-event, intra-event
    #: and total
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    ])

    #: Median calibrated for 800 m/s Vs30, no site term is required
    REQUIRES_SITES_PARAMETERS = set()

    #: Requires only magnitude
    REQUIRES_RUPTURE_PARAMETERS = set(('mag',))

    #: Required distance measure is Rrup
    REQUIRES_DISTANCES = set(('rrup', ))

    #: Defined for a reference velocity of 800 m/s
    DEFINED_FOR_REFERENCE_VELOCITY = 800.0

    def __init__(self, epsilon=0.0, tau_model="global", phi_model="global",
                 ergodic=True, tau_quantile=0.5, phi_ss_quantile=0.5,
                 phi_s2ss_quantile=None):
        """
        Instantiates the class with additional terms controlling both the
        epistemic uncertainty in the median and the preferred aleatory
        uncertainty model ('global', 'cena_constant', 'cena'), and the quantile
        of the epistemic uncertainty model (float in the range 0 to 1).
        """
        super().__init__()
        self.epsilon = epsilon
        self.tau_model = tau_model
        self.phi_model = phi_model
        self.TAU = None
        self.PHI_SS = None
        self.PHI_S2SS = None
        self.ergodic = ergodic
        self.tau_quantile = tau_quantile
        self.phi_ss_quantile = phi_ss_quantile
        self.phi_s2ss_quantile = phi_s2ss_quantile
        self._setup_standard_deviations()

    def _setup_standard_deviations(self):
        """
        Defines the standard deviation model from the NGA East aleatory
        uncertainty model according to the calibrations specified by the user
        """
        # setup tau
        self.TAU = get_tau_at_quantile(TAU_SETUP[self.tau_model]["MEAN"],
                                       TAU_SETUP[self.tau_model]["STD"],
                                       self.tau_quantile)
        # setup phi
        self.PHI_SS = get_phi_ss_at_quantile(PHI_SETUP[self.phi_model],
                                             self.phi_ss_quantile)

    def get_mean_and_stddevs(self, sctx, rctx, dctx, imt, stddev_types):
        """
        Returns the mean and standard deviations
        """
        C = self.COEFFS[imt]
        mean = (self.get_magnitude_scaling(C, rctx.mag) +
                self.get_distance_term(C, rctx.mag, dctx.rrup))
        stddevs = self.get_stddevs(rctx.mag, imt,
                                   stddev_types,
                                   dctx.rrup.shape)
        if self.epsilon:
            mean += (self.epsilon * C["sigma"])
        return mean, stddevs

    def get_magnitude_scaling(self, C, mag):
        """
        Returns the magnitude scaling term
        """
        d_m = mag - self.CONSTANTS["Mh"]
        if mag <= self.CONSTANTS["Mh"]:
            return C["e1"] + C["b1"] * d_m + C["b2"] * (d_m ** 2.0)
        else:
            return C["e1"] + C["b3"] * d_m

    def get_distance_term(self, C, mag, rrup):
        """
        Returns the distance attenuation factor
        """
        rval = np.sqrt(rrup ** 2. + self.CONSTANTS["h"] ** 2.)
        rref_val = np.sqrt(self.CONSTANTS["Rref"] ** 2. +
                           self.CONSTANTS["h"] ** 2.)

        f_r = (C["c1"] + C["c2"] * (mag - self.CONSTANTS["Mref"])) *\
            np.log(rval / rref_val) + (C["c3"] * (rval - rref_val) / 100.)
        return f_r

    def get_stddevs(self, mag, imt, stddev_types, num_sites):
        """
        Returns the standard deviations for either the ergodic or
        non-ergodic models
        """
        tau = self._get_tau(imt, mag)
        phi = self._get_phi(imt, mag, num_sites)
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

    def _get_phi(self, imt, mag, num_sites):
        """
        Returns the within-event standard deviation (phi). If the ergodic
        model is chosen the "global" phi_s2s model of Stewart et al. (2019)
        is used.
        """
        phi = get_phi_ss(imt, mag, self.PHI_SS)
        if self.ergodic:
            phi_s2s = get_phi_s2s(
                imt, 
                self.DEFINED_FOR_REFERENCE_VELOCITY + np.zeros(num_sites))
            phi = np.sqrt(phi ** 2. + phi_s2s ** 2.)
        return phi

    COEFFS = CoeffsTable(sa_damping=5, table="""\
    imt                    e1                 b1                   b2                   b3                  c1                  c2                   c3              sigma 
    pga    -0.411485133743509  0.357346331273981   -0.129331384661331   0.0770757852452283   -1.38864592227593   0.245059637911991  -0.2465479449497610  0.410702799670382
    0.010  -0.103475078856401  0.341483510987318   -0.114061217989270   0.0508117354903134   -1.45604098082087   0.248105221460813  -0.2457494342020140  0.369669481136582
    0.020   0.336257897750582  0.296350501617815   -0.119464529127535   0.0267008349263102   -1.49218798271606   0.251124889862470  -0.2760892116770320  0.410191232321801
    0.025   0.434087083277860  0.307038496646777   -0.120117155942429   0.0348542591869410   -1.47915121692012   0.249661232178513  -0.2909629365873760  0.408386306222312
    0.030   0.464551031038901  0.315459264036446   -0.122405110933239   0.0507825372759672   -1.45486461477134   0.246723714996131  -0.3033565363370380  0.394662049013359
    0.040   0.509831489896513  0.350931968258022   -0.123612601471266   0.0851362611174279   -1.41611328223800   0.239121031370779  -0.3179027407498340  0.382673612982367
    0.050   0.511507850602161  0.379303361787416   -0.124607784812312   0.1157742313577260   -1.38277098103329   0.232014216888536  -0.3257581673074960  0.389597269082968
    0.075   0.471254649589488  0.452557388362336   -0.130266452565699   0.1795938693313320   -1.33115721347293   0.214094856905885  -0.3235562575156860  0.414864891371193
    0.100   0.374823370344466  0.509213781433580   -0.142383781213790   0.2381589567211550   -1.29292220837939   0.198310791979300  -0.3064851775369350  0.425838747897656
    0.150   0.190098220628619  0.591738903356812   -0.171788411039197   0.3078618673052130   -1.23084701561788   0.173696275265383  -0.2722447014368730  0.397448437394601
    0.200   0.032875814239707  0.670058248506261   -0.192619396265411   0.3593609909058660   -1.19358042101065   0.157871399971597  -0.2397524423125980  0.390659762115960
    0.250  -0.105510059903519  0.731535748797577   -0.209385732538891   0.3949225065866600   -1.17572370723250   0.149227466176314  -0.2103676772887760  0.382301010735161
    0.300  -0.243002275120470  0.792379078830873   -0.223622485253086   0.4274224009908170   -1.16116424053833   0.141886842871746  -0.1809655456541290  0.385057037039707
    0.400  -0.470188491692722  0.895684105852058   -0.242293326869801   0.4825691572778840   -1.15050754146953   0.134233376086564  -0.1365206456594560  0.394598123701283
    0.500  -0.663811023740042  0.992172602134495   -0.253928977735411   0.5264929888090040   -1.14383789135037   0.130026296489582  -0.1122274532237300  0.416598167426613
    0.750  -1.058595526106100  1.237940341046050   -0.248354436725297   0.6131205668606990   -1.12726795748165   0.121481539043842  -0.0735699500419782  0.424890674487474
    1.000  -1.394371380905040  1.445802752394450   -0.229115766497733   0.6916183102860360   -1.10947272998521   0.116811006183697  -0.0583507989200372  0.435248468005265
    1.500  -1.917910281699970  1.730211057127810   -0.193720347848463   0.8056188557546130   -1.10238963746356   0.114304323234015  -0.0390002220659411  0.494395089992631
    2.000  -2.364529249897820  1.920444411586870   -0.161745955617800   0.9080459225974400   -1.09475713780704   0.113859128722744  -0.0296896047090773  0.529654108570759
    3.000  -3.065384610304430  2.146790919707320   -0.114822226957822   1.0850926107535200   -1.09078504639421   0.115722605696417  -0.0198124902094360  0.550847111232533
    4.000  -3.606408850681790  2.262672882091760   -0.088526578024167   1.2277545662334400   -1.09027303279062   0.117771231425802  -0.0135796351367465  0.547902753430950
    5.000  -4.051295851215090  2.318736625090610   -0.077703673686716   1.3466317607156100   -1.09024145026104   0.118983854011159  -0.0083306184323743  0.536941622214679
    7.500  -4.904365014803420  2.373210855722320   -0.064599388535475   1.5296860339577000   -1.10749401059022   0.131644329633500  -0.0000501350030582  0.531853243293249
    10.00  -5.515190031962340  2.381469552005210   -0.063355023353710   1.6200105502639700   -1.12739785746232   0.141293378818929   0.0059543369597639  0.560211171679617
    """)

    CONSTANTS = {"Mref": 4.5, "Rref": 1., "Mh": 6.2, "h": 5.0}
