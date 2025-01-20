# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2025 GEM Foundation
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
Module exports :class:`MunsonThurber1997`
               :class:`MunsonThurber1997Hawaii`
               :class:`MunsonThurber1997Vector`.
"""
import numpy as np

from openquake.hazardlib.gsim.base import GMPE
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA

# assign constant
LOG10E = np.log10(np.e)


class MunsonThurber1997(GMPE):
    """
    Implements GMPE developed by Clifford G. Munson and Clifford H. Thurber
    and published as "Analysis of the Attenuation of Strong Ground Motion
    on the Island of Hawaii" (1997, Bulletin of the Seismological Society
    of America, Vol. 87, No. 4, pp. 954-960).
    """

    #: Supported tectonic region type is volcanic,
    #: see paragraph 'Introduction', page 99.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.VOLCANIC

    #: Supported intensity measure types is spectral acceleration,
    #: see table 3, pag. 110
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA}

    #: Supported intensity measure component is maximum horizontal
    #: :attr:`~openquake.hazardlib.const.IMC.VECTORIAL`,
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.HORIZONTAL

    #: Supported standard deviation type is total
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    #: Required site parameters is Vs30.
    #: See paragraph 'Predictor Variables', pag 103
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameter is magnitude
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is hypocentral distance
    #: see page 18 in Atkinson and Boore's manuscript
    REQUIRES_DISTANCES = {'rjb'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        # Distance term
        R = np.sqrt(ctx.rjb ** 2 + 11.29 ** 2)

        # Magnitude term
        M = ctx.mag - 6

        # Site term only distinguishes between lava and ash;
        # since ash sites have Vs30 in the range 60-200m/s,
        # we use this upper value as class separator
        S = np.zeros_like(R)
        S[ctx.vs30 <= 200] = 1
        for m, imt in enumerate(imts):
            # Mean ground motion (log10)
            mean[m] = (0.518 + 0.387*M - np.log10(R) - 0.00256*R + 0.335*S)
            # Converting to natural log
            mean[m] /= np.log10(np.e)
            # Constant (total) standard deviation
            sig[m] = 0.237 / LOG10E


class MunsonThurber1997Hawaii(MunsonThurber1997):
    """
    Modifies :class:`MunsonThurber1997` for use with the USGS Hawaii seismic
    hazard map of Klein FW, Frankel AD,Mueller CS, Wesson RL, Okubo PG.
    Seismic-hazard maps for Hawaii. US Geological Survey; 2000.
    """
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        super().compute(ctx, imts, mean, sig, tau, phi)

        # Magnitude term
        M = ctx.mag - 6
        right = ctx.mag > 7.7
        center = (ctx.mag > 7.) & (ctx.mag <= 7.7)
        mean[:, center] += (0.171 * (1 - M[center])) / LOG10E
        mean[:, right] += (0.1512 + 0.387 * (1 - M[right])) / LOG10E

        for m, imt in enumerate(imts):
            # define natural log of SA 0.3 sec and 0.2 sec
            if imt.period == 0.3:
                mean[m] += np.log(2.2)
            elif imt.period == 0.2:
                mean[m] += np.log(2.5)
            if (self.DEFINED_FOR_INTENSITY_MEASURE_COMPONENT ==
                    const.IMC.VECTORIAL):
                # Conversion to geometric mean of horizontal components
                # using the coefficient in Beyer and Bommer, 2006
                mean[m] += np.log(1.1)


class MunsonThurber1997Vector(MunsonThurber1997):
    """
    Modification of the original base class to correct mean ground motion
    to geometric mean of horizontal components (Beyer and Bommer, 2006)
    """
    #: Supported intensity measure component is geometric mean of horizontal
    #: :attr:`~openquake.hazardlib.const.IMC.VECTORIAL`,
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.VECTORIAL
