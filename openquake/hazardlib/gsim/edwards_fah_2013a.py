# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2025 GEM Foundation
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
    COEFFS_ALPINE_60Bars, COEFFS_ALPINE_10Bars, COEFFS_ALPINE_20Bars,
    COEFFS_ALPINE_30Bars, COEFFS_ALPINE_50Bars, COEFFS_ALPINE_75Bars,
    COEFFS_ALPINE_90Bars, COEFFS_ALPINE_120Bars)
from openquake.hazardlib.gsim.utils_swiss_gmpe import (
    _compute_phi_ss, _compute_C1_term)

#: Fixed magnitude terms
M1 = 5.00
M2 = 4.70


def _compute_term_d(C, mag, rrup):
    """
    Compute distance term: original implementation from Carlo Cauzzi
    if M > 5.5     rmin = 0.55;
    elseif M > 4.7 rmin = -2.067.*M +11.92;
    else           rmin = -0.291.*M + 3.48;
    end
    d = log10(max(R,rmin));
    """
    rrup_min = np.where(
        mag > M1,
        .55,
        np.where(mag > M2, -2.067 * mag + 11.92, -0.291 * mag + 3.48))
    return np.log10(np.maximum(rrup_min, rrup))


def _compute_mean(C, mag, term_dist_r):
    """
    compute mean
    """
    return (_compute_term_1(C, mag) +
            _compute_term_2(C, mag, term_dist_r) +
            _compute_term_3(C, mag, term_dist_r) +
            _compute_term_4(C, mag, term_dist_r) +
            _compute_term_5(C, mag, term_dist_r))


def _compute_term_1(C, mag):
    """
    Compute term 1
    a1 + a2.*M + a3.*M.^2 + a4.*M.^3 + a5.*M.^4 + a6.*M.^5 + a7.*M.^6
    """
    return (C['a1'] + C['a2'] * mag + C['a3'] * mag ** 2 + C['a4'] * mag ** 3
            + C['a5'] * mag ** 4 + C['a6'] * mag ** 5 + C['a7'] * mag ** 6)


def _compute_term_2(C, mag, R):
    """
    (a8 + a9.*M + a10.*M.*M + a11.*M.*M.*M).*d(r)
    """
    return ((C['a8'] + C['a9'] * mag + C['a10'] * mag ** 2 +
             C['a11'] * mag ** 3) * R)


def _compute_term_3(C, mag, R):
    """
    (a12 + a13.*M + a14.*M.*M + a15.*M.*M.*M).*(d(r).^2)
    """
    return ((C['a12'] + C['a13'] * mag + C['a14'] * mag ** 2 +
             C['a15'] * mag ** 3) * R ** 2)


def _compute_term_4(C, mag, R):
    """
    (a16 + a17.*M + a18.*M.*M + a19.*M.*M.*M).*(d(r).^3)
    """
    return ((C['a16'] + C['a17'] * mag + C['a18'] * mag ** 2 +
             C['a19'] * mag ** 3) * R ** 3)


def _compute_term_5(C, mag, R):
    """
    (a20 + a21.*M + a22.*M.*M + a23.*M.*M.*M).*(d(r).^4)
    """
    return ((C['a20'] + C['a21'] * mag + C['a22'] * mag ** 2 +
             C['a23'] * mag ** 3) * R ** 4)


def _compute_term_r(C, mag, rrup):
    """
    Compute distance term
    d = log10(max(R,rmin));
    """
    rrup_min = np.where(
        mag > M1,
        .55,
        np.where(mag > M2, -2.80 * mag + 14.55, -0.295 * mag + 2.65))

    return np.log10(np.maximum(rrup, rrup_min))


def _get_stddevs(C, mag, c1_rrup, log_phi_ss, mean_phi_ss):
    """
    Return standard deviations
    """
    phi_ss = _compute_phi_ss(C, mag, c1_rrup, log_phi_ss, mean_phi_ss)
    return [np.sqrt(C['tau'] ** 2 + phi_ss ** 2), C['tau'], phi_ss]


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
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGV, PGA, SA}
    #: Supported intensity measure component is the geometric mean of two
    #: horizontal components
    #: :attr:`~openquake.hazardlib.const.IMC.GEOMETRIC_MEAN`
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation type is total, inter-event and intra-event
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Required site parameter is only Vs30 (used to distinguish rock
    #: and deep soil).
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters: magnitude
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'rake'}

    #: Required distance measure is Rrup
    REQUIRES_DISTANCES = {'rrup'}

    #: Vs30 value representing typical rock conditions in Switzerland.
    #: confirmed by the Swiss GMPE group
    DEFINED_FOR_REFERENCE_VELOCITY = 1105.

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            COEFFS = self.COEFFS[imt]
            if 'Foreland' in self.__class__.__name__:
                R = _compute_term_d(COEFFS, ctx.mag, ctx.rrup)
            else:
                R = _compute_term_r(COEFFS, ctx.mag, ctx.rrup)

            mean[m] = 10 ** _compute_mean(COEFFS, ctx.mag, R)

            # Convert units to g,
            # but only for PGA and SA (not PGV):
            if imt.string.startswith(("SA", "PGA")):
                mean[m] = np.log(mean[m] / (g*100.))
            else:
                # PGV:
                mean[m] = np.log(mean[m])

            c1_rrup = _compute_C1_term(COEFFS, ctx.rrup)
            log_phi_ss = 1.00

            sig[m], tau[m], phi[m] = _get_stddevs(
                COEFFS, ctx.mag, c1_rrup,
                log_phi_ss, COEFFS['mean_phi_ss'])

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
