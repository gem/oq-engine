"""
:module:`openquake.hazardlib.gsim.sinter` implements
:class:`SInterCan15Mid`, :class:`SInterCan15Upp`, :class:`SInterCan15Low`
"""

import numpy as np

from openquake.hazardlib.gsim.can15.western import get_sigma
from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib.gsim.zhao_2006 import ZhaoEtAl2006SInter
from openquake.hazardlib.gsim.atkinson_macias_2009 import AtkinsonMacias2009
from openquake.hazardlib.gsim.abrahamson_2015 import AbrahamsonEtAl2015SInter
from openquake.hazardlib.gsim.ghofrani_atkinson_2014 import \
    GhofraniAtkinson2014


class SInterCan15Mid(ZhaoEtAl2006SInter):
    """
    """

    def _get_delta(dists):
        """
        Computes the additional delta to be used for the computation of the
        upp and low models
        """
        delta = np.zeros_like(dists.rrup)
        delta = np.min([(0.15-0.0007*dists.rrup), 0.35])
        return delta

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        mean, stds = self._get_mean_and_stddevs(sites, rup, dists, imt,
                                                stddev_types)

    def _get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """ """
        # Zhao et al. 2006 - Vs30 + Rrup
        mean, stds1 = super().get_mean_and_stddevs(sites, rup, dists, imt,
                                                   stddev_types)
        cff = self.SITE_COEFFS[imt]
        mean_zh06 = mean + np.log(cff['mf'])
        # Atkinson and Macias (2009) - Rrup
        gmpe = AtkinsonMacias2009()
        mean_am09, stds2 = gmpe.get_mean_and_stddevs(sites, rup, dists, imt,
                                                     stddev_types)
        mean_am09 += np.log(cff['mf'])
        # Abrahamson et al. (2015) - Rrup + vs30 + backarc
        gmpe = AbrahamsonEtAl2015SInter()
        mean_ab15, stds3 = gmpe.get_mean_and_stddevs(sites, rup, dists, imt,
                                                     stddev_types)
        # Ghofrani and Atkinson (2014) - Rrup + vs30
        gmpe = GhofraniAtkinson2014()
        mean_ga14, stds4 = gmpe.get_mean_and_stddevs(sites, rup, dists, imt,
                                                     stddev_types)
        mean_ga14 += np.log(cff['mf'])
        # Computing adjusted mean and stds
        mean_adj = np.log(np.exp(mean_zh06)*0.1 + np.exp(mean_am09)*0.5 +
                          np.exp(mean_ab15)*0.2 + np.exp(mean_ga14)*0.2)
        # note that in this case we do not apply a triangular smoothing on
        # distance as explained at page 996
        stds_adj = np.log(np.exp(stds1) + np.exp(stds2) + np.exp(stds3) +
                          np.exp(stds4))
        return mean_adj, stds_adj

    SITE_COEFFS = CoeffsTable(sa_damping=5, table="""\
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


class SInterCan15Low(SInterCan15Mid):

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        mean, stds = self._get_mean_and_stddevs(sites, rup, dists, imt,
                                                stddev_types)
        mean -= self._get_delta(dists)


class SInterCan15Upp(SInterCan15Mid):

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        mean, stds = self._get_mean_and_stddevs(sites, rup, dists, imt,
                                                stddev_types)
        mean += self._get_delta(dists)
        stddevs = [np.ones(len(dists.rjb))*get_sigma(imt)]
        return mean, stddevs
