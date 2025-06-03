# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2025 GEM Foundation
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
Module exports :class:`ChiouYoungs2014`
               :class:`ChiouYoungs2014PEER`
               :class:`ChiouYoungs2014NearFaultEffect`
"""
import os
import pathlib
import numpy as np

from openquake.baselib.general import CallableDict
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable, add_alias
from openquake.hazardlib.gsim.abrahamson_2014 import get_epistemic_sigma
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA
from openquake.hazardlib.gsim.utils_usgs_basin_scaling import \
    _get_z1pt0_usgs_basin_scaling


CONSTANTS = {"c2": 1.06, "c4": -2.1, "c4a": -0.5, "crb": 50.0,
             "c8a": 0.2695, "c11": 0.0, "phi6": 300.0, "phi6jp": 800.0}


# CyberShake basin adjustments for CY14 (only applied above 
# 1.9 seconds so don't provide dummy values listed below 2 s)
# Taken from https://code.usgs.gov/ghsc/nshmp/nshmp-lib/-/blob/main/src/main/resources/gmm/coeffs/CY14.csv?ref_type=heads
COEFFS_CY = CoeffsTable(sa_damping=5, table="""\
IMT   phi5cy   phi6cy   
2     0.244    1000
3     0.262    608
4     0.819    1000
5     1.085    1000
7.5   1.365    1000
10    1.234    1000
""")


def japan_mean_z1pt0(vs30):
    """
    Return z1pt0 based on Japan region CY14 relationship
    """
    return (-5.23 / 2.) * np.log(((
        vs30 ** 2.) + 412.39 ** 2.) / (1360 ** 2. + 412.39 ** 2.))


def global_mean_z1pt0(vs30):
    """
    Return z1pt0 based on non-Japan region CY14 relationship
    """
    return (-7.15 / 4.) * np.log((
        (vs30) ** 4. + 570.94 ** 4.) / (1360 ** 4. + 570.94 ** 4.))


def _get_centered_z1pt0(region, vs30, z1pt0):
    """
    Get z1pt0 centered on the Vs30- dependent average z1pt0(m)
    California and non-Japan regions
    """
    if region == "JPN":
        mean_z1pt0 = japan_mean_z1pt0(vs30)
        return z1pt0 - np.exp(mean_z1pt0)

    else:
        mean_z1pt0 = global_mean_z1pt0(vs30)
        return z1pt0 - np.exp(mean_z1pt0)


def _get_centered_ztor(ctx):
    """
    Get ztor centered on the M- dependent avarage ztor(km)
    by different fault types.
    """
    # Strike-slip and normal faulting
    mean_ztor = np.clip(2.673 - 1.136 * np.clip(ctx.mag - 4.970, 0., None),
                        0., None) ** 2
    # Reverse and reverse-oblique faulting
    rev = (30. <= ctx.rake) & (ctx.rake <= 150.)
    mean_ztor[rev] = np.clip(2.704 - 1.226 * np.clip(
        ctx.mag[rev] - 5.849, 0.0, None), 0., None) ** 2
    return ctx.ztor - mean_ztor


def _get_ln_y_ref(ctx, C):
    """
    Get an intensity on a reference soil.
    Implements eq. 13a.
    """
    # Reverse faulting flag
    Frv = 1. if 30 <= ctx.rake <= 150 else 0.
    # Normal faulting flag
    Fnm = 1. if -120 <= ctx.rake <= -60 else 0.
    # A part in eq. 11
    mag_test1 = np.cosh(2. * np.clip(ctx.mag - 4.5, 0., None))
    # Centered DPP
    centered_dpp = 0
    # Centered Ztor
    centered_ztor = 0

    dist_taper = np.fmax(1 - (np.fmax(ctx.rrup - 40,
                              np.zeros_like(ctx)) / 30.),
                         np.zeros_like(ctx))
    dist_taper = dist_taper.astype(np.float64)
    ln_y_ref = (
        # first part of eq. 11
        C['c1']
        + (C['c1a'] + C['c1c'] / mag_test1) * Frv
        + (C['c1b'] + C['c1d'] / mag_test1) * Fnm
        + (C['c7'] + C['c7b'] / mag_test1) * centered_ztor
        + (C['c11'] + C['c11b'] / mag_test1) *
        np.cos(np.radians(ctx.dip)) ** 2
        # second part
        + C['c2'] * (ctx.mag - 6)
        + ((C['c2'] - C['c3']) / C['cn'])
        * np.log(1 + np.exp(C['cn'] * (C['cm'] - ctx.mag)))
        # third part
        + C['c4']
        * np.log(ctx.rrup + C['c5']
                 * np.cosh(C['c6'] * np.clip(ctx.mag - C['chm'], 0, None)))
        + (C['c4a'] - C['c4'])
        * np.log(np.sqrt(ctx.rrup ** 2 + C['crb'] ** 2))
        # forth part
        + (C['cg1'] + C['cg2'] / (
            np.cosh(np.clip(ctx.mag - C['cg3'], 0, None))))
        * ctx.rrup
        # fifth part
        + C['c8'] * dist_taper
        * np.clip((ctx.mag - 5.5, 0) / 0.8, 0., 1.)
        * np.exp(-1 * C['c8a'] * (ctx.mag - C['c8b']) ** 2) * centered_dpp
        # sixth part
        # + C['c9'] * Fhw * np.cos(math.radians(ctx.dip)) *
        # (C['c9a'] + (1 - C['c9a']) * np.tanh(ctx.rx / C['c9b']))
        # * (1 - np.sqrt(ctx.rjb ** 2 + ctx.ztor ** 2)
        #   / (ctx.rrup + 1.0))
    )
    return ln_y_ref


def _get_mean(ctx, C, ln_y_ref, exp1, exp2):
    """
    Add site effects to an intensity. Implements eq. 13b.
    """
    eta = epsilon = 0.
    ln_y = (
        # first line of eq. 12
        ln_y_ref + eta
        # second line
        + C['phi1'] * np.log(ctx.vs30 / 1130).clip(-np.inf, 0)
        # third line
        + C['phi2'] * (exp1 - exp2)
        * np.log((np.exp(ln_y_ref) * np.exp(eta) + C['phi4']) / C['phi4'])
        # fourth line - removed
        # fifth line
        + epsilon)
    return ln_y


def _get_basin_term(C, ctx, region, imt, usgs_bs=False, cy=False):
    """
    Returns the basin depth scaling
    """
    z1pt0 = ctx.z1pt0.copy()

    # Use GMMs vs30 to z1pt0 for non-measured values
    mask = z1pt0 == -999
    if region == "JPN":
        z1pt0[mask] = np.exp(japan_mean_z1pt0(ctx.vs30[mask]))
    else:
        z1pt0[mask] = np.exp(global_mean_z1pt0(ctx.vs30[mask]))

    # Get USGS basin scaling factor if required
    if usgs_bs:
        usgs_baf = _get_z1pt0_usgs_basin_scaling(z1pt0, imt.period)
    else:
        usgs_baf = np.ones(len(ctx.vs30))

    # Get basin depth
    dz1pt0 = _get_centered_z1pt0(region, ctx.vs30, z1pt0)

    # for Z1.0 = 0.0 no deep soil correction is applied
    dz1pt0[z1pt0 <= 0.0] = 0.0
    if region == "JPN":
        return C["phi5jp"] * (1.0 - np.exp(-dz1pt0 / CONSTANTS["phi6jp"]))

    # Apply cybershake adjustment if specified and SA(T > 1.9)
    if cy and imt.period > 1.9:
        phi5 = COEFFS_CY[imt]["phi5cy"]
        phi6 = COEFFS_CY[imt]["phi6cy"]
        adj = 0.1 # CY_CSIM variable in java code
    else:
        phi5 = C["phi5"]
        phi6 = CONSTANTS["phi6"]
        adj = 0.
    
    fb = (phi5 * (1.0 - np.exp(-dz1pt0 / phi6))) + adj

    return fb * usgs_baf


def get_directivity(C, ctx):
    """
    Returns the directivity term, if any.

    The directivity prediction parameter is centered on the average
    directivity prediction parameter. Here we set the centered_dpp
    equal to zero, since the near fault directivity effect prediction is
    off by default in our calculation.
    """    
    try:
        cdpp =  ctx.rcdpp
    except AttributeError:
        # No directivity term
        return 0.
    f_dir = np.exp(-C["c8a"] * ((ctx.mag - C["c8b"]) ** 2.)) * cdpp
    f_dir *= np.clip((ctx.mag - 5.5) / 0.8, 0., 1.)
    rrup_max = ctx.rrup - 40.
    rrup_max[rrup_max < 0.0] = 0.0
    rrup_max = 1.0 - (rrup_max / 30.)
    rrup_max[rrup_max < 0.0] = 0.0
    return C["c8"] * rrup_max * f_dir


get_far_field_distance_scaling = CallableDict()


@get_far_field_distance_scaling.add("CAL")
def get_far_field_distance_scaling_1(region, C, mag, rrup, delta_g):
    """
    Returns the far-field distance scaling term - both magnitude and
    distance - for California and other regions
    """
    # Get the attenuation distance scaling (geometric spreading term)
    f_r = (CONSTANTS["c4a"] - CONSTANTS["c4"]) * np.log(
        np.sqrt(rrup ** 2. + CONSTANTS["crb"] ** 2.))
    
    # Get the magnitude dependent term
    gamma = C["cg1"] + C["cg2"] / np.cosh(np.clip(mag - C["cg3"], 0.0, None))
    
    # Adjust path if delta_g (from Boore et al. 2022 CY14 adjustments paper)
    f_rm = (gamma + delta_g) * rrup
    
    return f_r + f_rm


@get_far_field_distance_scaling.add("JPN")
def get_far_field_distance_scaling_2(region, C, mag, rrup, delta_g):
    """
    Returns the far-field distance scaling term - both magnitude and
    distance - for Japan
    """
    # Get the attenuation distance scaling (geometric spreading term)
    f_r = (CONSTANTS["c4a"] - CONSTANTS["c4"]) * np.log(
        np.sqrt(rrup ** 2. + CONSTANTS["crb"] ** 2.))

    # Get the magnitude dependent term
    gamma = (C["cg1"] + C["cg2"] / np.cosh(np.clip(mag - C["cg3"], 0.0, None)))
    
    # Adjust path if delta_g (from Boore et al. 2022 CY14 adjustments paper)
    f_rm = (gamma + delta_g) * rrup
    
    # Apply adjustment factor for Japan
    f_rm[(mag > 6.0) & (mag < 6.9)] *= C["gjpit"]
    
    return f_r + f_rm


@get_far_field_distance_scaling.add("ITA")
def get_far_field_distance_scaling_3(region, C, mag, rrup, delta_g):
    """
    Returns the far-field distance scaling term - both magnitude and
    distance - for Italy
    """
    # Get the attenuation distance scaling (geometric spreading term)
    f_r = (CONSTANTS["c4a"] - CONSTANTS["c4"]) * np.log(
        np.sqrt(rrup ** 2. + CONSTANTS["crb"] ** 2.))

    # Get the magnitude dependent term
    gamma = (C["cg1"] + C["cg2"] / np.cosh(np.clip(mag - C["cg3"], 0.0, None)))
    
    # Adjust path if delta_g (from Boore et al. 2022 CY14 adjustments paper)
    f_rm = (gamma + delta_g) * rrup
    
    # Apply adjustment factor for Italy
    f_rm[(mag > 6.0) & (mag < 6.9)] *= C["gjpit"]
    
    return f_r + f_rm


@get_far_field_distance_scaling.add("WEN")
def get_far_field_distance_scaling_4(region, C, mag, rrup, delta_g):
    """
    Returns the far-field distance scaling term - both magnitude and
    distance - for Wenchuan
    """
    # Get the attenuation distance scaling (geometric spreading term)
    f_r = (CONSTANTS["c4a"] - CONSTANTS["c4"]) * np.log(
        np.sqrt(rrup ** 2. + CONSTANTS["crb"] ** 2.))

    # Get the magnitude dependent term
    gamma = (C["cg1"] + C["cg2"] / np.cosh(np.clip(mag - C["cg3"], 0.0, None)))
    
    # Adjust path if delta_g (from Boore et al. 2022 CY14 adjustments paper)
    f_rm = (gamma + delta_g) * rrup
    
    # Apply adjustment factor for Wenchuan
    return f_r + (f_rm * C["gwn"])


def get_geometric_spreading(C, mag, rrup):
    """
    Returns the near-field geometric spreading term
    """
    # Get the near-field magnitude scaling
    return CONSTANTS["c4"] * np.log(
        rrup + C["c5"] * np.cosh(C["c6"] * np.clip(mag - C["chm"], 0.0, None)))


def get_hanging_wall_term(C, ctx):
    """
    Returns the hanging wall term
    """
    fhw = np.zeros(ctx.rrup.shape)
    idx = ctx.rx >= 0.0
    if np.any(idx):
        fdist = 1.0 - (np.sqrt(ctx.rjb[idx] ** 2. + ctx.ztor[idx] ** 2.) /
                       (ctx.rrup[idx] + 1.0))
        fdist *= C["c9a"] + (1.0 - C["c9a"]) * np.tanh(ctx.rx[idx] / C["c9b"])
        fhw[idx] += C["c9"] * np.cos(np.radians(ctx.dip[idx])) * fdist
    return fhw


def get_linear_site_term(region, C, ctx):
    """
    Returns the linear site scaling term
    """
    if region == "JPN":
        return C["phi1jp"] * np.log(ctx.vs30 / 1130).clip(-np.inf, 0.0)
    return C["phi1"] * np.log(ctx.vs30 / 1130).clip(-np.inf, 0.0)

    
def get_delta_c1(rrup, imt, mag):
    """
    Return the delta_c1 long-period adjustment parameter as defined by equation
    2 of Boore et al.(2022).
    """
    # Initialise output
    delta_c1 = np.zeros_like(mag)

    # Apply correction only to 'PGA'
    if str(imt) != 'PGA':

        # Computing tB, the period below which the correction do not apply
        tb = 2 - np.maximum(0, mag-7)

        # Apply correction only if period is larger than tb
        idx = float(imt.period) > tb
        if np.any(idx):

            # Equations 3b, 3c and 3d
            s1 = 0.2704 - 0.0694 * np.maximum(mag[idx]-7, 0)
            s2 = -0.1342 + 0.0716 * np.maximum(mag[idx]-7, 0)
            s3 = 0.2513 - 0.0419 * np.maximum(mag[idx]-7, 0)

            # Equation 3a - Note that we add a capping to rrup to avoid an
            # overflow
            dst = rrup[idx]
            dst[dst>100] = 100
            s = s1 + s2 / np.cosh(s3 * dst)

            # Equation 2
            delta_c1[idx] = s * np.maximum(
                np.log(float(imt.period)/tb[idx]), 0)**2

    return delta_c1
    

def _get_delta_cm(conf, imt):
    """
    Return the delta_cm parameter as defined by equation A19 in Boore et al.
    (2022) for the host-to-target region source-scaling adjustment. 
    """
    # If the stress parameters are not defined at the instantiation level, the
    # conf dictionary does not contain the source_function_table
    source_function_table = conf.get('source_function_table', None)
    
    # Get stress params
    stress_par_host = conf.get('stress_par_host')
    stress_par_targ = conf.get('stress_par_target')
    C = source_function_table[imt]

    # Compute chi
    if stress_par_targ > stress_par_host:
        chi = C['chi_delta_pos']
    else:
        chi = C['chi_delta_neg']

    # Compute delta_cm
    delta_cm = chi * 2/3 * np.log10(stress_par_targ / stress_par_host)

    return delta_cm


def _get_delta_g(delta_gamma_tab, ctx, imt):
    """
    Returns the delta_g parameter as defined by equation 13 in Boore et al.
    (2022) for the host-to-target region path adjustment
    """
    # Get coefficients for imt
    C = delta_gamma_tab[imt]
    
    # Compute delta_g (magnitude-dependent)
    delta_g = C['c0'] + C['c1']*(ctx.mag - 6) + C['c2']*(
        ctx.mag - 6)**2 + C['c3']*(ctx.mag - 6)**3
    
    return delta_g
    

def get_ln_y_ref(region, C, ctx, conf):
    """
    Returns the ground motion on the reference rock, described fully by
    Equation 11 in CY14 (page 1131).
    """
    # Read configuration parameters
    imt = conf.get('imt')
    add_delta_c1 = conf.get('add_delta_c1')
    use_hw = conf.get('use_hw')
    alpha_nm = conf.get('alpha_nm')

    # Get the region name from the name of the class
    delta_ztor = _get_centered_ztor(ctx)

    # If stress correction required get delta cm
    delta_cm = 0
    if 'source_function_table' in conf:
        delta_cm = _get_delta_cm(conf, imt)

    # If path correction required get delta g
    delta_g = 0
    if 'delta_gamma_tab' in conf:
        delta_g = _get_delta_g(conf['delta_gamma_tab'], ctx, imt)

    # Compute median ground motion:
    # - The `get_magnitude_scaling` function when `delta_cm` ≠ 0 applies a
    #   correction to ground motion that accounts for the differences in the
    #   stress parameter between the host and target region as described in
    #   Boore at al. (2022)
    # - The `get_source_scaling_terms` function applies a correction to
    #   ground motion for the style of faulting as per Boore et al. (2022;
    #   eq. 5). The `alpha_nm` is provided at the instantiation level.
    # - The `get_far_field_distance_scaling` function applies a correction to
    #   ground motion for anelastic attenuation as per Boore et al. (2022)
    out = (get_stress_scaling(C) +
           get_magnitude_scaling(C, ctx.mag, delta_cm) +
           get_source_scaling_terms(C, ctx, delta_ztor, alpha_nm) +
           get_geometric_spreading(C, ctx.mag, ctx.rrup) +
           get_far_field_distance_scaling(
               region, C, ctx.mag, ctx.rrup, delta_g) +
           get_directivity(C, ctx))

    # Adjust ground-motion for the hanging wall effect
    if use_hw:
        out += get_hanging_wall_term(C, ctx)

    # Long period adjustment as per Boore et al. (2022; see equation 4)
    if add_delta_c1:
        out += get_delta_c1(ctx.rrup, imt, ctx.mag)

    return out


def get_magnitude_scaling(C, mag, delta_cm):
    """
    Returns the magnitude scaling
    """
    f_m = np.zeros_like(mag)
    f_m = np.log(1.0 + np.exp(C["cn"] * (C["cm"] + delta_cm - mag)))
    f_m = (CONSTANTS["c2"] * (mag - 6.0) +
           ((CONSTANTS["c2"] - C["c3"]) / C["cn"]) * f_m -
           (CONSTANTS["c2"] - C["c3"]) * delta_cm)
    return f_m


def get_nonlinear_site_term(C, ctx, y_ref):
    """
    Returns the nonlinear site term and the Vs-scaling factor (to be
    used in the standard deviation model
    """
    vs = ctx.vs30.clip(-np.inf, 1130.0)
    f_nl_scaling = C["phi2"] * (np.exp(C["phi3"] * (vs - 360.)) -
                                np.exp(C["phi3"] * (1130. - 360.)))
    f_nl = np.log((y_ref + C["phi4"]) / C["phi4"]) * f_nl_scaling
    return f_nl, f_nl_scaling


def get_phi(C, mag, ctx, nl0):
    """
    Returns the within-event variability described in equation 13, line 3
    """
    phi = C["sig3"] * np.ones(ctx.vs30.shape)
    phi[ctx.vs30measured] = 0.7
    phi = np.sqrt(phi + ((1.0 + nl0) ** 2.))
    mdep = C["sig1"] + (
        C["sig2"] - C["sig1"]) * np.clip(mag - 5., 0., 1.5) / 1.5
    return mdep * phi


def get_source_scaling_terms(C, ctx, delta_ztor, alpha_nm):
    """
    Returns additional source scaling parameters related to style of
    faulting, dip and top of rupture depth
    """
    f_src = np.zeros_like(ctx.mag)
    coshm = np.cosh(2.0 * np.clip(ctx.mag - 4.5, 0., None))

    # Style of faulting term
    pos = (30 <= ctx.rake) & (ctx.rake <= 150)
    neg = (-120 <= ctx.rake) & (ctx.rake <= -60)

    # reverse faulting flag
    f_src[pos] += C["c1a"] + (C["c1c"] / coshm[pos])

    # normal faulting flag
    f_src[neg] += (C["c1b"] + (C["c1d"] / coshm[neg])) * alpha_nm

    # Top of rupture term
    f_src += (C["c7"] + (C["c7b"] / coshm)) * delta_ztor

    # Dip term
    f_src += ((CONSTANTS["c11"] + (C["c11b"] / coshm)) *
              np.cos(np.radians(ctx.dip)) ** 2.0)
    return f_src


def get_stddevs(peer, C, ctx, mag, y_ref, f_nl_scaling):
    """
    Returns the standard deviation model described in equation 13
    """
    if peer:
        # the standard deviation, which is fixed at 0.65 for every site
        return [0.65 * np.ones_like(ctx.vs30), 0, 0]

    # Determines the nonlinear term described in equation 13, line 4
    nl0 = f_nl_scaling * (y_ref / (y_ref + C["phi4"]))
    # Get between and within-event variability
    tau = get_tau(C, mag)
    phi_nl0 = get_phi(C, mag, ctx, nl0)
    # Get total standard deviation propagating the uncertainty in the
    # nonlinear amplification term
    sigma = np.sqrt(((1.0 + nl0) ** 2.) * (tau ** 2.) + phi_nl0 ** 2.)
    return [sigma, np.abs((1 + nl0) * tau), phi_nl0]


def get_stress_scaling(C):
    """
    Returns the stress drop scaling factor
    """
    return C["c1"]


def get_tau(C, mag):
    """
    Returns the between-event variability described in equation 13, line 2
    """
    # eq. 13 to calculate inter-event standard error
    mag_test = np.clip(mag - 5.0, 0., 1.5)
    return C['tau1'] + (C['tau2'] - C['tau1']) / 1.5 * mag_test


def get_mean_stddevs(region, C, ctx, imt, conf, usgs_bs=False, cy=False):
    """
    Return mean and standard deviation values
    """
    # Get ground motion on reference rock
    ln_y_ref = get_ln_y_ref(region, C, ctx, conf)
    y_ref = np.exp(ln_y_ref)

    # Get basin term
    f_z1pt0 = _get_basin_term(C, ctx, region, imt, usgs_bs, cy)

    # Get linear amplification term
    f_lin = get_linear_site_term(region, C, ctx)

    # Get nonlinear amplification term
    f_nl, f_nl_scaling = get_nonlinear_site_term(C, ctx, y_ref)

    # Add on the site amplification
    mean = ln_y_ref + (f_lin + f_nl + f_z1pt0)

    # Get standard deviations
    sig, tau, phi = get_stddevs(
        conf['peer'], C, ctx, ctx.mag, y_ref, f_nl_scaling)

    return mean, sig, tau, phi


class ChiouYoungs2014(GMPE):
    """
    Implements GMPE developed by Brian S.-J. Chiou and Robert R. Youngs.

    Chiou, B. S.-J. and Youngs, R. R. (2014), "Update of the Chiou and Youngs
    NGA Model for the Average Horizontal Component of Peak Ground Motion and
    Response Spectra, Earthquake Spectra, 30(3), 1117 - 1153,
    DOI: 10.1193/072813EQS219M
    
    :param sigma_mu_epsilon:
        Epsilon for the statistical uncertainty term.
    :param use_hw:
        Bool which if true turns on the hanging-wall effect.
    :poram add_delta_c1:
        Long-period adjustment parameter as described in Boore et al. (2022)
        backbone paper.
    :param alpha_nm:
        Style-of-faulting correction for normal-faulting as described in Boore
        et al. (2022) backbone paper. This correction is magnitude independent.
    :param stress_par_host:
        Stress parameter for the host-region in bars. Used in Boore et al.
        (2022) backbone methodology.
    :param stress_par_target:
        Stress parameter for the target-region in bars. Used in Boore et
        al. (2022) backbone methodology.
    :param delta_gamma_tab:
        Filename containing path adjustments as described in Boore et al.
        (2022) backbone paper.
    """
    adapted = False  # Overridden in acme_2019

    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are spectral acceleration,
    #: peak ground velocity and peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    #: Supported intensity measure component is orientation-independent
    #: measure :attr:`~openquake.hazardlib.const.IMC.RotD50`,
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see chapter "Variance model".
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Required site parameters are Vs30, Vs30 measured flag
    #: and Z1.0.
    REQUIRES_SITES_PARAMETERS = {'vs30', 'vs30measured', 'z1pt0'}

    #: Required rupture parameters are magnitude, rake,
    #: dip and ztor.
    REQUIRES_RUPTURE_PARAMETERS = {'dip', 'rake', 'mag', 'ztor'}

    #: Required distance measures are RRup, Rjb and Rx.
    REQUIRES_DISTANCES = {'rrup', 'rjb', 'rx'}

    #: Reference shear wave velocity
    DEFINED_FOR_REFERENCE_VELOCITY = 1130
        
    def __init__(self, region='CAL', sigma_mu_epsilon=0.0, use_hw=True,
                 add_delta_c1=False, alpha_nm=1.0, stress_par_host=None,
                 stress_par_target=None, delta_gamma_tab=None,
                 usgs_basin_scaling=False, cybershake_basin_adj=False):

        # set region
        self.region = region

        # set sigma_mu_epsilon 
        self.sigma_mu_epsilon = sigma_mu_epsilon

        # set the conf dictionary
        self.conf = {}
        self.conf['peer'] = self.__class__.__name__.endswith('PEER')
        self.conf['use_hw'] = use_hw 
        self.conf['alpha_nm'] = alpha_nm
        self.conf['add_delta_c1'] = add_delta_c1
        self.conf['stress_par_host'] = stress_par_host
        self.conf['stress_par_target'] = stress_par_target
        
        # The file with the `source function table` has a structure similar to
        # a traditional coefficient table. The columns in the `source function
        # table` are:
        # - IMT             the intensity measure type (either PGA or SA)
        # - S1FS            param
        # - S1RS            param
        # - S2FS            param
        # - S2RS            param
        # - chi             i.e. χFS2RS in equation 6
        if stress_par_target is not None:
            cwd = pathlib.Path(__file__).parent.resolve()
            fname = os.path.join('chiou_youngs_2014',
                                 'source_function_table.txt')
            fpath = os.path.join(cwd, fname)
            with open(fpath, encoding='utf8') as f:
                tmp = f.read()
            self.conf['source_function_table'] = CoeffsTable(
                sa_damping=5, table=tmp)

        # The file with the `path adjustment table` also has a structure which
        # is similar to traditional coefficient table. The columns in the `path
        # adjustment table` are:
        # - IMT             the intensity measure type (either PGA or SA)
        # - c0              param
        # - c1              param
        # - c2              param
        # - c3              param
        if delta_gamma_tab is not None:
            with open(delta_gamma_tab, encoding='utf8') as f:
                tmp = f.read()
            self.conf['delta_gamma_tab'] = CoeffsTable(sa_damping=5, table=tmp)

        # USGS basin scaling
        self.usgs_basin_scaling = usgs_basin_scaling

        # CyberShake basin adj
        self.cybershake_basin_adj = cybershake_basin_adj

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        # Reference to page 1144, PSA might need PGA value
        self.conf['imt'] = PGA()
        pga_mean, pga_sig, pga_tau, pga_phi = get_mean_stddevs(
            self.region, self.COEFFS[PGA()], ctx, PGA(), self.conf,
            self.usgs_basin_scaling, self.cybershake_basin_adj)
        # compute
        for m, imt in enumerate(imts):
            self.conf['imt'] = imt
            if repr(imt) == "PGA":
                mean[m] = pga_mean
                mean[m] += (self.sigma_mu_epsilon*get_epistemic_sigma(ctx))
                sig[m], tau[m], phi[m] = pga_sig, pga_tau, pga_phi
            else:
                imt_mean, imt_sig, imt_tau, imt_phi = get_mean_stddevs(
                    self.region, self.COEFFS[imt], ctx, imt, self.conf,
                    self.usgs_basin_scaling, self.cybershake_basin_adj)
                # Reference to page 1144
                # Predicted PSA value at T ≤ 0.3s should be set equal to the
                # value of PGA when it falls below the predicted PGA
                mean[m] = np.where(imt_mean < pga_mean, pga_mean, imt_mean) \
                    if repr(imt).startswith("SA") and imt.period <= 0.3 \
                    else imt_mean
                mean[m] += (self.sigma_mu_epsilon*get_epistemic_sigma(ctx))

                sig[m], tau[m], phi[m] = imt_sig, imt_tau, imt_phi

    #: Coefficient tables are constructed from values in tables 1 - 5
    COEFFS = CoeffsTable(sa_damping=5, table="""\
IMT     c1      c1a     c1b     c1c     c1d     cn      cm    c2      c3    c4     c4a  crb   c5      chm     c6      c7      c7b     c8     c8a    c8b       c9     c9a    c9b     c11      c11b        cg1        cg2       cg3     phi1       phi2      phi3     phi4     phi5   phi6  gjpit  gwn      phi1jp  phi5jp   phi6jp     tau1     tau2    sig1    sig2    sig3    sig2jp
pga   -1.5065  0.165  -0.255  -0.165  0.255  16.0875  4.9993  1.06  1.9636  -2.1  -0.5  50  6.4551  3.0956  0.4908  0.0352   0.0462  0.     0.2695  0.4833  0.9228  0.1202  6.8607  0.      -0.4536    -0.007146  -0.006758  4.2542  -0.521   -0.1417   -0.00701   0.102151  0.     300  1.5817  0.7594  -0.6846  0.459    800.        0.4     0.26    0.4912  0.3762  0.8     0.4528
pgv    2.3549  0.165  -0.0626 -0.165  0.0626  3.3024  5.423   1.06  2.3152  -2.1  -0.5  50  5.8096  3.0514  0.4407  0.0324   0.0097  0.2154 0.2695  5.      0.3079  0.1     6.5     0       -0.3834    -0.001852  -0.007403  4.3439  -0.7936  -0.0699   -0.008444  5.41      0.0202 300. 2.2306  0.335   -0.7966  0.9488   800.        0.3894  0.2578  0.4785  0.3629  0.7504  0.3918
0.01  -1.5065  0.165  -0.255  -0.165  0.255  16.0875  4.9993  1.06  1.9636  -2.1  -0.5  50  6.4551  3.0956  0.4908  0.0352   0.0462  0.     0.2695  0.4833  0.9228  0.1202  6.8607  0.      -0.4536    -0.007146  -0.006758  4.2542  -0.521   -0.1417   -0.00701   0.102151  0.     300  1.5817  0.7594  -0.6846  0.459    800.        0.4     0.26    0.4912  0.3762  0.8     0.4528
0.02  -1.4798  0.165  -0.255  -0.165  0.255  15.7118  4.9993  1.06  1.9636  -2.1  -0.5  50  6.4551  3.0963  0.4925  0.0352   0.0472  0.     0.2695  1.2144  0.9296  0.1217  6.8697  0.      -0.4536    -0.007249  -0.006758  4.2386  -0.5055  -0.1364   -0.007279  0.10836   0.     300  1.574   0.7606  -0.6681  0.458    800.        0.4026  0.2637  0.4904  0.3762  0.8     0.4551
0.03  -1.2972  0.165  -0.255  -0.165  0.255  15.8819  4.9993  1.06  1.9636  -2.1  -0.5  50  6.4551  3.0974  0.4992  0.0352   0.0533  0.     0.2695  1.6421  0.9396  0.1194  6.9113  0.      -0.4536    -0.007869  -0.006758  4.2519  -0.4368  -0.1403   -0.007354  0.119888  0.     300  1.5544  0.7642  -0.6314  0.462    800.        0.4063  0.2689  0.4988  0.3849  0.8     0.4571
0.04  -1.1007  0.165  -0.255  -0.165  0.255  16.4556  4.9993  1.06  1.9636  -2.1  -0.5  50  6.4551  3.0988  0.5037  0.0352   0.0596  0.     0.2695  1.9456  0.9661  0.1166  7.0271  0.      -0.4536    -0.008316  -0.006758  4.296   -0.3752  -0.1591   -0.006977  0.133641  0.     300  1.5502  0.7676  -0.5855  0.453    800.        0.4095  0.2736  0.5049  0.391   0.8     0.4642
0.05  -0.9292  0.165  -0.255  -0.165  0.255  17.6453  4.9993  1.06  1.9636  -2.1  -0.5  50  6.4551  3.1011  0.5048  0.0352   0.0639  0.     0.2695  2.181   0.9794  0.1176  7.0959  0.      -0.4536    -0.008743  -0.006758  4.3578  -0.3469  -0.1862   -0.006467  0.148927  0.     300  1.5391  0.7739  -0.5457  0.436    800.        0.4124  0.2777  0.5096  0.3957  0.8     0.4716
0.075 -0.658   0.165  -0.254  -0.165  0.254  20.1772  5.0031  1.06  1.9636  -2.1  -0.5  50  6.4551  3.1094  0.5048  0.0352   0.063   0.     0.2695  2.6087  1.026   0.1171  7.3298  0.      -0.4536    -0.009537  -0.00619   4.5455  -0.3747  -0.2538   -0.005734  0.190596  0.     300  1.4804  0.7956  -0.4685  0.383    800.        0.4179  0.2855  0.5179  0.4043  0.8     0.5022
0.1   -0.5613  0.165  -0.253  -0.165  0.253  19.9992  5.0172  1.06  1.9636  -2.1  -0.5  50  6.8305  3.2381  0.5048  0.0352   0.0532  0.     0.2695  2.9122  1.0177  0.1146  7.2588  0.      -0.4536    -0.00983   -0.005332  4.7603  -0.444   -0.2943   -0.005604  0.230662  0.     300  1.4094  0.7932  -0.4985  0.375    800.        0.4219  0.2913  0.5236  0.4104  0.8     0.523
0.12  -0.5342  0.165  -0.252  -0.165  0.252  18.7106  5.0315  1.06  1.9795  -2.1  -0.5  50  7.1333  3.3407  0.5048  0.0352   0.0452  0.     0.2695  3.1045  1.0008  0.1128  7.2372  0.      -0.4536    -0.009913  -0.004732  4.8963  -0.4895  -0.3077   -0.005696  0.253169  0.     300  1.3682  0.7768  -0.5603  0.377    800.        0.4244  0.2949  0.527   0.4143  0.8     0.5278
0.15  -0.5462  0.165  -0.25   -0.165  0.25   16.6246  5.0547  1.06  2.0362  -2.1  -0.5  50  7.3621  3.43    0.5045  0.0352   0.0345  0.     0.2695  3.3399  0.9801  0.1106  7.2109  0.      -0.4536    -0.009896  -0.003806  5.0644  -0.5477  -0.3113   -0.005845  0.266468  0.     300  1.3241  0.7437  -0.6451  0.379    800.        0.4275  0.2993  0.5308  0.4191  0.8     0.5304
0.17  -0.5858  0.165  -0.248  -0.165  0.248  15.3709  5.0704  1.06  2.0823  -2.1  -0.5  50  7.4365  3.4688  0.5036  0.0352   0.0283  0.     0.2695  3.4719  0.9652  0.115   7.2491  0.      -0.4536    -0.009787  -0.00328   5.1371  -0.5922  -0.3062   -0.005959  0.26506   0.     300  1.3071  0.7219  -0.6981  0.38     800.        0.4292  0.3017  0.5328  0.4217  0.8     0.531
0.2   -0.6798  0.165  -0.2449 -0.165  0.2449 13.7012  5.0939  1.06  2.1521  -2.1  -0.5  50  7.4972  3.5146  0.5016  0.0352   0.0202  0.     0.2695  3.6434  0.9459  0.1208  7.2988  0.      -0.444     -0.009505  -0.00269   5.188   -0.6693  -0.2927   -0.006141  0.255253  0.     300  1.2931  0.6922  -0.7653  0.384    800.        0.4313  0.3047  0.5351  0.4252  0.8     0.5312
0.25  -0.8663  0.165  -0.2382 -0.165  0.2382 11.2667  5.1315  1.06  2.2574  -2.1  -0.5  50  7.5416  3.5746  0.4971  0.0352   0.009   0.     0.2695  3.8787  0.9196  0.1208  7.3691  0.      -0.3539    -0.008918  -0.002128  5.2164  -0.7766  -0.2662   -0.006439  0.231541  0.     300  1.315   0.6579  -0.8469  0.393    800.        0.4341  0.3087  0.5377  0.4299  0.7999  0.5309
0.3   -1.0514  0.165  -0.2313 -0.165  0.2313  9.1908  5.167   1.06  2.344   -2.1  -0.5  50  7.56    3.6232  0.4919  0.0352  -0.0004  0.     0.2695  4.0711  0.8829  0.1175  6.8789  0.      -0.2688    -0.008251  -0.001812  5.1954  -0.8501  -0.2405   -0.006704  0.207277  0.001  300  1.3514  0.6362  -0.8999  0.408    800.        0.4363  0.3119  0.5395  0.4338  0.7997  0.5307
0.4   -1.3794  0.165  -0.2146 -0.165  0.2146  6.5459  5.2317  1.06  2.4709  -2.1  -0.5  50  7.5735  3.6945  0.4807  0.0352  -0.0155  0.     0.2695  4.3745  0.8302  0.106   6.5334  0.      -0.1793    -0.007267  -0.001274  5.0899  -0.9431  -0.1975   -0.007125  0.165464  0.004  300  1.4051  0.6049  -0.9618  0.462    800.        0.4396  0.3165  0.5422  0.4399  0.7988  0.531
0.5   -1.6508  0.165  -0.1972 -0.165  0.1972  5.2305  5.2893  1.06  2.5567  -2.1  -0.5  50  7.5778  3.7401  0.4707  0.0352  -0.0278  0.0991 0.2695  4.6099  0.7884  0.1061  6.526   0.      -0.1428    -0.006492  -0.001074  4.7854  -1.0044  -0.1633   -0.007435  0.133828  0.01   300  1.4402  0.5507  -0.9945  0.524    800.        0.4419  0.3199  0.5433  0.4446  0.7966  0.5313
0.75  -2.1511  0.165  -0.162  -0.165  0.162   3.7896  5.4109  1.06  2.6812  -2.1  -0.5  50  7.5808  3.7941  0.4575  0.0352  -0.0477  0.1982 0.2695  5.0376  0.6754  0.1     6.5     0.      -0.1138    -0.005147  -0.001115  4.3304  -1.0602  -0.1028   -0.00812   0.085153  0.034  300  1.528   0.3582  -1.0225  0.658    800.        0.4459  0.3255  0.5294  0.4533  0.7792  0.5309
1     -2.5365  0.165  -0.14   -0.165  0.14    3.3024  5.5106  1.06  2.7474  -2.1  -0.5  50  7.5814  3.8144  0.4522  0.0352  -0.0559  0.2154 0.2695  5.3411  0.6196  0.1     6.5     0.      -0.1062    -0.004277  -0.001197  4.1667  -1.0941  -0.0699   -0.008444  0.058595  0.067  300  1.6523  0.2003  -1.0002  0.78     800.        0.4484  0.3291  0.5105  0.4594  0.7504  0.5302
1.5   -3.0686  0.165  -0.1184 -0.165  0.1184  2.8498  5.6705  1.06  2.8161  -2.1  -0.5  50  7.5817  3.8284  0.4501  0.0352  -0.063   0.2154 0.2695  5.7688  0.5101  0.1     6.5     0.      -0.102     -0.002979  -0.001675  4.0029  -1.1142  -0.0425   -0.007707  0.031787  0.143  300  1.8872  0.0356  -0.9245  0.96     800.        0.4515  0.3335  0.4783  0.468   0.7136  0.5276
2     -3.4148  0.1645 -0.11   -0.1645 0.11    2.5417  5.7981  1.06  2.8514  -2.1  -0.5  50  7.5818  3.833   0.45    0.0352  -0.0665  0.2154 0.2695  6.0723  0.3917  0.1     6.5     0.      -0.1009    -0.002301  -0.002349  3.8949  -1.1154  -0.0302   -0.004792  0.019716  0.203  300  2.1348  0.      -0.8626  1.11     800.        0.4534  0.3363  0.4681  0.4681  0.7035  0.5167
3     -3.9013  0.1168 -0.104  -0.1168 0.104   2.1488  5.9983  1.06  2.8875  -2.1  -0.5  50  7.5818  3.8361  0.45    0.016   -0.0516  0.2154 0.2695  6.5     0.1244  0.1     6.5     0.      -0.1003    -0.001344  -0.003306  3.7928  -1.1081  -0.0129   -0.001828  0.009643  0.277  300  3.5752  0.      -0.7882  1.291    800.        0.4558  0.3398  0.4617  0.4617  0.7006  0.4917
4     -4.2466  0.0732 -0.102  -0.0732 0.102  1.8957   6.1552  1.06  2.9058  -2.1  -0.5  50  7.5818  3.8369  0.45    0.0062  -0.0448  0.2154 0.2695  6.8035  0.0086  0.1     6.5     0.      -0.1001    -0.001084  -0.003566  3.7443  -1.0603  -0.0016   -0.001523  0.005379  0.309  300  3.8646  0.      -0.7195  1.387    800.        0.4574  0.3419  0.4571  0.4571  0.7001  0.4682
5     -4.5143  0.0484 -0.101  -0.0484 0.101  1.7228   6.2856  1.06  2.9169  -2.1  -0.5  50  7.5818  3.8376  0.45    0.0029  -0.0424  0.2154 0.2695  7.0389  0.      0.1     6.5     0.      -0.1001    -0.00101   -0.00364   3.709   -0.9872   0.       -0.00144   0.003223  0.321  300  3.7292  0.      -0.656   1.433    800.        0.4584  0.3435  0.4535  0.4535  0.7     0.4517
7.5   -5.0009  0.022  -0.101  -0.022  0.101  1.5737   6.5428  1.06  2.932   -2.1  -0.5  50  7.5818  3.838   0.45    0.0007  -0.0348  0.2154 0.2695  7.4666  0.      0.1     6.5     0.      -0.1       -0.000964  -0.003686  3.6632  -0.8274   0.       -0.001369  0.001134  0.329  300  2.3763  0.      -0.5202  1.46     800.        0.4601  0.3459  0.4471  0.4471  0.7     0.4167
10    -5.3461  0.0124 -0.1    -0.0124 0.1    1.5265   6.7415  1.06  2.9396  -2.1  -0.5  50  7.5818  3.838   0.45    0.0003  -0.0253  0.2154 0.2695  7.77    0.      0.1     6.5     0.      -0.1       -0.00095   -0.0037    3.623   -0.7053   0.       -0.001361  0.000515  0.33   300  1.7679  0.      -0.4068  1.464    800.        0.4612  0.3474  0.4426  0.4426  0.7     0.3755
""")


# Regionalisation of the Chiou & Youngs (2014) GMPE for use with the
# Japan far-field distance attuation scaling and site model
add_alias('ChiouYoungs2014Japan', ChiouYoungs2014, region='JPN')

# Adaption of the Chiou & Youngs (2014) GMPE for the the Italy far-field
# attenuation scaling, but assuming the California site amplification model
add_alias('ChiouYoungs2014Italy', ChiouYoungs2014, region='ITA')

# Adaption of the Chiou & Youngs (2014) GMPE for the Wenchuan far-field
# attenuation scaling, but assuming the California site amplification model.
# It should be note that according to Chiou & Youngs (2014) this adjustment
# is calibrated only for the M7.9 Wenchuan earthquake, so application to
#  other scenarios is at the user's own risk
add_alias('ChiouYoungs2014Wenchuan', ChiouYoungs2014, region='WEN')


class ChiouYoungs2014PEER(ChiouYoungs2014):
    """
    This implements the Chiou & Youngs (2014) GMPE for use with the PEER
    tests. In this version the total standard deviation is fixed at 0.65
    """
    #: Only the total standars deviation is defined
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}
    #: The PEER tests requires only PGA
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA}


class ChiouYoungs2014NearFaultEffect(ChiouYoungs2014):
    """
    This implements the Chiou & Youngs (2014) GMPE include the near fault
    effect prediction. In this version, we add the distance measure, rcdpp
    for directivity prediction.
    """
    #: Required distance measures are RRup, Rjb, Rx, and Rcdpp
    REQUIRES_DISTANCES = {'rrup', 'rjb', 'rx', 'rcdpp'}


class ChiouYoungs2014ACME2019(ChiouYoungs2014):
    """
    Implements a modified version of the CY2014 GMM. Main changes:
    - Hanging wall term excluded
    - Centered Ztor = 0
    - Centered Dpp = 0
    """
    adapted = True

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            # intensity on a reference soil is used for both mean
            # and stddev calculations.
            ln_y_ref = _get_ln_y_ref(self.region, ctx, C)
            # exp1 and exp2 are parts of eq. 12 and eq. 13,
            # calculate it once for both.
            exp1 = np.exp(C['phi3'] * (ctx.vs30.clip(-np.inf, 1130) - 360))
            exp2 = np.exp(C['phi3'] * (1130 - 360))
            mean[m] = _get_mean(ctx, C, ln_y_ref, exp1, exp2)
