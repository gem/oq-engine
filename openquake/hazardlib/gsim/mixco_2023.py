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
Module exports :class:`MixcoEtAl2023`,
               :class:`MixcoEtAl2020Site`,
               :class:`MixcoEtAl2020Slope`, 
               :class:`MixcoEtAl2023regional`
"""
import os
import numpy as np
from scipy.constants import g
from shapely.geometry import Point, shape
from shapely.prepared import prep
from openquake.baselib.general import CallableDict
from openquake.hazardlib.geo.packager import fiona
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA, from_string
from openquake.hazardlib.gsim.nga_east import ITPL


DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'Mixco_2023')

CONSTANTS = {"Mref": 4.5, "Rref": 30., "Mh": 5.7,
             "h_D10": 4.0, "h_10D20": 8.0, "h_D20": 12.0}


# TODO add Mixco et al. (2023) sigma mu coefficients
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


def _get_h(C, hypo_depth):
    """
    Returns the depth-specific coefficient
    """
    return np.where(
        hypo_depth <= 10.,
        CONSTANTS["h_D10"],
        np.where(hypo_depth > 20., CONSTANTS["h_D20"], CONSTANTS["h_10D20"]))


get_distance_coefficients = CallableDict()


@get_distance_coefficients.add("base", "site", "slope")
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


def get_distance_coefficients_2(att, delta_c3_epsilon, C, imt, sctx):
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
            l = np.concatenate([np.where((sctx['lon'] == p.x) &
                               (sctx['lat'] == p.y))[0] for p in contained])
            delta_c3[l, 0] = feature['properties'][str(imt)]
            delta_c3[l, 1] = feature['properties'][str(imt)+'_se']

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
            l = np.concatenate([np.where((ctx['hypo_lon'] == p.x) &
                               (ctx['hypo_lat'] == p.y))[0] for p in contained])
            dl2l[l, 0] = feature['properties'][str(imt)]
            dl2l[l, 1] = feature['properties'][str(imt)+'_se']

    return dl2l[:, 0] + delta_l2l_epsilon * dl2l[:, 1]


#TODO update with Mixco et al. information
def get_sigma_mu_adjustment(C, imt, ctx):
    """
    Returns the sigma_mu adjusment factor, which is taken as the
    maximum of tau_L2L and the sigma_mu. For M < 7.4
    the sigma statistical does not exceed tau_L2L at any period or
    distance. For M > 7.4, sigma_mu is approximately linear up to M 8.0
    so we interpolate between the two values and cap sigma statistical
    at M 8.0
    """
    C_SIG_MU = SIGMA_MU_COEFFS[imt]
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
    if kind == "base":  # no site amplification
        ampl = 0.
    elif kind in {"site", "regional"}:
        # Render with respect to 800 m/s reference Vs30
        sref = np.log(ctx.vs30 / 800.)
        ampl = (C["g0_vs30"] + C["g1_vs30"] * sref +
                C["g2_vs30"] * (sref ** 2.))
    elif kind == "slope":
        sref = np.log(ctx.slope / 0.1) # Render wrt to 0.1 m/m ref slope
        ampl = (C["g0_slope"] + C["g1_slope"] * sref +
                C["g2_slope"] * (sref ** 2.))
    return ampl


def get_stddevs(kind, ergodic, C, ctx, imt):
    """
    Returns the homoskedastic standard deviation model
    """
    tau = C["tau_event_0"]
    phi = C["phi_0"]
    if ergodic:
        if kind in {"site", "regional"}:
            phi = np.sqrt(phi ** 2.0 + C["phi_s2s_vs30"] ** 2.)
        elif kind == 'slope':
            phi = np.sqrt(phi ** 2. + C["phi_s2s_slope"] ** 2.)
        else:
            phi = np.sqrt(phi ** 2. + C["phis2s"] ** 2.)
    return [np.sqrt(tau ** 2. + phi ** 2.), tau, phi]


class MixcoEtAl2023(GMPE): #TODO add paper reference once published
    """
    Implements the Mixco et al. (2023) GMPE. This GMPE is a recalibration of
    the Kotha et al. (2020) GMPE based on strong-motion data from El Salvador
    provided in the RADES dataset. <ADD REFERENCE TO PAPER ONCE PUBLISHED>

    As within the Kotha et al. (2020) GMPE, this GMPE is designed for regional
    adaptation within a logic-tree framework, and as such contains several
    parameters that can be calibrated on input:
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
    Again, as within the Kotha et al. (2020) GMPE, in the core form of this 
    GMPE no site term is included. This is added in the subclasses.

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

    #: Required distance measure is Rjb (eq. 1 of Kotha et al. 2020).
    REQUIRES_DISTANCES = {'rjb'}

    def __init__(self, sigma_mu_epsilon=0.0, c3_epsilon=0.0, ergodic=True,
                 dl2l=None, c3=None, **kwargs):
        """
        Instantiate setting the sigma_mu_epsilon and c3 terms
        """
        super().__init__(sigma_mu_epsilon=sigma_mu_epsilon,
                         c3_epsilon=c3_epsilon, ergodic=ergodic, **kwargs)
        self.sigma_mu_epsilon = sigma_mu_epsilon
        self.c3_epsilon = c3_epsilon
        self.ergodic = ergodic
        if dl2l:
            # Check that the input is a dictionary and p
            if not isinstance(dl2l, dict):
                raise IOError("For Mixco et al. (2023) GMM, source-region "
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
                raise IOError("For Mixco et al. (2023) GMM, residual "
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
            if self.kind == 'regional':
                c3 = get_distance_coefficients_2(self.att,
                                                 self.delta_c3_epsilon,
                                                 C, imt, ctx)
            else:
                c3 = self.c3
            fp = get_distance_term(self.kind, c3, self.c3_epsilon,
                                   C, ctx, imt)
            mean[m] = (get_magnitude_scaling(C, ctx.mag) + fp +
                       get_site_amplification(self.kind, extra, C, ctx, imt))
            # GMPE originally in cm/s/s - convert to g
            if imt.string.startswith(('PGA', 'SA')):
                mean[m] -= np.log(100.0 * g)
            sig[m], tau[m], phi[m] = get_stddevs(self.kind, self.ergodic,
                                                 C, ctx, imt)
            if self.dl2l:
                # The source-region parameter is specified explicity
                mean[m] += self.dl2l[imt]["dl2l"]

            elif self.kind == 'regional':
                dl2l = get_dl2l(self.tec, ctx, imt, self.delta_l2l_epsilon)
                mean[m] += dl2l

            elif self.sigma_mu_epsilon:
                # epistemic uncertainty factor (sigma_mu) multiplied by
                # the number of standard deviations
                sigma_mu = get_sigma_mu_adjustment(C, imt, ctx)
                mean[m] += self.sigma_mu_epsilon * sigma_mu

    # Coefficients obtained directly from the regression outputs of
    # Mixco et al. (2020)
    COEFFS = CoeffsTable(sa_damping=5, table="""\
      imt           e1           b1               b2             b3               c1             c2               c3         tau_c3          phis2s     tau_event_0         tau_l2l            phi_0         g0_vs30         g1_vs30        g2_vs30     phi_s2s_vs30        g0_slope       g1_slope        g2_slope     phi_s2s_slope
   	  pgv  0.860260357	1.394508265 	-0.128071525	1.081444761 	-1.449036601	0.223455536 	-0.066180908	0.143248159 	0.235290455 	0.402920114 	0.458861490 	-0.033329822	-0.045698158   	 0.024234632	0.100860670 	-0.007622296	-0.011597866   -0.000776826 	0.103712027       0.103712027
	  pga  3.707131907	0.997342071	    -0.192522105	0.663287743 	-1.399563953	0.175983648 	-0.354727717	0.184023656 	0.370645796 	0.381796983 	0.438072442 	-0.041537319	-0.081029274	-0.003174677	0.236508633 	-0.010755298	-0.008435154	0.001471157 	0.230881736       0.230881736
	0.010  3.708307622	1.011790190	    -0.185666111	0.665717109 	-1.400092073	0.175492773 	-0.350694830	0.184487029 	0.371935140 	0.382353316 	0.437731590 	-0.041712339	-0.081448993	-0.003345166	0.236933589 	-0.010851166	-0.007965072	0.001721640 	0.233263459       0.233263459
	0.025  3.677006633	0.907379080	    -0.201256255	0.688558315 	-1.334857462	0.124177441 	-0.318827822	0.242576529 	0.331275585 	0.306743194 	0.494133478 	-0.033266272	-0.069738732	-0.004258073	0.172870724 	-0.007691678	-0.010204437	0.000108812 	0.171902080       0.171902080
	0.040  3.861875397	0.984635567	    -0.172556629	0.600191368 	-1.40171656	    0.166301945 	-0.394518934	0.244924967 	0.373287619 	0.326471747 	0.447412500 	-0.040187183	-0.076131314	 0.002550111	0.230784018 	-0.009077966	-0.008637118	0.001081917 	0.230595878       0.230595878
	0.050  4.075431605	1.031301538	    -0.163511021	0.467340280  	-1.437253888	0.191149079 	-0.470347311	0.228729188 	0.405053319 	0.348839748 	0.427637298 	-0.047233100	-0.094792084	-0.005215337	0.258283748 	-0.009503494	-0.008179721	0.001152869 	0.254389712       0.254389712
	0.070  4.282936205	0.888572790	    -0.229042948	0.420871754 	-1.528536607	0.232520644 	-0.511385083	0.233356965 	0.469727863 	0.351853309 	0.417248924 	-0.043009564	-0.068935638	 0.005098159	0.333466549 	-0.021413073	-0.006292182	0.005771930 	0.326031638       0.326031638
	0.100  4.446038975	0.728891558	    -0.322735749	0.441407413 	-1.504806563	0.219698020 	-0.527152599	0.223976733 	0.518946279 	0.384372295 	0.410094783 	-0.020357861	-0.072315159	-0.032603237	0.399671385 	-0.005002738	-0.021437090   -0.004059473 	0.385849957       0.385849957
	0.150  4.553778116	0.710264462	    -0.334386319	0.483662767 	-1.452952258	0.221027690 	-0.562804873	0.325620872 	0.475562899 	0.387326023 	0.440932497 	-0.029308325	-0.065672486	-0.014804422	0.334702063 	-0.013684589	-0.012308625	0.001386934 	0.344281094       0.344281094
	0.200  4.685918226	0.987683936	    -0.209619045	0.496999069 	-1.445162413	0.213206853 	-0.530656607	0.306029436 	0.446257444 	0.427334286 	0.434683851 	-0.037062410	-0.084843717	-0.015618591	0.307000861 	-0.018456276	 0.006009842	0.011284322 	0.297213924       0.297213924
	0.250  4.673325454	0.968738773	    -0.217770765	0.488817640  	-1.437967275	0.226731244 	-0.540404267	0.327027893 	0.437458692 	0.423524981 	0.438420577 	-0.036716820	-0.092950229	-0.024344004	0.290406108 	-0.014292500	 0.004380882	0.008940333 	0.303323771       0.303323771
	0.300  4.425406597	1.084892120	    -0.262451836	0.753337549	    -1.448862605	0.236021477 	-0.471301479	0.306656289 	0.435005136 	0.490385120  	0.431617738 	-0.056583082	-0.118235609	-0.017919334	0.266585518 	-0.012834766	 0.013083712	0.010165534 	0.285270605       0.285270605
	0.350  4.408150368	1.059060870	    -0.273424103	0.717685833	    -1.448422375	0.242214516 	-0.451479445	0.286486735 	0.425134479 	0.487272062 	0.431503527 	-0.053955383	-0.102543797	-0.000996504	0.276736218 	-0.018944143	 0.009000128	0.012073242 	0.286846487       0.286846487
	0.400  4.215934447	0.994198285	    -0.375181313	0.863018188 	-1.455676102	0.257199154 	-0.401443197	0.306236310 	0.356805390 	0.539784346 	0.462291236 	-0.043568299	-0.107875190	-0.026103477	0.191436234 	-0.012449021	-0.000964898	0.006532937 	0.188541107       0.188541107
	0.450  4.135871520	0.996959133	    -0.404992579	0.849167649 	-1.462750947	0.269062652 	-0.385126425	0.292081260 	0.368223922 	0.549018158 	0.440065440 	-0.051136839	-0.109553647	-0.010286964	0.222882278 	-0.017192904	 0.004574896	0.010639025 	0.208504820       0.208504820
	0.500  4.054515264	1.016717403 	-0.382484610    0.847271750 	-1.453960841	0.260179254 	-0.363230061	0.265560344 	0.384967231 	0.531714034 	0.433440249 	-0.067621388	-0.146716065	-0.013688740	0.237502650 	-0.021959258	 0.006142927	0.013949614 	0.244222243       0.244222243
	0.600  3.937072014	1.354179661 	-0.275106816	0.873168866 	-1.460396049	0.243941099 	-0.292144971	0.249033607 	0.432123315 	0.560508401 	0.386246974 	-0.102597607	-0.218160302	-0.014885305	0.280893415 	-0.030248583	-0.004943167	0.015174090 	0.307240019       0.307240019
	0.700  3.735920605	1.289429984 	-0.298041577	0.912606115 	-1.453442736	0.227383427 	-0.196069821	0.278934274 	0.448179814 	0.544320327 	0.389102680 	-0.128813301	-0.270407923	-0.013104171	0.318900651 	-0.035840962	-0.017601019	0.013807159 	0.317189809       0.317189809
	0.750  3.699974783	1.451906978 	-0.236569074	0.912089726 	-1.438498599	0.220024018 	-0.173169830	0.251151933 	0.453943438 	0.544091863 	0.397252184 	-0.134566162	-0.285112292	-0.013681039	0.323760764 	-0.033542244	-0.019326810	0.013602553 	0.335909883       0.335909883
	0.800  3.629770810	1.554753136 	-0.198126136	0.928151630 	-1.422919183	0.210126551 	-0.136594833	0.212955586 	0.463780507 	0.539966113 	0.403015181 	-0.138274615	-0.264307149	 0.018347113	0.346247392 	-0.032902338	-0.023669678	0.011083027 	0.349543125       0.349543125
	0.900  3.491320204	1.592052928 	-0.213894691	0.955754021 	-1.392113699	0.196599527 	-0.114652231	0.195829720 	0.480054014 	0.512520632 	0.432487631 	-0.142349485	-0.250099799	 0.055934150	0.336348133 	-0.023246000	-0.030207068	0.003981517 	0.345256306       0.345256306  
	1.000  3.307539803	1.568356637 	-0.247674173	1.007603399 	-1.380004879	0.187422522 	-0.084545091	0.210348575 	0.475900594 	0.514415744 	0.429596031 	-0.147401558	-0.238364538	 0.084403299	0.356081130 	-0.026596250	-0.031598746	0.006429762 	0.343291125       0.343291125
	1.200  3.060218988	1.688588612 	-0.213362986	1.119125650 	-1.362384475	0.193785030 	-0.102869498	0.125258534 	0.504991413 	0.567820875 	0.440624244 	-0.154148223	-0.272127554	 0.065028709	0.359295137 	-0.033025741	-0.031987899	0.010415506 	0.377689939       0.377689939
	1.400  2.832088390	1.679116460 	-0.239058128	1.162157992 	-1.389237449	0.205421764 	-0.083389916	0.132870922 	0.566991168 	0.605670203 	0.458441655 	-0.163158566	-0.305084842	 0.033587249	0.404054652 	-0.039537746	-0.029609245	0.012395451 	0.402870109       0.402870109
	1.600  2.655372247	1.809640857 	-0.190643176	1.150347192 	-1.360998841	0.220353299 	-0.094786090	0.123220786 	0.606526913 	0.632047964 	0.469698872 	-0.179441032	-0.306270928	 0.070365276	0.444024570 	-0.048618284	-0.022659485	0.019182493 	0.457779680       0.457779680
	1.800  2.458381884	1.930202081 	-0.127317266	1.124371207 	-1.374785229	0.254286099 	-0.102752396	0.000000000     0.665499937 	0.663013931 	0.467985794 	-0.218232563	-0.397581377	 0.052905643	0.471012359 	-0.053963500	-0.042925106	0.013820060 	0.528942270       0.528942270
	2.000  2.274473663	1.935738181 	-0.137067347	1.140705006 	-1.374813519	0.265735034 	-0.103422742	0.000000000     0.644737161     0.650558294 	0.478833979 	-0.209641417	-0.370245575	 0.060170238	0.436473198 	-0.062150034	-0.043274609	0.016831583 	0.478901605       0.478901605
	2.500  1.694710885	1.878912863 	-0.164374552	1.247760553 	-1.374460539	0.267615179 	-0.068244045	0.000000000     0.558082593 	0.646723913 	0.488735266 	-0.156729509	-0.282543058	 0.037019362	0.388662307 	-0.040962475	-0.020747289	0.013624951 	0.388075329       0.388075329
	3.000  1.243030733	1.910844345 	-0.142240234	1.356314819 	-1.385365382	0.269329919 	-0.057480215	0.085136059 	0.475070018 	0.632662760  	0.483340266 	-0.105553589	-0.158197567	 0.076323781	0.306732911 	-0.015677386	-0.010704490	0.005300912 	0.303241361       0.303241361
	3.500  0.905608009	2.008031740 	-0.087330790    1.454356274 	-1.371191313	0.260644045 	-0.070146879	0.129473332	    0.432567454 	0.626298938 	0.486667367 	-0.084004241	-0.099719341	 0.101164535	0.240397080 	-0.009857112	-0.003023818	0.004796286 	0.262328788       0.262328788
	4.000  0.576942888	2.021337006 	-0.056207401	1.581350448 	-1.366605074	0.272272139 	-0.091093435	0.134808200	    0.421292418 	0.627364001 	0.490905275 	-0.075635647	-0.077376608	 0.107844542	0.243758525 	-0.009158219	-0.003644929	0.004772686 	0.264222979       0.264222979
	4.500  0.320518808	2.009482911 	-0.049551506	1.667192296 	-1.363668858	0.276399051 	-0.102064769	0.158631712	    0.392863961 	0.608746838 	0.501933666 	-0.064902877	-0.061913326	 0.096923619	0.210213383 	-0.009610153	-0.003423751	0.005311962 	0.216613697       0.216613697
	5.000  0.058032927	1.949350429 	-0.063093798	1.718605495 	-1.367935745	0.283721696 	-0.097178697	0.167041461	    0.370052436 	0.582303862 	0.514384506 	-0.057168575	-0.056945330	 0.078586156	0.207294398 	-0.006995935	-0.000866250	0.004278185 	0.209981271       0.209981271
	6.000 -0.348822721	1.905657864 	-0.055184431	1.765841476 	-1.391762914	0.300084448 	-0.072362480	0.162922973	    0.323827056 	0.560081726 	0.529422369 	-0.046738707	-0.057653602	 0.050269826	0.167269039 	-0.007766733	 0.005384207	0.007027485 	0.181089495       0.181089495
	7.000 -0.653969424	1.868810854 	-0.046156232	1.772562151 	-1.395432782	0.296975200 	-0.047777252	0.165452428	    0.289126431 	0.542196888 	0.538762301 	-0.037750587	-0.054672642	 0.031420684	0.133222761 	-0.006418497	 0.003028610	0.005690131 	0.145515468       0.145515468
	8.000 -0.919688851	1.793134289 	-0.063121770	1.736144037 	-1.421833345	0.299037297 	 0.000607773	0.166338780	    0.301051702 	0.537950694 	0.526970836 	-0.041042072	-0.056409474	 0.036270409	0.146513169 	-0.009084255	 0.003172789	0.006974785 	0.153331571       0.153331571
    """)

class MixcoEtAl2023regional(MixcoEtAl2023):
    """
    Adaptation of the Mixco et al. (2023) GMPE using the source and site
    specific adjustments.
    """
    experimental = True

    #: Required rupture parameters are magnitude, hypocentral location
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'hypo_lat', 'hypo_lon', 'hypo_depth'}

    #: Required site parameter are vs30, lat and lon of the site
    REQUIRES_SITES_PARAMETERS = {'vs30', 'lat', 'lon'}

    kind = "regional"

    def __init__(self, delta_l2l_epsilon=0.0, delta_c3_epsilon=0.0,
                 ergodic=True, c3=None, dl2l=None, **kwargs):
        """
        Instantiate setting the dl2l and c3 terms.
        """
        super().__init__(delta_l2l_epsilon=delta_l2l_epsilon,
                         delta_c3_epsilon=delta_c3_epsilon,
                         ergodic=ergodic, **kwargs)
        self.delta_l2l_epsilon = delta_l2l_epsilon
        self.delta_c3_epsilon = delta_c3_epsilon
        self.ergodic = ergodic
        attenuation_file = os.path.join(
            DATA_FOLDER, 'mixco_attenuation_regions.geojson') #TODO 
        self.att = np.array(fiona.open(attenuation_file), dtype=object)
        tectonic_file = os.path.join(
            DATA_FOLDER, 'mixco_tectonic_regions.geojson') #TODO
        self.tec = np.array(fiona.open(tectonic_file), dtype=object)


class MixcoEtAl2023Site(MixcoEtAl2023):
    """
    Adaptation of the Mixco et al. (2023) GMPE using a polynomial site
    amplification function dependent on Vs30 (m/s)
    """
    #: Required site parameter is not set
    REQUIRES_SITES_PARAMETERS = {"vs30"}

    kind = "site"


class MixcoEtAl2023Slope(MixcoEtAl2023):
    """
    Adaptation of the Mixco et al. (2023) GMPE using a polynomial site
    amplification function dependent on slope (m/m)
    """
    #: Required site parameter is not set
    REQUIRES_SITES_PARAMETERS = {"slope"}

    kind = "slope"