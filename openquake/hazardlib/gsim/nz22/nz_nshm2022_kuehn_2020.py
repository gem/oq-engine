"""
New Zealand National Seismic Hazard Model 2022 Revision modification of Kuehn 2020 GMMs.
Adjustment in aleatory uncertainty to account for the effect of magnitude and distance
dependence towards smaller Vs30 values. In the intraslab model the adjustment for
backarc attenuation which is based on Abrahamson et al 2016 BC Hydro GMM.

Bradley, B. A., S. Bora, R. L. Lee, E. F. Manea, M. C. Gerstenberger, P.
J. Stafford, G. M. Atkinson, G. Weatherill, J. Hutchinson, C. A. de
la Torre, et al. (2022). Summary of the ground-motion character-
isation model for the 2022 New Zealand National Seismic Hazard
Model, GNS Science Rept. 2022/46, GNS Science, Lower Hutt, New
Zealand, 44 pp.

Bradley, B., S. Bora, R. Lee, E. Manea, M. Gerstenberger, P. Stafford, G.
Atkinson, G. Weatherill, J. Hutchinson, C. de la Torre, et al.
(2023). Summary of the ground-motion characterisation model
for the 2022 New Zealand National Seismic Hazard Model,
Bull. Seismol. Soc. Am.

Lee, R.L., B.A. Bradley, E.F. Manea, J.A. Hutchinson, S.S.
Bora (2022). Evaluation of Empirical Ground-Motion Models for the 2022 New
Zealand National Seismic Hazard Model Revision, Bull. Seismol. Soc. Am.

Module exports :class:`NZNSHM2022_KuehnEtAl2020SInter`
               :class:`NZNSHM2022_KuehnEtAl2020SSlab`
"""

import numpy as np

from scipy.interpolate import interp1d

from openquake.hazardlib.gsim.base import add_alias
from openquake.hazardlib.imt import PGA
from openquake.hazardlib import const
from openquake.hazardlib.gsim.kuehn_2020 import (
    _get_ln_z_ref,
    get_base_term,
    get_magnitude_scaling_term,
    get_geometric_attenuation_term,
    get_anelastic_attenuation_term,
    get_depth_term,
    get_shallow_site_response_term,
    get_sigma_mu_adjustment,
    KuehnEtAl2020SInter,
    CONSTS,
    REGION_TERMS_IF,
    REGION_TERMS_SLAB,
    SUPPORTED_REGIONS,
    Z_MODEL,
)


def get_basin_response_term(C, region, vs30, z_value):
    """
    Returns the basin response term, based on the region and the depth
    to a given velocity layer

    :param numpy.ndarray z_value:
        Basin depth term (Z2.5 for JPN and CAS, Z1.0 for NZL and TWN)
    """
    # Basin term only defined for the four regions: Cascadia, Japan,
    # New Zealand and Taiwan
    assert region in ("CAS", "JPN", "NZL", "TWN")
    # Get c11, c12 and Z-model (same for both interface and inslab events)
    c11 = C[REGION_TERMS_IF[region]["c11"]]
    c12 = C[REGION_TERMS_IF[region]["c12"]]
    CZ = Z_MODEL[region]

    brt = np.zeros_like(z_value)
    mask = z_value > 0.0
    if not np.any(mask):
        # No basin amplification to be applied
        return 0.0
    if region == "NZL": # Personal communication with Nico. We need to use the NZ specific Z1.0-Vs30 correlation (Sanjay Bora 20.06.2022).
        brt[mask] = c11 + c12 * (_get_ln_z_ref(CZ, vs30[mask]) -
                                     _get_ln_z_ref(CZ, vs30[mask]))
    else:
        brt[mask] = c11 + c12 * (np.log(z_value[mask]) -
                                 _get_ln_z_ref(CZ, vs30[mask]))
    return brt


def get_partial_derivative_site_pga(C, vs30, pga1100):
    """
    Defines the partial derivative of the site term with respect to the PGA on reference rock. Note that this is taken
    from AG20. The only difference is Vsref which is 1000 m/s in AG20. This function is added to get the nonlinear
    correction in aleatory sigma given below.
    """
    dfsite_dlnpga = np.zeros(vs30.shape)
    idx = vs30 <= C["k1"]
    vnorm = vs30[idx] / C["k1"]
    dfsite_dlnpga[idx] = C["k2"] * pga1100 * (
        (-1.0 / (pga1100 + CONSTS["c"])) +
        (1.0 / (pga1100 + CONSTS["c"] * (vnorm ** CONSTS["n"])))
        )
    return dfsite_dlnpga


def get_nonlinear_stddevs(C, C_PGA, imt, vs30, pga1100):
    """
    Get the heteroskedastic within-event and between-event standard deviation. This routine gives the aleatory sigma
    values corrected for nonlinearity in the soil response.
    """
    period = imt.period

    # Correlation coefficients from AG20
    periods_AG20 = [0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 7.5, 10.0]
    rho_Ws = [1.0, 0.99, 0.99, 0.97, 0.95, 0.92, 0.9, 0.87, 0.84, 0.82, 0.74, 0.66, 0.59, 0.5, 0.41, 0.33, 0.3, 0.27, 0.25, 0.22, 0.19, 0.17, 0.14, 0.1]
    rho_Bs = [1.0, 0.99, 0.99, 0.985, 0.98, 0.97, 0.96, 0.94, 0.93, 0.91, 0.86, 0.8, 0.78, 0.73, 0.69, 0.62, 0.56, 0.52, 0.495, 0.43, 0.4, 0.37, 0.32, 0.28]

    rho_W_itp = interp1d(np.log(periods_AG20), rho_Ws)
    rho_B_itp = interp1d(np.log(periods_AG20), rho_Bs)
    if period < 0.01:
        rhoW = 1.0
        rhoB = 1.0
    else:
        rhoW = rho_W_itp(np.log(period))
        rhoB = rho_B_itp(np.log(period))

    # Get linear tau and phi
    tau_lin = C["tau"]*np.ones(vs30.shape)
    tau_lin_pga = C_PGA["tau"]*np.ones(vs30.shape)
    phi_lin = C["phi"]*np.ones(vs30.shape)
    phi_lin_pga = C_PGA["phi"]*np.ones(vs30.shape)
    # Find the sites where nonlinear site terms apply
    idx = vs30 <= C["k1"]
    # Process the nonlinear site terms
    phi_amp = 0.3
    partial_f_pga = get_partial_derivative_site_pga(C, vs30[idx], pga1100[idx])
    phi_b = np.sqrt(phi_lin[idx] ** 2.0 - phi_amp ** 2.0)
    phi_b_pga = np.sqrt(phi_lin_pga[idx] ** 2.0 - phi_amp ** 2.0)

    # Get nonlinear tau and phi terms
    tau = tau_lin.copy()
    phi = phi_lin.copy()
    tau_nl_sq = tau_lin[idx]**2 + (partial_f_pga ** 2.0) * tau_lin_pga[idx]**2 +\
                (2.0 * partial_f_pga * tau_lin_pga[idx]*tau_lin[idx]*rhoB)

    phi_nl_sq = (phi_lin[idx] ** 2.0) + (partial_f_pga ** 2.0) * (phi_b_pga ** 2.0) +\
        (2.0 * partial_f_pga * phi_b_pga * phi_b * rhoW)
    tau[idx] = np.sqrt(tau_nl_sq)
    phi[idx] = np.sqrt(phi_nl_sq)
    sigma = np.sqrt(tau**2 + phi**2)

    return sigma, tau, phi


def get_mean_values(C, region, trt, m_b, ctx, a1100=None):
    """
    Returns the mean ground values for a specific IMT

    :param float m_b:
        Magnitude scaling breakpoint
    """
    if a1100 is None:
        # Refers to the reference rock case - so Vs30 is 1100 and no a1100
        # is defined
        vs30 = 1100.0 * np.ones(ctx.vs30.shape)
        a1100 = np.zeros(vs30.shape)
        z_values = np.zeros(vs30.shape)
    else:
        vs30 = ctx.vs30.copy()
        if region in ("JPN", "CAS"):
            z_values = ctx.z2pt5 * 1000.0
        elif region in ("TWN"):
            z_values = ctx.z1pt0.copy()
        else:
            z_values = np.zeros(vs30.shape)
    # Get the mean ground motions
    mean = (get_base_term(C, trt, region) +
            get_magnitude_scaling_term(C, trt, m_b, ctx.mag) +
            get_geometric_attenuation_term(C, trt, ctx.mag, ctx.rrup) +
            get_anelastic_attenuation_term(C, trt, region, ctx.rrup) +
            get_depth_term(C, trt, ctx.ztor) +
            get_shallow_site_response_term(C, region, vs30, a1100))

    # For Cascadia, Japan, New Zealand and Taiwan a basin depth term
    # is included
    if region in ("CAS", "JPN"):
        # For Cascadia and Japan Z2.5 is used as the basin parameter (in m
        # rather than km)
        mean += get_basin_response_term(C, region, vs30, z_values)
    elif region in ("NZL", "TWN"):
        # For New Zealand and Taiwan Z1.0 (m) is used as the basin parameter
        mean += get_basin_response_term(C, region, vs30, z_values)
    else:
        pass
    return mean


def get_backarc_term(trt, imt, ctx):

    """ The backarc correction factors to be applied with the ground motion prediction. In the NZ context, it is applied to only subduction intraslab events.
    It is essentially the correction factor taken from BC Hydro 2016. Abrahamson et al. (2016) Earthquake Spectra.
    The correction is applied only for backarc sites as function of distance."""

    periods =  [0.0, 0.02, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 7.5, 10.0]
    theta7s = [1.0988, 1.0988, 1.2536, 1.4175, 1.3997, 1.3582, 1.1648, 0.994, 0.8821, 0.7046, 0.5799, 0.5021, 0.3687, 0.1746,
       -0.082 , -0.2821, -0.4108, -0.4466, -0.4344, -0.4368, -0.4586, -0.4433, -0.4828]
    theta8s = [-1.42, -1.42, -1.65, -1.8 , -1.8 , -1.69, -1.49, -1.3 , -1.18, -0.98, -0.82, -0.7 , -0.54, -0.34, -0.05,  0.12,  0.25,  0.3,
        0.3,  0.3,  0.3,  0.3,  0.3]
    period  = imt.period

    w_epi_factor = 1.008

    theta7_itp = interp1d(np.log(periods[1:]), theta7s[1:])
    theta8_itp = interp1d(np.log(periods[1:]), theta8s[1:])
    # Note that there is no correction for PGV. Hence, I make theta7 and theta8 as 0 for periods < 0.
    if period < 0:
        theta7 = 0.0
        theta8 = 0.0
    elif (period >= 0 and period < 0.02):
        theta7 = 1.0988
        theta8 = -1.42
    else:
        theta7 = theta7_itp(np.log(period))
        theta8 = theta8_itp(np.log(period))

    dists = ctx.rrup

    if trt == const.TRT.SUBDUCTION_INTRASLAB:
        min_dist = 85.0
        backarc = np.bool_(ctx.backarc)
        f_faba = np.zeros_like(dists)
        fixed_dists = dists[backarc]
        fixed_dists[fixed_dists < min_dist] = min_dist
        f_faba[backarc] = theta7 + theta8*np.log(fixed_dists/40.0)
        return f_faba*w_epi_factor
    else:
        f_faba = np.zeros_like(dists)
        return f_faba


class NZNSHM2022_KuehnEtAl2020SInter(KuehnEtAl2020SInter):

    def __init__(self, region="GLO", m_b=None, sigma_mu_epsilon=0.0, sigma_type="Original", **kwargs):

        super().__init__(region=region, m_b=m_b, sigma_mu_epsilon=sigma_mu_epsilon, sigma_type=sigma_type, **kwargs)
        self.sigma_type = sigma_type

        # reset override of REQUIRES_SITES_PARAMETERS done by super
        if self.region in ("NZL"):
            self.REQUIRES_SITES_PARAMETERS = self.__class__.REQUIRES_SITES_PARAMETERS

    
    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        trt = self.DEFINED_FOR_TECTONIC_REGION_TYPE
        if self.m_b:
            # Take the user define magnitude scaling breakpoint
            m_b = self.m_b
        else:
            # Take the global m_b for the tectonic region type and region
            m_b = REGION_TERMS_IF[self.region]["mb"] \
                if trt == const.TRT.SUBDUCTION_INTERFACE else \
                REGION_TERMS_SLAB[self.region]["mb"]
        C_PGA = self.COEFFS[PGA()]

        # Get PGA on rock
        pga1100 = np.exp(get_mean_values(
            C_PGA, self.region, trt, m_b, ctx, None) + get_backarc_term(trt, PGA(), ctx))
        # For PGA and SA ( T <= 0.1 ) we need to define PGA on soil to
        # ensure that SA ( T ) does not fall below PGA on soil
        pga_soil = None
        for imt in imts:
            if ("PGA" in imt.string) or (("SA" in imt.string) and
                                         (imt.period <= 0.1)):
                pga_soil = get_mean_values(
                    C_PGA, self.region, trt, m_b,
                    ctx, pga1100) \
                        + get_backarc_term(trt, PGA(), ctx)
                break

        for m, imt in enumerate(imts):
            # Get coefficients for imt
            C = self.COEFFS[imt]
            m_break = m_b + C["dm_b"] if (
                trt == const.TRT.SUBDUCTION_INTERFACE and
                self.region in ("JPN", "SAM")) else m_b
            if imt.string == "PGA":
                mean[m] = pga_soil
            elif "SA" in imt.string and imt.period <= 0.1:
                # If Sa (T) < PGA for T <= 0.1 then set mean Sa(T) to mean PGA
                mean[m] = get_mean_values(
                    C, self.region, trt, m_break,
                    ctx, pga1100) \
                        + get_backarc_term(trt, imt, ctx)
                idx = mean[m] < pga_soil
                mean[m][idx] = pga_soil[idx]
            else:
                # For PGV and Sa (T > 0.1 s)
                mean[m] = get_mean_values(
                    C, self.region, trt, m_break,
                    ctx, pga1100) \
                        + get_backarc_term(trt, imt, ctx)
            # Apply the sigma mu adjustment if necessary
            if self.sigma_mu_epsilon:
                sigma_mu_adjust = get_sigma_mu_adjustment(
                    self.sigma_mu_model, imt, ctx.mag, ctx.rrup)
                mean[m] += self.sigma_mu_epsilon * sigma_mu_adjust
            # Get standard deviations
            if self.sigma_type.lower() == "modified":
                sig[m], tau[m], phi[m] = get_nonlinear_stddevs(C, C_PGA, imt, ctx.vs30, pga1100)
            else:
                tau[m] = C["tau"]
                phi[m] = C["phi"]
                sig[m] = np.sqrt(C["tau"] ** 2.0 + C["phi"] ** 2.0)


class NZNSHM2022_KuehnEtAl2020SSlab(NZNSHM2022_KuehnEtAl2020SInter):
    """
    """

    #: Supported tectonic region type is subduction in-slab
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB


# For the aliases use the verbose form of the region name
REGION_ALIASES = {
    "GLO": "",
    "USA-AK": "Alaska",
    "CAS": "Cascadia",
    "CAM": "CentralAmericaMexico",
    "JPN": "Japan",
    "NZL": "NewZealand",
    "SAM": "SouthAmerica",
    "TWN": "Taiwan",
}


for region in SUPPORTED_REGIONS[1:]:
    add_alias("KuehnEtAl2021SInter" + REGION_ALIASES[region],
              KuehnEtAl2020SInter, region=region)
