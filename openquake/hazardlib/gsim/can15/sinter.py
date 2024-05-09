# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# 
# Copyright (C) 2014-2023, GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
"""
:module:`openquake.hazardlib.gsim.sinter` implements
:class:`SInterCan15Mid`, :class:`SInterCan15Upp`, :class:`SInterCan15Low`
"""

import numpy as np

from openquake.hazardlib import const, contexts
from openquake.hazardlib.gsim.can15.western import get_sigma
from openquake.hazardlib.gsim.base import CoeffsTable, GMPE
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib.gsim.zhao_2006 import ZhaoEtAl2006SInter
from openquake.hazardlib.gsim.atkinson_macias_2009 import AtkinsonMacias2009
from openquake.hazardlib.gsim.abrahamson_2015 import AbrahamsonEtAl2015SInter
from openquake.hazardlib.gsim.ghofrani_atkinson_2014 import (
    GhofraniAtkinson2014)


class AtkinsonMacias2009NSHMP2014(AtkinsonMacias2009):
    """
    Implements an adjusted version of the Atkinson and Macias (2009) GMPE.
    The motion is scaled B/C conditions following the approach described in
    Atkinson and Adams (2013) and implemented in
    :mod:`openquake.hazardlib.gsim.can15.sinter`.
    """
    #: Shear-wave velocity for reference soil conditions in [m s-1]
    DEFINED_FOR_REFERENCE_VELOCITY = 760.

    #: GMPE not tested against independent implementation so raise
    #: not verified warning
    non_verified = True

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        super().compute(ctx, imts, mean, sig, tau, phi)
        for m, imt in enumerate(imts):
            mean[m] += np.log(SInterCan15Mid.COEFFS_SITE[imt]['mf'])


class SInterCan15Mid(GMPE):
    """
    Implements the Interface backbone model used for computing hazard for t
    the 2015 version of the Canada national hazard model developed by NRCan.
    """
    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration, see paragraph 'Development of Base Model'
    #: p. 901.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is geometric mean
    #: of two horizontal components :
    #: attr:`~openquake.hazardlib.const.IMC.GEOMETRIC_MEAN`, see paragraph
    #: 'Development of Base Model', p. 901.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Required site parameters is Vs30.
    #: See table 2, p. 901.
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are magnitude, rake, and focal depth.
    #: See paragraph 'Development of Base Model', p. 901.
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'rake', 'hypo_depth'}

    #: Required distance measure is Rrup.
    #: See paragraph 'Development of Base Model', p. 902.
    REQUIRES_DISTANCES = {'rrup'}

    #: Supported tectonic region type is subduction interface, this means
    #: that factors FR, SS and SSL are assumed 0 in equation 1, p. 901.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    #: Required rupture parameters are magnitude and focal depth.
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'hypo_depth'}

    #: Supported tectonic region type is subduction interface
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    #: Required site parameters
    REQUIRES_SITES_PARAMETERS = {'vs30', 'backarc'}

    #: Shear-wave velocity for reference soil conditions in [m s-1]
    DEFINED_FOR_REFERENCE_VELOCITY = 760.

    #: Supported standard deviations
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    REQUIRES_ATTRIBUTES = {'sgn'}

    #: GMPE not tested against independent implementation so raise
    #: not verified warning
    non_verified = True

    # underlying GSIMs
    gsims = [ZhaoEtAl2006SInter(), AtkinsonMacias2009(),
             AbrahamsonEtAl2015SInter(), GhofraniAtkinson2014()]
    sgn = 0

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method <.base.GMPE.compute>`
        for spec of input and result values.
        """
        mean_zh06, mean_am09, mean_ab15, mean_ga14 = contexts.get_mean_stds(
            self.gsims, ctx, imts)[0]

        # Computing adjusted means
        for m, imt in enumerate(imts):
            cff = self.COEFFS_SITE[imt]
            mean[m] = (np.log(np.exp(mean_zh06[m]) * cff['mf']) * 0.1 +
                       mean_am09[m] * 0.5 + mean_ab15[m] * 0.2 +
                       np.log(np.exp(mean_ga14[m]) * cff['mf']) * 0.2)
            if self.sgn:
                delta = np.minimum((0.15-0.0007 * ctx.rrup), 0.35)
                mean[m] += self.sgn * delta
            sig[m] = get_sigma(imt)

    COEFFS_SITE = CoeffsTable(sa_damping=5, table="""\
    IMT        mf
    pgv     1.000
    pga     0.500
    0.040   0.440
    0.100   0.440
    0.200   0.600
    0.300   0.810
    0.400   1.000
    1.000   1.040
    2.000   1.510
    3.000   1.200
    5.000   1.100
    10.00   1.000
    """)


# must be a class to avoid breaking NRCan15SiteTerm (test event_based/case_19)
class SInterCan15Low(SInterCan15Mid):
    sgn = -1


# must be a class to avoid breaking NRCan15SiteTerm (test event_based/case_19)
class SInterCan15Upp(SInterCan15Mid):
    sgn = +1
