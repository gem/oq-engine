# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2016 GEM Foundation, Chung-Han Chan
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
Module exports :class:`YuEtAl2013`, :class:`YuEtAl2013Tibet`,
:class:`YuEtAl2013Eastern`, :class:`YuEtAl2013Stable`

"""
from __future__ import division
from __future__ import print_function

import numpy as np

from scipy.constants import g
from scipy.optimize import minimize

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA


def rbf(ra, coeff, mag):
    """
    Calculate ground motion
    """
    if mag > 6.5:
        a1ca = coeff['ua']
        a1cb = coeff['ub']
        a1cc = coeff['uc']
        a1cd = coeff['ud']
        a1ce = coeff['ue']
        a2ca = coeff['ia']
        a2cb = coeff['ib']
        a2cc = coeff['ic']
        a2cd = coeff['id']
        a2ce = coeff['ie']
    else:
        a1ca = coeff['a']
        a1cb = coeff['b']
        a1cc = coeff['c']
        a1cd = coeff['d']
        a1ce = coeff['e']
        a2ca = coeff['ma']
        a2cb = coeff['mb']
        a2cc = coeff['mc']
        a2cd = coeff['md']
        a2ce = coeff['me']
    term1 = a1ca + a1cb * mag + a1cc * np.log(ra + a1cd*np.exp(a1ce*mag))
    term2 = a2ca + a2cb * mag
    term3 = a2cd*np.exp(a2ce*mag)
    return np.exp((term1 - term2) / a2cc) - term3


def fnc(ra, *args):
    """
    Find the rupture to site distance
    """
    #
    # epicentral distance
    repi = args[0]
    #
    # azimuth
    theta = args[1]
    #
    # magnitude
    mag = args[2]
    #
    # coefficients
    coeff = args[3]
    #
    #
    rb = rbf(ra, coeff, mag)
    t1 = ra**2 * (np.sin(np.radians(theta)))**2
    t2 = rb**2 * (np.cos(np.radians(theta)))**2
    xx = ra * rb / (t1+t2)**0.5
    return abs(repi-xx)


class YuEtAl2013Ms(GMPE):
    """
    Implements the Yu et al. (2013) GMPE used for the calculation of the 2015
    version of the national seismic hazard maps for China. Note that magnitude
    supported is Ms.
    """

    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are peak ground velocity and
    #: peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        PGV,
        SA
    ])

    #: Supported intensity measure component is geometric mean (supposed)
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Supported standard deviation types is total
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL
    ])

    #: No site parameters required
    REQUIRES_SITES_PARAMETERS = set(())

    #: Required rupture parameter is magnitude
    REQUIRES_RUPTURE_PARAMETERS = set(('mag',))

    #: Required distance measures are epicentral distance and azimuth
    REQUIRES_DISTANCES = set(('repi', 'azimuth'))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
            """
            See :meth:`superclass method
            <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
            for spec of input and result values.
            """
            # Check that the requested standard deviation type is available
            assert all(stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
                       for stddev_type in stddev_types)
            #
            # Set coefficients
            C = self.COEFFS[imt]
            if rup.mag > 6.5:
                a1ca = C['ua']
                a1cb = C['ub']
                a1cc = C['uc']
                a1cd = C['ud']
                a1ce = C['ue']
                a2ca = C['ia']
                a2cb = C['ib']
                a2cc = C['ic']
                a2cd = C['id']
                a2ce = C['ie']
            else:
                a1ca = C['a']
                a1cb = C['b']
                a1cc = C['c']
                a1cd = C['d']
                a1ce = C['e']
                a2ca = C['ma']
                a2cb = C['mb']
                a2cc = C['mc']
                a2cd = C['md']
                a2ce = C['me']
            #
            # Compute the mean value (i.e. natural logarithm of ground motion)
            mag = rup.mag
            epi = dists.repi
            theta = dists.azimuth
            #
            # Get correction coefficients
            ras = []
            for epi, theta in zip(dists.repi, dists.azimuth):
                res = minimize(fnc, epi, args=(epi, theta, mag, C),
                               method='Nelder-Mead', tol=0.1)
                ras.append(res.x[0])
            ras = np.array(ras)
            rbs = rbf(ras, C, mag)
            #
            # Compute values of ground motion for the two cases
            mean1 = (a1ca + a1cb * mag + a1cc *
                     np.log((ras**2+225)**0.5 + a1cd * np.exp(a1ce * mag)))
            mean2 = (a2ca + a2cb * mag + a2cc *
                     np.log((rbs**2+225)**0.5 + a2cd * np.exp(a2ce * mag)))
            #
            # Get distances
            x = (mean1 * np.sin(np.radians(dists.azimuth)))**2
            y = (mean2 * np.cos(np.radians(dists.azimuth)))**2
            mean = mean1 * mean2 / np.sqrt(x+y)
            if isinstance(imt, (PGA)):
                mean = np.exp(mean)/g/100
            elif isinstance(imt, (PGV)):
                mean = np.exp(mean)
            else:
                raise ValueError('Unsupported IMT')
            #
            # Get the standard deviation
            stddevs = self._compute_std(C, stddev_types, len(dists.repi))
            #
            # Return results
            return np.log(mean), stddevs

    def _compute_std(self, C, stddev_types, num_sites):
        return [np.ones(num_sites)*C['sigma']]

    #: Coefficient table
    COEFFS = CoeffsTable(sa_damping=5, table="""\
IMT a b c d e ua ub uc ud ue ma mb mc md me ia ib ic id ie sigma
PGA 4.1193 1.656 -2.389 1.772 0.424 7.8269 1.0856 -2.389 1.772 0.424 2.2609 1.6399 -2.118 0.825 0.465 6.003 1.0649 -2.118 0.825 0.465 0.5428
PGV -1.2581 1.932 -2.181 1.772 0.424 3.013 1.2742 -2.181 1.772 0.424 -3.1073 1.9389 -1.945 0.825 0.465 1.3087 1.2627 -1.945 0.825 0.465 0.6233
        """)


class YuEtAl2013MsTibet(YuEtAl2013Ms):
    #: Supported tectonic region type is Tibetan plateau
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST
    #: Coefficient table
    COEFFS = CoeffsTable(sa_damping=5, table="""\
IMT a b c d e ua ub uc ud ue ma mb mc md me ia ib ic id ie sigma
PGA 5.4901 1.4835 -2.416 2.647 0.366 8.7561 0.9453 -2.416 2.647 0.366 2.3069 1.4007 -1.854 0.612 0.457 5.6511 0.8924 -1.854 0.612 0.457 0.5428
PGV -0.1472 1.7618 -2.205 2.647 0.366 3.9422 1.1293 -2.205 2.647 0.366 -2.9923 1.7043 -1.696 0.612 0.457 1.0189 1.0902 -1.696 0.612 0.457 0.6233
     """)


class YuEtAl2013MsEastern(YuEtAl2013Ms):
    #: Supported tectonic region type is eastern part of China
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.STABLE_CONTINENTAL
    #: Coefficient table
    COEFFS = CoeffsTable(sa_damping=5, table="""\
IMT a b c d e ua ub uc ud ue ma mb mc md me ia ib ic id ie sigma
PGA 4.5517 1.5433 -2.315 2.088 0.399 8.1259 0.9936 -2.315 2.088 0.399 2.7048 1.518 -2.004 0.944 0.447 6.3319 0.9614 -2.004 0.944 0.447 0.5428
PGV -0.8349 1.8193 -2.103 2.088 0.399 3.3051 1.1799 -2.103 2.088 0.399 -2.6381 1.8124 -1.825 0.944 0.447 1.6376 1.1546 -1.825 0.944 0.447 0.6233
     """)


class YuEtAl2013MsStable(YuEtAl2013Ms):
    #: Supported tectonic region type is stable part of China
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.STABLE_CONTINENTAL
    #: Coefficient table
    COEFFS = CoeffsTable(sa_damping=5, table="""\
IMT a b c d e ua ub uc ud ue ma mb mc md me ia ib ic id ie sigma
PGA 5.5591 1.1454 -2.079 2.802 0.295 8.5238 0.6854 -2.079 2.802 0.295 3.9445 1.0833 -1.723 1.295 0.331 6.187 0.7383 -1.723 1.295 0.331 0.5428
PGV 0.2139 1.4283 -1.889 2.802 0.295 3.772 0.8786 -1.889 2.802 0.295 -1.3547 1.3823 -1.559 1.295 0.331 1.5433 0.9361 -1.559 1.295 0.331 0.6233
     """)
