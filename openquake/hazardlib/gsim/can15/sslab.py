"""
:module:`openquake.hazardlib.gsim.nrcan15` implements
:class:`SSlabCan15Mid`, :class:`SSlabCan15Upp`,
:class:`SSlabCan15Low`
"""

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
    REQUIRES_DISTANCES = set(('repi',))

    # Distances to be excluded while checking this GMPE. This parameter is
    # needed to avoid conflicts with the parameters included in the
    # verification table. For this GMPE the distance required is just
    # epicentral and rrup and rjb are computed following the methodology
    # described in Atkinson (2012).
    # See also :module:`openquake.hazardlib.tests.gsim.utils.py`
    DO_NOT_CHECK_DISTANCES = set(('rrup', 'rjb'))

    #: GMPE not tested against independent implementation so raise
    #: not verified warning
    non_verified = True

    #: Shear-wave velocity for reference soil conditions in [m s-1]
    DEFINED_FOR_REFERENCE_VELOCITY = 760.

    #: Supported standard deviations
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([const.StdDev.TOTAL])

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """

        # get original values
        hslab = 50  # See info in GMPEt_Inslab_med.dat
        rjb, rrup = utils.get_equivalent_distance_inslab(rup.mag, dists.repi,
                                                         hslab)
        dists.rjb = rjb
        dists.rrup = rrup
        mean, stddevs = super().get_mean_and_stddevs(sites, rup, dists, imt,
                                                     stddev_types)
        cff = self.SITE_COEFFS[imt]
        mean_adj = np.log(np.exp(mean) * 10**cff['mf'])
        stddevs = [np.ones(len(dists.rrup))*get_sigma(imt)]
        return mean_adj, stddevs

    # These are the coefficients included in Table 1 of Atkinson and Adams
    # (2013)
    SITE_COEFFS = CoeffsTable(sa_damping=5, table="""\
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

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        # get original values
        hslab = 50  # See info in GMPEt_Inslab_med.dat
        rjb, rrup = utils.get_equivalent_distance_inslab(rup.mag, dists.repi,
                                                         hslab)
        dists.rjb = rjb
        dists.rrup = rrup
        mean, stddevs = super().get_mean_and_stddevs(sites, rup, dists, imt,
                                                     stddev_types)
        # adjust mean values using the reccomended delta (see Atkinson and
        # Adams, 2013; page 992)
        delta = np.log(10.**(0.15))
        mean_adj = mean - delta
        stddevs = [np.ones(len(dists.rrup))*get_sigma(imt)]
        return mean_adj, stddevs


class SSlabCan15Upp(SSlabCan15Mid):
    """
    Slab backbone model for the Canada 2015 model. High ground motion version
    """

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        # get original values
        hslab = 50  # See info in GMPEt_Inslab_med.dat
        rjb, rrup = utils.get_equivalent_distance_inslab(rup.mag, dists.repi,
                                                         hslab)
        dists.rjb = rjb
        dists.rrup = rrup
        mean, stddevs = super().get_mean_and_stddevs(sites, rup, dists, imt,
                                                     stddev_types)
        # adjust mean values using the reccomended delta (see Atkinson and
        # Adams, 2013; page 992)
        delta = np.log(10.**(0.15))
        mean_adj = mean + delta
        stddevs = [np.ones(len(dists.rrup))*get_sigma(imt)]
        return mean_adj, stddevs
