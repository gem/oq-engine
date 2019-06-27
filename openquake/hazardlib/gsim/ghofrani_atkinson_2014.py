# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2019 GEM Foundation
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
Module exports :class:`GhofraniAtkinson2014`,
               :class:`GhofraniAtkinson2014Cascadia`,
               :class:`GhofraniAtkinson2014Lower`,
               :class:`GhofraniAtkinson2014Upper`,
               :class:`GhofraniAtkinson2014CascadiaLower`,
               :class:`GhofraniAtkinson2014CascadiaUpper`
"""
import numpy as np
# standard acceleration of gravity in m/s**2
from scipy.constants import g


from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA


class GhofraniAtkinson2014(GMPE):
    """
    Implements the Subduction Interface GMPE of Ghofrani & Atkinson (2014)
    for large magnitude earthquakes, based on the Tohoku records.
    Ghofrani, H. and Atkinson, G. M. (2014) Ground Motion Prediction Equations
    for Interface Earthquakes of M7 to M9 based on Empirical Data from Japan.
    Bulletin of Earthquake Engineering, 12, 549 - 571
    """
    #: The GMPE is derived for subduction interface earthquakes in Japan
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    #: Supported intensity measure types are peak ground acceleration,
    #: peak ground velocity and spectral acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        PGV,
        SA
    ])

    #: Supported intensity measure component is assumed to be geometric mean
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Supported standard deviation types is total.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT,
        const.StdDev.TOTAL,
    ])

    #: The GMPE provides a Vs30-dependent site scaling term and a forearc/
    #: backarc attenuation term
    REQUIRES_SITES_PARAMETERS = set(('vs30', 'backarc'))

    #: Required rupture parameters are magnitude
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', ))

    #: Required distance measure is rupture distance
    REQUIRES_DISTANCES = set(('rrup',))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        C = self.COEFFS[imt]

        imean = (self._get_magnitude_term(C, rup.mag) +
                 self._get_distance_term(C, dists.rrup, sites.backarc) +
                 self._get_site_term(C, sites.vs30) +
                 self._get_scaling_term(C, dists.rrup))
        # Convert mean from cm/s and cm/s/s and from common logarithm to
        # natural logarithm
        if imt.name in "SA PGA":
            mean = np.log((10.0 ** (imean - 2.0)) / g)
        else:
            mean = np.log((10.0 ** (imean)))
        stddevs = self._get_stddevs(C, len(dists.rrup), stddev_types)
        return mean, stddevs

    def _get_magnitude_term(self, C, mag):
        """
        Returns the linear magnitude scaling term
        """
        return C["a"] + C["b"] * mag

    def _get_distance_term(self, C, rrup, backarc):
        """
        Returns the distance scaling term, which varies depending on whether
        the site is in the forearc or the backarc
        """
        # Geometric attenuation function
        distance_scale = -np.log10(np.sqrt(rrup ** 2 + 3600.0))
        # Anelastic attenuation in the backarc
        distance_scale[backarc] += (C["c2"] * rrup[backarc])
        # Anelastic Attenuation in the forearc
        idx = np.logical_not(backarc)
        distance_scale[idx] += (C["c1"] * rrup[idx])
        return distance_scale

    def _get_scaling_term(self, C, rrup):
        """
        Returns a scaling term, which is over-ridden in subclasses
        """
        return 0.0

    def _get_site_term(self, C, vs30):
        """
        Returns the linear site scaling term
        """
        return C["c3"] * np.log10(vs30 / 760.0)

    def _get_stddevs(self, C, num_sites, stddev_types):
        """
        Returns the total, inter-event or intra-event standard deviation
        """
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                sig_tot = np.sqrt(C["tau"] ** 2. + C["sigma"] ** 2.)
                stddevs.append(np.log(10.0 ** sig_tot) + np.zeros(num_sites))
            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(
                    np.log(10.0 ** C["tau"]) + np.zeros(num_sites))
            elif stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(
                    np.log(10.0 ** C["sigma"]) + np.zeros(num_sites))
        return stddevs

    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT        c0         a        b         c1         c2       c3   sig_init       af   sigma     tau   sig_tot
    pgv    3.3900    0.8540   0.2795   -0.00070   -0.00099   -0.331      0.195    0.000   0.195   0.138     0.238
    pga    4.6460    2.8193   0.1908   -0.00219   -0.00298   -0.219      0.284   -0.301   0.284   0.196     0.345
    0.07   4.8880    3.1807   0.1759   -0.00236   -0.00329   -0.046      0.313   -0.357   0.313   0.215     0.380
    0.09   5.0220    3.3592   0.1700   -0.00244   -0.00346    0.027      0.326   -0.357   0.326   0.220     0.393
    0.11   5.0820    3.4483   0.1669   -0.00245   -0.00356    0.010      0.329   -0.319   0.329   0.218     0.394
    0.14   5.0720    3.5005   0.1604   -0.00240   -0.00357   -0.082      0.324   -0.272   0.324   0.212     0.387
    0.18   5.0510    3.4463   0.1650   -0.00235   -0.00358   -0.180      0.312   -0.237   0.312   0.206     0.374
    0.22   5.0150    3.3178   0.1763   -0.00235   -0.00355   -0.289      0.310   -0.183   0.310   0.202     0.370
    0.27   4.9580    3.2008   0.1839   -0.00233   -0.00346   -0.386      0.312   -0.114   0.312   0.199     0.370
    0.34   4.9070    3.0371   0.1970   -0.00231   -0.00333   -0.438      0.307   -0.046   0.307   0.191     0.361
    0.42   4.8200    2.7958   0.2154   -0.00224   -0.00315   -0.520      0.295    0.002   0.295   0.171     0.341
    0.53   4.7060    2.5332   0.2331   -0.00213   -0.00290   -0.606      0.276    0.007   0.276   0.155     0.316
    0.65   4.5870    2.3234   0.2435   -0.00200   -0.00262   -0.672      0.257    0.011   0.257   0.147     0.296
    0.81   4.4640    2.1321   0.2522   -0.00183   -0.00234   -0.705      0.249    0.014   0.249   0.131     0.281
    1.01   4.3360    1.9852   0.2561   -0.00158   -0.00205   -0.690      0.249    0.021   0.249   0.115     0.274
    1.25   4.2140    1.8442   0.2599   -0.00133   -0.00177   -0.646      0.261    0.089   0.261   0.110     0.283
    1.56   4.1050    1.6301   0.2730   -0.00112   -0.00152   -0.578      0.274    0.139   0.274   0.113     0.296
    1.92   3.9900    1.4124   0.2851   -0.00086   -0.00125   -0.518      0.285    0.174   0.285   0.121     0.310
    2.44   3.8290    1.1154   0.3015   -0.00059   -0.00097   -0.513      0.275    0.129   0.275   0.132     0.305
    3.03   3.6570    0.7965   0.3197   -0.00039   -0.00075   -0.554      0.264    0.079   0.264   0.137     0.298
    3.70   3.5020    0.5093   0.3361   -0.00023   -0.00057   -0.574      0.252    0.044   0.252   0.138     0.287
    4.55   3.3510    0.2578   0.3497   -0.00005   -0.00040   -0.561      0.237    0.013   0.237   0.147     0.279
    5.88   3.2320   -0.1469   0.3835    0.00000   -0.00027   -0.491      0.218    0.000   0.218   0.151     0.265
    7.14   3.1220   -0.5012   0.4119    0.00000   -0.00019   -0.462      0.201    0.000   0.201   0.148     0.250
    9.09   2.9850   -1.0932   0.4641    0.00000   -0.00019   -0.413      0.175    0.000   0.175   0.155     0.233
    """)


class GhofraniAtkinson2014Cascadia(GhofraniAtkinson2014):
    """
    Implements the Subduction Interface GMPE of Ghofrani & Atkinson (2014)
    adapted for application to Cascadia
    """

    def _get_scaling_term(self, C, rrup):
        """
        Applies the log of the Cascadia multiplicative factor (as defined in
        Table 2)
        """
        return C["af"]


class GhofraniAtkinson2014Upper(GhofraniAtkinson2014):
    """
    Implements the Subduction Interface GMPE of Ghofrani & Atkinson (2014)
    with the "upper" epistemic uncertainty model
    """
    def _get_scaling_term(self, C, rrup):
        """
        Applies the positive correction factor given on Page 567
        """
        a_f = 0.15 + 0.0007 * rrup
        a_f[a_f > 0.35] = 0.35
        return a_f


class GhofraniAtkinson2014Lower(GhofraniAtkinson2014):
    """
    Implements the Subduction Interface GMPE of Ghofrani & Atkinson (2014)
    with the "lower" epistemic uncertainty model
    """
    def _get_scaling_term(self, C, rrup):
        """
        Applies the negative correction factor given on Page 567
        """
        a_f = 0.15 + 0.0007 * rrup
        a_f[a_f > 0.35] = 0.35
        return -a_f


class GhofraniAtkinson2014CascadiaUpper(GhofraniAtkinson2014):
    """
    Implements the Subduction Interface GMPE of Ghofrani & Atkinson (2014)
    with the "upper" epistemic uncertainty model and the Cascadia correction
    term.
    """
    def _get_scaling_term(self, C, rrup):
        """
        Applies the Cascadia correction factor from Table 2 and the positive
        correction factor given on Page 567
        """
        a_f = 0.15 + 0.0007 * rrup
        a_f[a_f > 0.35] = 0.35
        return C["af"] + a_f


class GhofraniAtkinson2014CascadiaLower(GhofraniAtkinson2014):
    """
    Implements the Subduction Interface GMPE of Ghofrani & Atkinson (2014)
    with the "lower" epistemic uncertainty model and the Cascadia correction
    term.
    """
    def _get_scaling_term(self, C, rrup):
        """
        Applies the Cascadia correction factor from Table 2 and the negative
        correction factor given on Page 567
        """
        a_f = 0.15 + 0.0007 * rrup
        a_f[a_f > 0.35] = 0.35
        return C["af"] - a_f
