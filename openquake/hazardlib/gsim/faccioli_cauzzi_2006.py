# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2018 GEM Foundation
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
Module exports :
class:`FaccioliCauzzi2006`
"""

import numpy as np

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import MMI


class FaccioliCauzzi2006(GMPE):
    """
    Implements "Macroseismic Intensities for seismic scenarios estimated from
    instrumentally based correlations" by E. Faccioli and C. Cauzzi
    First European Conference on Earthquake Engineering and Seismology
    Geneva, Switzerland, 3-8 September 2006
    Paper Number: 569

    Implemented by laurentiu.danciu@sed.ethz.ch
    """

    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {MMI}

    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.HORIZONTAL

    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    REQUIRES_SITES_PARAMETERS = set()

    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    REQUIRES_DISTANCES = {'repi'}

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extract dictionaries of coefficients specific to required
        # intensity measure type
        C = self.COEFFS[imt]

        mean = self._compute_mean(C, rup, dists)

        stddevs = self._get_stddevs(
            C, stddev_types, num_sites=dists.repi.shape)

        return mean, stddevs

    def _compute_mean(self, C, rup, dists):
        """
        Compute mean value defined by equation 1/page 414
        no amplification factor is applied to the equation
        hence the S-factor = 0
        """

        d = np.sqrt(dists.repi**2+C['h']**2)

        term01 = C['c3'] * (np.log(d))
        mean = C['c1'] + C['c2'] * rup.mag + term01

        return mean

    def _get_stddevs(self, C, stddev_types, num_sites):
        """
        Return total standard deviation.
        """
        stddevs = []

        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            stddevs.append((C['sigma']) + np.zeros(num_sites))
        return stddevs

    #: Coefficient table constructed from the electronic suplements of the
    #: original paper - coeff in the same order as in Table 4/page 703
    #: for Maw only (read last paragraph on page 701 -
    #: expains what Maw should be used)

    COEFFS = CoeffsTable(table="""\
    IMT           c1        c2         c3       h    sigma
    MMI       1.0157    1.2566    -0.6547       2   0.5344
        """)
