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
    imt                  e1               b1                b2               b3                c1               c2                c3            sigma
    pga      0.058203162959   0.435129208559   -0.126016773739   0.139921741511   -1.448114519061   0.234306425051   -0.233982914608   0.439766676224
    0.010    0.367785208853   0.423961296596   -0.108565023780   0.113904930501   -1.515976246370   0.237105566352   -0.232829425951   0.398058200682
    0.020    0.898528961731   0.386491098413   -0.117998253567   0.098693181784   -1.573117959342   0.239700647094   -0.260364582826   0.432577246332
    0.025    0.970840243069   0.392204957064   -0.117456286270   0.105686184108   -1.552890959508   0.237571641180   -0.274154483086   0.434187584011
    0.030    0.999602740626   0.397619251108   -0.118945410698   0.119756272294   -1.522403348545   0.234320846139   -0.286508591698   0.419561090015
    0.040    1.022388685167   0.415210124396   -0.119754715001   0.139571133597   -1.465413332143   0.228720442179   -0.304185839759   0.406208241601
    0.050    1.020058718703   0.428755976572   -0.121572136782   0.158829375030   -1.419106697089   0.223472654618   -0.314898868534   0.407536745170
    0.075    0.973170152265   0.459944264989   -0.129845657365   0.186444512256   -1.335985123205   0.212655277011   -0.321921719809   0.417251590699
    0.100    1.059082029222   0.509213781421   -0.142383781225   0.238158956755   -1.292922208373   0.198310791973   -0.306485177536   0.425838747548
    0.150    0.807791666127   0.595167179096   -0.171506512723   0.310827931845   -1.232822964273   0.173110043228   -0.271670654797   0.398610401284
    0.200    0.464155671950   0.670058248555   -0.192619396258   0.359360990926   -1.193580420983   0.157871399965   -0.239752442319   0.390659761450
    0.250    0.237716787628   0.732877988682   -0.209295210092   0.396105701806   -1.176495163894   0.148994671021   -0.210153595194   0.382674777689
    0.300    0.040129373373   0.792379078781   -0.223622485279   0.427422400953   -1.161164240551   0.141886842878   -0.180965545655   0.385057037451
    0.400   -0.246646206050   0.895684105719   -0.242293326908   0.482569156981   -1.150507541567   0.134233376142   -0.136520645644   0.394598126828
    0.500   -0.477316078376   0.992172602233   -0.253928977705   0.526492988673   -1.143837891401   0.130026296513   -0.112227453205   0.416598169338
    0.750   -0.931005808847   1.237933704077   -0.248354824580   0.613114532340   -1.127263421027   0.121482691597   -0.073571223859   0.424891583465
    1.000   -1.306223882795   1.445802752398   -0.229115766474   0.691618310355   -1.109472729960   0.116811006176   -0.058350798924   0.435248467279
    1.500   -1.840491079390   1.730207671881   -0.193720408166   0.805615925622   -1.102386586192   0.114304760235   -0.039000737485   0.494396181587
    2.000   -2.285324076801   1.920444411511   -0.161745955632   0.908045922659   -1.094757137783   0.113859128713   -0.029689604709   0.529654107472
    3.000   -2.992641077096   2.146790919378   -0.114822227145   1.085092611030   -1.090785046255   0.115722605638   -0.019812490186   0.550847106758
    4.000   -3.541068131173   2.262672882226   -0.088526577933   1.227754566114   -1.090273032836   0.117771231448   -0.013579635157   0.547902755061
    5.000   -3.988592910855   2.318736624736   -0.077703673940   1.346631761408   -1.090241450007   0.118983853881   -0.008330618336   0.536941614306
    """)

    CONSTANTS = {"Mref": 4.5, "Rref": 1., "Mh": 6.2, "h": 5.0}
