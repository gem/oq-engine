# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2017 GEM Foundation
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
Module exports :class:`Travasarou2003`,
"""
from __future__ import division

import numpy as np

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import IA


class TravasarouEtAl2003(GMPE):
    """
    Implements the ground motion prediction equation for Arias Intensity
    given by Travasarou et al., (2003):
    Travasarou, T., Bray, J. D. and Abrahamson, N. A. (2003) "Emprical
    Attenuation Relationship for Arias Intensity", Earthquake Engineering
    and Structural Dynamics, 32: 1133 - 1155

    Ground motion records are generally taken from active shallow crustal
    regions
    """
    #: Supported tectonic region type is 'active shallow crust'
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Set of :mod:`intensity measure types <openquake.hazardlib.imt>`
    #: this GSIM can calculate. A set should contain classes from module
    #: :mod:`openquake.hazardlib.imt`.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        IA,
    ])

    #: Supported intensity measure component is actually the arithmetic mean of
    #: two horizontal components - we find this to be equivalent to
    #: :attr:`~openquake.hazardlib.const.IMC.AVERAGE_HORIZONTAL`
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see equations 13 - 15
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    ])

    #: Required site parameter is only Vs30 (used to distinguish rock
    #: and stiff and soft soil).
    REQUIRES_SITES_PARAMETERS = set(('vs30', ))

    #: Required rupture parameters are magnitude and rake (eq. 1, page 199).
    REQUIRES_RUPTURE_PARAMETERS = set(('rake', 'mag'))

    #: Required distance measure is RRup (eq. 1, page 199).
    REQUIRES_DISTANCES = set(('rrup', ))

    #: No independent tests - verification against paper
    non_verified = True

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extracting dictionary of coefficients specific to required
        # intensity measure type.
        C = self.COEFFS[imt]
        # Implements mean model (equation 12)
        mean = (self._compute_magnitude(rup, C) +
                self._compute_distance(dists, C) +
                self._get_site_amplification(sites, rup, C) +
                self._get_mechanism(rup, C))

        stddevs = self._get_stddevs(rup, np.exp(mean), stddev_types, sites)

        return mean, stddevs

    def _get_stddevs(self, rup, arias, stddev_types, sites):
        """
        Return standard deviations as defined in table 1, p. 200.
        """
        stddevs = []
        # Magnitude dependent inter-event term (Eq. 13)
        if rup.mag < 4.7:
            tau = 0.611
        elif rup.mag > 7.6:
            tau = 0.475
        else:
            tau = 0.611 - 0.047 * (rup.mag - 4.7)

        # Retrieve site-class dependent sigma
        sigma1, sigma2 = self._get_intra_event_sigmas(sites)
        sigma = np.copy(sigma1)
        # Implements the nonlinear intra-event sigma (Eq. 14)
        idx = arias >= 0.125
        sigma[idx] = sigma2[idx]
        idx = np.logical_and(arias > 0.013, arias < 0.125)
        sigma[idx] = sigma1[idx] - 0.106 * (np.log(arias[idx]) -
                                            np.log(0.0132))

        sigma_total = np.sqrt(tau ** 2. + sigma ** 2.)

        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(sigma_total)
            elif stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(sigma)
            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(tau * np.ones_like(sites.vs30))
        return stddevs

    def _get_intra_event_sigmas(self, sites):
        """
        The intra-event term nonlinear and dependent on both the site class
        and the expected ground motion. In this case the sigma coefficients
        are determined from the site class as described below Eq. 14
        """
        sigma1 = 1.18 * np.ones_like(sites.vs30)
        sigma2 = 0.94 * np.ones_like(sites.vs30)

        idx1 = np.logical_and(sites.vs30 >= 360.0, sites.vs30 < 760.0)
        idx2 = sites.vs30 < 360.0
        sigma1[idx1] = 1.17
        sigma2[idx1] = 0.93
        sigma1[idx2] = 0.96
        sigma2[idx2] = 0.73
        return sigma1, sigma2

    def _compute_magnitude(self, rup, C):
        """
        Compute the first term of the equation described on p. 1144:

        ``c1 + c2 * (M - 6) + c3 * log(M / 6)``
        """
        return C['c1'] + C['c2'] * (rup.mag - 6.0) +\
            (C['c3'] * np.log(rup.mag / 6.0))

    def _compute_distance(self, dists, C):
        """
        Compute the second term of the equation described on p. 1144:

        `` c4 * np.log(sqrt(R ** 2. + h ** 2.)
        """
        return C["c4"] * np.log(np.sqrt(dists.rrup ** 2. + C["h"] ** 2.))

    def _get_site_amplification(self, sites, rup, C):
        """
        Compute the third term of the equation described on p. 1144:

        ``(s11 + s12 * (M - 6)) * Sc + (s21 + s22 * (M - 6)) * Sd`
        """
        Sc, Sd = self._get_site_type_dummy_variables(sites)
        return (C["s11"] + C["s12"] * (rup.mag - 6.0)) * Sc +\
            (C["s21"] + C["s22"] * (rup.mag - 6.0)) * Sd

    def _get_site_type_dummy_variables(self, sites):
        """
        Get site type dummy variables, ``Sc`` (for soft and stiff soil sites)
        and ``Sd`` (for rock sites).
        """
        Sc = np.zeros_like(sites.vs30)
        Sd = np.zeros_like(sites.vs30)
        # Soft soil; Vs30 < 360 m/s. Page 199.
        Sd[sites.vs30 < 360.0] = 1
        # Stiff soil 360 <= Vs30 < 760
        Sc[np.logical_and(sites.vs30 >= 360.0, sites.vs30 < 760.0)] = 1

        return Sc, Sd

    def _get_mechanism(self, rup, C):
        """
        Compute the fourth term of the equation described on p. 199:

        ``f1 * Fn + f2 * Fr``
        """
        Fn, Fr = self._get_fault_type_dummy_variables(rup)
        return (C['f1'] * Fn) + (C['f2'] * Fr)

    def _get_fault_type_dummy_variables(self, rup):
        """
        The original classification considers four style of faulting categories
        (normal, strike-slip, reverse-oblique and reverse).
        """

        Fn, Fr = 0, 0
        if rup.rake >= -112.5 and rup.rake <= -67.5:
            # normal
            Fn = 1
        elif rup.rake >= 22.5 and rup.rake <= 157.5:
            # Joins both the reverse and reverse-oblique categories
            Fr = 1
        return Fn, Fr

    #: For Ia, coefficients are taken from table 3,
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT      c1       c2      c3       c4      h      s11      s12      s21      s22        f1      f2
    ia    2.800   -1.981   20.72   -1.703   8.78    0.454    0.101    0.479    0.334    -0.166   0.512
    """)
