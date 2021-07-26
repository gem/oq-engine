# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2021 GEM Foundation
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


def _get_magnitude_term(C, mag):
    """
    Returns the magnitude scaling term
    """
    return C["c0"] + (C["c1"] * mag) + (C["c2"] * (mag ** 2.0))


def _get_distance_term(C, rhypo, mag):
    """
    Returns the distance scaling term including the apparent anelastic
    attenuation term (C4 * R)
    """
    h_eff = _get_effective_distance(mag)
    r_val = np.sqrt(rhypo ** 2.0 + h_eff ** 2.0)
    return C["c3"] * np.log10(r_val) + C["c4"] * r_val


def _get_effective_distance(mag):
    """
    Returns the effective distance term in equation 3. This may be
    overwritten in sub-classes
    """
    h_eff = 10.0 ** (-1.72 + 0.43 * mag)
    if h_eff > 1.0:
        return h_eff
    else:
        return 1.0


def _get_stddevs(C, num_sites, stddev_types):
    """
    Return standard deviations, converting from log10 to log
    """
    stddevs = []
    for stddev_type in stddev_types:
        if stddev_type == const.StdDev.TOTAL:
            stddevs.append(
                np.log(10.0 ** C["sigma"]) + np.zeros(num_sites))
        elif stddev_type == const.StdDev.INTER_EVENT:
            stddevs.append(np.log(10.0 ** C["tau"]) + np.zeros(num_sites))
        elif stddev_type == const.StdDev.INTRA_EVENT:
            stddevs.append(np.log(10.0 ** C["phi"]) + np.zeros(num_sites))
    return stddevs


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
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    #: Supported intensity measure component is the larger of two components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    #: Supported standard deviation types is total.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: No required site parameters, the GMPE is derived for B/C site
    #: amplification factors
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameters are magnitude
    REQUIRES_RUPTURE_PARAMETERS = {'mag', }

    #: Required distance measure is hypocentral distance
    REQUIRES_DISTANCES = {'rhypo'}

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        C = self.COEFFS[imt]

        imean = (_get_magnitude_term(C, rup.mag) +
                 _get_distance_term(C, dists.rhypo, rup.mag))
        # Convert mean from cm/s and cm/s/s
        if imt.string.startswith(('PGA', 'SA')):
            mean = np.log((10.0 ** (imean - 2.0)) / g)
        else:
            mean = np.log(10.0 ** imean)
        stddevs = _get_stddevs(C, len(dists.rhypo), stddev_types)
        return mean, stddevs

    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT         c0      c1         c2      c3         c4    phi    tau    sigma
    pgv     -4.151   1.762  -0.09509   -1.669   -0.00060   0.27   0.19     0.33
    pga     -2.376   1.818  -0.1153    -1.752   -0.00200   0.28   0.24     0.37
    0.0300  -2.283   1.842  -0.1189    -1.785   -0.00200   0.28   0.27     0.39
    0.0500  -2.018   1.826  -0.1192    -1.831   -0.00200   0.28   0.30     0.41
    0.1000  -1.954   1.830  -0.1185    -1.774   -0.00200   0.29   0.25     0.39
    0.2000  -2.266   1.785  -0.1061    -1.657   -0.00140   0.30   0.21     0.37
    0.3000  -2.794   1.852  -0.1078    -1.608   -0.00100   0.30   0.19     0.36
    0.5000  -3.873   2.060  -0.1212    -1.544   -0.00060   0.29   0.20     0.35
    1.0000  -4.081   1.742  -0.07381   -1.481    0.00000   0.26   0.22     0.34
    2.0000  -4.462   1.485  -0.03815   -1.361    0.00000   0.24   0.23     0.33
    3.0000  -3.827   1.060   0.009086  -1.398    0.00000   0.24   0.22     0.32
    5.0000  -4.321   1.080   0.009376  -1.378    0.00000   0.25   0.18     0.31
    """)
