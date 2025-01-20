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
Module exports :class:`KothaEtAl2020`,
               :class:`KothaEtAl2020Site`,
               :class:`KothaEtAl2020Slope`,
               :class:`KothaEtAl2020ESHM20`,
               :class:`KothaEtAl2020ESHM20SlopeGeology`
               :class:`KothaEtAl2020regional`
"""
import os
import numpy as np
from scipy.constants import g
from shapely.geometry import Point, shape
from shapely.prepared import prep
from openquake.baselib.general import CallableDict
from openquake.hazardlib.geo.packager import fiona
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable, add_alias
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA, from_string
from openquake.hazardlib.gsim.nga_east import (get_tau_at_quantile, ITPL,
                                               TAU_EXECUTION, TAU_SETUP)

DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'Kotha_2020')

CONSTANTS = {"Mref": 4.5, "Rref": 30., "Mh": 5.7,
             "h_D10": 4.0, "h_10D20": 8.0, "h_D20": 12.0}

# The large-magnitude statistical standard deviation values are taken from data
# supplied by Kotha et al. (2020)
SIGMA_MU_COEFFS = CoeffsTable(sa_damping=5, table="""\
    imt     sigma_mu_m8_shallow   sigma_mu_m8_intermediate   sigma_mu_m8_deep   sigma_mu_m7p4_shallow   sigma_mu_m7p4_intermediate   sigma_mu_m7p4_deep
    pgv                  0.2865                     0.2829             0.2814                  0.2108                       0.2072               0.2057
    pga                  0.3040                     0.3003             0.2986                  0.2250                       0.2213               0.2197
    0.010                0.3039                     0.3002             0.2986                  0.2250                       0.2213               0.2197
    0.025                0.3026                     0.2988             0.2972                  0.2243                       0.2205               0.2189
    0.040                0.3010                     0.2972             0.2955                  0.2241                       0.2203               0.2186
    0.050                0.3053                     0.3014             0.2997                  0.2278                       0.2239               0.2222
    0.070                0.3133                     0.3093             0.3076                  0.2340                       0.2301               0.2284
    0.100                0.3219                     0.3179             0.3162                  0.2403                       0.2364               0.2346
    0.150                0.3199                     0.3159             0.3141                  0.2377                       0.2337               0.2319
    0.200                0.3174                     0.3134             0.3117                  0.2343                       0.2303               0.2285
    0.250                0.3118                     0.3078             0.3061                  0.2297                       0.2257               0.2240
    0.300                0.3094                     0.3055             0.3038                  0.2275                       0.2236               0.2220
    0.350                0.3038                     0.2999             0.2982                  0.2230                       0.2191               0.2174
    0.400                0.2989                     0.2950             0.2933                  0.2197                       0.2157               0.2140
    0.450                0.2964                     0.2926             0.2909                  0.2180                       0.2142               0.2125
    0.500                0.2916                     0.2878             0.2861                  0.2145                       0.2106               0.2090
    0.600                0.2897                     0.2860             0.2844                  0.2131                       0.2094               0.2078
    0.700                0.2888                     0.2852             0.2836                  0.2124                       0.2088               0.2072
    0.750                0.2902                     0.2867             0.2851                  0.2134                       0.2098               0.2083
    0.800                0.2923                     0.2888             0.2873                  0.2147                       0.2112               0.2097
    0.900                0.2948                     0.2915             0.2900                  0.2165                       0.2132               0.2117
    1.000                0.2964                     0.2932             0.2918                  0.2175                       0.2142               0.2128
    1.200                0.2961                     0.2930             0.2917                  0.2170                       0.2139               0.2126
    1.400                0.3019                     0.2990             0.2977                  0.2211                       0.2182               0.2169
    1.600                0.3041                     0.3013             0.3000                  0.2225                       0.2197               0.2184
    1.800                0.3060                     0.3032             0.3020                  0.2235                       0.2207               0.2195
    2.000                0.3094                     0.3067             0.3055                  0.2258                       0.2231               0.2219
    2.500                0.3121                     0.3095             0.3083                  0.2275                       0.2249               0.2237
    3.000                0.3279                     0.3254             0.3243                  0.2392                       0.2366               0.2355
    3.500                0.3256                     0.3230             0.3219                  0.2378                       0.2351               0.2339
    4.000                0.3269                     0.3243             0.3232                  0.2386                       0.2359               0.2348
    4.500                0.3483                     0.3456             0.3444                  0.2537                       0.2510               0.2498
    5.000                0.3525                     0.3498             0.3486                  0.2567                       0.2539               0.2527
    6.000                0.3458                     0.3422             0.3406                  0.2514                       0.2478               0.2462
    7.000                0.3453                     0.3417             0.3402                  0.2513                       0.2477               0.2461
    8.000                0.3428                     0.3392             0.3376                  0.2497                       0.2460               0.2444
    """)


AVGSA_SIGMA_MU_COEFFS = CoeffsTable(sa_damping=5, table="""\
    imt             sigma_mu_m8_shallow   sigma_mu_m8_intermediate   sigma_mu_m8_deep   sigma_mu_m7p4_shallow   sigma_mu_m7p4_intermediate  sigma_mu_m7p4_deep
    AvgSA(0.050)             0.36237117                 0.36194128         0.36153721              0.26814685                   0.26770184          0.26728207
    AvgSA(0.100)             0.37100348                 0.37058454         0.37019017              0.27464169                   0.27420650          0.27379506
    AvgSA(0.150)             0.37113960                 0.37073150         0.37034714              0.27399830                   0.27357286          0.27317036
    AvgSA(0.200)             0.36853324                 0.36813709         0.36776392              0.27144161                   0.27102774          0.27063616
    AvgSA(0.250)             0.36438013                 0.36399264         0.36362762              0.26790615                   0.26750087          0.26711746
    AvgSA(0.300)             0.36004639                 0.35966739         0.35931043              0.26444337                   0.26404673          0.26367159
    AvgSA(0.400)             0.34960757                 0.34924208         0.34889809              0.25636041                   0.25597756          0.25561573
    AvgSA(0.500)             0.34196320                 0.34160761         0.34127316              0.25046920                   0.25009644          0.24974445
    AvgSA(0.600)             0.33628994                 0.33594377         0.33561851              0.24613837                   0.24577525          0.24543272
    AvgSA(0.700)             0.33265779                 0.33232082         0.33200448              0.24327786                   0.24292413          0.24259077
    AvgSA(0.800)             0.33080518                 0.33047781         0.33017078              0.24172055                   0.24137672          0.24105304
    AvgSA(0.900)             0.33028960                 0.32997162         0.32967376              0.24123027                   0.24089610          0.24058191
    AvgSA(1.000)             0.33118486                 0.33087499         0.33058504              0.24174675                   0.24142106          0.24111520
    AvgSA(1.250)             0.33684608                 0.33655872         0.33629100              0.24552957                   0.24522646          0.24494296
    AvgSA(1.500)             0.34131151                 0.34103635         0.34078037              0.24857633                   0.24828558          0.24801406
    AvgSA(1.750)             0.34468757                 0.34442002         0.34417138              0.25099193                   0.25070866          0.25044432
    AvgSA(2.000)             0.34962212                 0.34936230         0.34912098              0.25441729                   0.25414208          0.25388544
    AvgSA(2.500)             0.35772559                 0.35748828         0.35726965              0.25993600                   0.25968178          0.25944620
    AvgSA(3.000)             0.38024588                 0.38006170         0.37989860              0.27645421                   0.27624724          0.27606079
    AvgSA(3.500)             0.37303807                 0.37283697         0.37265703              0.27159333                   0.27137037          0.27116809
    AvgSA(4.000)             0.37757969                 0.37738041         0.37720210              0.27464125                   0.27442015          0.27421954
    AvgSA(4.500)             0.39949828                 0.39927571         0.39907300              0.29012395                   0.28988040          0.28965658
    AvgSA(5.000)             0.40186133                 0.40163856         0.40143559              0.29173110                   0.29148734          0.29126324
    """)


def _get_h(C, hypo_depth):
    """
    Returns the depth-specific coefficient
    """
    return np.where(
        hypo_depth <= 10.,
        CONSTANTS["h_D10"],
        np.where(hypo_depth > 20., CONSTANTS["h_D20"], CONSTANTS["h_10D20"]))


get_distance_coefficients = CallableDict()


@get_distance_coefficients.add("base", "site", "slope", "avgsa_base")
def get_distance_coefficients_1(kind, c3, c3_epsilon, C, imt, sctx):
    """
    Returns either the directly specified c3 value or the c3 from the
    existing tau_c3 distribution
    """
    if c3:

        # Use the c3 that has been defined on input
        return c3
    else:
        # Define the c3 as a number of standard deviation multiplied
        # by tau_c3
        return C["c3"] + (c3_epsilon * C["tau_c3"])


@get_distance_coefficients.add("ESHM20", "geology", "avgsa_ESHM20",
                               "avgsa_ESHM20_geology",
                               "avgsa_ESHM20_homoskedastic")
def get_distance_coefficients_2(kind, c3, c3_epsilon, C, imt, sctx):
    """
    Returns the c3 term. If c3 was input directly into the GMPE then
    this over-rides the c3 regionalisation. Otherwise the c3 and tau_c3
    are determined according to the region to which each site is assigned.
    Note that no regionalisation is defined for PGV and hence the
    default values from Kotha et al. (2020) are taken unless defined
    otherwise in the input c3
    """
    if c3:
        # If c3 is input then this over-rides the regionalisation
        # assumed within this model
        return c3[imt]["c3"] * np.ones(sctx.region.shape)

    # Default c3 and tau values to the original GMPE c3 and tau
    c3_ = C["c3"] + np.zeros(sctx.region.shape)
    tau_c3 = C["tau_c3"] + np.zeros(sctx.region.shape)
    if not np.any(sctx.region) or ("PGV" in str(imt)):
        # No regionalisation - take the default C3 and multiply tau_c3
        # by the original epsilon
        return (c3_ + c3_epsilon * tau_c3) + np.zeros(sctx.region.shape)
    # Some ctx belong to the calibrated regions - loop through them
    C3_R = C3_REGIONS_AVGSA[imt] if kind.startswith("avgsa") else C3_REGIONS[imt]
    for i in range(1, 6):
        idx = sctx.region == i
        c3_[idx] = C3_R["region_{:s}".format(str(i))]
        tau_c3[idx] = C3_R["tau_region_{:s}".format(str(i))]
    return c3_ + c3_epsilon * tau_c3


def get_distance_coefficients_3(att, delta_c3_epsilon, C, imt, sctx):
    """
    Return site-specific coefficient 'C3'. The function retrieves the
    value of delta_c3 and the standard error of delta_c3 from the 'att'
    geojson file depending on the location of site. This delta_c3 is
    added to the generic coefficient 'c3' from the GMPE. A delta_c3_epsilon
    value of +/- 1.6 gives the 95% confidence interval for delta_c3.
    """
    s = [(Point(lon, lat)) for lon, lat in zip(sctx.lon, sctx.lat)]
    delta_c3 = np.zeros((len(sctx.lat), 2), dtype=float)
    for i, feature in enumerate(att):
        prepared_polygon = prep(shape(feature['geometry']))
        contained = list(filter(prepared_polygon.contains, s))
        if contained:
            ll = np.concatenate([
                np.where((sctx['lon'] == p.x) &
                         (sctx['lat'] == p.y))[0] for p in contained])
            delta_c3[ll, 0] = feature['properties'][str(imt)]
            delta_c3[ll, 1] = feature['properties'][str(imt)+'_se']

    return C["c3"] + delta_c3[:, 0] + delta_c3_epsilon * delta_c3[:, 1]


def get_distance_term(kind, c3, c3_epsilon, C, ctx, imt):
    """
    Returns the distance attenuation factor
    """
    h = _get_h(C, ctx.hypo_depth)
    rval = np.sqrt(ctx.rjb ** 2. + h ** 2.)
    rref_val = np.sqrt(CONSTANTS["Rref"] ** 2. + h ** 2.)
    if kind != 'regional':
        c3 = get_distance_coefficients(kind, c3, c3_epsilon, C, imt, ctx)
    f_r = (C["c1"] + C["c2"] * (ctx.mag - CONSTANTS["Mref"])) *\
        np.log(rval / rref_val) + (c3 * (rval - rref_val) / 100.)
    return f_r


def get_magnitude_scaling(C, mag):
    """
    Returns the magnitude scaling term
    """
    d_m = mag - CONSTANTS["Mh"]
    return np.where(mag <= CONSTANTS["Mh"],
                    C["e1"] + C["b1"] * d_m + C["b2"] * d_m ** 2.0,
                    C["e1"] + C["b3"] * d_m)


def get_dl2l(tec, ctx, imt, delta_l2l_epsilon):
    """
    Returns rupture source specific delta_l2l values. The method
    retrieves the delta_l2l and standard error of delta_l2l values.
    if delta_l2l_epsilon is provided, standard error of delta_c3
    will be included. A delta_l2l_epsilon value of +/- 1.6 gives
    the 95% confidence interval for delta_l2l.
    """
    f = [(Point(lon, lat)) for lon, lat in zip(ctx.hypo_lon, ctx.hypo_lat)]
    dl2l = np.zeros((len(ctx.hypo_lon), 2), dtype=float)
    for i, feature in enumerate(tec):
        prepared_polygon = prep(shape(feature['geometry']))
        contained = list(filter(prepared_polygon.contains, f))
        if contained:
            ll = np.concatenate([
                np.where((ctx['hypo_lon'] == p.x) &
                         (ctx['hypo_lat'] == p.y))[0] for p in contained])
            dl2l[ll, 0] = feature['properties'][str(imt)]
            dl2l[ll, 1] = feature['properties'][str(imt)+'_se']

    return dl2l[:, 0] + delta_l2l_epsilon * dl2l[:, 1]


def get_sigma_mu_adjustment(kind, C, imt, ctx):
    """
    Returns the sigma_mu adjusment factor, which is taken as the
    maximum of tau_L2L and the sigma_mu. For M < 7.4
    the sigma statistical does not exceed tau_L2L at any period or
    distance. For M > 7.4, sigma_mu is approximately linear up to M 8.0
    so we interpolate between the two values and cap sigma statistical
    at M 8.0
    """
    C_SIG_MU = AVGSA_SIGMA_MU_COEFFS[imt] if kind.startswith("avgsa") else\
        SIGMA_MU_COEFFS[imt]
    uf = np.full_like(ctx.mag, C_SIG_MU["sigma_mu_m8_intermediate"])
    lf = np.full_like(ctx.mag, C_SIG_MU["sigma_mu_m7p4_intermediate"])
    idx = ctx.hypo_depth < 10.0
    uf[idx] = C_SIG_MU["sigma_mu_m8_shallow"]
    lf[idx] = C_SIG_MU["sigma_mu_m7p4_shallow"]
    idx = ctx.hypo_depth >= 20.0
    uf[idx] = C_SIG_MU["sigma_mu_m8_deep"]
    lf[idx] = C_SIG_MU["sigma_mu_m7p4_deep"]
    adj = np.maximum(C["tau_l2l"], ITPL(ctx.mag, uf, lf, 7.4, 0.6))
    # Below M 7.4 tau_L2L is always larger than sigma mu
    adj[ctx.mag < 7.4] = C["tau_l2l"]
    # Cap the sigma mu as the value for M 8.0
    adj[ctx.mag >= 8.0] = np.maximum(C["tau_l2l"], uf[ctx.mag >= 8.0])
    return adj


def get_site_amplification(kind, extra, C, ctx, imt):
    """
    Apply the correct site amplification depending on the kind of GMPE
    """
    if kind in {"base", "avgsa_base"}:  # no site amplification
        ampl = 0.
    elif kind in {"site", "regional"}:
        # Render with respect to 800 m/s reference Vs30
        sref = np.log(ctx.vs30 / 800.)
        ampl = (C["g0_vs30"] + C["g1_vs30"] * sref +
                C["g2_vs30"] * (sref ** 2.))
    elif kind == "slope":
        # Render with respect to 0.1 m/m reference slope
        sref = np.log(ctx.slope / 0.1)
        ampl = (C["g0_slope"] + C["g1_slope"] * sref +
                C["g2_slope"] * (sref ** 2.))
    elif kind in {"ESHM20", "avgsa_ESHM20", "avgsa_ESHM20_homoskedastic"}:
        vs30 = np.copy(ctx.vs30)
        vs30[vs30 > 1100.] = 1100.
        ampl = np.zeros(vs30.shape)
        # For observed vs30 ctx
        ampl[ctx.vs30measured] = (C["d0_obs"] + C["d1_obs"] *
                                  np.log(vs30[ctx.vs30measured]))
        # For inferred Vs30 ctx
        idx = np.logical_not(ctx.vs30measured)
        ampl[idx] = (C["d0_inf"] + C["d1_inf"] * np.log(vs30[idx]))
    elif kind in {"geology", "avgsa_ESHM20_geology"}:
        C_AMP_FIXED = extra['COEFFS_FIXED'][imt]
        C_AMP_RAND_INT = extra['COEFFS_RANDOM_INT'][imt]
        C_AMP_RAND_GRAD = extra['COEFFS_RANDOM_GRAD'][imt]
        ampl = np.zeros(ctx.slope.shape)
        geol_units = np.unique(ctx.geology)
        t_slope = np.copy(ctx.slope)
        t_slope[t_slope > 0.3] = 0.3
        # Slope lower than 0.0005 m/m takes value for 0.0005 m/m
        t_slope[t_slope < 0.0005] = 0.0005
        for geol_unit in geol_units:
            idx = ctx.geology == geol_unit
            if geol_unit in extra['GEOLOGICAL_UNITS']:
                unit = geol_unit.decode()
                # Supported geological unit, use the random effects model
                v1 = C_AMP_FIXED["V1"] + C_AMP_RAND_INT[unit]
                v2 = C_AMP_FIXED["V2"] + C_AMP_RAND_GRAD[unit]
            else:
                # Unrecognised geological unit, use the fixed effects model
                v1 = C_AMP_FIXED["V1"]
                v2 = C_AMP_FIXED["V2"]
            ampl[idx] = v1 + v2 * np.log(t_slope[idx])
    return ampl


def get_stddevs(kind, ergodic, phi_s2s, C, ctx, imt):
    """
    Returns the homoskedastic standard deviation model
    """
    mag = ctx.mag
    if kind in {"ESHM20", "geology"}:
        # Get the heteroskedastic tau and phi0
        tau = get_tau(imt, mag)
        phi = get_phi_ss(imt, mag)
    elif kind in {'avgsa_ESHM20', "avgsa_ESHM20_geology"}:
        # Get the heteroskedastic tau and phi0 for AvgSA
        tau, phi = get_heteroskedastic_tau_phi0_avgsa(imt, ctx.mag)
    else:
        # Get the homoskedastic tau and phi0
        tau = C["tau_event_0"]
        phi = C["phi_0"]
    if ergodic:
        if kind in {'ESHM20', "geology", "avgsa_ESHM20_geology",
                    "avgsa_ESHM20", "avgsa_ESHM20_homoskedastic"}:
            # phi_s2s retrieved in the compute() function of the GMM
            phi = np.sqrt(phi ** 2. + phi_s2s ** 2.)
        elif kind in {"site", "regional"}:
            phi = np.sqrt(phi ** 2.0 + C["phi_s2s_vs30"] ** 2.)
        elif kind == 'slope':
            phi = np.sqrt(phi ** 2.0 + C["phi_s2s_slope"] ** 2.)
        else:
            phi = np.sqrt(phi ** 2. + C["phis2s"] ** 2.)
    return [np.sqrt(tau ** 2. + phi ** 2.), tau, phi]


class KothaEtAl2020(GMPE):
    """
    Implements the first complete version of the newly derived GMPE
    for Shallow Crustal regions using the Engineering Strong Motion Flatfile.
    Kotha, S. R., Weatherill, G., Bindi, D., Cotton F. (2020) "A regionally-
    adaptable ground-motion model for shallow crustal earthquakes in Europe.
    Bulletin of Earthquake Engineering, 18:4091-4125
    The GMPE is desiged for regional adaptation within a logic-tree framework,
    and as such contains several parameters that can be calibrated on input:
    1) Source-region scaling, a simple scalar factor that defines how much
    to increase or decrease the "regional average" ground motion in the region.
    This value is taken as the maximum of the source-region variability term
    (tau_l2l) and the statistical uncertainty (sigma_mu). The latter defines
    the within-model uncertainty owing to the data set from which the model is
    derived and only exceeds the former at large magnitudes
    2) Residual attenuation scaling "c3", a factor that controls the residual
    attenuation part of the model to make the ground motion decay more or less
    rapidly with distance than the regional average.
    Both factors are period dependent.
    The two adaptable factors can be controlled either by direct specification
    at input (in the form of an imt-dependent dictionary) or by a number of
    standard deviations multiplying the existing variance terms. The two
    approaches are mutually exclusive, with the directly specified parameters
    always being used if defined on input.
    In the core form of the GMPE no site term is included. This is added in the
    subclasses.

    :param float sigma_mu_epsilon:
        Parameter to control the source-region scaling as a number of
        standard deviations by which to multiply the source-region to source-
        region variance, max(tau_l2l, sigma_mu)
    :param float c3_epsilon:
        Parameter to control the residual attenuation scaling as a number
        of standard deviations by which to multiply the attenuation-region
        variance, tau_c3.
        User supplied table for the coefficient c3 controlling the anelastic
        attenuation as an instance of :class:
        `openquake.hazardlib.gsim.base.CoeffsTable`. If absent, the value is
        taken from the normal coefficients table.
    :param bool ergodic:
        Use the ergodic standard deviation (True) or non-ergodic standard
        deviation (False)
    :param dict dl2l:
        If specifying the source-region scaling directly, defines the
        increase or decrease of the ground motion in the form of an imt-
        dependent dictionary of delta L2L factors
    :param dict c3:
        If specifying the residual attenuation scaling directly, defines the
        apparent anelastic attenuation term, c3, as an imt-dependent
        dictionary
    """
    kind = "base"

    #: Supported tectonic region type is 'active shallow crust'
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Set of :mod:`intensity measure types <openquake.hazardlib.imt>`
    #: this GSIM can calculate. A set should contain classes from module
    #: :mod:`openquake.hazardlib.imt`.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    #: Supported intensity measure component is the geometric mean of two
    #: horizontal components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    #: Supported standard deviation types are inter-event, intra-event
    #: and total
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Required site parameter is not set
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameters are magnitude and hypocentral depth
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'hypo_depth'}

    #: Required distance measure is Rjb (eq. 1).
    REQUIRES_DISTANCES = {'rjb'}

    def __init__(self, sigma_mu_epsilon=0.0, c3_epsilon=0.0, ergodic=True,
                 dl2l=None, c3=None):
        """
        Instantiate setting the sigma_mu_epsilon and c3 terms
        """
        self.sigma_mu_epsilon = sigma_mu_epsilon
        self.c3_epsilon = c3_epsilon
        self.ergodic = ergodic
        if dl2l:
            # Check that the input is a dictionary and p
            if not isinstance(dl2l, dict):
                raise IOError("For Kotha et al. (2020) GMM, source-region "
                              "scaling parameter (dl2l) must be input in the "
                              "form of a dictionary, if specified")
            self.dl2l = {}
            for key in dl2l:
                self.dl2l[from_string(key)] = {"dl2l": dl2l[key]}
            self.dl2l = CoeffsTable.fromdict(self.dl2l)
        else:
            self.dl2l = None
        if c3:
            if not isinstance(c3, dict):
                raise IOError("For Kotha et al. (2020) GMM, residual "
                              "attenuation scaling (c3) must be input in the "
                              "form of a dictionary, if specified")
            self.c3 = {}
            for key in c3:
                self.c3[from_string(key)] = {"c3": c3[key]}
            self.c3 = CoeffsTable.fromdict(self.c3)
        else:
            self.c3 = None

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            extra = {}
            if self.kind in {'ESHM20', "avgsa_ESHM20",
                             "avgsa_ESHM20_homoskedastic"}:
                phi_s2s = np.zeros(ctx.vs30measured.shape, dtype=float)
                phi_s2s[ctx.vs30measured] += C["phi_s2s_obs"]
                phi_s2s[np.logical_not(ctx.vs30measured)] += C["phi_s2s_inf"]
            elif self.kind in {'geology', "avgsa_ESHM20_geology"}:
                phi_s2s = self.COEFFS_FIXED[imt]["phi_s2s"]
                extra['COEFFS_FIXED'] = self.COEFFS_FIXED
                extra['COEFFS_RANDOM_INT'] = self.COEFFS_RANDOM_INT
                extra['COEFFS_RANDOM_GRAD'] = self.COEFFS_RANDOM_GRAD
                extra['GEOLOGICAL_UNITS'] = self.GEOLOGICAL_UNITS
            else:
                phi_s2s = None
            if self.kind == 'regional':
                c3 = get_distance_coefficients_3(self.att,
                                                 self.delta_c3_epsilon,
                                                 C, imt, ctx)
            else:
                c3 = self.c3
            fp = get_distance_term(self.kind, c3, self.c3_epsilon,
                                   C, ctx, imt)
            mean[m] = (get_magnitude_scaling(C, ctx.mag) + fp +
                       get_site_amplification(self.kind, extra, C, ctx, imt))
            # GMPE originally in cm/s/s - convert to g
            if imt.string.startswith(('PGA', 'SA', 'AvgSA')):
                mean[m] -= np.log(100.0 * g)
            sig[m], tau[m], phi[m] = get_stddevs(
                self.kind, self.ergodic, phi_s2s, C, ctx, imt)
            if self.dl2l:
                # The source-region parameter is specified explicity
                mean[m] += self.dl2l[imt]["dl2l"]

            elif self.kind == 'regional':
                dl2l = get_dl2l(self.tec, ctx, imt, self.delta_l2l_epsilon)
                mean[m] += dl2l

            elif self.sigma_mu_epsilon:
                # epistemic uncertainty factor (sigma_mu) multiplied by
                # the number of standard deviations
                sigma_mu = get_sigma_mu_adjustment(self.kind, C, imt, ctx)
                mean[m] += self.sigma_mu_epsilon * sigma_mu

    # Coefficients obtained direclty from the regression outputs of
    # Kotha et al. (2020)
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    imt                   e1                 b1                  b2                  b3                  c1                   c2                   c3              tau_c3              phis2s         tau_event_0             tau_l2l               phi_0              g0_vs30              g1_vs30               g2_vs30         phi_s2s_vs30              g0_slope              g1_slope               g2_slope       phi_s2s_slope
    pgv     1.11912161648479   2.55771078860152   0.353267224391297   0.879839839344054   -1.41931258132547   0.2706807258213520   -0.304426142175370   0.178233997535235   0.560627759977840   0.422935885699239   0.258560350227890   0.446525247049620   -0.232891265610189   -0.492356618589364    0.0247963168536102    0.366726744441574   -0.0550827970556740   -0.1469535974165200   -0.00893120461876375   0.434256033254051
    pga     3.93782347219377   2.06573167101440   0.304988012209292   0.444773874960317   -1.49787542346412   0.2812414746313380   -0.609876182476899   0.253818777234181   0.606771946180224   0.441761487685862   0.355279206886721   0.467151252053241   -0.222196028066344   -0.558848724731566   -0.1330148640403130    0.389712940326169   -0.0267105106085816   -0.1098813702713090   -0.01742373265620930   0.506725958082485
    0.010   3.94038760011295   2.06441772899445   0.305294151898347   0.444352974827805   -1.50006146971318   0.2816120431678390   -0.608869451197394   0.253797652143759   0.607030265833062   0.441635449735044   0.356047209347534   0.467206938011971   -0.221989239810027   -0.558181442039516   -0.1330144520414310    0.391254585814764   -0.0266572723455345   -0.1097145490975510   -0.01741863169765470   0.506706245975056
    0.025   3.97499686979384   2.04519749120013   0.308841647142436   0.439374383710060   -1.54376149680542   0.2830031280602480   -0.573207556417252   0.252734624432000   0.610030865927204   0.437676505154608   0.368398604288111   0.468698397037258   -0.218745638720123   -0.546810177342948   -0.1315295091425130    0.395303566681041   -0.0254040142855204   -0.1072422064249640   -0.01765069385301560   0.506705856554187
    0.040   4.08702279605872   1.99149766561616   0.319673428428720   0.418531185104657   -1.63671359040283   0.2984823762486280   -0.535139204130152   0.244894143623498   0.626413180170373   0.429637401735540   0.412921240156940   0.473730661220076   -0.206923687805771   -0.525141264234585   -0.1368798835282360    0.415116874033842   -0.0222919270649348   -0.1024278275345350   -0.01847074311083690   0.515812197849121
    0.050   4.18397570399970   1.96912968528742   0.328982074841989   0.389853296189063   -1.66358950776148   0.3121928913488560   -0.555191107011420   0.260330694464557   0.638967955474841   0.433639923327438   0.444324049044753   0.479898166019243   -0.205629239209508   -0.514739138349666   -0.1368385040078350    0.422549340781658   -0.0209153599570857   -0.0989203779863760   -0.01851248498790100   0.526875631632610
    0.070   4.38176649786342   1.92450788134500   0.321182873495225   0.379581373255289   -1.64352914575492   0.3138101953091510   -0.641089475725666   0.286976037026550   0.661064599433347   0.444338223383705   0.470938801038256   0.487060899687138   -0.209348356311787   -0.506896476331228   -0.1456117952510990    0.443318525820235   -0.0188838682625869   -0.0951010574545904   -0.01880576764531640   0.553542604942032
    0.100   4.60722959404894   1.90125096928647   0.298805051330753   0.393002352641809   -1.54339428982169   0.2849395739776680   -0.744270750619733   0.321927482439715   0.663309669119995   0.458382304191096   0.478737965504940   0.496152397155402   -0.193509476649993   -0.521463491048192   -0.1824674441457950    0.437214022468042   -0.0165212272103937   -0.0871969707343552   -0.01674749313351450   0.537128822815826
    0.150   4.78583314367062   1.92620172077838   0.249893333649662   0.435396192976506   -1.38136438628699   0.2254113422224680   -0.815688997995934   0.322145126407981   0.655406109737959   0.459702777214781   0.414046169030935   0.497805936702476   -0.215418461095753   -0.579757224642522   -0.2016525247813580    0.457311836251173   -0.0153013615272199   -0.0898557092287409   -0.01820533201066010   0.548306674706135
    0.200   4.81847463780069   1.97006598187863   0.218722883323200   0.469713318293785   -1.30697558633587   0.1826533194804230   -0.773372802995208   0.301795870071949   0.643585009231006   0.464006126996261   0.321975745683642   0.494075956910651   -0.232802520913539   -0.646162914187111   -0.2102452066359760    0.449595599604904   -0.0185432743074803   -0.1091715402153590   -0.02203326475372750   0.542391858770537
    0.250   4.75134747347049   2.01097445156370   0.195062831156806   0.532210412551561   -1.26259484078950   0.1551575007473110   -0.722012122448262   0.274998157533509   0.623240061418664   0.457687642192569   0.293329526713994   0.488950837091220   -0.238646255489286   -0.649028548718928   -0.1965317433344580    0.449701754122993   -0.0268512786854638   -0.1177223461809770   -0.01990310375762760   0.514759188358396
    0.300   4.65252285968525   2.09278551802016   0.194929941231544   0.557034893811231   -1.24071282395616   0.1370008066985060   -0.660466290850886   0.260774631679394   0.609748615552919   0.457514283978959   0.266836791529257   0.482157450259502   -0.246093988657936   -0.645741652187205   -0.1720972685448300    0.429850112026890   -0.0356644839782008   -0.1265719157414280   -0.01728437065375890   0.490014753971745
    0.350   4.53350897671045   2.14179725762371   0.189511462582876   0.609892595327716   -1.21514531872583   0.1247122464559250   -0.618593385936676   0.254261888951322   0.609506191611413   0.450960093750492   0.231614185359720   0.480254056040507   -0.254026518879524   -0.648402249765170   -0.1446513637358710    0.397602725132059   -0.0423519589829896   -0.1401638874897640   -0.01672203482354180   0.483807852643816
    0.400   4.44193244811952   2.22862498827440   0.200305171692326   0.614767001033243   -1.18897228839914   0.1156387616270450   -0.591574546068960   0.243643375298288   0.615477199296824   0.441122908694716   0.240825814626397   0.475193646646757   -0.263328502132230   -0.653476851717702   -0.1186474533289450    0.439991306965322   -0.0452239204802930   -0.1514100096093150   -0.01778303668068960   0.500388492016146
    0.450   4.33697728548038   2.29103572171716   0.209573442606565   0.634252522127606   -1.18013993982454   0.1100834686500940   -0.555234498707119   0.245883260391068   0.619384591074073   0.436294164198843   0.249245758570064   0.469672671050266   -0.264631841951527   -0.638852650094042   -0.0836039291412020    0.424224393510765   -0.0543649832422398   -0.1588148016645050   -0.01500762961938830   0.492980996451707
    0.500   4.23507897753587   2.35399193121686   0.218088423514177   0.658541873692286   -1.17726165949601   0.1026978146186720   -0.519413341065942   0.238559829231160   0.624993564560933   0.428500398327627   0.243778652813106   0.463165027132890   -0.269124654561252   -0.626175743644433   -0.0537720540773490    0.423230860170143   -0.0610661425543540   -0.1647334612739770   -0.01304441434577370   0.495138633047097
    0.600   4.02306439391925   2.42753387249929   0.218787915039312   0.754615594874153   -1.16678688970027   0.0940582863096094   -0.454043559543982   0.216855298090451   0.635090711921061   0.426296731581312   0.246117069779268   0.451206692163190   -0.269626118151597   -0.582682427052082    0.0203225530214242    0.475220856944347   -0.0680919086636438   -0.1730542985615550   -0.00960057312582767   0.510149252547482
    0.700   3.83201580121827   2.51268432884949   0.225024841305000   0.765438564882833   -1.16236278470164   0.0865917976706938   -0.397781532595396   0.215716276719833   0.633635835573626   0.425379430268476   0.246750734502549   0.446704739768374   -0.272441022824943   -0.558163103244591    0.0652728074463838    0.446489639181972   -0.0742129950461250   -0.1739452472381870   -0.00549504377749866   0.502939558871623
    0.750   3.74614211993052   2.55840246083607   0.231604957273506   0.793480645885641   -1.15333203234665   0.0824927940948198   -0.376630503031279   0.209593410875067   0.637877956868669   0.428563811859323   0.245166749142241   0.444311331912854   -0.268471953245116   -0.546146873703377    0.0840210504832594    0.451727019248850   -0.0742883211225450   -0.1757280229442730   -0.00571924409424620   0.513908669690317
    0.800   3.65168809980226   2.59467404437385   0.237334498546207   0.828241777740572   -1.14645090256437   0.0837439530041729   -0.363246464853852   0.192106714053294   0.638753820813416   0.433880652259324   0.240072953116796   0.439300059540554   -0.268043587730749   -0.528310722806634    0.1053131905955920    0.476641301777151   -0.0733362133528447   -0.1769632805164950   -0.00623439334393725   0.516534123477592
    0.900   3.51228638217709   2.68810225072750   0.251716558693382   0.845561170244942   -1.13599614124436   0.0834018259445213   -0.333908265367165   0.177456610405390   0.640328521929993   0.438913972406961   0.247662698012904   0.433043490235851   -0.270747888599204   -0.498749188701101    0.1514549282913290    0.492678009609922   -0.0705690120386147   -0.1842212802961380   -0.00948523310240806   0.508758129697782
    1.000   3.36982044793917   2.74249776483975   0.256784133033388   0.896648260528882   -1.12443352348542   0.0854384622609198   -0.317465939881623   0.171997778367260   0.638429444564638   0.444086895369946   0.238111905941701   0.426703815544157   -0.268682366673877   -0.472355589159814    0.1912725393732170    0.486349823748500   -0.0730202296385978   -0.1861995093276410   -0.00833302021378029   0.499129039268700
    1.200   3.10224418952824   2.82683484364226   0.262683442221073   0.982921357727718   -1.12116148624672   0.0973231293288241   -0.275616235541070   0.160445653296358   0.640086303643832   0.446121165446841   0.226825215617356   0.416539877732589   -0.263517582328224   -0.465411813875967    0.2014565230611100    0.460802894674431   -0.0761329216007339   -0.1923688484322410   -0.00790676960410267   0.494333782654409
    1.400   2.84933745949861   2.89911332547612   0.272065572034688   1.040000637056720   -1.12848926976065   0.1002887249133400   -0.234977212668109   0.150949141990859   0.649359928046388   0.457011583377380   0.231922092201736   0.409641113489270   -0.253077954003716   -0.450716220871832    0.1900019177957120    0.520330220947425   -0.0777847149574368   -0.1977821544457880   -0.00694977055552574   0.521824672837616
    1.600   2.63503429015231   2.98365736561984   0.289670716036571   1.073002118658300   -1.14064711059980   0.1100788214866130   -0.198050139347725   0.148738498099927   0.650540540696659   0.462781403376806   0.223897549097876   0.404985162254916   -0.246009048662975   -0.427498542497053    0.2013164560891230    0.498576704112864   -0.0808481108779988   -0.1956817304755080   -0.00420478503206788   0.520676267977361
    1.800   2.43032254290751   3.06358840071518   0.316828766785138   1.109809835991900   -1.15419967841818   0.1131278831612640   -0.167123738873435   0.156141593013035   0.656949311785981   0.468432106332010   0.205207971335941   0.399057812399511   -0.259365145858505   -0.436165813138372    0.2103523943478280    0.494419960120798   -0.0866501788741884   -0.1968633287340960    0.00084917955133917   0.521315249011902
    2.000   2.24716354703519   3.11067747935049   0.326774527695550   1.132479221218060   -1.16620971948721   0.1162990300931710   -0.140731664063789   0.155054491423268   0.647763389017009   0.476577198889343   0.196850466599025   0.396502973620567   -0.255846430844076   -0.425096032934296    0.2073318834508050    0.484354097558551   -0.0881098607385541   -0.1980665849538590    0.00178776027496752   0.509385313956226
    2.500   1.83108464781202   3.23289020747997   0.374214285707986   1.226390493979360   -1.17531326311999   0.1395412164588280   -0.120745041347963   0.176744551716694   0.629481669044830   0.479859874942997   0.190867925368865   0.393288023064441   -0.257425360830402   -0.394240493031487    0.2135940556445740    0.460612029226665   -0.0842255772225518   -0.1909303606402940    0.00128428761198652   0.505686965707424
    3.000   1.58259215964414   3.44640772476285   0.454951810817816   1.313954219909490   -1.15664484431459   0.1494902905791280   -0.149050671035371   0.174876785480317   0.616446588503561   0.488309107285476   0.220914253465451   0.390859427279163   -0.251876760182310   -0.364653376508969    0.2122004191615380    0.407986805228384   -0.0784780440908414   -0.1844510105227600   -0.00047381737627311   0.485603444879608
    3.500   1.32153652077149   3.56445182133655   0.518610571029448   1.394984393379380   -1.16368470057735   0.1543445278711660   -0.142873831246493   0.193619214137258   0.600202108018105   0.479187019962682   0.237281350236338   0.388102875218375   -0.242628051593659   -0.322323015714785    0.2138248326399060    0.396737062193148   -0.0787732613082041   -0.1718918693565610    0.00223831455352896   0.479608514060425
    4.000   1.10607064193676   3.64336885536264   0.555331865800278   1.418144933323620   -1.17757508691221   0.1730832048262120   -0.142053716741244   0.193571789393738   0.593046407283143   0.482524831704549   0.233827536969510   0.386956009422453   -0.239634395956042   -0.294311486158724    0.2268951652965890    0.396113359026388   -0.0764209712209348   -0.1648847320168560    0.00295327439998048   0.475041314185757
    4.500   1.05987610378773   3.82152567982841   0.666476453600402   1.430548279466630   -1.17323633891422   0.1936210609543320   -0.156076448842833   0.152553585766189   0.581331910387036   0.456765160173852   0.196697785051230   0.372827866334900   -0.246998133746262   -0.241579092689847    0.2474533712720740    0.397717123177902   -0.0668746312766319   -0.1735273164380950   -0.00530669973001712   0.473200567096548
    5.000   0.82373381739570   3.84747968562771   0.684665144355361   1.496536314224210   -1.20969230916539   0.2213041109459350   -0.126052481240424   0.137919529808920   0.558954997903623   0.464229101930025   0.195572800413952   0.377458812369736   -0.234334071379258   -0.208962718979667    0.2332755435126690    0.338344656676906   -0.0617201190392144   -0.1636990315777190   -0.00649134386415973   0.450949884766277
    6.000   0.50685354955206   3.80040950285788   0.700805222359295   1.625591116375650   -1.22440411739130   0.2292764533844400   -0.113766839623945   0.141669390606605   0.538973145096788   0.439059204276786   0.190680023411634   0.384862538848542   -0.205342867591920   -0.166350345553781    0.2189842473229210    0.338688052762081   -0.0568786587375636   -0.1519590377762100   -0.00580039515645921   0.439827391985479
    7.000   0.19675504234642   3.78431011962409   0.716569352050671   1.696310364814470   -1.28517895409644   0.2596896867469380   -0.070585399916418   0.146488759166368   0.523331606096182   0.434396029381517   0.208231539543981   0.385850838707000   -0.204046508080049   -0.155173106999605    0.2164856914333770    0.339211265835413   -0.0541313319257671   -0.1393109833551150   -0.00443019667996698   0.432359150492787
    8.000  -0.08979569600589   3.74815514351616   0.726493405776986   1.695347146909250   -1.32882937608962   0.2849197966362740   -0.051296439369391   0.150981191615944   0.508537123776905   0.429104860654150   0.216201318346277   0.387633769846605   -0.193908824182191   -0.148759113452472    0.2094261301289650    0.337650861518699   -0.0507933301386227   -0.1365792860813190   -0.00532310915144333   0.411101516213337
    """)


class KothaEtAl2020regional(KothaEtAl2020):
    """
    Adaptation of the Kotha et al. (2020) GMPE using
    the source and site specific adjustments.
    """
    experimental = True

    #: Required rupture parameters are magnitude, hypocentral location
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'hypo_lat', 'hypo_lon', 'hypo_depth'}

    #: Required site parameter are vs30, lat and lon of the site
    REQUIRES_SITES_PARAMETERS = {'vs30', 'lat', 'lon'}

    kind = "regional"

    def __init__(self, delta_l2l_epsilon=0.0, delta_c3_epsilon=0.0,
                 ergodic=True, c3=None, dl2l=None):
        """
        Instantiate setting the dl2l and c3 terms.
        """
        super().__init__()  # important
        self.delta_l2l_epsilon = delta_l2l_epsilon
        self.delta_c3_epsilon = delta_c3_epsilon
        self.ergodic = ergodic
        attenuation_file = os.path.join(
            DATA_FOLDER, 'kotha_attenuation_regions.geojson')
        self.att = list(fiona.open(attenuation_file))
        tectonic_file = os.path.join(
            DATA_FOLDER, 'kotha_tectonic_regions.geojson')
        self.tec = list(fiona.open(tectonic_file))


class KothaEtAl2020Site(KothaEtAl2020):
    """
    Preliminary adaptation of the Kotha et al. (2020) GMPE using
    a polynomial site amplification function dependent on Vs30 (m/s)
    """
    #: Required site parameter is not set
    REQUIRES_SITES_PARAMETERS = {"vs30"}

    kind = "site"


class KothaEtAl2020Slope(KothaEtAl2020):
    """
    Preliminary adaptation of the Kotha et al. (2020) GMPE using
    a polynomial site amplification function dependent on slope (m/m)
    """
    #: Required site parameter is not set
    REQUIRES_SITES_PARAMETERS = {"slope"}

    kind = "slope"


# Defines the c3 distribution (expected and variance [tau]) for each of the
# residual attenuation regions shown in Weatherill et al. (2020)
C3_REGIONS = CoeffsTable(sa_damping=5, table="""\
    imt        region_1   tau_region_1       region_2   tau_region_2       region_3   tau_region_3       region_4   tau_region_4       region_5   tau_region_5
    pga     -0.45763990     0.12162060    -0.67064060     0.07538030    -0.94171710     0.10869170    -0.58146760     0.06361280    -0.06978450     0.11077130
    0.010   -0.45625230     0.12146360    -0.67063220     0.07654980    -0.93989760     0.10676080    -0.58019070     0.06459080    -0.09103080     0.12710680
    0.025   -0.42309710     0.11756810    -0.63522410     0.07630320    -0.90689690     0.11038900    -0.54050790     0.07589760    -0.12747550     0.16806130
    0.040   -0.39097280     0.11707830    -0.59696790     0.07228980    -0.85504400     0.12076280    -0.50717210     0.07771300    -0.14249730     0.18893460
    0.050   -0.39513900     0.11826330    -0.61908410     0.07248790    -0.89234840     0.12109140    -0.53160100     0.07993880    -0.13942630     0.18369880
    0.070   -0.45957040     0.10764180    -0.71040880     0.09406360    -1.00552160     0.13724410    -0.63070410     0.10958830    -0.13291470     0.17896380
    0.100   -0.52099420     0.13029080    -0.82289280     0.09869630    -1.15422780     0.13169510    -0.75266100     0.11450560    -0.08288840     0.11615220
    0.150   -0.59200740     0.12319070    -0.89972030     0.08844380    -1.24255770     0.16734440    -0.82179530     0.08966500    -0.21028500     0.16064740
    0.200   -0.57153280     0.13489290    -0.84916880     0.07358340    -1.19208340     0.15783590    -0.76891860     0.05839290    -0.21648230     0.17399630
    0.250   -0.55014010     0.14351500    -0.78444460     0.07522180    -1.10829210     0.17141070    -0.70329730     0.06207950    -0.18984460     0.18522660
    0.300   -0.50509870     0.14583000    -0.71748520     0.07218780    -1.02348990     0.16273460    -0.63133950     0.06122670    -0.13991660     0.19909820
    0.350   -0.48056150     0.14950310    -0.67675880     0.06622260    -0.95401710     0.14718070    -0.57059020     0.09801470    -0.11083090     0.20642470
    0.400   -0.46882610     0.15182940    -0.64969270     0.06447500    -0.90303360     0.15704530    -0.53491330     0.11598100    -0.09551250     0.21549390
    0.450   -0.44202290     0.15440110    -0.60495950     0.06457860    -0.86315180     0.14679390    -0.49352160     0.13364080    -0.10089570     0.20926840
    0.500   -0.42273000     0.14456970    -0.56473220     0.07014270    -0.81550440     0.13322880    -0.45404570     0.14251830    -0.07437870     0.20839480
    0.600   -0.37260270     0.11837610    -0.49811720     0.07395310    -0.70844270     0.13133940    -0.39191570     0.13619340    -0.04463750     0.18552380
    0.700   -0.32647710     0.11447010    -0.44770750     0.07916100    -0.64266210     0.11883890    -0.32374040     0.14591360    -0.00538170     0.16207570
    0.750   -0.31212810     0.10504110    -0.42376660     0.07993050    -0.61865170     0.11495330    -0.30231640     0.14234970    -0.00657300     0.15210100
    0.800   -0.30885360     0.09543160    -0.40634850     0.07581030    -0.58033210     0.09944790    -0.28537540     0.12282200    -0.01381650     0.15335160
    0.900   -0.29346380     0.09175490    -0.37405220     0.07021550    -0.53477520     0.09812570    -0.24896750     0.10985930    -0.02411190     0.17978300
    1.000   -0.28336210     0.09792990    -0.35762020     0.07145350    -0.50242310     0.10013390    -0.23100550     0.10572390    -0.01772240     0.17872480
    1.200   -0.25305440     0.08181450    -0.31606630     0.08745020    -0.43732660     0.09978290    -0.18635810     0.09066140     0.01266630     0.16111360
    1.400   -0.22429860     0.08927280    -0.27056900     0.09790690    -0.37099700     0.08939350    -0.14771960     0.06408710     0.01575050     0.17588430
    1.600   -0.20453730     0.08994080    -0.23500030     0.09531560    -0.32625390     0.14451300    -0.09812040     0.06719240     0.06392270     0.14553870
    1.800   -0.18202610     0.09563320    -0.21138570     0.09154740    -0.29356600     0.13625630    -0.05090820     0.06169050     0.14456010     0.09006530
    2.000   -0.16424010     0.09879570    -0.18541590     0.09221880    -0.26361980     0.14820630    -0.01584600     0.03570300     0.13974470     0.11070380
    2.500   -0.15855170     0.13226060    -0.17398540     0.11824340    -0.23076620     0.12647370     0.02472620     0.05698800     0.19515140     0.09070650
    3.000   -0.19290470     0.12142990    -0.20313660     0.11317040    -0.23228890     0.07428720    -0.00302590     0.08495680     0.14726330     0.16269230
    3.500   -0.20613910     0.14784030    -0.19631370     0.12839930    -0.21001250     0.06708210     0.01380630     0.11764140     0.14993210     0.11916760
    4.000   -0.21595710     0.16486300    -0.20044260     0.12168210    -0.19922260     0.09732930     0.00398580     0.12362070     0.19772940     0.08648060
    4.500   -0.22996680     0.14376190    -0.18437470     0.13098060    -0.18127450     0.09355350    -0.03302300     0.12887510    -0.01661270     0.20710350
    5.000   -0.19078450     0.12716500    -0.17112740     0.15092340    -0.13823220     0.09430520    -0.02007680     0.12041280    -0.00218690     0.20707570
    6.000   -0.18627470     0.12265290    -0.15729310     0.15258570    -0.12751980     0.07698390    -0.02685550     0.12260700    -0.00063180     0.19921860
    7.000   -0.13330430     0.13230600    -0.10941040     0.16592930    -0.09001300     0.08303110    -0.00013490     0.12385470     0.05526720     0.19002620
    8.000   -0.11027270     0.14320590    -0.07803880     0.16456320    -0.06784910     0.06704120     0.01757900     0.12861430     0.06941030     0.18559830
    """)


# Heteroskedastic values for single-station phi from measured and smoothed
# distributions of event- and site- orrected within-event residuals
HETERO_PHI0 = CoeffsTable(sa_damping=5, table="""\
  imt         a           b
  pgv    0.44654    0.38340
  pga    0.46719    0.36079
0.010    0.46725    0.36104
0.025    0.46874    0.36515
0.040    0.47377    0.37658
0.050    0.47995    0.38890
0.070    0.48709    0.39474
0.100    0.49618    0.39219
0.150    0.49784    0.37381
0.200    0.49409    0.34159
0.250    0.48895    0.34269
0.300    0.48217    0.33936
0.350    0.48025    0.33843
0.400    0.47515    0.34693
0.450    0.46967    0.34665
0.500    0.46318    0.34085
0.600    0.45123    0.33823
0.700    0.44672    0.35944
0.750    0.44428    0.35283
0.800    0.43930    0.34529
0.900    0.43301    0.34187
1.000    0.42666    0.34207
1.200    0.41647    0.35920
1.400    0.40957    0.37407
1.600    0.40494    0.38140
1.800    0.39905    0.36336
2.000    0.39648    0.35648
2.500    0.39329    0.36285
3.000    0.39085    0.36192
3.500    0.38808    0.38585
4.000    0.38696    0.38696
4.500    0.37283    0.37283
5.000    0.37743    0.37743
6.000    0.38494    0.38494
7.000    0.38589    0.38589
8.000    0.38768    0.38768
""")


def get_tau(imt, mag):
    """
    Heteroskedastic Tau model adopts the "global" model from Al Atik (2015)
    """
    tau_model = TAU_SETUP["global"]
    tau = get_tau_at_quantile(tau_model["MEAN"], tau_model["STD"], None)
    return TAU_EXECUTION["global"](imt, mag, tau)


def get_phi_ss(imt, mag):
    """
    Returns the single station phi (or it's variance) for a given magnitude
    and intensity measure type according to equation 5.14 of Al Atik (2015)
    with coefficients calibrated on the ESM data set and Kotha et al. (2020)
    GMPE
    """
    C = HETERO_PHI0[imt]
    phi = C["a"] + (mag - 5.0) * ((C["b"] - C["a"]) / 1.5)
    phi[mag <= 5.0] = C["a"]
    phi[mag > 6.5] = C["b"]
    return phi


class KothaEtAl2020ESHM20(KothaEtAl2020):
    """
    Adaptation of the Kotha et al. (2020) GMPE for application to the
    2020 European Seismic Hazard Model, as described in Weatherill et al.
    (2020)
    Weatherill, G., Kotha, S. R. and Cotton, F. (2020) "A regionally-adaptable
    'scaled-backbone' ground motion logic tree for shallow seismicity in
    Europe: application to the 2020 European seismic hazard model". Bulletin
    of Earthquake Engineering, 18:5087 - 5117
    There are three key adaptations of the original Kotha et al. (2020) GMM:
    1) The use of the residual attenuation regions, which represent the five
    main sub-regions of Europe with similar attenuation characteristics. The
    assignment to a particular group is now a site-dependent property,
    requiring the definition of the "eshm20_region", an integer value between
    0 and 5 indicating the residual attenuation region to which the site
    belongs (1 - 5) or else the default values (0). For each region an expected
    c3 and variance, tau_c3, are defined from which the resulting c3 is taken
    as a multiple of the number of standard deviations of tau_c3.
    2) The site amplification is defined using a two-segment piecewise linear
    linear function. This form of the GMPE defines the site in terms of a
    measured or inferred Vs30, with the total aleatory variability adjusted
    accordingly.
    3) A magnitude-dependent heteroskedastic aleatroy uncertainty model is
    used for the region-corrected between-event residuals and the site-
    corrected within event residuals. The former taken from the "global" tau
    model of Al Atik (2015), while the later is adapted from the "global" phi0
    model of Al Atik (2015) adapted to the distribution of site-corrected
    within-event residuals determined by the original regression of Kotha et
    al. (2020).
    Al Atik, L. (2015) NGA-East: Ground-Motion Standard Deviation Models for
    Central and Eastern North America, PEER Technical Report, No 2015/07
    """

    #: Required site parameters are vs30, vs30measured and the eshm20_region
    REQUIRES_SITES_PARAMETERS = set(("region", "vs30", "vs30measured"))

    kind = "ESHM20"

    COEFFS = CoeffsTable(sa_damping=5, table="""\
    imt                   e1                 b1                  b2                  b3                  c1                   c2                   c3              tau_c3             phi_s2s         tau_event_0             tau_l2l               phi_0       d0_obs        d1_obs   phi_s2s_obs       d0_inf        d1_inf   phi_s2s_inf
    pgv     1.11912161648479   2.55771078860152   0.353267224391297   0.879839839344054   -1.41931258132547   0.2706807258213520   -0.304426142175370   0.178233997535235   0.560627759977840   0.422935885699239   0.258560350227890   0.446525247049620   3.30975201   -0.53326451    0.36257068   2.78401517   -0.43790954    0.42677529
    pga     3.93782347219377   2.06573167101440   0.304988012209292   0.444773874960317   -1.49787542346412   0.2812414746313380   -0.609876182476899   0.253818777234181   0.606771946180224   0.441761487685862   0.355279206886721   0.467151252053241   2.65261454   -0.43301831    0.38806156   1.88258216   -0.29656277    0.51606938
    0.010   3.94038760011295   2.06441772899445   0.305294151898347   0.444352974827805   -1.50006146971318   0.2816120431678390   -0.608869451197394   0.253797652143759   0.607030265833062   0.441635449735044   0.356047209347534   0.467206938011971   2.56961762   -0.41981270    0.40044760   1.82057082   -0.28687880    0.51867018
    0.025   3.97499686979384   2.04519749120013   0.308841647142436   0.439374383710060   -1.54376149680542   0.2830031280602480   -0.573207556417252   0.252734624432000   0.610030865927204   0.437676505154608   0.368398604288111   0.468698397037258   2.52820436   -0.41328371    0.40623719   1.79206766   -0.28244435    0.52160624
    0.040   4.08702279605872   1.99149766561616   0.319673428428720   0.418531185104657   -1.63671359040283   0.2984823762486280   -0.535139204130152   0.244894143623498   0.626413180170373   0.429637401735540   0.412921240156940   0.473730661220076   2.42784360   -0.39762162    0.41977221   1.72300482   -0.27169228    0.53093819
    0.050   4.18397570399970   1.96912968528742   0.328982074841989   0.389853296189063   -1.66358950776148   0.3121928913488560   -0.555191107011420   0.260330694464557   0.638967955474841   0.433639923327438   0.444324049044753   0.479898166019243   2.30956730   -0.37937894    0.43465421   1.64224336   -0.25906654    0.54404664
    0.070   4.38176649786342   1.92450788134500   0.321182873495225   0.379581373255289   -1.64352914575492   0.3138101953091510   -0.641089475725666   0.286976037026550   0.661064599433347   0.444338223383705   0.470938801038256   0.487060899687138   2.21859665   -0.36551691    0.44921838   1.56920377   -0.24754055    0.55532276
    0.100   4.60722959404894   1.90125096928647   0.298805051330753   0.393002352641809   -1.54339428982169   0.2849395739776680   -0.744270750619733   0.321927482439715   0.663309669119995   0.458382304191096   0.478737965504940   0.496152397155402   2.22143266   -0.36624939    0.46432610   1.53915732   -0.24268225    0.56118134
    0.150   4.78583314367062   1.92620172077838   0.249893333649662   0.435396192976506   -1.38136438628699   0.2254113422224680   -0.815688997995934   0.322145126407981   0.655406109737959   0.459702777214781   0.414046169030935   0.497805936702476   2.35118737   -0.38662423    0.47703588   1.59963888   -0.25206957    0.55911690
    0.200   4.81847463780069   1.97006598187863   0.218722883323200   0.469713318293785   -1.30697558633587   0.1826533194804230   -0.773372802995208   0.301795870071949   0.643585009231006   0.464006126996261   0.321975745683642   0.494075956910651   2.55240529   -0.41806691    0.48025344   1.75423282   -0.27634242    0.54824186
    0.250   4.75134747347049   2.01097445156370   0.195062831156806   0.532210412551561   -1.26259484078950   0.1551575007473110   -0.722012122448262   0.274998157533509   0.623240061418664   0.457687642192569   0.293329526713994   0.488950837091220   2.74904047   -0.44882046    0.46891833   1.96527860   -0.30954933    0.53109975
    0.300   4.65252285968525   2.09278551802016   0.194929941231544   0.557034893811231   -1.24071282395616   0.1370008066985060   -0.660466290850886   0.260774631679394   0.609748615552919   0.457514283978959   0.266836791529257   0.482157450259502   2.93212957   -0.47759683    0.44983953   2.19913556   -0.34634476    0.51454301
    0.350   4.53350897671045   2.14179725762371   0.189511462582876   0.609892595327716   -1.21514531872583   0.1247122464559250   -0.618593385936676   0.254261888951322   0.609506191611413   0.450960093750492   0.231614185359720   0.480254056040507   3.12993498   -0.50873128    0.43569377   2.44212272   -0.38459154    0.50459028
    0.400   4.44193244811952   2.22862498827440   0.200305171692326   0.614767001033243   -1.18897228839914   0.1156387616270450   -0.591574546068960   0.243643375298288   0.615477199296824   0.441122908694716   0.240825814626397   0.475193646646757   3.33033435   -0.54013326    0.43045602   2.67707249   -0.42163058    0.50107926
    0.450   4.33697728548038   2.29103572171716   0.209573442606565   0.634252522127606   -1.18013993982454   0.1100834686500940   -0.555234498707119   0.245883260391068   0.619384591074073   0.436294164198843   0.249245758570064   0.469672671050266   3.50290267   -0.56696060    0.43223316   2.88578405   -0.45456492    0.50146998
    0.500   4.23507897753587   2.35399193121686   0.218088423514177   0.658541873692286   -1.17726165949601   0.1026978146186720   -0.519413341065942   0.238559829231160   0.624993564560933   0.428500398327627   0.243778652813106   0.463165027132890   3.65227902   -0.58990263    0.43887979   3.06576841   -0.48290522    0.50314566
    0.600   4.02306439391925   2.42753387249929   0.218787915039312   0.754615594874153   -1.16678688970027   0.0940582863096094   -0.454043559543982   0.216855298090451   0.635090711921061   0.426296731581312   0.246117069779268   0.451206692163190   3.78937389   -0.61070144    0.44724118   3.20894580   -0.50535303    0.50313816
    0.700   3.83201580121827   2.51268432884949   0.225024841305000   0.765438564882833   -1.16236278470164   0.0865917976706938   -0.397781532595396   0.215716276719833   0.633635835573626   0.425379430268476   0.246750734502549   0.446704739768374   3.90172707   -0.62754331    0.45268279   3.29999705   -0.51955858    0.50200072
    0.750   3.74614211993052   2.55840246083607   0.231604957273506   0.793480645885641   -1.15333203234665   0.0824927940948198   -0.376630503031279   0.209593410875067   0.637877956868669   0.428563811859323   0.245166749142241   0.444311331912854   3.97560847   -0.63847685    0.45583313   3.34616641   -0.52673049    0.50236259
    0.800   3.65168809980226   2.59467404437385   0.237334498546207   0.828241777740572   -1.14645090256437   0.0837439530041729   -0.363246464853852   0.192106714053294   0.638753820813416   0.433880652259324   0.240072953116796   0.439300059540554   4.01969394   -0.64478309    0.46384687   3.37966751   -0.53196741    0.50266660
    0.900   3.51228638217709   2.68810225072750   0.251716558693382   0.845561170244942   -1.13599614124436   0.0834018259445213   -0.333908265367165   0.177456610405390   0.640328521929993   0.438913972406961   0.247662698012904   0.433043490235851   4.05410191   -0.64939631    0.47448247   3.42678904   -0.53940883    0.49912472
    1.000   3.36982044793917   2.74249776483975   0.256784133033388   0.896648260528882   -1.12443352348542   0.0854384622609198   -0.317465939881623   0.171997778367260   0.638429444564638   0.444086895369946   0.238111905941701   0.426703815544157   4.07365692   -0.65153510    0.48134887   3.49473194   -0.55015995    0.49404787
    1.200   3.10224418952824   2.82683484364226   0.262683442221073   0.982921357727718   -1.12116148624672   0.0973231293288241   -0.275616235541070   0.160445653296358   0.640086303643832   0.446121165446841   0.226825215617356   0.416539877732589   4.05048971   -0.64704214    0.48708350   3.57270165   -0.56244631    0.49375397
    1.400   2.84933745949861   2.89911332547612   0.272065572034688   1.040000637056720   -1.12848926976065   0.1002887249133400   -0.234977212668109   0.150949141990859   0.649359928046388   0.457011583377380   0.231922092201736   0.409641113489270   3.99349305   -0.63756820    0.49596280   3.64615783   -0.57391983    0.49885402
    1.600   2.63503429015231   2.98365736561984   0.289670716036571   1.073002118658300   -1.14064711059980   0.1100788214866130   -0.198050139347725   0.148738498099927   0.650540540696659   0.462781403376806   0.223897549097876   0.404985162254916   3.94048869   -0.62914699    0.50237219   3.70614492   -0.58319956    0.50427003
    1.800   2.43032254290751   3.06358840071518   0.316828766785138   1.109809835991900   -1.15419967841818   0.1131278831612640   -0.167123738873435   0.156141593013035   0.656949311785981   0.468432106332010   0.205207971335941   0.399057812399511   3.90126474   -0.62332928    0.49599967   3.73733460   -0.58797931    0.50406486
    2.000   2.24716354703519   3.11067747935049   0.326774527695550   1.132479221218060   -1.16620971948721   0.1162990300931710   -0.140731664063789   0.155054491423268   0.647763389017009   0.476577198889343   0.196850466599025   0.396502973620567   3.84084468   -0.61459972    0.47661567   3.71781492   -0.58487198    0.49679447
    2.500   1.83108464781202   3.23289020747997   0.374214285707986   1.226390493979360   -1.17531326311999   0.1395412164588280   -0.120745041347963   0.176744551716694   0.629481669044830   0.479859874942997   0.190867925368865   0.393288023064441   3.71684077   -0.59605682    0.44991701   3.63149526   -0.57133201    0.48588889
    3.000   1.58259215964414   3.44640772476285   0.454951810817816   1.313954219909490   -1.15664484431459   0.1494902905791280   -0.149050671035371   0.174876785480317   0.616446588503561   0.488309107285476   0.220914253465451   0.390859427279163   3.54176439   -0.56936072    0.42220113   3.49013277   -0.54916732    0.47625314
    3.500   1.32153652077149   3.56445182133655   0.518610571029448   1.394984393379380   -1.16368470057735   0.1543445278711660   -0.142873831246493   0.193619214137258   0.600202108018105   0.479187019962682   0.237281350236338   0.388102875218375   3.34546112   -0.53906501    0.39951709   3.34520093   -0.52645323    0.47012445
    4.000   1.10607064193676   3.64336885536264   0.555331865800278   1.418144933323620   -1.17757508691221   0.1730832048262120   -0.142053716741244   0.193571789393738   0.593046407283143   0.482524831704549   0.233827536969510   0.386956009422453   3.13392178   -0.50620694    0.38303088   3.23169516   -0.50870031    0.46555128
    4.500   1.05987610378773   3.82152567982841   0.666476453600402   1.430548279466630   -1.17323633891422   0.1936210609543320   -0.156076448842833   0.152553585766189   0.581331910387036   0.456765160173852   0.196697785051230   0.372827866334900   2.90740942   -0.47082887    0.36840706   3.13020974   -0.49278809    0.46035806
    5.000   0.82373381739570   3.84747968562771   0.684665144355361   1.496536314224210   -1.20969230916539   0.2213041109459350   -0.126052481240424   0.137919529808920   0.558954997903623   0.464229101930025   0.195572800413952   0.377458812369736   2.68344324   -0.43562070    0.35254196   2.99932475   -0.47213713    0.45347349
    6.000   0.50685354955206   3.80040950285788   0.700805222359295   1.625591116375650   -1.22440411739130   0.2292764533844400   -0.113766839623945   0.141669390606605   0.538973145096788   0.439059204276786   0.190680023411634   0.384862538848542   2.50354874   -0.40714992    0.33854229   2.83412987   -0.44598168    0.44328149
    7.000   0.19675504234642   3.78431011962409   0.716569352050671   1.696310364814470   -1.28517895409644   0.2596896867469380   -0.070585399916418   0.146488759166368   0.523331606096182   0.434396029381517   0.208231539543981   0.385850838707000   2.39499327   -0.38989994    0.33074643   2.69365804   -0.42370171    0.43214765
    8.000  -0.08979569600589   3.74815514351616   0.726493405776986   1.695347146909250   -1.32882937608962   0.2849197966362740   -0.051296439369391   0.150981191615944   0.508537123776905   0.429104860654150   0.216201318346277   0.387633769846605   2.35979253   -0.38432385    0.32874669   2.64017872   -0.41521615    0.42722298
    """)


class KothaEtAl2020ESHM20SlopeGeology(KothaEtAl2020ESHM20):
    """
    Adaptation of the ESHM20-implemented Kotha et al. (2020) model for use when
    defining site amplification based on with slope and geology rather than
    inferred/measured Vs30.
    """
    kind = "geology"

    #: Required site parameter is not set
    REQUIRES_SITES_PARAMETERS = {"region", "slope", "geology"}

    #: Geological Units
    GEOLOGICAL_UNITS = [b"CENOZOIC", b"HOLOCENE", b"JURASSIC-TRIASSIC",
                        b"CRETACEOUS", b"PALEOZOIC", b"PLEISTOCENE",
                        b"PRECAMBRIAN", b"UNKNOWN"]

    COEFFS_FIXED = CoeffsTable(sa_damping=5, table="""\
    imt               V1            V2      phi_s2s
    pgv      -0.32011591   -0.10821634   0.43790400
    pga      -0.21384649   -0.07866419   0.50748976
    0.0100   -0.21204938   -0.07786954   0.50767629
    0.0250   -0.21022718   -0.07807579   0.51225982
    0.0400   -0.20136301   -0.07541908   0.52670786
    0.0500   -0.18838689   -0.07108179   0.54493364
    0.0700   -0.17184538   -0.06571920   0.55944471
    0.1000   -0.16163003   -0.06208429   0.56625853
    0.1500   -0.16374630   -0.06294572   0.56162087
    0.2000   -0.18251959   -0.06818065   0.54476261
    0.2500   -0.21409731   -0.07647401   0.52514338
    0.3000   -0.24386901   -0.08391627   0.50768598
    0.3500   -0.27400911   -0.09230534   0.49756674
    0.4000   -0.30308465   -0.09970264   0.49551267
    0.4500   -0.33071023   -0.10723760   0.49886138
    0.5000   -0.35922788   -0.11481966   0.50191789
    0.6000   -0.38424135   -0.12166326   0.50383885
    0.7000   -0.39238013   -0.12282731   0.50457268
    0.7500   -0.39666705   -0.12348753   0.50522559
    0.8000   -0.39392763   -0.12143042   0.50479578
    0.9000   -0.39358294   -0.12038202   0.50477401
    1.0000   -0.40028453   -0.12131011   0.50481908
    1.2000   -0.40988732   -0.12295578   0.50573308
    1.4000   -0.41409963   -0.12225306   0.50983436
    1.6000   -0.42464935   -0.12508523   0.51411562
    1.8000   -0.42930176   -0.12713783   0.51401210
    2.0000   -0.42551341   -0.12617452   0.50714903
    2.5000   -0.41410716   -0.12316018   0.49538482
    3.0000   -0.39322101   -0.11745721   0.48285566
    3.5000   -0.37377357   -0.11156417   0.47392688
    4.0000   -0.35892700   -0.10678276   0.46498100
    4.5000   -0.34593942   -0.10289679   0.45244339
    5.0000   -0.32936086   -0.09799475   0.43779077
    6.0000   -0.31083191   -0.09367866   0.41948366
    7.0000   -0.29038396   -0.08769334   0.40349430
    8.0000   -0.26798948   -0.07870836   0.39340689
    """)

    COEFFS_RANDOM_INT = CoeffsTable(sa_damping=5, table="""\
    imt       PRECAMBRIAN     PALEOZOIC   JURASSIC-TRIASSIC    CRETACEOUS      CENOZOIC   PLEISTOCENE      HOLOCENE       UNKNOWN
    pgv        0.00750400   -0.00515204         -0.06153554   -0.07234031    0.00736992    0.07121264    0.09269472   -0.03724508
    pga        0.04246887   -0.04689335         -0.12550972   -0.09220607   -0.12856371    0.17767008    0.03348558    0.14349446
    0.0100     0.04467747   -0.04719901         -0.12081014   -0.09275987   -0.12809141    0.17716640    0.03412759    0.13726836
    0.0250     0.03889165   -0.03778649         -0.12589811   -0.09016890   -0.13626584    0.17014868    0.02134094    0.16217912
    0.0400     0.03635013   -0.03184964         -0.12934774   -0.08599260   -0.14795654    0.16674580    0.00796619    0.18513009
    0.0500     0.03822106   -0.02889265         -0.13253481   -0.08320332   -0.15923731    0.16673471   -0.00399086    0.20306016
    0.0700     0.04842870   -0.02905574         -0.14094162   -0.08691977   -0.16757093    0.17089787   -0.01750887    0.22231487
    0.1000     0.06479680   -0.02666152         -0.14538543   -0.09881407   -0.15653309    0.17427644   -0.00898158    0.19655244
    0.1500     0.07592359   -0.03449021         -0.15017012   -0.11171407   -0.15175902    0.18843894    0.00585402    0.17659703
    0.2000     0.06707266   -0.03684141         -0.13591923   -0.10829435   -0.12956987    0.18685906    0.02395110    0.13564373
    0.2500     0.04549958   -0.03952544         -0.11954550   -0.09789634   -0.09538165    0.18260210    0.04789909    0.08864124
    0.3000     0.02309429   -0.04882340         -0.11020150   -0.08252276   -0.07858957    0.18895661    0.04729437    0.08229878
    0.3500    -0.00088865   -0.06080297         -0.11913566   -0.08032219   -0.04845977    0.19164678    0.08244406    0.05906910
    0.4000    -0.01394235   -0.06808797         -0.12746882   -0.07669384   -0.02102129    0.19645651    0.10471131    0.03662866
    0.4500    -0.01906609   -0.07042464         -0.12110002   -0.07169866   -0.00983259    0.18151311    0.11431121    0.02414359
    0.5000    -0.03318464   -0.06324744         -0.09788143   -0.06556113    0.01225172    0.15414730    0.12243590   -0.00543195
    0.6000    -0.05314149   -0.06436228         -0.08251682   -0.06918568    0.03294078    0.14637439    0.13892579   -0.02912185
    0.7000    -0.06083543   -0.06057868         -0.07101886   -0.06961153    0.03534846    0.13592405    0.12293154   -0.01958169
    0.7500    -0.07740521   -0.06314197         -0.07585198   -0.08188938    0.04827896    0.13735651    0.15060589   -0.03505339
    0.8000    -0.08428220   -0.06419910         -0.07628445   -0.08388821    0.04721248    0.14534687    0.14702926   -0.02542895
    0.9000    -0.08850823   -0.06219820         -0.07133046   -0.08391446    0.04406568    0.14264248    0.14560420   -0.02087862
    1.0000    -0.08695550   -0.05738604         -0.06232390   -0.07771771    0.03851214    0.13291669    0.13551423   -0.01697581
    1.2000    -0.08279930   -0.05351583         -0.05407772   -0.06869238    0.03347951    0.12221589    0.12328935   -0.01431109
    1.4000    -0.05949173   -0.03635251         -0.03538338   -0.04669483    0.02212916    0.08304733    0.08247065   -0.00669157
    1.6000    -0.06113887   -0.03333011         -0.03515454   -0.04035535    0.01985126    0.07993816    0.07719776   -0.00437551
    1.8000    -0.05820670   -0.02944153         -0.03437685   -0.03687461    0.01776400    0.07504155    0.07187361   -0.00344321
    2.0000    -0.05511928   -0.03048829         -0.03394715   -0.03445489    0.01725827    0.07299828    0.06981133   -0.00381850
    2.5000    -0.05529251   -0.03317679         -0.03524865   -0.03775773    0.01589549    0.07794768    0.07737765   -0.00519144
    3.0000    -0.04578721   -0.02599141         -0.02744938   -0.03513471    0.01117042    0.06571772    0.06714184   -0.00465567
    3.5000    -0.03981912   -0.02964418         -0.03012732   -0.03891412    0.00837912    0.06854646    0.07457700   -0.00526904
    4.0000    -0.04195342   -0.03422243         -0.03649884   -0.04116601    0.00956496    0.07505321    0.08162242   -0.00456870
    4.5000    -0.04206465   -0.04256136         -0.04317528   -0.04860474    0.01084912    0.08895943    0.09449063   -0.00778319
    5.0000    -0.04307842   -0.05127801         -0.05181793   -0.06233230    0.01139912    0.11137228    0.11654077   -0.01560194
    6.0000    -0.05288405   -0.06153656         -0.06086908   -0.08447680    0.01226796    0.14461811    0.15121486   -0.02571369
    7.0000    -0.05313788   -0.05972963         -0.05698048   -0.08639775    0.01139303    0.14354253    0.15094746   -0.02675383
    8.0000    -0.03321449   -0.03672124         -0.03072781   -0.04927415    0.00752873    0.07812242    0.08445355   -0.01061799
    """)

    COEFFS_RANDOM_GRAD = CoeffsTable(sa_damping=5, table="""\
    imt       PRECAMBRIAN     PALEOZOIC    JURASSIC-TRIASSIC    CRETACEOUS      CENOZOIC    PLEISTOCENE      HOLOCENE      UNKNOWN
    pgv       -0.00151889    0.00104283           0.01245549    0.01464249   -0.00149176    -0.01441424   -0.01876246   0.00753883
    pga        0.01074547   -0.01778485          -0.02616742   -0.02035435   -0.04046745     0.04524993   -0.00317088   0.05341858
    0.0100     0.01110581   -0.01817585          -0.02362103   -0.01978543   -0.04021423     0.04414265   -0.00393577   0.05210902
    0.0250     0.01054942   -0.01375128          -0.03204231   -0.02329083   -0.04298207     0.04740963   -0.00096118   0.05596879
    0.0400     0.01063103   -0.01076982          -0.03745690   -0.02482504   -0.04632847     0.04969505   -0.00047448   0.05991117
    0.0500     0.01167666   -0.00905529          -0.04064013   -0.02545862   -0.04918531     0.05122655   -0.00149106   0.06298322
    0.0700     0.01522096   -0.00866859          -0.04456948   -0.02765443   -0.05138391     0.05364480   -0.00391298   0.06719302
    0.1000     0.01898016   -0.00727708          -0.04378241   -0.02975827   -0.04595861     0.05216548   -0.00146284   0.05692836
    0.1500     0.02078272   -0.01041484          -0.04151626   -0.03076920   -0.04242245     0.05227380    0.00117824   0.05081748
    0.2000     0.01679209   -0.01251480          -0.03159881   -0.02500107   -0.03540564     0.04583389    0.00087255   0.04165261
    0.2500     0.01047086   -0.01254293          -0.01977080   -0.01652711   -0.02642314     0.03637504   -0.00140843   0.03164479
    0.3000     0.00492601   -0.01305137          -0.00935782   -0.00502304   -0.02551784     0.02973268   -0.01268061   0.03384470
    0.3500     0.00068207   -0.01138237          -0.00760508   -0.00115452   -0.01955133     0.02442332   -0.01202183   0.03011394
    0.4000    -0.00007763   -0.00826703          -0.00615682    0.00128058   -0.01483467     0.02048270   -0.01209326   0.02192539
    0.4500     0.00259298   -0.00548582          -0.00129611    0.00457027   -0.01408782     0.01079136   -0.01568248   0.01890988
    0.5000     0.00454355    0.00005525           0.00659854    0.00875027   -0.00980836    -0.00351454   -0.01917515   0.01134711
    0.6000     0.00604685    0.00440535           0.01064001    0.00948379   -0.00612234    -0.01236742   -0.01943292   0.00551060
    0.7000     0.01095305    0.00931412           0.01504193    0.01493469   -0.00924357    -0.02220648   -0.02871351   0.00826076
    0.7500     0.01369981    0.01235745           0.01395140    0.01427521   -0.00674976    -0.02722199   -0.02425577   0.00311240
    0.8000     0.01694348    0.01219280           0.01497930    0.01689579   -0.00946095    -0.02828030   -0.02848641   0.00440800
    0.9000     0.01892074    0.01405716           0.01640228    0.01933592   -0.01002078    -0.03204632   -0.03297697   0.00504239
    1.0000     0.02512104    0.01688438           0.01837402    0.02268965   -0.01141742    -0.03884472   -0.03943641   0.00505860
    1.2000     0.03327967    0.01980375           0.01991772    0.02534680   -0.01264104    -0.04622581   -0.04560074   0.00437189
    1.4000     0.04722160    0.02594108           0.02737100    0.03392452   -0.01676537    -0.06227400   -0.06074314   0.00371247
    1.6000     0.05194873    0.02697120           0.02973620    0.03495830   -0.01732309    -0.06667116   -0.06444819   0.00317279
    1.8000     0.05328046    0.02727815           0.03128253    0.03528866   -0.01722153    -0.06854742   -0.06616442   0.00307244
    2.0000     0.05210980    0.02951740           0.03229472    0.03437065   -0.01640282    -0.06939661   -0.06746935   0.00295572
    2.5000     0.04758107    0.02930987           0.03042051    0.03195468   -0.01450440    -0.06586126   -0.06512613   0.00334992
    3.0000     0.04481012    0.02796003           0.02876396    0.03433113   -0.01191492    -0.06543141   -0.06637460   0.00371933
    3.5000     0.03960965    0.02549857           0.02640242    0.03376046   -0.00933018    -0.06073490   -0.06386255   0.00364497
    4.0000     0.03061486    0.02435131           0.02643817    0.03285260   -0.00685464    -0.05646726   -0.06036334   0.00381148
    4.5000     0.02253163    0.02199085           0.02451190    0.02935520   -0.00551367    -0.04940159   -0.05254284   0.00387614
    5.0000     0.01675139    0.01898142           0.02123988    0.02293046   -0.00517242    -0.04022363   -0.04159239   0.00326963
    6.0000     0.00884584    0.01248789           0.01338540    0.01433546   -0.00328602    -0.02576612   -0.02615088   0.00321300
    7.0000     0.00754320    0.01081496           0.00952506    0.01292858   -0.00247815    -0.02210686   -0.02284293   0.00365737
    8.0000     0.01794388    0.01906271           0.01478150    0.02515701   -0.00401437    -0.03950798   -0.04270189   0.00480742
    """)


# Add aliases for the ESHM20 selection - shallow crustal sources
eshm20_crust_lines = '''\
ESHM20ShallowCrustVLowStressFastAtten -2.85697 -1.732051
ESHM20ShallowCrustVLowStressMidAtten -2.85697 0.000000
ESHM20ShallowCrustVLowStressSlowAtten -2.85697 1.732051
ESHM20ShallowCrustLowStressFastAtten -1.35563 -1.732051
ESHM20ShallowCrustLowStressMidAtten -1.35563 0.000000
ESHM20ShallowCrustLowStressSlowAtten -1.35563 1.732051
ESHM20ShallowCrustMidStressFastAtten 0.00000 -1.732051
ESHM20ShallowCrustMidStressMidAtten 0.00000 0.000000
ESHM20ShallowCrustMidStressSlowAtten 0.00000 1.732051
ESHM20ShallowCrustHighStressFastAtten 1.35563 -1.732051
ESHM20ShallowCrustHighStressMidAtten 1.35563 0.000000
ESHM20ShallowCrustHighStressSlowAtten 1.35563 1.732051
ESHM20ShallowCrustVHighStressFastAtten 2.85697 -1.732051
ESHM20ShallowCrustVHighStressMidAtten 2.85697 0.000000
ESHM20ShallowCrustVHighStressSlowAtten 2.85697 1.732051'''.splitlines()

for line_shallow in eshm20_crust_lines:
    alias, sig_mu_eps, c3_eps = line_shallow.split()
    add_alias(alias, KothaEtAl2020ESHM20,
              sigma_mu_epsilon=float(sig_mu_eps),
              c3_epsilon=float(c3_eps))


# Add aliases for the ESHM20 Iceland ground motion model
# dl2l values
ICELAND_dL2L = {
    "IMTs": ['PGA', 'SA(0.01)', 'SA(0.025)', 'SA(0.04)', 'SA(0.05)',
             'SA(0.07)', 'SA(0.1)', 'SA(0.15)', 'SA(0.2)', 'SA(0.25)',
             'SA(0.3)', 'SA(0.35)', 'SA(0.4)', 'SA(0.45)', 'SA(0.5)',
             'SA(0.6)', 'SA(0.7)', 'SA(0.75)', 'SA(0.8)', 'SA(0.9)', 'SA(1.0)',
             'SA(1.2)', 'SA(1.4)', 'SA(1.6)', 'SA(1.8)', 'SA(2.0)', 'SA(2.5)',
             'SA(3.0)', 'SA(3.5)', 'SA(4.0)', 'SA(4.5)', 'SA(5.0)', 'SA(6.0)',
             'SA(7.0)', 'SA(8.0)'],
    "VLow": [-1.320714,  -1.334702, -1.411144, -1.593190, -1.732470, -1.846624,
             -1.869080, -1.666701, -1.370120, -1.239216, -1.107578, -0.953322,
             -0.919893, -0.888578, -0.819694, -0.763689, -0.703255, -0.641188,
             -0.592629, -0.560762, -0.453129, -0.320960, -0.235436, -0.159245,
             -0.011255, 0.114595, 0.268825, 0.214030, 0.061128, -0.066012,
             -0.016226, 0.005109, 0.144121, 0.125620, -0.081479],
    "Low": [-0.787319, -0.800154, -0.858052, -0.973254, -1.065389, -1.139585,
            -1.150332, -1.045077, -0.886725, -0.798828, -0.706965, -0.605590,
            -0.558332, -0.514375, -0.453700, -0.394184, -0.332799, -0.273109,
            -0.232198, -0.188936, -0.095642, 0.019582, 0.112757, 0.176902,
            0.296832, 0.410135, 0.555383, 0.545697, 0.417368, 0.285042,
            0.279085, 0.298731, 0.430396, 0.438246, 0.243113],
    "Mid": [-0.305692, -0.317486, -0.358640, -0.413486, -0.463050, -0.501166,
            -0.501340, -0.483784, -0.450245, -0.401182, -0.345233, -0.291607,
            -0.231861, -0.176490, -0.123226, -0.060540, 0.001704, 0.059246,
            0.093252, 0.146803, 0.227150, 0.327073, 0.427158, 0.480424,
            0.575018, 0.676991, 0.814129, 0.845175, 0.739034, 0.602026,
            0.545734, 0.563855, 0.688888, 0.720531, 0.536202],
    "High": [0.175935, 0.165182, 0.140772, 0.146282, 0.139289, 0.137253,
             0.147652, 0.077509, -0.013765, -0.003536, 0.016499, 0.022376,
             0.094610, 0.161395, 0.207248, 0.273104, 0.336207, 0.391601,
             0.418702, 0.482542, 0.549942, 0.634564, 0.741559, 0.783946,
             0.853204, 0.943847, 1.072875, 1.144653, 1.060700, 0.919010,
             0.812383, 0.828979, 0.947380, 1.002816, 0.829291],
    "VHigh": [0.709330, 0.699730, 0.693864, 0.766218, 0.806370, 0.844292,
              0.866400, 0.699133, 0.469630, 0.436852, 0.417112, 0.370108,
              0.456171, 0.535598, 0.573242, 0.642609, 0.706663, 0.759680,
              0.779133, 0.854368, 0.907429, 0.975106, 1.089752, 1.120093,
              1.161291, 1.239387, 1.359433, 1.476320, 1.416940, 1.270064,
              1.107694, 1.122601, 1.233655, 1.315442, 1.153883],
}

# Build the set of aliases
for stress in list(ICELAND_dL2L)[1:]:
    dl2l = dict(list(zip(ICELAND_dL2L["IMTs"], ICELAND_dL2L[stress])))
    for c3_key, c3_eps in zip(["Fast", "Mid", "Slow"],
                              [-1.732051, 0.0, 1.732051]):
        alias = "ESHM20Iceland{:s}Stress{:s}Atten".format(stress, c3_key)
        add_alias(alias, KothaEtAl2020ESHM20, dl2l=dl2l, c3_epsilon=c3_eps)


C3_REGIONS_AVGSA = CoeffsTable(sa_damping=5, table="""\
    imt                  region_1      tau_region_1         region_2     tau_region_2         region_3     tau_region_3         region_4     tau_region_4         region_5     tau_region_5
    AvgSA(0.050)    -0.4656716000      0.1180142000    -0.7133721000     0.0946938000    -0.9685200000     0.1338548000    -0.5888355000     0.1820359000    -0.1240944000     0.1570220000
    AvgSA(0.100)    -0.5310625000      0.1309543000    -0.8190398000     0.1062527000    -1.1068865000     0.1375049000    -0.7067665000     0.1882153000    -0.1469747000     0.1360697000
    AvgSA(0.150)    -0.5581186000      0.1317465000    -0.8442356000     0.1110502000    -1.1565822000     0.1337646000    -0.7421298000     0.1763761000    -0.1974244000     0.1813739000
    AvgSA(0.200)    -0.5529085000      0.1327567000    -0.8229416000     0.1162142000    -1.1460833000     0.1362717000    -0.7302299000     0.1698309000    -0.1933789000     0.1984123000
    AvgSA(0.250)    -0.5372297000      0.1328342000    -0.7929952000     0.1156845000    -1.1136433000     0.1366984000    -0.7016690000     0.1682029000    -0.1857899000     0.2149315000
    AvgSA(0.300)    -0.5254234000      0.1334462000    -0.7654788000     0.1150564000    -1.0814921000     0.1377804000    -0.6748147000     0.1734933000    -0.1752417000     0.2206030000
    AvgSA(0.400)    -0.4898486000      0.1312907000    -0.7025190000     0.1123262000    -1.0049232000     0.1345776000    -0.6052932000     0.1785973000    -0.1397568000     0.2171827000
    AvgSA(0.500)    -0.4563844000      0.1284697000    -0.6492117000     0.1073397000    -0.9333463000     0.1320078000    -0.5430056000     0.1839070000    -0.1067728000     0.2055740000
    AvgSA(0.600)    -0.4252573000      0.1246073000    -0.6008299000     0.1033843000    -0.8654133000     0.1245591000    -0.4767390000     0.1872128000    -0.0830896000     0.1956748000
    AvgSA(0.700)    -0.4001896000      0.1204433000    -0.5650228000     0.0985488000    -0.8101765000     0.1193220000    -0.4274777000     0.1901049000    -0.0532689000     0.1719868000
    AvgSA(0.800)    -0.3825042000      0.1120253000    -0.5299286000     0.0981232000    -0.7604156000     0.1162526000    -0.3847776000     0.1938995000    -0.0476572000     0.1797690000
    AvgSA(0.900)    -0.3608326000      0.1070064000    -0.4965110000     0.0951311000    -0.7121393000     0.1103616000    -0.3488966000     0.1921782000    -0.0319083000     0.1744172000
    AvgSA(1.000)    -0.3445518000      0.1019015000    -0.4680719000     0.0933419000    -0.6699090000     0.1067803000    -0.3119548000     0.1899378000    -0.0231772000     0.1709575000
    AvgSA(1.250)    -0.3085981000      0.0942465000    -0.4043969000     0.0921493000    -0.5814821000     0.1020569000    -0.2430170000     0.1879356000     0.0096703000     0.1518318000
    AvgSA(1.500)    -0.2769769000      0.0909386000    -0.3528436000     0.0920438000    -0.5123643000     0.0996129000    -0.1845231000     0.1803464000     0.0388261000     0.1430487000
    AvgSA(1.750)    -0.2575783000      0.0904296000    -0.3244613000     0.0952487000    -0.4561763000     0.0864028000    -0.1453873000     0.1738825000     0.0564608000     0.1302481000
    AvgSA(2.000)    -0.2463514000      0.0909783000    -0.3030979000     0.0949550000    -0.4213413000     0.0836152000    -0.1120286000     0.1733245000     0.0705411000     0.1301361000
    AvgSA(2.500)    -0.2395616000      0.1008508000    -0.2822054000     0.0973938000    -0.3730267000     0.0823939000    -0.0721809000     0.1728203000     0.1038858000     0.1195501000
    AvgSA(3.000)    -0.2503677000      0.1049288000    -0.2777608000     0.0968775000    -0.3381454000     0.0639946000    -0.0809930000     0.1658070000     0.1030135000     0.1401671000
    AvgSA(3.500)    -0.2298273000      0.1105661000    -0.2450972000     0.0987783000    -0.2853042000     0.0523550000    -0.0565065000     0.1612552000     0.1442919000     0.0838447000
    AvgSA(4.000)    -0.2181743000      0.1188117000    -0.2285558000     0.1063640000    -0.2579791000     0.0561007000    -0.0374827000     0.1651242000     0.1518847000     0.0902318000
    AvgSA(4.500)    -0.2189357000      0.0947278000    -0.2256616000     0.1216485000    -0.2320831000     0.0557586000    -0.0572455000     0.1370899000    -0.0290722000     0.1395083000
    AvgSA(5.000)    -0.2069729000      0.0981588000    -0.2110292000     0.1268101000    -0.2118488000     0.0593289000    -0.0379903000     0.1392759000    -0.0114503000     0.1387377000
""")


# Coefficients for components of variability for AvgSa based on the indirect
# variability approach and the ESHM20-based cross-correlation model
COEFFS_AVGSA_TAU_PHI = CoeffsTable(sa_damping=5, table="""\
    imt                    tau1          tau2          tau3          tau4         phi0_a        phi0_b    phi_s2s_obs   phi_s2s_inf
    AvgSA(0.050)    0.450265228   0.425534126   0.385047171   0.349550065    0.469793727   0.373637252    0.422827263   0.533408863
    AvgSA(0.100)    0.443613368   0.419285824   0.379383631   0.344424617    0.469327412   0.368595315    0.441139506   0.539238447
    AvgSA(0.150)    0.437547947   0.413317059   0.374115591   0.339638982    0.463561498   0.350760067    0.446779972   0.532620604
    AvgSA(0.200)    0.433537996   0.409666567   0.370677538   0.336554639    0.456535303   0.338264036    0.443403456   0.521297604
    AvgSA(0.250)    0.430914023   0.407242752   0.368479157   0.334545957    0.450475499   0.330248213    0.436886715   0.510932860
    AvgSA(0.300)    0.429339157   0.405793790   0.367079555   0.333355308    0.445321228   0.326114255    0.431313565   0.503221482
    AvgSA(0.400)    0.426838581   0.403389369   0.364995154   0.331386762    0.433932123   0.317686930    0.426627088   0.493039840
    AvgSA(0.500)    0.426838581   0.403389369   0.364995154   0.331386762    0.427499912   0.318111364    0.426920015   0.488374099
    AvgSA(0.600)    0.426838581   0.403389369   0.364995154   0.331386762    0.421075089   0.315927942    0.430202863   0.484867766
    AvgSA(0.700)    0.426838581   0.403389369   0.364995154   0.331386762    0.415377483   0.315623688    0.433889171   0.481497235
    AvgSA(0.800)    0.426838581   0.403389369   0.364995154   0.331386762    0.409761405   0.316458809    0.437527308   0.478941984
    AvgSA(0.900)    0.426838581   0.403389369   0.364995154   0.331386762    0.404749602   0.318527404    0.441076619   0.477263647
    AvgSA(1.000)    0.426838581   0.403389369   0.364995154   0.331386762    0.400538795   0.319660717    0.444733966   0.476613844
    AvgSA(1.250)    0.426838581   0.403389369   0.364995154   0.331386762    0.391173979   0.323422526    0.449968173   0.475330279
    AvgSA(1.500)    0.426838581   0.403389369   0.364995154   0.331386762    0.384207569   0.324736699    0.448480052   0.472810059
    AvgSA(1.750)    0.426838581   0.403389369   0.364995154   0.331386762    0.378940921   0.324776768    0.444166577   0.469909402
    AvgSA(2.000)    0.426838581   0.403389369   0.364995154   0.331386762    0.375055253   0.327256765    0.438096814   0.466775537
    AvgSA(2.500)    0.426838581   0.403389369   0.364995154   0.331386762    0.368731863   0.331137495    0.425405874   0.461923495
    AvgSA(3.000)    0.426838581   0.403389369   0.364995154   0.331386762    0.362799048   0.333181208    0.412446255   0.456919212
    AvgSA(3.500)    0.426838581   0.403389369   0.364995154   0.331386762    0.359200676   0.337125666    0.399372262   0.452070311
    AvgSA(4.000)    0.426838581   0.403389369   0.364995154   0.331386762    0.357004460   0.337999154    0.388331894   0.447539253
    AvgSA(4.500)    0.426838581   0.403389369   0.364995154   0.331386762    0.355726550   0.340391710    0.379435900   0.442846515
    AvgSA(5.000)    0.426838581   0.403389369   0.364995154   0.331386762    0.354587686   0.340853193    0.371880106   0.438313782
    """)


def get_heteroskedastic_tau_phi0_avgsa(imt, mag):
    """Returns the heteroskedastic between-event and single-station within-
    event variability for AvgSa
    """
    C = COEFFS_AVGSA_TAU_PHI[imt]
    tau = np.full_like(mag, C["tau1"])
    tau[mag > 6.5] = C["tau4"]
    idx = (mag > 5.5) & (mag <= 6.5)
    tau[idx] = ITPL(mag[idx], C["tau4"], C["tau3"], 5.5, 1.0)
    idx = (mag > 5.0) & (mag <= 5.5)
    tau[idx] = ITPL(mag[idx], C["tau3"], C["tau2"], 5.0, 0.5)
    idx = (mag > 4.5) & (mag <= 5.0)
    tau[idx] = ITPL(mag[idx], C["tau2"], C["tau1"], 4.5, 0.5)

    phi0 = C["phi0_a"] + (mag - 5.0) * ((C["phi0_b"] - C["phi0_a"]) / 1.5)
    phi0[mag <= 5.0] = C["phi0_a"]
    phi0[mag > 6.5] = C["phi0_b"]
    return tau, phi0
