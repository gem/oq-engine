#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CanadaSHM6 GMMs for Interface
"""
import numpy as np

from openquake.hazardlib.gsim.can20.inslab import (
    CanSHM6_InSlab_ZhaoEtAl2006SSlabCascadia55, COEFFS_SITE_FACTORS,
    extrapolation_factor, CoeffsTable_CanadaSHM6)
from openquake.hazardlib.gsim.can20.active_crust import (
    CanSHM6_ActiveCrust_BooreEtAl2014, CanadaSHM6_hardrock_site_factor)
from openquake.hazardlib.gsim.abrahamson_2015 import AbrahamsonEtAl2015SInter
from openquake.hazardlib.gsim.atkinson_macias_2009 import AtkinsonMacias2009
from openquake.hazardlib.gsim.ghofrani_atkinson_2014 import (
    GhofraniAtkinson2014Cascadia)
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib import const
from scipy.constants import g


class CanSHM6_Interface_AbrahamsonEtAl2015SInter(AbrahamsonEtAl2015SInter):
    """
    For CanadaSHM6 the Abrahramson et al., 2015 (BCHydro) Inteface GMM is used
    as is and is included here only for consistency in GMM naming.
    """


class CanSHM6_Interface_ZhaoEtAl2006SInterCascadia(
        CanSHM6_InSlab_ZhaoEtAl2006SSlabCascadia55):
    """
    Zhao et al., 2006 Interface with Cascadia adjustment at a fixed hypo depth
    of 30 km and with modifications to the site term as implemented for
    CanadaSHM6 (see also CanadaSHM6_InSlab_ZhaoEtAl2006SSlabCascadia).

    Reference:
    """

    REQUIRES_RUPTURE_PARAMETERS = set(('mag', 'rake'))
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE
    extrapolate_GMM = CanSHM6_Interface_AbrahamsonEtAl2015SInter()

    HYPO_DEPTH = 30.

    def __init__(self):
        super(CanSHM6_Interface_ZhaoEtAl2006SInterCascadia,
              self).__init__()

        self.COEFFS_SINTER = CoeffsTable_CanadaSHM6(self.COEFFS_SINTER,
                                                    self.MAX_SA, self.MIN_SA,
                                                    self.MAX_SA_EXTRAP,
                                                    self.MIN_SA_EXTRAP)

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.

        CanadaSHM6 edits: modified site amplification term
                          added extrapolation beyond MAX_SA and MIN_SA
                          hard-coded hypo depth of 30km
        """
        # Determine if extrapolation is necessary
        if imt.period < self.MIN_SA and imt.period >= self.MIN_SA_EXTRAP:
            target_imt = imt
            imt = SA(self.MIN_SA)
            extrapolate = True
        elif imt.period > self.MAX_SA and imt.period <= self.MAX_SA_EXTRAP:
            target_imt = imt
            imt = SA(self.MAX_SA)
            extrapolate = True
        else:
            extrapolate = False

        # extracting dictionary of coefficients specific to required
        # intensity measure type.
        C = self.COEFFS_ASC[imt]
        C_SINTER = self.COEFFS_SINTER[imt]
        C_SF = COEFFS_SITE_FACTORS[imt]

        # mean value as given by equation 1, p. 901, without considering the
        # faulting style and intraslab terms (that is FR, SS, SSL = 0) and the
        # inter and intra event terms, plus the magnitude-squared term
        # correction factor (equation 5 p. 909)
        mean = self._compute_magnitude_term(C, rup.mag) +\
            self._compute_distance_term(C, rup.mag, dists.rrup) +\
            self._compute_focal_depth_term(C, self.HYPO_DEPTH) +\
            self._compute_site_class_term_CanadaSHM6(C, sites.vs30, imt) + \
            self._compute_magnitude_squared_term(P=0.0, M=6.3,
                                                 Q=C_SINTER['QI'],
                                                 W=C_SINTER['WI'],
                                                 mag=rup.mag) +\
            C_SINTER['SI']

        # multiply by site factor to "convert" Japan values to Cascadia values
        # then convert from cm/s**2 to g
        mean = np.log((np.exp(mean) * C_SF["MF"]) * 1e-2 / g)

        stddevs = self._get_stddevs(C['sigma'], C_SINTER['tauI'], stddev_types,
                                    num_sites=len(sites.vs30))

        # add extrapolation factor if outside SA range (0.07 - 9.09)
        if extrapolate:
            mean += extrapolation_factor(self.extrapolate_GMM, rup, sites,
                                         dists, imt, target_imt)

        return mean, stddevs

    # Coefs taken from ZhaoEtAl2006SInter
    COEFFS_SINTER = CoeffsTable(sa_damping=5, table="""\
        IMT    SI     QI      WI      tauI
        pga    0.000  0.0     0.0     0.308
        0.05   0.000  0.0     0.0     0.343
        0.10   0.000  0.0     0.0     0.403
        0.15   0.000 -0.0138  0.0286  0.367
        0.20   0.000 -0.0256  0.0352  0.328
        0.25   0.000 -0.0348  0.0403  0.289
        0.30   0.000 -0.0423  0.0445  0.280
        0.40  -0.041 -0.0541  0.0511  0.271
        0.50  -0.053 -0.0632  0.0562  0.277
        0.60  -0.103 -0.0707  0.0604  0.296
        0.70  -0.146 -0.0771  0.0639  0.313
        0.80  -0.164 -0.0825  0.0670  0.329
        0.90  -0.206 -0.0874  0.0697  0.324
        1.00  -0.239 -0.0917  0.0721  0.328
        1.25  -0.256 -0.1009  0.0772  0.339
        1.50  -0.306 -0.1083  0.0814  0.352
        2.00  -0.321 -0.1202  0.0880  0.360
        2.50  -0.337 -0.1293  0.0931  0.356
        3.00  -0.331 -0.1368  0.0972  0.338
        4.00  -0.390 -0.1486  0.1038  0.307
        5.00  -0.498 -0.1578  0.1090  0.272
        """)


class CanadaSHM6_Interface_AtkinsonMacias2009(AtkinsonMacias2009):
    """
    Atkinson and Macias, 2009 Interface GMM with an added site term following
    a modified version of BSSA14 (i.e., SS14) as implemented for CanadaSHM6.

    Reference:
    """

    REQUIRES_SITES_PARAMETERS = set(('vs30',))
    BSSA14 = CanSHM6_ActiveCrust_BooreEtAl2014()

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.

        CanadaSHM6 edits: Added site term (from CanadaSHM6 implementation of
                                           BSSA14)
        """

        C = self.COEFFS[imt]
        mean = self._get_mean_760(rup, dists, imt)  # AM09 is for Vs30 = 760m/s
        mean += self.site_term(rup, dists, sites, imt)
        stddevs = self._get_stddevs(C, len(dists.rrup), stddev_types)

        return mean, stddevs

    def _get_mean_760(self, rup, dists, imt):

        """
        See get_mean_and_stddevs in AtkinsonMacias2009
        """
        C = self.COEFFS[imt]
        imean = (self._get_magnitude_term(C, rup.mag) +
                 self._get_distance_term(C, dists.rrup, rup.mag))
        # Convert mean from cm/s and cm/s/s and from common logarithm to
        # natural logarithm
        mean = np.log((10.0 ** (imean - 2.0)) / g)

        return mean

    def site_term(self, rup, dists, sites, imt):
        """
        Site term for AM09 using the CanadaSHM6 implementation of BSSA14
        (see CanadaSHM6_ActiveCrust_BooreEtAl2014)
        """
        # get PGA for non-linear term in BSSA14
        pga760 = self._get_mean_760(rup, dists, PGA())

        C = self.BSSA14.COEFFS[imt]
        F = self.BSSA14._get_site_scaling(C, np.exp(pga760), sites, imt, [])

        return F


class CanadaSHM6_Interface_GhofraniAtkinson2014Cascadia(
                                                GhofraniAtkinson2014Cascadia):
    """
    Ghofrani and Atkinson 2014 Interface GMM with Cascadia adjustment and
    modifications to the site term as implemented for CanadaSHM6.

    Reference:
    """
    # Parameters used to extrapolate to 0.05s <= T <= 10s
    MAX_SA = 9.09
    MIN_SA = 0.07
    MAX_SA_EXTRAP = 10.0
    MIN_SA_EXTRAP = 0.05
    extrapolate_GMM = CanSHM6_Interface_AbrahamsonEtAl2015SInter()

    REQUIRES_SITES_PARAMETERS = set(('vs30', 'backarc'))

    def __init__(self):

        super(CanadaSHM6_Interface_GhofraniAtkinson2014Cascadia,
              self).__init__()

        # Need to use new CoeffsTable to be able to handle extrapolation
        self.COEFFS = CoeffsTable_CanadaSHM6(self.COEFFS, self.MAX_SA,
                                             self.MIN_SA, self.MAX_SA_EXTRAP,
                                             self.MIN_SA_EXTRAP)

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.

        CanadaSHM6 edits: added extrapolation beyond MAX_SA and MIN_SA
                          modified site amplification term for Vs30 >= 1100 m/s

        """
        if imt.period < self.MIN_SA and imt.period >= self.MIN_SA_EXTRAP:
            target_imt = imt
            imt = SA(self.MIN_SA)
            extrapolate = True
        elif imt.period > self.MAX_SA and imt.period <= self.MAX_SA_EXTRAP:
            target_imt = imt
            imt = SA(self.MAX_SA)
            extrapolate = True
        else:
            extrapolate = False

        C = self.COEFFS[imt]

        imean = (self._get_magnitude_term(C, rup.mag) +
                 self._get_distance_term(C, dists.rrup, sites.backarc) +
                 self._get_site_term_CanadaSHM6(C, sites.vs30, imt) +
                 self._get_scaling_term(C, dists.rrup))
        # Convert mean from cm/s and cm/s/s and from common logarithm to
        # natural logarithm
        if imt.name in "SA PGA":
            mean = np.log((10.0 ** (imean - 2.0)) / g)
        else:
            mean = np.log((10.0 ** (imean)))

        stddevs = self._get_stddevs(C, len(dists.rrup), stddev_types)

        # add extrapolation factor if outside SA range (0.07 - 9.09)
        if extrapolate:
            mean += extrapolation_factor(self.extrapolate_GMM, rup, sites,
                                         dists, imt, target_imt)

        return mean, stddevs

    def _get_site_term_CanadaSHM6(self, C, vs30, imt):
        """
        Returns the linear site scaling term following GA14 for Vs30 < 1100 m/s
        and the CanadaSHM6 hard-rock approach for Vs30 >= 1100 m/s.
        """
        # Native site factor for GA14
        GA14_vs = self._get_site_term(C, vs30)

        # Need log site factors at Vs30 = 1100 and 2000 to calculate
        # CanadaSHM6 hard rock site factors
        GA14_1100 = np.log(10**self._get_site_term(C, 1100.))
        GA14_2000 = np.log(10**self._get_site_term(C, 2000.))

        # CanadaSHM6 hard rock site factor
        F = CanadaSHM6_hardrock_site_factor(GA14_1100, GA14_2000,
                                            vs30[vs30 >= 1100], imt)

        # for Vs30 > 1100 set to CanadaSHM6 factor
        GA14_vs[vs30 >= 1100] = np.log10(np.exp(F))

        return GA14_vs
