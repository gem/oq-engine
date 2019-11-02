# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2019 GEM Foundation
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
Module exports :class:`AbrahamsonEtAl2014NSHMPUpper`
               :class:`AbrahamsonEtAl2014NSHMPLower`
               :class:`BooreEtAl2014NSHMPUpper`
               :class:`BooreEtAl2014NSHMPLower`
               :class:`CampbellBozorgnia2014NSHMPUpper`
               :class:`CampbellBozorgnia2014NSHMPLower`
               :class:`ChiouYoungs2014NSHMPUpper`
               :class:`ChiouYoungs2014NSHMPLower`
               :class:`Idriss2014NSHMPUpper`
               :class:`Idriss2014NSHMPLower`
"""
import numpy as np
# NGA West 2 GMPEs
from openquake.hazardlib.gsim import base
from openquake.hazardlib.gsim.abrahamson_2014 import AbrahamsonEtAl2014
from openquake.hazardlib.gsim.boore_2014 import BooreEtAl2014
from openquake.hazardlib.gsim.campbell_bozorgnia_2014 import \
    CampbellBozorgnia2014
from openquake.hazardlib.gsim.chiou_youngs_2014 import ChiouYoungs2014
from openquake.hazardlib.gsim.idriss_2014 import Idriss2014
# Required for Atkinson and Macias (2009)
from openquake.hazardlib.gsim.atkinson_macias_2009 import AtkinsonMacias2009
from openquake.hazardlib.gsim.can15.sinter import SInterCan15Mid


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

    def get_mean_and_stddevs(self, sctx, rctx, dctx, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # Get original mean and standard deviations
        mean, stddevs = super().get_mean_and_stddevs(
            sctx, rctx, dctx, imt, stddev_types)
        mean += np.log(SInterCan15Mid.SITE_COEFFS[imt]['mf'])
        return mean, stddevs


def nga_west2_epistemic_adjustment(magnitude, distance):
    """
    Applies the "average" adjustment factor for epistemic uncertainty
    as defined in Table 17 of Petersen et al., (2014)::

                 |  R < 10.  | 10.0 <= R < 30.0  |    R >= 30.0
     -----------------------------------------------------------
       M < 6.0   |   0.37    |      0.22         |       0.22
     6 <= M <7.0 |   0.25    |      0.23         |       0.23
       M >= 7.0  |   0.40    |      0.36         |       0.33
    """
    if magnitude < 6.0:
        adjustment = 0.22 * np.ones_like(distance)
        adjustment[distance < 10.0] = 0.37
    elif magnitude >= 7.0:
        adjustment = 0.36 * np.ones_like(distance)
        adjustment[distance < 10.0] = 0.40
        adjustment[distance >= 30.0] = 0.33
    else:
        adjustment = 0.23 * np.ones_like(distance)
        adjustment[distance < 10.0] = 0.25
    return adjustment


def get_mean_and_stddevs(self, sctx, rctx, dctx, imt, stddev_types):
    """
    See :meth:`superclass method
    <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
    for spec of input and result values.
    """
    mean, stddevs = self.__class__.__base__.get_mean_and_stddevs(
        self, sctx, rctx, dctx, imt, stddev_types)

    # return mean, increased by the adjustment factor, and standard deviation
    self.adjustment = nga_west2_epistemic_adjustment(rctx.mag, dctx.rrup)
    return mean + self.sgn * self.adjustment, stddevs


DEFAULT_WEIGHTING = [(0.185, -1.), (0.63, 0.), (0.185, 1.)]
SUFFIX = {0: 'Mean', -1: 'Lower', 1: 'Upper'}


def adjust(basecls, sgn):
    """
    :param basecls:
        a base class (Idriss2014, ChiouYoungs2014, CampbellBozorgnia2014,
        BooreEtAl2014, AbrahamsonEtAl2014)
    :param sgn:
        sign of the adjustement factor, -1, 0, +1
    :returns:
        adjusted subclass of basecls for use with the NSHMP 2014 model
    """
    name = basecls.__name__ + 'NSHMP' + SUFFIX[sgn]
    dic = dict(get_mean_and_stddevs=get_mean_and_stddevs, sgn=sgn)
    if sgn == 0:
        dic['weights_signs'] = DEFAULT_WEIGHTING
        dic['__doc__'] = ("Implements the %s GMPE for application to the "
                          "weighted mean case") % basecls.__name__
    else:
        dic['__doc__'] = ("Implements the %d NSHMP adjustment factor for the"
                          " %s NGA West 2 GMPE" % (sgn, basecls.__name__))
    # the base class requires only Rjb, but the epistemic adjustment factors
    # are given in terms of Rrup, so both are required in the subclass
    dic['REQUIRES_DISTANCES'] = frozenset(
        basecls.REQUIRES_DISTANCES | {'rrup'})

    return type(name, (basecls,), dic)


for cls in (Idriss2014, ChiouYoungs2014, CampbellBozorgnia2014, BooreEtAl2014,
            AbrahamsonEtAl2014):
    # register Upper/Lower/Mean subclasses
    for sgn in (1, -1, 0):
        c = adjust(cls, sgn)
        globals()[c.__name__] = c
