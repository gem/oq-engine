# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2026 GEM Foundation
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
:class:`EdwardsFah2013Foreland3Bars`,
:class:`EdwardsFah2013Foreland10Bars`,
:class:`EdwardsFah2013Foreland20Bars`,
:class:`EdwardsFah2013Foreland30Bars`,
:class:`EdwardsFah2013Foreland50Bars`,
:class:`EdwardsFah2013Foreland60Bars`,
:class:`EdwardsFah2013Foreland75Bars`,
:class:`EdwardsFah2013Foreland90Bars`,
:class:`EdwardsFah2013Foreland120Bars`
"""

import numpy as np
from scipy.constants import g

from openquake.hazardlib.gsim.edwards_fah_2013a import (
    EdwardsFah2013Alpine10Bars, _compute_mean, _compute_term_d)
from openquake.hazardlib.gsim.edwards_fah_2013f_coeffs import (
    COEFFS_FORELAND_3Bars, COEFFS_FORELAND_10Bars,
    COEFFS_FORELAND_20Bars, COEFFS_FORELAND_30Bars, COEFFS_FORELAND_50Bars,
    COEFFS_FORELAND_60Bars, COEFFS_FORELAND_75Bars,
    COEFFS_FORELAND_90Bars, COEFFS_FORELAND_120Bars)


def _get_cmag1(cmag35, cmag41, cmag51, mag):
    mag = np.asarray(mag)
    return np.where(mag <= 4, cmag35, np.where(mag <= 5, cmag41, cmag51))


def _get_cmag2(cmag4, cmag5, cmag6, mag):
    mag = np.asarray(mag)
    return np.where(mag <= 4, cmag4, np.where(mag <= 5, cmag5, cmag6))


class EdwardsFah2013Foreland10Bars(EdwardsFah2013Alpine10Bars):
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
    COEFFS = COEFFS_FORELAND_10Bars


class EdwardsFah2013Foreland3Bars(EdwardsFah2013Foreland10Bars):
    """
    This class extends :class:`EdwardsFah2013Foreland10Bars`
    and implements the 3.3Bars Model :class:`EdwardsFah2013Foreland3Bars`
    """

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        super().compute(ctx, imts, mean, sig, tau, phi)

        for m, imt in enumerate(imts):
            C3 = COEFFS_FORELAND_3Bars[imt]
            C10 = self.COEFFS[imt]

            cmag1 = _get_cmag1(
                C3['cmag35'], C3['cmag41'], C3['cmag51'], ctx.mag)
            cmag2 = _get_cmag2(
                C3['cmag4'], C3['cmag5'], C3['cmag6'], ctx.mag)
            term_dist = _compute_term_d(C10, ctx.mag, ctx.rrup)
            mean_10bars = _compute_mean(C10, ctx.mag, term_dist)
            c0 = cmag1 + cmag2 * ctx.mag
            mean_adjustment = (
                C3['c1'] + C3['c2'] * term_dist +
                C3['c3'] * term_dist ** 2 +
                C3['c4'] * term_dist ** 3 +
                C3['c5'] * term_dist ** 4)
            log10_mean_3bar = mean_10bars + c0 - mean_adjustment

            # Convert all IMTs to natural log of g for consistency with OpenQuake's internal
            # representation. Note that PGV is recomputed and overwritten in this method. So,
            # we need to take the log10 again.
            if imt.string.startswith(("SA", "PGA")):
                mean[m] = np.log(10 ** log10_mean_3bar / (g * 100.))
            else:
                mean[m] = np.log(10 ** log10_mean_3bar)


class EdwardsFah2013Foreland20Bars(EdwardsFah2013Foreland10Bars):
    """
    This class extends :class:`EdwardsFah2013Foreland10Bars`
    and implements the 20Bars Model :class:`EdwardsFah2013Foreland20Bars`
    """
    COEFFS = COEFFS_FORELAND_20Bars


class EdwardsFah2013Foreland30Bars(EdwardsFah2013Foreland10Bars):
    """
    This class extends :class:`EdwardsFah2013Foreland10Bars`
    and implements the 30Bars Model :class:`EdwardsFah2013Foreland30Bars`
    """
    COEFFS = COEFFS_FORELAND_30Bars


class EdwardsFah2013Foreland50Bars(EdwardsFah2013Foreland10Bars):
    """
    This class extends :class:`EdwardsFah2013Foreland10Bars`
    and implements the 50Bars Model :class:`EdwardsFah2013Foreland50Bars`
    """
    COEFFS = COEFFS_FORELAND_50Bars


class EdwardsFah2013Foreland60Bars(EdwardsFah2013Foreland10Bars):
    """
    This class extends :class:`EdwardsFah2013Foreland10Bars`
    and implements the 60Bars Model :class:`EdwardsFah2013Foreland60Bars`
    """
    COEFFS = COEFFS_FORELAND_60Bars


class EdwardsFah2013Foreland75Bars(EdwardsFah2013Foreland10Bars):
    """
    This class extends :class:`EdwardsFah2013Foreland10Bars`
    and implements the 75Bars Model :class:`EdwardsFah2013Foreland75Bars`
    """
    COEFFS = COEFFS_FORELAND_75Bars


class EdwardsFah2013Foreland90Bars(EdwardsFah2013Foreland10Bars):
    """
    This class extends :class:`EdwardsFah2013Foreland10Bars`
    and implements the 90Bars Model :class:`EdwardsFah2013Foreland90Bars`
    """
    COEFFS = COEFFS_FORELAND_90Bars


class EdwardsFah2013Foreland120Bars(EdwardsFah2013Foreland10Bars):
    """
    This class extends :class:`EdwardsFah2013Foreland10Bars`
    and implements the 120Bars Model :class:`EdwardsFah2013Foreland120Bars`
    """
    COEFFS = COEFFS_FORELAND_120Bars
