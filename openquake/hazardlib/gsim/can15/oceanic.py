"""
:module:`openquake.hazardlib.gsim.nrcan15` implements
:class:`BooreAtkinson2011NRCan15Mid`, :class:`BooreAtkinson2011NRCan15Low`,
:class:`BooreAtkinson2011NRCan15Low`
"""

import scipy
import numpy as np

from openquake.hazardlib.imt import PGA, PGV, SA
from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib.gsim.boore_atkinson_2011 import BooreAtkinson2011
from openquake.hazardlib.gsim.zhao_2006 import (ZhaoEtAl2006SSlab,
                                                ZhaoEtAl2006SInter)
from openquake.hazardlib.gsim.atkinson_macias_2009 import AtkinsonMacias2009
from openquake.hazardlib.gsim.silva_2002 import SilvaEtAl2002MwNSHMP2008
from openquake.hazardlib.gsim.abrahamson_2015 import AbrahamsonEtAl2015SInter
from openquake.hazardlib.gsim.pezeshk_2011 import PezeshkEtAl2011
from openquake.hazardlib.gsim.boore_atkinson_2011 import Atkinson2008prime
from openquake.hazardlib.gsim.ghofrani_atkinson_2014 import (
    GhofraniAtkinson2014Cascadia, GhofraniAtkinson2014)
from openquake.hazardlib.gsim.atkinson_boore_2006 import \
    AtkinsonBoore2006Modified2011


def get_rup_len_west(mag):
    """ Rupture length from WC1994 - See Atkinson (2012) Appendix A"""
    return 10**(-2.44+0.59*mag)


def get_rup_wid_west(mag):
    """ Rupture width from WC1994 - See Atkinson (2012) Appendix A"""
    return 10**(-1.01+0.32*mag)


def get_rup_len_east(mag):
    """ Rupture length from WC1994 - See Atkinson (2012) Appendix A"""
    return get_rup_len_west(mag)*0.6


def get_rup_wid_east(mag):
    """ Rupture width from WC1994 - See Atkinson (2012) Appendix A"""
    return get_rup_wid_west(mag)*0.6


def _get_equivalent_distances_east(wid, lng, mag, repi, focal_depth=10.,
                                   ab06=False):
    """
    Computes equivalent values of Joyner-Boore and closest distance to the
    rupture given epoicentral distance. The procedure is described in
    Atkinson (2012) - Appendix A (page 32).

    :param float wid:
        Width of rectangular rupture
    :param float lng:
        Length of rectangular rupture
    :param float mag:
        Magnitude
    :param repi:
        A :class:`numpy.ndarray` instance containing repi values
    :param float focal_depth:
        Focal depth
    :param boolean ab06:
        When true a minimum ztor value is set to force near-source saturation
    """
    dtop = focal_depth - 0.5*wid
    # this computes a minimum ztor value - used for AB2006
    if ab06:
        ztor_ab06 = 21-2.5*mag
        dtop = np.max([ztor_ab06, dtop])
    ztor = max(0, dtop)
    # find the average distance to the fault projection
    dsurf = np.max([repi-0.3*lng, 0.1*np.ones_like(repi)], axis=0)
    # rrup
    rrup = (dsurf**2+ztor**2)**0.5
    # return rjb and rrup
    return dsurf, rrup


def get_equivalent_distances_east(mag, repi, focal_depth=10., ab06=False):
    """ """
    wid = get_rup_wid_east(mag)
    lng = get_rup_len_east(mag)
    rjb, rrup = _get_equivalent_distances_east(wid, lng, mag, repi,
                                               focal_depth, ab06)
    return rjb, rrup


def get_equivalent_distances_west(mag, repi, focal_depth=10.):
    """ """
    wid = get_rup_wid_west(mag)
    lng = get_rup_len_west(mag)
    rjb, rrup = _get_equivalent_distances_east(wid, lng, mag, repi,
                                               focal_depth, ab06=False)
    return rjb, rrup


def get_equivalent_distance_inslab(mag, repi, hslab):
    """
    :param float mag:
        Magnitude
    :param repi:
        A :class:`numpy.ndarray` instance containing repi values
    :param float hslab:
        Depth of the slab
    """
    area = 10**(-3.225+0.89*mag)
    radius = (area / scipy.constants.pi)**0.5
    rjb = np.max([repi-radius, np.zeros_like(repi)], axis=0)
    rrup = (rjb**2+hslab**2)**0.5
    return rjb, rrup


# .............................................................................
# Stable model

class StableNRCan15Mid(PezeshkEtAl2011):
    """
    Implements the hybrid GMPE used to compute hazard in the Eastern part of
    Canada.

    The GMPEs used are:

    - Pezeshk et al. (2011) - For this GMPE we scale the ground motion from
    hard rock to B/C using the correction proposed in Atkinson and Adams (2013)
    Table 2 page 994. As the distance metric used is Rrup we compute and
    equivalent Rrup distance from Repi using the equations in Appendix A (page
    31) of Atkinson (2012).

    - Atkinson (2008) as revised in Atkinson and Boore (2011). As the distance
    metric used is Rjb we compute and equivalent Rjb distance from Repi
    using the equations in Appendix A (page 31) of Atkinson (2012).

    - Atkinson and Boore (2006) as revised in Atkinson and Boore (2011). As
    the distance metric used is Rjb we compute and equivalent Rjb distance
    from Repi using the equations in Appendix A (page 31) of Atkinson (2012).

    - Silva et al. (2002) single corner and saturation.

    - Silva et al. (2002) double corner and saturation.
    """

    # Required site parameters
    REQUIRES_SITES_PARAMETERS = set(('vs30',))

    # Required distance is only repi since rrup and rjb are obtained from repi
    REQUIRES_DISTANCES = set(('repi',))

    def apply_correction_to_BC(self, mean, imt, dists):
        """

        """
        if imt in self.SITE_COEFFS.sa_coeffs:
            cff = self.SITE_COEFFS[imt]
            tmp = cff['mf']
        elif imt in [PGA()]:
            tmp = -0.3+0.15*np.log10(dists.repi)
        else:
            raise ValueError('Unsupported IMT')
        return mean + np.log(10**tmp)

    # TODO Sigma model!!
    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        # distances
        rjb, rrup = get_equivalent_distances_east(rup.mag, dists.repi)
        dists.rrup = rrup
        dists.rjb = rjb
        #
        # Pezeshk et al. 2011 - Rrup
        mean1, stds1 = super().get_mean_and_stddevs(sites, rup, dists, imt,
                                                    stddev_types)
        mean1 = self.apply_correction_to_BC(mean1, imt, dists)
        #
        # Atkinson 2008 - Rjb
        gmpe = Atkinson2008prime()
        mean2, stds2 = gmpe.get_mean_and_stddevs(sites, rup, dists, imt,
                                                 stddev_types)
        #
        # Silva et al. 2002 - Rjb
        gmpe = SilvaEtAl2002SingleCornerSaturation()
        mean4, stds4 = gmpe.get_mean_and_stddevs(sites, rup, dists, imt,
                                                 stddev_types)
        mean4 = self.apply_correction_to_BC(mean4, imt, dists)
        #
        # Silva et al. 2002 - Rjb
        gmpe = SilvaEtAl2002DoubleCornerSaturation()
        mean5, stds5 = gmpe.get_mean_and_stddevs(sites, rup, dists, imt,
                                                 stddev_types)
        mean5 = self.apply_correction_to_BC(mean5, imt, dists)
        #
        # distances
        rjb, rrup = get_equivalent_distances_east(rup.mag, dists.repi,
                                                  ab06=True)
        dists.rrup = rrup
        dists.rjb = rjb
        #
        # Atkinson and Boore 2006 - Rrup
        gmpe = AtkinsonBoore2006Modified2011()
        mean3, stds3 = gmpe.get_mean_and_stddevs(sites, rup, dists, imt,
                                                 stddev_types)
        # Computing adjusted mean and stds
        mean_adj = np.log(np.exp(mean1)*0.2 + np.exp(mean2)*0.2 +
                          np.exp(mean3)*0.2 + np.exp(mean4)*0.2 +
                          np.exp(mean5)*0.2)
        # Note that in this case we do not apply a triangular smoothing on
        # distance as explained at page 996 for the calculation of the
        # standard deviation
        stds_adj = np.log(np.exp(stds1)*0.2 + np.exp(stds2)*0.2 +
                          np.exp(stds3)*0.2 + np.exp(stds4)*0.2 +
                          np.exp(stds5)*0.2)
        #
        return mean_adj, stds_adj

    SITE_COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT        mf
    pgv      0.09
    0.05    -0.10
    0.10     0.03
    0.20     0.12
    0.33     0.14
    0.50     0.14
    1.00     0.11
    2.00     0.09
    5.00     0.06
    """)

# .............................................................................
# Interface model


class SInterNRCan15Mid(ZhaoEtAl2006SInter):
    """
    """

    # TODO Sigma model!!
    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
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


# .............................................................................
# InSlab model
class ZhaoEtAl2006SSlabNRCan15Mid(ZhaoEtAl2006SSlab):
    """
    Implements the Zhao et al. (2006) for inslab earthquakes with
    modifications requested for the calculation of hazard for the fifth
    generation of Canada hazard maps, released in 2015. See Atkinson and Adams
    (2013).
    """

    # Required distance is only repi since rrup and rjb are obtained from repi
    REQUIRES_DISTANCES = set(('repi',))

    # TODO Sigma model!!
    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """ """
        # get original values
        hslab = 50  # See info in GMPEt_Inslab_med.dat
        rjb, rrup = get_equivalent_distance_inslab(rup.mag, dists.repi, hslab)
        dists.rjb = rjb
        dists.rrup = rrup
        mean, stddevs = super().get_mean_and_stddevs(sites, rup, dists, imt,
                                                     stddev_types)
        cff = self.SITE_COEFFS[imt]
        #cff = self.SITE_CO[imt]
        mean_adj = np.log(np.exp(mean) * 10**cff['mf'])
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

    # These are the coefficients included in the GMPEt_Inslab_med.dat file
    SITE_CO = CoeffsTable(sa_damping=5, table="""\
    IMT        mf
    pga     0.004
    0.005  -0.301
    0.100  -0.357
    0.200  -0.357
    0.303  -0.222
    0.500  -0.091
    1.000   0.004
    2.000   0.017
    5.000   0.179
    10.00   0.000
    """)


class ZhaoEtAl2006SSlabNRCan15Low(ZhaoEtAl2006SSlabNRCan15Mid):

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """ """
        # get original values
        hslab = 50  # See info in GMPEt_Inslab_med.dat
        rjb, rrup = get_equivalent_distance_inslab(rup.mag, dists.repi, hslab)
        dists.rjb = rjb
        dists.rrup = rrup
        mean, stddevs = super().get_mean_and_stddevs(sites, rup, dists, imt,
                                                     stddev_types)
        # adjust mean values using the reccomended delta (see Atkinson and
        # Adams, 2013; page 992)
        delta = np.log(10.**(0.15))
        mean_adj = mean - delta
        return mean_adj, stddevs


class ZhaoEtAl2006SSlabNRCan15Upp(ZhaoEtAl2006SSlabNRCan15Mid):

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """ """
        # get original values
        hslab = 50  # See info in GMPEt_Inslab_med.dat
        rjb, rrup = get_equivalent_distance_inslab(rup.mag, dists.repi, hslab)
        dists.rjb = rjb
        dists.rrup = rrup
        mean, stddevs = super().get_mean_and_stddevs(sites, rup, dists, imt,
                                                     stddev_types)
        # adjust mean values using the reccomended delta (see Atkinson and
        # Adams, 2013; page 992)
        delta = np.log(10.**(0.15))
        mean_adj = mean + delta
        return mean_adj, stddevs


# .............................................................................
# W Crust model

class BooreAtkinson2011NRCan15Mid(BooreAtkinson2011):
    """
    Implements the Boore and Atkinson (2008) with adjustments proposed by
    Boore and Atkinson (2011) and the modifications introduced for the
    calculation of hazard for the fifth generation of Canada hazard maps,
    released in 2015.
    """

    # TODO Sigma model!!
    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """ """
        # get original values
        mean, stddevs = super().get_mean_and_stddevs(sites, rup, dists, imt,
                                                     stddev_types)
        return mean, stddevs


class BooreAtkinson2011NRCan15Low(BooreAtkinson2011NRCan15Mid):

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """ """
        # get original values
        mean, stddevs = super().get_mean_and_stddevs(sites, rup, dists, imt,
                                                     stddev_types)
        # adjust mean values using the reccomended delta (see Atkinson and
        # Adams, 2013)
        tmp = 0.1+0.0007*dists.rjb
        tmp = np.vstack((tmp, np.ones_like(tmp)*0.3))
        delta = np.log(10.**(np.amin(tmp, axis=0)))
        mean_adj = mean - delta
        return mean_adj, stddevs


class BooreAtkinson2011NRCan15Upp(BooreAtkinson2011NRCan15Mid):

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """ """
        # get original values
        mean, stddevs = super().get_mean_and_stddevs(sites, rup, dists, imt,
                                                     stddev_types)
        # adjust mean values using the reccomended delta (see Atkinson and
        # Adams, 2013)
        tmp = 0.1+0.0007*dists.rjb
        tmp = np.vstack((tmp, np.ones_like(tmp)*0.3))
        print('tmp', tmp)
        print('min', np.amin(tmp, axis=0))
        delta = np.log(10.**(np.amin(tmp, axis=0)))
        mean_adj = mean + delta
        return mean_adj, stddevs

# .............................................................................
# OffShore model


class OffShoreNRCan15Mid(BooreAtkinson2011NRCan15Mid):

    # TODO Sigma model!!
    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        # get original values
        rup.mag -= 0.5
        mean, stddevs = super().get_mean_and_stddevs(sites, rup, dists, imt,
                                                     stddev_types)
        return mean, stddevs


# .............................................................................
# Silva et al. (2002)


class SilvaEtAl2002DoubleCornerSaturation(SilvaEtAl2002MwNSHMP2008):
    """
    This implements the Silva et al. (2002) GMPE for the double corner model
    with saturation.
    """

    # TODO check clip mean

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        assert all(stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
                   for stddev_type in stddev_types)

        C = self.COEFFS[imt]
        mag = self._convert_magnitude(rup.mag)
        mean = (
            C['c1'] + C['c2'] * mag + C['c10'] * (mag - 6) ** 2 +
            (C['c6'] + C['c7'] * mag) * np.log(dists.rjb + np.exp(C['c4']))
        )
        stddevs = self._compute_stddevs(C, dists.rjb.size, stddev_types)
        return mean, stddevs


    COEFFS = CoeffsTable(sa_damping=5, table="""\
        IMT      c1           c2           c4           c5         c6        c7           c8         c10      sigma_par    sigma
    +10.0000000  -16.16329    +1.9653500   +2.3000000   +0.0000000 -1.71374  +0.1054700   +0.0000000 -.32832  +0.4199000   +1.3429000
    +5.0000000   -12.17910    +1.6245100   +2.5000000   +0.0000000 -1.88291  +0.1156400   +0.0000000 -.30150  +0.4529000   +1.2228000
    +3.0003000   -9.24347     +1.3620100   +2.6000000   +0.0000000 -2.05193  +0.1295400   +0.0000000 -.24133  +0.4887000   +1.0871000
    +2.0000000   -6.86049     +1.1554800   +2.7000000   +0.0000000 -2.23472  +0.1461000   +0.0000000 -.19315  +0.5217000   +1.0095000
    +1.6000000   -5.75016     +1.0506100   +2.7000000   +0.0000000 -2.32003  +0.1554000   +0.0000000 -.17317  +0.5388000   +0.9450000
    +1.0000000   -3.10841     +0.7956100   +2.8000000   +0.0000000 -2.58562  +0.1819500   +0.0000000 -.15020  +0.5697000   +0.8739000
    +0.7500188   -1.68010     +0.6697100   +2.8000000   +0.0000000 -2.68318  +0.1926100   +0.0000000 -.14513  +0.5844000   +0.8815000
    +0.5000000   +0.1710400   +0.4866300   +2.8000000   +0.0000000 -2.81997  +0.2077300   +0.0000000 -.13719  +0.6016000   +0.8426000
    +0.4000000   +1.1769500   +0.3907800   +2.8000000   +0.0000000 -2.87626  +0.2135200   +0.0000000 -.12940  +0.6110000   +0.8320000
    +0.3000030   +2.2762600   +0.2703100   +2.8000000   +0.0000000 -2.95623  +0.2219300   +0.0000000 -.11697  +0.6231000   +0.8358000
    +0.2399981   +3.0470500   +0.1947100   +2.8000000   +0.0000000 -3.00223  +0.2263900   +0.0000000 -.10675  +0.6326000   +0.8272000
    +0.2000000   +3.6156800   +0.1431100   +2.8000000   +0.0000000 -3.03239  +0.2290000   +0.0000000 -.09861  +0.6412000   +0.8260000
    +0.1600000   +4.1928100   +0.0844100   +2.8000000   +0.0000000 -3.07579  +0.2330000   +0.0000000 -.08991  +0.6535000   +0.8290000
    +0.1499993   +4.3427700   +0.0691100   +2.8000000   +0.0000000 -3.08805  +0.2340900   +0.0000000 -.08764  +0.6587000   +0.8339000
    +0.1200005   +4.8166300   +0.0279300   +2.8000000   +0.0000000 -3.12224  +0.2368600   +0.0000000 -.08119  +0.6717000   +0.8485000
    +0.1000000   +5.1370600   -0.00173     +2.8000000   +0.0000000 -3.15185  +0.2392900   +0.0000000 -.07703  +0.6837000   +0.8468000
    +0.0800000   +5.9494200   -0.06741     +2.9000000   +0.0000000 -3.27328  +0.2482200   +0.0000000 -.07318  +0.6923000   +0.8476000
    +0.0700001   +6.1070800   -0.08387     +2.9000000   +0.0000000 -3.29509  +0.2500000   +0.0000000 -.07142  +0.6982000   +0.8521000
    +0.0599999   +6.2638400   -0.10044     +2.9000000   +0.0000000 -3.31911  +0.2519200   +0.0000000 -.06982  +0.7058000   +0.8602000
    +0.0550001   +6.3423800   -0.10886     +2.9000000   +0.0000000 -3.33222  +0.2529500   +0.0000000 -.06908  +0.7106000   +0.8604000
    +0.0500000   +6.4242300   -0.11726     +2.9000000   +0.0000000 -3.34604  +0.2540100   +0.0000000 -.06838  +0.7165000   +0.8675000
    +0.0400000   +6.6120400   -0.13370     +2.9000000   +0.0000000 -3.37593  +0.2561300   +0.0000000 -.06711  +0.7339000   +0.8795000
    +0.0322581   +7.3373600   -0.18563     +3.0000000   +0.0000000 -3.49824  +0.2645600   +0.0000000 -.06625  +0.7462000   +0.8869000
    +0.0250000   +7.5114500   -0.19862     +3.0000000   +0.0000000 -3.52888  +0.2665200   +0.0000000 -.06568  +0.7534000   +0.8902000
    +0.0200000   +7.5564800   -0.20898     +3.0000000   +0.0000000 -3.55306  +0.2685300   +0.0000000 -.06551  +0.7561000   +0.8939000
    +0.0100000   +6.1221300   -0.16489     +2.9000000   +0.0000000 -3.43941  +0.2660100   +0.0000000 -.06925  +0.6994000   +0.8468000
    pga          +5.9119600   -0.15727     +2.9000000   +0.0000000 -3.42401  +0.2656400   +0.0000000 -.07004  +0.6912000   +0.8400000
    """)

class SilvaEtAl2002SingleCornerSaturation(SilvaEtAl2002DoubleCornerSaturation):
    """
    This implements the Silva et al. (2002) GMPE for the single corner model
    with saturation.
    """
    COEFFS = CoeffsTable(sa_damping=5, table="""\
        IMT      c1           c2           c4           c5         c6        c7           c8         c10      sigma_par    sigma
    +10.0000000  -17.69763    +2.3387700   +2.3000000   +0.0000000 -1.75359  +0.1107100   +0.0000000 -.28005  +0.4204000   +1.3431000
    +5.0000000   -13.69697    +2.0348800   +2.5000000   +0.0000000 -1.91969  +0.1205200   +0.0000000 -.35463  +0.4597000   +1.2253000
    +3.0003000   -10.33313    +1.7175500   +2.6000000   +0.0000000 -2.08560  +0.1340100   +0.0000000 -.36316  +0.4981000   +1.0914000
    +2.0000000   -7.42051     +1.4194600   +2.7000000   +0.0000000 -2.26433  +0.1498400   +0.0000000 -.33999  +0.5309000   +1.0142000
    +1.6000000   -6.03692     +1.2582100   +2.7000000   +0.0000000 -2.33925  +0.1576500   +0.0000000 -.31816  +0.5472000   +0.9498000
    +1.0000000   -2.89906     +0.8811600   +2.8000000   +0.0000000 -2.58296  +0.1809800   +0.0000000 -.25757  +0.5767000   +0.8785000
    +0.7500188   -1.22930     +0.6851800   +2.8000000   +0.0000000 -2.68016  +0.1912700   +0.0000000 -.21501  +0.5914000   +0.8861000
    +0.5000000   +0.6953900   +0.4525400   +2.8000000   +0.0000000 -2.81800  +0.2061300   +0.0000000 -.16423  +0.6097000   +0.8484000
    +0.4000000   +1.6422800   +0.3475100   +2.8000000   +0.0000000 -2.87774  +0.2121500   +0.0000000 -.13838  +0.6199000   +0.8386000
    +0.3000030   +2.6068900   +0.2316500   +2.8000000   +0.0000000 -2.96321  +0.2211200   +0.0000000 -.11352  +0.6325000   +0.8428000
    +0.2399981   +3.2531900   +0.1661600   +2.8000000   +0.0000000 -3.01272  +0.2258900   +0.0000000 -.09854  +0.6423000   +0.8346000
    +0.2000000   +3.7195300   +0.1249000   +2.8000000   +0.0000000 -3.04591  +0.2287700   +0.0000000 -.08886  +0.6511000   +0.8338000
    +0.1600000   +4.1841600   +0.0787500   +2.8000000   +0.0000000 -3.09159  +0.2329700   +0.0000000 -.07992  +0.6633000   +0.8368000
    +0.1499993   +4.3041700   +0.0669500   +2.8000000   +0.0000000 -3.10445  +0.2341100   +0.0000000 -.07779  +0.6685000   +0.8417000
    +0.1200005   +5.1732000   +0.0018800   +2.9000000   +0.0000000 -3.22475  +0.2428600   +0.0000000 -.07200  +0.6814000   +0.8562000
    +0.1000000   +5.4378200   -0.02059     +2.9000000   +0.0000000 -3.25499  +0.2452700   +0.0000000 -.06853  +0.6933000   +0.8546000
    +0.0800000   +5.7063100   -0.04389     +2.9000000   +0.0000000 -3.29005  +0.2479900   +0.0000000 -.06548  +0.7017000   +0.8553000
    +0.0700001   +5.8347700   -0.05663     +2.9000000   +0.0000000 -3.31101  +0.2496500   +0.0000000 -.06416  +0.7077000   +0.8599000
    +0.0599999   +5.9639700   -0.06970     +2.9000000   +0.0000000 -3.33411  +0.2514500   +0.0000000 -.06300  +0.7152000   +0.8680000
    +0.0550001   +6.5676100   -0.11492     +3.0000000   +0.0000000 -3.44099  +0.2590400   +0.0000000 -.06249  +0.7200000   +0.8682000
    +0.0500000   +6.6393700   -0.12193     +3.0000000   +0.0000000 -3.45478  +0.2600800   +0.0000000 -.06201  +0.7259000   +0.8753000
    +0.0400000   +6.8101200   -0.13594     +3.0000000   +0.0000000 -3.48499  +0.2622000   +0.0000000 -.06115  +0.7429000   +0.8870000
    +0.0322581   +6.9787800   -0.14713     +3.0000000   +0.0000000 -3.51228  +0.2639200   +0.0000000 -.06051  +0.7550000   +0.8943000
    +0.0250000   +7.1408700   -0.15876     +3.0000000   +0.0000000 -3.54274  +0.2658900   +0.0000000 -.06019  +0.7619000   +0.8974000
    +0.0200000   +7.1744500   -0.16806     +3.0000000   +0.0000000 -3.56511  +0.2678600   +0.0000000 -.06041  +0.7643000   +0.9008000
    +0.0100000   +5.7388500   -0.12424     +2.9000000   +0.0000000 -3.43887  +0.2651000   +0.0000000 -.06699  +0.7079000   +0.8538000
    pga          +5.5345900   -0.11691     +2.9000000   +0.0000000 -3.42173  +0.2646100   +0.0000000 -.06810  +0.6998000   +0.8471000
    """)
