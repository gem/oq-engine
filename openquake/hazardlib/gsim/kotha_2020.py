# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2021 GEM Foundation
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
"""
import numpy as np
from scipy.constants import g
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA, from_string
from openquake.hazardlib.gsim.nga_east import (get_tau_at_quantile, ITPL,
                                               TAU_EXECUTION, TAU_SETUP)


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
    experimental = True

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
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    }

    #: Required site parameter is not set
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameters are magnitude and hypocentral depth
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'hypo_depth'}

    #: Required distance measure is Rjb (eq. 1).
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
                raise IOError("For Kotha et al. (2020) GMM, source-region "
                              "scaling parameter (dl2l) must be input in the "
                              "form of a dictionary, if specified")
            self.dl2l = {}
            for key in dl2l:
                self.dl2l[from_string(key)] = {"dl2l": dl2l[key]}
            self.dl2l = CoeffsTable(sa_damping=5, table=self.dl2l)
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
            self.c3 = CoeffsTable(sa_damping=5, table=self.c3)
        else:
            self.c3 = None

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extracting dictionary of coefficients specific to required
        # intensity measure type.
        C = self.COEFFS[imt]

        mean = (self.get_magnitude_scaling(C, rup.mag) +
                self.get_distance_term(C, rup, dists.rjb, imt, sites) +
                self.get_site_amplification(C, sites, imt))
        # GMPE originally in cm/s/s - convert to g
        if imt.name in "PGA SA":
            mean -= np.log(100.0 * g)
        stddevs = self.get_stddevs(C, dists.rjb.shape, stddev_types,
                                   sites, imt, rup.mag)
        if self.dl2l:
            # The source-region parameter is specified explicity
            return mean + self.dl2l[imt]["dl2l"], stddevs

        if self.sigma_mu_epsilon:
            # Apply the epistemic uncertainty factor (sigma_mu) multiplied by
            # the number of standard deviations
            sigma_mu = self.get_sigma_mu_adjustment(C, imt, rup)
            mean += (self.sigma_mu_epsilon * sigma_mu)
        return mean, stddevs

    @staticmethod
    def get_sigma_mu_adjustment(C, imt, rup):
        """
        Returns the sigma_mu adjusment factor, which is taken as the
        maximum of tau_L2L and the sigma_mu. For M < 7.4
        the sigma statistical does not exceed tau_L2L at any period or
        distance. For M > 7.4, sigma_mu is approximately linear up to M 8.0
        so we interpolate between the two values and cap sigma statistical
        at M 8.0
        """
        if rup.mag < 7.4:
            # Below M 7.4 tau_L2L is always larger than sigma mu
            return C["tau_l2l"]

        C_SIG_MU = SIGMA_MU_COEFFS[imt]
        if rup.hypo_depth < 10.0:
            uf, lf = C_SIG_MU["sigma_mu_m8_shallow"],\
                C_SIG_MU["sigma_mu_m7p4_shallow"]
        elif rup.hypo_depth >= 20.0:
            uf, lf = C_SIG_MU["sigma_mu_m8_deep"],\
                C_SIG_MU["sigma_mu_m7p4_deep"]
        else:
            uf, lf = C_SIG_MU["sigma_mu_m8_intermediate"],\
                C_SIG_MU["sigma_mu_m7p4_intermediate"]
        if rup.mag >= 8.0:
            # Cap the sigma mu as the value for M 8.0
            return max(C["tau_l2l"], uf)
        return max(C["tau_l2l"], ITPL(rup.mag, uf, lf, 7.4, 0.6))

    def get_magnitude_scaling(self, C, mag):
        """
        Returns the magnitude scaling term
        """
        d_m = mag - self.CONSTANTS["Mh"]
        if mag <= self.CONSTANTS["Mh"]:
            return C["e1"] + C["b1"] * d_m + C["b2"] * (d_m ** 2.0)
        else:
            return C["e1"] + C["b3"] * d_m

    def get_distance_term(self, C, rup, rjb, imt, sites):
        """
        Returns the distance attenuation factor
        """
        h = self._get_h(C, rup.hypo_depth)
        rval = np.sqrt(rjb ** 2. + h ** 2.)
        rref_val = np.sqrt(self.CONSTANTS["Rref"] ** 2. + h ** 2.)
        c3 = self.get_distance_coefficients(C, imt, sites)
        f_r = (C["c1"] + C["c2"] * (rup.mag - self.CONSTANTS["Mref"])) *\
            np.log(rval / rref_val) + (c3 * (rval - rref_val) / 100.)
        return f_r

    def _get_h(self, C, hypo_depth):
        """
        Returns the depth-specific coefficient
        """
        if hypo_depth <= 10.0:
            return self.CONSTANTS["h_D10"]
        elif hypo_depth > 20.0:
            return self.CONSTANTS["h_D20"]
        else:
            return self.CONSTANTS["h_10D20"]

    def get_distance_coefficients(self, C, imt, sctx):
        """
        Returns either the directly specified c3 value or the c3 from the
        existing tau_c3 distribution
        """
        if self.c3:
            # Use the c3 that has been defined on input
            return self.c3
        else:
            # Define the c3 as a number of standard deviation multiplied
            # by tau_c3
            return C["c3"] + (self.c3_epsilon * C["tau_c3"])

    def get_site_amplification(self, C, sites, imt):
        """
        In base model no site amplification is used
        """
        return 0.0

    def get_stddevs(self, C, stddev_shape, stddev_types, sites, imt, mag):
        """
        Returns the homoskedastic standard deviation model
        """
        stddevs = []
        tau = C["tau_event_0"]
        phi = C["phi_0"]
        if self.ergodic:
            phi = np.sqrt(phi ** 2. + C["phis2s"] ** 2.)
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(np.sqrt(tau ** 2. + phi ** 2.) +
                               np.zeros(stddev_shape))
            elif stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(phi + np.zeros(stddev_shape))
            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(tau + np.zeros(stddev_shape))
        return stddevs

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

    CONSTANTS = {"Mref": 4.5, "Rref": 30., "Mh": 5.7,
                 "h_D10": 4.0, "h_10D20": 8.0, "h_D20": 12.0}


class KothaEtAl2020Site(KothaEtAl2020):
    """
    Preliminary adaptation of the Kotha et al. (2020) GMPE using
    a polynomial site amplification function dependent on Vs30 (m/s)
    """
    #: Required site parameter is not set
    REQUIRES_SITES_PARAMETERS = set(("vs30",))

    def get_site_amplification(self, C, sites, imt):
        """
        Defines a second order polynomial site amplification model
        """
        # Render with respect to 800 m/s reference Vs30
        sref = np.log(sites.vs30 / 800.)
        return C["g0_vs30"] + C["g1_vs30"] * sref + C["g2_vs30"] * (sref ** 2.)

    def get_stddevs(self, C, stddev_shape, stddev_types, sites, imt, mag):
        """
        Returns the standard deviations
        """
        stddevs = []
        # Adopts homoskedastic tau and phi0 values
        tau = C["tau_event_0"]
        phi = C["phi_0"]
        if self.ergodic:
            phi = np.sqrt(phi ** 2.0 + C["phi_s2s_vs30"] ** 2.)
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(np.sqrt(tau ** 2. + phi ** 2.) +
                               np.zeros(stddev_shape))
            elif stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(phi + np.zeros(stddev_shape))
            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(tau + np.zeros(stddev_shape))
        return stddevs


class KothaEtAl2020Slope(KothaEtAl2020):
    """
    Preliminary adaptation of the Kotha et al. (2020) GMPE using
    a polynomial site amplification function dependent on slope (m/m)
    """
    #: Required site parameter is not set
    REQUIRES_SITES_PARAMETERS = set(("slope",))

    def get_site_amplification(self, C, sites, imt):
        """
        Defines a second order polynomial site amplification model
        """
        # Render with respect to 0.1 m/m reference slope
        sref = np.log(sites.slope / 0.1)
        return C["g0_slope"] + C["g1_slope"] * sref +\
            C["g2_slope"] * (sref ** 2.)

    def get_stddevs(self, C, stddev_shape, stddev_types, sites, imt, mag):
        """
        Returns the standard deviations
        """
        stddevs = []
        # Adopts homoskedastic tau and phi0 values
        tau = C["tau_event_0"]
        phi = C["phi_0"]
        if self.ergodic:
            phi = np.sqrt(phi ** 2. + C["phi_s2s_slope"] ** 2.)
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(np.sqrt(tau ** 2. + phi ** 2.) +
                               np.zeros(stddev_shape))
            elif stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(phi + np.zeros(stddev_shape))
            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(tau + np.zeros(stddev_shape))
        return stddevs


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
    if mag <= 5.0:
        phi = C["a"]
    elif mag > 6.5:
        phi = C["b"]
    else:
        phi = C["a"] + (mag - 5.0) * ((C["b"] - C["a"]) / 1.5)
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

    def get_distance_coefficients(self, C, imt, sctx):
        """
        Returns the c3 term. If c3 was input directly into the GMPE then
        this over-rides the c3 regionalisation. Otherwise the c3 and tau_c3
        are determined according to the region to which each site is assigned.

        Note that no regionalisation is defined for PGV and hence the
        default values from Kotha et al. (2020) are taken unless defined
        otherwise in the input c3
        """
        if self.c3:
            # If c3 is input then this over-rides the regionalisation
            # assumed within this model
            return self.c3[imt]["c3"] * np.ones(sctx.region.shape)

        # Default c3 and tau values to the original GMPE c3 and tau
        c3 = C["c3"] + np.zeros(sctx.region.shape)
        tau_c3 = C["tau_c3"] + np.zeros(sctx.region.shape)
        if not np.any(sctx.region) or ("PGV" in str(imt)):
            # No regionalisation - take the default C3 and multiply tau_c3
            # by the original epsilon
            return (c3 + self.c3_epsilon * tau_c3) +\
                np.zeros(sctx.region.shape)
        # Some sites belong to the calibrated regions - loop through them
        C3_R = C3_REGIONS[imt]
        for i in range(1, 6):
            idx = sctx.region == i
            c3[idx] = C3_R["region_{:s}".format(str(i))]
            tau_c3[idx] = C3_R["tau_region_{:s}".format(str(i))]
        return c3 + self.c3_epsilon * tau_c3

    def get_site_amplification(self, C, sites, imt):
        """
        Returns the linear site amplification term depending on whether the
        Vs30 is observed of inferred
        """
        vs30 = np.copy(sites.vs30)
        vs30[vs30 > 1100.] = 1100.
        ampl = np.zeros(vs30.shape)
        # For observed vs30 sites
        ampl[sites.vs30measured] = (C["d0_obs"] + C["d1_obs"] *
                                    np.log(vs30[sites.vs30measured]))
        # For inferred Vs30 sites
        idx = np.logical_not(sites.vs30measured)
        ampl[idx] = (C["d0_inf"] + C["d1_inf"] * np.log(vs30[idx]))
        return ampl

    def get_stddevs(self, C, stddev_shape, stddev_types, sites, imt, mag):
        """
        Returns the standard deviations, adopting different site-to-site
        standard deviations depending on whether the site has a measured
        or and inferred vs30. Relevant only in the ergodic case.
        """
        stddevs = []
        # Get the heteroskedastic tau and phi0
        tau = get_tau(imt, mag)
        phi = get_phi_ss(imt, mag)
        if self.ergodic:
            phi_s2s = np.zeros(sites.vs30measured.shape, dtype=float)
            phi_s2s[sites.vs30measured] += C["phi_s2s_obs"]
            phi_s2s[np.logical_not(sites.vs30measured)] += C["phi_s2s_inf"]
            phi = np.sqrt(phi ** 2. + phi_s2s ** 2.)
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(np.sqrt(tau ** 2. + phi ** 2.) +
                               np.zeros(stddev_shape))
            elif stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(phi + np.zeros(stddev_shape))
            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(tau + np.zeros(stddev_shape))
        return stddevs

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
    experimental = True

    #: Required site parameter is not set
    REQUIRES_SITES_PARAMETERS = set(("region", "slope", "geology"))

    #: Geological Units
    GEOLOGICAL_UNITS = [b"CENOZOIC", b"HOLOCENE", b"MESOZOIC",
                        b"PALEOZOIC", b"PLEISTOCENE", b"PRECAMBRIAN"]

    def get_site_amplification(self, C, sites, imt):
        """
        Returns the site amplification term depending on whether the Vs30
        is observed of inferred
        """
        C_AMP_FIXED = self.COEFFS_FIXED[imt]
        C_AMP_RAND_INT = self.COEFFS_RANDOM_INT[imt]
        C_AMP_RAND_GRAD = self.COEFFS_RANDOM_GRAD[imt]
        ampl = np.zeros(sites.slope.shape)
        geol_units = np.unique(sites.geology)
        t_slope = np.copy(sites.slope)
        t_slope[t_slope > 0.1] = 0.1
        # Slope lower than 0.003 m/m takes value for 0.003 m/m
        t_slope[t_slope < 0.003] = 0.003
        for geol_unit in geol_units:
            idx = sites.geology == geol_unit
            if geol_unit in self.GEOLOGICAL_UNITS:
                # Supported geological unit - use the random effects model
                v1 = C_AMP_FIXED["V1"] + C_AMP_RAND_INT[geol_unit.decode()]
                v2 = C_AMP_FIXED["V2"] + C_AMP_RAND_GRAD[geol_unit.decode()]
            else:
                # Unrecognised geological unit - use the fixed effects model
                v1 = C_AMP_FIXED["V1"]
                v2 = C_AMP_FIXED["V2"]
            ampl[idx] = v1 + v2 * np.log(t_slope[idx])
        return ampl

    def get_stddevs(self, C, stddev_shape, stddev_types, sites, imt, mag):
        """
        Returns the ergodic standard deviation with phi_s2s_inf based on
        that of the inferred Vs30
        """
        stddevs = []
        # Uses the heteroskedastic tau and phi0 values
        tau = get_tau(imt, mag)
        phi = get_phi_ss(imt, mag)
        if self.ergodic:
            phi = np.sqrt(phi ** 2. + C["phi_s2s_inf"] ** 2.)
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(np.sqrt(tau ** 2. + phi ** 2.) +
                               np.zeros(stddev_shape))
            elif stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(phi + np.zeros(stddev_shape))
            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(tau + np.zeros(stddev_shape))
        return stddevs

    COEFFS_FIXED = CoeffsTable(sa_damping=5, table="""\
    imt               V1            V2       phi_s2s
    pgv      -0.32324576   -0.12020038    0.44415954
    pga      -0.24052964   -0.08859926    0.53738151
    0.0100   -0.23496387   -0.08715414    0.54394999
    0.0250   -0.23196589   -0.08661428    0.54876737
    0.0400   -0.22535617   -0.08526151    0.56169098
    0.0500   -0.21757766   -0.08323442    0.57816019
    0.0700   -0.20912393   -0.08029556    0.59160446
    0.1000   -0.20286324   -0.07752007    0.59661642
    0.1500   -0.20514075   -0.07794259    0.59080123
    0.2000   -0.21897969   -0.08281367    0.57572994
    0.2500   -0.23988935   -0.08984659    0.55602436
    0.3000   -0.26279766   -0.09653115    0.53745164
    0.3500   -0.28656697   -0.10224154    0.52505924
    0.4000   -0.31242309   -0.10814091    0.51966661
    0.4500   -0.33932138   -0.11470673    0.51851135
    0.5000   -0.36157743   -0.11992917    0.51809718
    0.6000   -0.37322901   -0.12129274    0.51637748
    0.7000   -0.37482592   -0.11921264    0.51366508
    0.7500   -0.37269234   -0.11667676    0.51121047
    0.8000   -0.37172916   -0.11538592    0.50968262
    0.9000   -0.37321697   -0.11462760    0.50823033
    1.0000   -0.37739890   -0.11394194    0.50638971
    1.2000   -0.38373845   -0.11397761    0.50507607
    1.4000   -0.38999603   -0.11486428    0.50498282
    1.6000   -0.39463641   -0.11630257    0.50506741
    1.8000   -0.39631074   -0.11707146    0.50180099
    2.0000   -0.39140835   -0.11552992    0.49318368
    2.5000   -0.37673143   -0.11109489    0.48116716
    3.0000   -0.35487190   -0.10547313    0.46975649
    3.5000   -0.33384319   -0.10057926    0.46207401
    4.0000   -0.32304823   -0.09951507    0.45743459
    4.5000   -0.31998471   -0.10152963    0.45161269
    5.0000   -0.31008142   -0.09937151    0.44093475
    6.0000   -0.28784561   -0.09040942    0.42619444
    7.0000   -0.26367369   -0.07944937    0.41332844
    8.0000   -0.25325383   -0.07442950    0.40841495
    """)

    COEFFS_RANDOM_INT = CoeffsTable(sa_damping=5, table="""\
    imt      PRECAMBRIAN     PALEOZOIC      MESOZOIC      CENOZOIC   PLEISTOCENE     HOLOCENE
    pgv      -0.02283534   -0.08486729   -0.16622321   -0.03476549    0.13092937   0.17776196
    pga       0.01338856   -0.02141400   -0.07907828   -0.01820121    0.04742021   0.05788472
    0.0100    0.01691189   -0.01845777   -0.08272393   -0.02907664    0.05561945   0.05772700
    0.0250    0.01925469   -0.01838120   -0.09019813   -0.04172696    0.06799809   0.06305352
    0.0400    0.02436538   -0.01715826   -0.10414334   -0.06808891    0.09351454   0.07151059
    0.0500    0.03099936   -0.01495468   -0.11372221   -0.09205040    0.11725054   0.07247739
    0.0700    0.03588027   -0.01239313   -0.11202511   -0.09863914    0.12457889   0.06259823
    0.1000    0.03488640   -0.01000634   -0.10069725   -0.08227377    0.10957745   0.04851351
    0.1500    0.03036307   -0.01304422   -0.09585939   -0.06068337    0.09399392   0.04522999
    0.2000    0.02493699   -0.02526717   -0.10595539   -0.04905437    0.09626087   0.05907907
    0.2500    0.01654649   -0.04602618   -0.12328566   -0.04486642    0.11272881   0.08490295
    0.3000    0.00065978   -0.07015023   -0.13379157   -0.03383003    0.12455891   0.11255314
    0.3500   -0.02028025   -0.08792412   -0.12975387   -0.01334393    0.12181888   0.12948328
    0.4000   -0.04088380   -0.09872078   -0.11931215    0.00360637    0.11834936   0.13696100
    0.4500   -0.06139186   -0.10876043   -0.11078218    0.01398048    0.12238423   0.14456976
    0.5000   -0.07676442   -0.11707460   -0.10345753    0.02017138    0.12720917   0.14991601
    0.6000   -0.07948862   -0.11659076   -0.09402449    0.02260971    0.12435320   0.14314096
    0.7000   -0.07710283   -0.11068732   -0.08493075    0.02444830    0.11847777   0.12979484
    0.7500   -0.08028077   -0.10877532   -0.08267361    0.02690215    0.12008230   0.12474524
    0.8000   -0.08391929   -0.10639593   -0.08262138    0.02721720    0.12222717   0.12349224
    0.9000   -0.07655306   -0.09208434   -0.07304274    0.02365274    0.10928676   0.10874065
    1.0000   -0.05903508   -0.06808543   -0.05417703    0.01796115    0.08266130   0.08067509
    1.2000   -0.04319059   -0.04832949   -0.03767159    0.01290228    0.05954041   0.05674897
    1.4000   -0.03781835   -0.04103776   -0.03101518    0.00991471    0.05153967   0.04841691
    1.6000   -0.04175987   -0.04422212   -0.03289679    0.00876432    0.05667910   0.05343536
    1.8000   -0.04401104   -0.04669485   -0.03439678    0.00798956    0.06005260   0.05706051
    2.0000   -0.04197140   -0.04450708   -0.03244934    0.00626303    0.05738142   0.05528337
    2.5000   -0.03993140   -0.04159125   -0.03063888    0.00362879    0.05457192   0.05396081
    3.0000   -0.04267997   -0.04360611   -0.03515401    0.00043651    0.05974018   0.06126340
    3.5000   -0.04696179   -0.04865329   -0.04381117   -0.00242756    0.06899623   0.07285758
    4.0000   -0.05325955   -0.06393240   -0.06069315   -0.00736745    0.08763330   0.09761926
    4.5000   -0.06658953   -0.09344532   -0.08723316   -0.01357780    0.12082423   0.14002158
    5.0000   -0.07204152   -0.10837736   -0.09853129   -0.01440157    0.13541633   0.15793540
    6.0000   -0.06229663   -0.09413988   -0.08403012   -0.00848314    0.11589052   0.13305925
    7.0000   -0.04635655   -0.06644117   -0.05772413   -0.00002587    0.08110886   0.08943887
    8.0000   -0.03813182   -0.05223065   -0.04416795    0.00408566    0.06321014   0.06723461
    """)

    COEFFS_RANDOM_GRAD = CoeffsTable(sa_damping=5, table="""\
    imt      PRECAMBRIAN     PALEOZOIC      MESOZOIC      CENOZOIC    PLEISTOCENE      HOLOCENE
    pgv      -0.00171597   -0.00637738   -0.01249089   -0.00261246     0.00983872    0.01335797
    pga       0.00038434   -0.00061472   -0.00227007   -0.00052249     0.00136127    0.00166167
    0.0100    0.00143018   -0.00116093   -0.00622141   -0.00363208     0.00523011    0.00435412
    0.0250    0.00244167   -0.00176513   -0.01046921   -0.00713058     0.00956677    0.00735648
    0.0400    0.00466118   -0.00275928   -0.01906708   -0.01465463     0.01876932    0.01305050
    0.0500    0.00717444   -0.00323036   -0.02582969   -0.02175284     0.02731909    0.01631936
    0.0700    0.00857802   -0.00295771   -0.02628075   -0.02387137     0.02981087    0.01472095
    0.1000    0.00749769   -0.00216113   -0.02000512   -0.01892963     0.02381548    0.00978272
    0.1500    0.00508662   -0.00224647   -0.01378317   -0.01177504     0.01610138    0.00661668
    0.2000    0.00327310   -0.00365900   -0.01243770   -0.00755273     0.01306462    0.00731171
    0.2500    0.00246376   -0.00524524   -0.01375816   -0.00650537     0.01369457    0.00935044
    0.3000    0.00140878   -0.00554703   -0.01239145   -0.00499204     0.01222326    0.00929849
    0.3500    0.00075491   -0.00279639   -0.00601781   -0.00215149     0.00552927    0.00468152
    0.4000    0.00200374    0.00172241    0.00073362   -0.00099725    -0.00154393   -0.00191859
    0.4500    0.00388943    0.00546729    0.00481544   -0.00126289    -0.00593329   -0.00697598
    0.5000    0.00671673    0.01003641    0.00837280   -0.00214972    -0.01076459   -0.01221163
    0.6000    0.01248440    0.01836630    0.01391778   -0.00455237    -0.01932402   -0.02089208
    0.7000    0.01908932    0.02752836    0.02029137   -0.00731167    -0.02903059   -0.03056679
    0.7500    0.02350235    0.03225596    0.02406753   -0.00878449    -0.03496319   -0.03607817
    0.8000    0.02718169    0.03405760    0.02640578   -0.00932536    -0.03904657   -0.03927314
    0.9000    0.03374719    0.03934700    0.03130245   -0.01065803    -0.04730409   -0.04643451
    1.0000    0.04322961    0.04900481    0.03845172   -0.01314597    -0.05989743   -0.05764275
    1.2000    0.05192644    0.05744765    0.04393375   -0.01518622    -0.07111865   -0.06700296
    1.4000    0.05682959    0.06105913    0.04586554   -0.01542254    -0.07697374   -0.07135798
    1.6000    0.05751291    0.06079613    0.04517139   -0.01385441    -0.07772719   -0.07189884
    1.8000    0.05712618    0.06101547    0.04436394   -0.01193506    -0.07783350   -0.07273704
    2.0000    0.05737788    0.06210689    0.04408762   -0.01021997    -0.07864354   -0.07470887
    2.5000    0.05656952    0.06106920    0.04397844   -0.00771476    -0.07804900   -0.07585340
    3.0000    0.05167035    0.05517945    0.04290603   -0.00362528    -0.07286754   -0.07326301
    3.5000    0.04412177    0.04792440    0.04128141    0.00010328    -0.06525404   -0.06817683
    4.0000    0.03452469    0.03947164    0.03557267    0.00059728    -0.05343832   -0.05672796
    4.5000    0.02302706    0.02802272    0.02449246   -0.00149734    -0.03634321   -0.03770169
    5.0000    0.01697954    0.02236894    0.01839685   -0.00367703    -0.02724689   -0.02682141
    6.0000    0.01931773    0.02632893    0.02188040   -0.00422187    -0.03171695   -0.03158824
    7.0000    0.02589220    0.03540568    0.03002212   -0.00357645    -0.04296458   -0.04477898
    8.0000    0.02951666    0.04044110    0.03438328   -0.00319548    -0.04909299   -0.05205258
    """)
