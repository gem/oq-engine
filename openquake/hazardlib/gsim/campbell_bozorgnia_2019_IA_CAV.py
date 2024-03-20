# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2023 GEM Foundation
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
from openquake.hazardlib.gsim.abrahamson_2014 import get_epistemic_sigma
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, IA, CAV

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
    #print
    print(f"hypo_depth: {ctx.hypo_depth}")
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
    #print
    print(f"frv: {frv} fnm: {fnm}")
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
    #print check f-term values
    print("mag_term: " + str(_get_magnitude_term(C, ctx.mag)))
    print("geom_att_term: " + str(_get_geometric_attenuation_term(C, ctx.mag, ctx.rrup)))
    print("style_fault_term: " + str(_get_style_of_faulting_term(C, ctx)))
    print("hangwall_term: " + str(_get_hanging_wall_term(C, ctx)))
    print("shall_site_term: " + str(_get_shallow_site_response_term(SJ, C, temp_vs30, a1100)))
    print("basin_term: " + str(_get_basin_response_term(SJ, C, temp_z2pt5)))
    print("hypodepth_term: " + str(_get_hypocentral_depth_term(C, ctx)))
    print("faultdip_term: " + str(_get_fault_dip_term(C, ctx)))
    print("anel_att_term: "  + str(_get_anelastic_attenuation_term(C, ctx.rrup)))

    return (_get_magnitude_term(C, ctx.mag) +
            _get_geometric_attenuation_term(C, ctx.mag, ctx.rrup) +
            _get_style_of_faulting_term(C, ctx) +
            _get_hanging_wall_term(C, ctx) +
            _get_shallow_site_response_term(SJ, C, temp_vs30, a1100) +
            _get_basin_response_term(SJ, C, temp_z2pt5) +
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
    Returns the inter-event random effects coefficient (tau)
    Equation 28.
    """
    rho_ln_pga = C["rho2pga"] + (C["rho1pga"] - C["rho2pga"]) * (5.5 - mag)
    rho_ln_pga[mag <= 4.5] = C["rho1pga"]
    rho_ln_pga[mag >= 5.5] = C["rho2pga"]
    return rho_ln_pga

class CampbellBozorgnia2019_IA_CAV(GMPE):
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
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {CAV, IA}

    #: Supported intensity measure component is orientation-independent
    #: average horizontal :attr:`~openquake.hazardlib.const.IMC.GMRotI50`
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

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
        self.estimate_ztor = int(kwargs.get('estimate_ztor', 0))
        self.estimate_width = int(kwargs.get('estimate_width', 0))
        self.estimate_hypo_depth = int(kwargs.get('estimate_hypo_depth', 0))
        self.sigma_mu_epsilon = sigma_mu_epsilon

        if self.estimate_width:
            # To estimate a width, the GMPE needs Zbot
            self.REQUIRES_RUPTURE_PARAMETERS |= {"zbot"}

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

        #print check what is ctx?
        print('CTX; ' + 'type:' + str(type(ctx)))
        for field in ctx.dtype.names:
            for value in ctx[field]:
                print(f"Field: {field}, DataType: {ctx[field].dtype}, Value: {value}")
            print()

        print(str(ctx))

        C_PGA = self.COEFFS[PGA()]
        # Get mean and standard deviation of PGA on rock (Vs30 1100 m/s^2)
        pga1100 = np.exp(get_mean_values(self.SJ, C_PGA, ctx))
        for m, imt in enumerate(imts):
            #print
            print("m: " + str(m))
            print("imt: " + str(imt) + '\n')
            C = self.COEFFS[imt]
            # Get mean and standard deviations for IMT
            mean[m] = get_mean_values(self.SJ, C, ctx, pga1100)
            mean[m] += (self.sigma_mu_epsilon*get_epistemic_sigma(ctx))
            if imt.string[:2] == "SA" and imt.period < 0.25:
                # According to Campbell & Bozorgnia (2013) [NGA West 2 Report]
                # If Sa (T) < PGA for T < 0.25 then set mean Sa(T) to mean PGA
                # Get PGA on soil
                pga = get_mean_values(self.SJ, C_PGA, ctx, pga1100)
                idx = mean[m] <= pga
                mean[m, idx] = pga[idx]
                mean[m] += (self.sigma_mu_epsilon*get_epistemic_sigma(ctx))

            print(str(imt) + ': ' + str(np.exp(mean[m])))

            # Get stddevs for PGA on basement rock
            tau_lnpga_b = _get_taulny(C_PGA, ctx.mag)
            phi_lnpga_b = np.sqrt(_get_philny(C_PGA, ctx.mag) ** 2. -
                                  CONSTS["philnAF"] ** 2.)

            # Get tau_lny on the basement rock
            tau_lnyb = _get_taulny(C, ctx.mag)
            # Get phi_lny on the basement rock
            phi_lnyb = np.sqrt(_get_philny(C, ctx.mag) ** 2. -
                               C["philnAF"] ** 2.)
            # Get site scaling term
            alpha = _get_alpha(C, ctx.vs30, pga1100)
            # Evaluate tau according to equation 29
            t = np.sqrt(tau_lnyb**2 + alpha**2 * tau_lnpga_b**2 +
                        2.0 * alpha * _get_rholnpga(C, ctx.mag) * tau_lnyb * tau_lnpga_b)

            # Evaluate phi according to equation 30
            ##old phi calc from cb14
            # p = np.sqrt(
            #     phi_lnyb**2 + C["philnAF"]**2 + alpha**2 * phi_lnpga_b**2
            #     + 2.0 * alpha * _get_rholnpga(C, ctx.mag) * phi_lnyb * phi_lnpga_b)
            ##new phi calc from cb19 spreadsheet
            p = np.sqrt(
                (_get_philny(C, ctx.mag))**2. + alpha**2. * _get_philny(C_PGA, ctx.mag) ** 2.
                + 2.0 * alpha * _get_rholnpga(C, ctx.mag) * (_get_philny(C, ctx.mag)) * _get_philny(C_PGA, ctx.mag))
            #print check phi calc
            print(f'phi calc: phi_lnyb={phi_lnyb} philnAF={C["philnAF"]} alpha={alpha} phi_lnpga_b={phi_lnpga_b} rholnpga={_get_rholnpga(C, ctx.mag)}')
            sig[m] = np.sqrt(t**2 + p**2)
            tau[m] = t
            phi[m] = p
            #print check sigma tau phi
            print(f"sigma: {sig[m]} tau: {tau[m]} phi: {phi[m]}")

    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT        c0      c1      c2       c3       c4       c5      c6      c7      c8       c9     c10     c11     c12     c13       c14      c15     c16      c17      c18       c19       c20   Dc20      a2      h1      h2       h3       h5       h6    k1       k2      k3    phi1    phi2    tau1    tau2   rho1pga   rho2pga   philnAF
    pgv    -2.895    1.51    0.27   -1.299   -0.453   -2.466   0.204   5.837       0   -0.168   0.305   1.713   2.602   2.457     0.106    0.332   0.585   0.0517   0.0327   0.00613   -0.0017      0   0.596   0.117   1.616   -0.733   -0.128   -0.756   400   -1.955   1.929   0.655   0.494   0.317   0.297     0.877     0.654     0.300
    pga    -4.416   0.984   0.537   -1.499   -0.496   -2.773   0.248   6.768       0   -0.212    0.72    1.09   2.186    1.42   -0.0064   -0.202   0.393   0.0977   0.0333   0.00757   -0.0055      0   0.167   0.241   1.474   -0.715   -0.337    -0.27   865   -1.186   1.839   0.734   0.492   0.409   0.322     1.000     1.000     0.300
    cav     -4.75   1.397   0.282   -1.062    -0.17   -1.624   0.134   6.325   0.054     -0.1   0.469   1.015   1.208   1.777    0.1248   -0.191   1.087   0.0432   0.0127   0.00429   -0.0043      0   0.167   0.241   1.474   -0.715   -0.337    -0.27   400   -1.311       1   0.514   0.394   0.276   0.257     0.842     0.780     0.300
    ia    -10.272   2.318    0.88   -2.672   -0.837   -4.441   0.416   4.869   0.187   -0.196   1.165   1.596   2.829    2.76     0.108   -0.315   1.612   0.1311   0.0453   0.01242   -0.0103      0   0.167   0.241   1.474   -0.715   -0.337    -0.27   400   -1.982       1   1.174   0.809   0.614   0.435     0.948     0.911     0.616
    """)


class CampbellBozorgnia2019HighQ(CampbellBozorgnia2019_IA_CAV):
    """

    Implements the Campbell & Bozorgnia (2014) NGA-West2 GMPE for regions with
    low attenuation (high quality factor, Q) (i.e. China, Turkey)
    """
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT        c0      c1      c2       c3       c4       c5      c6      c7      c8       c9     c10     c11     c12     c13       c14      c15     c16      c17      c18       c19       c20      Dc20      a2      h1      h2       h3       h5       h6    k1       k2      k3    phi1    phi2    tau1    tau2   rho1pga   rho2pga   philnAF
    pga    -4.416   0.984   0.537   -1.499   -0.496   -2.773   0.248   6.768       0   -0.212    0.72    1.09   2.186    1.42   -0.0064   -0.202   0.393   0.0977   0.0333   0.00757   -0.0055    0.0036   0.167   0.241   1.474   -0.715   -0.337    -0.27   865   -1.186   1.839   0.734   0.492   0.409   0.322     1.000     1.000     0.300
    pgv    -2.895    1.51    0.27   -1.299   -0.453   -2.466   0.204   5.837       0   -0.168   0.305   1.713   2.602   2.457     0.106    0.332   0.585   0.0517   0.0327   0.00613   -0.0017    0.0017   0.596   0.117   1.616   -0.733   -0.128   -0.756   400   -1.955   1.929   0.655   0.494   0.317   0.297     0.877     0.654     0.300
    cav     -4.75   1.397   0.282   -1.062    -0.17   -1.624   0.134   6.325   0.054     -0.1   0.469   1.015   1.208   1.777    0.1248   -0.191   1.087   0.0432   0.0127   0.00429   -0.0043    0.0027   0.167   0.241   1.474   -0.715   -0.337    -0.27   400   -1.311       1   0.514   0.394   0.276   0.257     0.842     0.780     0.300
    ia    -10.272   2.318    0.88   -2.672   -0.837   -4.441   0.416   4.869   0.187   -0.196   1.165   1.596   2.829    2.76     0.108   -0.315   1.612   0.1311   0.0453   0.01242   -0.0103    0.0064   0.167   0.241   1.474   -0.715   -0.337    -0.27   400   -1.982       1   1.174   0.809   0.614   0.435     0.948     0.911     0.616
    """)


class CampbellBozorgnia2019LowQ(CampbellBozorgnia2019_IA_CAV):
    """
    Implements the Campbell & Bozorgnia (2014) NGA-West2 GMPE for regions with
    high attenuation (low quality factor, Q) (i.e. Japan, Italy)
    """
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT        c0      c1      c2       c3       c4       c5      c6      c7      c8       c9     c10     c11     c12     c13       c14      c15     c16      c17      c18       c19       c20      Dc20      a2      h1      h2       h3       h5       h6    k1       k2      k3    phi1    phi2    tau1    tau2   rho1pga   rho2pga   philnAF
    pga    -4.416   0.984   0.537   -1.499   -0.496   -2.773   0.248   6.768       0   -0.212    0.72    1.09   2.186    1.42   -0.0064   -0.202   0.393   0.0977   0.0333   0.00757   -0.0055   -0.0035   0.167   0.241   1.474   -0.715   -0.337    -0.27   865   -1.186   1.839   0.734   0.492   0.409   0.322     1.000     1.000     0.300
    pgv    -2.895    1.51    0.27   -1.299   -0.453   -2.466   0.204   5.837       0   -0.168   0.305   1.713   2.602   2.457     0.106    0.332   0.585   0.0517   0.0327   0.00613   -0.0017   -0.0006   0.596   0.117   1.616   -0.733   -0.128   -0.756   400   -1.955   1.929   0.655   0.494   0.317   0.297     0.877     0.654     0.300
    cav     -4.75   1.397   0.282   -1.062    -0.17   -1.624   0.134   6.325   0.054     -0.1   0.469   1.015   1.208   1.777    0.1248   -0.191   1.087   0.0432   0.0127   0.00429   -0.0043   -0.0024   0.167   0.241   1.474   -0.715   -0.337    -0.27   400   -1.311       1   0.514   0.394   0.276   0.257     0.842     0.780     0.300
    ia    -10.272   2.318    0.88   -2.672   -0.837   -4.441   0.416   4.869   0.187   -0.196   1.165   1.596   2.829    2.76     0.108   -0.315   1.612   0.1311   0.0453   0.01242   -0.0103   -0.0051   0.167   0.241   1.474   -0.715   -0.337    -0.27   400   -1.982       1   1.174   0.809   0.614   0.435     0.948     0.911     0.616
    """)


class CampbellBozorgnia2019JapanSite(CampbellBozorgnia2019_IA_CAV):
    """
    Implements the Campbell & Bozorgnia (2014) NGA-West2 GMPE for the case in
    which the "Japan" shallow site response term is activited
    """
    SJ = 1


class CampbellBozorgnia2019HighQJapanSite(CampbellBozorgnia2019HighQ):
    """
    Implements the Campbell & Bozorgnia (2014) NGA-West2 GMPE, for the low
    attenuation (high quality factor) coefficients, for the case in which
    the "Japan" shallow site response term is activited
    """
    SJ = 1


class CampbellBozorgnia2019LowQJapanSite(CampbellBozorgnia2019LowQ):
    """
    Implements the Campbell & Bozorgnia (2014) NGA-West2 GMPE, for the high
    attenuation (low quality factor) coefficients, for the case in which
    the "Japan" shallow site response term is activited
    """
    SJ = 1
