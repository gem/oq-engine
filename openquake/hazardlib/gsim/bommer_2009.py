# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2019 GEM Foundation
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
Module exports :class:`BommerEtAl2009RSD`
"""
import numpy as np

from openquake.hazardlib.gsim.base import CoeffsTable, GMPE
from openquake.hazardlib import const
from openquake.hazardlib.imt import RSD595, RSD575


class BommerEtAl2009RSD(GMPE):
    """
    Implements the GMPE of Bommer et al. (2009) for significant duration with
    5 - 75 % Arias Intensity and 5 - 95 % Arias Intensity
    """
    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are 5 - 95 % Arias and 5 - 75 % Arias
    #: significant duration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        RSD595,
        RSD575
    ])

    #: Supported intensity measure component is the geometric mean horizontal
    #: component
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Supported standard deviation type is only total, see table 7, page 35
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    ])

    #: Requires vs30
    REQUIRES_SITES_PARAMETERS = set(('vs30',))

    #: Required rupture parameters are magnitude and top of rupture depth
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', 'ztor'))

    #: Required distance measure is closest distance to rupture
    REQUIRES_DISTANCES = set(('rrup', ))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        C = self.COEFFS[imt]
        mean = (self.get_magnitude_term(C, rup.mag) +
                self.get_distance_term(C, dists.rrup, rup.mag) +
                self.get_ztor_term(C, rup.ztor) +
                self.get_site_amplification(C, sites.vs30))

        stddevs = self.get_stddevs(C, dists.rrup.shape, stddev_types)
        return mean, stddevs

    def get_magnitude_term(self, C, mag):
        """
        Returns linear magnitude scaling term
        """
        return C["c0"] + C["m1"] * mag

    def get_distance_term(self, C, rrup, mag):
        """
        Returns distance scaling term
        """
        return (C["r1"] + C["r2"] * mag) *\
            np.log(np.sqrt(rrup ** 2. + C["h1"] ** 2.))

    def get_ztor_term(self, C, ztor):
        """
        Returns depth to top of rupture scaling
        """
        return C["z1"] * ztor

    def get_site_amplification(self, C, vs30):
        """
        Returns linear site amplification term
        """
        return C["v1"] * np.log(vs30)

    def get_stddevs(self, C, nsites, stddev_types):
        """
        Returns the standard deviations
        """
        stddevs = []
        zeros_array = np.zeros(nsites)
        for stddev in stddev_types:
            assert stddev in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev == const.StdDev.TOTAL:
                stddevs.append(np.sqrt(C["tau"] ** 2. + C["phi"] ** 2.) +
                               zeros_array)
            elif stddev == const.StdDev.INTER_EVENT:
                stddevs.append(C["tau"] + zeros_array)
            elif stddev == const.StdDev.INTRA_EVENT:
                stddevs.append(C["phi"] + zeros_array)
        return stddevs

    COEFFS = CoeffsTable(sa_damping=5, table="""\
    imt          c0       m1      r1       r2      h1       v1       z1     tau     phi
    rsd575  -5.6298   1.2619  2.0063  -0.2520  2.3316  -0.2900  -0.0522  0.3527  0.4304
    rsd595  -2.2393   0.9368  1.5686  -0.1953  2.5000  -0.3478  -0.0365  0.3252  0.3460
    """)
