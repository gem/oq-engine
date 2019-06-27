# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (c) 2013-2019 GEM Foundation
#
# openquake is free software: you can redistribute it and/or modify it
# under the terms of the gnu affero general public license as published
# by the free software foundation, either version 3 of the license, or
# (at your option) any later version.
#
# openquake is distributed in the hope that it will be useful,
# but without any warranty; without even the implied warranty of
# merchantability or fitness for a particular purpose.  see the
# gnu affero general public license for more details.
#
# you should have received a copy of the gnu affero general public license
# along with openquake. if not, see <http://www.gnu.org/licenses/>.
"""
module exports :class:`HongGoda2007RotD100`.
"""
import numpy as np
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA


class HongGoda2007(GMPE):
    """
    Implements GMPE developed for RotD100 ground motion as defined by
    Hong, H. P. and Goda, K. (2007), "Orientation-Dependent Ground Motion
    Measure for Seismic Hazard Assessment", Bull. Seism. Soc. Am. 97(5),
    1525 - 1538

    This is really an experimental GMPE in which the amplification term
    is taken directly from Atkinson & Boore (2006) rather than constrained
    by the records themselves. There may exist a possible units issue as
    the amplification function for AB2006 is in cm/s/s whereas the
    GMPE here is given in g
    """
    #: The supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: The supported intensity measure types are PGA, PGV, and SA
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        PGV,
        SA
    ])

    #: The supported intensity measure component is RotD100
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD100

    #: The supported standard deviations are total, inter and intra event, see
    #: table 4.a, pages 22-23
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    ])

    #: The required site parameter is vs30, see equation 1, page 20.
    REQUIRES_SITES_PARAMETERS = set(('vs30',))

    #: The required rupture parameters are magnitude
    REQUIRES_RUPTURE_PARAMETERS = set(('mag',))

    #: The required distance parameter is 'Joyner-Boore' distance
    REQUIRES_DISTANCES = set(('rjb',))

    #: GMPE not tested against independent implementation
    non_verified = True

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.

        Implements equation 14 of Hong & Goda (2007)
        """

        C = self.COEFFS[imt]
        C_PGA = self.COEFFS[PGA()]
        C_AMP = self.AMP_COEFFS[imt]

        # Gets the PGA on rock - need to convert from g to cm/s/s
        pga_rock = self._compute_pga_rock(C_PGA, rup.mag, dists.rjb) * 980.665
        # Get the mean ground motion value
        mean = (self._compute_nonlinear_magnitude_term(C, rup.mag) +
                self._compute_magnitude_distance_term(C, dists.rjb, rup.mag) +
                self._get_site_amplification(C_AMP, sites.vs30, pga_rock))

        # Get standard deviations
        stddevs = self._get_stddevs(C, stddev_types, dists.rjb.shape)
        return mean, stddevs

    def _compute_pga_rock(self, C_PGA, mag, rjb):
        """
        Returns the PGA (g) on rock, as defined in equation 15
        """
        return np.exp(self._compute_linear_magnitude_term(C_PGA, mag) +
                      self._compute_simple_distance_term(C_PGA, rjb))

    def _compute_linear_magnitude_term(self, C, mag):
        """
        Computes the linear part of the magnitude term
        """
        return C["b1"] + C["b2"] * (mag - 7.0)

    def _compute_nonlinear_magnitude_term(self, C, mag):
        """
        Computes the non-linear magnitude term
        """
        return self._compute_linear_magnitude_term(C, mag) +\
            C["b3"] * ((mag - 7.0) ** 2.)

    def _compute_simple_distance_term(self, C, rjb):
        """
        The distance term for the PGA case ignores magnitude (equation 15)
        """
        return C["b4"] * np.log(np.sqrt(rjb ** 2. + C["h"] ** 2.))

    def _compute_magnitude_distance_term(self, C, rjb, mag):
        """
        Returns the magntude dependent distance term
        """
        rval = np.sqrt(rjb ** 2. + C["h"] ** 2.)
        return (C["b4"] + C["b5"] * (mag - 4.5)) * np.log(rval)

    def _get_site_amplification(self, C_AMP, vs30, pga_rock):
        """
        Gets the site amplification term based on equations 7 and 8 of
        Atkinson & Boore (2006)
        """
        # Get nonlinear term
        bnl = self._get_bnl(C_AMP, vs30)
        #
        f_nl_coeff = np.log(60.0 / 100.0) * np.ones_like(vs30)
        idx = pga_rock > 60.0
        f_nl_coeff[idx] = np.log(pga_rock[idx] / 100.0)
        return np.log(np.exp(
            C_AMP["blin"] * np.log(vs30 / self.CONSTS["Vref"]) +
            bnl * f_nl_coeff))

    def _get_bnl(self, C_AMP, vs30):
        """
        Gets the nonlinear term, given by equation 8 of Atkinson & Boore 2006
        """
        # Default case 8d
        bnl = np.zeros_like(vs30)
        if np.all(vs30 >= self.CONSTS["Vref"]):
            return bnl
        # Case 8a
        bnl[vs30 < self.CONSTS["v1"]] = C_AMP["b1sa"]
        # Cade 8b
        idx = np.logical_and(vs30 > self.CONSTS["v1"],
                             vs30 <= self.CONSTS["v2"])

        if np.any(idx):
            bnl[idx] = (C_AMP["b1sa"] - C_AMP["b2sa"]) *\
                (np.log(vs30[idx] / self.CONSTS["v2"]) /
                 np.log(self.CONSTS["v1"] / self.CONSTS["v2"])) + C_AMP["b2sa"]
        # Case 8c
        idx = np.logical_and(vs30 > self.CONSTS["v2"],
                             vs30 < self.CONSTS["Vref"])
        if np.any(idx):
            bnl[idx] = C_AMP["b2sa"] *\
                np.log(vs30[idx] / self.CONSTS["Vref"]) /\
                np.log(self.CONSTS["v2"] / self.CONSTS["Vref"])
        return bnl

    def _get_stddevs(self, C, stddev_types, stddev_shape):
        """
        Returns the standard deviations given in Table 2
        """
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(C["sigtot"] + np.zeros(stddev_shape))
            elif stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(C['sig2'] + np.zeros(stddev_shape))
            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(C['sig1'] + np.zeros(stddev_shape))
        return stddevs

    COEFFS = CoeffsTable(sa_damping=5, table="""\
    imt        b1       b2       b3       b4       b5     h    sig1    sig2  sigtot
    pga     1.365    0.349    0.000   -1.123    0.062   5.9   0.184   0.449   0.485
    pgv     5.540    0.931    0.000   -0.866   -0.009   3.8   0.248   0.494   0.553
    0.10    2.305   -0.084   -0.054   -1.461    0.167   8.2   0.218   0.467   0.515
    0.15    2.605   -0.045   -0.044   -1.514    0.179   8.6   0.218   0.473   0.521
    0.20    2.514    0.234   -0.053   -1.204    0.067   8.4   0.166   0.499   0.526
    0.25    2.228    0.369    0.000   -1.118    0.057   6.9   0.170   0.495   0.523
    0.30    1.762    0.515    0.000   -0.878    0.003   4.7   0.182   0.510   0.541
    0.40    1.608    0.577    0.000   -0.898    0.012   4.9   0.234   0.528   0.577
    0.50    1.713    0.837    0.000   -0.843   -0.041   6.0   0.216   0.542   0.584
    0.60    1.451    0.924   -0.030   -0.755   -0.066   5.0   0.274   0.557   0.621
    0.70    1.138    0.740   -0.093   -0.838   -0.014   4.2   0.320   0.581   0.664
    0.80    0.781    0.549   -0.182   -0.834    0.005   3.4   0.316   0.591   0.670
    0.90    0.763    0.484   -0.197   -0.960    0.052   4.0   0.324   0.594   0.677
    1.00    0.763    0.359   -0.270   -1.024    0.067   4.9   0.326   0.593   0.677
    1.10    0.827    0.596   -0.333   -0.819   -0.032   4.6   0.346   0.584   0.679
    1.20    0.853    0.845   -0.328   -0.689   -0.093   4.3   0.358   0.578   0.680
    1.30    0.682    0.921   -0.322   -0.634   -0.108   4.0   0.362   0.576   0.681
    1.40    0.540    0.954   -0.303   -0.635   -0.103   3.8   0.362   0.574   0.678
    1.50    0.433    1.005   -0.294   -0.617   -0.109   3.7   0.352   0.568   0.668
    1.60    0.289    0.988   -0.302   -0.617   -0.103   3.6   0.364   0.566   0.673
    1.70    0.102    0.976   -0.301   -0.611   -0.093   3.4   0.378   0.564   0.679
    1.80   -0.098    0.965   -0.310   -0.588   -0.088   3.0   0.380   0.560   0.676
    1.90   -0.216    0.936   -0.325   -0.601   -0.079   2.9   0.380   0.561   0.677
    2.00   -0.379    0.693   -0.308   -0.759   -0.001   2.7   0.364   0.562   0.670
    2.20   -0.549    0.643   -0.336   -0.776    0.011   2.5   0.378   0.570   0.684
    2.40   -0.663    0.772   -0.325   -0.706   -0.016   2.3   0.402   0.570   0.697
    2.60   -0.747    0.909   -0.302   -0.655   -0.039   2.3   0.404   0.575   0.703
    2.80   -0.883    1.024   -0.259   -0.630   -0.045   2.2   0.414   0.584   0.716
    3.00   -0.955    1.027   -0.265   -0.677   -0.029   2.3   0.420   0.594   0.728
    """)

    AMP_COEFFS = CoeffsTable(sa_damping=5, table="""\
    imt           blin       b1sa       b2sa
    pgv       -0.60000   -0.49500   -0.06000
    pga       -0.36100   -0.64100   -0.14400
    0.02500   -0.33000   -0.62400   -0.11500
    0.03125   -0.32200   -0.61800   -0.10800
    0.04000   -0.31400   -0.60900   -0.10500
    0.05000   -0.28600   -0.64300   -0.10500
    0.06289   -0.24900   -0.64200   -0.10500
    0.07937   -0.23200   -0.63700   -0.11700
    0.10000   -0.25000   -0.59500   -0.13200
    0.12500   -0.26000   -0.56000   -0.14000
    0.15873   -0.28000   -0.52800   -0.18500
    0.20000   -0.30600   -0.52100   -0.18500
    0.25000   -0.39000   -0.51800   -0.16000
    0.31250   -0.44500   -0.51300   -0.13000
    0.40000   -0.50000   -0.50800   -0.09500
    0.50000   -0.60000   -0.49500   -0.06000
    0.62500   -0.67000   -0.48000   -0.03100
    0.76923   -0.69000   -0.46500   -0.00200
    1.00000   -0.70000   -0.44000    0.00000
    1.58730   -0.72600   -0.39500    0.00000
    2.00000   -0.73000   -0.37500    0.00000
    3.12500   -0.74000   -0.33000    0.00000
    4.00000   -0.74500   -0.31000    0.00000
    5.00000   -0.75200   -0.30000    0.00000
    """)

    CONSTS = {"Vref": 760.0,
              "v1": 180.0,
              "v2": 300.0}
