"""
New Zealand National Seismic Hazard Model 2022 Revision modification of Abrahamson and Gulerce 2020 GMMs.

Backarc term added.

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

Module exports :class:`NZNSHM2022_AbrahamsonGulerce2020SInter`
               :class:`class NZNSHM2022_AbrahamsonGulerce2020SSlab`
"""

import numpy as np

from scipy.interpolate import interp1d

from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA
from openquake.hazardlib.gsim.base import add_alias
from openquake.hazardlib.gsim.abrahamson_gulerce_2020 import (
    AbrahamsonGulerce2020SInter,
    get_acceleration_on_reference_rock,
    get_epistemic_adjustment,
    get_mean_acceleration,
    get_tau_phi,
    SUPPORTED_REGIONS,
)
from openquake.hazardlib.gsim.nz22.const import periods, theta7s, theta8s


def get_backarc_term(trt, imt, ctx):
    """
    The backarc correction factors to be applied with the ground motion
    prediction. In the NZ context, it is applied to only subduction
    intraslab events.  It is essentially the correction factor taken
    from BC Hydro 2016. Abrahamson et al. (2016) Earthquake Spectra.
    The correction is applied only for backarc sites as function of
    distance.
    """
    period = imt.period
    w_epi_factor = 1.008

    theta7_itp = interp1d(np.log(periods[1:]), theta7s[1:])
    theta8_itp = interp1d(np.log(periods[1:]), theta8s[1:])
    # Note that there is no correction for PGV. Hence, I make theta7
    # and theta8 as 0 for periods < 0.
    if period < 0:
        theta7 = 0.0
        theta8 = 0.0
    elif period >= 0 and period < 0.02:
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
        f_faba[backarc] = theta7 + theta8 * np.log(fixed_dists / 40.0)
        return f_faba * w_epi_factor
    else:
        f_faba = np.zeros_like(dists)
        return f_faba


def get_acceleration_on_reference_rock_ba(
    C, trt, region, ctx, apply_adjustment
):
    return get_acceleration_on_reference_rock(
        C, trt, region, ctx, apply_adjustment
    ) + get_backarc_term(trt, PGA(), ctx)


def get_mean_acceleration_ba(
    C, trt, region, ctx, pga1000, apply_adjustment, imt
):
    return get_mean_acceleration(
        C, trt, region, ctx, pga1000, apply_adjustment, usgs_baf=1.0
    ) + get_backarc_term(trt, imt, ctx)


class NZNSHM2022_AbrahamsonGulerce2020SInter(AbrahamsonGulerce2020SInter):
    def __init__(
        self,
        region="GLO",
        ergodic=True,
        apply_usa_adjustment=False,
        sigma_mu_epsilon=0.0,
    ):
        super().__init__(
            region=region,
            ergodic=ergodic,
            apply_usa_adjustment=apply_usa_adjustment,
            sigma_mu_epsilon=sigma_mu_epsilon)

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        trt = self.DEFINED_FOR_TECTONIC_REGION_TYPE
        C_PGA = self.COEFFS[PGA()]
        pga1000 = get_acceleration_on_reference_rock_ba(
            C_PGA, trt, self.region, ctx, self.apply_usa_adjustment
        )
        pga1000 = np.exp(pga1000)

        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            mean[m] = get_mean_acceleration_ba(
                C,
                trt,
                self.region,
                ctx,
                pga1000,
                self.apply_usa_adjustment,
                imt,
            )
            if self.sigma_mu_epsilon:
                # Apply an epistmic adjustment factor
                mean[m] += self.sigma_mu_epsilon * get_epistemic_adjustment(
                    C, ctx.rrup
                )
            # Get the standard deviations
            tau_m, phi_m = get_tau_phi(
                C,
                C_PGA,
                self.region,
                imt.period,
                ctx.rrup,
                ctx.vs30,
                pga1000,
                self.ergodic,
            )
            tau[m] = tau_m
            phi[m] = phi_m
        sig += np.sqrt(tau**2.0 + phi**2.0)


class NZNSHM2022_AbrahamsonGulerce2020SSlab(
    NZNSHM2022_AbrahamsonGulerce2020SInter
):
    REQUIRES_RUPTURE_PARAMETERS = {"mag", "ztor"}
    REQUIRES_SITES_PARAMETERS = {"vs30", "backarc"}

    #: Supported tectonic region type is subduction inslab
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB


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
    add_alias(
        "NZNSHM2022_AbrahamsonGulerce2020SInter" + REGION_ALIASES[region],
        NZNSHM2022_AbrahamsonGulerce2020SInter,
        region=region,
    )
    add_alias(
        "NZNSHM2022_AbrahamsonGulerce2020SSlab" + REGION_ALIASES[region],
        NZNSHM2022_AbrahamsonGulerce2020SSlab,
        region=region,
    )
