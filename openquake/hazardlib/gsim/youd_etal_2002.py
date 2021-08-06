# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2020 GEM Foundation
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
Module exports :class:`YoudEtAl2002`.
"""
import numpy as np
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const, site
from openquake.hazardlib.imt import PGD


class YoudEtAl2002(GMPE):
    """
    Implements the GMPE of Youd et al. (2002) for calculating Permanent
    ground defomation(m) from lateral spread

    Youd, T. L., Hansen, C. M., & Bartlett, S. F. (2002). Revised
    multilinear regression equations for prediction of lateral spread
    displacement. Journal of Geotechnical and Geoenvironmental Engineering,
    128(12), 1007-1017.
    """
    #: This GMPE is based on non-subduction earthquakes with M<8
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are Permanent ground deformation (m)
    #: from lateral spread
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGD,
    ])

    #: Supported intensity measure component is the horizontal
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.HORIZONTAL

    #: Supported standard deviation types is total.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
    ])

    #: Required site parameters
    REQUIRES_SITES_PARAMETERS = {
        'slope',
        'freeface_ratio',
        'T_15',
        'F_15',
        'D50_15'}

    #: Required rupture parameters are magnitude (ML is used)
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'hypo_depth'}

    #: Required distance measure is epicentral distance
    REQUIRES_DISTANCES = {'repi'}

    #: GMPE not tested against independent implementation so raise
    #: not verified warning
    non_verified = True

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        if rup.hypo_depth >= 50.0:
            dists.repi.setflags(write=1)
            dists.repi[dists.repi < 5.0] = 5.0
        R = (10 ** ((0.89 * rup.mag) - 5.64)) + dists.repi

        if sites.freeface_ratio.all() == 0.0:
            C = self.COEFFS_SLOPE[imt]
        else:
            C = self.COEFFS_FREEFACE[imt]
            sites.slope = sites.freeface_ratio
        imean = (
            self.__get_mag__(C, rup.mag) +
            self.__get_dist__(C, dists.repi, R) +
            self.__get_soil__(C, sites.slope,
                              sites.T_15,
                              sites.F_15, sites.D50_15))
        mean = np.log(10.0 ** imean)
        stddevs = self.__get_stddevs__(C, len(dists.repi), stddev_types)
        return mean, stddevs

    def __get_mag__(self, C, mag):
        """
        Returns the magnitude scaling term
        """
        return C["c0"] + (C["c1"] * mag)

    def __get_dist__(self, C, repi, R):
        """
        Returns the distance scaling term
        """
        return (C["c3"] * repi) + (C["c2"] * np.log10(R))

    def __get_soil__(self, C, slope, T_15, F_15, D50_15):
        """
        Returns the distance scaling term
        """
        return (C["c4"] * np.log10(slope)) + (C["c5"] * np.log10(T_15)) + \
            (C["c6"] * np.log10(100 - F_15)) + \
            (C["c7"] * np.log10(D50_15 + 0.1))

    def __get_stddevs__(self, C, num_sites, stddev_types):
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

    COEFFS_SLOPE = CoeffsTable(table="""\
    IMT      c0     c1       c2      c3     c4     c5     c6      c7     sigma
    PGD -16.213  1.532   -1.406  -0.012  0.338   0.54  3.413  -0.795     0.464
    """)
    COEFFS_FREEFACE = CoeffsTable(table="""\
    IMT      c0     c1       c2      c3     c4     c5     c6      c7     sigma
    PGD -16.713  1.532   -1.406  -0.012  0.592   0.54  3.413  -0.795     0.464
    """)
