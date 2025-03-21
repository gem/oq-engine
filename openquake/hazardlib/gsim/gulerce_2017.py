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
Module exports :class:`GulerceEtAl2017`
               :class:`GulerceEtAl2017RegTWN`
               :class:`GulerceEtAl2017RegITA`
               :class:`GulerceEtAl2017RegMID`
               :class:`GulerceEtAl2017RegCHN`
               :class:`GulerceEtAl2017RegJPN`
"""

import numpy as np

from openquake.baselib.general import CallableDict
from openquake.hazardlib import const
from openquake.hazardlib.gsim.base import CoeffsTable, GMPE
from openquake.hazardlib.imt import SA

#: equation constants (that are IMT independent)
CONSTS = {
    # m1, m2 specified at section "Moderate-to-Large Magnitude Scaling"
    'm1': 6.75,
    'm2': 5.50,
    # h1, h2, h3 specified at section "Hanging Wall Effects"
    'h1': +0.25,
    'h2': +1.50,
    'h3': -0.75}


def _get_basic_term(C, ctx):
    """
    Compute and return basic form, see Equation 11 to 13.
    """
    # Fictitious depth calculation, Equation 13. Unlike ASK14, the break in
    # the c4m function is shifted to M6.0.
    # The equation for c4m for M4.0-6.0 is different from GKAS16 EQS paper,
    # but used the supplementary material instead after code verification.
    c4m = C['c4'] - (C['c4'] - 1.) * (6. - ctx.mag) / 2.
    c4m[ctx.mag > 6.] = C['c4']
    c4m[ctx.mag < 4.] = 1.
    # Equation 12
    R = np.sqrt(ctx.rrup**2. + c4m**2.)
    # basic form, Equation 11
    base_term = C['a1'] * np.ones_like(ctx.rrup) + C['a17'] * ctx.rrup
    # NB: m1 > m2
    after = ctx.mag >= CONSTS['m1']
    within = (ctx.mag < CONSTS['m1']) & (ctx.mag >= CONSTS['m2'])
    before = ctx.mag < CONSTS['m2']
    base_term[after] += (C['a5'] * (ctx.mag - CONSTS['m1']) +
                         C['a8'] * (8.5 - ctx.mag)**2. +
                         (C['a2'] + C['a3'] * (ctx.mag - CONSTS['m1'])) *
                         np.log(R))[after]
    base_term[within] += (C['a4'] * (ctx.mag - CONSTS['m1']) +
                          C['a8'] * (8.5 - ctx.mag)**2. +
                          (C['a2'] + C['a3'] * (ctx.mag - CONSTS['m1'])) *
                          np.log(R))[within]
    base_term[before] += (C['a4'] * (CONSTS['m2'] - CONSTS['m1']) +
                          C['a8'] * (8.5 - CONSTS['m2']) ** 2. +
                          C['a6'] * (ctx.mag - CONSTS['m2']) +
                          (C['a2'] + C['a3'] * (CONSTS['m2'] - CONSTS['m1'])
                          ) * np.log(R))[before]
    return base_term


def _get_faulting_style_term(C, ctx):
    """
    Compute and return faulting style term, that is the sum of the second
    and third terms in Equation 1.
    """
    # this implements Equations 3 and 4;
    # f7 is the term for reverse fault mechanisms;
    # f8 is the term for normal fault mechanisms.
    f7 = np.where(ctx.mag > 5., C['a11'],
                  np.where(ctx.mag >= 4.,  C['a11'] * (ctx.mag - 4.), 0.))
    f8 = np.where(ctx.mag > 5., C['a12'],
                  np.where(ctx.mag >= 4., C['a12'] * (ctx.mag - 4.), 0.))
    # ranges of rake values for each faulting mechanism are same with ASK14
    return (f7 * ((ctx.rake > 30) & (ctx.rake < 150)) +
            f8 * ((ctx.rake > -150) & (ctx.rake < -30)))


def _get_hanging_wall_term(C, ctx):
    """
    Compute and return hanging wall model term, see section on
    "Hanging Wall Effects".
    """
    Fhw = np.zeros_like(ctx.rx)
    Fhw[ctx.rx > 0] = 1.
    # Compute dip taper t1, Equation 6
    T1 = np.ones_like(ctx.rx)
    T1 *= np.where(ctx.dip <= 30, 60/45, (90.-ctx.dip) / 45)
    # Compute magnitude taper t2, Equation 7, with a2hw set to 0.2.
    T2 = np.zeros_like(ctx.rx)
    a2hw = 0.2
    after = ctx.mag >= 6.5
    within = (ctx.mag > 5.5) & (ctx.mag < 6.5)
    before = ctx.mag <= 5.5
    T2[after] += (1. + a2hw * (ctx.mag[after] - 6.5))
    T2[within] += (1. + a2hw * (ctx.mag[within] - 6.5) - (1. - a2hw) *
                   (ctx.mag[within] - 6.5)**2)
    T2[before] = 0.
    # Compute distance taper t3, Equation 8
    T3 = np.zeros_like(ctx.rx)
    r1 = ctx.width * np.cos(np.radians(ctx.dip))
    # The r2 term is different here from ASK14 where r2 = 3*r1.
    r2 = 4. * r1
    #
    idx = ctx.rx < r1
    T3[idx] = (np.ones_like(ctx.rx)[idx] * CONSTS['h1'] +
               CONSTS['h2'] * (ctx.rx[idx] / r1[idx]) +
               CONSTS['h3'] * (ctx.rx[idx] / r1[idx])**2)
    #
    idx = (ctx.rx >= r1) & (ctx.rx <= r2)
    T3[idx] = 1. - (ctx.rx[idx] - r1[idx]) / (r2[idx] - r1[idx])
    # Compute depth taper t4, Equation 9
    T4 = np.zeros_like(ctx.rx)
    #
    T4[ctx.ztor <= 10.] += (1. - ctx.ztor[ctx.ztor <= 10.]**2. / 100.)
    # Compute off-edge distance taper T5, Equation 10
    # ry1 computed same as in ASK14
    T5 = np.zeros_like(ctx.rx)
    ry1 = ctx.rx * np.tan(np.radians(20.))
    #
    idx = (ctx.ry0 - ry1) <= 0.0
    T5[idx] = 1.
    #
    idx = (((ctx.ry0 - ry1) > 0.0) & ((ctx.ry0 - ry1) < 5.0))
    T5[idx] = 1. - (ctx.ry0[idx] - ry1[idx]) / 5.0
    # Finally, compute the hanging wall term, Equation 5
    Fhw[ctx.dip == 90.0] = 0.
    return Fhw*C['a13']*T1*T2*T3*T4*T5


def _get_inter_event_std(region, C, mag):
    """
    Returns inter-event standard deviation, Tau, Equation 20
    """
    tau = _get_tau_regional(region, C, mag)
    return tau


def _get_intra_event_std(region, C, mag):
    """
    Returns intra-event std dev, Phi, Equation 19.
    """
    # Intra-event standard deviation model is simplified since the effect
    # of nonlinearity of the rock motion is not incorporated
    # (Equations 27-30 in ASK14 are not used).
    phi = _get_phi_regional(region, C, mag)
    return phi


_get_phi_regional = CallableDict()


@_get_phi_regional.add("CAL", "CHN", "ITA", "TWN", "MID")
def _get_phi_regional_1(region, C, mag):
    """
    Returns regional (default) intra-event standard deviation
    """
    phi = C['s1'] + (C['s2_noJP'] - C['s1']) / 2. * (mag - 4.)
    phi[mag < 4] = C['s1']
    phi[mag > 6] = C['s2_noJP']
    return phi


@_get_phi_regional.add("JPN")
def _get_phi_regional_2(region, C, mag):
    """
    Returns regional intra-event standard deviation (Phi) for Japan
    """
    phi = C['s1'] + (C['s2_all'] - C['s1']) / 2. * (mag - 4.)
    phi[mag < 4] = C['s1']
    phi[mag > 6] = C['s2_all']
    return phi


_get_regional_term = CallableDict()


@_get_regional_term.add("CAL")
def _get_regional_term_CAL(region, C, imt, vs30, rrup):
    """
    As with ASK14, we assume California as the default region,
    hence here the regional term is assumed = 0.
    """
    return 0.


@_get_regional_term.add("TWN")
def _get_regional_term_TWN(region, C, imt, vs30, rrup):
    """
    Compute regional term for Taiwan, see section "Regionalization and
    Aftershocks"
    """
    vs30star = _get_vs30star(vs30, imt)
    return C['a31'] * np.log(vs30star/C['vlin']) + C['a25'] * rrup


@_get_regional_term.add("ITA")
def _get_regional_term_ITA(region, C, imt, vs30, rrup):
    """
    Compute regional term for Italy, see section "Regionalization and
    Aftershocks"
    """
    # removed regional linear vs30 scaling term since a32=0
    return C['a26'] * rrup


@_get_regional_term.add("MID")
def _get_regional_term_MID(region, C, imt, vs30, rrup):
    """
    Compute regional term for Middle East, see section "Regionalization and
    Aftershocks"
    """
    return C['a27'] * rrup


@_get_regional_term.add("CHN")
def _get_regional_term_CHN(region, C, imt, vs30, rrup):
    """
    Compute regional term for China, see section "Regionalization and
    Aftershocks"
    """
    return C['a28'] * rrup


@_get_regional_term.add("JPN")
def _get_regional_term_JPN(region, C, imt, vs30, rrup):
    """
    Compute regional term for Japan, see section "Regionalization and
    Aftershocks"
    """
    vs30star = _get_vs30star(vs30, imt)
    return C['a35'] * np.log(vs30star/C['vlin']) + C['a29'] * rrup


def _get_site_response_term(C, imt, vs30):
    """
    Compute and return site response model term; see section
    "Site Amplification Effects".
    """
    # vs30 star, Equation 15
    vs30_star = _get_vs30star(vs30, imt)
    # compute the site term
    site_resp_term = np.zeros_like(vs30)

    # Unlike ASK14, the site term here is independent of nonlinear response
    # parameters b, c, and n.
    vs30_rat = vs30_star / C['vlin']
    site_resp_term = C['a10'] * np.log(vs30_rat)
    return site_resp_term


def _get_stddevs(region, C, imt, ctx):
    """
    Return standard deviations as described in section "Equations for
    Standard Deviation".
    """
    std_intra = _get_intra_event_std(region, C, ctx.mag)
    std_inter = _get_inter_event_std(region, C, ctx.mag)
    return [np.sqrt(std_intra ** 2 + std_inter ** 2), std_inter, std_intra]


_get_tau_regional = CallableDict()


@_get_tau_regional.add("CAL", "CHN", "ITA", "TWN", "MID")
def _get_tau_regional_CAL(region, C, mag):
    """
    Returns regional (default) inter-event standard deviation
    """
    tau = C['s3'] + (C['s4_noJP'] - C['s3']) / 2. * (mag - 5.)
    tau[mag < 5] = C['s3']
    tau[mag > 7] = C['s4_noJP']
    return tau


@_get_tau_regional.add("JPN")
def _get_tau_regional_JPN(region, C, mag):
    """
    Returns regional inter-event standard deviation (Tau) for Japan
    """
    tau = C['s3'] + (C['s4_all'] - C['s3']) / 2. * (mag - 5.)
    tau[mag < 5] = C['s3']
    tau[mag > 7] = C['s4_all']
    return tau


def _get_top_of_rupture_depth_term(C, imt, ctx):
    """
    Compute and return top-of-rupture depth term, see section
    "Deph Scaling Effects".
    """
    return np.where(ctx.ztor >= 20., C['a15'], C['a15'] * ctx.ztor / 20.)


def _get_vs30star(vs30, imt):
    """
    This computes and returns the tapered Vs30, in Equations 15 and 16.
    """
    # compute the limiting v1 value, see Equation 16.
    t = imt.period
    if t <= 0.50:
        v1 = 1500.0
    elif t < 3.0:
        # changed to -0.351 for additional significant figures
        v1 = np.exp(-0.351 * np.log(t / 0.5) + np.log(1500.))
    else:
        v1 = 800.0

    # set the vs30 star value, see Equation 15.
    vs30_star = np.ones_like(vs30) * vs30
    vs30_star[vs30 >= v1] = v1
    return vs30_star


class GulerceEtAl2017(GMPE):
    """
    Implements the GKAS16 GMPE by Gulerce et al. (2017) for vertical-component
    ground motions from the PEER NGA-West2 Project.

    This model follows the same functional form as in ASK14 by Abrahamson et
    al. (2014) with minor modifications to the underlying parameters.

    Note that this is a more updated version than the GMPE described in the
    original PEER Report 2013/24.

    Reference:

    Gulerce, Z., Kamai, R., Abrahamson, N., & Silva, W. (2017) "Ground Motion
    Prediction Equations for the Vertical Ground Motion Component Based on the
    NGA-W2 Database", Earthquake Spectra, 33(2), 499-528.
    """
    region = "CAL"

    #: Supported tectonic region type is active shallow crust, as part of the
    #: NGA-West2 Database; re-defined here for clarity.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure type is spectral acceleration
    #: at T=0.01 to 10.0 s; see Tables 1a and 1b.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {SA}

    #: Supported intensity measure component is the
    #: :attr:`~openquake.hazardlib.const.IMC.Vertical` direction component;
    #: see title.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.VERTICAL

    #: Supported standard deviation types are inter-event, intra-event
    #: and total; see the section for "Equations for Standard Deviation".
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Required site parameter is Vs30 only. Unlike in ASK14, the nonlinear
    #: site response and Z1.0 scaling is not incorporated; see the section
    #: for "Site Amplification Effects".
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are magnitude, rake, dip, ztor, and width;
    #: see the section for "Functional Form of the Model".
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'rake', 'dip', 'ztor', 'width'}

    #: Required distance measures are Rrup, Rjb, Ry0 and Rx;
    #: see the section for "Functional Form of the Model".
    REQUIRES_DISTANCES = {'rrup', 'rjb', 'rx', 'ry0'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        for spec of input and result values.
        <.base.GroundShakingIntensityModel.compute>`
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]

            # get the mean value
            mean[m] = (_get_basic_term(C, ctx) +
                       _get_faulting_style_term(C, ctx) +
                       _get_site_response_term(C, imt, ctx.vs30) +
                       _get_hanging_wall_term(C, ctx) +
                       _get_top_of_rupture_depth_term(C, imt, ctx))
            mean[m] += _get_regional_term(
                self.region, C, imt, ctx.vs30, ctx.rrup)
            # get standard deviations
            sig[m], tau[m], phi[m] = _get_stddevs(self.region, C, imt, ctx)

    #: Coefficients obtained from Tables 1a, 1b, 2, and 3 in
    #: Gulerce et al. (2017). This coefficient table is also provided in a free
    #: supplementary material distributed by the authors.
    COEFFS = CoeffsTable(sa_damping=5, table="""\
IMT      vlin    c       c4      a1         a2        a3       a4       a5        a6       a8      a10        a11       a12      a13      a14       a15       a17        a25        a26        a27       a28       a29        a31       a35       s1        s2_all    s3        s4_all    s2_noJP    s4_noJP
0.01     660     2.4     8.6     1.3504     -1.087    0.275    0.121    -0.592    1.78     0       -0.397     -0.2      -0.12    0.67     -0.168    1.1       -0.0062    0.0015     -0.0007    0.0031    0.0035    -0.001     0.252     0.38      0.734     0.52      0.4402    0.3501    0.45       0.3219
0.02     680     2.4     8.6     1.4832     -1.106    0.275    0.111    -0.592    1.78     0       -0.36      -0.2      -0.12    0.67     -0.165    1.1       -0.0064    0.0017     -0.0007    0.0031    0.0035    -0.0009    0.215     0.343     0.734     0.5396    0.4546    0.3586    0.473      0.3328
0.03     770     2.4     8.6     1.7798     -1.15     0.275    0.105    -0.592    1.759    0       -0.34      -0.2      -0.12    0.67     -0.18     1.1       -0.0069    0.0016     -0.0008    0.0032    0.0037    -0.001     0.195     0.323     0.734     0.551     0.4958    0.3904    0.4865     0.3613
0.05     915     2.4     8.6     1.9652     -1.108    0.26     0.148    -0.559    1.708    0       -0.405     -0.2      -0.12    0.67     -0.212    1.1       -0.0092    0.0013     -0.0011    0.003     0.0047    -0.0006    0.26      0.388     0.734     0.5654    0.5365    0.4604    0.5035     0.4108
0.075    960     2.4     8.6     1.7821     -1.006    0.247    0.202    -0.531    1.689    0       -0.46      -0.2      -0.12    0.67     -0.112    1.1       -0.0102    -0.0009    -0.0021    0.003     0.0054    -0.0009    0.315     0.443     0.734     0.5769    0.5078    0.468     0.504      0.3945
0.1      910     2.4     8.6     1.6862     -0.952    0.239    0.258    -0.514    1.742    0       -0.474     -0.2      -0.12    0.67     -0.09     1.1       -0.0097    -0.0014    -0.0035    0.0026    0.0051    -0.0014    0.329     0.457     0.734     0.585     0.4714    0.4165    0.504      0.3621
0.15     740     2.4     8.6     1.6087     -0.94     0.227    0.309    -0.488    1.831    0       -0.474     -0.159    -0.12    0.67     -0.075    1.1       -0.0075    -0.0014    -0.0045    0.002     0.0041    -0.0024    0.329     0.457     0.734     0.585     0.4189    0.3713    0.504      0.3283
0.2      590     2.4     8.6     1.4836     -0.928    0.218    0.346    -0.469    1.937    0       -0.474     -0.129    -0.12    0.67     -0.075    1.1       -0.006     -0.0012    -0.0045    0.002     0.0038    -0.0029    0.329     0.457     0.7098    0.585     0.3955    0.3389    0.504      0.3058
0.25     495     2.4     8.6     1.3777     -0.928    0.211    0.374    -0.454    2.032    0       -0.474     -0.106    -0.12    0.62     -0.075    1.1       -0.0045    -0.0015    -0.0047    0.0015    0.0029    -0.0037    0.329     0.457     0.6909    0.585     0.3819    0.3138    0.504      0.2884
0.3      430     1.8     8.6     1.3091     -0.928    0.206    0.397    -0.443    2.109    0       -0.474     -0.088    -0.12    0.579    -0.075    1.031     -0.0036    -0.0015    -0.0044    0.0013    0.0025    -0.004     0.329     0.457     0.6756    0.585     0.3835    0.2932    0.504      0.2741
0.4      360     1.8     8.6     1.1237     -0.928    0.197    0.434    -0.352    2.227    0       -0.474     -0.059    -0.12    0.515    -0.075    0.922     -0.0024    -0.0015    -0.0034    0.0011    0.0016    -0.0041    0.329     0.457     0.6513    0.585     0.4       0.2608    0.504      0.2516
0.5      340     1.8     8.6     0.961      -0.928    0.19     0.462    -0.281    2.351    0       -0.49      -0.036    -0.12    0.465    -0.075    0.837     -0.0017    -0.0012    -0.0025    0.0007    0.0011    -0.0041    0.345     0.473     0.6325    0.585     0.4277    0.2357    0.5249     0.2342
0.75     330     1.8     8.6     0.6477     -0.928    0.178    0.513    -0.152    2.577    0       -0.575     0.006     -0.12    0.374    -0.06     0.683     -0.001     -0.0002    -0.0006    0         0.0004    -0.0038    0.43      0.558     0.5983    0.611     0.4686    0.19      0.563      0.2025
1        330     1.8     8.6     0.4024     -0.928    0.169    0.6      -0.061    2.7      0       -0.626     0.035     -0.12    0.31     0.017     0.574     -0.001     0          0          0         0.0004    -0.0031    0.481     0.609     0.5741    0.6295    0.5       0.19      0.59       0.18
1.5      330     1.8     8.6     0.0656     -0.928    0.157    0.838    0.068     2.821    0       -0.721     0.076     -0.12    0.219    0.147     0.42      -0.001     0          0          0         0.0004    -0.0023    0.576     0.704     0.5399    0.6555    0.5337    0.19      0.628      0.184
2        330     1.8     8.6     -0.2475    -0.928    0.148    1.006    0.159     2.869    0       -0.73      0.106     -0.12    0.155    0.246     0.311     -0.001     0          0          0         0.0004    -0.0018    0.585     0.713     0.5157    0.674     0.5337    0.19      0.655      0.184
3        330     1.8     8.6     -0.7131    -0.928    0.136    1.244    0.288     2.92     0       -0.649     0.147     -0.12    0.064    0.385     0.157     -0.001     0          0          0         0.0004    -0.0018    0.504     0.632     0.4815    0.7       0.5337    0.19      0.693      0.184
4        330     1.8     8.6     -1.0571    -0.928    0.128    1.413    0.494     2.95     0       -0.575     0.176     -0.12    0        0.484     0.048     -0.001     0          0          0         0.0004    -0.0018    0.43      0.558     0.4572    0.7       0.5337    0.19      0.72       0.184
5        330     1.8     8.6     -1.7084    -0.848    0.121    1.544    0.654     2.95     0       -0.5       0.199     -0.12    0        0.561     -0.037    -0.001     0          0          0         0.0004    -0.0018    0.355     0.483     0.4384    0.7       0.5337    0.19      0.72       0.184
6        330     1.8     8.6     -2.2393    -0.783    0.115    1.651    0.784     2.95     0       -0.427     0.218     -0.12    0        0.624     -0.106    -0.001     0          0          0         0.0004    -0.0018    0.282     0.41      0.4231    0.7       0.5337    0.19      0.72       0.184
7.5      330     1.8     8.6     -2.9456    -0.704    0.109    1.78     0.9425    2.95     0       -0.3185    0.2405    -0.12    0        0.7       -0.19     -0.001     0          0          0         0.0004    -0.0018    0.1735    0.3015    0.4044    0.7       0.5337    0.19      0.72       0.184
10       330     1.8     8.6     -4.0143    -0.6      0.1      1.95     1.15      2.95     0       -0.209     0.27      -0.12    0        0.8       -0.3      -0.001     0          0          0         0.0004    -0.0018    0.064     0.192     0.38      0.7       0.5337    0.19      0.72       0.184
    """)


class GulerceEtAl2017RegTWN(GulerceEtAl2017):
    """
    Implements the GKAS16 GMPE by Gulerce et al. (2017) for vertical-component
    ground motions from the PEER NGA-West2 Project.

    Regional corrections for Taiwan
    """
    region = "TWN"


class GulerceEtAl2017RegITA(GulerceEtAl2017):
    """
    Implements the GKAS16 GMPE by Gulerce et al. (2017) for vertical-component
    ground motions from the PEER NGA-West2 Project.

    Regional corrections for Italy
    """
    region = "ITA"


class GulerceEtAl2017RegMID(GulerceEtAl2017):
    """
    Implements the GKAS16 GMPE by Gulerce et al. (2017) for vertical-component
    ground motions from the PEER NGA-West2 Project.

    Regional corrections for Middle East
    """
    region = "MID"


class GulerceEtAl2017RegCHN(GulerceEtAl2017):
    """
    Implements the GKAS16 GMPE by Gulerce et al. (2017) for vertical-component
    ground motions from the PEER NGA-West2 Project.

    Regional corrections for China
    """
    region = "CHN"


class GulerceEtAl2017RegJPN(GulerceEtAl2017):
    """
    Implements the GKAS16 GMPE by Gulerce et al. (2017) for vertical-component
    ground motions from the PEER NGA-West2 Project.

    Regional corrections for Japan
    """
    region = "JPN"
