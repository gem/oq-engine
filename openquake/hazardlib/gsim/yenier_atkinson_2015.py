# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2021 GEM Foundation
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
Module exports :class:`YenierAtkinson2015BSSA`
"""
import numpy as np
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA
from openquake.hazardlib.gsim.base import CoeffsTable, GMPE
from openquake.hazardlib.gsim.boore_2014 import BooreEtAl2014, CONSTS


def get_sof_adjustment(rake, imt):
    """
    Computes adjustment factor for style-of-faulting following the scheme
    proposed by Bommer et al. (2003).

    :param rake:
        Rake value
    :param imt:
        The intensity measure type
    :return:
        The adjustment factor
    """
    im2 = imt.string[:2]
    if imt.string == 'PGA' or (im2 == 'SA' and imt.period <= 0.4):
        f_r_ss = 1.2
    elif im2 == 'SA' and imt.period > 0.4 and imt.period < 3.0:
        f_r_ss = 1.2 - (0.3/np.log10(3.0/0.4))*np.log10(imt.period/0.4)
    elif im2 == 'SA' and imt.period >= 3.0:
        f_r_ss = 1.2 - (0.3/np.log10(3.0/0.4))*np.log10(3.0/0.4)
    else:
        raise ValueError('Unsupported IMT')
    # Set coefficients
    f_n_ss = 0.95
    p_r = 0.68
    p_n = 0.02
    # Normal - F_N:EQ
    if -135 < rake <= -45:
        famp = f_r_ss**(-p_r) * f_n_ss**(1-p_n)
    # Reverse - F_R:EQ
    elif 45 < rake <= 135:
        famp = f_r_ss**(1-p_r) * f_n_ss**(-p_n)
    # Strike-Slip - F_SS:EQ
    elif (-30 < rake <= 30) or (150 < rake <= 180) or (-180 < rake <= -150):
        famp = f_r_ss**(-p_r) * f_n_ss**(-p_n)
    else:
        raise ValueError('Unrecognised rake value')
    return famp


def _get_c_e(region, imt):
    """
    Implements the Ce calibration term.
        - For 'CENA' See eq. 23 at page 2003
    """
    if region == 'CENA':
        # See equation 23 page 2003 of Yenier and Atkinson
        if imt.string == 'PGA':
            return -0.25
        elif imt.string == 'PGV':
            return -0.21
        elif imt.period <= 10.:
            return -0.25 + np.max([0, 0.39*np.log(imt.period/2)])
        else:
            fmt = 'This IMT is not supported by the Ce calibration term'
            msg = fmt.format(region)
            raise ValueError(msg)
    else:
        fmt = '{:s} region does not have Ce calibration term'
        msg = fmt.format(region)
        raise ValueError(msg)


def _get_c_p(region, imt, rrup, m):
    """
    Implements the Cp calibration term
    """
    if region == 'CENA':
        # See equations 24 and 25 page 2003 of Yenier and Atkinson
        if imt.string == 'PGA':
            delta_b3 = 0.030
        elif imt.string == 'PGV':
            delta_b3 = 0.052
        elif imt.period <= 10.:
            tmp = 0.095*np.log(imt.period/0.065)
            delta_b3 = np.min([0.095, 0.030+np.max([0, tmp])])
        else:
            msg = 'This region is not supported by the Ce calibration term'
            raise ValueError(msg)
        # Compute the calibration term
        pseudo_depth = 10**(-0.405+0.235*m)
        reff = (rrup**2+pseudo_depth**2)**0.5
        cp = np.zeros_like(rrup)
        # cp[rrup <= 150] = delta_b3 * np.log(rrup[rrup <= 150]/150.)
        cp[reff <= 150] = delta_b3 * np.log(reff[reff <= 150]/150.)
        return cp
    else:
        fmt = '{:s} region does not have Cp calibration term'
        msg = fmt.format(region)
        raise ValueError(msg)


def _get_edelta(C, m, stress_drop):
    edelta = (C['s0'] + C['s1']*m + C['s2']*m**2 + C['s3']*m**3 +
              C['s4']*m**4)
    m = m[stress_drop > 100]
    edelta[stress_drop > 100] = (C['s5'] + C['s6']*m + C['s7']*m**2 +
                                 C['s8']*m**3 + C['s9']*m**4)
    return edelta


def _get_f_gamma(region, C, imt, rrup):
    """
    Implements
    """
    if region == 'CENA':
        return rrup * C['gCENA']
    elif region == 'CA':
        return rrup * C['gCalifornia']
    else:
        fmt = '{:s} is a key not supported for region definition'
        msg = fmt.format(region)
        raise ValueError(msg)


def _get_f_m(C, imt, m):
    """
    Implements eq. 3 at page 1991
    """
    mh = C['Mh']
    res = C['e0'] + C['e1'] * (m - mh) + C['e2'] * (m - mh)**2
    res[m > mh] = C['e0'] + C['e3']*(m[m > mh] - mh)
    return res


def _get_f_z(C, imt, rrup, m):
    """
    Implements eq. 7 and eq. 8 at page 1991
    """
    # Pseudo depth - see eq. 6 at page 1991
    pseudo_depth = 10**(-0.405+0.235*m)
    # Effective distance - see eq. 5 at page 1991
    reff = (rrup**2+pseudo_depth**2)**0.5
    # The transition_distance is 50 km as defined just below eq. 8
    transition_dst = 50.
    # Geometrical spreading rates
    b1 = -1.3
    b2 = -0.5
    # Geometrical attenuation
    z = reff**b1
    ratio_a = reff / transition_dst
    z[reff > transition_dst] = (transition_dst**b1 *
                                (ratio_a[reff > transition_dst])**b2)
    # Compute geometrical spreading function
    ratio_b = reff / (1.+pseudo_depth**2)**0.5
    return np.log(z) + (C['b3'] + C['b4']*m)*np.log(ratio_b)


def _get_mean_on_rock(region, focal_depth, C2, C3, C4, ctx, imt):
    # Get coefficients
    # Magnitude effect
    f_m = _get_f_m(C2, imt, ctx.mag)
    # Stress adjustment
    f_delta_sigma = _get_stress_drop_adjstment(
        region, focal_depth, C3, imt, ctx.mag)
    # Geometrical spreading
    f_z = _get_f_z(C2, imt, ctx.rrup, ctx.mag)
    # Anelastic attenuation function
    f_gamma = _get_f_gamma(region, C4, imt, ctx.rrup)
    # Regional term for stress drop
    c_e = _get_c_e(region, imt)
    # Regional term for path duration
    c_p = _get_c_p(region, imt, ctx.rrup, ctx.mag)
    # Compute mean using equation 26
    mean = f_m + f_delta_sigma + f_z + f_gamma + c_e + c_p
    return mean


def _get_mean_on_soil(adapted, region, focal_depth, gmm, C2, C3, C4, ctx, imt):
    # Get PGA on rock
    tmp = PGA()
    pga_rock = _get_mean_on_rock(region, focal_depth, C2, C3, C4, ctx, tmp)
    pga_rock = np.exp(pga_rock)
    if adapted:  # in acme_2019
        # Site-effect model: always evaluated for 760 (see HID 2.6.2)
        vs30 = np.ones_like(ctx.vs30) * 760.
    else:
        vs30 = ctx.vs30
    # Compute the mean on soil
    mean = _get_mean_on_rock(region, focal_depth, C2, C3, C4, ctx, imt)
    # coefficients of BooreEtAl2014
    C = gmm.COEFFS[imt]
    mean += get_fs_SeyhanStewart2014(C, imt, pga_rock, vs30)
    if adapted:
        # acme_2019 considers the SoF correction
        famp = [get_sof_adjustment(rake, imt) for rake in ctx.rake]
        mean += np.log(famp)
    return mean


def _get_stress_drop_adjstment(region, focal_depth, C, imt, m):
    """
    Implements eq. 4 at page 1991 and eq. 17 at page 1994. For CENA we
    use eq. 21 at page 2001
    """
    if region == 'CENA':
        d = focal_depth
        t1 = np.clip(0.290 * (d - 10.), None, 0)
        t2 = np.clip(0.229 * (m - 5.), None, 0)
        delta_sigma = np.exp(5.704 + t1 + t2)
        edelta = _get_edelta(C, m, delta_sigma)
        return edelta * np.log(delta_sigma/100.)
    else:
        fmt = '{:s} is a region not supported for stress drop adjustment'
        msg = fmt.format(region)
        raise ValueError(msg)


def get_fs_SeyhanStewart2014(C, imt, pga_rock, vs30):
    """
    Implements eq. 11 and 12 at page 1992 in Yenier and Atkinson (2015)

    :param pga_rock:
        Median peak ground horizontal acceleration for reference
    :param vs30:
    """
    # Linear term
    flin = vs30 / CONSTS['Vref']
    flin[vs30 > C['Vc']] = C['Vc'] / CONSTS['Vref']
    fl = C['c'] * np.log(flin)
    # Non-linear term
    v_s = np.copy(vs30)
    v_s[vs30 > 760.] = 760.
    # parameter (equation 8 of BSSA 2014)
    f_2 = C['f4'] * (np.exp(C['f5'] * (v_s - 360.)) -
                     np.exp(C['f5'] * 400.))
    fnl = CONSTS['f1'] + f_2 * np.log((pga_rock + CONSTS['f3']) / CONSTS['f3'])
    return fl + fnl


class YenierAtkinson2015BSSA(GMPE):
    """
    Implements the GMM of Yenier and Atkinson (2015) as described in the
    paper titled "Regionally Adjustable Generic Ground-Motion Prediction
    Equation to Central and Eastern North America" published on BSSA, vol 105.

    Note that this model does not provide a standard deviation, hence, in order
    to use it for PSHA calculations if must be combined with a model for ground
    motion aleatory uncertainty such as, for example, the one proposed by
    Al Atik (2014).

    :param focal_depth:
        A float defining focal depth [km].
    :param region:
        A string specifying a region. Admitted values are 'CENA' (Central and
        East North America) and 'CA' (California). Default is 'CENA'
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
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see paragraph "Equations for standard deviations", page
    #: 1046.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    #: Required site parameter is Vs30
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are magnitude and hypocenter depth
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'hypo_depth'}

    #: Required distance measures is Rrup
    REQUIRES_DISTANCES = {'rrup'}

    REQUIRES_ATTRIBUTES = {'adapted', 'region', 'focal_depth'}

    adapted = False

    def __init__(self, focal_depth=None, region='CENA'):
        self.focal_depth = focal_depth
        self.region = region
        self.gmpe = BooreEtAl2014()

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        for m, imt in enumerate(imts):
            C2 = self.COEFFS_TAB2[imt]
            C3 = self.COEFFS_TAB3[imt]
            C4 = self.COEFFS_TAB4[imt]

            # Compute focal depth if not set at the initialization level
            if self.focal_depth is None:
                focal_depth = ctx.hypo_depth
            else:
                focal_depth = np.full_like(ctx.hypo_depth, self.focal_depth)

            # Compute mean and std
            mean[m] = _get_mean_on_soil(
                self.adapted, self.region, focal_depth, self.gmpe,
                C2, C3, C4, ctx, imt)

    COEFFS_TAB2 = CoeffsTable(sa_damping=5, table="""\
   imt    Mh        e0      e1       e2      e3      b3        b4
  0.01  5.85  2.227000  0.6874 -0.13630  0.7643 -0.6209  0.060570
 0.013  5.90  2.281000  0.6855 -0.12900  0.7617 -0.6259  0.061290
 0.016  5.85  2.272000  0.6971 -0.12320  0.7594 -0.6308  0.061910
  0.02  5.90  2.378000  0.6999 -0.10660  0.7488 -0.6377  0.062510
 0.025  6.00  2.564000  0.6840 -0.09416  0.7413 -0.6311  0.060970
  0.03  6.15  2.806000  0.6607 -0.09087  0.7389 -0.6028  0.056410
  0.04  5.75  2.731000  0.7034 -0.10860  0.7383 -0.5484  0.048200
  0.05  5.35  2.559000  0.7193 -0.16360  0.7545 -0.5096  0.042790
 0.065  5.75  2.997000  0.6842 -0.15470  0.7553 -0.4665  0.036400
  0.08  5.20  2.576000  0.7651 -0.24340  0.7865 -0.4210  0.030710
   0.1  5.45  2.777000  0.7118 -0.26190  0.7941 -0.3774  0.024720
  0.13  5.35  2.641000  0.7346 -0.33210  0.8116 -0.3551  0.022240
  0.16  5.25  2.466000  0.8088 -0.38710  0.8407 -0.3265  0.019180
   0.2  5.45  2.549000  0.8194 -0.38600  0.8426 -0.2868  0.013760
  0.25  5.60  2.517000  0.8671 -0.37750  0.8785 -0.2429  0.009209
   0.3  5.85  2.635000  0.8471 -0.36310  0.8763 -0.2117  0.005164
   0.4  6.15  2.674000  0.8501 -0.34690  0.8966 -0.1927  0.004847
   0.5  6.25  2.544000  0.8856 -0.34860  0.9182 -0.2079  0.008540
  0.65  6.60  2.617000  0.8758 -0.31600  0.9251 -0.2277  0.013710
   0.8  6.85  2.664000  0.9053 -0.28880  0.8944 -0.2523  0.019060
     1  6.45  1.986000  1.3400 -0.24560  0.9829 -0.2974  0.027650
   1.3  6.75  2.011000  1.3860 -0.20570  1.0000 -0.3503  0.037770
   1.6  6.75  1.753000  1.5640 -0.16780  1.0540 -0.3849  0.044300
     2  6.65  1.251000  1.7480 -0.13160  1.1920 -0.4353  0.053610
   2.5  6.70  0.930800  1.8240 -0.10870  1.2880 -0.4787  0.061430
     3  6.65  0.515600  1.9080 -0.08979  1.4180 -0.5129  0.067610
     4  6.85  0.343900  1.9310 -0.07471  1.5060 -0.5515  0.074290
     5  6.85 -0.079230  1.9800 -0.06211  1.5850 -0.5800  0.078960
   6.5  7.15 -0.006674  1.9730 -0.05453  1.6300 -0.5961  0.081170
     8  7.50  0.256100  1.9420 -0.05230  1.5930 -0.6090  0.082990
    10  7.45 -0.276300  1.9720 -0.04633  1.7230 -0.6196  0.084200
   PGA  5.85  2.216000  0.6859 -0.13920  0.7656 -0.6187  0.060290
   PGV  5.90  5.960000  1.0300 -0.16510  1.0790 -0.5785  0.057370
""")

    COEFFS_TAB3 = CoeffsTable(sa_damping=5, table="""\
   imt      s0      s1       s2        s3        s4        s5       s6       s7        s8        s9
  0.01 -2.0480  1.8810 -0.49010  0.056680 -0.002433 -1.437000  1.24200 -0.28920  0.030880 -0.001252
 0.013 -1.9220  1.8020 -0.47130  0.054710 -0.002357 -1.348000  1.19500 -0.27990  0.030060 -0.001225
 0.016 -1.7110  1.6630 -0.43650  0.050870 -0.002199 -1.079000  1.04100 -0.24660  0.026900 -0.001114
  0.02 -1.1600  1.2740 -0.33440  0.039110 -0.001700 -1.272000  1.25400 -0.31710  0.036240 -0.001550
 0.025 -1.5350  1.5950 -0.42930  0.051030 -0.002242 -1.454000  1.36600 -0.33720  0.037270 -0.001537
  0.03 -1.0560  1.2050 -0.31320  0.036150 -0.001550 -2.243000  1.98100 -0.50860  0.057820 -0.002439
  0.04 -0.8571  1.0440 -0.26770  0.030820 -0.001328 -3.310000  2.66300 -0.66830  0.074150 -0.003056
  0.05 -0.9628  0.9826 -0.21560  0.020800 -0.000742 -4.228000  3.29300 -0.83160  0.093030 -0.003873
 0.065 -2.2250  1.9480 -0.49000  0.054860 -0.002293 -3.960000  2.87100 -0.66750  0.068830 -0.002650
  0.08 -3.6850  2.9620 -0.75100  0.084210 -0.003509 -3.139000  2.17700 -0.46740  0.044660 -0.001598
   0.1 -4.0510  3.1000 -0.76250  0.083280 -0.003393 -2.452000  1.56900 -0.28900  0.023000 -0.000657
  0.13 -4.1740  3.0920 -0.74380  0.079820 -0.003205 -1.384000  0.62640 -0.01161 -0.010920  0.000828
  0.16 -3.9650  2.8200 -0.64990  0.067200 -0.002614 -0.199700 -0.33700  0.25700 -0.042520  0.002176
   0.2 -2.7070  1.7290 -0.33020  0.028160 -0.000906  0.819700 -1.08300  0.43950 -0.061050  0.002846
  0.25 -1.7670  0.9826 -0.13140  0.005998 -0.000012  1.780000 -1.76700  0.60660 -0.078340  0.003498
   0.3 -0.3182 -0.1386  0.17040 -0.028500  0.001421  2.245000 -2.00300  0.63260 -0.076990  0.003268
   0.4  2.0180 -1.8570  0.61170 -0.076740  0.003341  2.422000 -1.93800  0.55580 -0.061740  0.002390
   0.5  3.9560 -3.2880  0.98850 -0.119600  0.005142  0.855500 -0.45280  0.06459  0.005220 -0.000830
  0.65  3.6450 -2.8220  0.79320 -0.089260  0.003555 -0.667100  0.92770 -0.37080  0.061830 -0.003430
   0.8  2.4040 -1.6520  0.40880 -0.037100  0.001051 -2.124000  2.15200 -0.73010  0.105300 -0.005287
     1  1.0660 -0.4552  0.03739  0.010330 -0.001084 -4.473000  4.05100 -1.27400  0.171000 -0.008137
   1.3 -2.5080  2.5230 -0.84460  0.120500 -0.006024 -5.494000  4.76600 -1.43900  0.184900 -0.008458
   1.6 -5.2640  4.7380 -1.47600  0.196300 -0.009284 -5.880000  4.97800 -1.46500  0.183200 -0.008156
     2 -6.6420  5.7670 -1.74200  0.224100 -0.010280 -6.010000  4.98500 -1.43300  0.174800 -0.007587
   2.5 -8.0780  6.8350 -2.01900  0.253800 -0.011410 -4.883000  3.94700 -1.08900  0.126400 -0.005173
     3 -7.9800  6.6430 -1.92400  0.236600 -0.010390 -4.180000  3.31700 -0.88620  0.098880 -0.003853
     4 -7.1230  5.7770 -1.61500  0.190400 -0.007982 -2.627000  1.96300 -0.46160  0.042400 -0.001176
     5 -6.3880  5.0830 -1.38100  0.157600 -0.006361 -1.377000  0.90930 -0.14220  0.001323  0.000710
   6.5 -4.8000  3.6840 -0.93680  0.097630 -0.003474 -0.392900  0.09826  0.09528 -0.027780  0.001959
     8 -3.4160  2.5120 -0.58030  0.051530 -0.001344 -0.006872 -0.18880  0.16920 -0.035340  0.002200
    10 -2.1940  1.5110 -0.28710  0.015340  0.000238  0.268400 -0.38620  0.21690 -0.039670  0.002304
   PGA -2.1320  1.9370 -0.50400  0.058240 -0.002498 -1.444000  1.23500 -0.28510  0.030210 -0.001217
   PGV -2.2460  1.9510 -0.51810  0.061390 -0.002725 -1.758000  1.37900 -0.32560  0.035000 -0.001425
""")

    COEFFS_TAB4 = CoeffsTable(sa_damping=5, table="""\
   imt     gCENA  gCalifornia
  0.01 -0.004661    -0.009823
 0.013 -0.004693    -0.009833
 0.016 -0.004687    -0.009834
  0.02 -0.004668    -0.009817
 0.025 -0.004884    -0.009881
  0.03 -0.005113    -0.010140
  0.04 -0.005266    -0.010760
  0.05 -0.005471    -0.011320
 0.065 -0.005714    -0.011940
  0.08 -0.005794    -0.012390
   0.1 -0.005640    -0.012500
  0.13 -0.005236    -0.012170
  0.16 -0.004771    -0.011660
   0.2 -0.004203    -0.010920
  0.25 -0.003648    -0.010190
   0.3 -0.003121    -0.009435
   0.4 -0.002438    -0.008259
   0.5 -0.002041    -0.007363
  0.65 -0.001638    -0.006452
   0.8 -0.001426    -0.005849
     1 -0.001259    -0.005130
   1.3 -0.001063    -0.004346
   1.6 -0.001171    -0.003900
     2 -0.001016    -0.003359
   2.5 -0.001060    -0.003012
     3 -0.001093    -0.002725
     4 -0.001301    -0.002123
     5 -0.000935    -0.001698
   6.5 -0.000787    -0.001306
     8 -0.000643    -0.001061
    10 -0.000365    -0.000849
   PGA -0.004667    -0.009808
   PGV -0.002792    -0.006313
""")
