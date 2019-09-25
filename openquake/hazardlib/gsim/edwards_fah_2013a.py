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
Module exports
:class:`EdwardsFah2013Alpine10Bars`,
:class:`EdwardsFah2013Alpine20Bars`,
:class:`EdwardsFah2013Alpine30Bars`,
:class:`EdwardsFah2013Alpine50Bars`,
:class:`EdwardsFah2013Alpine60Bars`,
:class:`EdwardsFah2013Alpine75Bars`,
:class:`EdwardsFah2013Alpine90Bars`,
:class:`EdwardsFah2013Alpine120Bars`.
"""
import numpy as np
from scipy.constants import g
from openquake.hazardlib.gsim.base import GMPE
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGV, PGA, SA
from openquake.hazardlib.gsim.edwards_fah_2013a_coeffs import (
    COEFFS_ALPINE_60Bars,
    COEFFS_ALPINE_10Bars,
    COEFFS_ALPINE_20Bars,
    COEFFS_ALPINE_30Bars,
    COEFFS_ALPINE_50Bars,
    COEFFS_ALPINE_75Bars,
    COEFFS_ALPINE_90Bars,
    COEFFS_ALPINE_120Bars
)
from openquake.hazardlib.gsim.utils_swiss_gmpe import (
    _compute_phi_ss,
    _compute_C1_term
)


class EdwardsFah2013Alpine10Bars(GMPE):
    """
    This function implements the GMPE developed by Ben Edwars and Donath Fah
    and published as "A Stochastic Ground-Motion Model for Switzerland"
    Bulletin of the Seismological Society of America,
    Vol. 103, No. 1, pp. 78–98, February 2013.
    The GMPE was parametrized by Carlo Cauzzi to be implemented in OpenQuake.
    This class implements the equations for 'Alpine' and 'Foreland - two
    tectonic regionalizations defined for the Switzerland -
    therefore this GMPE is region specific".
    @ implemented by laurentiu.danciu@sed.ethz.zh
    """
    #: Supported tectonic region type is ALPINE which
    #: is a sub-region of Active Shallow Crust.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration, see tables 3 and 4, pages 227 and 228.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGV,
        PGA,
        SA
    ])
    #: Supported intensity measure component is the geometric mean of two
    #: horizontal components
    #: :attr:`~openquake.hazardlib.const.IMC.AVERAGE_HORIZONTAL`
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Supported standard deviation type is total,
    #: Carlo Cauzzi - Personal Communication
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL
    ])

    #: Required site parameter is only Vs30 (used to distinguish rock
    #: and deep soil).
    REQUIRES_SITES_PARAMETERS = set(('vs30', ))

    #: Required rupture parameters: magnitude
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', 'rake'))

    #: Required distance measure is Rrup
    REQUIRES_DISTANCES = set(('rrup', ))

    #: Vs30 value representing typical rock conditions in Switzerland.
    #: confirmed by the Swiss GMPE group
    ROCK_VS30 = 1105

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """

        COEFFS = self.COEFFS[imt]
        R = self._compute_term_r(COEFFS, rup.mag, dists.rrup)

        mean = 10 ** (self._compute_mean(COEFFS, rup.mag, R))

        # Convert units to g,
        # but only for PGA and SA (not PGV):
        if imt.name in "SA PGA":
            mean = np.log(mean / (g*100.))
        else:
            # PGV:
            mean = np.log(mean)

        c1_rrup = _compute_C1_term(COEFFS, dists.rrup)
        log_phi_ss = 1.00

        stddevs = self._get_stddevs(
            COEFFS, stddev_types, sites.vs30.shape[0], rup.mag, c1_rrup,
            log_phi_ss, COEFFS['mean_phi_ss']
        )

        return mean, stddevs

    def _get_stddevs(self, C, stddev_types, num_sites, mag, c1_rrup,
                     log_phi_ss, mean_phi_ss):
        """
        Return standard deviations
        """
        phi_ss = _compute_phi_ss(C, mag, c1_rrup, log_phi_ss, mean_phi_ss)

        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES

            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(np.sqrt(
                               C['tau'] * C['tau'] +
                               phi_ss * phi_ss) +
                               np.zeros(num_sites))

            elif stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(phi_ss + np.zeros(num_sites))

            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(C['tau'] + np.zeros(num_sites))
        return stddevs

    def _compute_term_r(self, C, mag, rrup):
        """
        Compute distance term
        d = log10(max(R,rmin));
        """
        if mag > self.M1:
            rrup_min = 0.55

        elif mag > self.M2:
            rrup_min = -2.80 * mag + 14.55

        else:
            rrup_min = -0.295 * mag + 2.65

        R = np.maximum(rrup, rrup_min)

        return np.log10(R)

    def _compute_term_1(self, C, mag):
        """
        Compute term 1
        a1 + a2.*M + a3.*M.^2 + a4.*M.^3 + a5.*M.^4 + a6.*M.^5 + a7.*M.^6
        """
        return (
            C['a1'] + C['a2'] * mag + C['a3'] *
            np.power(mag, 2) + C['a4'] * np.power(mag, 3)
            + C['a5'] * np.power(mag, 4) + C['a6'] *
            np.power(mag, 5) + C['a7'] * np.power(mag, 6)
        )

    def _compute_term_2(self, C, mag, R):
        """
        (a8 + a9.*M + a10.*M.*M + a11.*M.*M.*M).*d(r)
        """
        return (
            (C['a8'] + C['a9'] * mag + C['a10'] * np.power(mag, 2) +
             C['a11'] * np.power(mag, 3)) * R
        )

    def _compute_term_3(self, C, mag, R):
        """
        (a12 + a13.*M + a14.*M.*M + a15.*M.*M.*M).*(d(r).^2)
        """
        return (
            (C['a12'] + C['a13'] * mag + C['a14'] * np.power(mag, 2) +
             C['a15'] * np.power(mag, 3)) * np.power(R, 2)
        )

    def _compute_term_4(self, C, mag, R):
        """
        (a16 + a17.*M + a18.*M.*M + a19.*M.*M.*M).*(d(r).^3)
        """
        return (
            (C['a16'] + C['a17'] * mag + C['a18'] * np.power(mag, 2) +
             C['a19'] * np.power(mag, 3)) * np.power(R, 3)
        )

    def _compute_term_5(self, C, mag, R):
        """
        (a20 + a21.*M + a22.*M.*M + a23.*M.*M.*M).*(d(r).^4)
        """
        return (
            (C['a20'] + C['a21'] * mag + C['a22'] * np.power(mag, 2) +
             C['a23'] * np.power(mag, 3)) * np.power(R, 4)
        )

    def _compute_mean(self, C, mag, term_dist_r):
        """
        compute mean
        """
        return (self._compute_term_1(C, mag) +
                self._compute_term_2(C, mag, term_dist_r) +
                self._compute_term_3(C, mag, term_dist_r) +
                self._compute_term_4(C, mag, term_dist_r) +
                self._compute_term_5(C, mag, term_dist_r))

    #: Fixed magnitude terms
    M1 = 5.00
    M2 = 4.70

    COEFFS = COEFFS_ALPINE_10Bars


class EdwardsFah2013Alpine20Bars(EdwardsFah2013Alpine10Bars):

    """
    This class extends :class:`EdwardsFah2013Alpine10Bars`
    and implements the 20Bars Model :class:`EdwardsFah2013Alpine20Bars`
    """
    COEFFS = COEFFS_ALPINE_20Bars


class EdwardsFah2013Alpine30Bars(EdwardsFah2013Alpine10Bars):

    """
    This class extends :class:`EdwardsFah2013Alpine10Bars`
    and implements the 30Bars Model :class:`EdwardsFah2013Alpine30Bars`
    """
    COEFFS = COEFFS_ALPINE_30Bars


class EdwardsFah2013Alpine50Bars(EdwardsFah2013Alpine10Bars):

    """
    This class extends :class:`EdwardsFah2013Alpine10Bars`
    and implements the 50Bars Model :class:`EdwardsFah2013Alpine50Bars`
    """
    COEFFS = COEFFS_ALPINE_50Bars


class EdwardsFah2013Alpine60Bars(EdwardsFah2013Alpine10Bars):

    """
    This class extends :class:`EdwardsFah2013Alpine10Bars`
    and implements the 60Bars Model :class:`EdwardsFah2013Alpine60Bars`
    """
    COEFFS = COEFFS_ALPINE_60Bars


class EdwardsFah2013Alpine75Bars(EdwardsFah2013Alpine10Bars):

    """
    This class extends :class:`EdwardsFah2013Alpine10Bars`
    and implements the 75Bars Model :class:`EdwardsFah2013Alpine75Bars`
    """
    COEFFS = COEFFS_ALPINE_75Bars


class EdwardsFah2013Alpine90Bars(EdwardsFah2013Alpine10Bars):

    """
    This class extends :class:`EdwardsFah2013Alpine10Bars`
    and implements the 90Bars Model :class:`EdwardsFah2013Alpine90Bars`
    """
    COEFFS = COEFFS_ALPINE_90Bars


class EdwardsFah2013Alpine120Bars(EdwardsFah2013Alpine10Bars):

    """
    This class extends :class:`EdwardsFah2013Alpine10Bars`
    and implements the 120Bars Model :class:`EdwardsFah2013Alpine120Bars`
    """
    COEFFS = COEFFS_ALPINE_120Bars
