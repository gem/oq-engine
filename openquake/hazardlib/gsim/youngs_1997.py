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
Module exports :class:`YoungsEtAl1997SInter`, :class:`YoungsEtAl1997SSlab`,
:class:`YoungsEtAl1997GSCSSlabBest`, :class:`YoungsEtAl1997GSCSSlabUpperLimit`,
:class:`YoungsEtAl1997GSCSSlabLowerLimit`,
:class:`YoungsEtAl1997SInterNSHMP2008`.
"""
import numpy as np
import copy

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA

#: constants for mean value calculation, see table 2, page 67.
CONSTS = {'A1_rock': 0.2418,
          'A2_rock': 1.414,
          'A3_rock': 10,
          'A4_rock': 1.7818,
          'A5_rock': 0.554,
          'A6_rock': 0.00607,
          'A7_rock': 0.3846,
          'A1_soil': -0.6687,
          'A2_soil': 1.438,
          'A3_soil': 10,
          'A4_soil': 1.097,
          'A5_soil': 0.617,
          'A6_soil': 0.00648,
          'A7_soil': 0.3643}


def _compute_mean(C, A1, A2, A3, A4, A5, A6, mag, hypo_depth,
                  rrup, mean, idx):
    """
    Compute mean for subduction interface events, as explained in table 2,
    page 67.
    """
    if isinstance(mag, np.ndarray):
        mag = mag[idx]
        hypo_depth = hypo_depth[idx]
    mean[idx] = (A1 + A2 * mag + C['C1'] + C['C2'] * (A3 - mag) ** 3 +
                 C['C3'] * np.log(rrup[idx] + A4 * np.exp(A5 * mag)) +
                 A6 * hypo_depth)


def get(array, idx):
    return array[idx] if isinstance(array, np.ndarray) else array


class YoungsEtAl1997SInter(GMPE):
    """
    Implements GMPE developed by R.R Youngs, S-J, Chiou, W.J. Silva, J.R.
    Humphrey and published as "Strong Ground Motion Attenuation Relationships
    for Subduction Zone Earthquakes" (Seismological Research Letters Volume 68,
    No. 1, pages 58-73, 1997).
    This class implements the equations for 'Subduction Interface' (that's why
    the class name ends with 'SInter').
    Mean value for SA at 4 s on rock (not originally supported) is obtained
    from mean value at 3 s divided by a factor equal to 0.399
    (scaling factor computed in the context of the SHARE project obtained as
    average ratio between median values at 4 and 3 seconds as predicted by
    SHARE subduction GMPEs).
    """
    #: Supported tectonic region type is subduction interface
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration, see table 2, page 67.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is the average horizontal
    #: component
    #: attr:`~openquake.hazardlib.const.IMC.GEOMETRIC_MEAN`, see
    #: paragraph: 'Analysis of peak horizontal accelerations', p. 59.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation types is total, table 2, page 67.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    DEFINED_FOR_REFERENCE_VELOCITY = 800

    #: Required site parameters is Vs30, used to distinguish between rock
    #: and soil ctx, see paragraph 'Strong Motion Data Base', page 59.
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are magnitude and focal depth, see
    #: equations 1 and 2, pages 59 and 66, respectively.
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'hypo_depth'}

    #: Required distance measure is Rrup, see equations 1 and 2, page 59 and
    #: 66, respectively.
    REQUIRES_DISTANCES = {'rrup'}

    #: Vs30 value representing typical rock conditions in California.
    ROCK_VS30 = 760

    delta = 0  # changed in subclasses

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        if self.__class__.__name__.endswith('NSHMP2008'):
            # NSHMP2008 adjustement of the hypo_depth
            ctx = copy.copy(ctx)
            ctx.hypo_depth = 20.
        idx_rock = ctx.vs30 >= self.ROCK_VS30
        idx_soil = ctx.vs30 < self.ROCK_VS30
        for m, imt in enumerate(imts):

            if idx_rock.any():
                C = self.COEFFS_ROCK[imt]
                _compute_mean(C, CONSTS['A1_rock'],
                              CONSTS['A2_rock'], CONSTS['A3_rock'],
                              CONSTS['A4_rock'], CONSTS['A5_rock'],
                              CONSTS['A6_rock'], ctx.mag, ctx.hypo_depth,
                              ctx.rrup, mean[m], idx_rock)
                sig[m, idx_rock] += C['C4'] + C['C5'] * np.clip(
                    get(ctx.mag, idx_rock), 0, 8.)

                if imt == SA(period=4.0, damping=5.0):
                    mean[m] /= 0.399

            if idx_soil.any():
                C = self.COEFFS_SOIL[imt]
                _compute_mean(C, CONSTS['A1_soil'],
                              CONSTS['A2_soil'], CONSTS['A3_soil'],
                              CONSTS['A4_soil'], CONSTS['A5_soil'],
                              CONSTS['A6_soil'], ctx.mag, ctx.hypo_depth,
                              ctx.rrup, mean[m], idx_soil)
                sig[m, idx_soil] += C['C4'] + C['C5'] * np.clip(
                    get(ctx.mag, idx_soil), 0, 8.)

            if (self.DEFINED_FOR_TECTONIC_REGION_TYPE ==
                    const.TRT.SUBDUCTION_INTRASLAB):  # sslab correction
                if imt.period == 4.0:
                    mean[m, idx_rock] += 0.3846 / 0.399
                else:
                    mean[m, idx_rock] += 0.3846

                mean[m, idx_soil] += 0.3643

        mean += self.delta

    #: Coefficient table containing soil coefficients,
    #: taken from table 2, p. 67
    COEFFS_SOIL = CoeffsTable(sa_damping=5, table="""\
    IMT       C1        C2         C3       C4       C5
    pga       0.000     0.0000    -2.329    1.45    -0.1
    0.075     2.400    -0.0019    -2.697    1.45    -0.1
    0.100     2.516    -0.0019    -2.697    1.45    -0.1
    0.200     1.549    -0.0020    -2.464    1.45    -0.1
    0.300     0.793    -0.0020    -2.327    1.45    -0.1
    0.400     0.144    -0.0035    -2.230    1.45    -0.1
    0.500    -0.438    -0.0048    -2.140    1.45    -0.1
    0.750    -1.704    -0.0066    -1.952    1.45    -0.1
    1.000    -2.870    -0.0114    -1.785    1.45    -0.1
    1.500    -5.101    -0.0164    -1.470    1.50    -0.1
    2.000    -6.433    -0.0221    -1.290    1.55    -0.1
    3.000    -6.672    -0.0235    -1.347    1.65    -0.1
    4.000    -7.618    -0.0235    -1.272    1.65    -0.1
        """)

    #: Coefficient table containing rock coefficients,
    #: taken from table 2, p. 67
    COEFFS_ROCK = CoeffsTable(sa_damping=5, table="""\
    IMT   C1        C2         C3       C4       C5
    pga       0.000      0.0000    -2.552    1.45    -0.1
    0.075     1.275      0.0000    -2.707    1.45    -0.1
    0.100     1.188     -0.0011    -2.655    1.45    -0.1
    0.200     0.722     -0.0027    -2.528    1.45    -0.1
    0.300     0.246     -0.0036    -2.454    1.45    -0.1
    0.400    -0.115    -0.0043    -2.401    1.45    -0.1
    0.500    -0.400    -0.0048    -2.360    1.45    -0.1
    0.750    -1.149    -0.0057    -2.286    1.45    -0.1
    1.000    -1.736    -0.0064    -2.234    1.45    -0.1
    1.500    -2.634    -0.0073    -2.160    1.50    -0.1
    2.000    -3.328    -0.0080    -2.107    1.55    -0.1
    3.000    -4.511    -0.0089    -2.033    1.65    -0.1
    4.000    -4.511    -0.0089    -2.033    1.65    -0.1
        """)


class YoungsEtAl1997SInterNSHMP2008(YoungsEtAl1997SInter):
    """
    Extends :class:`YoungsEtAl1997SInter` and fix rupture hypocenter depth
    at 20 km as defined by the National Seismic Hazard Mapping Project (NSHMP)
    for the 2008 US model.

    The class implement the equation as coded in ``subroutine getGeom`` in
    ``hazSUBXnga.f`` Fortran code available at:
    http://earthquake.usgs.gov/hazards/products/conterminous/2008/software/
    """


class YoungsEtAl1997SSlab(YoungsEtAl1997SInter):
    """
    Implements GMPE developed by R.R Youngs, S-J, Chiou, W.J. Silva, J.R.
    Humphrey and published as "Strong Ground Motion Attenuation Relationships
    for Subduction Zone Earthquakes" (Seismological Research Letters Volume 68,
    No. 1, pages 58-73, 1997).
    This class implements the equations for 'Subduction IntraSlab' (that's why
    the class name ends with 'SSlab').
    Mean value for SA at 4 s on rock (not originally supported) is obtained
    from mean value at 3 s divided by a factor equal to 0.399
    (scaling factor computed in the context of the SHARE project obtained as
    average ratio between median values at 4 and 3 seconds as predicted by
    SHARE subduction GMPEs).
    """
    #: Supported tectonic region type is subduction intraslab
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB


class YoungsEtAl1997GSCSSlabBest(YoungsEtAl1997SSlab):
    """
    Implement modification to :class:`YoungsEtAl1997SSlab` as defined by GSC
    (Geological Survey of Canada) for the 2010 Western Canada Model.
    Includes adjustement for firm ground. The model is associated to the 'Best'
    case, that is mean value unaffected.
    """
    delta = np.log(1.162)


class YoungsEtAl1997GSCSSlabUpperLimit(YoungsEtAl1997GSCSSlabBest):
    """
    Implement modification to :class:`YoungsEtAl1997SSlab` as defined by GSC
    (Geological Survey of Canada) for the 2010 Western Canada Model.
    Includes adjustement for firm ground. The model is associated to the 'Upper
    Limit' case, that is mean value plus 0.7 natural logarithm.
    """
    delta = np.log(1.162) + 0.7


class YoungsEtAl1997GSCSSlabLowerLimit(YoungsEtAl1997GSCSSlabBest):
    """
    Implement modification to :class:`YoungsEtAl1997SSlab` as defined by GSC
    (Geological Survey of Canada) for the 2010 Western Canada Model.
    Includes adjustement for firm ground. The model is associated to the 'Lower
    Limit' case, that is mean value minus 0.7 natural logarithm.
    """
    delta = np.log(1.162) - 0.7
