"""
:module:`openquake.hazardlib.gsim.sinter` implements
:class:`SInterCan15Mid`, :class:`SInterCan15Upp`, :class:`SInterCan15Low`
"""

import numpy as np

from openquake.hazardlib import const, contexts
from openquake.hazardlib.gsim.can15.western import get_sigma
from openquake.hazardlib.gsim.base import CoeffsTable
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

    def compute(self, ctx, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        super().compute(ctx, imts, mean, sig, tau, phi)
        for m, imt in enumerate(imts):
            mean[m] += np.log(SInterCan15Mid.COEFFS_SITE[imt]['mf'])


class SInterCan15Mid(ZhaoEtAl2006SInter):
    """
    Implements the Interface backbone model used for computing hazard for t
    the 2015 version of the Canada national hazard model developed by NRCan.
    """
    #: Supported tectonic region type is subduction interface
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    #: Required site parameters
    REQUIRES_SITES_PARAMETERS = {'vs30', 'backarc'}

    #: GMPE not tested against independent implementation so raise
    #: not verified warning
    non_verified = True

    #: Shear-wave velocity for reference soil conditions in [m s-1]
    DEFINED_FOR_REFERENCE_VELOCITY = 760.

    #: Supported standard deviations
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    REQUIRES_ATTRIBUTES = {'sgn'}

    gsims = [ZhaoEtAl2006SInter(), AtkinsonMacias2009(),
             AbrahamsonEtAl2015SInter(),
             GhofraniAtkinson2014()]  # underlying GSIMs
    sgn = 0

    def compute(self, ctx, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        imtls = {imt.string: [0] for imt in imts}
        cmaker = contexts.ContextMaker(
            self.DEFINED_FOR_TECTONIC_REGION_TYPE,
            self.gsims, {'imtls': imtls})
        mean_zh06, mean_am09, mean_ab15, mean_ga14 = cmaker.get_mean_stds(
            [ctx], None)  # 4 arrays of shape (1, M, N)

        # Computing adjusted means
        for m, imt in enumerate(imts):
            cff = self.COEFFS_SITE[imt]
            mean[m] = (np.log(np.exp(mean_zh06[0, m]) * cff['mf']) * 0.1 +
                       mean_am09[0, m] * 0.5 + mean_ab15[0, m] * 0.2 +
                       np.log(np.exp(mean_ga14[0, m]) * cff['mf']) * 0.2)
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
