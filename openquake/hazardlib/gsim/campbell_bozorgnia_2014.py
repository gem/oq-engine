# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2025 GEM Foundation
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
Module exports :class:`CampbellBozorgnia2014`
               :class:`CampbellBozorgnia2014HighQ`
               :class:`CampbellBozorgnia2014LowQ`
               :class:`CampbellBozorgnia2019`
               :class:`CampbellBozorgnia2019HighQ`
               :class:`CampbellBozorgnia2019LowQ`
"""
import numpy as np

from numpy import exp, radians, cos
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable, add_alias
from openquake.hazardlib.gsim.abrahamson_2014 import get_epistemic_sigma
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA, IA, CAV
from openquake.hazardlib.gsim.utils_usgs_basin_scaling import \
    _get_z2pt5_usgs_basin_scaling


CONSTS = {"h4": 1.0, "c": 1.88, "n": 1.18}

# CyberShake basin adjustments for CB14 (only applied above 
# 1.9 seconds so don't provide dummy values listed below 2 s)
# Taken from https://code.usgs.gov/ghsc/nshmp/nshmp-lib/-/blob/main/src/main/resources/gmm/coeffs/CB14.csv?ref_type=heads
COEFFS_CY = CoeffsTable(sa_damping=5, table="""\
IMT   slope_cy
2.0   0.764
3.0   1.279
4.0   1.726
5.0   2.080 
7.5   3.000
10    3.000
""")


def _get_alpha(C, vs30, pga_rock):
    """
    Returns the alpha, the linearised functional relationship between the
    site amplification and the PGA on rock. Equation 31.
    """
    alpha = np.zeros(len(pga_rock))
    idx = vs30 < C["k1"]
    if np.any(idx):
        af1 = pga_rock[idx] +\
            CONSTS["c"] * ((vs30[idx] / C["k1"]) ** CONSTS["n"])
        af2 = pga_rock[idx] + CONSTS["c"]
        alpha[idx] = C["k2"] * pga_rock[idx] * ((1.0 / af1) - (1.0 / af2))
    return alpha


def _get_anelastic_attenuation_term(C, rrup):
    """
    Returns the anelastic attenuation term defined in equation 25
    """
    f_atn = np.zeros(len(rrup))
    idx = rrup >= 80.0
    f_atn[idx] = (C["c20"] + C["Dc20"]) * (rrup[idx] - 80.0)
    return f_atn


def _basin_term(C, imt, z2pt5, SJ, cy):
    """
    Calculate the basin term
    """
    # Get CyberShake adjustment if required and SA(T > 1.9)
    if cy and imt.period > 1.9:
        basin_coeffs = COEFFS_CY[imt]['slope_cy']
    # Otherwise use regular coefficients
    else:
        basin_coeffs = C["c16"] * C["k3"]

    fb = np.zeros(len(z2pt5))
    idx = z2pt5 < 1.0
    fb[idx] = (C["c14"] + C["c15"] * SJ) * (z2pt5[idx] - 1.0)
    idx = z2pt5 > 3.0
    fb[idx] = basin_coeffs * exp(-0.75) * (
        1. - np.exp(-0.25 * (z2pt5[idx] - 3.)))
    
    return fb


def _get_z2pt5_ref(SJ, vs30):
    """
    Select the preferred basin model (California or Japan) to scale
    basin depth with respect to Vs30. Returns z2pt5 in km
    """
    if SJ:
        # Japan Basin Model - Equation 34 of Campbell & Bozorgnia (2014)
        return np.exp(5.359 - 1.102 * np.log(vs30))
    else:
        # California Basin Model - Equation 33 of
        # Campbell & Bozorgnia (2014)
        return np.exp(7.089 - 1.144 * np.log(vs30))


def _get_basin_term(C, ctx, region, imt, SJ, a1100,
                    usgs_bs=False, cy=False):
    """
    Returns the basin response term defined in equation 20 and
    apply any required adjustments.
    """
    # Get reference basin depth
    z_ref = _get_z2pt5_ref(SJ, 1100.0) * np.ones_like(ctx.vs30)
    z_ref_term = _basin_term(C, imt, z_ref, SJ, False)

    # Get basin term
    if isinstance(a1100, np.ndarray): # Site model defined
        z2pt5 = ctx.z2pt5.copy()
        # Use GMM's vs30 to z2pt5 for non-measured values
        mask = z2pt5 == -999
        z2pt5[mask] = _get_z2pt5_ref(SJ, ctx.vs30[mask])
    else:
        z2pt5 = z_ref
    z2pt5_term = _basin_term(C, imt, z2pt5, SJ, cy)

    # Apply USGS basin scaling model if required
    if usgs_bs:
        # Get the scaling factor per site
        usgs_baf = _get_z2pt5_usgs_basin_scaling(z2pt5, imt.period)
        z_scaled = z_ref_term * (1.0 - usgs_baf) + z2pt5_term * usgs_baf
        # Apply additional CyberShake (CY_CSIM) adjustment if required
        if cy and imt.period > 1.9:
            z_scaled += 0.1 
        # If period is 0.075 seconds scale by factor of 0.585
        if imt.period == 0.075:
            return z_scaled * 0.585
        # Otherwise return basin term adjusted except for sites shallower than
        # upper z2pt5 value in USGS basin model (use z_ref_term instead here)
        if imt.period > 0.5:
            idx = z2pt5 > 1.0 # Upper z2pt5 depth in USGS basin model is 1 km
            z_scaled[idx] = z_ref_term[idx]
        return z_scaled
        
    return z2pt5_term


def _get_f1rx(C, r_x, r_1):
    """
    Defines the f1 scaling coefficient defined in equation 9
    """
    rxr1 = r_x / r_1
    return C["h1"] + C["h2"] * rxr1 + C["h3"] * rxr1 ** 2


def _get_f2rx(C, r_x, r_1, r_2):
    """
    Defines the f2 scaling coefficient defined in equation 10
    """
    drx = (r_x - r_1) / (r_2 - r_1)
    return CONSTS["h4"] + C["h5"] * drx + C["h6"] * drx ** 2


def _get_fault_dip_term(C, ctx):
    """
    Returns the fault dip term, defined in equation 24
    """
    res = C["c19"] * (5.5 - ctx.mag) * ctx.dip
    res[ctx.mag < 4.5] = C["c19"] * ctx.dip[ctx.mag < 4.5]
    res[ctx.mag > 5.5] = 0.0
    return res


def _get_geometric_attenuation_term(C, mag, rrup):
    """
    Returns the geometric attenuation term defined in equation 3
    """
    return (C["c5"] + C["c6"] * mag) * np.log(
        np.sqrt(rrup ** 2 + C["c7"] ** 2))


def _get_hanging_wall_coeffs_dip(dip):
    """
    Returns the hanging wall dip term defined in equation 16
    """
    return (90.0 - dip) / 45.0


def _get_hanging_wall_coeffs_mag(C, mag):
    """
    Returns the hanging wall magnitude term defined in equation 14
    """
    res = (mag - 5.5) * (1.0 + C["a2"] * (mag - 6.5))
    res[mag < 5.5] = 0.0
    res[mag > 6.5] = 1.0 + C["a2"] * (mag[mag > 6.5] - 6.5)
    return res


def _get_hanging_wall_coeffs_rrup(ctx):
    """
    Returns the hanging wall rrup term defined in equation 13
    """
    fhngrrup = np.ones(len(ctx.rrup))
    idx = ctx.rrup > 0.0
    fhngrrup[idx] = (ctx.rrup[idx] - ctx.rjb[idx]) / ctx.rrup[idx]
    return fhngrrup


def _get_hanging_wall_coeffs_rx(C, ctx):
    """
    Returns the hanging wall r-x caling term defined in equation 7 to 12
    """
    r_x = ctx.rx
    # Define coefficients R1 and R2
    r_1 = ctx.width * cos(radians(ctx.dip))
    r_2 = 62.0 * ctx.mag - 350.0
    fhngrx = np.zeros(len(r_x))
    # Case when 0 <= Rx <= R1
    idx = np.logical_and(r_x >= 0., r_x < r_1)
    fhngrx[idx] = _get_f1rx(C, r_x[idx], r_1[idx])
    # Case when Rx > R1
    idx = r_x >= r_1
    f2rx = _get_f2rx(C, r_x[idx], r_1[idx], r_2[idx])
    f2rx[f2rx < 0.0] = 0.0
    fhngrx[idx] = f2rx
    return fhngrx


def _get_hanging_wall_coeffs_ztor(ztor):
    """
    Returns the hanging wall ztor term defined in equation 15
    """
    res = 1. - 0.06 * ztor
    res[ztor > 16.66] = 0.
    return res


def _get_hanging_wall_term(C, ctx):
    """
    Returns the hanging wall scaling term defined in equations 7 to 16
    """
    return (C["c10"] *
            _get_hanging_wall_coeffs_rx(C, ctx) *
            _get_hanging_wall_coeffs_rrup(ctx) *
            _get_hanging_wall_coeffs_mag(C, ctx.mag) *
            _get_hanging_wall_coeffs_ztor(ctx.ztor) *
            _get_hanging_wall_coeffs_dip(ctx.dip))


def _get_hypocentral_depth_term(C, ctx):
    """
    Returns the hypocentral depth scaling term defined in equations 21 - 23
    """
    fhyp_h = np.clip(ctx.hypo_depth - 7.0, 0., 13.)
    fhyp_m = C["c17"] + (C["c18"] - C["c17"]) * (ctx.mag - 5.5)
    fhyp_m[ctx.mag <= 5.5] = C["c17"]
    fhyp_m[ctx.mag > 6.5] = C["c18"]
    return fhyp_h * fhyp_m


def _get_magnitude_term(C, mag):
    """
    Returns the magnitude scaling term defined in equation 2
    """
    f_mag = C["c0"] + C["c1"] * mag
    around5 = (mag > 4.5) & (mag <= 5.5)
    around6 = (mag > 5.5) & (mag <= 6.5)
    beyond = mag > 6.5
    f_mag[around5] += C["c2"] * (mag[around5] - 4.5)
    f_mag[around6] += (C["c2"] * (mag[around6] - 4.5) +
                       C["c3"] * (mag[around6] - 5.5))
    f_mag[beyond] += (C["c2"] * (mag[beyond] - 4.5) +
                      C["c3"] * (mag[beyond] - 5.5) +
                      C["c4"] * (mag[beyond] - 6.5))
    return f_mag


def _get_philny(C, mag):
    """
    Returns the intra-event random effects coefficient (phi)
    Equation 28.
    """
    res = C["phi2"] + (C["phi1"] - C["phi2"]) * (5.5 - mag)
    res[mag <= 4.5] = C["phi1"]
    res[mag >= 5.5] = C["phi2"]
    return res


def _get_shallow_site_response_term(SJ, C, vs30, pga_rock):
    """
    Returns the shallow site response term defined in equations 17, 18 and
    19
    """
    vs_mod = vs30 / C["k1"]
    # Get linear global site response term
    f_site_g = C["c11"] * np.log(vs_mod)
    idx = vs30 > C["k1"]
    f_site_g[idx] = f_site_g[idx] + (C["k2"] * CONSTS["n"] *
                                    np.log(vs_mod[idx]))
    
     # Get nonlinear site response term
    idx = np.logical_not(idx)
    if np.any(idx):
        f_site_g[idx] = f_site_g[idx] + C["k2"] * (
            np.log(pga_rock[idx] +
                   CONSTS["c"] * (vs_mod[idx] ** CONSTS["n"])) -
            np.log(pga_rock[idx] + CONSTS["c"]))

    if SJ:
        fsite_j = (C["c13"] + C["k2"] * CONSTS["n"]) * \
            np.log(vs_mod)
        # additional term activated for soft ctx (Vs30 <= 200m/s)
        # in Japan data
        idx = vs30 <= 200.0
        add_soft = (C["c12"] + C["k2"] * CONSTS["n"]) * \
            (np.log(vs_mod) - np.log(200.0 / C["k1"]))
        # combine terms
        fsite_j[idx] += add_soft[idx]

        return f_site_g + fsite_j
    else:
        return f_site_g
    
    
def _get_style_of_faulting_term(C, ctx):
    """
    Returns the style-of-faulting scaling term defined in equations 4 to 6
    """
    frv = np.zeros_like(ctx.rake)
    fnm = np.zeros_like(ctx.rake)
    frv[(ctx.rake > 30.) & (ctx.rake < 150.)] = 1.
    fnm[(ctx.rake > -150.) & (ctx.rake < -30.)] = 1.
    fflt_f = C["c8"] * frv + C["c9"] * fnm
    fflt_m = ctx.mag - 4.5
    fflt_m[ctx.mag <= 4.5] = 0.
    fflt_m[ctx.mag > 5.5] = 1.
    return fflt_f * fflt_m


def _get_taulny(C, mag):
    """
    Returns the inter-event random effects coefficient (tau)
    Equation 28.
    """
    res = C["tau2"] + (C["tau1"] - C["tau2"]) * (5.5 - mag)
    res[mag <= 4.5] = C["tau1"]
    res[mag >= 5.5] = C["tau2"]
    return res


def get_mean_values(SJ, C, ctx, imt, usgs_bs=False, cy=False, a1100=None):
    """
    Returns the mean values for a specific IMT
    """
    if isinstance(a1100, np.ndarray):
        # Site model defined
        temp_vs30 = ctx.vs30
    else:
        # Default site and basin model
        temp_vs30 = 1100.0 * np.ones(len(ctx))
    return (_get_magnitude_term(C, ctx.mag) +
            _get_geometric_attenuation_term(C, ctx.mag, ctx.rrup) +
            _get_style_of_faulting_term(C, ctx) +
            _get_hanging_wall_term(C, ctx) +
            _get_shallow_site_response_term(SJ, C, temp_vs30, a1100) +
            _get_basin_term(C, ctx, None, imt, SJ, a1100, usgs_bs, cy) +
            _get_hypocentral_depth_term(C, ctx) +
            _get_fault_dip_term(C, ctx) +
            _get_anelastic_attenuation_term(C, ctx.rrup))


def _update_ctx(gsim, ctx):
    """
    Use the ztor, width and hypo_depth formula to estimate
    if the estimate attribute is set.
    """
    if gsim.estimate_ztor:
        # Equation 4 and 5 of Chiou & Youngs 2014
        ctx.ztor = np.where(
            (ctx.rake > 30.) & (ctx.rake < 150.),
            np.maximum(2.704-1.226 * np.maximum(ctx.mag-5.849, 0), 0)**2,
            np.maximum(2.673-1.136 * np.maximum(ctx.mag-4.970, 0), 0)**2)

    if gsim.estimate_width:
        # width estimation requires Zbot
        # where Zbot is the depth to the bottom of the seismogenic crust
        if not hasattr(ctx, "zbot"):
            raise KeyError('Zbot is required if width is unknown.')

        # Equation 39 of Campbell & Bozorgnia 2014
        mask = np.absolute(np.sin(np.radians(ctx.dip))) > 0
        ctx.width = np.sqrt(10**((ctx.mag - 4.07) / 0.98))
        ctx.width[mask] = np.minimum(
            ctx.width[mask], (ctx.zbot[mask] - ctx.ztor[mask]) /
            np.sin(np.radians(ctx.dip[mask])))

    if gsim.estimate_hypo_depth:
        # Equation 36 of Campbell & Bozorgnia 2014
        fdz_m = np.where(
            ctx.mag < 6.75, -4.317 + 0.984 * ctx.mag, 2.325)

        # Equation 37 of Campbell & Bozorgnia 2014
        fdz_d = np.where(
            ctx.dip <= 40, 0.0445 * (ctx.dip - 40), 0)

        # The depth to the bottom of the rupture plane
        zbor = ctx.ztor + ctx.width * np.sin(np.radians(ctx.dip))

        # Equation 35 of Campbell & Bozorgnia 2014
        mask = zbor > ctx.ztor
        dz = np.zeros_like(ctx.ztor)
        dz[mask] = np.exp(
            np.minimum(
                fdz_m[mask] + fdz_d[mask],
                np.log(0.9 * (zbor[mask] - ctx.ztor[mask]))))
        ctx.hypo_depth = ctx.ztor + dz


def _get_rholnpga(C, mag):
    """
    Returns the magnitude-dependent correlation coefficient (rho) —
    Equation 5 of CB19.
    """
    rho_ln_pga = C["rho2pga"] + (C["rho1pga"] - C["rho2pga"]) * (5.5 - mag)
    rho_ln_pga[mag <= 4.5] = C["rho1pga"]
    rho_ln_pga[mag >= 5.5] = C["rho2pga"]
    return rho_ln_pga


class CampbellBozorgnia2014(GMPE):
    """
    Implements NGA-West 2 GMPE developed by Kenneth W. Campbell and Yousef
    Bozorgnia, published as "NGA-West2 Ground Motion Model for the Average
    Horizontal Components of PGA, PGV, and 5 % Damped Linear Acceleration
    Response Spectra" (2014, Earthquake Spectra, Volume 30, Number 3,
    pages 1087 - 1115).
    """
    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are spectral acceleration, peak
    #: ground velocity and peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA, IA, CAV}

    #: Supported intensity measure component is orientation-independent
    #: average horizontal :attr:`~openquake.hazardlib.const.IMC.GMRotI50`
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see section "Aleatory Variability Model", page 1094.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Required site parameters are Vs30, Vs30 type (measured or inferred),
    #: and depth (km) to the 2.5 km/s shear wave velocity layer (z2pt5)
    REQUIRES_SITES_PARAMETERS = {'vs30', 'z2pt5'}

    #: Required rupture parameters are magnitude, rake, dip, ztor, rupture
    #: width and hypocentral depth
    REQUIRES_RUPTURE_PARAMETERS = {
        'mag', 'rake', 'dip', 'ztor', 'width', 'hypo_depth'}

    #: Required distance measures are Rrup, Rjb and Rx
    REQUIRES_DISTANCES = {'rrup', 'rjb', 'rx'}

    def __init__(self, coeffs={}, SJ=False, sigma_mu_epsilon=0.0,
                 estimate_ztor=False, estimate_width=False,
                 estimate_hypo_depth=False, usgs_basin_scaling=False,
                 cybershake_basin_adj=False):
        # tested in logictree/case_71
        if coeffs:  # extra coefficients by IMT
            self.COEFFS |= CoeffsTable.fromdict(coeffs)
        self.SJ = SJ  # flag for Japan
        self.sigma_mu_epsilon = sigma_mu_epsilon
        self.estimate_ztor = estimate_ztor
        self.estimate_width = estimate_width
        self.estimate_hypo_depth = estimate_hypo_depth
        if self.estimate_width:
            # To estimate a width, the GMPE needs Zbot
            self.REQUIRES_RUPTURE_PARAMETERS |= {"zbot"}
        self.usgs_basin_scaling = usgs_basin_scaling
        self.cybershake_basin_adj = cybershake_basin_adj

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        if (self.estimate_ztor or self.estimate_width or
                self.estimate_hypo_depth):
            ctx = ctx.copy()
            _update_ctx(self, ctx)

        C_PGA = self.COEFFS[PGA()]
        # Get mean and standard deviation of PGA on rock (Vs30 1100 m/s^2)
        pga1100 = np.exp(get_mean_values(self.SJ, C_PGA, ctx, PGA(),
                                         self.usgs_basin_scaling,
                                         self.cybershake_basin_adj))
     
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            # Get mean and standard deviations for IMT
            mean[m] = get_mean_values(self.SJ, C, ctx, imt, 
                                      self.usgs_basin_scaling,
                                      self.cybershake_basin_adj,
                                      pga1100)
            mean[m] += (self.sigma_mu_epsilon*get_epistemic_sigma(ctx))

            if imt.string[:2] == "SA" and imt.period < 0.25:
                # According to Campbell & Bozorgnia (2013) [NGA West 2 Report]
                # If Sa (T) < PGA for T < 0.25 then set mean Sa(T) to mean PGA
                # Get PGA on soil
                pga = get_mean_values(self.SJ, C_PGA, ctx, imt,
                                      self.usgs_basin_scaling,
                                      self.cybershake_basin_adj,
                                      pga1100)
                idx = mean[m] <= pga
                mean[m, idx] = pga[idx]
                mean[m] += self.sigma_mu_epsilon * get_epistemic_sigma(ctx)

            # Get stddevs for PGA on basement rock
            tau_lnpga_b = _get_taulny(C_PGA, ctx.mag)
            phi_lnpga_b = np.sqrt(_get_philny(C_PGA, ctx.mag) ** 2. -
                                  C_PGA["philnAF"] ** 2.)

            # Get tau_lny on the basement rock
            tau_lnyb = _get_taulny(C, ctx.mag)
            # Get phi_lny on the basement rock
            phi_lnyb = np.sqrt(_get_philny(C, ctx.mag) ** 2. -
                               C["philnAF"] ** 2.)
            # Get site scaling term
            alpha = _get_alpha(C, ctx.vs30, pga1100)

            if imt.string in ['CAV', 'IA']:
                # Use formula in CB19 supplementary spreadsheet
                t = np.sqrt(tau_lnyb**2 + alpha**2 * tau_lnpga_b**2 +
                2. * alpha * _get_rholnpga(C, ctx.mag) * tau_lnyb * tau_lnpga_b)

                p = np.sqrt(
                phi_lnyb**2 + C["philnAF"]**2 + alpha**2 * phi_lnpga_b**2
                + 2.0 * alpha * _get_rholnpga(C, ctx.mag) * phi_lnyb * phi_lnpga_b)

            else:
                # Use formula in CB14 supplementary spreadsheet
                t = np.sqrt(tau_lnyb**2 + alpha**2 * tau_lnpga_b**2 +
                        2.0 * alpha * C["rholny"] * tau_lnyb * tau_lnpga_b)

                p = np.sqrt(
                    phi_lnyb**2 + C["philnAF"]**2 + alpha**2 * phi_lnpga_b**2
                    + 2.0 * alpha * C["rholny"] * phi_lnyb * phi_lnpga_b)
                
            sig[m] = np.sqrt(t**2 + p**2)
            tau[m] = t
            phi[m] = p

    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT         c0     c1      c2      c3      c4      c5     c6     c7     c8      c9    c10     c11     c12    c13      c14     c15    c16      c17     c18      c19      c20  Dc20     a2     h1     h2      h3      h5      h6    k1      k2     k3   phi1   phi2   tau1   tau2  rho1pga  rho2pga      philnAF   phiC  rholny
    0.01    -4.365  0.977   0.533  -1.485  -0.499  -2.773  0.248  6.753      0  -0.214   0.72   1.094   2.191  1.416   -0.007  -0.207   0.39   0.0981  0.0334  0.00755  -0.0055     0  0.168  0.242  1.471  -0.714  -0.336   -0.27   865  -1.186  1.839  0.734  0.492  0.404  0.325        1        1          0.3   0.19       1
    0.02    -4.348  0.976   0.549  -1.488  -0.501  -2.772  0.247  6.502      0  -0.208   0.73   1.149   2.189  1.453  -0.0167  -0.199  0.387   0.1009  0.0327  0.00759  -0.0055     0  0.166  0.244  1.467  -0.711  -0.339  -0.263   865  -1.219   1.84  0.738  0.496  0.417  0.326    0.999    0.998          0.3  0.166   0.998
    0.03    -4.024  0.931   0.628  -1.494  -0.517  -2.782  0.246  6.291      0  -0.213  0.759    1.29   2.164  1.476  -0.0422  -0.202  0.378   0.1095  0.0331   0.0079  -0.0057     0  0.167  0.246  1.467  -0.713  -0.338  -0.259   908  -1.273  1.841  0.747  0.503  0.446  0.344    0.987    0.987          0.3  0.166   0.986
    0.05    -3.479  0.887   0.674  -1.388  -0.615  -2.791   0.24  6.317      0  -0.244  0.826   1.449   2.138  1.549  -0.0663  -0.339  0.295   0.1226   0.027  0.00803  -0.0063     0  0.173  0.251  1.449  -0.701  -0.338  -0.263  1054  -1.346  1.843  0.777   0.52  0.508  0.377    0.955    0.946          0.3  0.166   0.938
    0.075   -3.293  0.902   0.726  -1.469  -0.596  -2.745  0.227  6.861      0  -0.266  0.815   1.535   2.446  1.772  -0.0794  -0.404  0.322   0.1165  0.0288  0.00811   -0.007     0  0.198   0.26  1.435  -0.695  -0.347  -0.219  1086  -1.471  1.845  0.782  0.535  0.504  0.418    0.943    0.897          0.3  0.165   0.887
    0.1     -3.666  0.993   0.698  -1.572  -0.536  -2.633   0.21  7.294      0  -0.229  0.831   1.615   2.969  1.916  -0.0294  -0.416  0.384   0.0998  0.0325  0.00744  -0.0073     0  0.174  0.259  1.449  -0.708  -0.391  -0.201  1032  -1.624  1.847  0.769  0.543  0.445  0.426    0.942    0.883          0.3  0.162    0.87
    0.15    -4.866  1.267    0.51  -1.669   -0.49  -2.458  0.183  8.031      0  -0.211  0.749   1.877   3.544  2.161   0.0642  -0.407  0.417    0.076  0.0388  0.00716  -0.0069     0  0.198  0.254  1.461  -0.715  -0.449  -0.099   878  -1.931  1.852  0.769  0.543  0.382  0.387    0.921    0.891          0.3  0.158   0.876
    0.2     -5.411  1.366   0.447   -1.75  -0.451  -2.421  0.182  8.385      0  -0.163  0.764   2.069   3.707  2.465   0.0968  -0.311  0.404   0.0571  0.0437  0.00688   -0.006     0  0.204  0.237  1.484  -0.721  -0.393  -0.198   748  -2.188  1.856  0.761  0.552  0.339  0.338    0.874    0.881          0.3   0.17    0.87
    0.25    -5.962  1.458   0.274  -1.711  -0.404  -2.392  0.189  7.534      0   -0.15  0.716   2.205   3.343  2.766   0.1441  -0.172  0.466   0.0437  0.0463  0.00556  -0.0055     0  0.185  0.206  1.581  -0.787  -0.339   -0.21   654  -2.381  1.861  0.744  0.545   0.34  0.316    0.809    0.861          0.3   0.18    0.85
    0.3     -6.403  1.528   0.193   -1.77  -0.321  -2.376  0.195   6.99      0  -0.131  0.737   2.306   3.334  3.011   0.1597  -0.084  0.528   0.0323  0.0508  0.00458  -0.0049     0  0.164   0.21  1.586  -0.795  -0.447  -0.121   587  -2.518  1.865  0.727  0.568   0.34    0.3    0.741    0.824          0.3  0.186   0.819
    0.4     -7.566  1.739   -0.02  -1.594  -0.426  -2.303  0.185  7.012      0  -0.159  0.738   2.398   3.544  3.203    0.141   0.085   0.54   0.0209  0.0432  0.00401  -0.0037     0   0.16  0.226  1.544   -0.77  -0.525  -0.086   503  -2.657  1.874   0.69  0.593  0.356  0.264    0.635    0.738          0.3  0.191   0.743
    0.5     -8.379  1.872  -0.121  -1.577   -0.44  -2.296  0.186  6.902      0  -0.153  0.718   2.355   3.016  3.333   0.1474   0.233  0.638   0.0092  0.0405  0.00388  -0.0027     0  0.184  0.217  1.554   -0.77  -0.407  -0.281   457  -2.669  1.883  0.663  0.611  0.379  0.263    0.553    0.661          0.3  0.198   0.684
    0.75    -9.841  2.021  -0.042  -1.757  -0.443  -2.232  0.186  5.522      0   -0.09  0.795   1.995   2.616  3.054   0.1764   0.411  0.776  -0.0082   0.042   0.0042  -0.0016     0  0.216  0.154  1.626   -0.78  -0.371  -0.285   410  -2.401  1.906  0.606  0.633   0.43  0.326    0.393    0.526          0.3  0.206   0.562
    1      -11.011   2.18  -0.069  -1.707  -0.527  -2.158  0.169   5.65      0  -0.105  0.556   1.447    2.47  2.562   0.2593   0.479  0.771  -0.0131  0.0426  0.00409  -0.0006     0  0.596  0.117  1.616  -0.733  -0.128  -0.756   400  -1.955  1.929  0.579  0.628   0.47  0.353    0.313    0.438          0.3  0.208   0.467
    1.5    -12.469   2.27   0.047  -1.621   -0.63  -2.063  0.158  5.795      0  -0.058   0.48    0.33   2.108  1.453   0.2881   0.566  0.748  -0.0187   0.038  0.00424        0     0  0.596  0.117  1.616  -0.733  -0.128  -0.756   400  -1.025  1.974  0.541  0.603  0.497  0.399    0.242     0.36          0.3  0.221   0.364
    2      -12.969  2.271   0.149  -1.512  -0.768  -2.104  0.158  6.632      0  -0.028  0.401  -0.514   1.327  0.657   0.3112   0.562  0.763  -0.0258  0.0252  0.00448        0     0  0.596  0.117  1.616  -0.733  -0.128  -0.756   400  -0.299  2.019  0.529  0.588  0.499    0.4    0.234    0.318          0.3  0.225   0.298
    3      -13.306   2.15   0.368  -1.315   -0.89  -2.051  0.148  6.759      0       0  0.206  -0.848   0.601  0.367   0.3478   0.534  0.686  -0.0311  0.0236  0.00345        0     0  0.596  0.117  1.616  -0.733  -0.128  -0.756   400       0   2.11  0.527  0.578    0.5  0.417    0.236    0.295          0.3  0.222   0.234
    4       -14.02  2.132   0.726  -1.506  -0.885  -1.986  0.135  7.978      0       0  0.105  -0.793   0.568  0.306   0.3747   0.522  0.691  -0.0413  0.0102  0.00603        0     0  0.596  0.117  1.616  -0.733  -0.128  -0.756   400       0    2.2  0.521  0.559  0.543  0.393    0.232    0.274          0.3  0.226   0.202
    5      -14.558  2.116   1.027  -1.721  -0.878  -2.021  0.135  8.538      0       0      0  -0.748   0.356  0.268   0.3382   0.477   0.67  -0.0281  0.0034  0.00805        0     0  0.596  0.117  1.616  -0.733  -0.128  -0.756   400       0  2.291  0.502  0.551  0.534  0.421    0.182    0.247          0.3  0.229   0.184
    7.5    -15.509  2.223   0.169  -0.756  -1.077  -2.179  0.165  8.468      0       0      0  -0.664   0.075  0.374   0.3754   0.321  0.757  -0.0205   0.005   0.0028        0     0  0.596  0.117  1.616  -0.733  -0.128  -0.756   400       0  2.517  0.457  0.546  0.523  0.438    0.142    0.203          0.3  0.237   0.176
    10     -15.975  2.132   0.367    -0.8  -1.282  -2.244   0.18  6.564      0       0      0  -0.576  -0.027  0.297   0.3506   0.174  0.621   0.0009  0.0099  0.00458        0     0  0.596  0.117  1.616  -0.733  -0.128  -0.756   400       0  2.744  0.441  0.543  0.466  0.438    0.111    0.103          0.3  0.237   0.154
    pga     -4.416  0.984   0.537  -1.499  -0.496  -2.773  0.248  6.768      0  -0.212   0.72    1.09   2.186   1.42  -0.0064  -0.202  0.393   0.0977  0.0333  0.00757  -0.0055     0  0.167  0.241  1.474  -0.715  -0.337   -0.27   865  -1.186  1.839  0.734  0.492  0.409  0.322        1        1          0.3  0.271       1
    pgv     -2.895   1.51    0.27  -1.299  -0.453  -2.466  0.204  5.837      0  -0.168  0.305   1.713   2.602  2.457    0.106   0.332  0.585   0.0517  0.0327  0.00613  -0.0017     0  0.596  0.117  1.616  -0.733  -0.128  -0.756   400  -1.955  1.929  0.655  0.494  0.317  0.297    0.877    0.654          0.3   0.29   0.684
    cav      -4.75  1.397   0.282  -1.062   -0.17  -1.624  0.134  6.325  0.054    -0.1  0.469   1.015   1.208  1.777   0.1248  -0.191  1.087   0.0432  0.0127  0.00429  -0.0043     0  0.167  0.241  1.474  -0.715  -0.337   -0.27   400  -1.311      1  0.514  0.394  0.276  0.257    0.842     0.78          0.3      0       0
    ia     -10.272  2.318    0.88  -2.672  -0.837  -4.441  0.416  4.869  0.187  -0.196  1.165   1.596   2.829   2.76    0.108  -0.315  1.612   0.1311  0.0453  0.01242  -0.0103     0  0.167  0.241  1.474  -0.715  -0.337   -0.27   400  -1.982      1  1.174  0.809  0.614  0.435    0.948    0.911  0.615989848      0       0
    """)

coeffs_high = CoeffsTable.fromtoml('''
"SA(0.01)".Dc20 = 0.0036
"SA(0.02)".Dc20 = 0.0036
"SA(0.03)".Dc20 = 0.0037
"SA(0.05)".Dc20 = 0.0040
"SA(0.075)".Dc20 = 0.0039
"SA(0.1)".Dc20 = 0.0042
"SA(0.15)".Dc20 = 0.0042
"SA(0.2)".Dc20 = 0.0041
"SA(0.25)".Dc20 = 0.0036
"SA(0.3)".Dc20 = 0.0031
"SA(0.4)".Dc20 = 0.0028
"SA(0.5)".Dc20 = 0.0025
"SA(0.75)".Dc20 = 0.0016
"SA(1.0)".Dc20 = 0.0006
PGA.Dc20 = 0.0036
PGV.Dc20 = 0.0017
CAV.Dc20 = 0.0027
IA.Dc20 = 0.0064
''').to_dict()

coeffs_low = CoeffsTable.fromtoml('''
"SA(0.01)".Dc20 = -0.0035
"SA(0.02)".Dc20 = -0.0035
"SA(0.03)".Dc20 = -0.0034
"SA(0.05)".Dc20 = -0.0037
"SA(0.075)".Dc20 = -0.0037
"SA(0.1)".Dc20 = -0.0034
"SA(0.15)".Dc20 = -0.0030
"SA(0.2)".Dc20 = -0.0031
"SA(0.25)".Dc20 = -0.0033
"SA(0.3)".Dc20 = -0.0035
"SA(0.4)".Dc20 = -0.0034
"SA(0.5)".Dc20 = -0.0034
"SA(0.75)".Dc20 = -0.0032
"SA(1.0)".Dc20 = -0.0030
"SA(1.5)".Dc20 = -0.0019
"SA(2.0)".Dc20 = -0.0005
PGA.Dc20 = -0.0035
PGV.Dc20 = -0.0006
CAV.Dc20 = -0.0024
IA.Dc20 = -0.0051
''').to_dict()


class CampbellBozorgnia2019(CampbellBozorgnia2014):
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN


add_alias('CampbellBozorgnia2014HighQ', CampbellBozorgnia2014,
          coeffs=coeffs_high)
add_alias('CampbellBozorgnia2014LowQ', CampbellBozorgnia2014,
          coeffs=coeffs_low)
add_alias('CampbellBozorgnia2014JapanSite', CampbellBozorgnia2014,
          SJ=True)
add_alias('CampbellBozorgnia2014HighQJapanSite', CampbellBozorgnia2014,
          coeffs=coeffs_high, SJ=True)
add_alias('CampbellBozorgnia2014LowQJapanSite', CampbellBozorgnia2014,
          coeffs=coeffs_low, SJ=True)

add_alias('CampbellBozorgnia2019HighQ', CampbellBozorgnia2019,
          coeffs=coeffs_high)
add_alias('CampbellBozorgnia2019LowQ', CampbellBozorgnia2019,
          coeffs=coeffs_low)
add_alias('CampbellBozorgnia2019JapanSite', CampbellBozorgnia2019,
          SJ=True)
add_alias('CampbellBozorgnia2019HighQJapanSite', CampbellBozorgnia2019,
          coeffs=coeffs_high, SJ=True)
add_alias('CampbellBozorgnia2019LowQJapanSite', CampbellBozorgnia2019,
          coeffs=coeffs_low, SJ=True)
