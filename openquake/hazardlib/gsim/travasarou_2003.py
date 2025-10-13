# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2025 GEM Foundation
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
import numpy as np

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import IA


def _get_stddevs(ctx, arias):
    """
    Return standard deviations as defined in table 1, p. 200.
    """
    # Magnitude dependent inter-event term (Eq. 13)
    tau = 0.611 - 0.047 * (ctx.mag - 4.7)
    tau[ctx.mag < 4.7] = 0.611
    tau[ctx.mag > 7.6] = 0.475

    # Retrieve site-class dependent sigma
    sigma1, sigma2 = _get_intra_event_sigmas(ctx)
    sigma = np.copy(sigma1)

    # Implements the nonlinear intra-event sigma (Eq. 14)
    idx = arias >= 0.125
    sigma[idx] = sigma2[idx]
    idx = np.logical_and(arias > 0.013, arias < 0.125)
    sigma[idx] = sigma1[idx] - 0.106 * np.log(arias[idx] / 0.0132)
    sigma_total = np.sqrt(tau ** 2. + sigma ** 2.)
    return [sigma_total, tau, sigma]


def _get_intra_event_sigmas(ctx):
    """
    The intra-event term nonlinear and dependent on both the site class
    and the expected ground motion. In this case the sigma coefficients
    are determined from the site class as described below Eq. 14
    """
    sigma1 = 1.18 * np.ones_like(ctx.vs30)
    sigma2 = 0.94 * np.ones_like(ctx.vs30)

    idx1 = np.logical_and(ctx.vs30 >= 360.0, ctx.vs30 < 760.0)
    idx2 = ctx.vs30 < 360.0
    sigma1[idx1] = 1.17
    sigma2[idx1] = 0.93
    sigma1[idx2] = 0.96
    sigma2[idx2] = 0.73
    return sigma1, sigma2


def _compute_magnitude(ctx, C):
    """
    Compute the first term of the equation described on p. 1144:

    ``c1 + c2 * (M - 6) + c3 * log(M / 6)``
    """
    return C['c1'] + C['c2'] * (ctx.mag - 6.0) + (
        C['c3'] * np.log(ctx.mag / 6.0))


def _compute_distance(ctx, C):
    """
    Compute the second term of the equation described on p. 1144:

    `` c4 * np.log(sqrt(R ** 2. + h ** 2.)
    """
    return C["c4"] * np.log(np.sqrt(ctx.rrup ** 2. + C["h"] ** 2.))


def _get_site_amplification(ctx, C):
    """
    Compute the third term of the equation described on p. 1144:

    ``(s11 + s12 * (M - 6)) * Sc + (s21 + s22 * (M - 6)) * Sd`
    """
    Sc, Sd = _get_site_type_dummy_variables(ctx)
    return (C["s11"] + C["s12"] * (ctx.mag - 6.0)) * Sc +\
        (C["s21"] + C["s22"] * (ctx.mag - 6.0)) * Sd


def _get_site_type_dummy_variables(ctx):
    """
    Get site type dummy variables, ``Sc`` (for soft and stiff soil ctx)
    and ``Sd`` (for rock ctx).
    """
    Sc = np.zeros_like(ctx.vs30)
    Sd = np.zeros_like(ctx.vs30)
    # Soft soil; Vs30 < 360 m/s. Page 199.
    Sd[ctx.vs30 < 360.0] = 1.
    # Stiff soil 360 <= Vs30 < 760
    Sc[np.logical_and(ctx.vs30 >= 360.0, ctx.vs30 < 760.0)] = 1.
    return Sc, Sd


def _get_mechanism(ctx, C):
    """
    Compute the fourth term of the equation described on p. 199:

    ``f1 * Fn + f2 * Fr``
    """
    Fn, Fr = _get_fault_type_dummy_variables(ctx)
    return (C['f1'] * Fn) + (C['f2'] * Fr)


def _get_fault_type_dummy_variables(ctx):
    """
    The original classification considers four style of faulting categories
    (normal, strike-slip, reverse-oblique and reverse).
    """
    Fn, Fr = np.zeros_like(ctx.rake), np.zeros_like(ctx.rake)
    Fn[(ctx.rake >= -112.5) & (ctx.rake <= -67.5)] = 1.  # normal
    Fr[(ctx.rake >= 22.5) & (ctx.rake <= 157.5)] = 1.
    # joins both the reverse and reverse-oblique categories
    return Fn, Fr


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
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {IA}

    #: Supported intensity measure component is actually the arithmetic mean of
    #: two horizontal components - we find this to be equivalent to
    #: :attr:`~openquake.hazardlib.const.IMC.GEOMETRIC_MEAN`
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see equations 13 - 15
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Required site parameter is only Vs30 (used to distinguish rock
    #: and stiff and soft soil).
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are magnitude and rake (eq. 1, page 199).
    REQUIRES_RUPTURE_PARAMETERS = {'rake', 'mag'}

    #: Required distance measure is RRup (eq. 1, page 199).
    REQUIRES_DISTANCES = {'rrup'}

    #: No independent tests - verification against paper
    non_verified = True

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            # Implements mean model (equation 12)
            mean[m] = (_compute_magnitude(ctx, C) +
                       _compute_distance(ctx, C) +
                       _get_site_amplification(ctx, C) +
                       _get_mechanism(ctx, C))

            sig[m], tau[m], phi[m] = _get_stddevs(ctx, np.exp(mean[m]))

    #: For Ia, coefficients are taken from table 3
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT      c1       c2      c3       c4      h      s11      s12      s21      s22        f1      f2
    ia    2.800   -1.981   20.72   -1.703   8.78    0.454    0.101    0.479    0.334    -0.166   0.512
    """)
