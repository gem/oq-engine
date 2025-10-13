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
Module
:mod:`openquake.hazardlib.gsim.nath_2012`
exports
:class:`NathEtAl2012Lower`
:class:`NathEtAl2012Upper`
"""
import numpy as np

from openquake.hazardlib import const
from openquake.hazardlib.imt import SA, PGA
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable

CONSTS = {'ref_mag': 10.}


def _compute_mean(ctx, coeffs):
    """
    Evaluate equation (11) on p. 484.
    """
    ln_p = coeffs['c1'] + coeffs['c2']*ctx.mag + \
        coeffs['c3']*(CONSTS['ref_mag'] - ctx.mag)**3 + \
        coeffs['c4']*np.log(
            ctx.rrup + coeffs['c5']*np.exp(coeffs['c6']*ctx.mag))
    return ln_p


def _get_stddev(coeffs):
    """
    Look up values from Table 5 on p. 483 and convert to natural logarithm.
    Interpretation of "sigma_log(Y)" as the common logarithm is based on
    the order of magnitude of the values and consistent use of "log" and
    "ln" to denote common and natural logarithm elsewhere in the paper.
    """
    log_stddev = coeffs['sigma']
    ln_stddev = log_stddev*np.log(10)
    return ln_stddev


class NathEtAl2012Lower(GMPE):
    # pylint: disable=too-few-public-methods, no-init
    """
    Implements GMPE of Nath et. al (2012) for intraplate margin seismicity in
    the Shillong Plateau of India at 25-45 km deph.

    This model is based on stochastic simulation with a mean stress drop of 150
    bars.

    Verification of mean value data was done by digitizing Figure 11 using
    http://arohatgi.info/WebPlotDigitizer/app/. Note that this independent
    verification did not include magnitude dependence or standard deviations.
    
    PGV is not provided in this gsim class because the coefficients within the
    paper provide physically unrealistic values.

    **Reference**

    Page number citations in this documentation refer to:

    Nath, S. K., Thingbaijam, K. K. S., Maiti, S. K., and Nayak, A. (2012).
    Ground-motion predictions in Shillong region, northeast India. *Journal of
    Seismology*, 16(3):475–488.
    """

    #: "studies on micro-earthquakes indicated that reverse faulting is
    #: predominant in the region" (p. 476)
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    #: Set of :mod:`intensity measure types <openquake.hazardlib.imt>`
    #: this GSIM can calculate. A set should contain classes from
    #: module :mod:`openquake.hazardlib.imt`.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([SA, PGA])

    #: In simulations only the vertical component is estimated (see p. 479)
    #: and the stochastic dataset is what the GMPE is based on, so this model
    #: effectively predicts vertical motions.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.VERTICAL

    #: The only sigma is reported in the main coefficient table, Table 5 on
    #: p. 483, and must be the total standard deviation.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([const.StdDev.TOTAL])

    #: Required site parameter Vs30 is used to determing the NEHRP
    #: site class, and thus to choose site amplification coefficients
    #: and site amplification stanard error from Table 5 on p. 208.
    REQUIRES_SITES_PARAMETERS = set()

    #: Sole required rupture parameter is magnitude, since faulting
    #: style is not addressed.
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: It is noted that "r_rup is the fault-rupture distance in kilometers"
    #: following equation (11) on p. 484.
    REQUIRES_DISTANCES = {'rrup'}

    #: no site parameters are defined, the GMPE is calibrated for rock ctx
    #: m/s (provisionally set to 800 for compatibility with SiteTerm class)
    REQUIRES_SITES_PARAMETERS = set()
    DEFINED_FOR_REFERENCE_VELOCITY = 800.

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        # pylint: disable=too-many-arguments
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for specification of input and result values.

        Implements equation (11) on p. 484:

        ``ln(P) = c1 + c2*M + c3*(10 - M)^3 + c4*ln(R + c5*exp(c6*M)``
        """
        for m, imt in enumerate(imts):
            c = self.COEFFS_BEDROCK[imt]
            coeffs = CONSTS.copy()
            for n in c.dtype.names:
                coeffs[n] = c[n]

            # compute bedrock motion, equation (11)
            ln_mean = _compute_mean(ctx, coeffs)

            # obtain standard deviation
            ln_stddev = _get_stddev(coeffs)

            if hasattr(self, 'COEFFS_UPPER'):  # in subclass
                # compute site corrections, equation (9)
                corr = self.COEFFS_UPPER[imt]['correction']
                ln_mean += np.log(corr)

            mean[m], sig[m] = ln_mean, ln_stddev

    #: Coefficients taken from Table 5, p. 483.
    COEFFS_BEDROCK = CoeffsTable(sa_damping=5., table="""\
     IMT      c1      c2      c3      c4       c5      c6   sigma
     pga  9.1430  0.2470 -0.0140 -2.6700  32.9458  0.0663  0.3300
     0.1  4.8183  0.3531 -0.0152 -1.7445   5.0087  0.2973  0.3441
     0.2  4.0396  0.3376 -0.0148 -1.6820   3.9925  0.2764  0.3117
     0.5  2.6536  0.5799 -0.0162 -1.8479   1.9570  0.3919  0.3384
       1  2.9150  0.1758 -0.0235 -1.3546   7.1026  0.1700  0.3762
       2 -0.8191  0.4950 -0.0247 -1.1763   1.4407  0.3910  0.4536
       4 -6.9619  0.9977 -0.0270 -0.8393   0.0000  1.9613  0.4614
    """)


class NathEtAl2012Upper(NathEtAl2012Lower):
    # pylint: disable=too-few-public-methods, no-init
    """
    Implements GMPE of Nath et. al (2012) for intraplate margin seismicity in
    the Shillong Plateau of India above 25 km deph.

    This model is based on stochastic simulation with a mean stress drop of 40
    bars.
    """
    #: Coefficients taken from Table 6, p. 485.
    COEFFS_UPPER = CoeffsTable(sa_damping=5., table="""\
     IMT  correction
     pga      0.6169
     0.1      0.6249
     0.2      0.6584
     0.5      0.8355
       1      0.8704
       2      0.9109
       4      0.9292
    """)
