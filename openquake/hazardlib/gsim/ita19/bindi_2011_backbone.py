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
Module exports :class:`BindiEtAl2011Low`.
"""
import numpy as np
from scipy.constants import g

from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib.gsim.bindi_2011 import BindiEtAl2011


class BindiEtAl2011Low(BindiEtAl2011):
    """
    Implements the lower term of the ITA18 backbone model.
    """

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        mean, stddevs = self._get_mean_and_stddevs(sites, rup, dists, imt,
                                                   stddev_types)
        delta = self._get_delta(imt, rup.mag)
        return mean-delta, stddevs

    def _get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        In this method w
        """
        # extracting dictionary of coefficients specific to required
        # intensity measure type.

        C = self.COEFFS[imt]

        imean = (self._compute_magnitude(rup, C) +
                 self._compute_distance(rup, dists, C) +
                 self._get_site_amplification(sites, C) +
                 self._get_mechanism(rup, C))

        istddevs = self._get_stddevs(C,
                                     stddev_types,
                                     num_sites=len(sites.vs30))

        # Convert units to g, but only for PGA and SA (not PGV)
        if imt.name in "SA PGA":
            mean = np.log((10.0 ** (imean - 2.0)) / g)
        else:
            # PGV:
            mean = np.log(10.0 ** imean)
        # Return stddevs in terms of natural log scaling
        stddevs = np.log(10.0 ** np.array(istddevs))
        return mean, stddevs

    def _get_delta(self, imt, mag):
        # Get the coefficients needed to compute the delta used for scaling
        coeffs = self.DELTACOEFF[imt]
        return coeffs[0]*mag**2 + coeffs[1]*mag + coeffs[2]


class BindiEtAl2011Upp(BindiEtAl2011):
    """
    Implements the upper term of the ITA18 backbone model.
    """

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        mean, stddevs = self._get_mean_and_stddevs(sites, rup, dists, imt,
                                                   stddev_types)
        delta = self._get_delta(imt, rup.mag)
        return mean+delta, stddevs


DELTACOEFF = CoeffsTable(sa_damping=5, table="""
IMT   a      b     c
PGA   0.101 -1.136 3.555
PGV   0.066 -0.741 2.400
0.05  0.105 -1.190 3.691
0.1   0.112 -1.284 4.001
0.15  0.094 -1.033 3.177
0.2   0.085 -0.907 2.831
0.3   0.086 -0.927 2.869
0.4   0.088 -0.974 3.076
0.5   0.083 -0.916 2.933
0.75  0.073 -0.808 2.628
1s    0.066 -0.736 2.420
2s    0.041 -0.512 1.888
3s    0.050 -0.616 2.193
4s    0.076 -0.906 3.046
    """)
