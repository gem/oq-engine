# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2019 GEM Foundation
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
Module exports :class:`YuEtAl2013Ms`, :class:`YuEtAl2013MsTibet`,
:class:`YuEtAl2013MsEastern`, :class:`YuEtAl2013MsStable`
:class:`YuEtAl2013Mw`, :class:`YuEtAl2013MwTibet`,
:class:`YuEtAl2013MwEastern`, :class:`YuEtAl2013MwStable`

"""
import numpy as np
from scipy.constants import g

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA


def gc(coeff, mag):
    """
    Returns the set of coefficients to be used for the calculation of GM
    as a function of earthquake magnitude

    :param coeff:
        A dictionary of parameters for the selected IMT
    :param mag:
        Magnitude value
    :returns:
        The set of coefficients
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
    return a1ca, a1cb, a1cc, a1cd, a1ce, a2ca, a2cb, a2cc, a2cd, a2ce


def rbf(ra, coeff, mag):
    """
    Calculate the median ground motion for a given magnitude and distance

    :param ra:
        Distance value [km]
    :param coeff:
        The set of coefficients
    :param mag:
        Magnitude value
    :returns:

    """
    a1ca, a1cb, a1cc, a1cd, a1ce, a2ca, a2cb, a2cc, a2cd, a2ce = gc(coeff, mag)
    term1 = a1ca + a1cb * mag + a1cc * np.log(ra + a1cd*np.exp(a1ce*mag))
    term2 = a2ca + a2cb * mag
    term3 = a2cd*np.exp(a2ce*mag)
    return np.exp((term1 - term2) / a2cc) - term3


def fnc(ra, *args):
    """
    Function used in the minimisation problem.

    :param ra:
        Semi-axis of the ellipses used in the Yu et al.
    :returns:
        The absolute difference between the epicentral distance and the
        adjusted distance
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
    # compute the difference between epicentral distances
    rb = rbf(ra, coeff, mag)
    t1 = ra**2 * (np.sin(np.radians(theta)))**2
    t2 = rb**2 * (np.cos(np.radians(theta)))**2
    xx = ra * rb / (t1+t2)**0.5
    return xx-repi


def get_ras(repi, theta, mag, coeff):
    """
    Computes equivalent distance

    :param repi:
        Epicentral distance
    :param theta:
        Azimuth value
    :param mag:
        Magnitude
    :param coeff:
        GMPE coefficients
    """
    rx = 100.
    ras = 200.
    #
    # calculate the difference between epicentral distances
    dff = fnc(ras, repi, theta, mag, coeff)
    while abs(dff) > 1e-3:
        # update the value of distance computed
        if dff > 0.:
            ras = ras - rx
        else:
            ras = ras + rx
        dff = fnc(ras, repi, theta, mag, coeff)
        rx = rx / 2.
        if rx < 1e-3:
            break
    return ras


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
        # Set parameters
        mag = rup.mag
        epi = dists.repi
        theta = dists.azimuth
        #
        # Set coefficients
        coeff = self.COEFFS[imt]
        a1ca, a1cb, a1cc, a1cd, a1ce, a2ca, a2cb, a2cc, a2cd, a2ce = \
            gc(coeff, mag)
        #
        # Get correction coefficients. Here for each site we find the
        # the geometry of the ellipses
        ras = []
        for epi, theta in zip(dists.repi, dists.azimuth):
            res = get_ras(epi, theta, mag, coeff)
            ras.append(res)
        ras = np.array(ras)
        rbs = rbf(ras, coeff, mag)
        #
        # Compute values of ground motion for the two cases. The value of
        # 225 is hardcoded under the assumption that the hypocentral depth
        # corresponds to 15 km (i.e. 15**2)
        mean1 = (a1ca + a1cb * mag +
                 a1cc * np.log((ras**2+225)**0.5 +
                               a1cd * np.exp(a1ce * mag)))
        mean2 = (a2ca + a2cb * mag +
                 a2cc * np.log((rbs**2+225)**0.5 +
                               a2cd * np.exp(a2ce * mag)))
        #
        # Get distances
        x = (mean1 * np.sin(np.radians(dists.azimuth)))**2
        y = (mean2 * np.cos(np.radians(dists.azimuth)))**2
        mean = mean1 * mean2 / np.sqrt(x+y)
        if imt.name == "PGA":
            mean = np.exp(mean)/g/100
        elif imt.name == "PGV":
            mean = np.exp(mean)
        else:
            raise ValueError('Unsupported IMT')
        #
        # Get the standard deviation
        stddevs = self._compute_std(coeff, stddev_types, len(dists.repi))
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


class YuEtAl2013Mw(YuEtAl2013Ms):
    """
    This is a modified version of the original Yu et al. (2013) that supports
    the use of Mw rather than Ms. The Mw to Ms conversion equation used is the
    one proposed by Cheng et al. (2017). Note that this version does not
    propagate the uncertainty related to the magnitude conversion process.
    """

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
        # Set parameters
        magn = rup.mag
        epi = dists.repi
        theta = dists.azimuth
        #
        # Convert Mw into Ms
        if magn < 6.58:
            mag = (magn - 0.59) / 0.86
        else:
            mag = (magn + 2.42) / 1.28
        #
        # Set coefficients
        coeff = self.COEFFS[imt]
        a1ca, a1cb, a1cc, a1cd, a1ce, a2ca, a2cb, a2cc, a2cd, a2ce = \
            gc(coeff, mag)
        #
        # Get correction coefficients. Here for each site we find the
        # the geometry of the ellipses
        ras = []
        for epi, theta in zip(dists.repi, dists.azimuth):
            res = get_ras(epi, theta, mag, coeff)
            ras.append(res)
        ras = np.array(ras)
        rbs = rbf(ras, coeff, mag)
        #
        # Compute values of ground motion for the two cases. The value of
        # 225 is hardcoded under the assumption that the hypocentral depth
        # corresponds to 15 km (i.e. 15**2)
        mean1 = (a1ca + a1cb * mag +
                 a1cc * np.log((ras**2+225)**0.5 +
                               a1cd * np.exp(a1ce * mag)))
        mean2 = (a2ca + a2cb * mag +
                 a2cc * np.log((rbs**2+225)**0.5 +
                               a2cd * np.exp(a2ce * mag)))
        #
        # Get distances
        x = (mean1 * np.sin(np.radians(dists.azimuth)))**2
        y = (mean2 * np.cos(np.radians(dists.azimuth)))**2
        mean = mean1 * mean2 / np.sqrt(x+y)
        if imt.name == "PGA":
            mean = np.exp(mean)/g/100
        elif imt.name == "PGV":
            mean = np.exp(mean)
        else:
            raise ValueError('Unsupported IMT')
        #
        # Get the standard deviation
        stddevs = self._compute_std(coeff, stddev_types, len(dists.repi))
        #
        # Return results
        return np.log(mean), stddevs


class YuEtAl2013MwTibet(YuEtAl2013Mw):
    #: Supported tectonic region type is Tibetan plateau
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST
    #: Coefficient table
    COEFFS = CoeffsTable(sa_damping=5, table="""\
IMT a b c d e ua ub uc ud ue ma mb mc md me ia ib ic id ie sigma
PGA 5.4901 1.4835 -2.416 2.647 0.366 8.7561 0.9453 -2.416 2.647 0.366 2.3069 1.4007 -1.854 0.612 0.457 5.6511 0.8924 -1.854 0.612 0.457 0.5428
PGV -0.1472 1.7618 -2.205 2.647 0.366 3.9422 1.1293 -2.205 2.647 0.366 -2.9923 1.7043 -1.696 0.612 0.457 1.0189 1.0902 -1.696 0.612 0.457 0.6233
     """)


class YuEtAl2013MwEastern(YuEtAl2013Mw):
    #: Supported tectonic region type is eastern part of China
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.STABLE_CONTINENTAL
    #: Coefficient table
    COEFFS = CoeffsTable(sa_damping=5, table="""\
IMT a b c d e ua ub uc ud ue ma mb mc md me ia ib ic id ie sigma
PGA 4.5517 1.5433 -2.315 2.088 0.399 8.1259 0.9936 -2.315 2.088 0.399 2.7048 1.518 -2.004 0.944 0.447 6.3319 0.9614 -2.004 0.944 0.447 0.5428
PGV -0.8349 1.8193 -2.103 2.088 0.399 3.3051 1.1799 -2.103 2.088 0.399 -2.6381 1.8124 -1.825 0.944 0.447 1.6376 1.1546 -1.825 0.944 0.447 0.6233
     """)


class YuEtAl2013MwStable(YuEtAl2013Mw):
    #: Supported tectonic region type is stable part of China
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.STABLE_CONTINENTAL
    #: Coefficient table
    COEFFS = CoeffsTable(sa_damping=5, table="""\
IMT a b c d e ua ub uc ud ue ma mb mc md me ia ib ic id ie sigma
PGA 5.5591 1.1454 -2.079 2.802 0.295 8.5238 0.6854 -2.079 2.802 0.295 3.9445 1.0833 -1.723 1.295 0.331 6.187 0.7383 -1.723 1.295 0.331 0.5428
PGV 0.2139 1.4283 -1.889 2.802 0.295 3.772 0.8786 -1.889 2.802 0.295 -1.3547 1.3823 -1.559 1.295 0.331 1.5433 0.9361 -1.559 1.295 0.331 0.6233
     """)
