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
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        PGV,
        SA
    ])

    #: Supported intensity measure component is the geometric mean of two
    #: horizontal components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    #: Supported standard deviation types are inter-event, intra-event
    #: and total
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    ])

    #: Required site parameter is not set
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameters are magnitude and hypocentral depth
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', 'hypo_depth'))

    #: Required distance measure is Rjb (eq. 1).
    REQUIRES_DISTANCES = set(('rjb', ))

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
            self.retreive_sigma_mu_data()
        else:
            # No adjustments, so skip this step
            self.mags = None
            self.dists = None
            self.s_a = None
            self.pga = None
            self.pgv = None
            self.periods = None

    def retreive_sigma_mu_data(self):
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
        stddevs = self.get_stddevs(C, dists.rjb.shape, stddev_types, sites)
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

    def get_stddevs(self, C, stddev_shape, stddev_types, sites):
        """
        Returns the standard deviations
        """
        stddevs = []
        tau = C["tau_event"]
        phi = C["phi0"]
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

    def get_stddevs(self, C, stddev_shape, stddev_types, sites):
        """
        Returns the standard deviations
        """
        stddevs = []
        tau = C["tau_event"]
        phi = np.sqrt(C["phi0"] ** 2.0 + C["phi_s2s_vs30"] ** 2.)
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

    def get_stddevs(self, C, stddev_shape, stddev_types, sites):
        """
        Returns the standard deviations
        """
        stddevs = []
        tau = C["tau_event"]
        phi = C["phi0"]
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

    def get_stddevs(self, C, stddev_shape, stddev_types, sites):
        """
        Returns the standard deviations, with different site standard
        deviation for inferred vs. observed vs30 sites.
        """
        stddevs = []
        tau = C["tau_event"]
        phi = C["phi0"]
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
    imt                 e1               b1               b2                b3                c1               c2                c3           tau_c3           phis2s        tau_event          tau_l2l             phi0         d0_obs          d1_obs    phi_s2s_obs         d0_inf          d1_inf    phi_s2s_inf
    pgv     1.986297847767   2.278515925276   0.172184178053    0.299544503900   -1.419871787778   0.270864702674   -0.303453527552   0.179928856360   0.560214787771   0.430621988652   0.279217449810   0.446536749421   3.3097520070   -0.5332645095   0.3625706750   2.7840151700   -0.4379095000   0.4267752900
    pga     4.593600817502   1.806328676733   0.144764965899   -0.187664517098   -1.498595099847   0.281454363399   -0.608840589420   0.254501921365   0.606285802404   0.449637491699   0.368682450293   0.467191048339   2.6526145408   -0.4330183106   0.3880615605   1.8825821600   -0.2965628000   0.5160693800
    0.010   4.595831841359   1.805720064378   0.145203067800   -0.187853401989   -1.500785325936   0.281826029391   -0.607836921386   0.254473840849   0.606540945437   0.449511849989   0.369530025591   0.467246778966   2.6478971475   -0.4322729523   0.3897287075   1.8792573300   -0.2960445000   0.5163109500
    0.025   4.625178798002   1.794292615521   0.150033923813   -0.187172831518   -1.544504636982   0.283200216216   -0.572198448811   0.253266193047   0.609478297455   0.445517217217   0.383781890123   0.468739331200   2.5745762874   -0.4205652923   0.3983208764   1.8198326500   -0.2867428000   0.5163641200
    0.040   4.722447583759   1.761676216451   0.163644691708   -0.199095303420   -1.637542321107   0.298686311412   -0.534112656153   0.245054022905   0.625714780107   0.437333696331   0.430292749853   0.473766331531   2.3981825805   -0.3926344156   0.4282655838   1.7054122900   -0.2689552000   0.5303068400
    0.050   4.804502449486   1.739937888686   0.170300151677   -0.219411777440   -1.664377529574   0.312428747006   -0.554344743057   0.260199667680   0.638254309793   0.441516738857   0.460524334450   0.479945223969   2.3273316602   -0.3818559907   0.4292589857   1.6516398200   -0.2606188000   0.5376008400
    0.070   4.991633222166   1.706553346455   0.168745580437   -0.213340469096   -1.644248691403   0.314012606725   -0.640526595472   0.286956317682   0.660284949711   0.452277718801   0.482487985372   0.487092836506   2.1877718947   -0.3613850020   0.4517359114   1.5607340000   -0.2463570000   0.5718250900
    0.100   5.216725999474   1.685519997832   0.153695785712   -0.204807294178   -1.544031349660   0.285148522630   -0.743396259134   0.322309553915   0.662735917380   0.465579412757   0.480973092170   0.496181528747   2.0730412641   -0.3424998011   0.4604892411   1.4820895200   -0.2336438000   0.5553963500
    0.150   5.409547877051   1.678363948934   0.108964259966   -0.189890325563   -1.381902206554   0.225689831260   -0.815043098860   0.322007237429   0.654720113336   0.466509140156   0.417460279625   0.497838049779   2.2727708182   -0.3749611267   0.4861666221   1.4809090000   -0.2333155000   0.5672743200
    0.200   5.453890202270   1.689438303007   0.076992089883   -0.153502646971   -1.307510701800   0.182940816317   -0.772880020737   0.301572220795   0.643153063650   0.470050836760   0.324515411666   0.494091741457   2.6560670263   -0.4340991448   0.4869896477   1.7649609300   -0.2779753000   0.5576915400
    0.250   5.411971846531   1.719357494611   0.056936402466   -0.096882602431   -1.263089491625   0.155409119964   -0.721417443819   0.274901019805   0.622862866230   0.463722804830   0.298346506228   0.488946620721   2.7480683773   -0.4484644519   0.4855914355   1.9701452500   -0.3103584000   0.5292167200
    0.300   5.339975712573   1.786378891274   0.053245731458   -0.098663301545   -1.241241570029   0.137235308693   -0.659797998230   0.261180806047   0.609434612997   0.462823521005   0.275386022961   0.482173998888   2.8690364768   -0.4676298108   0.4393192245   2.1556977900   -0.3395422000   0.5032666700
    0.350   5.245031598707   1.831650711430   0.048429888707   -0.035148822891   -1.215628172562   0.124916267250   -0.617942668472   0.254737453226   0.609391922679   0.456749384828   0.243074261426   0.480246325971   3.1481308412   -0.5118397745   0.4195610063   2.4598770000   -0.3872901000   0.5061812600
    0.400   5.172478034239   1.895942168737   0.049858426143   -0.039080879414   -1.189517733110   0.115875870187   -0.590763475754   0.244367107710   0.615351146488   0.448758077757   0.255382872509   0.475149460687   3.3647442835   -0.5456308979   0.4383505477   2.7118078300   -0.4270472000   0.4975640200
    0.450   5.084466738157   1.944571514150   0.051712882438   -0.031025330564   -1.180661600660   0.110338135521   -0.554433746532   0.246565073080   0.619024594684   0.444336103250   0.264492801723   0.469668176199   3.5172857307   -0.5691696371   0.4314804201   2.8933025700   -0.4558113000   0.4986495800
    0.500   4.997951964959   1.990170872429   0.052104332867   -0.004593285736   -1.177723569167   0.102936390188   -0.518700657967   0.239580664585   0.624726936080   0.436707512229   0.258906103862   0.463184820845   3.6397488812   -0.5884174971   0.4196265192   3.0624020100   -0.4825319000   0.5049358500
    0.600   4.821460385119   2.063102481959   0.052488866603    0.117270851639   -1.167185092157   0.094270555357   -0.453602302389   0.217919431330   0.634947226995   0.433297884320   0.265768656453   0.451229616810   3.8040787963   -0.6128637121   0.4673840372   3.2736918500   -0.5155067000   0.5093605500
    0.700   4.650874453016   2.126986704093   0.051778511140    0.120976499985   -1.162794994152   0.086764496441   -0.397369836147   0.216884654674   0.633121909658   0.432670860724   0.274180569758   0.446717273621   3.9395148792   -0.6334305858   0.4531075195   3.3268218200   -0.5237339000   0.4964101200
    0.750   4.580870529797   2.166636035270   0.054444522760    0.159198932290   -1.153741511196   0.082709852357   -0.376202497137   0.211017683167   0.637549459649   0.435994625372   0.273343997189   0.444283762342   4.0010944942   -0.6422485195   0.4476754524   3.3516081200   -0.5276008000   0.4975281800
    0.800   4.497603764971   2.195468114219   0.055851944127    0.214945824678   -1.146853808225   0.083957213881   -0.362739820962   0.193658451006   0.638406037308   0.441665448007   0.269316725748   0.439302983387   4.0073965405   -0.6430431894   0.4549584586   3.3543753500   -0.5279128000   0.5127660600
    0.900   4.372780254749   2.259226501052   0.057725868653    0.243584010275   -1.136554168196   0.083559304602   -0.333308869969   0.179232974308   0.640053399804   0.448275692043   0.273544894553   0.433011855491   4.0581106377   -0.6504430607   0.4877138340   3.4302810200   -0.5399158000   0.5013492500
    1.000   4.255539415762   2.314814900323   0.061598261165    0.288848394594   -1.124817963757   0.085698397408   -0.316824095141   0.174173178526   0.638043742056   0.453370642316   0.262695165808   0.426660877769   4.0896108054   -0.6537189691   0.4870532362   3.4660194900   -0.5456740000   0.4878925500
    1.200   4.038599595326   2.413732093230   0.069991626760    0.369266408381   -1.121368599080   0.097564258606   -0.274783316235   0.163249277591   0.639395647808   0.453417592399   0.257117589119   0.416472588508   4.1246638246   -0.6584485092   0.4692237794   3.5875517700   -0.5648816000   0.4845956400
    1.400   3.815947355550   2.479964334173   0.074509347805    0.445566078826   -1.128767790619   0.100523683037   -0.234349930531   0.153501938280   0.648910293044   0.466113494834   0.263334123938   0.409571407808   3.9697198427   -0.6338273936   0.5022021590   3.6648316400   -0.5769183000   0.5064035300
    1.600   3.631646560196   2.559663313300   0.085101029487    0.460566449431   -1.140937389837   0.110319345222   -0.197546621568   0.150851270249   0.649738124629   0.472690014103   0.252120577182   0.404939609587   3.8711186097   -0.6176294725   0.5126268954   3.6993783000   -0.5821365000   0.5024275700
    1.800   3.459724392382   2.650290580770   0.107675261134    0.455981136562   -1.154459813177   0.113516198465   -0.166778722563   0.157733949899   0.655942138094   0.477315304326   0.238457136523   0.399046345798   3.9660790917   -0.6335559109   0.5101397071   3.7677577300   -0.5926361000   0.5116718900
    2.000   3.289052190839   2.690118527117   0.112598356463    0.489296858106   -1.166418273993   0.116678434812   -0.140417710429   0.156493287404   0.646925330835   0.486249114926   0.231543933787   0.396483198980   3.8693291853   -0.6186475723   0.4717092960   3.7909059000   -0.5963036000   0.5027081800
    2.500   2.936473383149   2.857769625873   0.160897057712    0.545092895748   -1.175520686035   0.139980229243   -0.120374488710   0.178207969780   0.628898821285   0.488212793617   0.215164835150   0.393293172095   3.7597972552   -0.6030692340   0.4562264913   3.6413000600   -0.5729685000   0.4802799200
    3.000   2.772015641952   3.103623207489   0.227949145568    0.607228251145   -1.156752134438   0.150053019616   -0.148534265023   0.175955415496   0.615630529159   0.497280231565   0.229320445467   0.390850272410   3.5640717199   -0.5731014738   0.4208254002   3.5236038000   -0.5542990000   0.4724179200
    3.500   2.550306389498   3.234115206129   0.275697742205    0.704199586033   -1.163732516411   0.154956829284   -0.142560085634   0.192759182459   0.599224713100   0.489117033253   0.247687790856   0.388075167947   3.2966184393   -0.5316018810   0.3863543972   3.3014560900   -0.5196663000   0.4724968600
    4.000   2.352929414968   3.310357136230   0.300931330210    0.729865592495   -1.177718479274   0.173699671898   -0.141789103905   0.192905670114   0.591874392925   0.493886994741   0.247444911315   0.386955162338   3.2063095555   -0.5172618161   0.3836599987   3.1680036400   -0.4986039000   0.4643274700
    4.500   2.339517782000   3.464574018363   0.362671054888    0.775124154936   -1.172989084907   0.194344947085   -0.155260019763   0.154450733985   0.580249366526   0.467632240734   0.222127895033   0.372830297647   2.8881185592   -0.4682135114   0.3791048229   3.2204644000   -0.5070963000   0.4609898500
    5.000   2.125081971333   3.513252751909   0.382599171515    0.861508135975   -1.209544942675   0.221973829002   -0.125368353163   0.139412564761   0.557973798141   0.475772516421   0.220292403287   0.377432067281   2.6635403637   -0.4328883380   0.3445275272   3.0189620500   -0.4754012000   0.4564274600
    6.000   1.789669612797   3.467032240903   0.390672960654    1.071637690955   -1.224759159711   0.230159180846   -0.112670397633   0.144727555167   0.537858947825   0.449550499950   0.211281351794   0.384943159783   2.4302706471   -0.3950400505   0.3335484380   2.8183061300   -0.4433903000   0.4455756900
    7.000   1.486846474799   3.474332494304   0.408363526227    1.227180966945   -1.285471191423   0.260498715762   -0.069644614376   0.148649539627   0.522468807073   0.444894957763   0.234268694156   0.385888378683   2.3856802170   -0.3888725579   0.3307736581   2.6317335200   -0.4139773000   0.4319478800
    8.000   1.186154376927   3.447858314030   0.418038426054    1.258318646654   -1.329185530776   0.285751511968   -0.050512729714   0.152958209816   0.507682898129   0.440122399653   0.246895677579   0.387676375770   2.2857219463   -0.3721426781   0.3233053528   2.5637828000   -0.4029874000   0.4109592700
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

    def get_stddevs(self, C, stddev_shape, stddev_types, sites):
        """
        Returns the ergodic standard deviation with phi_s2s_inf based on
        that of the inferred Vs30
        """
        stddevs = []
        tau = C["tau_event"]
        phi = C["phi0"]
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
    imt              V1           V2
    pgv     -0.39341866  -0.13481396
    pga     -0.29452412  -0.10139168
    0.0100  -0.29669217  -0.10286746
    0.0250  -0.30159629  -0.10517674
    0.0400  -0.31078421  -0.10955506
    0.0500  -0.31350486  -0.11143807
    0.0700  -0.30101410  -0.10762801
    0.1000  -0.27677509  -0.09933628
    0.1500  -0.25910646  -0.09270073
    0.2000  -0.26216715  -0.09236768
    0.2500  -0.28252048  -0.09712923
    0.3000  -0.30905284  -0.10368510
    0.3500  -0.33949889  -0.11183386
    0.4000  -0.37663849  -0.12258381
    0.4500  -0.41091170  -0.13210332
    0.5000  -0.42752568  -0.13473636
    0.6000  -0.42540127  -0.13071676
    0.7000  -0.41564728  -0.12480806
    0.7500  -0.40812831  -0.12069992
    0.8000  -0.40365318  -0.11835608
    0.9000  -0.40125176  -0.11666171
    1.0000  -0.40229742  -0.11549082
    1.2000  -0.42326943  -0.12205893
    1.4000  -0.47826523  -0.14350172
    1.6000  -0.53714148  -0.16790990
    1.8000  -0.56669999  -0.18088943
    2.0000  -0.57078751  -0.18356059
    2.5000  -0.56937347  -0.18485605
    3.0000  -0.56348106  -0.18577307
    3.5000  -0.53863711  -0.17950416
    4.0000  -0.49270393  -0.16369559
    5.0000  -0.42753793  -0.13854620
    6.0000  -0.35391502  -0.10915034
    7.0000  -0.29887783  -0.08733112
    8.0000  -0.27997634  -0.07999381
    """)

    COEFFS_RANDOM_INT = CoeffsTable(sa_damping=5, table="""\
    imt      PRECAMBRIAN     PALEOZOIC      MESOZOIC      CENOZOIC   PLEISTOCENE     HOLOCENE
    pgv      -0.04511728   -0.13136056   -0.18001284   -0.03707882    0.15836140   0.23520810
    pga       0.01219580   -0.04970639   -0.09890170   -0.03764331    0.07670686   0.09734874
    0.0100    0.01533802   -0.05013079   -0.10570863   -0.05550472    0.09391737   0.10208875
    0.0250    0.01484921   -0.05600987   -0.11752524   -0.07579728    0.11901269   0.11547049
    0.0400    0.01481762   -0.06618308   -0.14016495   -0.11760419    0.17022449   0.13891010
    0.0500    0.01869939   -0.07164723   -0.15637671   -0.15427718    0.21552290   0.14807883
    0.0700    0.02715475   -0.06977797   -0.16327819   -0.16985317    0.23757146   0.13818312
    0.1000    0.03442503   -0.06172966   -0.16251306   -0.15668822    0.22653014   0.11997577
    0.1500    0.03354460   -0.05549254   -0.15500108   -0.12214645    0.19114828   0.10794719
    0.2000    0.02307337   -0.06041465   -0.14445088   -0.08176772    0.15392561   0.10963428
    0.2500    0.00709515   -0.07696600   -0.13396619   -0.05060453    0.13421273   0.12022884
    0.3000   -0.01198412   -0.10029723   -0.12913823   -0.03015621    0.13412885   0.13744694
    0.3500   -0.03816362   -0.12906927   -0.13326702   -0.01385106    0.14836072   0.16599025
    0.4000   -0.07310134   -0.16266592   -0.14379833   -0.00138047    0.17515971   0.20578634
    0.4500   -0.10398615   -0.18487344   -0.14805115    0.00729355    0.19560013   0.23401706
    0.5000   -0.11344841   -0.17621413   -0.13147360    0.01364461    0.18566877   0.22182277
    0.6000   -0.10263361   -0.14653758   -0.10424944    0.01724100    0.15518854   0.18099109
    0.7000   -0.09003508   -0.12090367   -0.08458995    0.01925331    0.13071759   0.14555781
    0.7500   -0.08754214   -0.10968099   -0.07707821    0.02109986    0.12244465   0.13075683
    0.8000   -0.08813501   -0.10247871   -0.07351865    0.02111362    0.11868867   0.12433008
    0.9000   -0.08205339   -0.08915012   -0.06531793    0.01822001    0.10724245   0.11105899
    1.0000   -0.07090768   -0.07322311   -0.05334984    0.01413841    0.09081701   0.09252520
    1.2000   -0.08884488   -0.08551099   -0.05780292    0.01058145    0.11286028   0.10871707
    1.4000   -0.16629049   -0.15266807   -0.09785700    0.00735734    0.21188351   0.19757471
    1.6000   -0.25949238   -0.23487485   -0.14999422    0.00431025    0.33078413   0.30926707
    1.8000   -0.31116827   -0.27808781   -0.17967320    0.00087488    0.39538274   0.37267165
    2.0000   -0.32219642   -0.28044321   -0.18468110   -0.00496891    0.40718948   0.38510016
    2.5000   -0.32729903   -0.27808434   -0.18869352   -0.01434389    0.41388831   0.39453247
    3.0000   -0.33054632   -0.28187680   -0.20225424   -0.02705065    0.42448364   0.41724437
    3.5000   -0.30366378   -0.27259313   -0.21193373   -0.03747213    0.40662104   0.41904173
    4.0000   -0.24211383   -0.23957031   -0.19941948   -0.03754530    0.34734392   0.37130500
    5.0000   -0.16158511   -0.17845904   -0.15328860   -0.02599092    0.24995201   0.26937166
    6.0000   -0.08403767   -0.10359760   -0.08914993   -0.01036742    0.13917923   0.14797339
    7.0000   -0.03574464   -0.04677124   -0.04075787   -0.00053391    0.06073989   0.06306776
    8.0000   -0.02197328   -0.02715535   -0.02481612    0.00194432    0.03569322   0.03630720
    """)

    COEFFS_RANDOM_GRAD = CoeffsTable(sa_damping=5, table="""\
    imt      PRECAMBRIAN     PALEOZOIC      MESOZOIC      CENOZOIC   PLEISTOCENE     HOLOCENE
    pgv      -0.00377539   -0.01099219   -0.01506339   -0.00310274    0.01325160   0.01968210
    pga       0.00082083   -0.00334544   -0.00665649   -0.00253355    0.00516268   0.00655197
    0.0100    0.00143450   -0.00559292   -0.01163716   -0.00789349    0.01214384   0.01154522
    0.0250    0.00175995   -0.00840252   -0.01742227   -0.01404592    0.02053739   0.01757337
    0.0400    0.00268444   -0.01374949   -0.02902116   -0.02692220    0.03794890   0.02905951
    0.0500    0.00446022   -0.01736141   -0.03792810   -0.03833820    0.05327756   0.03588992
    0.0700    0.00679173   -0.01756870   -0.04090881   -0.04285452    0.05982109   0.03471921
    0.1000    0.00791817   -0.01465675   -0.03749064   -0.03779000    0.05394811   0.02807112
    0.1500    0.00651200   -0.01074805   -0.02920993   -0.02589674    0.03891131   0.02043141
    0.2000    0.00355278   -0.00791426   -0.01977059   -0.01332566    0.02284373   0.01461400
    0.2500    0.00134682   -0.00576354   -0.01173464   -0.00560782    0.01190128   0.00985790
    0.3000    0.00028407   -0.00396232   -0.00662483   -0.00261403    0.00662457   0.00629255
    0.3500   -0.00153070   -0.00451714   -0.00510216   -0.00095266    0.00570660   0.00639605
    0.4000   -0.00460162   -0.00838084   -0.00702825    0.00010529    0.00900041   0.01090500
    0.4500   -0.00536110   -0.00966305   -0.00784643    0.00025691    0.01021350   0.01240016
    0.5000    0.00049697   -0.00070336   -0.00110620   -0.00060095    0.00058357   0.00132997
    0.6000    0.01162399    0.01531601    0.01052193   -0.00270846   -0.01668135  -0.01807213
    0.7000    0.02210851    0.02892367    0.02012612   -0.00520967   -0.03167407  -0.03427456
    0.7500    0.02868897    0.03559221    0.02503883   -0.00699066   -0.03990509  -0.04242425
    0.8000    0.03374459    0.03850612    0.02783394   -0.00791762   -0.04506538  -0.04710166
    0.9000    0.04014491    0.04274323    0.03144282   -0.00852165   -0.05211671  -0.05369260
    1.0000    0.04789522    0.04905975    0.03524228   -0.00907716   -0.06125321  -0.06186688
    1.2000    0.04530281    0.04587299    0.03176464   -0.00861789   -0.05720943  -0.05711311
    1.4000    0.02053609    0.02171626    0.01472133   -0.00633121   -0.02502446  -0.02561802
    1.6000   -0.01119364   -0.00911637   -0.00576127   -0.00322652    0.01558554   0.01371227
    1.8000   -0.02933279   -0.02626479   -0.01694104   -0.00119070    0.03817246   0.03555685
    2.0000   -0.03385865   -0.02937003   -0.01934717   -0.00125874    0.04331988   0.04051471
    2.5000   -0.03793958   -0.03189031   -0.02177657   -0.00246749    0.04834548   0.04572848
    3.0000   -0.04414596   -0.03742074   -0.02685797   -0.00388275    0.05677537   0.05553205
    3.5000   -0.04187817   -0.03738244   -0.02887518   -0.00502456    0.05588741   0.05727294
    4.0000   -0.02831360   -0.02663928   -0.02209343   -0.00540328    0.03960300   0.04284660
    5.0000   -0.00650593   -0.00439066   -0.00351352   -0.00504094    0.00820062   0.01125043
    6.0000    0.01744442    0.02257143    0.02058306   -0.00426916   -0.02892987  -0.02739987
    7.0000    0.03349592    0.04154954    0.03789116   -0.00364860   -0.05460270  -0.05468531
    8.0000    0.03828146    0.04740530    0.04337585   -0.00342909   -0.06242891  -0.06320461
    """)
