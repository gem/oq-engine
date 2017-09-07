# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation, Chung-Han Chan
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
Module exports :class:`megawatipan2010`.
"""
from __future__ import division
from __future__ import print_function

import numpy as np
from scipy.constants import g

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA


class MegawatiPan2010(GMPE):
    """
    Implements GMPE developed by Kusnowidjaja Megawati and Tso-Chien Pan
    and published as "Ground-motion attenuation relationship for the
    Sumatran megathrust earthquakes" (2010, Earthquake Engineering &
    Structural Dynamics Volume 39, Issue 8, pages 827-845).
    """

    #: Supported tectonic region type is subduction interface along the
    #: Sumatra subduction zone.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    #: Supported intensity measure types are spectral acceleration,
    #: peak ground velocity and peak ground acceleration, see table IV
    #: pag. 837
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        PGV,
        SA
    ])

    #: Supported intensity measure component is geometric mean
    #: of two horizontal components,
    #####: PLEASE CONFIRM!!!!! 140709
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Supported standard deviation types is total, see equation IV page 837.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL
    ])

    #: Required site parameter is only Vs30 (used to distinguish rock
    #: and deep soil).
    #: This GMPE is for very hard rock site condition,
    #: see the abstract page 827.
    REQUIRES_SITES_PARAMETERS = set(())

    #: Required rupture parameters are magnitude, and focal depth, see
    #: equation 10 page 226.
    REQUIRES_RUPTURE_PARAMETERS = set(('mag',))

    #: Required distance measure is hypocentral distance,
    #: see equation 1 page 834.
    REQUIRES_DISTANCES = set(('rhypo',))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        assert all(stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
                   for stddev_type in stddev_types)

        C = self.COEFFS[imt]
        mean = (self._get_magnitude_scaling(C, rup.mag) +
                self._get_distance_scaling(C, rup.mag, dists.rhypo))
        if isinstance(imt, (PGA, SA)):
            mean = np.log(np.exp(mean) / (100.0 * g))
        stddevs = self._compute_std(C, stddev_types, len(dists.rhypo))
        return mean, stddevs

    def _get_magnitude_scaling(self, C, mag):
        """
        Returns the magnitude scaling term
        """
        return C["a0"] + C["a1"] * (mag - 6.0) + C["a2"] * (mag - 6.0) ** 2.

    def _get_distance_scaling(self, C, mag, rhypo):
        """
        Returns the distance scalig term
        """
        return (C["a3"] * np.log(rhypo)) + (C["a4"] + C["a5"] * mag) * rhypo

    def _compute_std(self, C, stddev_types, num_sites):
        """
        Compute total standard deviation, see tables 3 and 4, pages 227 and
        228.
        """
        std_total = C['sigma']

        stddevs = []
        for _ in stddev_types:
            stddevs.append(np.zeros(num_sites) + std_total)
        return stddevs

    #: Coefficient table for rock sites, see table 3 page 227.
    COEFFS = CoeffsTable(sa_damping=5, table="""\
        IMT          a0       a1         a2         a3          a4          a5    sigma
        PGV       2.369   2.0852   -0.23564   -0.87906   -0.001363   0.0001189   0.3478
        PGA       3.882   1.8988   -0.11736   -1.00000   -0.001741   0.0000776   0.2379
        0.50      4.068   1.9257   -0.12435   -0.99864   -0.001790   0.0000564   0.2410
        0.60      4.439   1.9094   -0.13693   -0.99474   -0.002462   0.0001051   0.2496
        0.70      4.836   1.8308   -0.13510   -0.99950   -0.003323   0.0001945   0.2565
        0.80      4.978   1.8570   -0.12887   -1.00000   -0.003054   0.0001475   0.2626
        0.90      5.108   1.9314   -0.13954   -0.98621   -0.002986   0.0001075   0.2424
        1.00      4.973   1.9547   -0.13913   -0.97603   -0.002851   0.0001106   0.2343
        1.20      2.729   2.0316   -0.13658   -0.60751   -0.002570   0.0000409   0.2436
        1.50      2.421   1.8960   -0.07075   -0.59262   -0.002453   0.0000668   0.2614
        2.00      2.670   1.8182   -0.07657   -0.62089   -0.002190   0.0000674   0.2780
        3.00      1.716   1.7922   -0.01895   -0.61167   -0.001177   0.0000121   0.2944
        5.00     -0.060   1.8694   -0.09103   -0.32688   -0.001765   0.0000529   0.3963
        7.00      0.518   2.1948   -0.24519   -0.47529   -0.001064   0.0000189   0.4206
        10.00     0.044   2.3081   -0.29060   -0.50356   -0.000848   0.0000125   0.5183
        15.00    -0.525   2.5297   -0.41930   -0.52777   -0.001454   0.0001435   0.4495
        20.00    -1.695   2.5197   -0.42807   -0.42096   -0.001575   0.0001498   0.4543
        30.00    -2.805   2.6640   -0.42674   -0.43304   -0.001576   0.0001568   0.3686
        50.00    -4.340   2.2968   -0.27844   -0.38291   -0.002564   0.0002540   0.3946
    """)
