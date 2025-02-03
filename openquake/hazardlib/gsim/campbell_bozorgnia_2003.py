# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2025 GEM Foundation
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
Module exports :class:`CampbellBozorgnia2003NSHMP2007`.
"""
import numpy as np

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


def _get_mean(C, mag, rake, dip, rrup, rjb):
    """
    Return mean value (eq. 1, page 319).
    """
    f1 = _compute_magnitude_scaling(C, mag)
    f2 = _compute_distance_scaling(C, mag, rrup)
    f3 = _compute_faulting_mechanism(C, rake, dip)
    f4 = _compute_far_source_soil_effect(C)
    f5 = _compute_hanging_wall_effect(C, rjb, rrup, dip, mag)
    return C['c1'] + f1 + C['c4'] * np.log(np.sqrt(f2)) + f3 + f4 + f5


def _compute_magnitude_scaling(C, mag):
    """
    Compute and return magnitude scaling term (eq.2, page 319)
    """
    return C['c2'] * mag + C['c3'] * (8.5 - mag) ** 2


def _compute_distance_scaling(C, mag, rrup):
    """
    Compute distance scaling term (eq.3, page 319).

    The distance scaling assumes the near-source effect of local site
    conditions due to 50% very firm soil and soft rock and 50% firm rock.
    """
    g = C['c5'] + C['c6'] * 0.5 + C['c7'] * 0.5

    return rrup ** 2 + (np.exp(
        C['c8'] * mag + C['c9'] * (8.5 - mag) ** 2) * g) ** 2


def _compute_faulting_mechanism(C, rake, dip):
    """
    Compute faulting mechanism term (see eq. 5, page 319).

    Reverse faulting is defined as occurring on steep faults (dip > 45)
    and rake in (22.5, 157.5).

    Thrust faulting is defined as occurring on shallow dipping faults
    (dip <=45) and rake in (22.5, 157.5)
    """
    # flag for reverse faulting
    frv = (dip > 45) & (22.5 <= rake) & (rake <= 157.5)
    # flag for thrust faulting
    fth = (dip <= 45) & (22.5 <= rake) & (rake <= 157.5)
    return C['c10'] * frv + C['c11'] * fth


def _compute_far_source_soil_effect(C):
    """
    Compute far-source effect of local site conditions (see eq. 6,
    page 319) assuming 'firm rock' conditions.
    """
    return C['c14']


def _compute_hanging_wall_effect(C, rjb, rrup, dip, mag):
    """
    Compute hanging-wall effect (see eq. 7, 8, 9 and 10 page 319).
    Considers correct version of equation 8 as given in the erratum and not
    in the original paper.
    """
    # eq. 8 (to be noticed that the USGS-NSHMP implementation defines
    # the hanging-wall term for all rjb distances, while in the original
    # manuscript, hw is computed only for rjb < 5). Again the 'firm rock'
    # is considered
    hw = np.zeros_like(rjb)
    hw[dip <= 70.] = (5. - rjb[dip <= 70.]) / 5.

    # eq. 9
    f_m = np.clip(mag - 5.5, None, 1.)

    # eq. 10
    f_rrup = C['c15'] + np.zeros_like(rrup)
    idx = rrup < 8
    f_rrup[idx] *= rrup[idx] / 8

    # eq. 7 (to be noticed that the f3 factor is not included
    # while this is defined in the original manuscript)
    f_hw = hw * f_m * f_rrup

    return f_hw


class CampbellBozorgnia2003NSHMP2007(GMPE):
    """
    Implements GMPE developed by Kenneth W. Campbell and Yousef Bozorgnia and
    published as "Updated Near-Source Ground-Motion (Attenuation) Relations for
    the Horizontal and Vertical Components of Peak Ground Acceleration and
    Acceleration Responce Spectra", Bulletin of the Seismological Society of
    America, Vol. 93, No. 1, pp. 314-331, 2003.

    The class implement the equation as modified by the United States
    Geological Survey - National Seismic Hazard Mapping Project (USGS-NSHMP)
    for the 2007 Alaska model
    (http://earthquake.usgs.gov/hazards/products/ak/2007/).

    The class replicates the equation as coded in ``subroutine getCamp2000``
    in ``hazFXv7.f`` available from
    http://earthquake.usgs.gov/hazards/products/ak/2007/software/.

    The equation compute mean value for the 'firm rock' conditon.
    """
    #: Supported tectonic region type is 'active shallow crust' (see Abstract)
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are PGA and SA (see Abstract)
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is the geometric mean of two
    #: horizontal components (see paragraph 'Strong-Motion Database', page 316)
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation type is Total (see equations 11, 12 pp. 319
    #: 320)
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    #: No ctx parameters are required. Mean value is computed for
    #: 'firm rock'.
    DEFINED_FOR_REFERENCE_VELOCITY = 760.
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameters are magnitude, rake and dip (eq. 1 and
    #: following, page 319).
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'rake', 'dip'}

    #: Required distance measure are RRup and Rjb (eq. 1 and following,
    #: page 319).
    REQUIRES_DISTANCES = {'rrup', 'rjb'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            mean[m] = _get_mean(
                C, ctx.mag, ctx.rake, ctx.dip, ctx.rrup, ctx.rjb)
            sig[m] = C['c16'] - np.where(ctx.mag < 7.4, 0.07 * ctx.mag, 0.518)

    #: Coefficient table (table 4, page 321. Coefficients for horizontal
    #: component and for corrected PGA)
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT     c1     c2      c3      c4     c5      c6      c7     c8      c9      c10    c11     c12     c13     c14    c15    c16
    pga    -4.033  0.812   0.036  -1.061  0.041  -0.005  -0.018  0.766   0.034   0.343  0.351  -0.123  -0.138  -0.289  0.370  0.920
    0.10   -2.661  0.812   0.060  -1.308  0.166  -0.009  -0.068  0.621   0.046   0.224  0.313  -0.146  -0.253  -0.299  0.370  0.958
    0.20   -2.771  0.812   0.030  -1.153  0.098  -0.014  -0.038  0.704   0.026   0.296  0.342  -0.148  -0.183  -0.330  0.370  0.981
    0.30   -2.999  0.812   0.007  -1.080  0.059  -0.007  -0.022  0.752   0.007   0.359  0.385  -0.162  -0.157  -0.453  0.370  0.984
    0.50   -3.556  0.812  -0.035  -0.964  0.023  -0.002  -0.004  0.842  -0.036   0.406  0.479  -0.122  -0.130  -0.528  0.370  0.990
    1.0    -3.867  0.812  -0.101  -0.964  0.019   0       0      0.842  -0.105   0.329  0.338  -0.073  -0.072  -0.607  0.281  1.021
    2.0    -4.311  0.812  -0.180  -0.964  0.019   0       0      0.842  -0.187   0.060  0.064  -0.124  -0.116  -0.649  0.160  1.021
    """)
