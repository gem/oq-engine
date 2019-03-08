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
Module exports :class:'DostEtAl2004'
"""
import numpy as np
# standard acceleration of gravity in m/s**2
from scipy.constants import g

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV


class DostEtAl2004(GMPE):
    """
    Implements the GMPE of Dost et al. (2004) for PGA and PGV from
    induced seismicity earthquakes in the Netherlands
    Dost, B., van Eck, T. and Haak, H. (2004) Scaling of peak ground
    acceleration and peak ground velocity recorded in the Netherlands.
    Bollettino di Geofisica Teorica ed Applicata. 45(3), 153 - 168
    """
    #: The GMPE is derived from induced earthquakes
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.INDUCED

    #: Supported intensity measure types are peak ground acceleration
    #: and peak ground velocity
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        PGV
    ])

    #: Supported intensity measure component is the average horizontal
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GMRotD100

    #: Supported standard deviation types is total.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL 
    ])

    #: No required site parameters
    REQUIRES_SITES_PARAMETERS = set(())

    #: Required rupture parameters are magnitude (ML is used)
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

        imean = (self._compute_magnitude_term(C, rup.mag) +
                 self._compute_distance_term(C, dists.rhypo))
        # Convert mean from cm/s and cm/s/s
        if imt.name == "PGA":
            mean = np.log((10.0 ** (imean)) / g)
        else:
            mean = np.log(10.0 ** imean)
        stddevs = self._get_stddevs(C, len(dists.rhypo), stddev_types)
        return mean, stddevs

    def _compute_magnitude_term(self, C, mag):
        """
        Returns the magnitude scaling term
        """
        return C["c0"] + (C["c1"] * mag)

    def _compute_distance_term(self, C, rhypo):
        """
        Returns the distance scaling term
        """
        return (C["c2"] * rhypo) + (C["c3"] * np.log10(rhypo))

    def _get_stddevs(self, C, num_sites, stddev_types):
        """
        Returns the total standard deviation
        """
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(
                    np.log(10.0 ** C["sigma"]) + np.zeros(num_sites))
        return stddevs

    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT     c0     c1        c2      c3   sigma
    pgv  -1.53   0.74  -0.00139   -1.33    0.33
    pga  -1.41   0.57  -0.00139   -1.33    0.33
    """)


class DostEtAl2004BommerAdaptation(DostEtAl2004):
    """
    Adaptation of the GMPE for application to higher magnitudes proposed
    by Bommer et al. (2013)
    """
    #: Supported standard deviation types is total.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    ])

    def _compute_magnitude_term(self, C, mag):
        """
        Returns the magnitude scaling term
        """
        return C["c0"] + (C["c1"] * mag) + (C["c1e"] * ((mag - 4.5) ** 2.0))
    
    def _get_stddevs(self, C, num_sites, stddev_types):
        """
        Returns the the total, inter-event and intra-event standard deviation
        """
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(
                    np.log(10.0 ** C["sigma"]) + np.zeros(num_sites))
            if stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(
                    np.log(10.0 ** C["tau"]) + np.zeros(num_sites))
            if stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(
                    np.log(10.0 ** C["phi"]) + np.zeros(num_sites))
        return stddevs

    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT     c0         c1       c1e         c2      c3     tau     phi  sigma
    pgv  -1.3972   0.7105   -0.0829   -0.00139   -1.33  0.1476  0.2952   0.33
    pga  -1.6090   0.6140   -0.1116   -0.00139   -1.33  0.1476  0.2952   0.33
    """)
