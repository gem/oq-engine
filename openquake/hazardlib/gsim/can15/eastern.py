"""
:module:`openquake.hazardlib.gsim.nrcan15` implements
:class:`EasternCan15Mid`, :class:`EasterCnan15Low`,
:class:`EasternCan15Upp`
"""

import copy
import numpy as np

from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib.gsim.can15 import utils
from openquake.hazardlib.gsim.can15.western import get_sigma

from openquake.hazardlib.imt import PGA
from openquake.hazardlib.const import StdDev
from openquake.hazardlib.gsim.pezeshk_2011 import PezeshkEtAl2011
from openquake.hazardlib.gsim.boore_atkinson_2011 import Atkinson2008prime
from openquake.hazardlib.gsim.atkinson_boore_2006 import \
    AtkinsonBoore2006Modified2011
from openquake.hazardlib.gsim.silva_2002 import (
    SilvaEtAl2002DoubleCornerSaturation, SilvaEtAl2002SingleCornerSaturation)


class EasternCan15Mid(PezeshkEtAl2011):
    """
    Implements the hybrid GMPE used to compute hazard in the Eastern part of
    Canada.

    The GMPEs used are:

    - Pezeshk et al. (2011) - For this GMPE we scale the ground motion from
    hard rock to B/C using the correction proposed in Atkinson and Adams (2013)
    Table 2 page 994. As the distance metric used is Rrup we compute an
    equivalent Rrup distance from Repi using the equations in Appendix A (page
    31) of Atkinson (2012).

    - Atkinson (2008) as revised in Atkinson and Boore (2011). As the distance
    metric used is Rjb we compute an equivalent Rjb distance from Repi
    using the equations in Appendix A (page 31) of Atkinson (2012).

    - Atkinson and Boore (2006) as revised in Atkinson and Boore (2011). As
    the distance metric used is Rjb we compute an equivalent Rjb distance
    from Repi using the equations in Appendix A (page 31) of Atkinson (2012).

    - Silva et al. (2002) single corner and saturation.

    - Silva et al. (2002) double corner and saturation.
    """

    #: GMPE not tested against independent implementation so raise
    #: not verified warning
    non_verified = True

    #: Required site parameters
    REQUIRES_SITES_PARAMETERS = set(('vs30',))

    #: Required distance is only repi since rrup and rjb are obtained from repi
    REQUIRES_DISTANCES = set(('repi',))

    #: Required rupture parameters
    REQUIRES_RUPTURE_PARAMETERS = set(('rake', 'mag'))

    #: Shear-wave velocity for reference soil conditions in [m s-1]
    DEFINED_FOR_REFERENCE_VELOCITY = 760.

    #: Standard deviation types supported
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([StdDev.TOTAL])

    def apply_correction_to_BC(self, mean, imt, dists):
        """
        """
        if imt.period:
            cff = self.SITE_COEFFS[imt]
            tmp = cff['mf']
        elif imt in [PGA()]:
            tmp = -0.3+0.15*np.log10(dists.repi)
        else:
            raise ValueError('Unsupported IMT', str(imt))
        return mean + np.log(10**tmp)

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See documentation for method `GroundShakingIntensityModel` in
        :class:~`openquake.hazardlib.gsim.base.GSIM`
        """
        mean, stds = self._get_mean_and_stddevs(sites, rup, dists, imt,
                                                stddev_types)
        stddevs = [np.ones(len(dists.repi))*get_sigma(imt)]
        return mean, stddevs

    def _get_delta(self, stds, dists):
        """
        Computes the additional delta to be used for the computation of the
        upp and low models
        """
        delta = np.maximum((0.1-0.001*dists.repi), np.zeros_like(dists.repi))
        return delta

    def _get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        Returns only the mean values.

        See documentation for method `GroundShakingIntensityModel` in
        :class:~`openquake.hazardlib.gsim.base.GSIM`
        """
        # distances
        distsl = copy.copy(dists)
        distsl.rjb, distsl.rrup = \
            utils.get_equivalent_distances_east(rup.mag, dists.repi)
        #
        # Pezeshk et al. 2011 - Rrup
        mean1, stds1 = super().get_mean_and_stddevs(sites, rup, distsl, imt,
                                                    stddev_types)
        mean1 = self.apply_correction_to_BC(mean1, imt, distsl)
        #
        # Atkinson 2008 - Rjb
        gmpe = Atkinson2008prime()
        mean2, stds2 = gmpe.get_mean_and_stddevs(sites, rup, distsl, imt,
                                                 stddev_types)
        #
        # Silva et al. 2002 - Rjb
        gmpe = SilvaEtAl2002SingleCornerSaturation()
        mean4, stds4 = gmpe.get_mean_and_stddevs(sites, rup, distsl, imt,
                                                 stddev_types)
        mean4 = self.apply_correction_to_BC(mean4, imt, distsl)
        #
        # Silva et al. 2002 - Rjb
        gmpe = SilvaEtAl2002DoubleCornerSaturation()
        mean5, stds5 = gmpe.get_mean_and_stddevs(sites, rup, distsl, imt,
                                                 stddev_types)
        mean5 = self.apply_correction_to_BC(mean5, imt, distsl)
        #
        # distances
        distsl.rjb, distsl.rrup = \
            utils.get_equivalent_distances_east(rup.mag, dists.repi, ab06=True)
        #
        # Atkinson and Boore 2006 - Rrup
        gmpe = AtkinsonBoore2006Modified2011()
        mean3, stds3 = gmpe.get_mean_and_stddevs(sites, rup, distsl, imt,
                                                 stddev_types)
        # Computing adjusted mean and stds
        mean_adj = mean1*0.2 + mean2*0.2 + mean3*0.2 + mean4*0.2 + mean5*0.2

        # Note that in this case we do not apply a triangular smoothing on
        # distance as explained at page 996 of Atkinson and Adams (2013)
        # for the calculation of the standard deviation
        stds_adj = np.log(np.exp(stds1)*0.2 + np.exp(stds2)*0.2 +
                          np.exp(stds3)*0.2 + np.exp(stds4)*0.2 +
                          np.exp(stds5)*0.2)
        #
        return mean_adj, stds_adj

    SITE_COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT        mf
    0.05    -0.10
    0.10     0.03
    0.20     0.12
    0.33     0.14
    0.50     0.14
    1.00     0.11
    2.00     0.09
    5.00     0.06
    """)


class EasternCan15Low(EasternCan15Mid):

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See documentation for method `GroundShakingIntensityModel` in
        :class:~`openquake.hazardlib.gsim.base.GSIM`
        """
        # This is just used for testing purposes
        if len(stddev_types) == 0:
            stddev_types = [StdDev.TOTAL]
        mean, stds = self._get_mean_and_stddevs(sites, rup, dists, imt,
                                                stddev_types)
        stddevs = [np.ones(len(dists.repi))*get_sigma(imt)]
        delta = self._get_delta(stds, dists)
        mean = mean - stds - delta
        mean = np.squeeze(mean)
        return mean, stddevs


class EasternCan15Upp(EasternCan15Mid):

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See documentation for method `GroundShakingIntensityModel` in
        :class:~`openquake.hazardlib.gsim.base.GSIM`
        """
        # This is just used for testing purposes
        if len(stddev_types) == 0:
            stddev_types = [StdDev.TOTAL]
        mean, stds = self._get_mean_and_stddevs(sites, rup, dists, imt,
                                                stddev_types)
        stddevs = [np.ones(len(dists.repi))*get_sigma(imt)]
        delta = self._get_delta(stds, dists)
        mean = mean + stds + delta
        mean = np.squeeze(mean)
        return mean, stddevs
