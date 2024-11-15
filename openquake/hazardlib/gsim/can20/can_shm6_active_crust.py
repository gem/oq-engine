#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
6th Generation Seismic Hazard Model of Canada (CanadaSHM6) Active Crust GMMs.

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
import types
import numpy as np

import openquake.hazardlib.gsim.boore_2014 as BA14
import openquake.hazardlib.gsim.abrahamson_2014 as ASK14
import openquake.hazardlib.gsim.chiou_youngs_2014 as CY14
import openquake.hazardlib.gsim.campbell_bozorgnia_2014 as CB14

from openquake.hazardlib.imt import PGA, PGV
from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib.gsim.abrahamson_2014 import AbrahamsonEtAl2014
from openquake.hazardlib.gsim.boore_2014 import BooreEtAl2014
from openquake.hazardlib.gsim.chiou_youngs_2014 import ChiouYoungs2014
from openquake.hazardlib.gsim.campbell_bozorgnia_2014 import (
    CampbellBozorgnia2014)

METRES_PER_KM = 1000.

MAX_SA = 10.
MIN_SA = 0.05


def _check_imts(imts):
    # CSHM6 results only valid for PGV, PGA and 0.05 - 10s
    for imt in imts:
        if (imt != PGV() and
            (imt.period != 0 and
                (imt.period < MIN_SA or imt.period > MAX_SA))):
            raise ValueError(str(imt) + ' is not supported. SA must be in '
                             + 'range of ' + str(MIN_SA) + 's and '
                             + str(MAX_SA) + 's.')


# NB: this is calling the basin term
def _get_site_scaling_ba14(kind, region, C, pga_rock, sites, imt, rjb):
    """
    Returns the site-scaling term (equation 5), broken down into a
    linear scaling, a nonlinear scaling and a basin scaling

    CanadaSHM6 edits: modified linear site term for Vs30 > 1100
    """
    # Native site factor for BSSA14
    flin = BA14._get_linear_site_term(C, sites.vs30)

    # Need site factors at Vs30 = 1100 and 2000 to calculate
    # CanadaSHM6 hard rock site factors
    BSSA14_1100 = BA14._get_linear_site_term(C, np.array([1100.0]))
    BSSA14_2000 = BA14._get_linear_site_term(C, np.array([2000.0]))

    # CanadaSHM6 hard rock site factor
    flin[sites.vs30 > 1100] = CanadaSHM6_hardrock_site_factor(
        BSSA14_1100[0], BSSA14_2000[0], sites.vs30[sites.vs30 > 1100], imt)

    fnl = BA14._get_nonlinear_site_term(C, sites.vs30, pga_rock)
    fbd = BA14._get_basin_term(C, sites, region, imt)  # returns 0
    fbd = 0.0

    return flin + fnl + fbd


class CanadaSHM6_ActiveCrust_BooreEtAl2014(BooreEtAl2014):
    """
    Boore et al., 2014 with CanadaSHM6 modifications to amplification factors
    for vs30 > 1100 and limited period range to 0.05 - 10s.

    See also header in CanadaSHM6_ActiveCrust.py
    """
    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method <.base.GMPE.compute>`
        for spec of input and result values.

        CanadaSHM6 edits: limited to the period range of 0.05 - 10s
        """

        # Checking the IMTs used to compute ground-motion
        _check_imts(imts)

        # Compute ground-motion
        c_pga = self.COEFFS[PGA()]
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            pga_rock = BA14._get_pga_on_rock(
                self.kind, self.region, self.sof, c_pga, ctx)
            mean[m] = (
                BA14._get_magnitude_scaling_term(self.sof, C, ctx) +
                BA14._get_path_scaling(self.kind, self.region, C, ctx) +
                _get_site_scaling_ba14(self.kind, self.region, C, pga_rock,
                                       ctx, imt, ctx.rjb))
            sig[m], tau[m], phi[m] = BA14._get_stddevs(self.kind, C, ctx)

# =============================================================================
# =============================================================================


def shm6_site_correction(C, mean, ctx, imt):

    # Need site factors at Vs30 = 760, 1100 and 2000 to calculate
    # CanadaSHM6 hard rock site factors
    vs30_ge1100 = ctx.vs30 > 1100.
    if ~np.any(vs30_ge1100):
        return

    # Computing linear amplification factors for the default case (i.e. NOT
    # for Japan)
    fake = types.SimpleNamespace()
    fake.vs30 = np.array([760.])
    cy14_760 = CY14.get_linear_site_term("", C, fake)

    fake = types.SimpleNamespace()
    fake.vs30 = np.array([1100.])
    cy14_1100 = CY14.get_linear_site_term("", C, fake)

    fake = types.SimpleNamespace()
    fake.vs30 = np.array([2000.])
    cy14_2000 = CY14.get_linear_site_term("", C, fake)

    # CY14 amplification factors relative to Vs30=760 to be consistent
    # with CanadaSHM6 hardrock site factor
    cy14_2000div760 = cy14_2000[0] - cy14_760[0]
    cy14_1100div760 = cy14_1100[0] - cy14_760[0]

    # CanadaSHM6 hard rock site factor
    factor = CanadaSHM6_hardrock_site_factor(cy14_1100div760, cy14_2000div760,
                                             vs30_ge1100, imt)

    # for Vs30 > 1100 add CY14 amplification at 760 and CanadaSHM6 factor
    mean[vs30_ge1100] = factor + cy14_760 + mean[vs30_ge1100]


def get_mean_stddevs_cy14(region, C, ctx, conf):
    """
    Return mean and standard deviation values
    """
    # Get ground motion on reference rock
    ln_y_ref = CY14.get_ln_y_ref(region, C, ctx, conf)
    y_ref = np.exp(ln_y_ref)

    # Set basin depth to 0
    f_z1pt0 = 0.0

    # Get linear amplification term
    f_lin = CY14.get_linear_site_term(region, C, ctx)

    # Get nonlinear amplification term
    f_nl, f_nl_scaling = CY14.get_nonlinear_site_term(C, ctx, y_ref)

    # Add on the site amplification
    mean = ln_y_ref + (f_lin + f_nl + f_z1pt0)

    # Get standard deviations
    sig, tau, phi = CY14.get_stddevs(
        conf['peer'], C, ctx, ctx.mag, y_ref, f_nl_scaling)

    return mean, sig, tau, phi


class CanadaSHM6_ActiveCrust_ChiouYoungs2014(ChiouYoungs2014):
    """
    Chiou and Youngs 2014 with CanadaSHM6 modifications to amplification
    factors for vs30 > 1100, the removal of the basin term (i.e., returns
    mean values on the GMM-centered z1pt0 value) and limited to the period
    range of 0.05 - 10s.

    TODO: CY14 was heavily updated/refactored for OQ v3.11. In order to
    maintain functionaility the original CY14 functions were restored directly
    here. CanadaSHM6_CY14 should be updated to maintain compatibility with the
    refactored CY14.

    See also header.
    """
    #: Required site parameters are Vs30, Vs30 measured flag
    #: and Z1.0.
    REQUIRES_SITES_PARAMETERS = {'vs30', 'vs30measured', 'z1pt0'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        Notes:
            - Centered cdpp already defaulted to 0
        """

        # Checking the IMTs used to compute ground-motion
        _check_imts(imts)

        # Reference to page 1144, PSA might need PGA value
        pga_mean, pga_sig, pga_tau, pga_phi = get_mean_stddevs_cy14(
            self.region, self.COEFFS[PGA()], ctx, self.conf)

        # Processing IMTs
        for m, imt in enumerate(imts):
            if repr(imt) == "PGA":
                mean[m] = pga_mean

                # Site term correction fos SHM6
                shm6_site_correction(self.COEFFS[imt], mean[m], ctx, imt)

                sig[m], tau[m], phi[m] = pga_sig, pga_tau, pga_phi
            else:
                imt_mean, imt_sig, imt_tau, imt_phi = get_mean_stddevs_cy14(
                    self.region, self.COEFFS[imt], ctx, self.conf)
                # reference to page 1144
                # Predicted PSA value at T ≤ 0.3s should be set equal to the
                # value of PGA when it falls below the predicted PGA
                mean[m] = np.where(imt_mean < pga_mean, pga_mean, imt_mean) \
                    if repr(imt).startswith("SA") and imt.period <= 0.3 \
                    else imt_mean

                # Site term correction fos SHM6
                shm6_site_correction(self.COEFFS[imt], mean[m], ctx, imt)
                sig[m], tau[m], phi[m] = imt_sig, imt_tau, imt_phi

# =============================================================================
# =============================================================================


def _get_site_response_term_ask14(C, imt, vs30, sa1180):
    """
    CanadaSHM6 edits: modified linear site term for Vs30 > 1100
    """
    # Native site factor for ASK14
    ask14_vs = ASK14._get_site_response_term(C, imt, vs30, sa1180)

    # Need site factors at Vs30 = 760, 1100 and 2000 to calculate
    # CanadaSHM6 hard rock site factors
    ask14_1100 = ASK14._get_site_response_term(C, imt, np.array([1100.]),
                                               np.array([0.]))
    ask14_760 = ASK14._get_site_response_term(C, imt, np.array([760.]),
                                              np.array([0.]))
    ask14_2000 = ASK14._get_site_response_term(C, imt, np.array([2000.]),
                                               np.array([0.]))

    # ASK14 amplification factors relative to Vs30=760 to be consistent
    # with CanadaSHM6 hardrock site factor
    ask14_1100div760 = ask14_1100[0] - ask14_760[0]
    ask14_2000div760 = ask14_2000[0] - ask14_760[0]

    # CanadaSHM6 hard rock site factor
    F = CanadaSHM6_hardrock_site_factor(ask14_1100div760,
                                        ask14_2000div760,
                                        vs30[vs30 >= 1100.], imt)

    # for Vs30 > 1100 add ASK14 amplification at 760 and CanadaSHM6 factor
    ask14_vs[vs30 >= 1100.] = F + ask14_760

    return ask14_vs


class CanadaSHM6_ActiveCrust_AbrahamsonEtAl2014(AbrahamsonEtAl2014):
    """
    Abrahamson et al., 2014 with CanadaSHM6 modifications to amplification
    factors for vs30 > 1100, the removal of the basin term (i.e., returns
    mean values on the GMM-centered z1pt0 value), and limited to the period
    range of 0.05 - 10s.

    See also header in CanadaSHM6_ActiveCrust.py
    """
    REQUIRES_SITES_PARAMETERS = {'vs30measured', 'vs30', 'z1pt0'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """

        _check_imts(imts)
        # sites.vs30 = sites.vs30.astype(float) # bug in ASK14 if vs30 is int?

        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]

            # compute median sa on rock (vs30=1180m/s). Used for site response
            # term calculation
            sa1180 = np.exp(ASK14._get_sa_at_1180(self.region, C, imt, ctx))

            # Get the mean value. Note that in this version the
            # `soil_depth_term` has been removed
            mean[m] = (ASK14._get_basic_term(C, ctx) +
                       ASK14._get_faulting_style_term(C, ctx) +
                       _get_site_response_term_ask14(
                           C, imt, ctx.vs30, sa1180) +
                       ASK14._get_hanging_wall_term(C, ctx) +
                       ASK14._get_top_of_rupture_depth_term(C, imt, ctx))

            mean[m] += ASK14._get_regional_term(
                self.region, C, imt, ctx.vs30, ctx.rrup)

            # get standard deviations
            sig[m], tau[m], phi[m] = ASK14._get_stddevs(
                self.region, C, imt, ctx, sa1180)

# =============================================================================
# =============================================================================


def _get_shallow_site_response_term_cb14(C, vs30, pga_rock, imt):
    """
    Returns the mean values for a specific IMT

    CanadaSHM6 edits: modified linear site term for Vs30 > 1100
    """
    # Native site factor for CB14
    cb14_vs = CB14._get_shallow_site_response_term(0, C, vs30, pga_rock)

    # Need site factors at Vs30 = 760, 1100 and 2000 to calculate
    # CanadaSHM6 hard rock site factors
    cb14_1100 = CB14._get_shallow_site_response_term(0, C, np.array([1100.]),
                                                     np.array([0.]))
    cb14_760 = CB14._get_shallow_site_response_term(0, C, np.array([760.]),
                                                    np.array([0.]))
    cb14_2000 = CB14._get_shallow_site_response_term(0, C, np.array([2000.]),
                                                     np.array([0.]))

    # CB14 amplification factors relative to Vs30=760 to be consistent
    # with CanadaSHM6 hardrock site factor
    cb14_2000div760 = cb14_2000[0] - cb14_760[0]
    cb14_1100div760 = cb14_1100[0] - cb14_760[0]

    # CanadaSHM6 hard rock site factor
    F = CanadaSHM6_hardrock_site_factor(cb14_1100div760, cb14_2000div760,
                                        vs30[vs30 >= 1100], imt)

    # for Vs30 > 1100 add CB14 amplification at 760 and CanadaSHM6 factor
    cb14_vs[vs30 >= 1100] = F + cb14_760

    return cb14_vs


def get_mean_values_cb14(C, ctx, imt, a1100=None):
    """()
    Returns the mean values for a specific IMT
    """
    if isinstance(a1100, np.ndarray):
        # Site model defined
        temp_vs30 = ctx.vs30
    else:
        # Default site model
        temp_vs30 = 1100.0 * np.ones(len(ctx))

    return (CB14._get_magnitude_term(C, ctx.mag) +
            CB14._get_geometric_attenuation_term(C, ctx.mag, ctx.rrup) +
            CB14._get_style_of_faulting_term(C, ctx) +
            CB14._get_hanging_wall_term(C, ctx) +
            _get_shallow_site_response_term_cb14(C, temp_vs30, a1100, imt) +
            CB14._get_hypocentral_depth_term(C, ctx) +
            CB14._get_fault_dip_term(C, ctx) +
            CB14._get_anelastic_attenuation_term(C, ctx.rrup))


class CanadaSHM6_ActiveCrust_CampbellBozorgnia2014(CampbellBozorgnia2014):
    """
    Campbell and Bozorgnia, 2014 with CanadaSHM6 modifications to amplification
    factors for vs30 > 1100, the removal of the basin term (i.e., returns
    mean values on the GMM-centered z1pt0 value) and limited to the period
    range of 0.05 - 10s.

    See also description in the header
    """
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """

        # Checking the IMTs used to compute ground-motion
        _check_imts(imts)

        # Updating context
        CB14._update_ctx(self, ctx)

        # Get mean and standard deviation of PGA on rock (Vs30 1100 m/s^2)
        C_PGA = self.COEFFS[PGA()]
        pga1100 = np.exp(get_mean_values_cb14(C_PGA, ctx, PGA()))

        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            # Get mean and standard deviations for IMT
            mean[m] = get_mean_values_cb14(C, ctx, imt, pga1100)
            if imt.string[:2] == "SA" and imt.period < 0.25:
                # According to Campbell & Bozorgnia (2013) [NGA West 2 Report]
                # If Sa (T) < PGA for T < 0.25 then set mean Sa(T) to mean PGA
                # Get PGA on soil
                pga = get_mean_values_cb14(C_PGA, ctx, PGA(), pga1100)
                idx = mean[m] <= pga
                mean[m, idx] = pga[idx]

            # Get stddevs for PGA on basement rock
            tau_lnpga_b = CB14._get_taulny(C_PGA, ctx.mag)
            phi_lnpga_b = np.sqrt(CB14._get_philny(C_PGA, ctx.mag) ** 2. -
                                  C["philnAF"] ** 2.)

            # Get tau_lny on the basement rock
            tau_lnyb = CB14._get_taulny(C, ctx.mag)
            # Get phi_lny on the basement rock
            phi_lnyb = np.sqrt(CB14._get_philny(C, ctx.mag) ** 2. -
                               C["philnAF"] ** 2.)
            # Get site scaling term
            alpha = CB14._get_alpha(C, ctx.vs30, pga1100)
            # Evaluate tau according to equation 29
            t = np.sqrt(tau_lnyb**2 + alpha**2 * tau_lnpga_b**2 +
                        2.0 * alpha * C["rholny"] * tau_lnyb * tau_lnpga_b)

            # Evaluate phi according to equation 30
            p = np.sqrt(
                phi_lnyb**2 + C["philnAF"]**2 +
                alpha**2 * phi_lnpga_b**2 +
                2.0 * alpha * C["rholny"] * phi_lnyb * phi_lnpga_b)
            sig[m] = np.sqrt(t**2 + p**2)
            tau[m] = t
            phi[m] = p


def CanadaSHM6_hardrock_site_factor(A1100, A2000, vs30, imt):
    """
    Returns CanadaSHM6 hard rock (Vs30 > 1100 m/s) amplification factors in
    log units.

    A1100: native GMM site factor for 1100 m/s (relative to 760 m/s)
    A2000: native GMM site factor for 2000 m/s (relative to 760 m/s)
    Vs30: array of Vs30 values
    imt: OQ imt class
    """

    # 760-to-2000 factor calculated from AB06 following methodology outlined
    # in AA13
    AB06 = np.log(1./COEFFS_AB06[imt]['c'])

    # Amplification at 2000 m/s for CanadaSHM6
    fac_2000 = np.min([A1100, np.max([A2000, AB06])])

    # Log-Log interpolate for amplification factors between 1100 and 2000
    F = np.interp(np.log(vs30), np.log([1100., 2000.]), [A1100, fac_2000])

    return F


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
