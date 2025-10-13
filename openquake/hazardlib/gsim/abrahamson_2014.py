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
Module exports :class:`AbrahamsonEtAl2014`
               :class:`AbrahamsonEtAl2014RegCHN`
               :class:`AbrahamsonEtAl2014RegJPN`
               :class:`AbrahamsonEtAl2014RegTWN`
"""
import numpy as np

from scipy import interpolate
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable, add_alias
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA
from openquake.hazardlib.gsim.utils_usgs_basin_scaling import \
    _get_z1pt0_usgs_basin_scaling

METRES_PER_KM = 1000.

#: equation constants (that are IMT independent)
CONSTS = {
    'n': 1.5,
    # m2 specified at page 1032 (top)
    'm2': 5.00,
    # h1, h2, h3 specified at page 1040 (top)
    'h1': +0.25,
    'h2': +1.50,
    'h3': -0.75
    }

# CyberShake basin adjustments for ASK14 (only applied above 
# 1.9 seconds so don't provide dummy values listed below 2 s)
# Taken from https://code.usgs.gov/ghsc/nshmp/nshmp-lib/-/blob/main/src/main/resources/gmm/coeffs/ASK14.csv?ref_type=heads
COEFFS_CY = CoeffsTable(sa_damping=5, table="""\
IMT   a44cy    a45cy   
2.0   0.048    0.114     
3.0   0.092    0.223
4.0   0.202    0.333
5.0   0.270    0.399
6.0   0.320    0.200  
7.5   0.354    0.426
10    0.343    0.334
""")


def _get_phi_al_regional(C, mag, vs30measured, rrup):
    """
    Returns intra-event (Phi) standard deviation (equation 24, page 1046)
    """
    s1 = np.ones_like(mag) * C['s1e']
    s2 = np.ones_like(mag) * C['s2e']
    s1[vs30measured] = C['s1m']
    s2[vs30measured] = C['s2m']
    phi_al = s1 + (s2 - s1) / 2. * (mag - 4.)
    phi_al[mag < 4] = s1[mag < 4]
    phi_al[mag >= 6] = s2[mag >= 6]
    return phi_al


def _get_phi_al_regional_JPN(C, mag, vs30measured, rrup):
    """
    Returns intra-event (Tau) standard deviation (equation 26, page 1046)
    """
    phi_al = np.ones((len(vs30measured)))

    idx = rrup < 30
    phi_al[idx] *= C['s5']

    idx = (rrup <= 80.) & (rrup >= 30.)
    phi_al[idx] *= C['s5'] + (C['s6'] - C['s5']) / 50. * (rrup[idx] - 30.)

    idx = rrup > 80
    phi_al[idx] *= C['s6']

    return phi_al


def _get_basic_term(C, ctx):
    """
    Compute and return basic form, see page 1030.
    """
    # Fictitious depth calculation
    c4m = C['c4'] - (C['c4'] - 1.) * (5. - ctx.mag)
    c4m[ctx.mag > 5.] = C['c4']
    c4m[ctx.mag < 4] = 1.
    R = np.sqrt(ctx.rrup**2. + c4m**2.)
    # basic form
    base_term = C['a1'] * np.ones_like(ctx.rrup) + C['a17'] * ctx.rrup
    # equation 2 at page 1030
    after = ctx.mag >= C['m1']
    within = (ctx.mag >= CONSTS['m2']) & (ctx.mag < C['m1'])
    before = ctx.mag < CONSTS['m2']
    base_term[after] += (C['a5'] * (ctx.mag[after] - C['m1']) +
                         C['a8'] * (8.5 - ctx.mag[after])**2. +
                         (C['a2'] + C['a3'] * (ctx.mag[after] - C['m1'])) *
                         np.log(R[after]))
    base_term[within] += (C['a4'] * (ctx.mag[within] - C['m1']) +
                          C['a8'] * (8.5 - ctx.mag[within])**2. +
                          (C['a2'] + C['a3'] * (ctx.mag[within] - C['m1'])) *
                          np.log(R[within]))
    base_term[before] += (C['a4'] * (CONSTS['m2'] - C['m1']) +
                          C['a8'] * (8.5 - CONSTS['m2'])**2. +
                          C['a6'] * (ctx.mag[before] - CONSTS['m2']) +
                          C['a7'] * (ctx.mag[before] - CONSTS['m2'])**2. +
                          (C['a2'] + C['a3'] * (CONSTS['m2'] - C['m1'])) *
                          np.log(R[before]))
    return base_term


def _get_derivative(C, sa1180, vs30):
    """
    Returns equation 30 page 1047
    """
    derAmp = np.zeros_like(vs30)
    n = CONSTS['n']
    c = C['c']
    b = C['b']
    idx = vs30 < C['vlin']
    derAmp[idx] = (b * sa1180[idx] * (-1. / (sa1180[idx] + c) +
                   1. / (sa1180[idx] + c * (vs30[idx] / C['vlin'])**n)))
    return derAmp


def _get_faulting_style_term(C, ctx):
    """
    Compute and return faulting style term, that is the sum of the second
    and third terms in equation 1, page 74.
    """
    # this implements equations 5 and 6 at page 1032. f7 is the
    # coefficient for reverse mechanisms while f8 is the correction
    # factor for normal ruptures
    f7 = C['a11'] * np.clip(ctx.mag - 4., 0., 1.)
    f8 = C['a12'] * np.clip(ctx.mag - 4., 0., 1.)
    # ranges of rake values for each faulting mechanism are specified in
    # table 2, page 1031
    return (f7 * ((ctx.rake > 30) & (ctx.rake < 150)) +
            f8 * ((ctx.rake > -150) & (ctx.rake < -30)))


def _get_hanging_wall_term(C, ctx):
    """
    Compute and return hanging wall model term, see page 1038.
    """
    Fhw = np.zeros_like(ctx.rx)
    Fhw[ctx.rx > 0] = 1.
    # Taper 1
    T1 = _hw_taper1(ctx)
    # Taper 2
    T2 = _hw_taper2(ctx)
    # Taper 3
    T3 = _hw_taper3(ctx)
    # Taper 4
    T4 = _hw_taper4(ctx)
    # Taper 5
    T5 = _hw_taper5(ctx)
    Fhw[ctx.dip == 90.] = 0.
    # Finally, compute the hanging wall term
    return Fhw * C['a13'] * T1 * T2 * T3 * T4 * T5


def _get_inter_event_std(C, mag, sa1180, vs30):
    """
    Returns inter event (tau) standard deviation (equation 25, page 1046)
    """
    tau_al = C['s3'] + (C['s4'] - C['s3']) / 2. * (mag - 5.)
    tau_al[mag < 5.] = C['s3']
    tau_al[mag >= 7.] = C['s4']
    tau_b = tau_al
    tau = tau_b * (1 + _get_derivative(C, sa1180, vs30))
    return tau


def _get_intra_event_std(region, C, mag, sa1180, vs30, vs30measured,
                         rrup):
    """
    Returns Phi as described at pages 1046 and 1047
    """
    phi_al = _get_phi_al_regional_JPN(
        C, mag, vs30measured, rrup
    ) if region == 'JPN' else _get_phi_al_regional(
        C, mag, vs30measured, rrup)
    derAmp = _get_derivative(C, sa1180, vs30)
    phi_amp = 0.4
    idx = phi_al < phi_amp
    if np.any(idx):
        # In the case of small magnitudes and long periods it is possible
        # for phi_al to take a value less than phi_amp, which would return
        # a complex value. According to the GMPE authors in this case
        # phi_amp should be reduced such that it is fractionally smaller
        # than phi_al
        phi_amp = 0.4 * np.ones_like(phi_al)
        phi_amp[idx] = 0.99 * phi_al[idx]
    phi_b = np.sqrt(phi_al**2 - phi_amp**2)
    phi = np.sqrt(phi_b**2 * (1 + derAmp)**2 + phi_amp**2)
    return phi


def _get_regional_term(region, C, imt, vs30, rrup):
    """
    In accordance with Abrahamson et al. (2014) we assume California
    as the default region.
    """
    if region == 'TWN':
        vs30star = _get_vs30star(vs30, imt)
        return C['a31'] * np.log(vs30star/C['vlin']) + C['a25'] * rrup
    elif region == 'CHN':
        return C['a28'] * rrup
    elif region == 'JPN':  # See page 1043
        f3 = interpolate.interp1d(
            [150, 250, 350, 450, 600, 850, 1150, 2000],
            [C['a36'], C['a37'], C['a38'], C['a39'], C['a40'], C['a41'],
             C['a42'], C['a42']],
            fill_value='extrapolate', kind='linear')
        return f3(vs30) + C['a29'] * rrup
    else:  # California
        return 0.


def _get_site_response_term(C, imt, vs30, sa1180):
    """
    Compute and return site response model term see page 1033
    """
    # vs30 star
    vs30_star = _get_vs30star(vs30, imt)
    # compute the site term
    site_resp_term = np.zeros_like(vs30)
    gt_vlin = vs30 >= C['vlin']
    lw_vlin = vs30 < C['vlin']
    # compute site response term for ctx with vs30 greater than vlin
    vs30_rat = vs30_star / C['vlin']
    site_resp_term[gt_vlin] = ((C['a10'] + C['b'] * CONSTS['n']) *
                               np.log(vs30_rat[gt_vlin]))
    # compute site response term for ctx with vs30 lower than vlin
    site_resp_term[lw_vlin] = (C['a10'] * np.log(vs30_rat[lw_vlin]) -
                               C['b'] * np.log(sa1180[lw_vlin] + C['c']) +
                               C['b'] * np.log(sa1180[lw_vlin] + C['c'] *
                                               vs30_rat[lw_vlin] **
                                               CONSTS['n']))
    return site_resp_term


def _get_basin_term(C, ctx, region, imt, usgs_bs=False, cy=False, v1180=None):
    """
    Compute and return soil depth term.  See page 1042.
    """
    # Get vs30
    vs30 = ctx.vs30

    if v1180 is None:
        z10 = ctx.z1pt0.copy()
    else:
        vs30 = v1180
        # fake Z1.0 - Since negative it will be replaced by the default Z1.0
        # for the corresponding region
        z10 = np.ones_like(vs30) * -1

    # Get USGS basin scaling factor if required
    if usgs_bs:
        usgs_baf = _get_z1pt0_usgs_basin_scaling(z10, imt.period)
    else:
        usgs_baf = np.ones(len(vs30))

    # Get reference z1pt0
    z1ref = _get_z1pt0ref(region, vs30) # in km
    # Get z1pt0
    z10 /= METRES_PER_KM # convert site z1pt0 to km
    # This is used for the calculation of the motion on reference rock
    idx = z10 < 0
    z10[idx] = z1ref[idx] # -999 z1pt0 values in site model updated here
    factor = np.log((z10 + 0.01) / (z1ref + 0.01))
    
    # Get cybershake adjustments if required and SA(T > 1.9)
    if cy and imt.period > 1.9:
        a44 = COEFFS_CY[imt]['a44cy']
        a45 = COEFFS_CY[imt]['a45cy']
        adj = 0.1 # CY_CSIM variable in USGS java code for ASK14
    # Regular basin term
    else:
        a44 = C['a44']
        a45 = C['a45']
        adj = 0.  # No additive adjustment

    # Here we use a linear interpolation as suggested in the 'Application
    # guidelines' at page 1044
    # Above 700 m/s the trend is flat, but we extend the Vs30 range to
    # 6,000 m/s (basically the upper limit for mantle shear wave velocity
    # on earth) to allow extrapolation without throwing an error.
    f2 = interpolate.interp1d([0.0, 150, 250, 400, 700, 1000, 6000],
                              [C['a43'], C['a43'], a44, a45, C['a46'],
                               C['a46'], C['a46']], kind='linear')
    f10 = (f2(vs30) * factor) + adj
    
    return f10 * usgs_baf


def _get_stddevs(region, C, imt, ctx, sa1180):
    """
    Return standard deviations as described in paragraph 'Equations for
    standard deviation', page 1046.
    """
    std_intra = _get_intra_event_std(region, C, ctx.mag, sa1180, ctx.vs30,
                                     ctx.vs30measured, ctx.rrup)
    std_inter = _get_inter_event_std(C, ctx.mag, sa1180, ctx.vs30)
    return [np.sqrt(std_intra ** 2 + std_inter ** 2),
            std_inter,
            std_intra]


def _get_top_of_rupture_depth_term(C, imt, ctx):
    """
    Compute and return top of rupture depth term. See paragraph
    'Depth-to-Top of Rupture Model', page 1042.
    """
    return C['a15'] * np.clip(ctx.ztor / 20.0, None, 1.)


def _get_vs30star(vs30, imt):
    """
    This computes equations 8 and 9 at page 1034
    """
    # compute the v1 value (see eq. 9, page 1034)
    if imt.string[:2] == "SA":
        t = imt.period
        if t <= 0.50:
            v1 = 1500.0
        elif t < 3.0:
            v1 = np.exp(-0.35 * np.log(t / 0.5) + np.log(1500.))
        else:
            v1 = 800.0
    elif imt.string == "PGA":
        v1 = 1500.0
    else:
        # This covers the PGV case
        v1 = 1500.0
    # set the vs30 star value (see eq. 8, page 1034)
    vs30_star = np.ones_like(vs30) * vs30
    vs30_star[vs30 >= v1] = v1
    return vs30_star


def _get_z1pt0ref(region, vs30):
    """
    This computes the reference depth to the 1.0 km/s interface
    (z1pt0 in km) using equation 18 at page 1042 of Abrahamson et
    al. (2014)
    """
    if region == 'JPN':
        return np.exp(-5.23/2.*np.log(
            (vs30**2+412.**2.) / (1360.**2+412**2.))) / METRES_PER_KM
    else:    
        return np.exp((-7.67 / 4.)*np.log(
            (vs30**4 + 610.**4) / (1360.**4 + 610.**4))) / METRES_PER_KM


def _hw_taper1(ctx):
    # Compute taper t1
    T1 = (90.-ctx.dip) / 45.0
    T1[ctx.dip <= 30.] = 60./45.
    return T1


def _hw_taper2(ctx):
    # Compute taper t2 (eq 12 at page 1039) - a2hw set to 0.2 as
    # indicated at page 1041
    a2hw = 0.2
    T2 = (1. + a2hw * (ctx.mag - 6.5) - (1. - a2hw) *
          (ctx.mag - 6.5)**2)
    T2[ctx.mag > 6.5] = 1. + a2hw * (ctx.mag[ctx.mag > 6.5] - 6.5)
    T2[ctx.mag <= 5.5] = 0.
    return T2


def _hw_taper3(ctx):
    # Compute taper t3 (eq. 13 at page 1039) - r1 and r2 specified at
    # page 1040
    T3 = np.zeros_like(ctx.rx)
    r1 = ctx.width * np.cos(np.radians(ctx.dip))
    r2 = 3. * r1
    idx = ctx.rx < r1
    T3[idx] = (np.ones_like(ctx.rx)[idx] * CONSTS['h1'] +
               CONSTS['h2'] * (ctx.rx[idx] / r1[idx]) +
               CONSTS['h3'] * (ctx.rx[idx] / r1[idx])**2)
    idx = (ctx.rx >= r1) & (ctx.rx <= r2)
    T3[idx] = 1. - (ctx.rx[idx] - r1[idx]) / (r2[idx] - r1[idx])
    return T3


def _hw_taper4(ctx):
    # Compute taper t4 (eq. 14 at page 1040)
    T4 = np.zeros_like(ctx.rx)
    T4[ctx.ztor <= 10.] = 1. - ctx.ztor[ctx.ztor <= 10.]**2. / 100.
    return T4


def _hw_taper5(ctx):
    # Compute T5 (eq 15a at page 1040) - ry1 computed according to
    # suggestions provided at page 1040
    T5 = np.zeros_like(ctx.rx)
    ry1 = ctx.rx * np.tan(np.radians(20.))
    idx = (ctx.ry0 - ry1) <= 0.0
    T5[idx] = 1.
    idx = ((ctx.ry0 - ry1) > 0.0) & ((ctx.ry0 - ry1) < 5.0)
    T5[idx] = 1. - (ctx.ry0[idx] - ry1[idx]) / 5.0
    return T5


def _get_sa_at_1180(region, C, imt, ctx, usgs_baf=False, cy=False):
    """
    Compute and return mean imt value for rock conditions
    (vs30 = 1100 m/s)
    """
    # reference vs30 = 1180 m/s
    vs30_1180 = np.ones_like(ctx.vs30) * 1180.
    # reference shaking intensity = 0
    ref_iml = np.zeros_like(ctx.vs30)
    return (_get_basic_term(C, ctx) +
            _get_faulting_style_term(C, ctx) +
            _get_site_response_term(C, imt, vs30_1180, ref_iml) +
            _get_hanging_wall_term(C, ctx) +
            _get_top_of_rupture_depth_term(C, imt, ctx) +
            _get_basin_term(C, ctx, region, imt, usgs_baf, cy, vs30_1180) +
            _get_regional_term(region, C, imt, vs30_1180, ctx.rrup))

def get_epistemic_sigma(ctx):
    """
    This function gives the epistemic sigma computed following USGS-2014
    approach. Also, note that the events are
    counted in each magnitude and distance bins. However, the epistemic sigma
    is based on NZ SMDB v1.0
    """
    n = 2
    dist_func_5_6 = np.where(ctx.rrup <=10, 0.4*np.sqrt(n/11),
                             np.where((ctx.rrup > 10) & (ctx.rrup <30),
                                      0.4*np.sqrt(n/38), 0.4*np.sqrt(n/94)))

    dist_func_6_7 = np.where(ctx.rrup <=10, 0.4*np.sqrt(n/2),
                             np.where((ctx.rrup > 10) & (ctx.rrup <30),
                                      0.4*np.sqrt(n/7), 0.4*np.sqrt(n/13)))

    dist_func_7_above = np.where(ctx.rrup <=10, 0.4*np.sqrt(n/2),
                                 np.where((ctx.rrup > 10) & (ctx.rrup <30),
                                          0.4*np.sqrt(n/2), 0.4*np.sqrt(n/4)))

    sigma_epi = np.where((ctx.mag>=5) & (ctx.mag<6), dist_func_5_6,
                         np.where((ctx.mag >=6) & (ctx.mag < 7),
                                  dist_func_6_7, dist_func_7_above))

    return sigma_epi


class AbrahamsonEtAl2014(GMPE):
    """
    Implements GMPE by Abrahamson, Silva and Kamai developed within the
    the PEER West 2 Project. This GMPE is described in a paper
    published in 2014 on Earthquake Spectra, Volume 30, Number 3 and
    titled 'Summary of the ASK14 Ground Motion Relation for Active Crustal
    Regions'.
    """
    #: Supported tectonic region type is active shallow crust, see title!
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are spectral acceleration, peak
    #: ground velocity and peak ground acceleration, see tables 4
    #: pages 1036
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    #: Supported intensity measure component is orientation-independent
    #: average horizontal :attr:`~openquake.hazardlib.const.IMC.RotD50`,
    #: see page 1025.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see paragraph "Equations for standard deviations", page
    #: 1046.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Required site parameters are Vs30 and Z1.0, see table 2, page 1031
    #: Unit of measure for Z1.0 is [m]
    REQUIRES_SITES_PARAMETERS = {'vs30', 'z1pt0', 'vs30measured'}

    #: Required rupture parameters are magnitude, rake, dip, ztor, and width
    #: (see table 2, page 1031)
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'rake', 'dip', 'ztor', 'width'}

    #: Required distance measures are Rrup, Rjb, Ry0 and Rx (see Table 2,
    #: page 1031).
    REQUIRES_DISTANCES = {'rrup', 'rjb', 'rx', 'ry0'}

    #: Reference rock conditions as defined at page
    DEFINED_FOR_REFERENCE_VELOCITY = 1180

    def __init__(self, sigma_mu_epsilon=0.0, region=None,
                 usgs_basin_scaling=False, cybershake_basin_adj=False):
        self.region = region
        assert self.region in (None, 'CHN', 'JPN', 'TWN'), region
        self.sigma_mu_epsilon = sigma_mu_epsilon
        self.usgs_basin_scaling = usgs_basin_scaling
        self.cybershake_basin_adj = cybershake_basin_adj

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            # compute median sa on rock (vs30=1180m/s). Used for site response
            # term calculation
            sa1180 = np.exp(_get_sa_at_1180(self.region,
                                            C, imt, ctx,
                                            self.usgs_basin_scaling,
                                            self.cybershake_basin_adj))

            # For debugging purposes
            # f1 = _get_basic_term(C, ctx)
            # f4 = _get_hanging_wall_term(C, ctx)
            # f5 = _get_site_response_term(C, imt, ctx.vs30, sa1180)
            # f6 = _get_top_of_rupture_depth_term(C, imt, ctx)
            # f7 = _get_faulting_style_term(C, ctx)
            # f10 = _get_basin_term(C, ctx, self.region, imt,
            #                       self.usgs_basin_scaling,
            #                       self.cybershake)
            # fre = _get_regional_term(self.region, C, imt, ctx.vs30, ctx.rrup)

            # get the mean value
            mean[m] = (_get_basic_term(C, ctx) +
                       _get_hanging_wall_term(C, ctx) +
                       _get_site_response_term(C, imt, ctx.vs30, sa1180) +
                       _get_top_of_rupture_depth_term(C, imt, ctx) +
                       _get_faulting_style_term(C, ctx) +
                       _get_basin_term(C, ctx, self.region, imt,
                                       self.usgs_basin_scaling,
                                       self.cybershake_basin_adj))

            mean[m] += _get_regional_term(
                self.region, C, imt, ctx.vs30, ctx.rrup)

            mean[m] += (self.sigma_mu_epsilon*get_epistemic_sigma(ctx))

            # get standard deviations
            sig[m], tau[m], phi[m] = _get_stddevs(
                self.region, C, imt, ctx, sa1180)

    #: Coefficient tables as per annex B of Abrahamson et al. (2014)
    COEFFS = CoeffsTable(sa_damping=5, table="""\
IMT     m1      vlin    b       c       c4      a1      a2      a3      a4      a5      a6      a7   a8      a10     a11     a12     a13     a14     a15     a17     a43     a44     a45     a46     a25     a28     a29     a31     a36     a37     a38     a39     a40     a41     a42     s1e     s2e     s3      s4      s1m     s2m     s5      s6      
pga     6.75    660     -1.47   2.4     4.5     0.587   -0.79   0.275   -0.1    -0.41   2.154   0.0  -0.015  1.735   0       -0.1    0.6     -0.3    1.1     -0.0072 0.1     0.05    0       -0.05   -0.0015 0.0025  -0.0034 -0.1503 0.265   0.337   0.188   0       0.088   -0.196  0.044   0.754   0.52    0.47    0.36    0.741   0.501   0.54    0.6300
pgv     6.75    330     -2.02   2400    4.5     5.975   -0.919  0.275   -0.1    -0.41   2.366   0.0  -0.094  2.36    0       -0.1    0.25    0.22    0.3     -0.0005 0.28    0.15    0.09    0.07    -0.0001 0.0005  -0.0037 -0.1462 0.377   0.212   0.157   0       0.095   -0.038  0.065   0.662   0.51    0.38    0.38    0.66    0.51    0.58    0.5300
0.01    6.75    660     -1.47   2.4     4.5     0.587   -0.790  0.275   -0.1    -0.41   2.154   0.0  -0.015  1.735   0       -0.1    0.6     -0.3    1.1     -0.0072 0.1     0.05    0       -0.05   -0.0015 0.0025  -0.0034 -0.1503 0.265   0.337   0.188   0       0.088   -0.196  0.044   0.754   0.52    0.47    0.36    0.741   0.501   0.54    0.6300
0.02    6.75    680     -1.46   2.4     4.5     0.598   -0.790  0.275   -0.1    -0.41   2.146   0.0  -0.015  1.718   0       -0.1    0.6     -0.3    1.1     -0.0073 0.1     0.05    0       -0.05   -0.0015 0.0024  -0.0033 -0.1479 0.255   0.328   0.184   0       0.088   -0.194  0.061   0.76    0.52    0.47    0.36    0.747   0.501   0.54    0.6300
0.03    6.75    770     -1.39   2.4     4.5     0.602   -0.790  0.275   -0.1    -0.41   2.157   0.0  -0.015  1.615   0       -0.1    0.6     -0.3    1.1     -0.0075 0.1     0.05    0       -0.05   -0.0016 0.0023  -0.0034 -0.1447 0.249   0.32    0.18    0       0.093   -0.175  0.162   0.781   0.52    0.47    0.36    0.769   0.501   0.55    0.6300
0.05    6.75    915     -1.22   2.4     4.5     0.707   -0.790  0.275   -0.1    -0.41   2.085   0.0  -0.015  1.358   0       -0.1    0.6     -0.3    1.1     -0.008  0.1     0.05    0       -0.05   -0.002  0.0027  -0.0033 -0.1326 0.202   0.289   0.167   0       0.133   -0.09   0.451   0.81    0.53    0.47    0.36    0.798   0.512   0.56    0.6500
0.075   6.75    960     -1.15   2.4     4.5     0.973   -0.790  0.275   -0.1    -0.41   2.029   0.0  -0.015  1.258   0       -0.1    0.6     -0.3    1.1     -0.0089 0.1     0.05    0       -0.05   -0.0027 0.0032  -0.0029 -0.1353 0.126   0.275   0.173   0       0.186   0.09    0.506   0.81    0.54    0.47    0.36    0.798   0.522   0.57    0.6900
0.1     6.75    910     -1.23   2.4     4.5     1.169   -0.790  0.275   -0.1    -0.41   2.041   0.0  -0.015  1.31    0       -0.1    0.6     -0.3    1.1     -0.0095 0.1     0.05    0       -0.05   -0.0033 0.0036  -0.0025 -0.1128 0.022   0.256   0.189   0       0.16    0.006   0.335   0.81    0.55    0.47    0.36    0.795   0.527   0.57    0.7000
0.15    6.75    740     -1.59   2.4     4.5     1.442   -0.790  0.275   -0.1    -0.41   2.121   0.0  -0.022  1.66    0       -0.1    0.6     -0.3    1.1     -0.0095 0.1     0.05    0       -0.05   -0.0035 0.0033  -0.0025 0.0383  -0.136  0.162   0.108   0       0.068   -0.156  -0.084  0.801   0.56    0.47    0.36    0.773   0.519   0.58    0.7000
0.2     6.75    590     -2.01   2.4     4.5     1.637   -0.790  0.275   -0.1    -0.41   2.224   0.0  -0.03   2.22    0       -0.1    0.6     -0.3    1.1     -0.0086 0.1     0.05    0       -0.03   -0.0033 0.0027  -0.0031 0.0775  -0.078  0.224   0.115   0       0.048   -0.274  -0.178  0.789   0.565   0.47    0.36    0.753   0.514   0.59    0.7000
0.25    6.75    495     -2.41   2.4     4.5     1.701   -0.790  0.275   -0.1    -0.41   2.312   0.0  -0.038  2.77    0       -0.1    0.6     -0.24   1.1     -0.0074 0.1     0.05    0       0       -0.0029 0.0024  -0.0036 0.0741  0.037   0.248   0.122   0       0.055   -0.248  -0.187  0.77    0.57    0.47    0.36    0.729   0.513   0.61    0.7000
0.3     6.75    430     -2.76   2.4     4.5     1.712   -0.790  0.275   -0.1    -0.41   2.338   0.0  -0.045  3.25    0       -0.1    0.6     -0.19   1.03    -0.0064 0.1     0.05    0.03    0.03    -0.0027 0.002   -0.0039 0.2548  -0.091  0.203   0.096   0       0.073   -0.203  -0.159  0.74    0.58    0.47    0.36    0.693   0.519   0.63    0.7000
0.4     6.75    360     -3.28   2.4     4.5     1.662   -0.790  0.275   -0.1    -0.41   2.469   0.0  -0.055  3.99    0       -0.1    0.58    -0.11   0.92    -0.0043 0.1     0.07    0.06    0.06    -0.0023 0.001   -0.0048 0.2136  0.129   0.232   0.123   0       0.143   -0.154  -0.023  0.699   0.59    0.47    0.36    0.644   0.524   0.66    0.7000
0.5     6.75    340     -3.6    2.4     4.5     1.571   -0.790  0.275   -0.1    -0.41   2.559   0.0  -0.065  4.45    0       -0.1    0.56    -0.04   0.84    -0.0032 0.1     0.1     0.1     0.09    -0.002  0.0008  -0.005  0.1542  0.31    0.252   0.134   0       0.16    -0.159  -0.029  0.676   0.6     0.47    0.36    0.616   0.532   0.69    0.7000
0.75    6.75    330     -3.8    2.4     4.5     1.299   -0.790  0.275   -0.1    -0.41   2.682   0.0  -0.095  4.75    0       -0.1    0.53    0.07    0.68    -0.0025 0.14    0.14    0.14    0.13    -0.001  0.0007  -0.0041 0.0787  0.505   0.208   0.129   0       0.158   -0.141  0.061   0.631   0.615   0.47    0.36    0.566   0.548   0.73    0.6900
1       6.75    330     -3.5    2.4     4.5     1.043   -0.790  0.275   -0.1    -0.41   2.763   0.0  -0.11   4.3     0       -0.1    0.5     0.15    0.57    -0.0025 0.17    0.17    0.17    0.14    -0.0005 0.0007  -0.0032 0.0476  0.358   0.208   0.152   0       0.145   -0.144  0.062   0.609   0.63    0.47    0.36    0.541   0.565   0.77    0.6800
1.5     6.75    330     -2.4    2.4     4.5     0.665   -0.790  0.275   -0.1    -0.41   2.836   0.0  -0.124  2.6     0       -0.1    0.42    0.27    0.42    -0.0022 0.22    0.21    0.2     0.16    -0.0004 0.0006  -0.002  -0.0163 0.131   0.108   0.118   0       0.131   -0.126  0.037   0.578   0.64    0.47    0.36    0.506   0.576   0.8     0.6600
2       6.75    330     -1      2.4     4.5     0.329   -0.790  0.275   -0.1    -0.41   2.897   0.0  -0.138  0.55    0       -0.1    0.35    0.35    0.31    -0.0019 0.26    0.25    0.22    0.16    -0.0002 0.0003  -0.0017 -0.1203 0.123   0.068   0.119   0       0.083   -0.075  -0.143  0.555   0.65    0.47    0.36    0.48    0.587   0.8     0.6200
3       6.82    330     0       2.4     4.5     -0.060  -0.790  0.275   -0.1    -0.41   2.906   0.0  -0.172  -0.95   0       -0.1    0.2     0.46    0.16    -0.0015 0.34    0.3     0.23    0.16    0       0       -0.002  -0.2719 0.109   -0.023  0.093   0       0.07    -0.021  -0.028  0.548   0.64    0.47    0.36    0.472   0.576   0.8     0.5500
4       6.92    330     0       2.4     4.5     -0.299  -0.790  0.275   -0.1    -0.41   2.889   0.0  -0.197  -0.95   0       -0.1    0       0.54    0.05    -0.001  0.41    0.32    0.23    0.14    0       0       -0.002  -0.2958 0.135   0.028   0.084   0       0.101   0.072   -0.097  0.527   0.63    0.47    0.36    0.447   0.565   0.76    0.5200
5       7       330     0       2.4     4.5     -0.562  -0.765  0.275   -0.1    -0.41   2.898   0.0  -0.218  -0.93   0       -0.1    0       0.61    -0.04   -0.001  0.51    0.32    0.22    0.13    0       0       -0.002  -0.2718 0.189   0.031   0.058   0       0.095   0.205   0.015   0.505   0.63    0.47    0.36    0.425   0.568   0.72    0.5000
6       7.06    330     0       2.4     4.5     -0.875  -0.711  0.275   -0.1    -0.41   2.896   0.0  -0.235  -0.91   0       -0.2    0       0.65    -0.11   -0.001  0.55    0.32    0.2     0.1     0       0       -0.002  -0.2517 0.215   0.024   0.065   0       0.133   0.285   0.104   0.477   0.63    0.47    0.36    0.395   0.571   0.7     0.5000
7.5     7.15    330     0       2.4     4.5     -1.303  -0.634  0.275   -0.1    -0.41   2.870   0.0  -0.255  -0.87   0       -0.2    0       0.72    -0.19   -0.001  0.49    0.28    0.17    0.09    0       0       -0.002  -0.14   0.15    -0.07   0       0       0.151   0.329   0.299   0.457   0.63    0.47    0.36    0.378   0.575   0.67    0.5000
10      7.25    330     0       2.4     4.5     -1.928  -0.529  0.275   -0.1    -0.41   2.843   0.0  -0.285  -0.8    0       -0.2    0       0.8     -0.3    -0.001  0.42    0.22    0.14    0.08    0       0       -0.002  -0.0216 0.092   -0.159  -0.05   0       0.124   0.301   0.243   0.429   0.63    0.47    0.36    0.359   0.585   0.64    0.5000
    """)


for region in 'CHN JPN TWN'.split():
    add_alias('AbrahamsonEtAl2014Reg' + region, AbrahamsonEtAl2014,
              region=region)
