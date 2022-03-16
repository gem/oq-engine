"""
:module:`openquake.hazardlib.gsim.nrcan15` implements
:class:`SSlabCan15Mid`, :class:`SSlabCan15Upp`,
:class:`SSlabCan15Low`
"""
import copy
import numpy as np

from openquake.hazardlib import const
from openquake.hazardlib.gsim.can15.western import get_sigma
from openquake.hazardlib.gsim.can15 import utils
from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib.gsim.zhao_2006 import ZhaoEtAl2006SSlab


class SSlabCan15Mid(ZhaoEtAl2006SSlab):
    """
    Implements the Zhao et al. (2006) for inslab earthquakes with
    modifications requested for the calculation of hazard for the fifth
    generation of Canada hazard maps, released in 2015. See Atkinson and Adams
    (2013).
    """
    #: Required distance is only repi since rrup and rjb are obtained from repi
    REQUIRES_DISTANCES = {'repi'}

    # Distances to be excluded while checking this GMPE. This parameter is
    # needed to avoid conflicts with the parameters included in the
    # verification table. For this GMPE the distance required is just
    # epicentral and rrup and rjb are computed following the methodology
    # described in Atkinson (2012).
    # See also :module:`openquake.hazardlib.tests.gsim.utils.py`
    DO_NOT_CHECK_DISTANCES = {'rrup', 'rjb'}

    #: GMPE not tested against independent implementation so raise
    #: not verified warning
    non_verified = True

    #: Shear-wave velocity for reference soil conditions in [m s-1]
    DEFINED_FOR_REFERENCE_VELOCITY = 760.

    #: Supported standard deviations
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    delta = 0.

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        # get original values
        hslab = 50  # See info in GMPEt_Inslab_med.dat
        rjb, rrup = utils.get_equivalent_distance_inslab(
            ctx.mag, ctx.repi, hslab)
        ctx = copy.copy(ctx)
        ctx.rjb = rjb
        ctx.rrup = rrup
        super().compute(ctx, imts, mean, sig, tau, phi)
        for m, imt in enumerate(imts):
            cff = self.COEFFS_SITE[imt]
            mean[m] = np.log(np.exp(mean[m]) * 10**cff['mf']) + self.delta
            sig[m] = get_sigma(imt)

    # These are the coefficients included in Table 1 of Atkinson and Adams
    # (2013)
    COEFFS_SITE = CoeffsTable(sa_damping=5, table="""\
    IMT        mf
    pgv     1.000
    pga    -0.301
    0.040  -0.357
    0.100  -0.357
    0.200  -0.222
    0.300  -0.091
    0.400   0.000
    1.000   0.017
    2.000   0.179
    3.000   0.079
    5.000   0.040
    10.00   0.000
    """)


class SSlabCan15Low(SSlabCan15Mid):
    """
    Slab backbone model for the Canada 2015 model. Low ground motion version
    """
    # adjust mean values using the recommended delta (see Atkinson and
    # Adams, 2013; page 992)
    delta = -np.log(10.**0.15)


class SSlabCan15Upp(SSlabCan15Mid):
    """
    Slab backbone model for the Canada 2015 model. High ground motion version
    """
    # adjust mean values using the recommended delta (see Atkinson and
    # Adams, 2013; page 992)
    delta = np.log(10.**0.15)
