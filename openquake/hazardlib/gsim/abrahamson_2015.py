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
Module exports :class:`AbrahamsonEtAl2015`
               :class:`AbrahamsonEtAl2015SInter`
               :class:`AbrahamsonEtAl2015SInterHigh`
               :class:`AbrahamsonEtAl2015SInterLow`
               :class:`AbrahamsonEtAl2015SSlab`
               :class:`AbrahamsonEtAl2015SSlabHigh`
               :class:`AbrahamsonEtAl2015SSlabLow`

"""
import numpy as np

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA

# Period-Independent Coefficients (Table 2)
CONSTS = {
    'n': 1.18,
    'c': 1.88,
    'theta3': 0.1,
    'theta4': 0.9,
    'theta5': 0.0,
    'theta9': 0.4,
    'c4': 10.0,
    'C1': 7.8
}

C1 = 7.2  # for Montalva2017

# Total epistemic uncertainty factors from Abrahamson et al. (2018)
BCHYDRO_SIGMA_MU = CoeffsTable(sa_damping=5, table="""
    imt     SIGMA_MU_SINTER    SIGMA_MU_SSLAB
    pga                 0.3              0.50
    0.010               0.3              0.50
    0.020               0.3              0.50
    0.030               0.3              0.50
    0.050               0.3              0.50
    0.075               0.3              0.50
    0.100               0.3              0.50
    0.150               0.3              0.50
    0.200               0.3              0.50
    0.250               0.3              0.46
    0.300               0.3              0.42
    0.400               0.3              0.38
    0.500               0.3              0.34
    0.600               0.3              0.30
    0.750               0.3              0.30
    1.000               0.3              0.30
    1.500               0.3              0.30
    2.000               0.3              0.30
    2.500               0.3              0.30
    3.000               0.3              0.30
    4.000               0.3              0.30
    5.000               0.3              0.30
    6.000               0.3              0.30
    7.500               0.3              0.30
    10.00               0.3              0.30
    """)


def get_stress_factor(imt, slab):
    """
    Returns the stress adjustment factor for the BC Hydro GMPE according to
    Abrahamson et al. (2018)
    """
    C = BCHYDRO_SIGMA_MU[imt]
    return (C["SIGMA_MU_SSLAB"] if slab else C["SIGMA_MU_SINTER"]) / 1.65


def _compute_magterm(C1, theta1, theta4, theta5, theta13, dc1, mag):
    """
    Computes the magnitude scaling term given by equation (2)
    corrected by a local adjustment factor
    """
    base = theta1 + theta4 * dc1
    dmag = C1 + dc1
    f_mag = np.where(
        mag > dmag, theta5 * (mag - dmag), theta4 * (mag - dmag))
    return base + f_mag + theta13 * (10. - mag) ** 2.


# theta6_adj used in BCHydro
def _compute_disterm(trt, C1, theta2, theta14, theta3, ctx, c4, theta9,
                     theta6_adj, theta6, theta10):
    if trt == const.TRT.SUBDUCTION_INTERFACE:
        dists = ctx.rrup
        assert theta10 == 0., theta10
    elif trt == const.TRT.SUBDUCTION_INTRASLAB:
        dists = ctx.rhypo
    else:
        raise NotImplementedError(trt)
    return (theta2 + theta14 + theta3 * (ctx.mag - C1)) * np.log(
        dists + c4 * np.exp((ctx.mag - 6.) * theta9)) + (
        theta6_adj + theta6) * dists + theta10


def _compute_forearc_backarc_term(trt, faba_model, C, ctx):
    if trt == const.TRT.SUBDUCTION_INTERFACE:
        dists = ctx.rrup
        a, b = C['theta15'], C['theta16']
        min_dist = 100.
    elif trt == const.TRT.SUBDUCTION_INTRASLAB:
        dists = ctx.rhypo
        a, b = C['theta7'], C['theta8']
        min_dist = 85.
    else:
        raise NotImplementedError(trt)
    if faba_model is None:
        backarc = np.bool_(ctx.backarc)
        f_faba = np.zeros_like(dists)
        # Term only applies to backarc ctx (F_FABA = 0. for forearc)
        fixed_dists = dists[backarc]
        fixed_dists[fixed_dists < min_dist] = min_dist
        f_faba[backarc] = a + b * np.log(fixed_dists / 40.)
        return f_faba

    # in BCHydro subclasses
    fixed_dists = np.copy(dists)
    fixed_dists[fixed_dists < min_dist] = min_dist
    f_faba = a + b * np.log(fixed_dists / 40.)
    return f_faba * faba_model(-ctx.xvf)


def _compute_distance_term(kind, trt, theta6_adj, C, ctx):
    """
    Computes the distance scaling term, as contained within equation (1)
    """
    if kind.startswith("montalva"):
        theta3 = C['theta3']
    else:
        theta3 = CONSTS['theta3']
    if kind == "montalva17":
        C1 = 7.2
    else:
        C1 = 7.8
    if trt == const.TRT.SUBDUCTION_INTERFACE:
        return _compute_disterm(
            trt, C1, C['theta2'], 0., theta3, ctx, CONSTS['c4'],
            CONSTS['theta9'], theta6_adj, C['theta6'], theta10=0.)
    else:  # sslab
        return _compute_disterm(
            trt, C1, C['theta2'], C['theta14'], theta3, ctx,
            CONSTS['c4'], CONSTS['theta9'], theta6_adj, C['theta6'],
            C["theta10"])


def _compute_focal_depth_term(trt, C, ctx):
    """
    Computes the hypocentral depth scaling term - as indicated by
    equation (3)
    For interface events F_EVENT = 0.. so no depth scaling is returned.
    For SSlab events computes the hypocentral depth scaling term as
    indicated by equation (3)
    """
    if trt == const.TRT.SUBDUCTION_INTERFACE:
        return np.zeros_like(ctx.mag)
    z_h = np.clip(ctx.hypo_depth, None, 120.)
    return C['theta11'] * (z_h - 60.)


def _compute_magnitude_term(kind, C, dc1, mag):
    """
    Computes the magnitude scaling term given by equation (2)
    """
    if kind == "base":
        return _compute_magterm(
            CONSTS['C1'], C['theta1'], CONSTS['theta4'],
            CONSTS['theta5'], C['theta13'], dc1, mag)
    elif kind == "montalva16":
        return _compute_magterm(
            CONSTS['C1'], C['theta1'], C['theta4'],
            C['theta5'], C['theta13'], dc1, mag)
    elif kind == "montalva17":
        return _compute_magterm(C1, C['theta1'], C['theta4'],
                                C['theta5'], 0., dc1, mag)


def _compute_pga_rock(kind, trt, theta6_adj, faba_model, C, dc1, ctx):
    """
    Compute and return mean imt value for rock conditions
    (vs30 = 1000 m/s)
    """
    mean = (_compute_magnitude_term(kind, C, dc1, ctx.mag) +
            _compute_distance_term(kind, trt, theta6_adj, C, ctx) +
            _compute_focal_depth_term(trt, C, ctx) +
            _compute_forearc_backarc_term(trt, faba_model, C, ctx))
    # Apply linear site term
    site_response = ((C['theta12'] + C['b'] * CONSTS['n']) *
                     np.log(1000. / C['vlin']))
    return mean + site_response


def _compute_site_response_term(C, ctx, pga1000):
    """
    Compute and return site response model term
    This GMPE adopts the same site response scaling model of
    Walling et al (2008) as implemented in the Abrahamson & Silva (2008)
    GMPE. The functional form is retained here.
    """
    vs_star = ctx.vs30.copy()
    vs_star[vs_star > 1000.0] = 1000.
    arg = vs_star / C["vlin"]
    site_resp_term = C["theta12"] * np.log(arg)
    # Get linear scaling term
    idx = ctx.vs30 >= C["vlin"]
    site_resp_term[idx] += (C["b"] * CONSTS["n"] * np.log(arg[idx]))
    # Get nonlinear scaling term
    idx = np.logical_not(idx)
    site_resp_term[idx] += (
        -C["b"] * np.log(pga1000[idx] + CONSTS["c"]) +
        C["b"] * np.log(pga1000[idx] + CONSTS["c"] *
                        (arg[idx] ** CONSTS["n"])))
    return site_resp_term


class AbrahamsonEtAl2015SInter(GMPE):
    """
    Implements the Subduction GMPE developed by Norman Abrahamson, Nicholas
    Gregor and Kofi Addo, otherwise known as the "BC Hydro" Model, published
    as "BC Hydro Ground Motion Prediction Equations For Subduction Earthquakes
    (2015, Earthquake Spectra, in press), for subduction interface events.

    From observations of very large events it was found that the magnitude
    scaling term can be adjusted as part of the epistemic uncertainty model.
    The adjustment comes in the form of the parameter DeltaC1, which is
    period dependent for interface events. To capture the epistemic uncertainty
    in DeltaC1, three models are proposed: a 'central', 'upper' and 'lower'
    model. The current class implements the 'central' model, whilst additional
    classes will implement the 'upper' and 'lower' alternatives.
    """
    #: Supported tectonic region type is subduction interface
    DEFINED_FOR_TECTONIC_REGION_TYPE = trt = const.TRT.SUBDUCTION_INTERFACE

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is the geometric mean component
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see table 3, pages 12 - 13
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Site amplification is dependent upon Vs30
    #: For the Abrahamson et al (2013) GMPE a new term is introduced to
    #: determine whether a site is on the forearc with respect to the
    #: subduction interface, or on the backarc. This boolean is a vector
    #: containing True for a backarc site or False for a forearc or
    #: unknown site.
    REQUIRES_SITES_PARAMETERS = {'vs30', 'backarc'}

    #: Required rupture parameters are magnitude for the interface model
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is closest distance to rupture, for
    #: interface events
    REQUIRES_DISTANCES = {'rrup'}

    #: Reference soil conditions (bottom of page 29)
    DEFINED_FOR_REFERENCE_VELOCITY = 1000

    delta_c1 = None
    kind = "base"
    FABA_ALL_MODELS = {}  # overridden in BCHydro

    def __init__(self, ergodic=True, theta6_adjustment=0, sigma_mu_epsilon=0.,
                 faba_taper_model='Step', **faba_args):
        self.ergodic = ergodic
        self.theta6_adj = theta6_adjustment
        self.sigma_mu_epsilon = sigma_mu_epsilon
        faba_type = faba_taper_model
        if 'xvf' in self.REQUIRES_SITES_PARAMETERS:  # BCHydro subclasses
            self.faba_model = self.FABA_ALL_MODELS[faba_type](**faba_args)
        else:
            self.faba_model = None

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        C_PGA = self.COEFFS[PGA()]
        dc1_pga = self.delta_c1 or self.COEFFS_MAG_SCALE[PGA()]["dc1"]
        # compute median pga on rock (vs30=1000), needed for site response
        # term calculation
        pga1000 = np.exp(_compute_pga_rock(
            self.kind, self.trt, self.theta6_adj, self.faba_model,
            C_PGA, dc1_pga, ctx))
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            dc1 = self.delta_c1 or self.COEFFS_MAG_SCALE[imt]["dc1"]
            mean[m] = (
                _compute_magnitude_term(
                    self.kind, C, dc1, ctx.mag) +
                _compute_distance_term(
                    self.kind, self.trt, self.theta6_adj, C, ctx) +
                _compute_focal_depth_term(
                    self.trt, C, ctx) +
                _compute_forearc_backarc_term(
                    self.trt, self.faba_model, C, ctx) +
                _compute_site_response_term(
                    C, ctx, pga1000))
            if self.sigma_mu_epsilon:
                sigma_mu = get_stress_factor(
                    imt, self.DEFINED_FOR_TECTONIC_REGION_TYPE ==
                    const.TRT.SUBDUCTION_INTRASLAB)
                mean[m] += sigma_mu * self.sigma_mu_epsilon

            sig[m] = C["sigma"] if self.ergodic else C["sigma_ss"]
            tau[m] = C['tau']
            phi[m] = C["phi"] if self.ergodic else np.sqrt(
                C["sigma_ss"] ** 2. - C["tau"] ** 2.)

    # Period-dependent coefficients (Table 3)
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    imt          vlin        b   theta1    theta2    theta6   theta7    theta8  theta10  theta11   theta12   theta13   theta14  theta15   theta16      phi     tau   sigma  sigma_ss
    pga      865.1000  -1.1860   4.2203   -1.3500   -0.0012   1.0988   -1.4200   3.1200   0.0130    0.9800   -0.0135   -0.4000   0.9969   -1.0000   0.6000  0.4300  0.7400    0.6000
    0.0200   865.1000  -1.1860   4.2203   -1.3500   -0.0012   1.0988   -1.4200   3.1200   0.0130    0.9800   -0.0135   -0.4000   0.9969   -1.0000   0.6000  0.4300  0.7400    0.6000
    0.0500  1053.5000  -1.3460   4.5371   -1.4000   -0.0012   1.2536   -1.6500   3.3700   0.0130    1.2880   -0.0138   -0.4000   1.1030   -1.1800   0.6000  0.4300  0.7400    0.6000
    0.0750  1085.7000  -1.4710   5.0733   -1.4500   -0.0012   1.4175   -1.8000   3.3700   0.0130    1.4830   -0.0142   -0.4000   1.2732   -1.3600   0.6000  0.4300  0.7400    0.6000
    0.1000  1032.5000  -1.6240   5.2892   -1.4500   -0.0012   1.3997   -1.8000   3.3300   0.0130    1.6130   -0.0145   -0.4000   1.3042   -1.3600   0.6000  0.4300  0.7400    0.6000
    0.1500   877.6000  -1.9310   5.4563   -1.4500   -0.0014   1.3582   -1.6900   3.2500   0.0130    1.8820   -0.0153   -0.4000   1.2600   -1.3000   0.6000  0.4300  0.7400    0.6000
    0.2000   748.2000  -2.1880   5.2684   -1.4000   -0.0018   1.1648   -1.4900   3.0300   0.0129    2.0760   -0.0162   -0.3500   1.2230   -1.2500   0.6000  0.4300  0.7400    0.6000
    0.2500   654.3000  -2.3810   5.0594   -1.3500   -0.0023   0.9940   -1.3000   2.8000   0.0129    2.2480   -0.0172   -0.3100   1.1600   -1.1700   0.6000  0.4300  0.7400    0.6000
    0.3000   587.1000  -2.5180   4.7945   -1.2800   -0.0027   0.8821   -1.1800   2.5900   0.0128    2.3480   -0.0183   -0.2800   1.0500   -1.0600   0.6000  0.4300  0.7400    0.6000
    0.4000   503.0000  -2.6570   4.4644   -1.1800   -0.0035   0.7046   -0.9800   2.2000   0.0127    2.4270   -0.0206   -0.2300   0.8000   -0.7800   0.6000  0.4300  0.7400    0.6000
    0.5000   456.6000  -2.6690   4.0181   -1.0800   -0.0044   0.5799   -0.8200   1.9200   0.0125    2.3990   -0.0231   -0.1900   0.6620   -0.6200   0.6000  0.4300  0.7400    0.6000
    0.6000   430.3000  -2.5990   3.6055   -0.9900   -0.0050   0.5021   -0.7000   1.7000   0.0124    2.2730   -0.0256   -0.1600   0.5800   -0.5000   0.6000  0.4300  0.7400    0.6000
    0.7500   410.5000  -2.4010   3.2174   -0.9100   -0.0058   0.3687   -0.5400   1.4200   0.0120    1.9930   -0.0296   -0.1200   0.4800   -0.3400   0.6000  0.4300  0.7400    0.6000
    1.0000   400.0000  -1.9550   2.7981   -0.8500   -0.0062   0.1746   -0.3400   1.1000   0.0114    1.4700   -0.0363   -0.0700   0.3300   -0.1400   0.6000  0.4300  0.7400    0.6000
    1.5000   400.0000  -1.0250   2.0123   -0.7700   -0.0064  -0.0820   -0.0500   0.7000   0.0100    0.4080   -0.0493    0.0000   0.3100    0.0000   0.6000  0.4300  0.7400    0.6000
    2.0000   400.0000  -0.2990   1.4128   -0.7100   -0.0064  -0.2821    0.1200   0.7000   0.0085   -0.4010   -0.0610    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    2.5000   400.0000   0.0000   0.9976   -0.6700   -0.0064  -0.4108    0.2500   0.7000   0.0069   -0.7230   -0.0711    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    3.0000   400.0000   0.0000   0.6443   -0.6400   -0.0064  -0.4466    0.3000   0.7000   0.0054   -0.6730   -0.0798    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    4.0000   400.0000   0.0000   0.0657   -0.5800   -0.0064  -0.4344    0.3000   0.7000   0.0027   -0.6270   -0.0935    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    5.0000   400.0000   0.0000  -0.4624   -0.5400   -0.0064  -0.4368    0.3000   0.7000   0.0005   -0.5960   -0.0980    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    6.0000   400.0000   0.0000  -0.9809   -0.5000   -0.0064  -0.4586    0.3000   0.7000  -0.0013   -0.5660   -0.0980    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    7.5000   400.0000   0.0000  -1.6017   -0.4600   -0.0064  -0.4433    0.3000   0.7000  -0.0033   -0.5280   -0.0980    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    10.0000  400.0000   0.0000  -2.2937   -0.4000   -0.0064  -0.4828    0.3000   0.7000  -0.0060   -0.5040   -0.0980    0.0000   0.3000    0.0000   0.6000  0.4300  0.7400    0.6000
    """)

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


class AbrahamsonEtAl2015SInterHigh(AbrahamsonEtAl2015SInter):
    """
    Defines the Abrahamson et al. (2013) scaling relation  assuming the upper
    values of the magnitude scaling for large slab earthquakes, as defined in
    table 4
    """
    COEFFS_MAG_SCALE = CoeffsTable(sa_damping=5, table="""
    IMT    dc1
    pga    0.4
    0.02   0.4
    0.30   0.4
    0.50   0.3
    1.00   0.2
    2.00   0.1
    3.00   0.0
    10.0   0.0
    """)


class AbrahamsonEtAl2015SInterLow(AbrahamsonEtAl2015SInter):
    """
    Defines the Abrahamson et al. (2013) scaling relation  assuming the lower
    values of the magnitude scaling for large slab earthquakes, as defined in
    table 4
    """

    COEFFS_MAG_SCALE = CoeffsTable(sa_damping=5, table="""
    IMT    dc1
    pga    0.0
    0.02   0.0
    0.30   0.0
    0.50  -0.1
    1.00  -0.2
    2.00  -0.3
    3.00  -0.4
    10.0  -0.4
    """)


class AbrahamsonEtAl2015SSlab(AbrahamsonEtAl2015SInter):
    """
    Implements the Subduction GMPE developed by Norman Abrahamson, Nicholas
    Gregor and Kofi Addo, otherwise known as the "BC Hydro" Model, published
    as "BC Hydro Ground Motion Prediction Equations For Subduction Earthquakes
    (2013, Earthquake Spectra, in press).
    This implements only the inslab GMPE. For inslab events the source is
    considered to be a point source located at the hypocentre. Therefore
    the hypocentral distance metric is used in place of the rupture distance,
    and the hypocentral depth is used to scale the ground motion by depth
    """
    #: Supported tectonic region type is subduction in-slab
    DEFINED_FOR_TECTONIC_REGION_TYPE = trt = const.TRT.SUBDUCTION_INTRASLAB

    #: Required distance measure is hypocentral for in-slab events
    REQUIRES_DISTANCES = {'rhypo'}

    #: In-slab events require constraint of hypocentral depth and magnitude
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'hypo_depth'}

    delta_c1 = -0.3


class AbrahamsonEtAl2015SSlabHigh(AbrahamsonEtAl2015SSlab):
    """
    Defines the Abrahamson et al. (2013) scaling relation  assuming the upper
    values of the magnitude scaling for large slab earthquakes, as defined in
    table 8
    """
    delta_c1 = -0.1


class AbrahamsonEtAl2015SSlabLow(AbrahamsonEtAl2015SSlab):
    """
    Defines the Abrahamson et al. (2013) scaling relation  assuming the lower
    values of the magnitude scaling for large slab earthquakes, as defined in
    table 8
    """
    delta_c1 = -0.5


class AbrahamsonEtAl2015SInter_scaled(AbrahamsonEtAl2015SInter):
    """
    Implements the Subduction GMPE developed by Norman Abrahamson, Nicholas
    Gregor and Kofi Addo, otherwise known as the "BC Hydro" Model, published
    as "BC Hydro Ground Motion Prediction Equations For Subduction Earthquakes
    (2015, Earthquake Spectra, in press), for subduction interface events.

    Application of a scaling factor that converts the prediction of
    AbrahamsonEtAl2015SInter to the corresponding
    prediction for the Maximum value.
    """
    # Period-dependent coefficients
    COEFFS = CoeffsTable(sa_damping=5, table="""\
	IMT		vlin	b		theta1		theta2	theta6		theta7	theta8	theta10	theta11	theta12	theta13	theta14	theta15	theta16	phi	tau		sigma	sigma_ss
	pga		865.1	-1.186	4.313152617	-1.35	-0.0012		1.0988	-1.42	3.12	0.013	0.98	-0.0135	-0.4	0.9969	-1		0.6	0.43	0.74	0.6
	0.05	1053.5	-1.346	4.626666443	-1.4	-0.0012		1.2536	-1.65	3.37	0.013	1.288	-0.0138	-0.4	1.103	-1.18	0.6	0.43	0.74	0.6
	0.1		1032.5	-1.624	5.38940726	-1.45	-0.0012		1.3997	-1.8	3.33	0.013	1.613	-0.0145	-0.4	1.3042	-1.36	0.6	0.43	0.74	0.6
	0.15	877.6	-1.931	5.561740512	-1.45	-0.0014		1.3582	-1.69	3.25	0.013	1.882	-0.0153	-0.4	1.26	-1.3	0.6	0.43	0.74	0.6
	0.2		748.2	-2.188	5.381371479	-1.4	-0.0018		1.1648	-1.49	3.03	0.0129	2.076	-0.0162	-0.35	1.223	-1.25	0.6	0.43	0.74	0.6
	0.3		587.1	-2.518	4.914236682	-1.28	-0.0027		0.8821	-1.18	2.59	0.0128	2.348	-0.0183	-0.28	1.05	-1.06	0.6	0.43	0.74	0.6
	0.4		503		-2.657	4.591825288	-1.18	-0.0035		0.7046	-0.98	2.2		0.0127	2.427	-0.0206	-0.23	0.8		-0.78	0.6	0.43	0.74	0.6
	0.5		456.6	-2.669	4.142704163	-1.08	-0.0044		0.5799	-0.82	1.92	0.0125	2.399	-0.0231	-0.19	0.662	-0.62	0.6	0.43	0.74	0.6
	0.75	410.5	-2.401	3.347462884	-0.91	-0.0058		0.3687	-0.54	1.42	0.012	1.993	-0.0296	-0.12	0.48	-0.34	0.6	0.43	0.74	0.6
	1		400		-1.955	2.922350962	-0.85	-0.0062		0.1746	-0.34	1.1		0.0114	1.47	-0.0363	-0.07	0.33	-0.14	0.6	0.43	0.74	0.6
	2		400		-0.299	1.539520753	-0.71	-0.0064		-0.2821	0.12	0.7		0.0085	-0.401	-0.061	0		0.3		0		0.6	0.43	0.74	0.6
	3		400		0		0.776117425	-0.64	-0.0064		-0.4466	0.3		0.7		0.0054	-0.673	-0.0798	0		0.3		0		0.6	0.43	0.74	0.6
	4		400		0		0.202413823	-0.58	-0.0064		-0.4344	0.3		0.7		0.0027	-0.627	-0.0935	0		0.3		0		0.6	0.43	0.74	0.6

    """)


class AbrahamsonEtAl2015SSlab_scaled(AbrahamsonEtAl2015SInter_scaled):
    """
    Implements the Subduction GMPE developed by Norman Abrahamson, Nicholas
    Gregor and Kofi Addo, otherwise known as the "BC Hydro" Model, published
    as "BC Hydro Ground Motion Prediction Equations For Subduction Earthquakes
    (2013, Earthquake Spectra, in press).
    This implements only the inslab GMPE. For inslab events the source is
    considered to be a point source located at the hypocentre. Therefore
    the hypocentral distance metric is used in place of the rupture distance,
    and the hypocentral depth is used to scale the ground motion by depth

    Application of a scaling factor that converts the prediction of
    AbrahamsonEtAl2015SSlab to the corresponding
    prediction for the Maximum value.
    """
    #: Supported tectonic region type is subduction in-slab
    DEFINED_FOR_TECTONIC_REGION_TYPE = trt = const.TRT.SUBDUCTION_INTRASLAB

    #: Required distance measure is hypocentral for in-slab events
    REQUIRES_DISTANCES = {'rhypo'}

    #: In-slab events require constraint of hypocentral depth and magnitude
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'hypo_depth'}

    delta_c1 = -0.3
