# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2018 GEM Foundation
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
Module exports:
class:`ECOS2009`,
class:`ECOS2009Highest`
"""
import numpy as np

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import MMI


def _compute_mean(C, ctx, num_sites):
    """
    Compute mean value.
    """
    c0 = C['alpha'] * (C['a']*np.log(30/C['hypo_depth']) +
                       C['b']*(30-C['hypo_depth'])) + C['beta']
    c1 = C['alpha']
    c2 = -(C['a']) * C['alpha']
    c3 = -(C['b']) * C['alpha']

    log_term = np.log(ctx.rhypo / C['hypo_depth'])
    dist_term = c3 * (ctx.rhypo-C['hypo_depth'])

    return (ctx.mag - c2 * log_term - dist_term - c0) / c1


class ECOS2009(GMPE):
    """
    Implements the Intensity Prediction Equation of
    "Calibration of historical earthquakes for the earthquake catalogue
    of Switzerland (ECOS-09)": Appendix D

    This class implements the version using "all intensity levels",
    fixed depth (h=10km) and the weighting scheme "no weighting".

    See page 18 for general equation (8) - needs to be solved for I_obs -
    and equation (9) for estimating coefficients c0,c1,c2,c3.
    Coefficients a,b are taken from Table 4 on page 19.
    Coefficients alpha,beta are taken from Table 5 on page 19.

    Implemented by laurentiu.danciu@sed.ethz.ch
    """

    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {MMI}

    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.HORIZONTAL

    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    REQUIRES_SITES_PARAMETERS = set()

    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'hypo_depth'}

    #: Required distance rhypo
    REQUIRES_DISTANCES = {'rhypo'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            mean[m] = _compute_mean(C, ctx, imt)
            sig[m] = C['sigma']

    #: Coefficient table constructed from the electronic suplements of the
    #: original paper.
    COEFFS = CoeffsTable(table="""\
    IMT             a          b    alpha      beta   hypo_depth   sigma
    MMI      -0.67755   -0.00174   0.7725    1.0363      10.0      0.4073
        """)


class ECOS2009Highest(ECOS2009):
    """
    This class implements the version using "three highest intensity levels",
    fixed depth (h=10km) and the weighting scheme "no weighting".

    See page 18 for general equation (8) - needs to be solved for I_obs -
    and equation (9) for estimating coefficients c0,c1,c2,c3.
    Coefficients a,b are taken from Table 4 on page 19.
    Coefficients alpha,beta are taken from Table 5 on page 19.
    """

    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            mean[m] = _compute_mean(C, ctx, imt)
            sig[m] = C['sigma']

    COEFFS = CoeffsTable(sa_damping=5.0, table="""\
    IMT             a          b    alpha      beta   hypo_depth   sigma
    MMI       -0.4834   -0.00179    0.732     1.132      10.0      0.36474
    """)
