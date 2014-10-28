# -*- coding: utf-8 -*-
# The Hazard Library
# Copyright (C) 2013-2014, GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Module exports
:class:`EdwardsFah2013Foreland10MPa`,
:class:`EdwardsFah2013Foreland20MPa`,
:class:`EdwardsFah2013Foreland30MPa`,
:class:`EdwardsFah2013Foreland50MPa`,
:class:`EdwardsFah2013Foreland60MPa`,
:class:`EdwardsFah2013Foreland75MPa`,
:class:`EdwardsFah2013Foreland90MPa`,
:class:`EdwardsFah2013Foreland120MPa`
"""

from __future__ import division
import numpy as np
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib.gsim.edwards_fah_2013a import (
    EdwardsFah2013Alpine10MPa
)
from openquake.hazardlib.gsim.edwards_fah_2013f_coeffs import (
    COEFFS_FORELAND_10Bars,
    COEFFS_FORELAND_20Bars,
    COEFFS_FORELAND_30Bars,
    COEFFS_FORELAND_50Bars,
    COEFFS_FORELAND_60Bars,
    COEFFS_FORELAND_75Bars,
    COEFFS_FORELAND_90Bars,
    COEFFS_FORELAND_120Bars
)
from openquake.hazardlib.gsim.utils_swiss_gmpe import _compute_C1_term


class EdwardsFah2013Foreland10MPa(EdwardsFah2013Alpine10MPa):

    """
    This function implements the GMPE developed by Ben Edwards and
    Donath Fah and published as "A Stochastic Ground-Motion Model
    for Switzerland" Bulletin of the Seismological
    Society of America, Vol. 103, No. 1, pp. 78–98, February 2013.
    The GMPE was parametrized by Carlo Cauzzi to be implemented in OpenQuake.
    This class implements the equations for 'Foreland - two
    tectonic regionalizations defined for the Switzerland -
    therefore this GMPE is region specific".
    """
    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        compute mean for Foreland
        """
        COEFFS = self.COEFFS[imt]
        R = self._compute_term_d(COEFFS, rup.mag, dists.rrup)

        mean = 10 ** (self._compute_mean(COEFFS, rup.mag, R))

        # Convert units to g,
        # but only for PGA and SA (not PGV):
        if isinstance(imt, (PGA, SA)):
            mean = np.log(mean / 981)
        else:
            # PGV:
            mean = np.log(mean)

        c1_rrup = _compute_C1_term(COEFFS, dists.rrup)
        log_phi_ss = 1.00
        stddevs = self._get_stddevs(COEFFS, stddev_types, sites.vs30.shape[0],
                                    rup.mag, c1_rrup, log_phi_ss,
                                    COEFFS['mean_phi_ss'])

        return mean, stddevs

    def _compute_term_d(self, C, mag, rrup):
        """
        Compute distance term: original implementation from Carlo Cauzzi
        if M > 5.5     rmin = 0.55;
        elseif M > 4.7 rmin = -2.067.*M +11.92;
        else           rmin = -0.291.*M + 3.48;
        end
        d = log10(max(R,rmin));
        """
        if mag > self.M1:
            rrup_min = 0.55
        elif mag > self.M2:
            rrup_min = -2.067 * mag + 11.92
        else:
            rrup_min = -0.291 * mag + 3.48

        R = np.maximum(rrup_min, rrup)

        return np.log10(R)

    #: Fixed magnitude terms

    M1 = 5.00
    M2 = 4.70
    COEFFS = COEFFS_FORELAND_10Bars


class EdwardsFah2013Foreland20MPa(EdwardsFah2013Foreland10MPa):

    """
    This class extends :class:`EdwardsFah2013Foreland10MPa`
    and implements the 20Bars Model :class:`EdwardsFah2013Foreland20MPa`
    """
    COEFFS = COEFFS_FORELAND_20Bars


class EdwardsFah2013Foreland30MPa(EdwardsFah2013Foreland10MPa):

    """
    This class extends :class:`EdwardsFah2013Foreland10MPa`
    and implements the 30Bars Model :class:`EdwardsFah2013Foreland30MPa`
    """
    COEFFS = COEFFS_FORELAND_30Bars


class EdwardsFah2013Foreland50MPa(EdwardsFah2013Foreland10MPa):

    """
    This class extends :class:`EdwardsFah2013Foreland10MPa`
    and implements the 50Bars Model :class:`EdwardsFah2013Foreland50MPa`
    """
    COEFFS = COEFFS_FORELAND_50Bars


class EdwardsFah2013Foreland60MPa(EdwardsFah2013Foreland10MPa):

    """
    This class extends :class:`EdwardsFah2013Foreland10MPa`
    and implements the 60Bars Model :class:`EdwardsFah2013Foreland60MPa`
    """
    COEFFS = COEFFS_FORELAND_60Bars


class EdwardsFah2013Foreland75MPa(EdwardsFah2013Foreland10MPa):

    """
    This class extends :class:`EdwardsFah2013Foreland10MPa`
    and implements the 75Bars Model :class:`EdwardsFah2013Foreland75MPa`
    """
    COEFFS = COEFFS_FORELAND_75Bars


class EdwardsFah2013Foreland90MPa(EdwardsFah2013Foreland10MPa):

    """
    This class extends :class:`EdwardsFah2013Foreland10MPa`
    and implements the 90Bars Model :class:`EdwardsFah2013Foreland90MPa`
    """
    COEFFS = COEFFS_FORELAND_90Bars


class EdwardsFah2013Foreland120MPa(EdwardsFah2013Foreland10MPa):

    """
    This class extends :class:`EdwardsFah2013Foreland10MPa`
    and implements the 120Bars Model :class:`EdwardsFah2013Foreland120MPa`
    """
    COEFFS = COEFFS_FORELAND_120Bars
