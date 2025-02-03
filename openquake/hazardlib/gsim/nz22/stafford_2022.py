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
Module exports :class:`Stafford2022`
"""

import numpy as np
from scipy import stats

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib.gsim.chiou_youngs_2014 import (
    _get_centered_ztor,
    get_hanging_wall_term,
    get_geometric_spreading,
    get_magnitude_scaling,
    get_directivity,
    _get_basin_term,
    get_linear_site_term,
    get_nonlinear_site_term,
)

CONSTANTS = {
    "c2": 1.06,
    "c4": -2.1,
    "c4a": -0.5,
    "crb": 50.0,
    "c8a": 0.2695,
    "c11": 0.0,
    "phi6": 300.0,
    "phi6jp": 800.0,
}


def _sigmoid1d(x, start, finish, centre, slope):
    """
    Returns 1D sigmoid function allowing a smooth transition from `start` to
    `finish`. The transition is centred at `centre` and changes at a rate
    linked to `slope`
    """
    amplitude = finish - start
    y = start + amplitude / (1.0 + np.exp(-(x - centre) / slope))
    return y


def _empirical_sigma(T, r, m, start=0.4, finish=0.15):
    """
    Epistemic standard deviation associated with empirical constraint.
    Takes period `T`, rupture distance `r` and magnitude `m`.
    """
    centre_r = _sigmoid1d(T, 3.75, 5.75, 3.5, 0.5)
    slope_r = _sigmoid1d(T, 0.225, 1.3, 3.5, 0.5)
    centre_m = _sigmoid1d(T, 5.82, 6.4, 3.5, 0.5)
    slope_m = _sigmoid1d(T, 0.42, 0.38, 2.5, 0.2)
    amplitude = finish - start
    s_lnr = _sigmoid1d(
        np.log(np.clip(r, 10**-10, None)), 0.0, 1.0, centre_r, slope_r
    )
    s_m = _sigmoid1d(m, 1.0, 0.0, centre_m, slope_m)
    y = start + amplitude * s_lnr * s_m
    return y


def _saturation_sigma(m, r):
    """
    Standard deviation of the near-source saturation model.
    Takes a magnitude `m` and rupture distance `r`
    """
    return _sigmoid1d(
        np.log(np.clip(r, 10**-10, None)),
        0.6638 - 0.2570 * (np.clip(m, -np.inf, 7.0) - 6.0),
        0.0,
        0.7990,
        0.9835,
    )


def _anelastic_correction(T):
    """
    Mean anelastic attenuation correction -- a function of period `T`
    """
    return np.clip(0.0024 * np.tanh(0.8 * np.log(T / 1.8)), -np.inf, 0.0)


def _anelastic_sigma(T):
    """
    Standard deviation of the anelastic attenuation coefficient -- a function
    of period `T`
    """
    return _sigmoid1d(np.log(T), 0.00054, 0.0004, np.log(0.9), 0.2)


def _between_event(T, M):
    """
    Between-event standard deviation, function of period `T` and magnitude `M`
    """
    # between event
    β0_0 = 0.45
    β0_1 = 0.35
    β1 = 0.4
    β2 = 0.0
    β3 = 0.2
    τ0 = _sigmoid1d(np.log(T), β0_0, β1, β2, β3)
    τ1 = _sigmoid1d(np.log(T), β0_1, β1, β2, β3)

    τ = τ0 + (τ1 - τ0) * (np.clip(M, 5.0, 6.5) - 5.0) / 1.5
    return τ


def _between_station(T):
    """
    Between-station standard deviation, function of period `T`
    """
    β0_S2S = 0.3171
    β1_S2S = 0.3248
    β2_S2S = 0.7911
    β3_S2S = 0.8970
    β4_S2S = 0.7170

    ϕS2S = β0_S2S + β1_S2S * (T / β4_S2S) ** (β2_S2S) * np.exp(
        -β3_S2S * (T / β4_S2S)
    )
    return ϕS2S


def _neff_model(T):
    """
        neff_model(T)

    Model for the effective number of observations in NZ data, function of
    period `T`
    """
    β0 = 190.34
    β1 = 221.16
    β2 = -2.4341
    β3 = 0.10366
    β4 = 0.10299
    if T <= 0.3:
        return _sigmoid1d(np.log(T), β0, β1, β2, β3)
    else:
        return β1 / ((T / 0.3) ** β4)


def get_adjustments(T, ctx, adjust_c1, adjust_chm, adjust_c7, adjust_cg1):
    ρEhEx = 0.4
    epistemic_scale_factor = 0.893
    # The scale factor of 0.9 is applied based upon the discussion that it
    # accounts for the reduction in epistemic uncertainty when no perfect
    # correlation is assumed between rupture scenarios. See the note of Peter
    # and Brendon on slack.
    MEAN_ADJUSTMENT_TERMS_IF = {
        "Lower": {
            "delta_c1": (
                -1.28155
                * epistemic_scale_factor
                * _empirical_sigma(T, ctx.rrup, ctx.mag)
                if adjust_c1
                else 0.0
            ),
            "delta_c1hm": (
                -1.28155
                * epistemic_scale_factor
                * ρEhEx
                * _saturation_sigma(ctx.mag, ctx.rrup)
                if adjust_chm
                else 0.0
            ),
            "delta_c7": (-0.02578 if adjust_c7 else 0.0),
            "delta_c7b": (
                _sigmoid1d(np.log(T), -0.05737, 0.05733, -1.0324, 0.04875)
                if adjust_c7
                else 0.0
            ),
            "delta_cg1": (
                _anelastic_correction(T)
                - 1.28155 * epistemic_scale_factor * _anelastic_sigma(T)
                if adjust_cg1
                else 0.0
            ),
        },
        "Central": {
            "delta_c1": 0.0,
            "delta_c1hm": 0.0,
            "delta_c7": 0.0,
            "delta_c7b": (
                _sigmoid1d(np.log(T), -0.0865, 0.0, -1.5364, 0.3266)
                if adjust_c7
                else 0.0
            ),
            "delta_cg1": (_anelastic_correction(T) if adjust_cg1 else 0.0),
        },
        "Upper": {
            "delta_c1": (
                1.28155
                * epistemic_scale_factor
                * _empirical_sigma(T, ctx.rrup, ctx.mag)
                if adjust_c1
                else 0.0
            ),
            "delta_c1hm": (
                1.28155
                * epistemic_scale_factor
                * ρEhEx
                * _saturation_sigma(ctx.mag, ctx.rrup)
                if adjust_chm
                else 0.0
            ),
            "delta_c7": 0.0,
            "delta_c7b": 0.0,
            "delta_cg1": (
                _anelastic_correction(T)
                + 1.28155 * epistemic_scale_factor * _anelastic_sigma(T)
                if adjust_cg1
                else 0.0
            ),
        },
    }
    return MEAN_ADJUSTMENT_TERMS_IF


# Modified CY14 fucntions:


def get_stress_scaling(
    T, C, ctx, mu_branch, adjust_c1, adjust_chm, adjust_c7, adjust_cg1
):
    """This term includes adjustments related to stress scaling."""
    delta_c1 = get_adjustments(
        T, ctx, adjust_c1, adjust_chm, adjust_c7, adjust_cg1
    )[mu_branch]["delta_c1"]
    delta_c1hm = get_adjustments(
        T, ctx, adjust_c1, adjust_chm, adjust_c7, adjust_cg1
    )[mu_branch]["delta_c1hm"]
    return C["c1"] + delta_c1 + delta_c1hm


def get_far_field_distance_scaling(
    T, C, ctx, mu_branch, adjust_c1, adjust_chm, adjust_c7, adjust_cg1
):
    """
    Returns the far-field distance scaling term - both magnitude and
    distance. It includes adjustments made for NZ through delta_cg1.
    """
    delta_cg1 = get_adjustments(
        T, ctx, adjust_c1, adjust_chm, adjust_c7, adjust_cg1
    )[mu_branch]["delta_cg1"]

    # Get the attenuation distance scaling
    f_r = (CONSTANTS["c4a"] - CONSTANTS["c4"]) * np.log(
        np.sqrt(ctx.rrup**2.0 + CONSTANTS["crb"] ** 2.0)
    )
    # Get the magnitude dependent term
    f_rm = (
        C["cg1"]
        + delta_cg1
        + C["cg2"] / np.cosh(np.clip(ctx.mag - C["cg3"], 0.0, None))
    )
    return f_r + f_rm * ctx.rrup


def get_source_scaling_terms(
    T,
    C,
    ctx,
    delta_ztor,
    mu_branch,
    adjust_c1,
    adjust_chm,
    adjust_c7,
    adjust_cg1,
):
    """
    Returns additional source scaling parameters related to style of
    faulting, dip and top of rupture depth. It includes adjustments for NZ backbone model through
    delta_c7 and delta_c7b.
    """
    delta_c7 = get_adjustments(
        T, ctx, adjust_c1, adjust_chm, adjust_c7, adjust_cg1
    )[mu_branch]["delta_c7"]
    delta_c7b = get_adjustments(
        T, ctx, adjust_c1, adjust_chm, adjust_c7, adjust_cg1
    )[mu_branch]["delta_c7b"]

    f_src = np.zeros_like(ctx.mag)
    coshm = np.cosh(2.0 * np.clip(ctx.mag - 4.5, 0.0, None))
    # Style of faulting term
    pos = (30 <= ctx.rake) & (ctx.rake <= 150)
    neg = (-120 <= ctx.rake) & (ctx.rake <= -60)
    # reverse faulting flag
    f_src[pos] += C["c1a"] + (C["c1c"] / coshm[pos])
    # normal faulting flag
    f_src[neg] += C["c1b"] + (C["c1d"] / coshm[neg])
    # Top of rupture term
    f_src += (
        (C["c7"] + delta_c7) + ((C["c7b"] + delta_c7b) / coshm)
    ) * delta_ztor
    # Dip term
    f_src += (CONSTANTS["c11"] + (C["c11b"] / coshm)) * np.cos(
        np.radians(ctx.dip)
    ) ** 2
    return f_src


def get_ln_y_ref(
    T, C, ctx, mu_branch, adjust_c1, adjust_chm, adjust_c7, adjust_cg1
):
    """
    Returns the ground motion on the reference rock.
    """
    delta_ztor = _get_centered_ztor(ctx)
    return (
        get_stress_scaling(
            T, C, ctx, mu_branch, adjust_c1, adjust_chm, adjust_c7, adjust_cg1
        )
        + get_magnitude_scaling(C, ctx.mag, delta_cm=0)
        + get_source_scaling_terms(
            T,
            C,
            ctx,
            delta_ztor,
            mu_branch,
            adjust_c1,
            adjust_chm,
            adjust_c7,
            adjust_cg1,
        )
        + get_hanging_wall_term(C, ctx)
        + get_geometric_spreading(C, ctx.mag, ctx.rrup)
        + get_far_field_distance_scaling(
            T, C, ctx, mu_branch, adjust_c1, adjust_chm, adjust_c7, adjust_cg1
        )
        + get_directivity(C, ctx)
    )


def _nl_sigma(C, ctx, ln_y_ref):
    vs = ctx.vs30.clip(-np.inf, 1130.0)
    NL = C["phi2"] * (
        (
            np.exp(C["phi3"] * (vs - 360.0))
            - np.exp(C["phi3"] * (1130.0 - 360.0))
        )
        * (np.exp(ln_y_ref) / (np.exp(ln_y_ref) + C["phi4"]))
    )
    return NL


def get_stddevs(T, ln_y_ref, C, ctx, sigma_branch):
    """
    Returns the standard deviation model described in equation 8.16
    (Peter Stafford NSHM report)
    """
    tau = _between_event(T, ctx.mag)
    phi_S2S = _between_station(T)
    phi_SS = 0.39
    NL = _nl_sigma(C, ctx, ln_y_ref)
    phi = np.sqrt(
        phi_S2S**2 + (1.0 + NL) ** 2 * 0.736 * phi_SS**2 + 0.264 * phi_SS**2
    )
    # nominal total standard deviation for the branch
    sigma = np.sqrt((1.0 + NL) ** 2 * tau**2 + phi**2)

    # perform the potential inflation of σ for epistemic uncertainty
    neff = _neff_model(T)
    nfac = (
        _empirical_sigma(T, ctx.rrup, ctx.mag) / _empirical_sigma(T, 80.0, 5.0)
    ) ** 2

    ndof = neff / nfac
    if sigma_branch == "Lower":
        sigma = np.sqrt(
            (sigma**2 / (ndof - 1)) * stats.chi2.ppf(0.1, ndof - 1)
        )
    elif sigma_branch == "Central":
        sigma = np.sqrt(
            (sigma**2 / (ndof - 1)) * stats.chi2.ppf(0.5, ndof - 1)
        )
    elif sigma_branch == "Upper":
        sigma = np.sqrt(
            (sigma**2 / (ndof - 1)) * stats.chi2.ppf(0.9, ndof - 1)
        )
    else:
        print("sigma branch not recognised: "
              "must be one of :Lower, :Central, :Upper")
        sigma = np.nan
    return sigma, np.abs((1.0 + NL) * tau), phi


def get_mean_stddevs(
    T,
    mu_branch,
    sigma_branch,
    adjust_c1,
    adjust_chm,
    adjust_c7,
    adjust_cg1,
    C,
    ctx,
    imt
):
    """
    Return mean and standard deviation values.
    """
    # Get ground motion on reference rock
    ln_y_ref = get_ln_y_ref(
        T, C, ctx, mu_branch, adjust_c1, adjust_chm, adjust_c7, adjust_cg1
    )
    y_ref = np.exp(ln_y_ref)
    # Get the site amplification
    # Get basin depth
    f_z1pt0 = _get_basin_term(C, ctx, "Stafford2022", imt)
    # Get linear amplification term
    f_lin = get_linear_site_term("Stafford2022", C, ctx)
    # Get nonlinear amplification term
    f_nl, _f_nl_scaling = get_nonlinear_site_term(C, ctx, y_ref)

    # Add on the site amplification
    mean = ln_y_ref + (f_lin + f_nl + f_z1pt0)
    # Get standard deviations
    sig, tau, phi = get_stddevs(T, ln_y_ref, C, ctx, sigma_branch)

    return mean, sig, tau, phi


class Stafford2022(GMPE):
    """
    Implements Backbone model developed by Peter Stafford for NZ NSHM revision.
    For more details see Peter Stafford's GNS report.
    The base model implementation remains the same as for Chiou and Youngs
    (2014).

    Chiou, B. S.-J. and Youngs, R. R. (2014), "Updated of the Chiou and Youngs
    NGA Model for the Average Horizontal Component of Peak Ground Motion and
    Response Spectra, Earthquake Spectra, 30(3), 1117 - 1153,
    DOI: 10.1193/072813EQS219M
    """

    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is orientation-independent
    #: measure :attr:`~openquake.hazardlib.const.IMC.RotD50`,
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see chapter "Variance model".
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Required site parameters are Vs30, Vs30 measured flag
    #: and Z1.0.
    REQUIRES_SITES_PARAMETERS = {"vs30", "vs30measured", "z1pt0"}

    #: Required rupture parameters are magnitude, rake,
    #: dip and ztor.
    REQUIRES_RUPTURE_PARAMETERS = {"dip", "rake", "mag", "ztor"}

    #: Required distance measures are RRup, Rjb and Rx.
    REQUIRES_DISTANCES = {"rrup", "rjb", "rx"}

    #: Reference shear wave velocity
    DEFINED_FOR_REFERENCE_VELOCITY = 1130

    def __init__(
        self,
        mu_branch="Central",
        sigma_branch="Central",
        adjust_c1=True,
        adjust_chm=True,
        adjust_c7=True,
        adjust_cg1=True,
    ):
        """
        Additional parameter for epistemic central,
        lower and upper bounds.
        """
        self.mu_branch = mu_branch
        self.sigma_branch = sigma_branch
        self.adjust_c1 = adjust_c1
        self.adjust_chm = adjust_chm
        self.adjust_c7 = adjust_c7
        self.adjust_cg1 = adjust_cg1

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            if repr(imt) == "PGV":
                print("Invalid IMT provided. The model does not predict"
                      " ground motions for PGV.")
                sig[m], tau[m], phi[m] = None, None, None
            elif repr(imt) == "PGA":
                pga_mean, pga_sig, pga_tau, pga_phi = get_mean_stddevs(
                    SA(0.01).period,
                    self.mu_branch,
                    self.sigma_branch,
                    self.adjust_c1,
                    self.adjust_chm,
                    self.adjust_c7,
                    self.adjust_cg1,
                    self.COEFFS[SA(0.01)],
                    ctx,
                    imt
                )
                # Peter has used T = 0.01 as the period for PGA because the
                # coefficients (for 0.01s and PGA) are identical.
                mean[m] = pga_mean
                sig[m], tau[m], phi[m] = pga_sig, pga_tau, pga_phi
            else:
                T = imt.period
                imt_mean, imt_sig, imt_tau, imt_phi = get_mean_stddevs(
                    T,
                    self.mu_branch,
                    self.sigma_branch,
                    self.adjust_c1,
                    self.adjust_chm,
                    self.adjust_c7,
                    self.adjust_cg1,
                    self.COEFFS[imt],
                    ctx,
                    imt
                )
                mean[m] = imt_mean
                sig[m], tau[m], phi[m] = imt_sig, imt_tau, imt_phi

    #: Coefficient tables are constructed from values in tables 1 - 5
    COEFFS = CoeffsTable(
        sa_damping=5,
        table="""\
IMT     c1      c1a     c1b     c1c     c1d     cn      cm    c2      c3    c4     c4a  crb   c5      chm     c6      c7      c7b     c8     c8a    c8b       c9     c9a    c9b     c11      c11b        cg1        cg2       cg3     phi1       phi2      phi3     phi4     phi5   phi6  gjpit  gwn      phi1jp  phi5jp   phi6jp     tau1    tau2    sig1    sig2    sig3    sig2jp
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
""",
    )
