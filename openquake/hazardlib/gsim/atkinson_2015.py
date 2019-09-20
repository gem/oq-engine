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
Module exports :class:'Atkinson2015'
"""
import numpy as np
# standard acceleration of gravity in m/s**2
from scipy.constants import g


from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA


class Atkinson2015(GMPE):
    """
    Implements the Induced Seismicity GMPE of Atkinson (2015)
    Atkinson, G. A. (2015) Ground-Motion Prediction Equation for Small-to-
    Moderate Events at Short Hypocentral Distances, with Application to
    Induced-Seismicity Hazards. Bulletin of the Seismological Society of
    America. 105(2).
    """
    #: The GMPE is derived from induced earthquakes
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.INDUCED

    #: Supported intensity measure types are peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        PGV,
        SA
    ])

    #: Supported intensity measure component is the larger of two components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    #: Supported standard deviation types is total.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT 
    ])

    #: No required site parameters, the GMPE is derived for B/C site
    #: amplification factors
    REQUIRES_SITES_PARAMETERS = set(())

    #: Required rupture parameters are magnitude
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', ))

    #: Required distance measure is hypocentral distance
    REQUIRES_DISTANCES = set(('rhypo',))

    #: GMPE not tested against independent implementation so raise
    #: not verified warning
    non_verified = True

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        C = self.COEFFS[imt]

        imean = (self._get_magnitude_term(C, rup.mag) +
                 self._get_distance_term(C, dists.rhypo, rup.mag))
        # Convert mean from cm/s and cm/s/s
        if imt.name in "SA PGA":
            mean = np.log((10.0 ** (imean - 2.0)) / g)
        else:
            mean = np.log(10.0 ** imean)
        stddevs = self._get_stddevs(C, len(dists.rhypo), stddev_types)
        return mean, stddevs

    def _get_magnitude_term(self, C, mag):
        """
        Returns the magnitude scaling term
        """
        return C["c0"] + (C["c1"] * mag) + (C["c2"] * (mag ** 2.0))

    def _get_distance_term(self, C, rhypo, mag):
        """
        Returns the distance scaling term
        """
        h_eff = self._get_effective_distance(mag)
        r_val = np.sqrt(rhypo ** 2.0 + h_eff ** 2.0)
        return C["c3"] * np.log10(r_val)

    def _get_effective_distance(self, mag):
        """
        Returns the effective distance term in equation 3. This may be
        overwritten in sub-classes
        """
        h_eff = 10.0 ** (-1.72 + 0.43 * mag)
        if h_eff > 1.0:
            return h_eff
        else:
            return 1.0

    def _get_stddevs(self, C, num_sites, stddev_types):
        """
        Return standard deviations, converting from log10 to log
        """
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(
                    np.log(10.0 ** C["sigma"]) + np.zeros(num_sites))
            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(np.log(10.0 ** C["tau"]) + np.zeros(num_sites))
            elif stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(np.log(10.0 ** C["phi"]) + np.zeros(num_sites))
        return stddevs

    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT         c0      c1         c2      c3    phi    tau    sigma
    pgv     -4.151   1.762  -0.09509   -1.669   0.27   0.19     0.33
    pga     -2.376   1.818  -0.1153    -1.752   0.28   0.24     0.37
    0.0303  -2.283   1.842  -0.1189    -1.785   0.28   0.27     0.39
    0.0500  -2.018   1.826  -0.1192    -1.831   0.28   0.30     0.41
    0.1000  -1.954   1.830  -0.1185    -1.774   0.29   0.25     0.39
    0.2000  -2.266   1.785  -0.1061    -1.657   0.30   0.21     0.37
    0.3000  -2.794   1.852  -0.1078    -1.608   0.30   0.19     0.36
    0.5000  -3.873   2.060  -0.1212    -1.544   0.29   0.20     0.35
    1.0000  -4.081   1.742  -0.07381   -1.481   0.26   0.22     0.34
    2.0000  -4.462   1.485  -0.03815   -1.361   0.24   0.23     0.33
    3.0303  -3.827   1.060   0.009086  -1.398   0.24   0.22     0.32
    5.0000  -4.321   1.080   0.009376  -1.378   0.25   0.18     0.31
    """)
