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
Module exports :class:'AllenEtAl2012',
                      'AllenEtAl2012Rhypo'
"""
from __future__ import division
import numpy as np

from openquake.hazardlib.gsim.base import IPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import MMI


class AllenEtAl2012(IPE):
    """
    Implements the Intensity Prediction Equation of Allen, Wald and Worden
    (2012) for Modified Mercalli Intensity in Active Crustal Regions
    Allen, T. I., Wald, D. J. and Worden, C. B. (2012) Intensity attenuation
    in active crustal regions, J. Seismology, 16: 409 - 433

    This class implements the version using rupture distance, neglecting
    site amplification
    """
    #: The GMPE is derived from induced earthquakes
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are peak ground acceleration
    #: and peak ground velocity
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        MMI,
    ])

    #: Supported intensity measure component is not considered for IPEs, so
    #: we assume equivalent to 'average horizontal'
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Supported standard deviation types is total.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL
    ])

    #: No required site parameters (in the present version)
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameters are magnitude (ML is used)
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
        mean = (self._compute_magnitude_term(C, rup.mag) +
                self._compute_distance_term(C, dists.rrup, rup.mag))
        stddevs = self._get_stddevs(C, dists.rrup, stddev_types)
        return mean, stddevs

    def _compute_magnitude_term(self, C, mag):
        """
        Returns the magnitude scaling term
        """
        return C["c0"] + (C["c1"] * mag)

    def _compute_distance_term(self, C, rrup, mag):
        """
        Returns the distance scaling term
        """
        exponent_term = (1.0 + C["c3"] * np.exp(mag - 5.)) ** 2.
        return C["c2"] * np.log(np.sqrt(rrup ** 2. + exponent_term))

    def _get_stddevs(self, C, distance, stddev_types):
        """
        Returns the total standard deviation, which is a function of distance
        """
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                sigma = C["s1"] + (C["s2"] / (1.0 +
                                   ((distance / C["s3"]) ** 2.)))
                stddevs.append(sigma + np.zeros_like(distance))
        return stddevs

    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT     c0     c1      c2     c3    s1     s2    s3
    mmi  3.950  0.913  -1.107  0.813  0.72   0.23  44.7
    """)


class AllenEtAl2012Rhypo(AllenEtAl2012):
    """
    Version of the Allen, Wald and Worden (2012) IPE for hypocentral distance
    """
    #: Required distance measure is hypocentral distance
    REQUIRES_DISTANCES = set(('rhypo',))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        C = self.COEFFS[imt]

        mean = (self._compute_magnitude_term(C, rup.mag) +
                self._compute_distance_term(C, dists.rhypo, rup.mag))
        stddevs = self._get_stddevs(C, dists.rhypo, stddev_types)
        return mean, stddevs

    def _compute_distance_term(self, C, rhypo, mag):
        """
        Returns the distance scaling term
        """
        r_m = C["m1"] + C["m2"] * np.exp(mag - 5.)
        f_r = C["c2"] * np.log(np.sqrt(rhypo ** 2. + r_m ** 2.))
        # For distances greater than 50 km an anelastic term is added
        idx = rhypo > 50.0
        f_r[idx] += C["c4"] * np.log(rhypo[idx] / 50.)
        return f_r

    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT     c0     c1      c2   c3     c4      m1      m2     s1     s2    s3
    mmi  2.085  1.428  -1.402  0.0  0.078  -0.209   2.042   0.82   0.37  22.9
    """)
