# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2017 GEM Foundation
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
Module exports :class:`Idriss2014`,
"""
from __future__ import division

import numpy as np

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


class Idriss2014(GMPE):
    """
    Implements GMPE developed by Idriss 2014 and published as "An NGA-West2
    Empirical Model for Estimating the Horizontal Spectral Values Generated
    by Shallow Crustal Earthquakes.
    (2014, Earthquake Spectra, Volume 30, No. 3, pages 1155 - 1177).

    Idriss (2014) defines the GMPE only for the case in which Vs30 >= 450 m/s.
    In the present implementation no check is made for the use of this model
    for sites with Vs30 < 450 m/s
    """
    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are spectral acceleration,
    #:and peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        SA
    ])

    #: Supported intensity measure component is orientation-independent
    #: measure :attr:`~openquake.hazardlib.const.IMC.RotD50`
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    #: Supported standard deviation types are total
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
    ])

    #: Required site parameters is Vs30
    REQUIRES_SITES_PARAMETERS = set(('vs30', ))

    #: Required rupture parameters are magnitude, and rake.
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', 'rake'))

    #: Required distance measure is Rrup
    REQUIRES_DISTANCES = set(('rrup', ))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extracting dictionary of coefficients specific to required
        # intensity measure type.
        C = self.COEFFS[imt]

        mean = (self._get_magnitude_scaling_term(C, rup.mag) +
                self._get_distance_scaling_term(C, rup.mag, dists.rrup) +
                self._get_style_of_faulting_term(C, rup.rake) +
                self._get_site_scaling_term(C, sites.vs30))

        stddevs = self._get_stddevs(imt,
                                    rup.mag,
                                    len(dists.rrup),
                                    stddev_types)
        return mean, stddevs

    def _get_magnitude_scaling_term(self, C, mag):
        """
        Returns the magnitude scaling term defined in equation 3
        """
        if mag < 6.75:
            return C["a1_lo"] + C["a2_lo"] * mag + C["a3"] *\
                ((8.5 - mag) ** 2.0)
        else:
            return C["a1_hi"] + C["a2_hi"] * mag + C["a3"] *\
                ((8.5 - mag) ** 2.0)

    def _get_distance_scaling_term(self, C, mag, rrup):
        """
        Returns the magnitude dependent distance scaling term
        """
        if mag < 6.75:
            mag_factor = -(C["b1_lo"] + C["b2_lo"] * mag)
        else:
            mag_factor = -(C["b1_hi"] + C["b2_hi"] * mag)
        return mag_factor * np.log(rrup + 10.0) + (C["gamma"] * rrup)

    def _get_style_of_faulting_term(self, C, rake):
        """
        Only distinction is between reverse faulting events and
        normal/strike-slip. Returns the style-of-faulting factor only for
        reverse events
        """
        if (rake > 30.0) and (rake < 150.0):
            return C["phi"]
        else:
            return 0.0

    def _get_site_scaling_term(self, C, vs30):
        """
        Returns the site scaling. For sites with Vs30 > 1200 m/s the site
        amplification for Vs30 = 1200 is used
        """
        site_amp = C["xi"] * np.log(1200.0) * np.ones(len(vs30))
        idx = vs30 < 1200.0
        site_amp[idx] = C["xi"] * np.log(vs30[idx])
        return site_amp

    def _get_stddevs(self, imt, mag, n_sites, stddev_types):
        """
        The standard error (assumed equivalent to total standard deviation)
        is defined as a function of magnitude and period (equation 4,
        page 1168). For magnitudes lower than 5.0 the standard deviation is
        equal to that for the case in which magnitude is 5.0. For short
        periods (T < 0.05), including PGA, the standard deviation is
        assumed to be equal to the case in which T = 0.05, whilst for long
        periods (T > 3.0) it is assumed to be equal to the case in which
        T = 3.0
        """
        if mag < 5.0:
            stddev_mag = 5.0
        else:
            stddev_mag = mag

        if isinstance(imt, PGA) or (imt.period < 0.05):
            total_sigma = 1.18 + 0.035 * np.log(0.05) - 0.06 * stddev_mag
        elif imt.period > 3.0:
            total_sigma = 1.18 + 0.035 * np.log(3.0) - 0.06 * stddev_mag
        else:
            total_sigma = 1.18 + 0.035 * np.log(imt.period) - 0.06 * stddev_mag
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(total_sigma + np.zeros(n_sites, dtype=float))
        return stddevs

    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT       a1_lo    a2_lo    b1_lo     b2_lo     a1_hi     a2_hi    b1_hi    b2_hi         a3        xi     gamma      phi
    pga      7.0887   0.2058   2.9935   -0.2287    9.0138   -0.0794   2.9935   -0.2287    0.0589   -0.8540   -0.0027   0.0800
    0.010    7.0887   0.2058   2.9935   -0.2287    9.0138   -0.0794   2.9935   -0.2287    0.0589   -0.8540   -0.0027   0.0800
    0.020    7.1157   0.2058   2.9935   -0.2287    9.0408   -0.0794   2.9935   -0.2287    0.0589   -0.8540   -0.0027   0.0800
    0.030    7.2087   0.2058   2.9935   -0.2287    9.1338   -0.0794   2.9935   -0.2287    0.0589   -0.8540   -0.0027   0.0800
    0.050    6.2638   0.0625   2.8664   -0.2418    7.9837   -0.1923   2.7995   -0.2319    0.0417   -0.6310   -0.0061   0.0800
    0.075    5.9051   0.1128   2.9406   -0.2513    7.7560   -0.1614   2.8143   -0.2326    0.0527   -0.5910   -0.0056   0.0800
    0.100    7.5791   0.0848   3.0190   -0.2516    9.4252   -0.1887   2.8131   -0.2211    0.0442   -0.7570   -0.0042   0.0800
    0.150    8.0190   0.1713   2.7871   -0.2236    9.6242   -0.0665   2.4091   -0.1676    0.0329   -0.9110   -0.0046   0.0800
    0.200    9.2812   0.1041   2.8611   -0.2229   11.1300   -0.1698   2.4938   -0.1685    0.0188   -0.9980   -0.0030   0.0800
    0.250    9.5804   0.0875   2.8289   -0.2200   11.3629   -0.1766   2.3773   -0.1531    0.0095   -1.0420   -0.0028   0.0800
    0.300    9.8912   0.0003   2.8423   -0.2284   11.7818   -0.2798   2.3772   -0.1595   -0.0039   -1.0300   -0.0029   0.0800
    0.400    9.5342   0.0027   2.8300   -0.2318   11.6097   -0.3048   2.3413   -0.1594   -0.0133   -1.0190   -0.0028   0.0800
    0.500    9.2142   0.0399   2.8560   -0.2337   11.4484   -0.2911   2.3477   -0.1584   -0.0224   -1.0230   -0.0021   0.0800
    0.750    8.3517   0.0689   2.7544   -0.2392   10.9065   -0.3097   2.2042   -0.1577   -0.0267   -1.0560   -0.0029   0.0800
    1.000    7.0453   0.1600   2.7339   -0.2398    9.8565   -0.2565   2.1493   -0.1532   -0.0198   -1.0090   -0.0032   0.0600
    1.500    5.1307   0.2429   2.6800   -0.2417    8.3363   -0.2320   2.0408   -0.1470   -0.0367   -0.8980   -0.0033   0.0400
    2.000    3.3610   0.3966   2.6837   -0.2450    6.8656   -0.1226   2.0013   -0.1439   -0.0291   -0.8510   -0.0032   0.0200
    3.000    0.1784   0.7560   2.6907   -0.2389    4.1178    0.1724   1.9408   -0.1278   -0.0214   -0.7610   -0.0031   0.0200
    4.000   -2.4301   0.9283   2.5782   -0.2514    1.8102    0.3001   1.7763   -0.1326   -0.0240   -0.6750   -0.0051   0.0000
    5.000   -4.3570   1.1209   2.5468   -0.2541    0.0977    0.4609   1.7030   -0.1291   -0.0202   -0.6290   -0.0059   0.0000
    7.500   -7.8275   1.4016   2.4478   -0.2593   -3.0563    0.6948   1.5212   -0.1220   -0.0219   -0.5310   -0.0057   0.0000
    10.00   -9.2857   1.5574   2.3922   -0.2586   -4.4387    0.8393   1.4195   -0.1145   -0.0035   -0.5860   -0.0061   0.0000
    """)
