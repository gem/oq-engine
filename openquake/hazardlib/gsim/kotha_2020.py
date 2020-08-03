# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2020 GEM Foundation
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
               :class:`KothaEtAl2020SERA`,
               :class:`KothaEtAl2020Site`,
               :class:`KothaEtAl2020Slope`,
               :class:`KothaEtAl2020SERASlopeGeology`
"""
import os
import h5py
import numpy as np
from scipy.constants import g
from scipy.interpolate import interp1d
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA, from_string
from openquake.hazardlib.gsim.nga_east import (get_tau_at_quantile,
                                               TAU_EXECUTION, TAU_SETUP)


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


BASE_PATH = os.path.join(os.path.dirname(__file__), "kotha_2020_tables")


class KothaEtAl2020(GMPE):
    """
    Implements the first complete version of the newly derived GMPE
    for Shallow Crustal regions using the Engineering Strong Motion Flatfile.

    (Working Title)
    Kotha, S. R., Weatherill, G., Bindi, D., Cotton F. (2020) A Regionally
    Adaptable Ground Motion Model for Shallow Crustal Earthquakes in
    Europe, Bulletin of Earthquake Engineering, under review

    The GMPE is desiged for calibration of the stress parameter term
    (a multiple of the fault-to-fault variability, tau_f) an attenuation
    scaling term (c3) and a statistical uncertainty term (sigma_mu). The
    statistical uncertainty is a scalar factor dependent on period, magnitude
    and distance. These are read in from hdf5 upon instantiation and
    interpolated to the necessary values.

    In the core form of the GMPE no site term is included. This will be
    added in the subclasses.

    :param c3:
        User supplied table for the coefficient c3 controlling the anelastic
        attenuation as an instance of :class:
        `openquake.hazardlib.gsim.base.CoeffsTable`. If absent, the value is
        taken from the normal coefficients table.

    :param sigma_mu_epsilon:
        The number by which to multiply the epistemic uncertainty (sigma_mu)
        for the adjustment of the mean ground motion.
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

    def __init__(self, sigma_mu_epsilon=0.0, c3=None, ergodic=True):
        """
        Instantiate setting the sigma_mu_epsilon and c3 terms
        """
        super().__init__()
        if isinstance(c3, dict):
            # Inputing c3 as a dictionary sorted by the string representation
            # of the IMT
            c3in = {}
            for c3key in c3:
                c3in[from_string(c3key)] = {"c3": c3[c3key]}
            self.c3 = CoeffsTable(sa_damping=5, table=c3in)
        else:
            self.c3 = c3

        self.sigma_mu_epsilon = sigma_mu_epsilon
        self.ergodic = ergodic
        if self.sigma_mu_epsilon:
            # Connect to hdf5 and load tables into memory
            self.retrieve_sigma_mu_data()
        else:
            # No adjustments, so skip this step
            self.mags = None
            self.dists = None
            self.s_a = None
            self.pga = None
            self.pgv = None
            self.periods = None

    def retrieve_sigma_mu_data(self):
        """
        For the general form of the GMPE this retrieves the sigma mu
        values from the hdf5 file using the "general" model, i.e. sigma mu
        factors that are independent of the choice of region or depth
        """
        fle = h5py.File(os.path.join(BASE_PATH,
                                     "KothaEtAl2020_SigmaMu_Fixed.hdf5"), "r")
        self.mags = fle["M"][:]
        self.dists = fle["R"][:]
        self.periods = fle["T"][:]
        self.pga = fle["PGA"][:]
        self.pgv = fle["PGV"][:]
        self.s_a = fle["SA"][:]
        fle.close()

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
                self.get_distance_term(C, rup, dists.rjb, imt) +
                self.get_site_amplification(C, sites, imt))
        # GMPE originally in cm/s/s - convert to g
        if imt.name in "PGA SA":
            mean -= np.log(100.0 * g)
        stddevs = self.get_stddevs(C, dists.rjb.shape, stddev_types,
                                   sites, imt, rup.mag)
        if self.sigma_mu_epsilon:
            # Apply the epistemic uncertainty factor (sigma_mu) multiplied by
            # the number of standard deviations
            sigma_mu = self.get_sigma_mu_adjustment(C, imt, rup, dists)
            # Cap sigma_mu at 0.5 ln units
            sigma_mu[sigma_mu > 0.5] = 0.5
            # Sigma mu should not be less than the standard deviation of the
            # fault-to-fault variability
            sigma_mu[sigma_mu < C["tau_l2l"]] = C["tau_l2l"]
            mean += (self.sigma_mu_epsilon * sigma_mu)
        return mean, stddevs

    def get_magnitude_scaling(self, C, mag):
        """
        Returns the magnitude scaling term
        """
        d_m = mag - self.CONSTANTS["Mh"]
        if mag <= self.CONSTANTS["Mh"]:
            return C["e1"] + C["b1"] * d_m + C["b2"] * (d_m ** 2.0)
        else:
            return C["e1"] + C["b3"] * d_m

    def get_distance_term(self, C, rup, rjb, imt):
        """
        Returns the distance attenuation factor
        """
        h = self._get_h(C, rup.hypo_depth)
        rval = np.sqrt(rjb ** 2. + h ** 2.)
        rref_val = np.sqrt(self.CONSTANTS["Rref"] ** 2. + h ** 2.)
        c3 = self.get_distance_coefficients(C, imt)

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

    def get_distance_coefficients(self, C, imt):
        """
        Returns the c3 term
        """
        c3 = self.c3[imt]["c3"] if self.c3 else C["c3"]
        return c3

    def get_site_amplification(self, C, sites, imt):
        """
        In base model no site amplification is used
        """
        return 0.0

    def get_sigma_mu_adjustment(self, C, imt, rup, dists):
        """
        Returns the sigma mu adjustment factor
        """
        if imt.name in "PGA PGV":
            # PGA and PGV are 2D arrays of dimension [nmags, ndists]
            sigma_mu = getattr(self, imt.name.lower())
            if rup.mag <= self.mags[0]:
                sigma_mu_m = sigma_mu[0, :]
            elif rup.mag >= self.mags[-1]:
                sigma_mu_m = sigma_mu[-1, :]
            else:
                intpl1 = interp1d(self.mags, sigma_mu, axis=0)
                sigma_mu_m = intpl1(rup.mag)
            # Linear interpolation with distance
            intpl2 = interp1d(self.dists, sigma_mu_m, bounds_error=False,
                              fill_value=(sigma_mu_m[0], sigma_mu_m[-1]))
            return intpl2(dists.rjb)
        # In the case of SA the array is of dimension [nmags, ndists, nperiods]
        # Get values for given magnitude
        if rup.mag <= self.mags[0]:
            sigma_mu_m = self.s_a[0, :, :]
        elif rup.mag >= self.mags[-1]:
            sigma_mu_m = self.s_a[-1, :, :]
        else:
            intpl1 = interp1d(self.mags, self.s_a, axis=0)
            sigma_mu_m = intpl1(rup.mag)
        # Get values for period - N.B. ln T, linear sigma mu interpolation
        if imt.period <= self.periods[0]:
            sigma_mu_t = sigma_mu_m[:, 0]
        elif imt.period >= self.periods[-1]:
            sigma_mu_t = sigma_mu_m[:, -1]
        else:
            intpl2 = interp1d(np.log(self.periods), sigma_mu_m, axis=1)
            sigma_mu_t = intpl2(np.log(imt.period))
        intpl3 = interp1d(self.dists, sigma_mu_t, bounds_error=False,
                          fill_value=(sigma_mu_t[0], sigma_mu_t[-1]))
        return intpl3(dists.rjb)

    def get_stddevs(self, C, stddev_shape, stddev_types, sites, imt, mag):
        """
        Returns the standard deviations
        """
        stddevs = []
        tau = get_tau(imt, mag)
        phi = get_phi_ss(imt, mag)
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

    COEFFS = CoeffsTable(sa_damping=5, table="""\
    imt                 e1               b1               b2                b3                c1               c2                c3           tau_c3           phis2s        tau_event          tau_l2l             phi0              g0_vs30              g1_vs30              g2_vs30        phi_s2s_vs30             g0_slope             g1_slope             g2_slope       phi_s2s_slope
    pgv     1.986297847767   2.278515925276   0.172184178053    0.299544503900   -1.419871787778   0.270864702674   -0.303453527552   0.179928856360   0.560214787771   0.430621988652   0.279217449810   0.446536749421   -0.231077354280506   -0.493957951802596    0.024957396415867   0.365614160325143   -0.055278165876675   -0.146520388963317   -0.008584052062615   0.433946476723565
    pga     4.593600817502   1.806328676733   0.144764965899   -0.187664517098   -1.498595099847   0.281454363399   -0.608840589420   0.254501921365   0.606285802404   0.449637491699   0.368682450293   0.467191048339   -0.220611183943551   -0.561602687510659   -0.133980848644021   0.388263986170585   -0.027081220086203   -0.109683817165521   -0.017167709027252   0.507083778984519
    0.010   4.595831841359   1.805720064378   0.145203067800   -0.187853401989   -1.500785325936   0.281826029391   -0.607836921386   0.254473840849   0.606540945437   0.449511849989   0.369530025591   0.467246778966   -0.220407105515350   -0.560739244518243   -0.133822566324568   0.391294103015453   -0.027029303894035   -0.109518851675393   -0.017164529064930   0.507647182479991
    0.025   4.625178798002   1.794292615521   0.150033923813   -0.187172831518   -1.544504636982   0.283200216216   -0.572198448811   0.253266193047   0.609478297455   0.445517217217   0.383781890123   0.468739331200   -0.217234656391890   -0.549669366194560   -0.132422097361002   0.394393060441682   -0.025736227212091   -0.107098982191857   -0.017425516876989   0.507034880250357
    0.040   4.722447583759   1.761676216451   0.163644691708   -0.199095303420   -1.637542321107   0.298686311412   -0.534112656153   0.245054022905   0.625714780107   0.437333696331   0.430292749853   0.473766331531   -0.205567556225473   -0.528777395378919   -0.138287921055099   0.412491306427046   -0.022557806807548   -0.102370504214299   -0.018294397899200   0.516450416080127
    0.050   4.804502449486   1.739937888686   0.170300151677   -0.219411777440   -1.664377529574   0.312428747006   -0.554344743057   0.260199667680   0.638254309793   0.441516738857   0.460524334450   0.479945223969   -0.204312873549905   -0.518186607805250   -0.138039287961884   0.419111467695475   -0.021269844261771   -0.098897830859855   -0.018326112585389   0.524530960968232
    0.070   4.991633222166   1.706553346455   0.168745580437   -0.213340469096   -1.644248691403   0.314012606725   -0.640526595472   0.286956317682   0.660284949711   0.452277718801   0.482487985372   0.487092836506   -0.207611889061548   -0.509564047493291   -0.146589159457830   0.440054072401786   -0.019170291863061   -0.095115940396699   -0.018653750469469   0.550500261235956
    0.100   5.216725999474   1.685519997832   0.153695785712   -0.204807294178   -1.544031349660   0.285148522630   -0.743396259134   0.322309553915   0.662735917380   0.465579412757   0.480973092170   0.496181528747   -0.192931726444399   -0.525578768052468   -0.183495608072230   0.446080480049729   -0.016813836872792   -0.087261228811468   -0.016604164803633   0.539340788770085
    0.150   5.409547877051   1.678363948934   0.108964259966   -0.189890325563   -1.381902206554   0.225689831260   -0.815043098860   0.322007237429   0.654720113336   0.466509140156   0.417460279625   0.497838049779   -0.214194229924967   -0.581529840384920   -0.201990736791951   0.455358185254245   -0.015554158630302   -0.089810009587356   -0.018014820777837   0.547775377589848
    0.200   5.453890202270   1.689438303007   0.076992089883   -0.153502646971   -1.307510701800   0.182940816317   -0.772880020737   0.301572220795   0.643153063650   0.470050836760   0.324515411666   0.494091741457   -0.231483359554058   -0.648018888888013   -0.210851713462973   0.443009935904118   -0.018874082314837   -0.109048616846721   -0.021794841049725   0.538783067860204
    0.250   5.411971846531   1.719357494611   0.056936402466   -0.096882602431   -1.263089491625   0.155409119964   -0.721417443819   0.274901019805   0.622862866230   0.463722804830   0.298346506228   0.488946620721   -0.237412839274978   -0.650666391566593   -0.196891703508675   0.446042945916869   -0.027143094075199   -0.117484624734672   -0.019626975376044   0.518516643420853
    0.300   5.339975712573   1.786378891274   0.053245731458   -0.098663301545   -1.241241570029   0.137235308693   -0.659797998230   0.261180806047   0.609434612997   0.462823521005   0.275386022961   0.482173998888   -0.244503716196265   -0.647386909849244   -0.172606826076631   0.428275840618894   -0.035831384061132   -0.126401303626803   -0.017092719333357   0.491028529060573
    0.350   5.245031598707   1.831650711430   0.048429888707   -0.035148822891   -1.215628172562   0.124916267250   -0.617942668472   0.254737453226   0.609391922679   0.456749384828   0.243074261426   0.480246325971   -0.252605292409522   -0.649894292484875   -0.144640406078841   0.401274800895868   -0.042424065056186   -0.139968511173383   -0.016555040218554   0.490358839320492
    0.400   5.172478034239   1.895942168737   0.049858426143   -0.039080879414   -1.189517733110   0.115875870187   -0.590763475754   0.244367107710   0.615351146488   0.448758077757   0.255382872509   0.475149460687   -0.261700878877309   -0.655928988832784   -0.119230958425086   0.434044180231674   -0.045474518987588   -0.151112200510891   -0.017477486312685   0.500359399676765
    0.450   5.084466738157   1.944571514150   0.051712882438   -0.031025330564   -1.180661600660   0.110338135521   -0.554433746532   0.246565073080   0.619024594684   0.444336103250   0.264492801723   0.469668176199   -0.262803686082410   -0.641283423740159   -0.084382501664206   0.416693133040647   -0.054504155894867   -0.158433972667347   -0.014699759226245   0.495927448757934
    0.500   4.997951964959   1.990170872429   0.052104332867   -0.004593285736   -1.177723569167   0.102936390188   -0.518700657967   0.239580664585   0.624726936080   0.436707512229   0.258906103862   0.463184820845   -0.267494200696851   -0.628224179998946   -0.053616926922775   0.420229918007586   -0.061221630697767   -0.164317325803277   -0.012703360059700   0.496200883437177
    0.600   4.821460385119   2.063102481959   0.052488866603    0.117270851639   -1.167185092157   0.094270555357   -0.453602302389   0.217919431330   0.634947226995   0.433297884320   0.265768656453   0.451229616810   -0.268140357369656   -0.585435859294930    0.020153665466998   0.475689455824438   -0.068503431096073   -0.172692448118099   -0.009221760971171   0.506289325583946
    0.700   4.650874453016   2.126986704093   0.051778511140    0.120976499985   -1.162794994152   0.086764496441   -0.397369836147   0.216884654674   0.633121909658   0.432670860724   0.274180569758   0.446717273621   -0.271077817298483   -0.559883392128881    0.066291539266807   0.453944172029534   -0.074233094656159   -0.173564996429183   -0.005262341801681   0.505704006971710
    0.750   4.580870529797   2.166636035270   0.054444522760    0.159198932290   -1.153741511196   0.082709852357   -0.376202497137   0.211017683167   0.637549459649   0.435994625372   0.273343997189   0.444283762342   -0.266529681492224   -0.547373596925130    0.085239196755405   0.462108057803813   -0.074496812667098   -0.175360565960122   -0.005433771452332   0.512554147992876
    0.800   4.497603764971   2.195468114219   0.055851944127    0.214945824678   -1.146853808225   0.083957213881   -0.362739820962   0.193658451006   0.638406037308   0.441665448007   0.269316725748   0.439302983387   -0.266033533484732   -0.530796360150866    0.105834564490773   0.474270662756106   -0.073279829544726   -0.176647564649954   -0.005983980615392   0.517658386603091
    0.900   4.372780254749   2.259226501052   0.057725868653    0.243584010275   -1.136554168196   0.083559304602   -0.333308869969   0.179232974308   0.640053399804   0.448275692043   0.273544894553   0.433011855491   -0.268925198150758   -0.501872457621322    0.152434105046546   0.489795918410426   -0.070521299078690   -0.184005561252889   -0.009231460997641   0.507049772283348
    1.000   4.255539415762   2.314814900323   0.061598261165    0.288848394594   -1.124817963757   0.085698397408   -0.316824095141   0.174173178526   0.638043742056   0.453370642316   0.262695165808   0.426660877769   -0.266466719108452   -0.474442250837531    0.191902161843052   0.491598121148994   -0.073147366886850   -0.185515681790388   -0.007928703582317   0.500036528398695
    1.200   4.038599595326   2.413732093230   0.069991626760    0.369266408381   -1.121368599080   0.097564258606   -0.274783316235   0.163249277591   0.639395647808   0.453417592399   0.257117589119   0.416472588508   -0.261741301653183   -0.468173010057581    0.200978818815827   0.471578598976065   -0.076292565963820   -0.191718200439291   -0.007557022853542   0.492320424017099
    1.400   3.815947355550   2.479964334173   0.074509347805    0.445566078826   -1.128767790619   0.100523683037   -0.234349930531   0.153501938280   0.648910293044   0.466113494834   0.263334123938   0.409571407808   -0.250997358470485   -0.452375748174702    0.190624868046166   0.511099586454834   -0.077864783321444   -0.197122651270617   -0.006543983160426   0.520938940378748
    1.600   3.631646560196   2.559663313300   0.085101029487    0.460566449431   -1.140937389837   0.110319345222   -0.197546621568   0.150851270249   0.649738124629   0.472690014103   0.252120577182   0.404939609587   -0.244724645158367   -0.427750364224493    0.203275743351652   0.492840049391064   -0.081042659716350   -0.194753676316974   -0.003693171578408   0.524314148903611
    1.800   3.459724392382   2.650290580770   0.107675261134    0.455981136562   -1.154459813177   0.113516198465   -0.166778722563   0.157733949899   0.655942138094   0.477315304326   0.238457136523   0.399046345798   -0.257358042672462   -0.436347731484410    0.211718085815373   0.496454897044341   -0.086932115618659   -0.195828543984984    0.001334265249543   0.521682867835024
    2.000   3.289052190839   2.690118527117   0.112598356463    0.489296858106   -1.166418273993   0.116678434812   -0.140417710429   0.156493287404   0.646925330835   0.486249114926   0.231543933787   0.396483198980   -0.253887092682547   -0.426848881500208    0.208441482263887   0.474445846977249   -0.088488159102521   -0.197216098829870    0.002328159410275   0.507490959577411
    2.500   2.936473383149   2.857769625873   0.160897057712    0.545092895748   -1.175520686035   0.139980229243   -0.120374488710   0.178207969780   0.628898821285   0.488212793617   0.215164835150   0.393293172095   -0.255954981716856   -0.397304297599626    0.213653670092794   0.451934655437954   -0.084752948744130   -0.190531648835506    0.001786278769957   0.500971872354277
    3.000   2.772015641952   3.103623207489   0.227949145568    0.607228251145   -1.156752134438   0.150053019616   -0.148534265023   0.175955415496   0.615630529159   0.497280231565   0.229320445467   0.390850272410   -0.250805121199420   -0.368462110456447    0.213829341094000   0.417865051347770   -0.078347578064021   -0.184038495872259   -0.000328331875429   0.486409406127982
    3.500   2.550306389498   3.234115206129   0.275697742205    0.704199586033   -1.163732516411   0.154956829284   -0.142560085634   0.192759182459   0.599224713100   0.489117033253   0.247687790856   0.388075167947   -0.241010333806051   -0.325538649156754    0.214824460474638   0.401528691091061   -0.078358061998557   -0.171600067705098    0.002253014011067   0.482809801537462
    4.000   2.352929414968   3.310357136230   0.300931330210    0.729865592495   -1.177718479274   0.173699671898   -0.141789103905   0.192905670114   0.591874392925   0.493886994741   0.247444911315   0.386955162338   -0.237440863136386   -0.296727854846452    0.227451558534291   0.391576245308447   -0.076116438798639   -0.164516343183801    0.002924897294648   0.475839146102743
    4.500   2.339517782000   3.464574018363   0.362671054888    0.775124154936   -1.172989084907   0.194344947085   -0.155260019763   0.154450733985   0.580249366526   0.467632240734   0.222127895033   0.372830297647   -0.245285606381372   -0.248426599869749    0.246971516699644   0.392529514611620   -0.066396835970665   -0.173899175092314   -0.005544686845989   0.472037440632925
    5.000   2.125081971333   3.513252751909   0.382599171515    0.861508135975   -1.209544942675   0.221973829002   -0.125368353163   0.139412564761   0.557973798141   0.475772516421   0.220292403287   0.377432067281   -0.232148132971693   -0.217363330154369    0.231488972422077   0.352724652422622   -0.061388115977658   -0.163999607690241   -0.006787304301947   0.447841024453769
    6.000   1.789669612797   3.467032240903   0.390672960654    1.071637690955   -1.224759159711   0.230159180846   -0.112670397633   0.144727555167   0.537858947825   0.449550499950   0.211281351794   0.384943159783   -0.203366115104074   -0.172388588991144    0.216955944441405   0.339638377577193   -0.056513309760614   -0.152056358419027   -0.005859253152988   0.439633129906047
    7.000   1.486846474799   3.474332494304   0.408363526227    1.227180966945   -1.285471191423   0.260498715762   -0.069644614376   0.148649539627   0.522468807073   0.444894957763   0.234268694156   0.385888378683   -0.203227850072267   -0.160800461123655    0.215058518716830   0.331405036821493   -0.053809564599965   -0.139582550281575   -0.004508132242376   0.432518975385726
    8.000   1.186154376927   3.447858314030   0.418038426054    1.258318646654   -1.329185530776   0.285751511968   -0.050512729714   0.152958209816   0.507682898129   0.440122399653   0.246895677579   0.387676375770   -0.193425426029436   -0.153079085712522    0.209345832047528   0.332011646534902   -0.050524974867254   -0.136743999821539   -0.005424899352572   0.409504428895680
    """)

    CONSTANTS = {"Mref": 4.5, "Rref": 30., "Mh": 6.2,
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
        tau = get_tau(imt, mag)
        phi = get_phi_ss(imt, mag)
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
        tau = get_tau(imt, mag)
        phi = get_phi_ss(imt, mag)
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


class KothaEtAl2020SERA(KothaEtAl2020):
    """
    Implementation of the Kotha et al. (2020) GMPE with the site
    amplification components included using a two-segment piecewise
    linear function. This form of the GMPE defines the
    site in terms of a measured or inferred Vs30, with the total
    aleatory variability adjusted accordingly.
    """

    #: Required site parameter is not set
    REQUIRES_SITES_PARAMETERS = set(("vs30", "vs30measured"))

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
    imt                 e1               b1               b2                b3                c1               c2                c3           tau_c3           phis2s        tau_event          tau_l2l             phi0        d0_obs        d1_obs   phi_s2s_obs       d0_inf        d1_inf   phi_s2s_inf
    pgv     1.986297847767   2.278515925276   0.172184178053    0.299544503900   -1.419871787778   0.270864702674   -0.303453527552   0.179928856360   0.560214787771   0.430621988652   0.279217449810   0.446536749421    3.30975201   -0.53326451    0.36257068   2.78401517   -0.43790954    0.42677529
    pga     4.593600817502   1.806328676733   0.144764965899   -0.187664517098   -1.498595099847   0.281454363399   -0.608840589420   0.254501921365   0.606285802404   0.449637491699   0.368682450293   0.467191048339    2.65261454   -0.43301831    0.38806156   1.88258216   -0.29656277    0.51606938
    0.010   4.595831841359   1.805720064378   0.145203067800   -0.187853401989   -1.500785325936   0.281826029391   -0.607836921386   0.254473840849   0.606540945437   0.449511849989   0.369530025591   0.467246778966    2.56961762   -0.41981270    0.40044760   1.82057082   -0.28687880    0.51867018
    0.025   4.625178798002   1.794292615521   0.150033923813   -0.187172831518   -1.544504636982   0.283200216216   -0.572198448811   0.253266193047   0.609478297455   0.445517217217   0.383781890123   0.468739331200    2.52820436   -0.41328371    0.40623719   1.79206766   -0.28244435    0.52160624
    0.040   4.722447583759   1.761676216451   0.163644691708   -0.199095303420   -1.637542321107   0.298686311412   -0.534112656153   0.245054022905   0.625714780107   0.437333696331   0.430292749853   0.473766331531    2.42784360   -0.39762162    0.41977221   1.72300482   -0.27169228    0.53093819
    0.050   4.804502449486   1.739937888686   0.170300151677   -0.219411777440   -1.664377529574   0.312428747006   -0.554344743057   0.260199667680   0.638254309793   0.441516738857   0.460524334450   0.479945223969    2.30956730   -0.37937894    0.43465421   1.64224336   -0.25906654    0.54404664
    0.070   4.991633222166   1.706553346455   0.168745580437   -0.213340469096   -1.644248691403   0.314012606725   -0.640526595472   0.286956317682   0.660284949711   0.452277718801   0.482487985372   0.487092836506    2.21859665   -0.36551691    0.44921838   1.56920377   -0.24754055    0.55532276
    0.100   5.216725999474   1.685519997832   0.153695785712   -0.204807294178   -1.544031349660   0.285148522630   -0.743396259134   0.322309553915   0.662735917380   0.465579412757   0.480973092170   0.496181528747    2.22143266   -0.36624939    0.46432610   1.53915732   -0.24268225    0.56118134
    0.150   5.409547877051   1.678363948934   0.108964259966   -0.189890325563   -1.381902206554   0.225689831260   -0.815043098860   0.322007237429   0.654720113336   0.466509140156   0.417460279625   0.497838049779    2.35118737   -0.38662423    0.47703588   1.59963888   -0.25206957    0.55911690
    0.200   5.453890202270   1.689438303007   0.076992089883   -0.153502646971   -1.307510701800   0.182940816317   -0.772880020737   0.301572220795   0.643153063650   0.470050836760   0.324515411666   0.494091741457    2.55240529   -0.41806691    0.48025344   1.75423282   -0.27634242    0.54824186
    0.250   5.411971846531   1.719357494611   0.056936402466   -0.096882602431   -1.263089491625   0.155409119964   -0.721417443819   0.274901019805   0.622862866230   0.463722804830   0.298346506228   0.488946620721    2.74904047   -0.44882046    0.46891833   1.96527860   -0.30954933    0.53109975
    0.300   5.339975712573   1.786378891274   0.053245731458   -0.098663301545   -1.241241570029   0.137235308693   -0.659797998230   0.261180806047   0.609434612997   0.462823521005   0.275386022961   0.482173998888    2.93212957   -0.47759683    0.44983953   2.19913556   -0.34634476    0.51454301
    0.350   5.245031598707   1.831650711430   0.048429888707   -0.035148822891   -1.215628172562   0.124916267250   -0.617942668472   0.254737453226   0.609391922679   0.456749384828   0.243074261426   0.480246325971    3.12993498   -0.50873128    0.43569377   2.44212272   -0.38459154    0.50459028
    0.400   5.172478034239   1.895942168737   0.049858426143   -0.039080879414   -1.189517733110   0.115875870187   -0.590763475754   0.244367107710   0.615351146488   0.448758077757   0.255382872509   0.475149460687    3.33033435   -0.54013326    0.43045602   2.67707249   -0.42163058    0.50107926
    0.450   5.084466738157   1.944571514150   0.051712882438   -0.031025330564   -1.180661600660   0.110338135521   -0.554433746532   0.246565073080   0.619024594684   0.444336103250   0.264492801723   0.469668176199    3.50290267   -0.56696060    0.43223316   2.88578405   -0.45456492    0.50146998
    0.500   4.997951964959   1.990170872429   0.052104332867   -0.004593285736   -1.177723569167   0.102936390188   -0.518700657967   0.239580664585   0.624726936080   0.436707512229   0.258906103862   0.463184820845    3.65227902   -0.58990263    0.43887979   3.06576841   -0.48290522    0.50314566
    0.600   4.821460385119   2.063102481959   0.052488866603    0.117270851639   -1.167185092157   0.094270555357   -0.453602302389   0.217919431330   0.634947226995   0.433297884320   0.265768656453   0.451229616810    3.78937389   -0.61070144    0.44724118   3.20894580   -0.50535303    0.50313816
    0.700   4.650874453016   2.126986704093   0.051778511140    0.120976499985   -1.162794994152   0.086764496441   -0.397369836147   0.216884654674   0.633121909658   0.432670860724   0.274180569758   0.446717273621    3.90172707   -0.62754331    0.45268279   3.29999705   -0.51955858    0.50200072
    0.750   4.580870529797   2.166636035270   0.054444522760    0.159198932290   -1.153741511196   0.082709852357   -0.376202497137   0.211017683167   0.637549459649   0.435994625372   0.273343997189   0.444283762342    3.97560847   -0.63847685    0.45583313   3.34616641   -0.52673049    0.50236259
    0.800   4.497603764971   2.195468114219   0.055851944127    0.214945824678   -1.146853808225   0.083957213881   -0.362739820962   0.193658451006   0.638406037308   0.441665448007   0.269316725748   0.439302983387    4.01969394   -0.64478309    0.46384687   3.37966751   -0.53196741    0.50266660
    0.900   4.372780254749   2.259226501052   0.057725868653    0.243584010275   -1.136554168196   0.083559304602   -0.333308869969   0.179232974308   0.640053399804   0.448275692043   0.273544894553   0.433011855491    4.05410191   -0.64939631    0.47448247   3.42678904   -0.53940883    0.49912472
    1.000   4.255539415762   2.314814900323   0.061598261165    0.288848394594   -1.124817963757   0.085698397408   -0.316824095141   0.174173178526   0.638043742056   0.453370642316   0.262695165808   0.426660877769    4.07365692   -0.65153510    0.48134887   3.49473194   -0.55015995    0.49404787
    1.200   4.038599595326   2.413732093230   0.069991626760    0.369266408381   -1.121368599080   0.097564258606   -0.274783316235   0.163249277591   0.639395647808   0.453417592399   0.257117589119   0.416472588508    4.05048971   -0.64704214    0.48708350   3.57270165   -0.56244631    0.49375397
    1.400   3.815947355550   2.479964334173   0.074509347805    0.445566078826   -1.128767790619   0.100523683037   -0.234349930531   0.153501938280   0.648910293044   0.466113494834   0.263334123938   0.409571407808    3.99349305   -0.63756820    0.49596280   3.64615783   -0.57391983    0.49885402
    1.600   3.631646560196   2.559663313300   0.085101029487    0.460566449431   -1.140937389837   0.110319345222   -0.197546621568   0.150851270249   0.649738124629   0.472690014103   0.252120577182   0.404939609587    3.94048869   -0.62914699    0.50237219   3.70614492   -0.58319956    0.50427003
    1.800   3.459724392382   2.650290580770   0.107675261134    0.455981136562   -1.154459813177   0.113516198465   -0.166778722563   0.157733949899   0.655942138094   0.477315304326   0.238457136523   0.399046345798    3.90126474   -0.62332928    0.49599967   3.73733460   -0.58797931    0.50406486
    2.000   3.289052190839   2.690118527117   0.112598356463    0.489296858106   -1.166418273993   0.116678434812   -0.140417710429   0.156493287404   0.646925330835   0.486249114926   0.231543933787   0.396483198980    3.84084468   -0.61459972    0.47661567   3.71781492   -0.58487198    0.49679447
    2.500   2.936473383149   2.857769625873   0.160897057712    0.545092895748   -1.175520686035   0.139980229243   -0.120374488710   0.178207969780   0.628898821285   0.488212793617   0.215164835150   0.393293172095    3.71684077   -0.59605682    0.44991701   3.63149526   -0.57133201    0.48588889
    3.000   2.772015641952   3.103623207489   0.227949145568    0.607228251145   -1.156752134438   0.150053019616   -0.148534265023   0.175955415496   0.615630529159   0.497280231565   0.229320445467   0.390850272410    3.54176439   -0.56936072    0.42220113   3.49013277   -0.54916732    0.47625314
    3.500   2.550306389498   3.234115206129   0.275697742205    0.704199586033   -1.163732516411   0.154956829284   -0.142560085634   0.192759182459   0.599224713100   0.489117033253   0.247687790856   0.388075167947    3.34546112   -0.53906501    0.39951709   3.34520093   -0.52645323    0.47012445
    4.000   2.352929414968   3.310357136230   0.300931330210    0.729865592495   -1.177718479274   0.173699671898   -0.141789103905   0.192905670114   0.591874392925   0.493886994741   0.247444911315   0.386955162338    3.13392178   -0.50620694    0.38303088   3.23169516   -0.50870031    0.46555128
    4.500   2.339517782000   3.464574018363   0.362671054888    0.775124154936   -1.172989084907   0.194344947085   -0.155260019763   0.154450733985   0.580249366526   0.467632240734   0.222127895033   0.372830297647    2.90740942   -0.47082887    0.36840706   3.13020974   -0.49278809    0.46035806
    5.000   2.125081971333   3.513252751909   0.382599171515    0.861508135975   -1.209544942675   0.221973829002   -0.125368353163   0.139412564761   0.557973798141   0.475772516421   0.220292403287   0.377432067281    2.68344324   -0.43562070    0.35254196   2.99932475   -0.47213713    0.45347349
    6.000   1.789669612797   3.467032240903   0.390672960654    1.071637690955   -1.224759159711   0.230159180846   -0.112670397633   0.144727555167   0.537858947825   0.449550499950   0.211281351794   0.384943159783    2.50354874   -0.40714992    0.33854229   2.83412987   -0.44598168    0.44328149
    7.000   1.486846474799   3.474332494304   0.408363526227    1.227180966945   -1.285471191423   0.260498715762   -0.069644614376   0.148649539627   0.522468807073   0.444894957763   0.234268694156   0.385888378683    2.39499327   -0.38989994    0.33074643   2.69365804   -0.42370171    0.43214765
    8.000   1.186154376927   3.447858314030   0.418038426054    1.258318646654   -1.329185530776   0.285751511968   -0.050512729714   0.152958209816   0.507682898129   0.440122399653   0.246895677579   0.387676375770    2.35979253   -0.38432385    0.32874669   2.64017872   -0.41521615    0.42722298
    """)


class KothaEtAl2020SERASlopeGeology(KothaEtAl2020SERA):
    """
    Adaptation of the Kotha et al. (2020) GMPE for use with slope and geology
    in place of inferred/measured Vs30.
    """
    experimental = True

    #: Required site parameter is not set
    REQUIRES_SITES_PARAMETERS = set(("slope", "geology"))

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
