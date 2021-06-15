#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CanadaSHM6 GMMs for InSlab

"""
import numpy as np

from openquake.hazardlib.gsim.garcia_2005 import GarciaEtAl2005SSlab
from openquake.hazardlib.gsim.zhao_2006 import ZhaoEtAl2006SSlabCascadia
from openquake.hazardlib.gsim.abrahamson_2015 import AbrahamsonEtAl2015SSlab
from openquake.hazardlib.gsim.atkinson_boore_2003 import (
    AtkinsonBoore2003SSlabCascadia)
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib.const import StdDev
from openquake.hazardlib.gsim.base import (CoeffsTable, SitesContext,
                                           DistancesContext)
from openquake.hazardlib.gsim.boore_2014 import BooreEtAl2014
from scipy.constants import g


class CanSHM6_InSlab_AbrahamsonEtAl2015SSlab55(AbrahamsonEtAl2015SSlab):
    """
    Abrahramson et al., 2015 (BCHydro) InSlab GMM with a fixed hypo depth of
    55 km
    """
    HYPO_DEPTH = 55.

    def _compute_focal_depth_term(self, C, rup):
        """
        Computes the hypocentral depth scaling term - as indicated by
        equation (3)

        CanadaSHM6 edits: hard-coded hypo depth
        """
        return C['theta11'] * (self.HYPO_DEPTH - 60.)


class CanSHM6_InSlab_AbrahamsonEtAl2015SSlab30(
        CanSHM6_InSlab_AbrahamsonEtAl2015SSlab55):
    """
    Variant of CanadaSHM6_InSlab_AbrahamsonEtAl2015SSlab55 with a hypo depth
    of 30 km.
    """
    HYPO_DEPTH = 30.


class CanSHM6_InSlab_ZhaoEtAl2006SSlabCascadia55(ZhaoEtAl2006SSlabCascadia):
    """
    Zhao et al., 2006 InSlab with Cascadia adjustment, at a fixed hypo depth of
    55 km and with modifications to the site term as implemented for
    CanadaSHM6.
    """

    # Parameters used to extrapolate to 0.05s <= T <= 10s
    MAX_SA = 5.0
    MIN_SA = 0.05
    MAX_SA_EXTRAP = 10.0
    MIN_SA_EXTRAP = 0.05
    extrapolate_GMM = CanSHM6_InSlab_AbrahamsonEtAl2015SSlab55()

    REQUIRES_SITES_PARAMETERS = set(('vs30', 'backarc'))

    HYPO_DEPTH = 55.

    def __init__(self):
        super(CanSHM6_InSlab_ZhaoEtAl2006SSlabCascadia55,
              self).__init__()

        self.COEFFS_SSLAB = CoeffsTable_CanadaSHM6(self.COEFFS_SSLAB,
                                                   self.MAX_SA, self.MIN_SA,
                                                   self.MAX_SA_EXTRAP,
                                                   self.MIN_SA_EXTRAP)
        self.COEFFS_ASC = CoeffsTable_CanadaSHM6(self.COEFFS_ASC,
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
        C_SSLAB = self.COEFFS_SSLAB[imt]
        C_SF = COEFFS_SITE_FACTORS[imt]
        # to avoid singularity at 0.0 (in the calculation of the
        # slab correction term), replace 0 values with 0.1
        d = dists.rrup
        d[d == 0.0] = 0.1

        # mean value as given by equation 1, p. 901, without considering the
        # faulting style and intraslab terms (that is FR, SS, SSL = 0) and the
        # inter and intra event terms, plus the magnitude-squared term
        # correction factor (equation 5 p. 909)
        mean = self._compute_magnitude_term(C, rup.mag) +\
            self._compute_distance_term(C, rup.mag, d) +\
            self._compute_focal_depth_term(C, self.HYPO_DEPTH) +\
            self._compute_site_class_term_CanadaSHM6(C, sites.vs30, imt) +\
            self._compute_magnitude_squared_term(P=C_SSLAB['PS'], M=6.5,
                                                 Q=C_SSLAB['QS'],
                                                 W=C_SSLAB['WS'],
                                                 mag=rup.mag) +\
            C_SSLAB['SS'] + self._compute_slab_correction_term(C_SSLAB, d)

        # multiply by site factor to "convert" Japan values to Cascadia values
        # then convert from cm/s**2 to g
        mean = np.log((np.exp(mean) * C_SF["MF"]) * 1e-2 / g)

        stddevs = self._get_stddevs(C['sigma'], C_SSLAB['tauS'], stddev_types,
                                    num_sites=len(sites.vs30))

        # add extrapolation factor if outside SA range (0.05 - 5.0)
        if extrapolate:
            dctx = DistancesContext()
            dctx.rhypo = dists.rrup  # approximation for extrapolation only
            mean += extrapolation_factor(self.extrapolate_GMM, rup, sites,
                                         dctx, imt, target_imt)
        return mean, stddevs

    def _compute_site_class_term_CanadaSHM6(self, C, vs30, imt):
        """
        For CanadaSHM6 the ZhaoEtAl2006 site term is replaced with:
            Vs30
            2000 = minimum(1100, maximum[hard-rock, SC I + AA13/AB06 factor])
            1100 = average of hard-rock and SC I
            760 = SC I
            450 = SC II
            250 = SC III
            160 = SC IV

            log-log interpolation for intermediate values

        """

        ref_vs30 = np.array([2000., 1100., 760., 450., 250., 160.])
        ref_values = np.array([0.0, 0.5*(C['CH'] + C['C1']), C['C1'], C['C2'],
                               C['C3'], C['C4']])

        # Equivalent to CanadaSHM6_hardrock_site_factor but reproduced here
        # to avoid using np.interp twice.
        fac_760_2000 = np.log(1./COEFFS_AB06[imt]['c'])
        ref_values[0] = np.min([0.5*(C['CH'] + C['C1']),
                                np.max([C['CH'], C['C1'] + fac_760_2000])])
        site_term = np.interp(np.log(vs30), np.log(np.flip(ref_vs30, axis=0)),
                              np.flip(ref_values, axis=0))
        return site_term


class CanSHM6_InSlab_ZhaoEtAl2006SSlabCascadia30(
        CanSHM6_InSlab_ZhaoEtAl2006SSlabCascadia55):
    """
    Variant of CanadaSHM6_InSlab_ZhaoEtAl2006SSlabCascadia55 with a hypo depth
    of 30 km.
    """

    HYPO_DEPTH = 30.
    extrapolate_GMM = CanSHM6_InSlab_AbrahamsonEtAl2015SSlab30()


class CanSHM6_InSlab_AtkinsonBoore2003SSlabCascadia55(
        AtkinsonBoore2003SSlabCascadia):
    """
    Atkinson and Boore 2003 InSlab with Cascadia adjustment, at a fixed hypo
    depth of 55 km and with modifications to the site term as implemented for
    CanadaSHM6.
    """
    # Parameters used to extrapolate to 0.05s <= T <= 10s
    MAX_SA = 3.0
    MIN_SA = 0.04
    MAX_SA_EXTRAP = 10.0
    MIN_SA_EXTRAP = 0.05
    extrapolate_GMM = CanSHM6_InSlab_AbrahamsonEtAl2015SSlab55()

    REQUIRES_SITES_PARAMETERS = set(('vs30', 'backarc'))

    HYPO_DEPTH = 55.

    def __init__(self):
        super(CanSHM6_InSlab_AtkinsonBoore2003SSlabCascadia55,
              self).__init__()

        self.COEFFS_SSLAB = CoeffsTable_CanadaSHM6(self.COEFFS_SSLAB,
                                                   self.MAX_SA, self.MIN_SA,
                                                   self.MAX_SA_EXTRAP,
                                                   self.MIN_SA_EXTRAP)
        self.COEFFS_SINTER = CoeffsTable_CanadaSHM6(self.COEFFS_SINTER,
                                                    self.MAX_SA, self.MIN_SA,
                                                    self.MAX_SA_EXTRAP,
                                                    self.MIN_SA_EXTRAP)

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.

        CanadaSHM6 edits: added extrapolation beyond MAX_SA and MIN_SA
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

        # extracting dictionary of coefficients specific to required
        # intensity measure type.
        C = self.COEFFS_SSLAB[imt]

        # cap magnitude values at 8.0, see page 1709
        mag = rup.mag
        if mag >= 8.0:
            mag = 8.0

        # compute PGA on rock (needed for site amplification calculation)
        G = 10 ** (0.301 - 0.01 * mag)
        pga_rock = self._compute_mean(self.COEFFS_SSLAB[PGA()], G, mag,
                                      self.HYPO_DEPTH, dists.rrup, sites.vs30,
                                      # by passing pga_rock > 500 the soil
                                      # amplification is 0
                                      np.zeros_like(sites.vs30) + 600,
                                      PGA())
        pga_rock = 10 ** (pga_rock)

        # compute actual mean and convert from log10 to ln and units from
        # cm/s**2 to g
        mean = self._compute_mean(C, G, mag, self.HYPO_DEPTH, dists.rrup,
                                  sites.vs30, pga_rock, imt)
        mean = np.log((10 ** mean) * 1e-2 / g)

        if imt.period == 4.0:
            mean /= 0.550

        stddevs = self._get_stddevs(C, stddev_types, sites.vs30.shape[0])

        # add extrapolation factor if outside SA range (0.07 - 9.09)
        if extrapolate:
            dctx = DistancesContext()
            dctx.rhypo = dists.rrup  # approximation for extrapolation only
            mean += extrapolation_factor(self.extrapolate_GMM, rup, sites,
                                         dctx, imt, target_imt)

        return mean, stddevs

    def _compute_soil_amplification(self, C, vs30, pga_rock, imt):
        """
        For CanadaSHM6 the AtkinsonBoore2003 site term is replaced with one as
        documented in X. In short, the site term is defined as:

            Vs30
            2000 = min(0, AA13/AB06 factor relative to 1100)
            1100 = 0 (GMM base condition is Site Class B = 1100 m/s)
            760 = log-interpolated values between 0 and 450
            450 = Site Class C (c5)
            250 = Site Class D (c6)
            160 = Site Class E (c7)

            log-log interpolation for intermediate values

        """
        # factor controlling degree of linearity
        sl = self._compute_soil_linear_factor(pga_rock, imt)

        ref_vs30 = np.array([2000., 1100., 760., 450., 250., 160.])
        ref_values = np.array([0.0, 0.0, C['c5']*0.41367, C['c5'], C['c6'],
                               C['c7']])

        # Equivalent to CanadaSHM6_hardrock_site_factor but reproduced here
        # to avoid using np.interp twice.
        ref_values[0] = np.min([0, np.log10(1./COEFFS_AB06[imt]['c']) +
                                ref_values[2]])
        site_term = np.interp(np.log10(vs30), np.log10(np.flip(ref_vs30,
                                                               axis=0)),
                              np.flip(ref_values, axis=0))
        site_term[vs30 < 1100.] *= sl[vs30 < 1100.]
        return site_term


class CanSHM6_InSlab_AtkinsonBoore2003SSlabCascadia30(
        CanSHM6_InSlab_AtkinsonBoore2003SSlabCascadia55):
    """
    Variant of CanadaSHM6_InSlab_AtkinsonBoore2003SSlabCascadia55 with a hypo
    depth of 30 km.
    """

    HYPO_DEPTH = 30.
    extrapolate_GMM = CanSHM6_InSlab_AbrahamsonEtAl2015SSlab30()


class CanSHM6_InSlab_GarciaEtAl2005SSlab55(GarciaEtAl2005SSlab):
    """
    Garcia et al., 2005 (horizontal) GMM at a fixed hypo depth of 55 km and
    with an added site term (modified version of BSSA14 / SS14) as implemented
    for CanadaSHM6.
    """

    REQUIRES_SITES_PARAMETERS = set(('vs30', 'backarc'))

    # Parameters used to extrapolate to 0.05s <= T <= 10s
    MAX_SA = 5.0
    MIN_SA = 0.04
    MAX_SA_EXTRAP = 10.0
    MIN_SA_EXTRAP = 0.05
    extrapolate_GMM = CanSHM6_InSlab_AbrahamsonEtAl2015SSlab55()
    BSSA14 = BooreEtAl2014()

    HYPO_DEPTH = 55.

    def __init__(self):

        super(CanSHM6_InSlab_GarciaEtAl2005SSlab55,
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
                          added site amplification term
                          forced rrup = rhypo (to be inline with the
                                               CanadaSHM6-table implementation)
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

        # Approximation made to match the table-GMM implementation of
        # GarciaEtAl2005SSlab used to generate CanadaSHM6 and NBCC2020 values.
        # For CanadaSHM6 the net effect on mean hazard is small.
        dctx = DistancesContext()
        dctx.rrup = dists.rhypo
        dctx.rhypo = dists.rhypo

        # Extracting dictionary of coefficients specific to required
        # intensity measure type.
        C = self.COEFFS[imt]
        mag = rup.mag

        mean = self._compute_mean(C, g, mag, self.HYPO_DEPTH, dctx, imt)
        stddevs = self._get_stddevs(C, stddev_types, sites.vs30.shape[0])

        pga1100 = self._compute_mean(self.COEFFS[PGA()], g, mag,
                                     self.HYPO_DEPTH, dctx, PGA())

        mean += self.site_amplification(sites, imt, pga1100)

        # add extrapolation factor if outside SA range 0.04 - 5.0
        if extrapolate:
            mean += extrapolation_factor(self.extrapolate_GMM, rup, sites,
                                         dctx, imt, target_imt)

        return mean, stddevs

    def site_amplification(self, sites, imt, pga1100):
        """
        For CanadaSHM6 a site term is added to GarciaEtAl2005SSlab which is
        defined as:

            Vs30 < 1100 m/s: BSSA14 relative to Vs30=1100m/s

            Vs30 >= 1100 m/s: The larger of AB06/AA13 760-to-2000 factor
                              (interpolated for 1100-to-2000) and BSSA14.
                              Note: this slightly differs from other western
                              CanadaSHM6 hard rock site terms as it allows for
                              the AB06/AA13 amplification for short-periods
                              and PGA.

        """
        amp = np.zeros_like(pga1100)

        # Amplification for Vs30 >= 1100 m/s
        vs30_gte1100 = sites.vs30[sites.vs30 >= 1100.]
        # AB06 / AA13 factor for 1100 to 2000
        AB06 = np.log(1./COEFFS_AB06[imt]['c'])
        AB06_1100 = np.interp(np.log(1100), np.log([760, 2000]), [0, AB06])
        AB06_2000div1100 = AB06 - AB06_1100
        AB06_vs = np.interp(np.log(vs30_gte1100), np.log([1100, 2000]),
                            [0, AB06_2000div1100])

        # BSSA14 factor relative to 1100
        C = self.BSSA14.COEFFS[imt]
        BSSA14_vs = (self.BSSA14._get_linear_site_term(C, vs30_gte1100)
                     - self.BSSA14._get_linear_site_term(C, np.array([1100.])))

        # Larger of BSSA14 and AB06/AA13 factor
        F_gte1100 = np.maximum.reduce([AB06_vs, BSSA14_vs])

        # Amplification for Vs30 < 1100 m/s
        sites_lt1100 = SitesContext()
        sites_lt1100.vs30 = sites.vs30[sites.vs30 < 1100.]

        # Correct PGA to 760 m/s using BSSA14
        C_pga = self.BSSA14.COEFFS[PGA()]
        BSSA14_pga1100 = self.BSSA14._get_linear_site_term(C_pga,
                                                           np.array([1100.0]))
        pga760 = pga1100[sites.vs30 < 1100.] - BSSA14_pga1100

        # IMT amplification relative to 1100 m/s following BSSA14
        C = self.BSSA14.COEFFS[imt]

        BSSA14_Vs = self.BSSA14._get_site_scaling(C, np.exp(pga760),
                                                  sites_lt1100, imt.period, [])
        BSSA14_1100 = self.BSSA14._get_linear_site_term(C, np.array([1100.0]))
        F_lt1100 = BSSA14_Vs - BSSA14_1100

        # Set amplifiation above/below 1100 m/s
        amp[sites.vs30 >= 1100.] = F_gte1100
        amp[sites.vs30 < 1100.] = F_lt1100

        return amp


class CanSHM6_InSlab_GarciaEtAl2005SSlab30(
        CanSHM6_InSlab_GarciaEtAl2005SSlab55):
    """
    Variant of CanadaSHM6_InSlab_GarciaEtAl2005SSlab55 with a hypo depth
    of 30 km.
    """

    HYPO_DEPTH = 30
    extrapolate_GMM = CanSHM6_InSlab_AbrahamsonEtAl2015SSlab30()


def extrapolation_factor(GMM, rctx, sctx, dctx, boundingIMT, extrapIMT):
    """
    Returns the log-difference in ground motion between two IMTs.
    with CanadaSHM6 this is used to extrapolate GMMs which are not valid over
    the desired UHS range of 0.05 - 10 s using comparable GMMs which are.

    GMM: OQ gsim
    rctx, sctx, dctx: OQ rupture, site and distance contexts
    boundingIMT: IMT for the bounding period
    extrapIMT: IMT for the SA being extrapolated to
    """

    bounding_vals, _ = GMM.get_mean_and_stddevs(sctx, rctx, dctx, boundingIMT,
                                                [StdDev.TOTAL])
    extrap_vals, _ = GMM.get_mean_and_stddevs(sctx, rctx, dctx, extrapIMT,
                                              [StdDev.TOTAL])

    return extrap_vals - bounding_vals


class CoeffsTable_CanadaSHM6(object):
    """
    Variant of the OpenQuake CoeffsTable object which returns the imt at the
    bounding period if you request the table for periods between the max/min
    period range of the table and the defined max/min extrapolation range.
    """

    def __init__(self, coeff, max_SA, min_SA, max_SA_extrap, min_SA_extrap):
        self.coeff = coeff
        self.max_SA = max_SA
        self.min_SA = min_SA
        self.max_SA_extrap = max_SA_extrap
        self.min_SA_extrap = min_SA_extrap

    def __getitem__(self, key):

        if (key.name == 'SA') and (key.period > self.max_SA
                                   and key.period <= self.max_SA_extrap):
            return self.coeff[SA(self.max_SA)]

        if (key.name == 'SA') and (key.period < self.min_SA
                                   and key.period >= self.min_SA_extrap):
            return self.coeff[SA(self.min_SA)]

        if (key.name == 'SA') and (key.period > self.max_SA_extrap
                                   or key.period < self.min_SA_extrap):
            raise KeyError(key)

        else:
            return self.coeff[key]

    # causes issues with pickling - removed this means that
    # CoeffsTable_CanadaSHM6 is not called during check_imt by OQ
    # @property
    # def __class__(self):
    #     return CoeffsTable


COEFFS_AB06 = CoeffsTable(sa_damping=5, table="""\
    IMT     c
    pgv 1.23
    pga  0.891
    0.005 0.791
    0.05 0.791
    0.1 1.072
    0.2 1.318
    0.3 1.38
    0.5 1.38
    1.0 1.288
    2.0 1.230
    5.0 1.148
    10.0 1.072
    """)

# Coefficient table taken from Gail Atkinson's "White paper on
# Proposed Ground-motion Prediction Equations (GMPEs) for 2015
# National Seismic Hazard Maps" (2012, page 16).
# Values were interpolated to include all listed periods.
# MF is the linear multiplicative factor.
COEFFS_SITE_FACTORS = CoeffsTable(sa_damping=5, table="""\
    IMT    MF
    pga    0.50
    pgv    1.00
    0.05   0.44
    0.10   0.44
    0.15   0.53
    0.20   0.60
    0.25   0.72
    0.30   0.81
    0.40   1.00
    0.50   1.01
    0.60   1.02
    0.70   1.02
    0.80   1.03
    0.90   1.04
    1.00   1.04
    1.25   1.19
    1.50   1.31
    2.00   1.51
    2.50   1.34
    3.00   1.21
    4.00   1.09
    5.00   1.00
    """)
