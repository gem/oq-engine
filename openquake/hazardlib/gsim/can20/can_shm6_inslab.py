#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
6th Generation Seismic Hazard Model of Canada (CanadaSHM6) InSlab GMMs.
The final documentation for the GMMs is being prepared. The GMMs are subject
to change up until the release of the documentation.
Preliminary documentation is available in:
Kolaj, M., Halchuk, S., Adams, J., Allen, T.I. (2020): Sixth Generation Seismic
Hazard Model of Canada: input files to produce values proposed for the 2020
National Building Code of Canada; Geological Survey of Canada, Open File 8630,
2020, 15 pages, https://doi.org/10.4095/327322
Kolaj, M., Adams, J., Halchuk, S (2020): The 6th Generation seismic hazard
model of Canada. 17th World Conference on Earthquake Engineering, Sendai,
Japan. Paper 1c-0028.
Kolaj, M., Allen, T., Mayfield, R., Adams, J., Halchuk, S (2019): Ground-motion
models for the 6th Generation Seismic Hazard Model of Canada. 12th Canadian
Conference on Earthquake Engineering, Quebec City, Canada.
"""
import numpy as np

from openquake.hazardlib import const
from openquake.hazardlib.contexts import get_mean_stds
from openquake.hazardlib.gsim.garcia_2005 import GarciaEtAl2005SSlab
from openquake.hazardlib.gsim.garcia_2005 import _get_stddevs as _get_stddevs_ga
from openquake.hazardlib.gsim.zhao_2006 import (
    ZhaoEtAl2006SSlabCascadia, _compute_slab_correction_term,
    _compute_magnitude_squared_term, _set_stddevs)
from openquake.hazardlib.gsim.zhao_2006 import (
    _compute_magnitude_term as _compute_magnitude_term_zh)
from openquake.hazardlib.gsim.zhao_2006 import (
    _compute_focal_depth_term as _compute_focal_depth_term_zh)
from openquake.hazardlib.gsim.zhao_2006 import (
    _compute_distance_term as _compute_distance_term_zh)
from openquake.hazardlib.gsim.abrahamson_2015 import (
    _compute_distance_term as _compute_distance_term_abr)
from openquake.hazardlib.gsim.abrahamson_2015 import (
    _compute_magnitude_term as _compute_magnitude_term_abr)
from openquake.hazardlib.gsim.abrahamson_2015 import (
    _compute_focal_depth_term as _compute_focal_depth_term_abr)
from openquake.hazardlib.gsim.abrahamson_2015 import (
    AbrahamsonEtAl2015SSlab, _compute_pga_rock, get_stress_factor,
    _compute_forearc_backarc_term, _compute_site_response_term)
from openquake.hazardlib.gsim.atkinson_boore_2003 import (
    _compute_mean as _compute_mean_ab)
from openquake.hazardlib.gsim.atkinson_boore_2003 import (
    AtkinsonBoore2003SSlabCascadia, _compute_soil_linear_factor)
from openquake.hazardlib.imt import PGA, SA, PGV
from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib.gsim.boore_2014 import (BooreEtAl2014,
                    _get_linear_site_term, _get_site_scaling)
from scipy.constants import g


def _compute_mean_ga(C, g, ctx, imt):
    """
    Compute mean according to equation on Table 2, page 2275.
    """
    mag = ctx.mag
    hypo_depth = ctx.hypo_depth
    delta = 0.00750 * 10 ** (0.507 * mag)

    # computing R for different values of mag
    R = np.where(mag < 6.5, np.sqrt(ctx.rhypo ** 2 + delta ** 2),
                 np.sqrt(ctx.rhypo ** 2 + delta ** 2))

    mean = (
        # 1st term
        C['c1'] + C['c2'] * mag +
        # 2nd term
        C['c3'] * R -
        # 3rd term
        C['c4'] * np.log10(R) +
        # 4th term
        C['c5'] * hypo_depth)
    # convert from base 10 to base e
    if imt == PGV():
        mean = np.log(10 ** mean)
    else:
        # convert from cm/s**2 to g
        mean = np.log((10 ** mean) * 1e-2 / g)
    return mean


def _compute_site_class_term_CanadaSHM6(C, ctx, imt):
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
    ref_vs30 = np.array([2000., 1100., 760., 450., 250., 160., ])
    ref_values = np.array([0.0, 0.5*(C['CH'] + C['C1']), C['C1'], C['C2'],
                           C['C3'], C['C4']])
    
    # Equivalent to CanadaSHM6_hardrock_site_factor but reproduced here
    # to avoid using np.interp twice.
    fac_760_2000 = np.log(1./COEFFS_AB06[imt]['c'])
    ref_values[0] = np.min([0.5*(C['CH'] + C['C1']), np.max(
        [C['CH'], C['C1'] + fac_760_2000])])
    site_term = np.interp(
        np.log(ctx.vs30), np.log(np.flip(ref_vs30, axis=0)),
        np.flip(ref_values, axis=0))
    
    return site_term


def _compute_soil_amplification(C, ctx, pga_rock, imt):
        """
        For CanadaSHM6 the AtkinsonBoore2003 site term is replaced.
        The site term is defined as:
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
        sl = _compute_soil_linear_factor(pga_rock, imt)

        ref_vs30 = np.array([2000., 1100., 760., 450., 250., 160., ])
        ref_values = np.array([0.0, 0.0, C['c5']*0.41367, C['c5'], C['c6'],
                              C['c7']])

        # Equivalent to CanadaSHM6_hardrock_site_factor but reproduced here
        # to avoid using np.interp twice.
        ref_values[0] = np.min([0, np.log10(1./COEFFS_AB06[imt]['c']) +
                                ref_values[2]])
        site_term = np.interp(np.log10(ctx.vs30), np.log10(np.flip(ref_vs30,
                                                               axis=0)),
                              np.flip(ref_values, axis=0))
        site_term[ctx.vs30 < 1100.] *= sl[ctx.vs30 < 1100.]

        return site_term


def site_amplification(ctx, imt, pga1100):
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
        vs30_gte1100 = ctx.vs30[ctx.vs30 >= 1100.]
        # AB06 / AA13 factor for 1100 to 2000
        AB06 = np.log(1./COEFFS_AB06[imt]['c'])
        AB06_1100 = np.interp(np.log(1100), np.log([760, 2000]), [0, AB06])
        AB06_2000div1100 = AB06 - AB06_1100
        AB06_vs = np.interp(np.log(vs30_gte1100), np.log([1100, 2000]),
                            [0, AB06_2000div1100])

        # BSSA14 factor relative to 1100
        BSSA14 = BooreEtAl2014()
        C = BSSA14.COEFFS[imt]
        BSSA14_vs = (_get_linear_site_term(C, vs30_gte1100)
                     - _get_linear_site_term(C, np.array([1100.])))

        # Larger of BSSA14 and AB06/AA13 factor
        F_gte1100 = np.maximum.reduce([AB06_vs, BSSA14_vs])

        # Amplification for Vs30 < 1100 m/s
        sites_lt1100 = ctx[ctx.vs30 < 1100.]

        # Correct PGA to 760 m/s using BSSA14
        C_pga = BSSA14.COEFFS[PGA()]
        BSSA14_pga1100 = _get_linear_site_term(C_pga, np.array([1100.0]))
        pga760 = pga1100[ctx.vs30 < 1100.] - BSSA14_pga1100

        # IMT amplification relative to 1100 m/s following BSSA14
        C = BSSA14.COEFFS[imt]
        imt_per = 0 if imt == PGV() else imt.period

        BSSA14_Vs = _get_site_scaling(
            '', "nobasin", C, np.exp(pga760), sites_lt1100, imt_per, [])
        BSSA14_1100 = _get_linear_site_term(C, np.array([1100.0]))
        F_lt1100 = BSSA14_Vs - BSSA14_1100

        # Set amplifiation above/below 1100 m/s
        amp[ctx.vs30 >= 1100.] = F_gte1100
        amp[ctx.vs30 < 1100.] = F_lt1100

        return amp


COEFFS_MAG_SCALE = CoeffsTable(sa_damping=5, table="""
    IMT    dc1
    pga    0.2
    0.02   0.2
    0.30   0.2
    0.50   0.1
    1.00   0.0
    2.00  -0.1
    3.00  -0.2
    10.0  -0.2
    """)


class CanadaSHM6_InSlab_AbrahamsonEtAl2015SSlab55(AbrahamsonEtAl2015SSlab):
    """
    Abrahramson et al., 2015 (BCHydro) InSlab GMM with a fixed hypo depth of
    55 km, the addition of PGV (scaled from Sa[0.5]) and limited to the CSHM6
    period range of 0.05 <= T <= 10.
    See also header in CanadaSHM6_InSlab.py
    """

    HYPO_DEPTH = 55.
    MAX_SA = 10.
    MIN_SA = 0.05
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([PGA, PGV, SA])

    delta_c1 = None
    kind = "base"

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        Added PGV limited to the period range of 0.05 - 10s
        """
        ctx = ctx.copy()
        ctx.hypo_depth = self.HYPO_DEPTH
        for m, imt in enumerate(imts):
            # set correlated IMT for PGV and check T bounds
            PGVimt = False
            if imt == PGV():
                PGVimt = True
                imt = SA(0.5)
            elif imt.period and (imt.period < self.MIN_SA or
                                 imt.period > self.MAX_SA):
                raise ValueError(str(imt) + ' is not supported. SA must be in '
                                 + 'range of ' + str(self.MIN_SA) + 's and '
                                 + str(self.MAX_SA) + 's.')

            C_PGA = self.COEFFS[PGA()]
            dc1_pga = self.delta_c1 or COEFFS_MAG_SCALE[PGA()]["dc1"]

            # compute median pga on rock (vs30=1000), needed for site response
            # term calculation
            pga1000 = np.exp(_compute_pga_rock(
                    self.kind, self.trt, self.theta6_adj, self.faba_model,
            C_PGA, dc1_pga, ctx))

            C = self.COEFFS[imt]
            dc1 = self.delta_c1 or COEFFS_MAG_SCALE[imt]["dc1"]
            mean[m] = (
                _compute_magnitude_term_abr(
                    self.kind, C, dc1, ctx.mag) +
                _compute_distance_term_abr(
                    self.kind, self.trt, self.theta6_adj, C, ctx) +
                _compute_focal_depth_term_abr(
                    self.trt, C, ctx) +
                _compute_forearc_backarc_term(
                    self.trt, self.faba_model, C, ctx) +
                _compute_site_response_term(
                    C, ctx, pga1000))
            if self.sigma_mu_epsilon:
                # TODO: this part is not tested!
                sigma_mu = get_stress_factor(
                    imt, self.DEFINED_FOR_TECTONIC_REGION_TYPE ==
                    const.TRT.SUBDUCTION_INTRASLAB)
                mean[m] += sigma_mu * self.sigma_mu_epsilon

            sig[m] = C["sigma"] if self.ergodic else C["sigma_ss"]
            tau[m] = C['tau']
            phi[m] = C["phi"] if self.ergodic else np.sqrt(
                C["sigma_ss"] ** 2. - C["tau"] ** 2.)

            if PGVimt:
                mean[m] = (0.995*mean[m]) + 3.937



class CanadaSHM6_InSlab_AbrahamsonEtAl2015SSlab30(
    CanadaSHM6_InSlab_AbrahamsonEtAl2015SSlab55):
    """
    Variant of CanadaSHM6_InSlab_AbrahamsonEtAl2015SSlab55 with a hypo depth
    of 30 km.
    """
    HYPO_DEPTH = 30.


class CanadaSHM6_InSlab_ZhaoEtAl2006SSlabCascadia55(ZhaoEtAl2006SSlabCascadia):
    """
    Zhao et al., 2006 InSlab with Cascadia adjustment, at a fixed hypo depth of
    55 km, extrapolated to 0.05 - 10s and with modifications to the site term
    as implemented for CanadaSHM6.
    See also header in CanadaSHM6_InSlab.py
    """
    # Parameters used to extrapolate to 0.05s <= T <= 10s
    MAX_SA = 5.0
    MIN_SA = 0.05
    MAX_SA_EXTRAP = 10.0
    MIN_SA_EXTRAP = 0.05
    extrapolate_GMM = CanadaSHM6_InSlab_AbrahamsonEtAl2015SSlab55()

    REQUIRES_SITES_PARAMETERS = {'vs30', 'backarc'}
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}
    REQUIRES_DISTANCES = {'rrup'}
    HYPO_DEPTH = 55.

    def __init__(self):
        super().__init__()
        self.COEFFS_SSLAB = CoeffsTable_CanadaSHM6(self.COEFFS_SSLAB,
                                                   self.MAX_SA, self.MIN_SA,
                                                   self.MAX_SA_EXTRAP,
                                                   self.MIN_SA_EXTRAP)
        self.COEFFS_ASC = CoeffsTable_CanadaSHM6(self.COEFFS_ASC,
                                                 self.MAX_SA, self.MIN_SA,
                                                 self.MAX_SA_EXTRAP,
                                                 self.MIN_SA_EXTRAP)

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method <.base.GMPE.compute>`
        for spec of input and result values.
        CanadaSHM6 edits: modified site amplification term
                          added extrapolation beyond MAX_SA and MIN_SA to 0.05
                          - 10s
        """
        ctx = ctx.copy()
        ctx.hypo_depth = self.HYPO_DEPTH
        for m, imt in enumerate(imts):
            extrapolate = False
            PGVimt = False
            if imt == PGV():
                PGVimt = True
                imt = SA(0.5)
            elif imt.period < self.MIN_SA and imt.period >= self.MIN_SA_EXTRAP:
                target_imt = imt
                imt = SA(self.MIN_SA)
                extrapolate = True
            elif imt.period > self.MAX_SA and imt.period <= self.MAX_SA_EXTRAP:
                target_imt = imt
                imt = SA(self.MAX_SA)
                extrapolate = True

            # extracting dictionary of coefficients specific to required
            # intensity measure type.
            C = self.COEFFS_ASC[imt]
            C_SSLAB = self.COEFFS_SSLAB[imt]
            C_SF = COEFFS_SITE_FACTORS[imt]

            # to avoid singularity at 0.0 (in the calculation of the
            # slab correction term), replace 0 values with 0.1
            d = np.array(ctx.rrup)  # make a copy
            d[d == 0.0] = 0.1

            # mean value as given by equation 1, p. 901, without considering
            # faulting style and intraslab terms (that is FR, SS, SSL = 0) and
            # inter and intra event terms, plus the magnitude-squared term
            # correction factor (equation 5 p. 909)
            mean[m] = (_compute_magnitude_term_zh(C, ctx.mag) +
                       _compute_distance_term_zh(C, ctx.mag, d) +
                       _compute_focal_depth_term_zh(C, self.HYPO_DEPTH) +
                       _compute_site_class_term_CanadaSHM6(C, ctx, imt) +
                       _compute_magnitude_squared_term(P=C_SSLAB['PS'], M=6.5,
                                                       Q=C_SSLAB['QS'],
                                                       W=C_SSLAB['WS'],
                                                       mag=ctx.mag) +
                       C_SSLAB['SS']+_compute_slab_correction_term(C_SSLAB, d))

            # multiply by site factor to "convert" Japan values to Cascadia
            # values then convert from cm/s**2 to g
            mean[m] = np.log((np.exp(mean[m]) * C_SF["MF"]) * 1e-2 / g)
            _set_stddevs(sig[m], tau[m], phi[m], C['sigma'], C_SSLAB['tauS'])

            # add extrapolation factor if outside SA range (0.05 - 5.0)
            if extrapolate:
                ctxt = ctx.copy()
                ctxt.rhypo = ctx.rrup  # approximation for extrapolation only
                mean[m] += extrapolation_factor(self.extrapolate_GMM,
                                                ctxt, imt, target_imt)
            if PGVimt:
                mean[m] = (0.995*mean[m]) + 3.937


class CanadaSHM6_InSlab_ZhaoEtAl2006SSlabCascadia30(
        CanadaSHM6_InSlab_ZhaoEtAl2006SSlabCascadia55):
    """
    Variant of CanadaSHM6_InSlab_ZhaoEtAl2006SSlabCascadia55 with a hypo depth
    of 30 km.
    """
    HYPO_DEPTH = 30.
    extrapolate_GMM = CanadaSHM6_InSlab_AbrahamsonEtAl2015SSlab30()


class CanadaSHM6_InSlab_AtkinsonBoore2003SSlabCascadia55(
        AtkinsonBoore2003SSlabCascadia):
    """
    Atkinson and Boore 2003 InSlab with Cascadia adjustment, at a fixed hypo
    depth of 55 km, extrapolated to 0.05 - 10s and with modifications to the
    site term as implemented for CanadaSHM6.
    See also header in CanadaSHM6_InSlab.py
    """
    # Parameters used to extrapolate to 0.05s <= T <= 10s
    MAX_SA = 3.0
    MIN_SA = 0.04
    MAX_SA_EXTRAP = 10.0
    MIN_SA_EXTRAP = 0.05
    extrapolate_GMM = CanadaSHM6_InSlab_AbrahamsonEtAl2015SSlab55()
    REQUIRES_SITES_PARAMETERS = {'vs30', 'backarc'}
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}
    HYPO_DEPTH = 55.

    def __init__(self):
        super().__init__()
        self.COEFFS_SSLAB = CoeffsTable_CanadaSHM6(self.COEFFS_SSLAB,
                                                   self.MAX_SA, self.MIN_SA,
                                                   self.MAX_SA_EXTRAP,
                                                   self.MIN_SA_EXTRAP)
        self.COEFFS_SINTER = CoeffsTable_CanadaSHM6(self.COEFFS_SINTER,
                                                    self.MAX_SA, self.MIN_SA,
                                                    self.MAX_SA_EXTRAP,
                                                    self.MIN_SA_EXTRAP)

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        CanadaSHM6 edits: added extrapolation beyond MAX_SA and MIN_SA to 0.05
                          - 10s
                          limted to the period range of 0.05 - 10s
        """
        ctx = ctx.copy()
        ctx.hypo_depth = self.HYPO_DEPTH

        # cap magnitude values at 8.0, see page 1709
        mag = np.clip(ctx.mag, 0, 8.0)

        # compute PGA on rock (needed for site amplification calculation)
        G = 10 ** (0.301 - 0.01 * mag)
        self.kind = 'SSlab2008'
        pga_rock = _compute_mean_ab(self.kind, self.COEFFS_SSLAB[PGA()], G, mag,
                                    self.HYPO_DEPTH, ctx.rrup, ctx.vs30,
                                    # by passing pga_rock > 500 the soil
                                    # amplification is 0
                                    np.zeros_like(ctx.vs30) + 600,
                                    PGA())
        pga_rock = 10 ** (pga_rock)

        for m, imt in enumerate(imts):

            extrapolate = False
            PGVimt = False

            if imt == PGV():
                PGVimt = True
                imt = SA(0.5)
            elif self.MIN_SA_EXTRAP <= imt.period < self.MIN_SA:
                target_imt = imt
                imt = SA(self.MIN_SA)
                extrapolate = True
            elif self.MAX_SA < imt.period <= self.MAX_SA_EXTRAP:
                target_imt = imt
                imt = SA(self.MAX_SA)
                extrapolate = True
        
            # extracting dictionary of coefficients specific to required
            # intensity measure type.
            C = self.COEFFS_SSLAB[imt]

            # compute actual mean and convert from log10 to ln and units from
            # cm/s**2 to g
            hypo_depth = np.clip(ctx.hypo_depth, 0, 100.) 
            delta = 0.00724 * 10 ** (0.507 * mag)
            R = np.sqrt(ctx.rrup ** 2 + delta ** 2)

            s_amp = _compute_soil_amplification(C, ctx, pga_rock, imt)

            mean[m] =  (
                # 1st term
                C['c1'] + C['c2'] * mag +
                # 2nd term
                C['c3'] * hypo_depth +
                # 3rd term
                C['c4'] * R -
                # 4th term
                G * np.log10(R) +
                # 5th, 6th and 7th terms
                s_amp)

            mean[m] = np.log((10 ** mean[m]) * 1e-2 / g)

            if imt.period == 4.0:
                mean[m] /= 0.550

            sig[m] = np.log(10 ** C['sigma'])
            if 's2' in C.dtype.names:  # in the Gupta subclass
                tau[m] = np.log(10 ** C['s2'])
                phi[m] = np.log(10 ** C['s1'])

            # add extrapolation factor if outside SA range (0.07 - 9.09)
            if extrapolate:
                ctxt = ctx.copy()
                ctxt.rhypo = ctx.rrup  # approximation for extrapolation only
                mean[m] += extrapolation_factor(self.extrapolate_GMM,
                                         ctxt, imt, target_imt)
            if PGVimt:
                mean[m] = (0.995*mean[m]) + 3.937


class CanadaSHM6_InSlab_AtkinsonBoore2003SSlabCascadia30(
                        CanadaSHM6_InSlab_AtkinsonBoore2003SSlabCascadia55):
    """
    Variant of CanadaSHM6_InSlab_AtkinsonBoore2003SSlabCascadia55 with a hypo
    depth of 30 km.
    """
    HYPO_DEPTH = 30.
    extrapolate_GMM = CanadaSHM6_InSlab_AbrahamsonEtAl2015SSlab30()


class CanadaSHM6_InSlab_GarciaEtAl2005SSlab55(GarciaEtAl2005SSlab):
    """
    Garcia et al., 2005 (horizontal) GMM at a fixed hypo depth of 55 km,
    extraploted to 0.05 - 10s and with an added site term (modified version of
    BSSA14 / SS14) as implemented for CanadaSHM6.
    See also header in CanadaSHM6_InSlab.py
    """
    REQUIRES_SITES_PARAMETERS = {'vs30', 'backarc'}
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    # Parameters used to extrapolate to 0.05s <= T <= 10s
    MAX_SA = 5.0
    MIN_SA = 0.04
    MAX_SA_EXTRAP = 10.0
    MIN_SA_EXTRAP = 0.05
    extrapolate_GMM = CanadaSHM6_InSlab_AbrahamsonEtAl2015SSlab55()
    HYPO_DEPTH = 55.

    def __init__(self):
        super().__init__()
        # Need to use new CoeffsTable to be able to handle extrapolation
        self.COEFFS = CoeffsTable_CanadaSHM6(self.COEFFS, self.MAX_SA,
                                             self.MIN_SA, self.MAX_SA_EXTRAP,
                                             self.MIN_SA_EXTRAP)

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GMPE.compute>`
        for spec of input and result values.
        CanadaSHM6 edits: added extrapolation beyond MAX_SA and MIN_SA to 0.05
                          - 10s
                          added site amplification term
                          forced rrup = rhypo (to be inline with the
                                               CanadaSHM6-table implementation)
        """
        ctx = ctx.copy()
        ctx.hypo_depth = self.HYPO_DEPTH
        for m, imt in enumerate(imts):

            if imt == PGV():
                extrapolate = False
            elif imt.period < self.MIN_SA and imt.period >= self.MIN_SA_EXTRAP:
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
            # GarciaEtAl2005SSlab used to generate CanadaSHM6 and NBCC2020
            # For CanadaSHM6 the net effect on mean hazard is small

            C = self.COEFFS[imt]
            mean[m] = _compute_mean_ga(C, g, ctx, imt)
            sig[m], tau[m], phi[m] = _get_stddevs_ga(C)

            pga1100 = _compute_mean_ga(self.COEFFS[PGA()], g, ctx, PGA())

            mean[m] += site_amplification(ctx, imt, pga1100)

            # add extrapolation factor if outside SA range 0.04 - 5.0
            if extrapolate:
                mean[m] += extrapolation_factor(
                    self.extrapolate_GMM, ctx, imt, target_imt)


class CanadaSHM6_InSlab_GarciaEtAl2005SSlab30(
        CanadaSHM6_InSlab_GarciaEtAl2005SSlab55):
    """
    Variant of CanadaSHM6_InSlab_GarciaEtAl2005SSlab55 with a hypo depth
    of 30 km.
    """
    HYPO_DEPTH = 30
    extrapolate_GMM = CanadaSHM6_InSlab_AbrahamsonEtAl2015SSlab30()


def extrapolation_factor(GMM, ctx, boundingIMT, extrapIMT):
    """
    Returns the log-difference in ground motion between two IMTs.
    with CanadaSHM6 this is used to extrapolate GMMs which are not valid over
    the desired UHS range of 0.05 - 10 s using comparable GMMs which are.
    GMM: OQ gsim
    rctx, sctx, dctx: OQ rupture, site and distance contexts
    boundingIMT: IMT for the bounding period
    extrapIMT: IMT for the SA being extrapolated to
    """
    return (get_mean_stds(GMM, ctx, [extrapIMT]) -
            get_mean_stds(GMM, ctx, [boundingIMT]))[0, 0]  # 4, M, N -> N


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
        if self.max_SA < key.period <= self.max_SA_extrap:
            return self.coeff[SA(self.max_SA)]

        if self.min_SA_extrap <= key.period < self.min_SA:
            return self.coeff[SA(self.min_SA)]

        if key.period and (key.period > self.max_SA_extrap or
                           key.period < self.min_SA_extrap):
            raise ValueError(str(key) + ' is not supported. SA must be in '
                             + 'range of ' + str(self.min_SA_extrap) + 's and '
                             + str(self.max_SA_extrap) + 's.')
        else:
            return self.coeff[key]


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
