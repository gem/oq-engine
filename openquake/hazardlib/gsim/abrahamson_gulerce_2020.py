# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2025 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.


"""
Module exports :class:`AbrahamsonGulerce2020SInter`,
               :class:`AbrahamsonGulerce2020SSlab`
"""
import numpy as np

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable, add_alias
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib.gsim.utils_usgs_basin_scaling import \
    _get_z2pt5_usgs_basin_scaling

# The regions for which the model is supported. If not listed then the
# global model (GLO) should be applied
SUPPORTED_REGIONS = ["GLO", "USA-AK", "CAS", "CAM", "JPN", "NZL", "SAM", "TWN"]

# Region-specific constants or references to the corresponding column
# of the coefficients table
REGIONAL_TERMS = {
    "GLO": {
        "C1s": 7.5,
        "a1": "a1",
        },
    "USA-AK": {
        "C1s": 7.9,   # In-slab magnitude scaling breakpoint
        "a1": "a31",   # Region-specific base constant
        "a2-adj": None,  # Adjustment to the geometric spreading term
        "a6-adj": "a24",  # Adjustment to the anelastic attenuation term
        "a12-adj": "a17",  # Adjustment to the linear Vs30 scaling term
        "Z25-adj": None,  # Adjustment to the basin depth scaling term
        },
    "CAS": {
        "C1s": 7.1,
        "a1": "a32",
        "a2-adj": None,
        "a6-adj": "a25",
        "a12-adj": "a18",
        "Z25-adj": "a39",
        },
    "CAM": {
        "C1s": 7.4,
        "a1": "a33",
        "a2-adj": None,
        "a6-adj": "a26",
        "a12-adj": "a19",
        "Z25-adj": None,
        },
    "JPN": {
        "C1s": 7.6,
        "a1": "a34",
        "a2-adj": None,
        "a6-adj": "a27",
        "a12-adj": "a20",
        "Z25-adj": "a41",
        },
    "NZL": {
        "C1s": 8.0,
        "a1": "a35",
        "a2-adj": None,
        "a6-adj": "a28",
        "a12-adj": "a21",
        "Z25-adj": None,
        },
    "SAM": {
        "C1s": 7.5,
        "a1": "a36",
        "a2-adj": None,
        "a6-adj": "a29",
        "a12-adj": "a22",
        "Z25-adj": None,
        },
    "TWN": {
        "C1s": 7.7,
        "a1": "a37",
        "a2-adj": "a16",
        "a6-adj": "a30",
        "a12-adj": "a23",
        "Z25-adj": None,
        },
}


# Region- and period-independent constant values
CONSTS = {
    "C4": 10.0,
    "a3": 0.1,
    "a4": 0.73,
    "a5": 0.0,
    "a9": 0.4,
    "a15": -0.1,
    "a17": 0.0,
    "a19": 0.0,
    "a45": 0.34,
    "d0": 0.47,
    "n": 1.18,
    "c": 1.88,
    "tau_lin": 0.47,
    "phi_amp": 0.3,
    "alpha_phi3": 0.42,
    "T1_phi2": 0.03,
    "T2_phi2": 0.075,
    "T3_phi2": 0.20,
    "T4_phi2": 1.0,
    "T1_phi3": 0.03,
    "T2_phi3": 0.075,
    "T3_phi3": 0.10,
    "T4_phi3": 0.3,
    "d3_phi2": 0.109,
    "d4_phi2": 0.062,
    "d5_phi2": 0.470,
    "d3_phi3": 0.242,
    "d4_phi3": 0.000,
    "d5_phi3": 0.000,
}

METRES_PER_KM = 1000.


def get_base_term(C, region, apply_adjust):
    """
    Returns the region-specific base term (a1 - Equation 3.1)

    :param C:
        Coefficient dictionary for the specfic IMT
    :param str region:
        Region identifier
    :param bool apply_adjust:
        For Alaska and Cascadia apply the modeller-defined adjustment factors
        to the base term (True) or else leave regionalised but unadjusted
        (False)
    """
    if region in ("USA-AK", "CAS") and apply_adjust:
        # For Alaska and Cascdia, apply the adjustments to the coefficient a1
        return C[REGIONAL_TERMS[region]["a1"]] + C["{:s}_Adj".format(region)]
    else:
        return C[REGIONAL_TERMS[region]["a1"]]


def get_magnitude_scaling_term(C, trt, region, mag):
    """
    Returns the magnitude scaling term (defined in Eq 3.3) and regional
    constant

    :param str trt:
        Tectonic region type
    :param np.ndarray mag:
        Earthquake magnitude
    """
    f_mag_quad = C["a13"] * ((10.0 - mag) ** 2.0)
    a4 = CONSTS["a4"]

    if trt == const.TRT.SUBDUCTION_INTERFACE:
        c1 = C["c1i"]
    else:
        c1 = REGIONAL_TERMS[region]["C1s"]
        a4 += CONSTS["a45"]
    f_mag = np.where(mag <= c1,
                     f_mag_quad + a4 * (mag - c1),
                     f_mag_quad + CONSTS["a5"] * (mag - c1))
    return f_mag


def get_geometric_spreading_term(C, region, mag, rrup):
    """
    Returns the geometric spreading term defined in equation 3.1

    :param numpy.ndarray rrup:
        Rupture distances (km)
    """
    a_2 = C["a2"]
    if region == "TWN":
        a_2 += C[REGIONAL_TERMS[region]["a2-adj"]]

    f_r = a_2 + CONSTS["a3"] * (mag - 7.0)
    hff = CONSTS["C4"] * np.exp(CONSTS["a9"] * (mag - 6.0))
    f_r *= np.log(rrup + hff)
    return f_r


def get_anelastic_attenuation_term(C, region, rrup):
    """
    Returns the regionally-adjusted anelastic attenuation term
    """
    a_6 = C["a6"]
    if region != "GLO":
        a_6 += C[REGIONAL_TERMS[region]["a6-adj"]]
    return a_6 * rrup


def get_inslab_scaling_term(C, trt, region, mag, rrup):
    """
    For inslab events, returns the inslab scaling term defined in equation 3.5
    and corrected in the Erratum
    """
    if trt == const.TRT.SUBDUCTION_INTERFACE:
        # Doesn't apply to interface events
        return 0.0
    hff = 10.0 * np.exp(CONSTS["a9"] * (mag - 6.0))
    c1s = REGIONAL_TERMS[region]["C1s"]
    return C["a10"] + (CONSTS["a4"] + CONSTS["a45"]) * (c1s - 7.5) +\
        C["a14"] * np.log(rrup + hff)


def get_rupture_depth_scaling_term(C, trt, ctx):
    """
    Returns the rupture depth scaling described in Equation 3.6, which takes
    the value 0 for interface events

    :param numpy.ndarray ztor:
        Top of rupture depths (km)
    """
    if trt == const.TRT.SUBDUCTION_INTERFACE:
        # Not defined for interface events
        return 0.0
    if isinstance(ctx.ztor, np.ndarray):
        f_dep = C["a11"] * (ctx.ztor - 50.0)
        f_dep[ctx.ztor > 200.0] = C["a11"] * 150.0
        idx = ctx.ztor <= 50.0
        f_dep[idx] = C["a8"] * (ctx.ztor[idx] - 50.0)
    elif ctx.ztor > 200.0:
        f_dep = C["a11"] * 150.0
    elif ctx.ztor <= 50.0:
        f_dep = C["a8"] * (ctx.ztor - 50.0)
    else:
        f_dep = C["a11"] * (ctx.ztor - 50.0)
    return f_dep


def get_site_amplification_term(C, region, vs30, pga1000):
    """
    Returns the shallow site amplification term as descrbied in Equation 3.7,
    and corrected in the Erratum

    :param numpy.ndarray vs30:
        30-m averaged shearwave velocity (m/s)
    :param numpy.ndarray pga1000:
        Peak Ground Acceleration (PGA), g, on a reference bedrock of 1000 m/s
    """
    a12 = C["a12"]
    if region != "GLO":
        # Apply regional adjustment
        a12 += C[REGIONAL_TERMS[region]["a12-adj"]]
    # V* is defined according to Equation 3.8 (i.e. Vs30 clipped at 1000 m/s
    # in the Erratum)
    vstar = np.clip(vs30, -np.inf, 1000.0)
    vnorm = vstar / C["vlin"]
    fsite = a12 * np.log(vnorm)
    idx = vstar >= C["vlin"]
    # Linear site term
    fsite[idx] += (C["b"] * CONSTS["n"] * np.log(vnorm[idx]))
    idx = np.logical_not(idx)
    # Nonlinear site term
    fsite[idx] += C["b"] * (
        np.log(pga1000[idx] + CONSTS["c"] * (vnorm[idx] ** CONSTS["n"])) -
        np.log(pga1000[idx] + CONSTS["c"])
        )
    return fsite


def get_reference_basin_depth(region, vs30):
    """
    For the Cascadia and Japan regions a reference basin depth, dependent
    on the Vs30, is returned according to equations 2.1 and 2.2
    """
    if region == "CAS":
        ln_zref = np.clip(8.52 - 0.88 * np.log(vs30 / 200.0), 7.6, 8.52)
    elif region == "JPN":
        ln_zref = np.clip(7.3 - 2.066 * np.log(vs30 / 170.0), 4.1, 7.3)
    else:
        raise ValueError("No reference basin depth term defined for region %s"
                         % region)
    return np.exp(ln_zref)


def _get_basin_term(C, ctx, region, imt, usgs_baf):
    """
    Returns the basin depth scaling term, applicable only for the Cascadia
    and Japan regions, defined in equations 3.9 - 3.11 and corrected in the
    Erratum

    :param numpy.ndarray z25 (attribute of ctx object):
        Depth to 2.5 m/s shearwave velocity layer (km)
    """
    if region not in ("CAS", "JPN"):
        # Basin depth defined only for Cascadia and Japan, so return 0
        return 0.0

    # Define the ref basin depth (z2pt5 in m) from Vs30
    z25_ref = get_reference_basin_depth(region, ctx.vs30)

    # Use GMM's vs30 to z2pt5 for none-measured values
    z2pt5 = ctx.z2pt5.copy()
    mask = z2pt5 == -999
    z25 = METRES_PER_KM * z2pt5 # From km in ctx metres
    z25[mask] = z25_ref[mask]
        
    # Get USGS basin scaling factor if required (can only be for
    # CAS region)
    if usgs_baf:
        usgs_bf = _get_z2pt5_usgs_basin_scaling(z25, imt.period)
    else:
        usgs_bf = np.ones(len(ctx.vs30))

    # Normalise the basin depth term (Equation 3.9)
    ln_z25_prime = np.log((z25 + 50.0) / (z25_ref + 50.0))
    f_basin = np.zeros(ctx.vs30.shape)
    if region == "JPN":
        # Japan Basin (Equation 3.10)
        f_basin = C["a41"] * np.clip(ln_z25_prime, -2.0, np.inf)
    else:
        # Cascadia Basin (Equation 3.11)
        idx = ln_z25_prime > 0.0
        f_basin[idx] = C["a39"] * ln_z25_prime[idx] * usgs_bf[idx]

    return f_basin


def get_acceleration_on_reference_rock(C, trt, region, ctx, apply_adjustment):
    """
    Returns acceleration on reference rock - intended for use primarily with
    PGA. Overrides the Vs30 values and removes any basin depth terms
    """
    # Set all Vs30 to 1000 m/s
    vs30 = np.full_like(ctx.vs30, 1000.)
    # On rock the amplification is only linear, so PGA1000 is not used
    # set to a null array
    null_pga1000 = np.zeros(vs30.shape)
    # No basin depth is calculated here
    return (get_base_term(C, region, apply_adjustment) +
            get_magnitude_scaling_term(C, trt, region, ctx.mag) +
            get_geometric_spreading_term(C, region, ctx.mag, ctx.rrup) +
            get_anelastic_attenuation_term(C, region, ctx.rrup) +
            get_rupture_depth_scaling_term(C, trt, ctx) +
            get_inslab_scaling_term(C, trt, region, ctx.mag, ctx.rrup) +
            get_site_amplification_term(C, region, vs30, null_pga1000))


def get_mean_acceleration(C, trt, region, ctx, pga1000, imt,
                          apply_adjustment, usgs_baf=False):
    """
    Returns the mean acceleration on soil
    """
    return (get_base_term(C, region, apply_adjustment) +
            get_magnitude_scaling_term(C, trt, region, ctx.mag) +
            get_geometric_spreading_term(C, region, ctx.mag, ctx.rrup) +
            get_anelastic_attenuation_term(C, region, ctx.rrup) +
            get_rupture_depth_scaling_term(C, trt, ctx) +
            get_inslab_scaling_term(C, trt, region, ctx.mag, ctx.rrup) +
            get_site_amplification_term(C, region, ctx.vs30, pga1000) +
            _get_basin_term(C, ctx, region, imt, usgs_baf))


def _get_f2(t1, t2, t3, t4, alpha, period):
    """
    Returns the linear phi short-period scaling term (f2) defined in
    equation 5.3 and corrected in the Erratum
    """
    if period <= t1:
        f2 = 1.0 - alpha
    elif period <= t2:
        f2 = 1.0 - alpha * (np.log(period / t2) / np.log(t1 / t2))
    elif period <= t3:
        f2 = 1.0
    elif period < t4:
        f2 = np.log(period / t4) / np.log(t3 / t4)
    else:
        f2 = 0.0
    return f2


def _get_a_phi2(rrup, d3, d4, d5):
    """
    Returns Aphi, the short period linear phi normalising factor to be
    added to the base linear within-event term, as defined in Equation 5.4
    """
    rrup_norm = (rrup - 225.0) / 225.0
    a_phi2 = d3 + d4 * rrup_norm + d5 * (rrup_norm ** 2.)
    a_phi2[rrup < 225] = d3
    a_phi2[rrup > 450.0] = d3 + d4 + d5
    return a_phi2


def get_phi_lin_model(C, C_PGA, region, period, rrup):
    """
    Returns the distance-dependent linear phi term for both PGA and the
    required spectral period. The term is regionally dependent with additional
    factors added on for Central America, Japan and South America

    Several equations are used here, described fully in section 5.3

    :param float period:
        Spectral period of ground motion
    """
    # Define phi1 term according to equation 5.2
    rrup_norm = (rrup - 150.0) / 300.0
    phi1_sq = np.clip(C["d1"] + C["d2"] * rrup_norm,
                      C["d1"],
                      C["d1"] + C["d2"])
    phi1_sq_pga = np.clip(C_PGA["d1"] + C_PGA["d2"] * rrup_norm,
                          C_PGA["d1"],
                          C_PGA["d1"] + C_PGA["d2"])

    if region in ("USA-AK", "CAS", "NZL", "TWN", "GLO"):
        # For Alaska, Cascadia, New Zealand and Taiwan then phi_lin corresponds
        # only to phi1
        return np.sqrt(phi1_sq), np.sqrt(phi1_sq_pga)
    # Phi 2 model
    # Alpha according to equation 5.6
    alpha = np.clip(1.0 - 0.0036 * (rrup - 250.0), 0.28, 1.0)
    # Retrieve the specific corner periods needed for phi2
    t1, t2, t3, t4 = CONSTS["T1_phi2"], CONSTS["T2_phi2"], CONSTS["T3_phi2"],\
        CONSTS["T4_phi2"]
    # Retrieve the function describing the trapezoidal shape of the increase
    # in linear phi at short periods
    f2_phi2 = _get_f2(t1, t2, t3, t4, alpha, period)
    f2_phi2_pga = 1.0 - alpha
    # Retrieve constants needed for the amplitude scaling factor for
    # the phi2 increase
    d3, d4, d5 = CONSTS["d3_phi2"], CONSTS["d4_phi2"], CONSTS["d5_phi2"]
    a_phi2 = _get_a_phi2(rrup, d3, d4, d5)
    phi2_sq = a_phi2 * f2_phi2
    phi2_sq_pga = a_phi2 * f2_phi2_pga

    if region == "CAM":
        # For Central America and Mexico only the phi1 and phi2 terms are used
        return np.sqrt(phi1_sq + phi2_sq), np.sqrt(phi1_sq_pga + phi2_sq_pga)

    # Phi 3 model - applies to Japan and South America
    # Alpha term is constant
    alpha = CONSTS["alpha_phi3"]
    # Retrieve normalised phi_lin scaling function
    t1, t2, t3, t4 = CONSTS["T1_phi3"], CONSTS["T2_phi3"], CONSTS["T3_phi3"],\
        CONSTS["T4_phi3"]
    f2_phi3 = _get_f2(t1, t2, t3, t4, alpha, period)
    f2_phi3_pga = 1.0 - alpha
    # In this case the amplitude of additional variance is constant
    a_phi3 = CONSTS["d3_phi3"]
    phi3_sq = a_phi3 * f2_phi3
    phi3_sq_pga = a_phi3 * f2_phi3_pga
    return np.sqrt(phi1_sq + phi2_sq + phi3_sq),\
        np.sqrt(phi1_sq_pga + phi2_sq_pga + phi3_sq_pga)


def get_partial_derivative_site_pga(C, vs30, pga1000):
    """
    Defines the partial derivative of the site term with respect to the PGA
    on reference rock, described in equation 5.9 (corrected in Erratum)
    """
    dfsite_dlnpga = np.zeros(vs30.shape)
    vstar = np.clip(vs30, -np.inf, 1000.0)
    idx = vstar <= C["vlin"]
    vnorm = vstar[idx] / C["vlin"]
    dfsite_dlnpga[idx] = C["b"] * pga1000 * (
        (-1.0 / (pga1000 + CONSTS["c"])) +
        (1.0 / (pga1000 + CONSTS["c"] * (vnorm ** CONSTS["n"])))
        )
    return dfsite_dlnpga


def get_tau_phi(C, C_PGA, region, period, rrup, vs30, pga1000, ergodic):
    """
    Get the heteroskedastic within-event and between-event standard deviation
    """
    # Get the site-to-site variability
    if region == "CAM":
        phi_s2s = C["phi_s2s_g2"]
        phi_s2s_pga = C_PGA["phi_s2s_g2"]
    elif region in ("JPN", "SAM"):
        phi_s2s = C["phi_s2s_g3"]
        phi_s2s_pga = C_PGA["phi_s2s_g3"]
    else:
        phi_s2s = C["phi_s2s_g1"]
        phi_s2s_pga = C["phi_s2s_g1"]
    # Get linear tau and phi
    # linear tau is period independent
    tau = CONSTS["tau_lin"] * np.ones(vs30.shape)
    phi_lin, phi_lin_pga = get_phi_lin_model(C, C_PGA, region, period, rrup)
    # Find the sites where nonlinear site terms apply
    idx = np.clip(vs30, -np.inf, 1000) < C["vlin"]
    if not np.any(idx):
        # Only linear term
        if ergodic:
            return tau, phi_lin
        else:
            # Remove the site-to-site variability from phi
            phi = np.sqrt(phi_lin ** 2.0 - phi_s2s ** 2.0)
            return tau, phi

    # Process the nonlinear site terms
    phi = phi_lin.copy()
    partial_f_pga = get_partial_derivative_site_pga(C, vs30[idx], pga1000[idx])
    phi_b = np.sqrt(phi_lin[idx] ** 2.0 - CONSTS["phi_amp"] ** 2.0)
    phi_b_pga = np.sqrt(phi_lin_pga[idx] ** 2.0 - CONSTS["phi_amp"] ** 2.0)

    # Get nonlinear tau and phi terms
    tau_sq = tau[idx] ** 2.0
    tau_sq = tau_sq + (partial_f_pga ** 2.0) * tau_sq +\
        2.0 * partial_f_pga * tau_sq * C["rhoB"]

    phi_nl_sq = (phi_lin[idx] ** 2.0) +\
        (partial_f_pga ** 2.0) * (phi_b_pga ** 2.0) +\
        (2.0 * partial_f_pga * phi_b_pga * phi_b * C["rhoW"])
    tau[idx] = np.sqrt(tau_sq)
    phi[idx] = np.sqrt(phi_nl_sq)
    if not ergodic:
        # Need to update the nonlinear within-event variability term to remove
        # the site-to-site variability
        phi_ss = np.sqrt(phi_lin ** 2.0 - phi_s2s ** 2.0)
        phi_ss_pga = np.sqrt(phi_lin_pga ** 2.0 - phi_s2s_pga ** 2.0)
        phi_ss_b = np.sqrt(phi_ss[idx] ** 2.0 - CONSTS["phi_amp"] ** 2.0)
        phi_ss_b_pga = np.sqrt(phi_ss_pga[idx] ** 2.0 -
                               CONSTS["phi_amp"] ** 2.0)
        phi_ss_nl_sq = (phi_ss[idx] ** 2.0) +\
            (partial_f_pga ** 2.0) * (phi_ss_b_pga ** 2.0) +\
            (2.0 * partial_f_pga * phi_ss_b_pga * phi_ss_b * C["rhoW"])
        phi_ss[idx] = np.sqrt(phi_ss_nl_sq)
        return tau, phi_ss
    return tau, phi


def get_epistemic_adjustment(C, rrup):
    """
    Returns the distance-dependent epistemic adjustment factor defined in
    equation 6.1. In theory, this should only be applied to the global
    model, but we do not enforce this constraint here.
    """
    rrup_norm = np.clip(rrup, 50.0, 500.0) / 100.0
    return C["e1"] + C["e2"] * rrup_norm + C["e3"] * (rrup_norm ** 2.0)


class AbrahamsonGulerce2020SInter(GMPE):
    """
    Implements the 2020 Subduction ground motion model of Abrahamson &
    Gulerce (2020):

    Abrahamson N. and Gulurce Z. (2020) "Regionalized Ground-Motion Models
    for Subduction Earthquakes based on the NGA-SUB Database", Pacific
    Earthquake Engineering Research Center (PEER) Technical Report,
    PEER 2020/25

    The model is regionalised, defining specific adjustment factors for
    (invoking region term in parenthesis):

    - Global ("GLO" - for application to any subduction region for which
      no region-specific adjustment is defined)
    - Alaska ("USA-AK")
    - Cascadia ("CAS")
    - Central America & Mexico ("CAM")
    - Japan ("JPN")
    - New Zealand ("NZL")
    - South America ("SAM")
    - Taiwan ("TWN")

    The region-specific adjustments primarily affect the constant term,
    the anelastic attenuation term and the linear Vs30 scaling term. In
    addition, however, further period-specific adjustment factors can be
    applied for the Alaska and Cascadia regions using the boolean
    input `apply_adjustment`. These adjustments scale the resulting
    ground motion values to appropriate levels accounting for limited data
    and the Alaska and Cascadia region, based on analysis undertaken by
    the authors.

    A general epistemic uncertainty median adjustment factor is also defined
    based on the standard deviation of the median ground motion from five
    regions with estimated regional terms. This term should be applied only
    to the global model (though this is not strictly enforced), and it is
    controlled via the use of `sigma_mu_epsilon`, the number of standard
    deviations by which the adjustment will be multiplied (default = 0)

    A non-ergodic aleatory uncertainty model can be returned by setting
    `ergodic=False`.

    The code implementation and test tables have been verified using
    Fortran code supplied by Professor N. Abrahamson, and cross-checked against
    an independent implementation from Feng Li, Jason Motha and James Paterson
    from University of Canterbury (New Zealand).

    Attributes:
        region (str): Choice of region among the supported regions ("GLO",
                      "USA-AK", "CAS", "CAM", "JPN", "NZL", "SAM", "TWN")
        ergodic (bool): Return the ergodic aleatory variability model (True)
                        or non-ergodic form (False)
        apply_usa_adjustment (bool): Apply the modeller designated Alaska or
                                     Cascadia adjustments (available only for
                                     the regions "USA-AK" or "CAS")
        usgs_basin_scaling (bool): Scaling factor to be applied to basin term
                                   based on USGS basin model
        sigma_mu_epsilon (float): Number of standard deviations to multiply
                                  sigma mu (the standard deviation of the
                                  median) for the epistemic uncertainty model
    """

    #: Supported tectonic region type is subduction interface
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is RotD50
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see section 4.5
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Site amplification is dependent only upon Vs30 for the majority of cases
    #: but Z2.5 is added for the JPN and CAS regions
    REQUIRES_SITES_PARAMETERS = {'vs30', }

    #: Required rupture parameters are only magnitude for the interface model
    REQUIRES_RUPTURE_PARAMETERS = {'mag', }

    #: Required distance measure is closest distance to rupture, for
    #: interface events
    REQUIRES_DISTANCES = {'rrup', }

    #: Defined for a reference velocity of 1000 m/s
    DEFINED_FOR_REFERENCE_VELOCITY = 1000.0

    # Other required params
    REQUIRES_ATTRIBUTES = {'region', 'ergodic', 'apply_usa_adjustment',
                           'usgs_basin_scaling', 'sigma_mu_epsilon'}

    def __init__(self, region="GLO", ergodic=True, apply_usa_adjustment=False,
                 usgs_basin_scaling=False, sigma_mu_epsilon=0.0):
        assert region in SUPPORTED_REGIONS, "Region %s not supported by %s" \
            % (region, self.__class__.__name__)
        self.region = region
        self.ergodic = ergodic
        self.apply_usa_adjustment = apply_usa_adjustment
        self.usgs_basin_scaling = usgs_basin_scaling
        self.sigma_mu_epsilon = sigma_mu_epsilon
        
        # If running for Cascadia or Japan then z2.5 is needed
        if region in ("CAS", "JPN"):
            self.REQUIRES_SITES_PARAMETERS = \
                self.REQUIRES_SITES_PARAMETERS.union({"z2pt5", })
        
        # USGS basin scaling only used if region is set to Cascadia
        if self.usgs_basin_scaling and self.region != "CAS":
            raise ValueError('USGS basin scaling is only applicable to the '
                             'Cascadia region for AbrahamsonGulerce2020.')

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        trt = self.DEFINED_FOR_TECTONIC_REGION_TYPE
        C_PGA = self.COEFFS[PGA()]
        pga1000 = get_acceleration_on_reference_rock(C_PGA, trt,
                                                     self.region, ctx,
                                                     self.apply_usa_adjustment)
        pga1000 = np.exp(pga1000)

        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]

            # Get USGS basin scaling factor if required (can only be for
            # CAS region)
            if self.usgs_basin_scaling:
                usgs_baf = _get_z2pt5_usgs_basin_scaling(ctx.z2pt5, imt.period)
            else:
                usgs_baf = np.ones(len(ctx.vs30))
            
            mean[m] = get_mean_acceleration(C, trt, self.region, ctx, pga1000, imt,
                                            self.apply_usa_adjustment,
                                            self.usgs_basin_scaling)

            if self.sigma_mu_epsilon:
                # Apply an epistmic adjustment factor
                mean[m] += (self.sigma_mu_epsilon *
                            get_epistemic_adjustment(C, ctx.rrup))
            # Get the standard deviations
            tau_m, phi_m = get_tau_phi(C, C_PGA, self.region, imt.period,
                                       ctx.rrup, ctx.vs30, pga1000,
                                       self.ergodic)
            tau[m] = tau_m
            phi[m] = phi_m
        sig[:] = np.sqrt(tau ** 2.0 + phi ** 2.0)

    # Coefficients taken from digital files supplied by Norm Abrahamson
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    imt     c1i   vlin       b        a1       a2       a6      a7      a8    a10     a11      a12      a13      a14     a16    a17      a18    a19      a20     a21     a22     a23     a24      a25      a26      a27     a28      a29     a30      a31      a32      a33      a34      a35      a36      a37    a39     a41  USA-AK_Adj  CAS_Adj     d1     d2   rhoW   rhoB  phi_s2s_g1  phi_s2s_g2   phi_s2s_g3      e1       e2      e3
    pga    8.20   865.1  -1.186   4.5960  -1.4500  -0.0043  3.2100  0.0440  3.210  0.0070   0.9000   0.0000  -0.4600  0.0900  0.000  -0.2000  0.000   0.0000  0.0400  0.0400  0.0000  0.0015   0.0007   0.0036  -0.0004  0.0025   0.0006  0.0033   3.7783   3.3468   3.8025   5.0361   4.6272   4.8044   3.5669  0.000  -0.029       0.487    0.828  0.325  0.137  1.000  1.000       0.396       0.396        0.545   0.550   -0.270   0.050
    0.010  8.20   865.1  -1.186   4.5960  -1.4500  -0.0043  3.2100  0.0440  3.210  0.0070   0.9000   0.0000  -0.4600  0.0900  0.000  -0.2000  0.000   0.0000  0.0400  0.0400  0.0000  0.0015   0.0007   0.0036  -0.0004  0.0025   0.0006  0.0033   3.7783   3.3468   3.8025   5.0361   4.6272   4.8044   3.5669  0.000  -0.029       0.487    0.828  0.325  0.137  1.000  1.000       0.396       0.396        0.545   0.550   -0.270   0.050
    0.020  8.20   865.1  -1.219   4.6780  -1.4500  -0.0043  3.2100  0.0440  3.210  0.0070   1.0080   0.0000  -0.4600  0.0900  0.000  -0.2000  0.000   0.0000  0.0400  0.0400  0.0000  0.0015   0.0006   0.0036  -0.0005  0.0025   0.0005  0.0033   3.8281   3.4401   3.9053   5.1375   4.6958   4.8943   3.6425  0.000  -0.024       0.519    0.825  0.325  0.137  0.990  0.990       0.396       0.396        0.545   0.550   -0.270   0.050
    0.030  8.20   907.8  -1.273   4.7730  -1.4500  -0.0044  3.2100  0.0440  3.210  0.0070   1.1270   0.0000  -0.4600  0.0900  0.000  -0.2000  0.000   0.0000  0.0400  0.0400  0.0000  0.0015   0.0006   0.0037  -0.0007  0.0025   0.0005  0.0034   3.8933   3.5087   4.0189   5.2699   4.7809   5.0028   3.7063  0.000  -0.034       0.543    0.834  0.325  0.137  0.990  0.990       0.396       0.396        0.545   0.550   -0.270   0.050
    0.050  8.20  1053.5  -1.346   5.0290  -1.4500  -0.0046  3.2100  0.0440  3.210  0.0070   1.3330   0.0000  -0.4600  0.0900  0.000  -0.2000  0.000   0.0000  0.0400  0.0400  0.0000  0.0011   0.0006   0.0039  -0.0009  0.0026   0.0004  0.0036   4.2867   3.6553   4.2952   5.6157   5.0211   5.2819   3.9184  0.000  -0.061       0.435    0.895  0.325  0.137  0.970  0.985       0.396       0.467        0.644   0.560   -0.270   0.050
    0.075  8.20  1085.7  -1.471   5.3340  -1.4500  -0.0047  3.2100  0.0440  3.210  0.0070   1.5650   0.0000  -0.4600  0.0900  0.000  -0.2000  0.000   0.0000  0.0600  0.0600  0.0000  0.0011   0.0004   0.0039  -0.0009  0.0026   0.0003  0.0037   4.5940   3.9799   4.5464   6.0204   5.3474   5.6123   4.2207  0.000  -0.076       0.410    0.863  0.325  0.137  0.950  0.980       0.396       0.516        0.713   0.580   -0.270   0.050
    0.100  8.20  1032.5  -1.624   5.4550  -1.4500  -0.0048  3.2100  0.0440  3.210  0.0070   1.6790   0.0000  -0.4600  0.0900  0.000  -0.2000  0.000   0.0000  0.1000  0.1000  0.0000  0.0012   0.0003   0.0039  -0.0008  0.0026   0.0003  0.0038   4.7077   4.1312   4.6138   6.1625   5.5065   5.7668   4.3536  0.000  -0.049       0.397    0.842  0.325  0.137  0.920  0.970       0.396       0.516        0.713   0.590   -0.270   0.050
    0.150  8.20   877.6  -1.931   5.3760  -1.4250  -0.0047  3.2100  0.0440  3.210  0.0070   1.8530   0.0000  -0.4600  0.0900  0.000  -0.1860  0.000  -0.0550  0.1350  0.1350  0.0690  0.0013  -0.0002   0.0037  -0.0009  0.0022   0.0001  0.0037   4.6065   4.2737   4.5290   5.9614   5.5180   5.7313   4.3664  0.000  -0.026       0.428    0.737  0.325  0.137  0.900  0.960       0.396       0.516        0.647   0.590   -0.270   0.050
    0.200  8.20   748.2  -2.188   4.9360  -1.3350  -0.0045  3.2100  0.0430  3.210  0.0062   2.0220   0.0000  -0.4600  0.0840  0.000  -0.1500  0.000  -0.1050  0.1700  0.1700  0.1400  0.0013  -0.0007   0.0031  -0.0010  0.0018  -0.0001  0.0035   4.1866   3.9650   4.1656   5.3920   5.1668   5.2943   4.0169  0.000  -0.011       0.442    0.746  0.325  0.137  0.870  0.940       0.396       0.516        0.596   0.570   -0.270   0.050
    0.250  8.20   654.3  -2.381   4.6360  -1.2750  -0.0043  3.2100  0.0420  3.210  0.0056   2.1810   0.0000  -0.4600  0.0800  0.000  -0.1400  0.000  -0.1340  0.1700  0.1700  0.1640  0.0013  -0.0009   0.0027  -0.0011  0.0016  -0.0003  0.0033   3.8515   3.6821   3.9147   5.0117   4.8744   5.0058   3.7590  0.101  -0.009       0.494    0.796  0.325  0.137  0.840  0.930       0.396       0.501        0.539   0.530   -0.224   0.043
    0.300  8.20   587.1  -2.518   4.4230  -1.2310  -0.0042  3.2100  0.0410  3.210  0.0051   2.2810  -0.0020  -0.4600  0.0780  0.000  -0.1200  0.000  -0.1500  0.1700  0.1700  0.1900  0.0014  -0.0010   0.0020  -0.0009  0.0014  -0.0002  0.0032   3.5783   3.5415   3.7846   4.7057   4.6544   4.7588   3.5914  0.184   0.005       0.565    0.782  0.325  0.137  0.820  0.910       0.396       0.488        0.488   0.490   -0.186   0.037
    0.400  8.20   503.0  -2.657   4.1240  -1.1650  -0.0040  3.2100  0.0400  3.210  0.0043   2.3790  -0.0070  -0.4700  0.0750  0.000  -0.1000  0.000  -0.1500  0.1700  0.1700  0.2060  0.0015  -0.0010   0.0013  -0.0007  0.0011   0.0000  0.0030   3.2493   3.3256   3.5702   4.2896   4.3660   4.3789   3.3704  0.315   0.040       0.625    0.768  0.325  0.137  0.740  0.860       0.396       0.468        0.468   0.425   -0.126   0.028
    0.500  8.20   456.6  -2.669   3.8380  -1.1150  -0.0037  3.2100  0.0390  3.210  0.0037   2.3390  -0.0110  -0.4800  0.0720  0.000  -0.0800  0.000  -0.1500  0.1700  0.1700  0.2200  0.0015  -0.0011   0.0009  -0.0007  0.0008   0.0002  0.0027   2.9818   3.1334   3.3552   3.9322   4.0779   4.0394   3.1564  0.416   0.097       0.634    0.728  0.325  0.137  0.660  0.800       0.396       0.451        0.451   0.375   -0.079   0.022
    0.600  8.20   430.3  -2.599   3.5620  -1.0710  -0.0035  3.2100  0.0380  3.210  0.0033   2.2170  -0.0150  -0.4900  0.0700  0.000  -0.0600  0.000  -0.1500  0.1700  0.1700  0.2250  0.0015  -0.0012   0.0006  -0.0007  0.0006   0.0002  0.0025   2.7784   2.9215   3.0922   3.6149   3.8146   3.7366   2.9584  0.499   0.145       0.581    0.701  0.325  0.137  0.590  0.780       0.396       0.438        0.438   0.345   -0.041   0.016
    0.750  8.15   410.5  -2.401   3.1520  -1.0200  -0.0032  3.2100  0.0370  3.210  0.0027   1.9460  -0.0210  -0.5000  0.0670  0.000  -0.0470  0.000  -0.1500  0.1700  0.1700  0.2170  0.0014  -0.0011   0.0003  -0.0007  0.0004   0.0002  0.0022   2.4780   2.5380   2.6572   3.1785   3.4391   3.2930   2.6556  0.600   0.197       0.497    0.685  0.325  0.137  0.500  0.730       0.396       0.420        0.420   0.300    0.005   0.009
    1.000  8.10   400.0  -1.955   2.5440  -0.9500  -0.0029  3.2100  0.0350  3.210  0.0019   1.4160  -0.0280  -0.5100  0.0630  0.000  -0.0350  0.000  -0.1500  0.1700  0.1700  0.1850  0.0013  -0.0008   0.0001  -0.0008  0.0002   0.0001  0.0019   1.9252   1.9626   2.1459   2.5722   2.8056   2.6475   2.0667  0.731   0.269       0.469    0.642  0.325  0.137  0.410  0.690       0.396       0.396        0.396   0.240    0.065   0.000
    1.500  8.05   400.0  -1.025   1.6360  -0.8600  -0.0026  3.2100  0.0340  3.210  0.0008   0.3940  -0.0410  -0.5200  0.0590  0.000  -0.0180  0.000  -0.1300  0.1700  0.1700  0.0830  0.0014  -0.0004  -0.0001  -0.0008  0.0001   0.0000  0.0016   0.9924   1.3568   1.3499   1.6499   1.8546   1.6842   1.3316  0.748   0.347       0.509    0.325  0.312  0.113  0.330  0.620       0.379       0.379        0.379   0.230    0.065   0.000
    2.000  8.00   400.0  -0.299   1.0760  -0.8200  -0.0024  3.2100  0.0320  3.210  0.0000  -0.4170  -0.0500  -0.5300  0.0590  0.000  -0.0100  0.000  -0.1100  0.1700  0.1700  0.0450  0.0015   0.0002   0.0000  -0.0007  0.0002   0.0000  0.0014   0.4676   0.8180   0.8148   1.0658   1.3020   1.1002   0.7607  0.761   0.384       0.478    0.257  0.302  0.096  0.300  0.560       0.366       0.366        0.366   0.230    0.065   0.000
    2.500  7.95   400.0   0.000   0.6580  -0.7980  -0.0022  3.2100  0.0310  3.210  0.0000  -0.7250  -0.0570  -0.5400  0.0600  0.000  -0.0050  0.000  -0.0950  0.1700  0.1700  0.0260  0.0014   0.0004   0.0000  -0.0007  0.0002  -0.0002  0.0012   0.0579   0.4389   0.3979   0.6310   0.8017   0.6737   0.3648  0.770   0.397       0.492    0.211  0.295  0.082  0.270  0.520       0.356       0.356        0.356   0.230    0.065   0.000
    3.000  7.90   400.0   0.000   0.4240  -0.7930  -0.0021  3.1300  0.0300  3.130  0.0000  -0.6950  -0.0650  -0.5400  0.0590  0.000   0.0000  0.000  -0.0850  0.1700  0.1700  0.0350  0.0014   0.0007   0.0003  -0.0007  0.0004  -0.0002  0.0011  -0.1391   0.1046   0.1046   0.3882   0.5958   0.4126   0.1688  0.778   0.404       0.470    0.296  0.289  0.072  0.250  0.495       0.348       0.348        0.348   0.240    0.065   0.000
    4.000  7.85   400.0   0.000   0.0930  -0.7930  -0.0020  2.9850  0.0290  2.985  0.0000  -0.6380  -0.0770  -0.5400  0.0500  0.000   0.0000  0.000  -0.0730  0.1700  0.1700  0.0530  0.0014   0.0010   0.0007  -0.0006  0.0006  -0.0002  0.0010  -0.3030  -0.1597  -0.2324   0.0164   0.3522   0.0097  -0.0323  0.790   0.397       0.336    0.232  0.280  0.055  0.220  0.430       0.335       0.335        0.335   0.270    0.065   0.000
    5.000  7.80   400.0   0.000  -0.1450  -0.7930  -0.0020  2.8180  0.0280  2.818  0.0000  -0.5970  -0.0880  -0.5400  0.0430  0.000   0.0000  0.000  -0.0650  0.1700  0.1700  0.0720  0.0014   0.0013   0.0014  -0.0004  0.0008  -0.0001  0.0010  -0.4094  -0.2063  -0.5722  -0.2802   0.1874  -0.2715  -0.1516  0.799   0.378       0.228    0.034  0.273  0.041  0.190  0.400       0.324       0.324        0.324   0.300    0.065   0.000
    6.000  7.80   400.0   0.000  -0.3200  -0.7930  -0.0020  2.6820  0.0270  2.682  0.0000  -0.5610  -0.0980  -0.5400  0.0380  0.000   0.0000  0.000  -0.0600  0.1700  0.1700  0.0860  0.0014   0.0015   0.0015  -0.0003  0.0011   0.0000  0.0010  -0.5010  -0.3223  -0.8631  -0.4822  -0.1243  -0.4591  -0.2217  0.807   0.358       0.151   -0.037  0.267  0.030  0.170  0.370       0.314       0.314        0.314   0.320    0.065   0.000
    7.500  7.80   400.0   0.000  -0.5560  -0.7930  -0.0020  2.5150  0.0260  2.515  0.0000  -0.5300  -0.1100  -0.5400  0.0320  0.000   0.0000  0.000  -0.0550  0.1700  0.1700  0.1150  0.0014   0.0017   0.0015  -0.0002  0.0014   0.0001  0.0010  -0.6209  -0.4223  -1.1773  -0.7566  -0.3316  -0.6822  -0.3338  0.817   0.333       0.051   -0.178  0.259  0.017  0.140  0.320       0.301       0.301        0.301   0.350    0.065   0.000
    10.00  7.80   400.0   0.000  -0.8600  -0.7930  -0.0020  2.3000  0.0250  2.300  0.0000  -0.4860  -0.1270  -0.5400  0.0240  0.000   0.0000  0.000  -0.0450  0.1700  0.1700  0.1510  0.0014   0.0017   0.0015  -0.0001  0.0017   0.0002  0.0010  -0.6221  -0.5909  -1.4070  -1.0870  -0.6783  -0.9173  -0.5441  0.829   0.281      -0.251   -0.313  0.250  0.000  0.100  0.280       0.286       0.286        0.286   0.350    0.065   0.000
    """)


class AbrahamsonGulerce2020SSlab(AbrahamsonGulerce2020SInter):
    """
    Implements the 2020 Subduction ground motion model of Abrahamson &
    Gulerce (2020) for subduction in-slab earthquakes

    Abrahamson N. and Gulurce Z. (2020) "Regionalized Ground-Motion Models
    for Subduction Earthquakes based on the NGA-SUB Database", Pacific
    Earthquake Engineering Research Center (PEER) Technical Report,
    PEER 2020/25
    """
    #: Required rupture parameters are magnitude and top-of-rupture depth
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'ztor'}

    #: Supported tectonic region type is subduction inslab
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB


# Long form regional aliases
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
    add_alias("AbrahamsonGulerce2020SInter" + REGION_ALIASES[region],
              AbrahamsonGulerce2020SInter,
              region=region)
    add_alias("AbrahamsonGulerce2020SSlab" + REGION_ALIASES[region],
              AbrahamsonGulerce2020SSlab,
              region=region)
