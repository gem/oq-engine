# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2022 GEM Foundation
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
               :class:`CampbellBozorgnia2014JapanSite`
               :class:`CampbellBozorgnia2014HighQJapanSite`
               :class:`CampbellBozorgnia2014LowQJapanSite`
"""
import numpy as np
from numpy import exp, radians, cos
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA

CONSTS = {"c8": 0.0,
          "h4": 1.0,
          "c": 1.88,
          "n": 1.18,
          "philnAF": 0.3}


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


def _get_basin_response_term(SJ, C, z2pt5):
    """
    Returns the basin response term defined in equation 20
    """
    f_sed = np.zeros(len(z2pt5))
    idx = z2pt5 < 1.0
    f_sed[idx] = (C["c14"] + C["c15"] * SJ) * (z2pt5[idx] - 1.0)
    idx = z2pt5 > 3.0
    f_sed[idx] = C["c16"] * C["k3"] * exp(-0.75) * (
        1. - np.exp(-0.25 * (z2pt5[idx] - 3.)))
    return f_sed


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

    # For Japan (SJ = 1) further scaling is needed (equation 19)
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
    fflt_f = CONSTS["c8"] * frv + C["c9"] * fnm
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


def _select_basin_model(SJ, vs30):
    """
    Select the preferred basin model (California or Japan) to scale
    basin depth with respect to Vs30
    """
    if SJ:
        # Japan Basin Model - Equation 34 of Campbell & Bozorgnia (2014)
        return np.exp(5.359 - 1.102 * np.log(vs30))
    else:
        # California Basin Model - Equation 33 of
        # Campbell & Bozorgnia (2014)
        return np.exp(7.089 - 1.144 * np.log(vs30))


def get_mean_values(SJ, C, ctx, a1100=None):
    """
    Returns the mean values for a specific IMT
    """
    if isinstance(a1100, np.ndarray):
        # Site model defined
        temp_vs30 = ctx.vs30
        temp_z2pt5 = ctx.z2pt5
    else:
        # Default site and basin model
        temp_vs30 = 1100.0 * np.ones(len(ctx))
        temp_z2pt5 = _select_basin_model(SJ, 1100.0) * \
            np.ones_like(temp_vs30)

    return (_get_magnitude_term(C, ctx.mag) +
            _get_geometric_attenuation_term(C, ctx.mag, ctx.rrup) +
            _get_style_of_faulting_term(C, ctx) +
            _get_hanging_wall_term(C, ctx) +
            _get_shallow_site_response_term(SJ, C, temp_vs30, a1100) +
            _get_basin_response_term(SJ, C, temp_z2pt5) +
            _get_hypocentral_depth_term(C, ctx) +
            _get_fault_dip_term(C, ctx) +
            _get_anelastic_attenuation_term(C, ctx.rrup))

def get_epistemic_sigma(ctx):
    """This function gives the epistemic sigma computed following USGS-2014 approach. Also, note that the events are counted in each magnitude and distance bins.
    However, the epistemic sigma is based on NZ SMDB v1.0"""

    n = 2
    dist_func_5_6 = np.where(ctx.rrup <=10, 0.4*np.sqrt(n/11), np.where((ctx.rrup > 10) & (ctx.rrup <30), 0.4*np.sqrt(n/38), 0.4*np.sqrt(n/94)))

    dist_func_6_7 = np.where(ctx.rrup <=10, 0.4*np.sqrt(n/2), np.where((ctx.rrup > 10) & (ctx.rrup <30), 0.4*np.sqrt(n/7), 0.4*np.sqrt(n/13)))

    dist_func_7_above = np.where(ctx.rrup <=10, 0.4*np.sqrt(n/2), np.where((ctx.rrup > 10) & (ctx.rrup <30), 0.4*np.sqrt(n/2), 0.4*np.sqrt(n/4)))

    sigma_epi = np.where((ctx.mag>=5) & (ctx.mag<6), dist_func_5_6, np.where((ctx.mag >=6) & (ctx.mag < 7), dist_func_6_7, dist_func_7_above))

    return sigma_epi


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
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

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

    SJ = 0  # 1 for Japan

    def __init__(self, sigma_mu_epsilon=0.0, **kwargs):
        self.kwargs = kwargs
        self.better_ztor = int(kwargs.get('better_ztor', 0))
        self.sigma_mu_epsilon = sigma_mu_epsilon

    def set_parameters(self, ctx):
        """
        Use the ztor formula in equation 4 and 5 of Chiou & Youngs 2014
        if the attribute .better_ztor is set.
        """
        if self.better_ztor:
            ctx.ztor = np.where(
                (ctx.rake > 30.) & (ctx.rake < 150.),
                np.maximum(2.704-1.226 * np.maximum(ctx.mag-5.849, 0), 0)**2,
                np.maximum(2.673-1.136 * np.maximum(ctx.mag-4.970, 0), 0)**2)

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
        pga1100 = np.exp(get_mean_values(self.SJ, C_PGA, ctx))
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            # Get mean and standard deviations for IMT
            mean[m] = get_mean_values(self.SJ, C, ctx, pga1100)
            if self.sigma_mu_epsilon:
                mean[m] += (self.sigma_mu_epsilon*get_epistemic_sigma(ctx))
            if imt.string[:2] == "SA" and imt.period < 0.25:
                # According to Campbell & Bozorgnia (2013) [NGA West 2 Report]
                # If Sa (T) < PGA for T < 0.25 then set mean Sa(T) to mean PGA
                # Get PGA on soil
                pga = get_mean_values(self.SJ, C_PGA, ctx, pga1100)
                idx = mean[m] <= pga
                mean[m, idx] = pga[idx]
                mean[m] += (self.sigma_mu_epsilon*get_epistemic_sigma(ctx))

            # Get stddevs for PGA on basement rock
            tau_lnpga_b = _get_taulny(C_PGA, ctx.mag)
            phi_lnpga_b = np.sqrt(_get_philny(C_PGA, ctx.mag) ** 2. -
                                  CONSTS["philnAF"] ** 2.)

            # Get tau_lny on the basement rock
            tau_lnyb = _get_taulny(C, ctx.mag)
            # Get phi_lny on the basement rock
            phi_lnyb = np.sqrt(_get_philny(C, ctx.mag) ** 2. -
                               CONSTS["philnAF"] ** 2.)
            # Get site scaling term
            alpha = _get_alpha(C, ctx.vs30, pga1100)
            # Evaluate tau according to equation 29
            t = np.sqrt(tau_lnyb**2 + alpha**2 * tau_lnpga_b**2 +
                        2.0 * alpha * C["rholny"] * tau_lnyb * tau_lnpga_b)

            # Evaluate phi according to equation 30
            p = np.sqrt(
                phi_lnyb**2 + CONSTS["philnAF"]**2 + alpha**2 * phi_lnpga_b**2
                + 2.0 * alpha * C["rholny"] * phi_lnyb * phi_lnpga_b)
            sig[m] = np.sqrt(t**2 + p**2)
            tau[m] = t
            phi[m] = p

    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT         c0      c1       c2       c3       c4       c5      c6      c7       c9     c10      c11      c12     c13       c14      c15     c16       c17      c18       c19       c20     Dc20      a2      h1      h2       h3       h5       h6     k1       k2      k3    phi1    phi2    tau1    tau2    phiC   rholny
    pgv     -2.895   1.510    0.270   -1.299   -0.453   -2.466   0.204   5.837   -0.168   0.305    1.713    2.602   2.457    0.1060    0.332   0.585    0.0517   0.0327   0.00613   -0.0017   0.0000   0.596   0.117   1.616   -0.733   -0.128   -0.756    400   -1.955   1.929   0.655   0.494   0.317   0.297   0.190    0.684
    pga     -4.416   0.984    0.537   -1.499   -0.496   -2.773   0.248   6.768   -0.212   0.720    1.090    2.186   1.420   -0.0064   -0.202   0.393    0.0977   0.0333   0.00757   -0.0055   0.0000   0.167   0.241   1.474   -0.715   -0.337   -0.270    865   -1.186   1.839   0.734   0.492   0.409   0.322   0.166    1.000
    0.01    -4.365   0.977    0.533   -1.485   -0.499   -2.773   0.248   6.753   -0.214   0.720    1.094    2.191   1.416   -0.0070   -0.207   0.390    0.0981   0.0334   0.00755   -0.0055   0.0000   0.168   0.242   1.471   -0.714   -0.336   -0.270    865   -1.186   1.839   0.734   0.492   0.404   0.325   0.166    1.000
    0.02    -4.348   0.976    0.549   -1.488   -0.501   -2.772   0.247   6.502   -0.208   0.730    1.149    2.189   1.453   -0.0167   -0.199   0.387    0.1009   0.0327   0.00759   -0.0055   0.0000   0.166   0.244   1.467   -0.711   -0.339   -0.263    865   -1.219   1.840   0.738   0.496   0.417   0.326   0.166    0.998
    0.03    -4.024   0.931    0.628   -1.494   -0.517   -2.782   0.246   6.291   -0.213   0.759    1.290    2.164   1.476   -0.0422   -0.202   0.378    0.1095   0.0331   0.00790   -0.0057   0.0000   0.167   0.246   1.467   -0.713   -0.338   -0.259    908   -1.273   1.841   0.747   0.503   0.446   0.344   0.165    0.986
    0.05    -3.479   0.887    0.674   -1.388   -0.615   -2.791   0.240   6.317   -0.244   0.826    1.449    2.138   1.549   -0.0663   -0.339   0.295    0.1226   0.0270   0.00803   -0.0063   0.0000   0.173   0.251   1.449   -0.701   -0.338   -0.263   1054   -1.346   1.843   0.777   0.520   0.508   0.377   0.162    0.938
    0.075   -3.293   0.902    0.726   -1.469   -0.596   -2.745   0.227   6.861   -0.266   0.815    1.535    2.446   1.772   -0.0794   -0.404   0.322    0.1165   0.0288   0.00811   -0.0070   0.0000   0.198   0.260   1.435   -0.695   -0.347   -0.219   1086   -1.471   1.845   0.782   0.535   0.504   0.418   0.158    0.887
    0.10    -3.666   0.993    0.698   -1.572   -0.536   -2.633   0.210   7.294   -0.229   0.831    1.615    2.969   1.916   -0.0294   -0.416   0.384    0.0998   0.0325   0.00744   -0.0073   0.0000   0.174   0.259   1.449   -0.708   -0.391   -0.201   1032   -1.624   1.847   0.769   0.543   0.445   0.426   0.170    0.870
    0.15    -4.866   1.267    0.510   -1.669   -0.490   -2.458   0.183   8.031   -0.211   0.749    1.877    3.544   2.161    0.0642   -0.407   0.417    0.0760   0.0388   0.00716   -0.0069   0.0000   0.198   0.254   1.461   -0.715   -0.449   -0.099    878   -1.931   1.852   0.769   0.543   0.382   0.387   0.180    0.876
    0.20    -5.411   1.366    0.447   -1.750   -0.451   -2.421   0.182   8.385   -0.163   0.764    2.069    3.707   2.465    0.0968   -0.311   0.404    0.0571   0.0437   0.00688   -0.0060   0.0000   0.204   0.237   1.484   -0.721   -0.393   -0.198    748   -2.188   1.856   0.761   0.552   0.339   0.338   0.186    0.870
    0.25    -5.962   1.458    0.274   -1.711   -0.404   -2.392   0.189   7.534   -0.150   0.716    2.205    3.343   2.766    0.1441   -0.172   0.466    0.0437   0.0463   0.00556   -0.0055   0.0000   0.185   0.206   1.581   -0.787   -0.339   -0.210    654   -2.381   1.861   0.744   0.545   0.340   0.316   0.191    0.850
    0.30    -6.403   1.528    0.193   -1.770   -0.321   -2.376   0.195   6.990   -0.131   0.737    2.306    3.334   3.011    0.1597   -0.084   0.528    0.0323   0.0508   0.00458   -0.0049   0.0000   0.164   0.210   1.586   -0.795   -0.447   -0.121    587   -2.518   1.865   0.727   0.568   0.340   0.300   0.198    0.819
    0.40    -7.566   1.739   -0.020   -1.594   -0.426   -2.303   0.185   7.012   -0.159   0.738    2.398    3.544   3.203    0.1410    0.085   0.540    0.0209   0.0432   0.00401   -0.0037   0.0000   0.160   0.226   1.544   -0.770   -0.525   -0.086    503   -2.657   1.874   0.690   0.593   0.356   0.264   0.206    0.743
    0.50    -8.379   1.872   -0.121   -1.577   -0.440   -2.296   0.186   6.902   -0.153   0.718    2.355    3.016   3.333    0.1474    0.233   0.638    0.0092   0.0405   0.00388   -0.0027   0.0000   0.184   0.217   1.554   -0.770   -0.407   -0.281    457   -2.669   1.883   0.663   0.611   0.379   0.263   0.208    0.684
    0.75    -9.841   2.021   -0.042   -1.757   -0.443   -2.232   0.186   5.522   -0.090   0.795    1.995    2.616   3.054    0.1764    0.411   0.776   -0.0082   0.0420   0.00420   -0.0016   0.0000   0.216   0.154   1.626   -0.780   -0.371   -0.285    410   -2.401   1.906   0.606   0.633   0.430   0.326   0.221    0.562
    1.00   -11.011   2.180   -0.069   -1.707   -0.527   -2.158   0.169   5.650   -0.105   0.556    1.447    2.470   2.562    0.2593    0.479   0.771   -0.0131   0.0426   0.00409   -0.0006   0.0000   0.596   0.117   1.616   -0.733   -0.128   -0.756    400   -1.955   1.929   0.579   0.628   0.470   0.353   0.225    0.467
    1.50   -12.469   2.270    0.047   -1.621   -0.630   -2.063   0.158   5.795   -0.058   0.480    0.330    2.108   1.453    0.2881    0.566   0.748   -0.0187   0.0380   0.00424    0.0000   0.0000   0.596   0.117   1.616   -0.733   -0.128   -0.756    400   -1.025   1.974   0.541   0.603   0.497   0.399   0.222    0.364
    2.00   -12.969   2.271    0.149   -1.512   -0.768   -2.104   0.158   6.632   -0.028   0.401   -0.514    1.327   0.657    0.3112    0.562   0.763   -0.0258   0.0252   0.00448    0.0000   0.0000   0.596   0.117   1.616   -0.733   -0.128   -0.756    400   -0.299   2.019   0.529   0.588   0.499   0.400   0.226    0.298
    3.00   -13.306   2.150    0.368   -1.315   -0.890   -2.051   0.148   6.759    0.000   0.206   -0.848    0.601   0.367    0.3478    0.534   0.686   -0.0311   0.0236   0.00345    0.0000   0.0000   0.596   0.117   1.616   -0.733   -0.128   -0.756    400    0.000   2.110   0.527   0.578   0.500   0.417   0.229    0.234
    4.00   -14.020   2.132    0.726   -1.506   -0.885   -1.986   0.135   7.978    0.000   0.105   -0.793    0.568   0.306    0.3747    0.522   0.691   -0.0413   0.0102   0.00603    0.0000   0.0000   0.596   0.117   1.616   -0.733   -0.128   -0.756    400    0.000   2.200   0.521   0.559   0.543   0.393   0.237    0.202
    5.00   -14.558   2.116    1.027   -1.721   -0.878   -2.021   0.135   8.538    0.000   0.000   -0.748    0.356   0.268    0.3382    0.477   0.670   -0.0281   0.0034   0.00805    0.0000   0.0000   0.596   0.117   1.616   -0.733   -0.128   -0.756    400    0.000   2.291   0.502   0.551   0.534   0.421   0.237    0.184
    7.50   -15.509   2.223    0.169   -0.756   -1.077   -2.179   0.165   8.468    0.000   0.000   -0.664    0.075   0.374    0.3754    0.321   0.757   -0.0205   0.0050   0.00280    0.0000   0.0000   0.596   0.117   1.616   -0.733   -0.128   -0.756    400    0.000   2.517   0.457   0.546   0.523   0.438   0.271    0.176
    10.0   -15.975   2.132    0.367   -0.800   -1.282   -2.244   0.180   6.564    0.000   0.000   -0.576   -0.027   0.297    0.3506    0.174   0.621    0.0009   0.0099   0.00458    0.0000   0.0000   0.596   0.117   1.616   -0.733   -0.128   -0.756    400    0.000   2.744   0.441   0.543   0.466   0.438   0.290    0.154
    """)


class CampbellBozorgnia2014HighQ(CampbellBozorgnia2014):
    """
    Implements the Campbell & Bozorgnia (2014) NGA-West2 GMPE for regions with
    low attenuation (high quality factor, Q) (i.e. China, Turkey)
    """
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT         c0      c1       c2       c3       c4       c5      c6      c7       c9     c10      c11      c12     c13       c14      c15     c16       c17      c18       c19       c20     Dc20      a2      h1      h2       h3       h5       h6     k1       k2      k3    phi1    phi2    tau1    tau2    phiC   rholny
    pgv     -2.895   1.510    0.270   -1.299   -0.453   -2.466   0.204   5.837   -0.168   0.305    1.713    2.602   2.457    0.1060    0.332   0.585    0.0517   0.0327   0.00613   -0.0017   0.0017   0.596   0.117   1.616   -0.733   -0.128   -0.756    400   -1.955   1.929   0.655   0.494   0.317   0.297   0.190   0.684
    pga     -4.416   0.984    0.537   -1.499   -0.496   -2.773   0.248   6.768   -0.212   0.720    1.090    2.186   1.420   -0.0064   -0.202   0.393    0.0977   0.0333   0.00757   -0.0055   0.0036   0.167   0.241   1.474   -0.715   -0.337   -0.270    865   -1.186   1.839   0.734   0.492   0.409   0.322   0.166   1.000
    0.01    -4.365   0.977    0.533   -1.485   -0.499   -2.773   0.248   6.753   -0.214   0.720    1.094    2.191   1.416   -0.0070   -0.207   0.390    0.0981   0.0334   0.00755   -0.0055   0.0036   0.168   0.242   1.471   -0.714   -0.336   -0.270    865   -1.186   1.839   0.734   0.492   0.404   0.325   0.166   1.000
    0.02    -4.348   0.976    0.549   -1.488   -0.501   -2.772   0.247   6.502   -0.208   0.730    1.149    2.189   1.453   -0.0167   -0.199   0.387    0.1009   0.0327   0.00759   -0.0055   0.0036   0.166   0.244   1.467   -0.711   -0.339   -0.263    865   -1.219   1.840   0.738   0.496   0.417   0.326   0.166   0.998
    0.03    -4.024   0.931    0.628   -1.494   -0.517   -2.782   0.246   6.291   -0.213   0.759    1.290    2.164   1.476   -0.0422   -0.202   0.378    0.1095   0.0331   0.00790   -0.0057   0.0037   0.167   0.246   1.467   -0.713   -0.338   -0.259    908   -1.273   1.841   0.747   0.503   0.446   0.344   0.165   0.986
    0.05    -3.479   0.887    0.674   -1.388   -0.615   -2.791   0.240   6.317   -0.244   0.826    1.449    2.138   1.549   -0.0663   -0.339   0.295    0.1226   0.0270   0.00803   -0.0063   0.0040   0.173   0.251   1.449   -0.701   -0.338   -0.263   1054   -1.346   1.843   0.777   0.520   0.508   0.377   0.162   0.938
    0.075   -3.293   0.902    0.726   -1.469   -0.596   -2.745   0.227   6.861   -0.266   0.815    1.535    2.446   1.772   -0.0794   -0.404   0.322    0.1165   0.0288   0.00811   -0.0070   0.0039   0.198   0.260   1.435   -0.695   -0.347   -0.219   1086   -1.471   1.845   0.782   0.535   0.504   0.418   0.158   0.887
    0.10    -3.666   0.993    0.698   -1.572   -0.536   -2.633   0.210   7.294   -0.229   0.831    1.615    2.969   1.916   -0.0294   -0.416   0.384    0.0998   0.0325   0.00744   -0.0073   0.0042   0.174   0.259   1.449   -0.708   -0.391   -0.201   1032   -1.624   1.847   0.769   0.543   0.445   0.426   0.170   0.870
    0.15    -4.866   1.267    0.510   -1.669   -0.490   -2.458   0.183   8.031   -0.211   0.749    1.877    3.544   2.161    0.0642   -0.407   0.417    0.0760   0.0388   0.00716   -0.0069   0.0042   0.198   0.254   1.461   -0.715   -0.449   -0.099    878   -1.931   1.852   0.769   0.543   0.382   0.387   0.180   0.876
    0.20    -5.411   1.366    0.447   -1.750   -0.451   -2.421   0.182   8.385   -0.163   0.764    2.069    3.707   2.465    0.0968   -0.311   0.404    0.0571   0.0437   0.00688   -0.0060   0.0041   0.204   0.237   1.484   -0.721   -0.393   -0.198    748   -2.188   1.856   0.761   0.552   0.339   0.338   0.186   0.870
    0.25    -5.962   1.458    0.274   -1.711   -0.404   -2.392   0.189   7.534   -0.150   0.716    2.205    3.343   2.766    0.1441   -0.172   0.466    0.0437   0.0463   0.00556   -0.0055   0.0036   0.185   0.206   1.581   -0.787   -0.339   -0.210    654   -2.381   1.861   0.744   0.545   0.340   0.316   0.191   0.850
    0.30    -6.403   1.528    0.193   -1.770   -0.321   -2.376   0.195   6.990   -0.131   0.737    2.306    3.334   3.011    0.1597   -0.084   0.528    0.0323   0.0508   0.00458   -0.0049   0.0031   0.164   0.210   1.586   -0.795   -0.447   -0.121    587   -2.518   1.865   0.727   0.568   0.340   0.300   0.198   0.819
    0.40    -7.566   1.739   -0.020   -1.594   -0.426   -2.303   0.185   7.012   -0.159   0.738    2.398    3.544   3.203    0.1410    0.085   0.540    0.0209   0.0432   0.00401   -0.0037   0.0028   0.160   0.226   1.544   -0.770   -0.525   -0.086    503   -2.657   1.874   0.690   0.593   0.356   0.264   0.206   0.743
    0.50    -8.379   1.872   -0.121   -1.577   -0.440   -2.296   0.186   6.902   -0.153   0.718    2.355    3.016   3.333    0.1474    0.233   0.638    0.0092   0.0405   0.00388   -0.0027   0.0025   0.184   0.217   1.554   -0.770   -0.407   -0.281    457   -2.669   1.883   0.663   0.611   0.379   0.263   0.208   0.684
    0.75    -9.841   2.021   -0.042   -1.757   -0.443   -2.232   0.186   5.522   -0.090   0.795    1.995    2.616   3.054    0.1764    0.411   0.776   -0.0082   0.0420   0.00420   -0.0016   0.0016   0.216   0.154   1.626   -0.780   -0.371   -0.285    410   -2.401   1.906   0.606   0.633   0.430   0.326   0.221   0.562
    1.00   -11.011   2.180   -0.069   -1.707   -0.527   -2.158   0.169   5.650   -0.105   0.556    1.447    2.470   2.562    0.2593    0.479   0.771   -0.0131   0.0426   0.00409   -0.0006   0.0006   0.596   0.117   1.616   -0.733   -0.128   -0.756    400   -1.955   1.929   0.579   0.628   0.470   0.353   0.225   0.467
    1.50   -12.469   2.270    0.047   -1.621   -0.630   -2.063   0.158   5.795   -0.058   0.480    0.330    2.108   1.453    0.2881    0.566   0.748   -0.0187   0.0380   0.00424    0.0000   0.0000   0.596   0.117   1.616   -0.733   -0.128   -0.756    400   -1.025   1.974   0.541   0.603   0.497   0.399   0.222   0.364
    2.00   -12.969   2.271    0.149   -1.512   -0.768   -2.104   0.158   6.632   -0.028   0.401   -0.514    1.327   0.657    0.3112    0.562   0.763   -0.0258   0.0252   0.00448    0.0000   0.0000   0.596   0.117   1.616   -0.733   -0.128   -0.756    400   -0.299   2.019   0.529   0.588   0.499   0.400   0.226   0.298
    3.00   -13.306   2.150    0.368   -1.315   -0.890   -2.051   0.148   6.759    0.000   0.206   -0.848    0.601   0.367    0.3478    0.534   0.686   -0.0311   0.0236   0.00345    0.0000   0.0000   0.596   0.117   1.616   -0.733   -0.128   -0.756    400    0.000   2.110   0.527   0.578   0.500   0.417   0.229   0.234
    4.00   -14.020   2.132    0.726   -1.506   -0.885   -1.986   0.135   7.978    0.000   0.105   -0.793    0.568   0.306    0.3747    0.522   0.691   -0.0413   0.0102   0.00603    0.0000   0.0000   0.596   0.117   1.616   -0.733   -0.128   -0.756    400    0.000   2.200   0.521   0.559   0.543   0.393   0.237   0.202
    5.00   -14.558   2.116    1.027   -1.721   -0.878   -2.021   0.135   8.538    0.000   0.000   -0.748    0.356   0.268    0.3382    0.477   0.670   -0.0281   0.0034   0.00805    0.0000   0.0000   0.596   0.117   1.616   -0.733   -0.128   -0.756    400    0.000   2.291   0.502   0.551   0.534   0.421   0.237   0.184
    7.50   -15.509   2.223    0.169   -0.756   -1.077   -2.179   0.165   8.468    0.000   0.000   -0.664    0.075   0.374    0.3754    0.321   0.757   -0.0205   0.0050   0.00280    0.0000   0.0000   0.596   0.117   1.616   -0.733   -0.128   -0.756    400    0.000   2.517   0.457   0.546   0.523   0.438   0.271   0.176
    10.0   -15.975   2.132    0.367   -0.800   -1.282   -2.244   0.180   6.564    0.000   0.000   -0.576   -0.027   0.297    0.3506    0.174   0.621    0.0009   0.0099   0.00458    0.0000   0.0000   0.596   0.117   1.616   -0.733   -0.128   -0.756    400    0.000   2.744   0.441   0.543   0.466   0.438   0.290   0.154
    """)


class CampbellBozorgnia2014LowQ(CampbellBozorgnia2014):
    """
    Implements the Campbell & Bozorgnia (2014) NGA-West2 GMPE for regions with
    high attenuation (low quality factor, Q) (i.e. Japan, Italy)
    """
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT         c0      c1       c2       c3       c4       c5      c6      c7       c9     c10      c11      c12     c13       c14      c15     c16       c17      c18       c19       c20      Dc20      a2      h1      h2       h3       h5       h6     k1       k2      k3    phi1    phi2    tau1    tau2    phiC  rholny
    pgv     -2.895   1.510    0.270   -1.299   -0.453   -2.466   0.204   5.837   -0.168   0.305    1.713    2.602   2.457    0.1060    0.332   0.585    0.0517   0.0327   0.00613   -0.0017   -0.0006   0.596   0.117   1.616   -0.733   -0.128   -0.756    400   -1.955   1.929   0.655   0.494   0.317   0.297   0.190   0.684
    pga     -4.416   0.984    0.537   -1.499   -0.496   -2.773   0.248   6.768   -0.212   0.720    1.090    2.186   1.420   -0.0064   -0.202   0.393    0.0977   0.0333   0.00757   -0.0055   -0.0035   0.167   0.241   1.474   -0.715   -0.337   -0.270    865   -1.186   1.839   0.734   0.492   0.409   0.322   0.166   1.000
    0.01    -4.365   0.977    0.533   -1.485   -0.499   -2.773   0.248   6.753   -0.214   0.720    1.094    2.191   1.416   -0.0070   -0.207   0.390    0.0981   0.0334   0.00755   -0.0055   -0.0035   0.168   0.242   1.471   -0.714   -0.336   -0.270    865   -1.186   1.839   0.734   0.492   0.404   0.325   0.166   1.000
    0.02    -4.348   0.976    0.549   -1.488   -0.501   -2.772   0.247   6.502   -0.208   0.730    1.149    2.189   1.453   -0.0167   -0.199   0.387    0.1009   0.0327   0.00759   -0.0055   -0.0035   0.166   0.244   1.467   -0.711   -0.339   -0.263    865   -1.219   1.840   0.738   0.496   0.417   0.326   0.166   0.998
    0.03    -4.024   0.931    0.628   -1.494   -0.517   -2.782   0.246   6.291   -0.213   0.759    1.290    2.164   1.476   -0.0422   -0.202   0.378    0.1095   0.0331   0.00790   -0.0057   -0.0034   0.167   0.246   1.467   -0.713   -0.338   -0.259    908   -1.273   1.841   0.747   0.503   0.446   0.344   0.165   0.986
    0.05    -3.479   0.887    0.674   -1.388   -0.615   -2.791   0.240   6.317   -0.244   0.826    1.449    2.138   1.549   -0.0663   -0.339   0.295    0.1226   0.0270   0.00803   -0.0063   -0.0037   0.173   0.251   1.449   -0.701   -0.338   -0.263   1054   -1.346   1.843   0.777   0.520   0.508   0.377   0.162   0.938
    0.075   -3.293   0.902    0.726   -1.469   -0.596   -2.745   0.227   6.861   -0.266   0.815    1.535    2.446   1.772   -0.0794   -0.404   0.322    0.1165   0.0288   0.00811   -0.0070   -0.0037   0.198   0.260   1.435   -0.695   -0.347   -0.219   1086   -1.471   1.845   0.782   0.535   0.504   0.418   0.158   0.887
    0.10    -3.666   0.993    0.698   -1.572   -0.536   -2.633   0.210   7.294   -0.229   0.831    1.615    2.969   1.916   -0.0294   -0.416   0.384    0.0998   0.0325   0.00744   -0.0073   -0.0034   0.174   0.259   1.449   -0.708   -0.391   -0.201   1032   -1.624   1.847   0.769   0.543   0.445   0.426   0.170   0.870
    0.15    -4.866   1.267    0.510   -1.669   -0.490   -2.458   0.183   8.031   -0.211   0.749    1.877    3.544   2.161    0.0642   -0.407   0.417    0.0760   0.0388   0.00716   -0.0069   -0.0030   0.198   0.254   1.461   -0.715   -0.449   -0.099    878   -1.931   1.852   0.769   0.543   0.382   0.387   0.180   0.876
    0.20    -5.411   1.366    0.447   -1.750   -0.451   -2.421   0.182   8.385   -0.163   0.764    2.069    3.707   2.465    0.0968   -0.311   0.404    0.0571   0.0437   0.00688   -0.0060   -0.0031   0.204   0.237   1.484   -0.721   -0.393   -0.198    748   -2.188   1.856   0.761   0.552   0.339   0.338   0.186   0.870
    0.25    -5.962   1.458    0.274   -1.711   -0.404   -2.392   0.189   7.534   -0.150   0.716    2.205    3.343   2.766    0.1441   -0.172   0.466    0.0437   0.0463   0.00556   -0.0055   -0.0033   0.185   0.206   1.581   -0.787   -0.339   -0.210    654   -2.381   1.861   0.744   0.545   0.340   0.316   0.191   0.850
    0.30    -6.403   1.528    0.193   -1.770   -0.321   -2.376   0.195   6.990   -0.131   0.737    2.306    3.334   3.011    0.1597   -0.084   0.528    0.0323   0.0508   0.00458   -0.0049   -0.0035   0.164   0.210   1.586   -0.795   -0.447   -0.121    587   -2.518   1.865   0.727   0.568   0.340   0.300   0.198   0.819
    0.40    -7.566   1.739   -0.020   -1.594   -0.426   -2.303   0.185   7.012   -0.159   0.738    2.398    3.544   3.203    0.1410    0.085   0.540    0.0209   0.0432   0.00401   -0.0037   -0.0034   0.160   0.226   1.544   -0.770   -0.525   -0.086    503   -2.657   1.874   0.690   0.593   0.356   0.264   0.206   0.743
    0.50    -8.379   1.872   -0.121   -1.577   -0.440   -2.296   0.186   6.902   -0.153   0.718    2.355    3.016   3.333    0.1474    0.233   0.638    0.0092   0.0405   0.00388   -0.0027   -0.0034   0.184   0.217   1.554   -0.770   -0.407   -0.281    457   -2.669   1.883   0.663   0.611   0.379   0.263   0.208   0.684
    0.75    -9.841   2.021   -0.042   -1.757   -0.443   -2.232   0.186   5.522   -0.090   0.795    1.995    2.616   3.054    0.1764    0.411   0.776   -0.0082   0.0420   0.00420   -0.0016   -0.0032   0.216   0.154   1.626   -0.780   -0.371   -0.285    410   -2.401   1.906   0.606   0.633   0.430   0.326   0.221   0.562
    1.00   -11.011   2.180   -0.069   -1.707   -0.527   -2.158   0.169   5.650   -0.105   0.556    1.447    2.470   2.562    0.2593    0.479   0.771   -0.0131   0.0426   0.00409   -0.0006   -0.0030   0.596   0.117   1.616   -0.733   -0.128   -0.756    400   -1.955   1.929   0.579   0.628   0.470   0.353   0.225   0.467
    1.50   -12.469   2.270    0.047   -1.621   -0.630   -2.063   0.158   5.795   -0.058   0.480    0.330    2.108   1.453    0.2881    0.566   0.748   -0.0187   0.0380   0.00424    0.0000   -0.0019   0.596   0.117   1.616   -0.733   -0.128   -0.756    400   -1.025   1.974   0.541   0.603   0.497   0.399   0.222   0.364
    2.00   -12.969   2.271    0.149   -1.512   -0.768   -2.104   0.158   6.632   -0.028   0.401   -0.514    1.327   0.657    0.3112    0.562   0.763   -0.0258   0.0252   0.00448    0.0000   -0.0005   0.596   0.117   1.616   -0.733   -0.128   -0.756    400   -0.299   2.019   0.529   0.588   0.499   0.400   0.226   0.298
    3.00   -13.306   2.150    0.368   -1.315   -0.890   -2.051   0.148   6.759    0.000   0.206   -0.848    0.601   0.367    0.3478    0.534   0.686   -0.0311   0.0236   0.00345    0.0000    0.0000   0.596   0.117   1.616   -0.733   -0.128   -0.756    400    0.000   2.110   0.527   0.578   0.500   0.417   0.229   0.234
    4.00   -14.020   2.132    0.726   -1.506   -0.885   -1.986   0.135   7.978    0.000   0.105   -0.793    0.568   0.306    0.3747    0.522   0.691   -0.0413   0.0102   0.00603    0.0000    0.0000   0.596   0.117   1.616   -0.733   -0.128   -0.756    400    0.000   2.200   0.521   0.559   0.543   0.393   0.237   0.202
    5.00   -14.558   2.116    1.027   -1.721   -0.878   -2.021   0.135   8.538    0.000   0.000   -0.748    0.356   0.268    0.3382    0.477   0.670   -0.0281   0.0034   0.00805    0.0000    0.0000   0.596   0.117   1.616   -0.733   -0.128   -0.756    400    0.000   2.291   0.502   0.551   0.534   0.421   0.237   0.184
    7.50   -15.509   2.223    0.169   -0.756   -1.077   -2.179   0.165   8.468    0.000   0.000   -0.664    0.075   0.374    0.3754    0.321   0.757   -0.0205   0.0050   0.00280    0.0000    0.0000   0.596   0.117   1.616   -0.733   -0.128   -0.756    400    0.000   2.517   0.457   0.546   0.523   0.438   0.271   0.176
    10.0   -15.975   2.132    0.367   -0.800   -1.282   -2.244   0.180   6.564    0.000   0.000   -0.576   -0.027   0.297    0.3506    0.174   0.621    0.0009   0.0099   0.00458    0.0000    0.0000   0.596   0.117   1.616   -0.733   -0.128   -0.756    400    0.000   2.744   0.441   0.543   0.466   0.438   0.290   0.154
    """)


class CampbellBozorgnia2014JapanSite(CampbellBozorgnia2014):
    """
    Implements the Campbell & Bozorgnia (2014) NGA-West2 GMPE for the case in
    which the "Japan" shallow site response term is activited
    """
    SJ = 1


class CampbellBozorgnia2014HighQJapanSite(CampbellBozorgnia2014HighQ):
    """
    Implements the Campbell & Bozorgnia (2014) NGA-West2 GMPE, for the low
    attenuation (high quality factor) coefficients, for the case in which
    the "Japan" shallow site response term is activited
    """
    SJ = 1


class CampbellBozorgnia2014LowQJapanSite(CampbellBozorgnia2014LowQ):
    """
    Implements the Campbell & Bozorgnia (2014) NGA-West2 GMPE, for the high
    attenuation (low quality factor) coefficients, for the case in which
    the "Japan" shallow site response term is activited
    """
    SJ = 1
