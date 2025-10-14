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
Module exports :class:`LanzanoEtAl2019`.
"""
import numpy as np
from scipy.constants import g

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib.gsim import utils
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA


def _get_stddevs(C):
    """
    Return standard deviations as defined in table 1.
    """
    return [np.sqrt(C['tau'] ** 2 + C['phi_S2S'] ** 2 + C['phi_0'] ** 2),
            C['tau'],
            np.sqrt(C['phi_S2S'] ** 2 + C['phi_0'] ** 2)]


def _compute_distance(ctx, dist_type, C):
    """
    Compute the third term of the equation 1:
    FD(Mw,R) = [c1(Mw-Mref) + c2] * log10(R) + c3(R) (eq 4)
    Mref, h, Mh are in matrix C
    """
    dist = getattr(ctx, dist_type)
    R = np.sqrt(dist ** 2 + C['h'] ** 2)
    return ((C['c1'] * (ctx.mag - C['Mref']) + C['c2']) * np.log10(R) +
            C['c3']*R)


def _compute_magnitude(ctx, C):
    """
    Compute the second term of the equation 1:
    b1 * (Mw-Mh) for M<=Mh
    b2 * (Mw-Mh) otherwise
    """
    dmag = ctx.mag - C["Mh"]
    return np.where(
        ctx.mag <= C["Mh"], C['a'] + C['b1'] * dmag, C['a'] + C['b2'] * dmag)


def _site_amplification(ctx, C):
    """
    Compute the fourth term of the equation 1 :
    The functional form Fs in Eq. (1) represents the site amplification and
    it is given by FS = klog10(V0/800), where V0 = Vs30 when Vs30 <= 1500
    and V0=1500 otherwise
    """
    return C['k'] * np.log10(np.clip(ctx.vs30, -np.inf, 1500.0) / 800.0)


def _gen2ref_rock_scaling(C, vs30, kappa0, imt):
    """
    Computes the generic-to reference rock scaling factor as presented
    in:
    Lanzano, G., C. Felicetta, F. Pacor, D. Spallarossa, and P. Traversa
    (2022). Generic-To-Reference Rock Scaling Factors for Seismic Ground Motion
    in Italy, Bull. Seismol. Soc. Am. 112, 1583–1606, doi: 10.1785/0120210063

    The coefficients are from table S2. They allow to scale the grond motion to
    a reference rock from a generic site.

    kappa0 is in meter.
    """
    return C['a'] + C['b'] * np.log10(vs30/800.0) + C['c'] * kappa0


def _ness_correction(ctx, dist_type, C):
    """
    Compute near-source correction C in Eq. 4 of Sgobba, S., Felicetta,
    C., Lanzano, G., Ramadan, F., D’Amico, M., & Pacor, F. (2021).
    NESS2. 0: An updated version of the worldwide dataset for calibrating
    and adjusting ground‐motion models in near source. 
    Bulletin of the Seismological Society of America, 111(5), 2358-2378.
    """
    dist = getattr(ctx, dist_type)
    R = np.sqrt(dist ** 2 + C['hR'] ** 2)
    SS, _NF, TF = utils.get_fault_type_dummy_variables(ctx)
    return np.where(ctx.mag <= C['MrefR'], C['aR'] + C['bR'] * (ctx.mag - C['MrefR']) +
                C['cR'] * np.log10(R) + C['f1R'] * SS + C['f2R'] * TF,
                C['aR'] + C['cR'] * np.log10(R) + C['f1R'] * SS + C['f2R'] * TF)


def _get_mechanism(ctx, C):
    """
    Compute the part of the second term of the equation 1 (FM(SoF)):
    Get fault type dummy variables
    """
    SS, _NF, TF = utils.get_fault_type_dummy_variables(ctx)
    return C['f1'] * SS + C['f2'] * TF


class LanzanoEtAl2019_RJB_OMO(GMPE):
    """
    Implements GMPE developed by G.Lanzano, L.Luzi, F.Pacor, L.Luzi,
    C.Felicetta, R.Puglia, S. Sgobba, M. D'Amico and published as "A Revised
    Ground-Motion Prediction Model for Shallow Crustal Earthquakes in Italy",
    Bull Seismol. Soc. Am., DOI 10.1785/0120180210
    SA are given up to 10 s.

    The horizontal component of motion corresponds to RotD50, i.e. the median
    of the distribution of the intensity measures, obtained from the
    combination of the two horizontal components across all nonredundant
    azimuths (Boore, 2010).
    """
    #: Supported tectonic region type is 'active shallow crust' because the
    #: equations have been derived from data from Italian database ITACA, as
    #: explained in the 'Introduction'.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Set of :mod:`intensity measure types <openquake.hazardlib.imt>`
    #: this GSIM can calculate. A set should contain classes from module
    #: :mod:`openquake.hazardlib.imt`.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    #: Supported intensity measure component is orientation-independent
    #: measure :attr:`~openquake.hazardlib.const.IMC.RotD50`
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, page 1904
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Required site parameter is only Vs30
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are magnitude and rake (eq. 1).
    REQUIRES_RUPTURE_PARAMETERS = {'rake', 'mag'}

    #: Required distance measure is R Joyner-Boore distance (eq. 1).
    REQUIRES_DISTANCES = {'rjb'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        dist_type = 'rjb' if "RJB" in self.__class__.__name__ else 'rrup'
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            imean = (_compute_magnitude(ctx, C) +
                     _compute_distance(ctx, dist_type, C) +
                     _site_amplification(ctx, C) +
                     _get_mechanism(ctx, C))

            istddevs = _get_stddevs(C)

            # Convert units to g, but only for PGA and SA (not PGV):
            if imt.string.startswith(("SA", "PGA")):
                mean[m] = np.log((10.0 ** (imean - 2.0)) / g)
            else:
                # PGV:
                mean[m] = np.log(10.0 ** imean)

            # Return stddevs in terms of natural log scaling
            sig[m], tau[m], phi[m] = np.log(10.0 ** np.array(istddevs))
            # mean_LogNaturale = np.log((10 ** mean) * 1e-2 / g)

    #: Coefficients from SA PGA and PGV from esupp Table S2

    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT     a               b1              b2              c1              c2              c3              k               f1              f2              tau             phi_S2S         phi_0           Mh              Mref            h
    pga     3.4210464090    0.1939540900    -0.0219827770   0.2871492910    -1.4056354760   -0.0029112640   -0.3945759700   0.0859837430    0.0105002390    0.1559878330    0.2205815790    0.2000991410    5.5000000000    5.3239727140    6.9237429440
    pgv     2.0774292740    0.3486332380    0.1359129150    0.2840909830    -1.4565164760   -0.0005727360   -0.5927640710   0.0410782350    -0.0123124280   0.1388529950    0.1641479240    0.1938530300    5.7000000000    5.0155451980    5.9310213910
    0.010   3.4245483320    0.1925159840    -0.0226504290   0.2875277900    -1.4065574040   -0.0029092280   -0.3936344950   0.0859882130    0.0104732970    0.1561741750    0.2207225690    0.2001331220    5.5000000000    5.3265568770    6.9261983550
    0.025   3.4831620980    0.1745072330    -0.0303191060   0.2917712270    -1.4243608230   -0.0028437300   -0.3808661290   0.0869007960    0.0121168920    0.1585446770    0.2231805710    0.2008657270    5.5000000000    5.3726995880    6.9273792970
    0.040   3.6506006610    0.1159102530    -0.0646660020   0.3111117150    -1.4695119300   -0.0027310440   -0.3429284420   0.0870477700    0.0161177530    0.1644920090    0.2324602390    0.2038917110    5.5000000000    5.4968889680    6.9815887950
    0.050   3.7315797180    0.0938111470    -0.0847276080   0.3184743710    -1.4684793000   -0.0029101640   -0.3201326870   0.0900141460    0.0129486380    0.1679197090    0.2388540270    0.2068943560    5.5000000000    5.5554373580    7.1218137630
    0.070   3.8298265420    0.0775399420    -0.1074506180   0.3219830820    -1.4693089940   -0.0034922110   -0.2775266740   0.1027835460    0.0229271220    0.1761561100    0.2512937930    0.2101610770    5.5000000000    5.5053847230    7.2904858360
    0.100   3.8042169810    0.1360109680    -0.0692203330   0.2908601720    -1.4016627520   -0.0043005780   -0.2686743880   0.1147824540    0.0248269350    0.1787478720    0.2637458450    0.2113961580    5.5000000000    5.3797044570    7.2742555760
    0.150   3.6500641550    0.2565050720    0.0271400960    0.2339551240    -1.3111751160   -0.0047018230   -0.3207560810   0.1109474740    0.0198659050    0.1666766970    0.2596149390    0.2113112910    5.5000000000    5.0965762810    6.6927744070
    0.200   3.5441076850    0.3561477800    0.0934922750    0.1983575680    -1.2809085750   -0.0045122270   -0.3768139640   0.0942130060    0.0116640180    0.1611613280    0.2493593750    0.2085199270    5.5000000000    4.8016422440    6.1273995880
    0.250   3.4904108560    0.4258794620    0.1431007860    0.1768779550    -1.2710203890   -0.0038947210   -0.4275803190   0.0803226570    0.0097630190    0.1541437520    0.2349586720    0.2074459640    5.5000000000    4.7851094040    6.0907948160
    0.300   3.4415379890    0.4717747480    0.1926037060    0.1614915210    -1.2949801370   -0.0032193060   -0.4770515440   0.0776675640    0.0061077540    0.1465825190    0.2248859230    0.2059316980    5.5000000000    4.7167541960    5.9795025500
    0.350   3.3446630670    0.5062658120    0.2151211470    0.1564621150    -1.3178170520   -0.0029990590   -0.5306569440   0.0728397670    0.0026993430    0.1410870920    0.2175844480    0.2080023630    5.5000000000    4.3812120300    5.8130994320
    0.400   3.2550575400    0.5331242140    0.2421620470    0.1502822370    -1.2806103220   -0.0027428760   -0.5562808430   0.0661760590    0.0011870680    0.1351999940    0.2142019330    0.2045660900    5.5000000000    4.4598958150    5.8073330520
    0.450   3.3642504070    0.5364578580    0.1855438960    0.1489823740    -1.3018257500   -0.0022889740   -0.5950316360   0.0648499220    0.0049044230    0.1282711800    0.2116409250    0.2038392300    5.8000000000    4.4733992810    5.9505143630
    0.500   3.3608504670    0.5595158750    0.2002091480    0.1445889550    -1.3577631940   -0.0018214290   -0.6175021300   0.0643336580    0.0049344710    0.1292553150    0.2101486370    0.2021378460    5.8000000000    4.3061718270    6.0827633150
    0.600   3.3138586220    0.6159734570    0.2429526950    0.1308776180    -1.3751116050   -0.0011783100   -0.6515274580   0.0517509190    -0.0106807380   0.1388319340    0.2085483340    0.2012532670    5.8000000000    4.2621864430    6.0960486570
    0.700   3.2215424560    0.6410331910    0.2631217720    0.1310231460    -1.3777586170   -0.0008288090   -0.6770253130   0.0348343350    -0.0138034390   0.1487445760    0.2078712150    0.1990177160    5.8000000000    4.2242791970    5.8705686780
    0.750   3.1945748660    0.6615384790    0.2753805270    0.1279582150    -1.3816587680   -0.0006332620   -0.6770002780   0.0325604250    -0.0106144310   0.1493281120    0.2061474600    0.1985444200    5.8000000000    4.2193032080    5.9399226070
    0.800   3.1477172010    0.6744754580    0.2843168320    0.1274454970    -1.3805238730   -0.0005387910   -0.6807607950   0.0301501140    -0.0093150580   0.1488858080    0.2059923330    0.1975251810    5.8000000000    4.1788159560    5.9158308810
    0.900   3.0438692320    0.6960808380    0.2908389870    0.1307696640    -1.3712299710   -0.0003650810   -0.6901600210   0.0243867030    -0.0057274610   0.1510220880    0.2088059530    0.1964681960    5.8000000000    4.1280019240    5.6499915110
    1.000   2.9329562820    0.7162569260    0.2992085610    0.1330221520    -1.3581003000   -0.0003481280   -0.7010380780   0.0187836090    -0.0026838270   0.1498799880    0.2099740670    0.1952706350    5.8000000000    4.0068764960    5.4265347610
    1.200   2.7969754630    0.7522683610    0.3148914470    0.1356882390    -1.3418915980   -0.0001946160   -0.7211447760   0.0156692770    -0.0123682580   0.1475708640    0.2085469600    0.1935369570    5.8000000000    4.0000000000    5.2114400990
    1.400   2.6681627290    0.7789439750    0.3310958850    0.1374053210    -1.3265422970   -0.0001071290   -0.7304122120   0.0122846810    -0.0159220670   0.1480430620    0.2089391760    0.1905401100    5.8000000000    4.0000000000    5.0911883420
    1.600   2.5723270160    0.7847328080    0.3394239090    0.1454225100    -1.3308582950   0.0000000000    -0.7386216010   0.0034499080    -0.0231247190   0.1468224080    0.2119887010    0.1888323370    5.8000000000    4.0644421250    5.1206266020
    1.800   2.4933386330    0.7900020080    0.3305433860    0.1542283440    -1.3289912520   0.0000000000    -0.7538191680   -0.0079587620   -0.0354487870   0.1517555390    0.2125975420    0.1861583190    5.8000000000    4.1264090540    5.2737078390
    2.000   2.4060176790    0.7777348120    0.3199509080    0.1684793150    -1.3282655150   0.0000000000    -0.7472001440   -0.0111369970   -0.0375300390   0.1533446260    0.2112262090    0.1855430060    5.8000000000    4.2174770140    5.3910987520
    2.500   2.2251396500    0.7789914250    0.3280727550    0.1827792890    -1.3593977940   0.0000000000    -0.7332744950   -0.0298755170   -0.0447073420   0.1581459890    0.2057405400    0.1873131960    5.8000000000    4.0841192840    5.2885431340
    3.000   2.0653645110    0.7855377910    0.3585874760    0.1917372820    -1.3622291610   -0.0000725000   -0.6907295050   -0.0523142100   -0.0534721760   0.1730562270    0.2046940180    0.1856376420    5.8000000000    4.0000000000    5.0089807590
    3.500   1.9413692760    0.8006822910    0.3924715050    0.2003105480    -1.3459808710   -0.0003295060   -0.6572701800   -0.0831135690   -0.0497671120   0.1694808560    0.2000002880    0.1858647730    5.8000000000    4.0000000000    5.2239249130
    4.000   1.8088893770    0.7742293710    0.3863288840    0.2209746660    -1.3605497440   -0.0004514760   -0.6361325920   -0.0850828750   -0.0481922640   0.1729190890    0.1933427470    0.1876984700    5.8000000000    4.0000000000    5.1428287170
    4.500   1.7067047740    0.7606577820    0.3932273220    0.2318655310    -1.3607064390   -0.0005424670   -0.6212289540   -0.0851787910   -0.0420861940   0.1750836140    0.1912528510    0.1875258320    5.8000000000    4.0000000000    4.9944908560
    5.000   1.5674508510    0.7351540960    0.4075899440    0.2444741770    -1.3443973430   -0.0006142880   -0.5996128590   -0.0740372190   -0.0294935120   0.1724655580    0.1849939070    0.1920775290    5.8000000000    4.0995166500    4.9182635170
    6.000   1.8015664050    0.6866068140    0.2400330900    0.2681399590    -1.4273047180   -0.0004079660   -0.5582643820   -0.0530155580   -0.0281879710   0.1608258320    0.1827343650    0.1868738640    6.3000000000    4.0725997780    5.6196373890
    7.000   1.6596668010    0.6688108030    0.2910039860    0.2736804460    -1.4575752030   -0.0002092330   -0.5293913010   -0.0164879330   -0.0063757230   0.1639920950    0.1793061350    0.1785781870    6.3000000000    4.0597872070    5.3393074950
    8.000   1.5146417080    0.6053146580    0.2927231020    0.3021009530    -1.4528220690   -0.0001882700   -0.5054615800   0.0012388470    -0.0011382590   0.1605307940    0.1737530120    0.1769475170    6.3000000000    4.2884159230    5.4984545260
    9.000   1.4186859130    0.5413850170    0.2751627760    0.3283351620    -1.4351308790   0.0000000000    -0.5015172920   0.0083605610    0.0036314410    0.1593645820    0.1666775610    0.1771272580    6.3000000000    4.5884949620    6.0000000000
    10.000  1.3142120360    0.4897308100    0.2536297690    0.3484436940    -1.4421713740   0.0000000000    -0.4867303450   0.0170019340    0.0044164240    0.1580884750    0.1616666450    0.1776399420    6.3000000000    4.6826704140    6.2391199410
    """)

    COEFFS_SITE = CoeffsTable(sa_damping=5, table="""
    IMT     a       b       c
    PGA	    0.107	-0.394	-11.775
    0.01	0.107	-0.394	-11.775
    0.025	0.137	-0.381	-12.812
    0.04	0.168	-0.343	-14.276
    0.05	0.182	-0.320	-15.012
    0.07	0.180	-0.278	-15.428
    0.10	0.162	-0.269	-15.014
    0.15	0.119	-0.321	-13.081
    0.20	0.084	-0.377	-11.228
    0.25	0.057	-0.428	-9.620
    0.30	0.042	-0.477	-8.360
    0.35	0.030	-0.531	-7.276
    0.40	0.018	-0.557	-6.266
    0.45	0.009	-0.595	-5.563
    0.50	0.002	-0.617	-5.174
    0.60	-0.006	-0.651	-4.621
    0.70	-0.010	-0.677	-4.184
    0.75	-0.010	-0.677	-3.968
    0.80	-0.009	-0.681	-3.756
    0.90	-0.007	-0.690	-3.473
    1.00	-0.008	-0.701	-3.298
    1.20	-0.010	-0.721	-2.947
    1.40	-0.012	-0.730	-2.630
    1.60	-0.015	-0.739	-2.337
    1.80	-0.021	-0.754	-2.054
    2.00	-0.024	-0.747	-1.685
    2.50	-0.026	-0.733	-0.954
    3.00	-0.024	-0.691	-0.632
    3.50	-0.020	-0.657	-0.499
    4.00	-0.016	-0.636	-0.444
    4.50	-0.016	-0.621	-0.437
    5.00	-0.022	-0.600	-0.349
    6.00	-0.034	-0.558	-0.409
    7.00	-0.043	-0.529	-0.519
    8.00	-0.048	-0.505	-0.601
    9.00	-0.052	-0.502	-0.493
    10.0	-0.055	-0.487	-0.414
    """)


class LanzanoEtAl2019_RUP_OMO(LanzanoEtAl2019_RJB_OMO):
    """
    Implements GMPE developed by G.Lanzano, L.Luzi, F.Pacor, L.Luzi,
    C.Felicetta, R.Puglia, S. Sgobba, M. D'Amico and published as "A Revised
    Ground-Motion Prediction Model for Shallow Crustal Earthquakes in Italy",
    Bull Seismol. Soc. Am., DOI 10.1785/0120180210
    SA are given up to 10 s.
    The prediction is valid for RotD50, which is the median of the
    distribution of the intensity measures, obtained from the combination
    of the two horizontal components across all nonredundant azimuths
    (Boore, 2010).
    """
    #: Supported tectonic region type is 'active shallow crust' because the
    #: equations have been derived from data from Italian database ITACA, as
    #: explained in the 'Introduction'.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Set of :mod:`intensity measure types <openquake.hazardlib.imt>`
    #: this GSIM can calculate. A set should contain classes from module
    #: :mod:`openquake.hazardlib.imt`.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    #: Supported intensity measure component is orientation-independent
    #: measure :attr:`~openquake.hazardlib.const.IMC.RotD50`
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, page 1904
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Required site parameter is only Vs30
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are magnitude and rake (eq. 1).
    REQUIRES_RUPTURE_PARAMETERS = {'rake', 'mag'}

    #: Required distance measure is Rrup (eq. 1).
    REQUIRES_DISTANCES = {'rrup'}

    #: Coefficients from SA PGA and PGV from esupp Table S2
    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT     a               b1              b2              c1              c2              c3              k               f1              f2              tau             phi_S2S         phi_0           Mh              Mref            h
    pga     3.8476009130    0.0774422740    -0.1419991420   0.3478652700    -1.5533187520   -0.0018762870   -0.3804756380   0.0981863920    0.0312839980    0.1614849070    0.2214693590    0.2009857770    5.5000000000    5.7161225870    6.6412174580
    pgv     2.3828051810    0.2389279260    0.0261097410    0.3406251950    -1.5178700950   0.0000000000    -0.5766806200   0.0496574190    0.0048867220    0.1377338650    0.1657577940    0.1947190870    5.7000000000    5.4986237650    5.2603202210
    0.010   3.8506248160    0.0758687500    -0.1428322710   0.3483279440    -1.5537399740   -0.0018758340   -0.3795182780   0.0982026160    0.0312888740    0.1617017580    0.2216042230    0.2010196680    5.5000000000    5.7182953400    6.6339536220
    0.025   3.9192103880    0.0557696980    -0.1527646590   0.3537205430    -1.5755362770   -0.0017839260   -0.3665232370   0.0994148360    0.0335230700    0.1648739390    0.2239781630    0.2017348520    5.5000000000    5.7583429090    6.6418028640
    0.040   4.1174892770    -0.0090338610   -0.1935502850   0.3762847240    -1.6561808690   -0.0015888760   -0.3280283020   0.1003977920    0.0391489610    0.1728423350    0.2330030290    0.2047022980    5.5000000000    5.7989637460    6.7563889150
    0.050   4.2100749050    -0.0339492180   -0.2162534440   0.3850707690    -1.6588279250   -0.0017350640   -0.3051389660   0.1038403080    0.0364310640    0.1769569220    0.2393492360    0.2072790280    5.5000000000    5.8513503470    6.9511244450
    0.070   4.3116802080    -0.0505614890   -0.2390930110   0.3886131870    -1.6360072930   -0.0023201630   -0.2625774900   0.1169554080    0.0468045100    0.1850495830    0.2515478690    0.2106976190    5.5000000000    5.8718716570    7.2254468560
    0.100   4.2619091410    0.0155135150    -0.1931111810   0.3536108950    -1.5607240070   -0.0031932490   -0.2541922120   0.1287730480    0.0481946680    0.1870755970    0.2641319770    0.2116384010    5.5000000000    5.7816875540    7.1942049600
    0.150   4.0281333720    0.1490530750    -0.0842910460   0.2904596360    -1.4558853220   -0.0038111280   -0.3065865390   0.1234294560    0.0409920340    0.1747944550    0.2597923620    0.2119010310    5.5000000000    5.5070413070    6.0448362270
    0.200   3.9581561800    0.2581085140    -0.0067616210   0.2493181400    -1.4304030950   -0.0035049250   -0.3631567460   0.1054336950    0.0308675300    0.1663095650    0.2500575700    0.2094881320    5.5000000000    5.4083470680    6.0814859680
    0.250   3.8975164920    0.3349956980    0.0504825640    0.2239371150    -1.4165129430   -0.0028978730   -0.4143360740   0.0906817050    0.0279033120    0.1577890900    0.2357231150    0.2084723930    5.5000000000    5.4514190000    6.0143888830
    0.300   3.8389631040    0.3840688150    0.1030589990    0.2069719800    -1.4440780970   -0.0022541340   -0.4636965900   0.0874129150    0.0234314860    0.1496049650    0.2259333260    0.2073687490    5.5000000000    5.3968851350    5.8135245350
    0.350   3.7427724390    0.4229320630    0.1304612770    0.1993820250    -1.4408251060   -0.0020338970   -0.5174986310   0.0820839430    0.0191395270    0.1437104080    0.2185074890    0.2098701290    5.5000000000    5.2806552370    5.8177492120
    0.400   3.6333013750    0.4525776370    0.1603621910    0.1917091960    -1.4190236990   -0.0018301470   -0.5434295700   0.0748159970    0.0169681240    0.1358758520    0.2149494900    0.2064883230    5.5000000000    5.2222009260    5.6501186180
    0.450   3.7154781180    0.4556396130    0.1097027610    0.1893950510    -1.4373487560   -0.0013790170   -0.5822090800   0.0724614960    0.0200828160    0.1287203560    0.2124451610    0.2057455270    5.8000000000    5.2478823960    5.7811054530
    0.500   3.7225644930    0.4791000150    0.1250270520    0.1847593340    -1.4792888180   -0.0008746350   -0.6048678230   0.0719131380    0.0201771040    0.1286518970    0.2113216850    0.2036659890    5.8000000000    5.2517779510    5.9416879950
    0.600   3.6682670680    0.5366335520    0.1687213280    0.1707059500    -1.5049666160   -0.0002411380   -0.6392187290   0.0588865330    0.0046486850    0.1365657160    0.2100293700    0.2024728710    5.8000000000    5.2219439350    5.7575653430
    0.700   3.5476098040    0.5605925270    0.1871321630    0.1717388940    -1.4920154380   0.0000000000    -0.6643250560   0.0414345280    0.0015640500    0.1444444740    0.2094865120    0.2002723840    5.8000000000    5.1693165540    5.2232086450
    0.750   3.4860153280    0.5835516220    0.2009753460    0.1676162740    -1.4705858310   0.0000000000    -0.6633662960   0.0390747580    0.0045913530    0.1444192940    0.2075499490    0.1999247850    5.8000000000    5.1608011770    5.2390714490
    0.800   3.4153176700    0.5963140190    0.2090305350    0.1674214930    -1.4563908280   0.0000000000    -0.6668025460   0.0364159000    0.0057644770    0.1435650390    0.2072863380    0.1990343260    5.8000000000    5.1084013460    5.0192508660
    0.900   3.2837755070    0.6203647060    0.2174322510    0.1695628290    -1.4268589930   0.0000000000    -0.6750760810   0.0302972660    0.0092171050    0.1439597930    0.2100453700    0.1980967980    5.8000000000    5.0273018570    4.6888779800
    1.000   3.1646298450    0.6394268750    0.2244466880    0.1725257020    -1.4104378560   0.0000000000    -0.6858604010   0.0243862220    0.0120110190    0.1425963490    0.2117095410    0.1964539980    5.8000000000    4.9152918370    4.2786484540
    1.200   3.0000699100    0.6752604010    0.2398000250    0.1754340770    -1.3847402050   0.0000000000    -0.7049869270   0.0203886700    0.0020858610    0.1376747050    0.2106367700    0.1947050440    5.8000000000    4.8219418190    3.8902573240
    1.400   2.8548239110    0.7016598380    0.2555322610    0.1774234610    -1.3693052940   0.0000000000    -0.7139420780   0.0169071570    -0.0016271820   0.1352870520    0.2110771360    0.1914515130    5.8000000000    4.7438528440    3.6282580540
    1.600   2.7452884200    0.7087902600    0.2642955350    0.1848978730    -1.3616920690   0.0000000000    -0.7215074520   0.0083121970    -0.0083006310   0.1331921300    0.2141947700    0.1895359950    5.8000000000    4.7549230280    3.7025291230
    1.800   2.6642129620    0.7154152980    0.2560921110    0.1931546230    -1.3507839540   0.0000000000    -0.7371011570   -0.0017321440   -0.0190618180   0.1382147940    0.2147123860    0.1868917710    5.8000000000    4.8130574510    3.9589480220
    2.000   2.5756862730    0.7028435510    0.2447144810    0.2076118600    -1.3471065740   0.0000000000    -0.7307501910   -0.0050040160   -0.0212358510   0.1397875260    0.2129299180    0.1864771670    5.8000000000    4.8506617380    4.1479373910
    2.500   2.3963959400    0.7033050700    0.2518818530    0.2222780470    -1.3743185070   0.0000000000    -0.7168917870   -0.0246343480   -0.0290936910   0.1437343890    0.2068222070    0.1887206470    5.8000000000    4.7203537770    4.1181389600
    3.000   2.2442760420    0.7064408310    0.2805790070    0.2323944870    -1.3938825540   0.0000000000    -0.6755767110   -0.0449346600   -0.0392006000   0.1579916440    0.2051285540    0.1872462500    5.8000000000    4.5967141280    3.6676358910
    3.500   2.1509457620    0.7197140890    0.3144950490    0.2408879210    -1.3056875070   0.0000000000    -0.6454403000   -0.0712686810   -0.0377413380   0.1574415450    0.2005062730    0.1876227070    5.8000000000    5.0000000000    3.9746700550
    4.000   2.0269129410    0.6873092210    0.3037401830    0.2643086690    -1.3612857890   0.0000000000    -0.6250815320   -0.0736555330   -0.0363730290   0.1610380970    0.1940097180    0.1895939010    5.8000000000    4.8167431120    3.5842582520
    4.500   1.9350799290    0.6687716310    0.3061467880    0.2778468310    -1.3144751280   0.0000000000    -0.6110294070   -0.0740593630   -0.0294989060   0.1623295570    0.1927623170    0.1893881480    5.8000000000    5.0000000000    3.2644687160
    5.000   1.8090192480    0.6410330200    0.3183807710    0.2915021780    -1.3209096320   0.0000000000    -0.5897990580   -0.0632488020   -0.0172750890   0.1600134890    0.1872621910    0.1941054980    5.8000000000    5.0000000000    3.3548060430
    6.000   1.9455190300    0.5901995040    0.1564201050    0.3140022010    -1.3375771520   0.0000000000    -0.5478118740   -0.0424599370   -0.0125854850   0.1509581730    0.1838901820    0.1900203310    6.3000000000    5.0000000000    3.9006202840
    7.000   1.7832223090    0.5733237300    0.2019467610    0.3199016260    -1.3374591120   0.0000000000    -0.5197861950   -0.0045757050   0.0111162730    0.1555189840    0.1794302890    0.1819988840    6.3000000000    5.0000000000    3.7233318770
    8.000   1.6472982850    0.5073993280    0.2006409390    0.3494261080    -1.4463813400   0.0000000000    -0.4956266160   0.0136222610    0.0172305930    0.1529394340    0.1736945870    0.1803254150    6.3000000000    4.8103931580    4.3526246000
    9.000   1.5105710010    0.4450324910    0.1830610430    0.3751346350    -1.4367324130   0.0000000000    -0.4912014160   0.0208945970    0.0217267490    0.1529569490    0.1662440990    0.1804191720    6.3000000000    4.9295888090    4.5509858920
    10.000  1.3966806560    0.3900867860    0.1589602600    0.3968394420    -1.4232531770   0.0000000000    -0.4765713040   0.0296164880    0.0222468600    0.1525077910    0.1614679730    0.1808181160    6.3000000000    5.0403227000    4.5998115120
  """)


class LanzanoEtAl2019_RJB_OMOscaled(LanzanoEtAl2019_RJB_OMO):
    """
    Implements GMPE developed by G.Lanzano, L.Luzi, F.Pacor, L.Luzi,
    C.Felicetta, R.Puglia, S. Sgobba, M. D'Amico and published as "A Revised
    Ground-Motion Prediction Model for Shallow Crustal Earthquakes in Italy",
    Bull Seismol. Soc. Am., DOI 10.1785/0120180210
    SA are given up to 10 s.
    The prediction is valid for RotD50, which is the median of the
    distribution of the intensity measures, obtained from the combination
    of the two horizontal components across all nonredundant azimuths
    (Boore, 2010).
    Application of a scaling factor that converts the prediction of
    LanzanoEtAl2019_RJB_OMO, valid for RotD50, to the corresponding
    prediction for the Maximum value.
    """

    #: Coefficient table constructed from the electronic suplements of the
    #: original paper.

    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT     a           b1          b2          c1          c2          c3          k           f1          f2          tau         phi_S2S     phi_0       Mh          Mref        h
    pga     3.4597007   0.1939541   -0.0219828  0.2871493   -1.4056355  -0.0029113  -0.3945760  0.0859837   0.0105002   0.1559878   0.2205816   0.2000991   5.5000000   5.3239727   6.9237429
    pgv     2.1195033   0.3486332   0.1359129   0.2840910   -1.4565165  -0.0005727  -0.5927641  0.0410782   -0.0123124  0.1388530   0.1641479   0.1938530   5.7000000   5.0155452   5.9310214
    0.05    3.7703201   0.0938111   -0.0847276  0.3184744   -1.4684793  -0.0029102  -0.3201327  0.0900141   0.0129486   0.1679197   0.2388540   0.2068944   5.5000000   5.5554374   7.1218138
    0.10    3.8445966   0.1360110   -0.0692203  0.2908602   -1.4016628  -0.0043006  -0.2686744  0.1147825   0.0248269   0.1787479   0.2637458   0.2113962   5.5000000   5.3797045   7.2742556
    0.15    3.6932915   0.2565051   0.0271401   0.2339551   -1.3111751  -0.0047018  -0.3207561  0.1109475   0.0198659   0.1666767   0.2596149   0.2113113   5.5000000   5.0965763   6.6927744
    0.20    3.5896393   0.3561478   0.0934923   0.1983576   -1.2809086  -0.0045122  -0.3768140  0.0942130   0.0116640   0.1611613   0.2493594   0.2085199   5.5000000   4.8016422   6.1273996
    0.30    3.4885390   0.4717747   0.1926037   0.1614915   -1.2949801  -0.0032193  -0.4770515  0.0776676   0.0061078   0.1465825   0.2248859   0.2059317   5.5000000   4.7167542   5.9795026
    0.40    3.3047378   0.5331242   0.2421620   0.1502822   -1.2806103  -0.0027429  -0.5562808  0.0661761   0.0011871   0.1352000   0.2142019   0.2045661   5.5000000   4.4598958   5.8073331
    0.50    3.4107980   0.5595159   0.2002091   0.1445890   -1.3577632  -0.0018214  -0.6175021  0.0643337   0.0049345   0.1292553   0.2101486   0.2021378   5.8000000   4.3061718   6.0827633
    0.75    3.2462015   0.6615385   0.2753805   0.1279582   -1.3816588  -0.0006333  -0.6770003  0.0325604   -0.0106144  0.1493281   0.2061475   0.1985444   5.8000000   4.2193032   5.9399226
    1.00    2.9835849   0.7162569   0.2992086   0.1330222   -1.3581003  -0.0003481  -0.7010381  0.0187836   -0.0026838  0.1498800   0.2099741   0.1952706   5.8000000   4.0068765   5.4265348
    2.00    2.4561293   0.7777348   0.3199509   0.1684793   -1.3282655  0.0000000   -0.7472001  -0.0111370  -0.0375300  0.1533446   0.2112262   0.1855430   5.8000000   4.2174770   5.3910988
    3.00    2.1181011   0.7855378   0.3585875   0.1917373   -1.3622292  -0.0000725  -0.6907295  -0.0523142  -0.0534722  0.1730562   0.2046940   0.1856376   5.8000000   4.0000000   5.0089808
    4.00    1.8623784   0.7742294   0.3863289   0.2209747   -1.3605497  -0.0004515  -0.6361326  -0.0850829  -0.0481923  0.1729191   0.1933427   0.1876985   5.8000000   4.0000000   5.1428287
  """)


class LanzanoEtAl2019_RJB_OMO_RefRock(GMPE):
    """
    Implements GMPE developed by G.Lanzano, L.Luzi, F.Pacor, L.Luzi,
    C.Felicetta, R.Puglia, S. Sgobba, M. D'Amico and published as "A Revised
    Ground-Motion Prediction Model for Shallow Crustal Earthquakes in Italy",
    Bull Seismol. Soc. Am., DOI 10.1785/0120180210
    SA are given up to 10 s.

    The horizontal component of motion corresponds to RotD50, i.e. the median
    of the distribution of the intensity measures, obtained from the
    combination of the two horizontal components across all nonredundant
    azimuths (Boore, 2010).

    In this version we scale the ground-motion to reference rock conditions
    using the findings of Lanzano et al. (2020) "Generic-To-Reference Rock
    Scaling Factors for Seismic Ground Motion in Italy", BSSA, 112(3),
    https://doi.org/10.1785/0120210063
    """
    #: Supported tectonic region type is 'active shallow crust' because the
    #: equations have been derived from data from Italian database ITACA, as
    #: explained in the 'Introduction'.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Set of :mod:`intensity measure types <openquake.hazardlib.imt>`
    #: this GSIM can calculate. A set should contain classes from module
    #: :mod:`openquake.hazardlib.imt`.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is orientation-independent
    #: measure :attr:`~openquake.hazardlib.const.IMC.RotD50`
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, page 1904
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Required site parameter is only Vs30
    REQUIRES_SITES_PARAMETERS = {'vs30', 'kappa0'}

    #: Required rupture parameters are magnitude and rake (eq. 1).
    REQUIRES_RUPTURE_PARAMETERS = {'rake', 'mag'}

    #: Required distance measure is R Joyner-Boore distance (eq. 1).
    REQUIRES_DISTANCES = {'rjb'}

    COEFFS = LanzanoEtAl2019_RJB_OMO.COEFFS
    COEFFS_SITE = LanzanoEtAl2019_RJB_OMO.COEFFS_SITE

    def __init__(self, kappa0=None):
        """
        Instantiate the model. When the kappa0 value is provided when
        initializing the class, this overrides the kappa0 value assigned to
        the site.
        """
        self.kappa0 = kappa0

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        if self.kappa0 is not None:
            ctx = ctx.copy()
            ctx.kappa0 = self.kappa0
        [dist_type] = self.REQUIRES_DISTANCES
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            imean = (_compute_magnitude(ctx, C) +
                     _compute_distance(ctx, dist_type, C) +
                     _site_amplification(ctx, C) +
                     _get_mechanism(ctx, C))

            istddevs = _get_stddevs(C)

            # Return stddevs in terms of natural log scaling
            sig[m], tau[m], phi[m] = np.log(10.0 ** np.array(istddevs))

            # Apply correction to reference according to Lanzano et al.
            # (2022; BSSA)
            SCOF = self.COEFFS_SITE[imt]
            adjustment = _gen2ref_rock_scaling(SCOF, ctx.vs30, ctx.kappa0, imt)
            imean += adjustment

            # Convert units to g, but only for PGA and SA (not PGV):
            mean[m] = np.log((10.0 ** (imean - 2.0)) / g)


class LanzanoEtAl2019_RJB_OMO_NESS2(GMPE):
    """
    Implements GMPE developed by G.Lanzano, L.Luzi, F.Pacor, L.Luzi,
    C.Felicetta, R.Puglia, S. Sgobba, M. D'Amico and published as "A Revised
    Ground-Motion Prediction Model for Shallow Crustal Earthquakes in Italy",
    Bull Seismol. Soc. Am., DOI 10.1785/0120180210
    SA are given up to 10 s.

    The horizontal component of motion corresponds to RotD50, i.e. the median
    of the distribution of the intensity measures, obtained from the
    combination of the two horizontal components across all nonredundant
    azimuths (Boore, 2010).

    In this version we add a near-source correction as calibrated in
    Sgobba, S., Felicetta, C., Lanzano, G., Ramadan, F., D’Amico, M.,
    & Pacor, F. (2021). NESS2. 0: An updated version of the worldwide
    dataset for calibrating and adjusting ground‐motion models in near source.
    Bulletin of the Seismological Society of America, 111(5), 2358-2378.
    """
    #: Supported tectonic region type is 'active shallow crust' because the
    #: equations have been derived from data from Italian database ITACA, as
    #: explained in the 'Introduction'.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Set of :mod:`intensity measure types <openquake.hazardlib.imt>`
    #: this GSIM can calculate. A set should contain classes from module
    #: :mod:`openquake.hazardlib.imt`.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is orientation-independent
    #: measure :attr:`~openquake.hazardlib.const.IMC.RotD50`
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, page 1904
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Required site parameter is only Vs30
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are magnitude and rake (eq. 1).
    REQUIRES_RUPTURE_PARAMETERS = {'rake', 'mag'}

    #: Required distance measure is R Joyner-Boore distance (eq. 1).
    REQUIRES_DISTANCES = {'rjb'}

    COEFFS = LanzanoEtAl2019_RJB_OMO.COEFFS

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        [dist_type] = self.REQUIRES_DISTANCES
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            imean = (_compute_magnitude(ctx, C) +
                     _compute_distance(ctx, dist_type, C) +
                     _site_amplification(ctx, C) +
                     _get_mechanism(ctx, C))

            istddevs = _get_stddevs(C)

            # Return stddevs in terms of natural log scaling
            sig[m], tau[m], phi[m] = np.log(10.0 ** np.array(istddevs))

            # Apply correction to reference according to Sgobba et al (2021)
            COEFF_R = self.COEFFS_R[imt]
            adjustment = _ness_correction(ctx, dist_type, COEFF_R)
            adjustment[adjustment < 0] = 0
            imean += adjustment

            # Convert units to g, but only for PGA and SA (not PGV):
            if imt.string.startswith(("SA", "PGA")):
                mean[m] = np.log((10.0 ** (imean - 2.0)) / g)
            else:
                mean[m] = np.log(10.0 ** imean)

    COEFFS_R = CoeffsTable(sa_damping=5, table="""
    IMT     aR              bR              cR              f1R             f2R             hR          MrefR
    pga     0.787478215     0.088770426     -0.413768294    -0.06026392     0.033858525     47.74672921 6.7
    pgv     0.8592549       0.071563232     -0.491301268    0.026774225     0.069196361     41.20192962 6.7
    0.010   0.787175425     0.08896066      -0.413534       -0.06028122     0.03365462      47.75602121 6.7
    0.025   0.764491242     0.093130958     -0.396257625    -0.069223728    0.023615346     48.9614708  6.7
    0.040   0.726355304     0.115782012     -0.366697331    -0.074779741    0.013805846     51.15058401 6.7
    0.050   0.612054704     0.122639338     -0.299314474    -0.084376271    0.0110746       49.05470755 6.7
    0.070   0.400708515     0.108985501     -0.182716111    -0.087470327    0.014284547     45.72288419 6.7
    0.100   0.15499496      0.095270453     -0.039327593    -0.099731305    0.018751436     40.91092673 6.7
    0.150   -0.00844227     0.055307361     0.054636175     -0.097962926    0.032572387     41.2447101  6.7
    0.200   0.009087855     0.057109969     0.043497701     -0.114999243    0.021501432     38.36526231 6.7
    0.250   -0.00226902     0.055972206     0.049428586     -0.119321061    0.016406682     40.70320281 6.7
    0.300   0.133512633     0.053620918     -0.030034406    -0.12000329     0.018602122     39.49920779 6.7
    0.350   0.168517781     0.046429228     -0.052704492    -0.115711083    0.018465044     38.75956761 6.7
    0.400   0.274226221     0.039948329     -0.121628272    -0.099248914    0.040560722     41.50434408 6.7
    0.450   0.3981889       0.036947038     -0.203091887    -0.071998627    0.065723723     47.32999832 6.7
    0.500   0.64992861      0.046333218     -0.338630857    -0.049621838    0.081624352     58.44922068 6.7
    0.600   1.131029598     0.025283514     -0.578953165    -0.02155919     0.086655937     78.36451744 6.7
    0.700   1.153825076     0.013173396     -0.591675895    -0.007083008    0.083557283     81.12064206 6.7
    0.750   1.035871545     -0.001472946    -0.540809171    0.004759027     0.077596681     77.74202337 6.7
    0.800   1.024820433     -0.001170074    -0.539405242    0.008952563     0.069284856     74.31852489 6.7
    0.900   1.960532101     0.023226485     -0.972275599    0.017006082     0.065846277     96.96619773 6.7
    1.000   2.010631147     0.027242195     -1.017890523    0.032711631     0.060514594     86.4514989  6.7
    1.200   2.388754809     0.048935181     -1.234235642    0.059185841     0.061690355     80.93239898 6.7
    1.400   1.646513458     0.081121474     -0.898090616    0.065535469     0.078703437     60.67359062 6.7
    1.600   1.331164843     0.099387448     -0.754064859    0.092138178     0.123430272     51.23511146 6.7
    1.800   1.19457951      0.084516446     -0.685088996    0.111323616     0.142764607     51.02063196 6.7
    2.000   0.97064787      0.077383157     -0.561095606    0.108652508     0.138837329     48.15759882 6.7
    2.500   0.541663899     0.0854089       -0.340575056    0.143613017     0.146084029     37.91884921 6.7
    3.000   0.528462362     0.102182005     -0.333805253    0.143023908     0.141003536     39.51910168 6.7
    3.500   0.635235933     0.105833915     -0.383912684    0.110313089     0.064950541     35.5783488  6.7
    4.000   0.499658821     0.118334308     -0.310867658    0.130591575     0.064005226     32.29346011 6.7
    4.500   0.661570957     0.128856871     -0.403179297    0.137230924     0.04353781      34.30312303 6.7
    5.000   0.969181154     0.129530859     -0.584060571    0.146503294     0.026093139     38.41884159 6.7
    6.000   1.147797426     0.080843293     -0.688890512    0.168970647     0.025350344     43.92034279 6.7
    7.000   1.101971251     0.053294728     -0.659793326    0.127546199     0.010135258     44.77159699 6.7
    8.000   0.878221711     0.047664714     -0.530125235    0.110275005     -0.004572099    40.26392403 6.7
    9.000   0.521928688     0.041132751     -0.318520893    0.08476785      -0.02866004     30.74731071 6.7
    10.000  0.489350096     0.035146663     -0.296663906    0.0675214       -0.035733553    26.74188349 6.7
    """)
