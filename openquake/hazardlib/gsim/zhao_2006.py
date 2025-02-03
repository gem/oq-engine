# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2025 GEM Foundation
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
Module exports :class:`ZhaoEtAl2006Asc`, :class:`ZhaoEtAl2006SInter`,
:class:`ZhaoEtAl2006SSlab`, :class:`ZhaoEtAl2006SInterNSHMP2008` and
:class:`ZhaoEtAl2006SSlabNSHMP2014`
"""
import numpy as np
# standard acceleration of gravity in m/s**2
from scipy.constants import g
import copy

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib.gsim.mgmpe.cb14_basin_term import _get_cb14_basin_term


def _get_us23_nshm_adjustments(ln_mean, imt, ctx, cb14_basin_term,
                               m9_basin_term):
    """
    If specified get the US 2023 NSHM basin adjustments:

    1) The ZhaoEtAl2006 GMM lacks a basin term and therefore uses the Campbell
       and Bozorgnia (2014) (z2pt5-based) basin term.
    2) If Seattle Basin region, the M9 basin term is applied instead of the
       CB14 basin term if long period ground-motion (T >= 1.9s) and is a deep
       basin site (z2pt5 >= 6.0 km)
    """
    # Set a null basin term
    fb = np.zeros(len(ln_mean))
    # Apply cb14 basin term if specified
    if cb14_basin_term:
        fb = _get_cb14_basin_term(imt, ctx)
    # Apply m9 basin term if specified (will override
    # cb14 basin term for basin sites if T >= 1.9 s)
    if m9_basin_term and imt.period >= 1.9:
        fb[ctx.z2pt5 >= 6.0] = np.log(2.0) # Basin sites use m9 basin

    return fb


def _compute_distance_term(C, mag, rrup):
    """
    Compute second and third terms in equation 1, p. 901.
    """
    term1 = C['b'] * rrup
    term2 = - np.log(rrup + C['c'] * np.exp(C['d'] * mag))

    return term1 + term2


def _compute_faulting_style_term(C, rake):
    """
    Compute fifth term in equation 1, p. 901.
    """
    # p. 900. "The differentiation in focal mechanism was
    # based on a rake angle criterion, with a rake of +/- 45
    # as demarcation between dip-slip and strike-slip."
    return ((rake > 45.0) & (rake < 135.0)) * C['FR']


def _compute_focal_depth_term(C, hypo_depth):
    """
    Compute fourth term in equation 1, p. 901.
    """
    # p. 901. "(i.e, depth is capped at 125 km)".
    focal_depth = np.clip(hypo_depth, 0, 125.)

    # p. 902. "We used the value of 15 km for the
    # depth coefficient hc ...".
    hc = 15.0

    # p. 901. "When h is larger than hc, the depth terms takes
    # effect ...". The next sentence specifies h>=hc.
    return (focal_depth >= hc) * C['e'] * (focal_depth - hc)


def _compute_magnitude_squared_term(P, M, Q, W, mag):
    """
    Compute magnitude squared term, equation 5, p. 909.
    """
    return P * (mag - M) + Q * (mag - M) ** 2 + W


def _compute_magnitude_term(C, mag):
    """
    Compute first term in equation 1, p. 901.
    """
    return C['a'] * mag


def _compute_site_class_term(C, vs30):
    """
    Compute nine-th term in equation 1, p. 901.
    """
    # map vs30 value to site class, see table 2, p. 901.
    site_term = np.zeros(len(vs30))

    # hard rock
    site_term[vs30 > 1100.0] = C['CH']

    # rock
    site_term[(vs30 > 600) & (vs30 <= 1100)] = C['C1']

    # hard soil
    site_term[(vs30 > 300) & (vs30 <= 600)] = C['C2']

    # medium soil
    site_term[(vs30 > 200) & (vs30 <= 300)] = C['C3']

    # soft soil
    site_term[vs30 <= 200] = C['C4']

    return site_term


def _compute_slab_correction_term(C, rrup):
    """
    Compute path modification term for slab events, that is
    the 8-th term in equation 1, p. 901.
    """
    slab_term = C['SSL'] * np.log(rrup)

    return slab_term


def _set_stddevs(sig, tau, phi, Cs, Ct):
    """
    Set standard deviations as defined in equation 3 p. 902.
    """
    sig[:] = np.sqrt(Cs ** 2 + Ct ** 2)
    tau[:] = Ct
    phi[:] = Cs


class ZhaoEtAl2006Asc(GMPE):
    """
    Implements GMPE developed by John X. Zhao et al. and published as
    "Attenuation Relations of Strong Ground Motion in Japan Using Site
    Classification Based on Predominant Period" (2006, Bulletin of the
    Seismological Society of America, Volume 96, No. 3, pages 898-913).
    This class implements the equations for 'Active Shallow Crust'
    (that's why the class name ends with 'Asc').
    """
    #: Supported tectonic region type is active shallow crust, this means
    #: that factors SI, SS and SSL are assumed 0 in equation 1, p. 901.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration, see paragraph 'Development of Base Model'
    #: p. 901.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Supported intensity measure component is geometric mean
    #: of two horizontal components :
    #: attr:`~openquake.hazardlib.const.IMC.GEOMETRIC_MEAN`, see paragraph
    #: 'Development of Base Model', p. 901.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see equation 3, p. 902.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}

    #: Required site parameters is Vs30.
    #: See table 2, p. 901.
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required rupture parameters are magnitude, rake, and focal depth.
    #: See paragraph 'Development of Base Model', p. 901.
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'rake', 'hypo_depth'}

    #: Required distance measure is Rrup.
    #: See paragraph 'Development of Base Model', p. 902.
    REQUIRES_DISTANCES = {'rrup'}

    #: Reference conditions. See Table 2 at page 901. The hard rock conditions
    #: is 1100 m/s. Here we force it to 800 to make it compatible with a
    #: generic site term
    #  DEFINED_FOR_REFERENCE_VELOCITY = 1100
    DEFINED_FOR_REFERENCE_VELOCITY = 800

    def __init__(self, cb14_basin_term=False, m9_basin_term=False):
        if cb14_basin_term or m9_basin_term:
            self.REQUIRES_SITES_PARAMETERS = frozenset(
            self.REQUIRES_SITES_PARAMETERS | {'z2pt5'})
        self.cb14_basin_term = cb14_basin_term
        self.m9_basin_term = m9_basin_term

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            # extracting dictionary of coefficients specific to required
            # intensity measure type.
            C = self.COEFFS_ASC[imt]

            # mean value as given by equation 1, p. 901, without considering
            # interface and intraslab terms (that is SI, SS, SSL = 0) and
            # inter and intra event terms, plus the magnitude-squared term
            # correction factor (equation 5 p. 909).
            mean_i = _compute_magnitude_term(C, ctx.mag) +\
                _compute_distance_term(C, ctx.mag, ctx.rrup) +\
                _compute_focal_depth_term(C, ctx.hypo_depth) +\
                _compute_faulting_style_term(C, ctx.rake) +\
                _compute_site_class_term(C, ctx.vs30) +\
                _compute_magnitude_squared_term(P=0.0, M=6.3, Q=C['QC'],
                                                W=C['WC'], mag=ctx.mag)

            # convert from cm/s**2 to g and back into natural log
            ln_mean = np.log(np.exp(mean_i) * 1e-2 / g)

            # Get basin adjustments if specified
            fb = _get_us23_nshm_adjustments(ln_mean, imt, ctx,
                                            self.cb14_basin_term,
                                            self.m9_basin_term)

            mean[m] = ln_mean + fb
            _set_stddevs(sig[m], tau[m], phi[m], C['sigma'], C['tauC'])

    #: Coefficient table obtained by joining table 4 (except columns for
    #: SI, SS, SSL), table 5 (both at p. 903) and table 6 (only columns for
    #: QC WC TauC), p. 907.
    COEFFS_ASC = CoeffsTable(sa_damping=5, table="""\
    IMT    a     b         c       d      e        FR     CH     C1     C2     C3     C4     sigma   QC      WC      tauC
    pga    1.101 -0.00564  0.0055  1.080  0.01412  0.251  0.293  1.111  1.344  1.355  1.420  0.604   0.0     0.0     0.303
    0.05   1.076 -0.00671  0.0075  1.060  0.01463  0.251  0.939  1.684  1.793  1.747  1.814  0.640   0.0     0.0     0.326
    0.10   1.118 -0.00787  0.0090  1.083  0.01423  0.240  1.499  2.061  2.135  2.031  2.082  0.694   0.0     0.0     0.342
    0.15   1.134 -0.00722  0.0100  1.053  0.01509  0.251  1.462  1.916  2.168  2.052  2.113  0.702   0.0     0.0     0.331
    0.20   1.147 -0.00659  0.0120  1.014  0.01462  0.260  1.280  1.669  2.085  2.001  2.030  0.692   0.0     0.0     0.312
    0.25   1.149 -0.00590  0.0140  0.966  0.01459  0.269  1.121  1.468  1.942  1.941  1.937  0.682   0.0     0.0     0.298
    0.30   1.163 -0.00520  0.0150  0.934  0.01458  0.259  0.852  1.172  1.683  1.808  1.770  0.670   0.0     0.0     0.300
    0.40   1.200 -0.00422  0.0100  0.959  0.01257  0.248  0.365  0.655  1.127  1.482  1.397  0.659   0.0     0.0     0.346
    0.50   1.250 -0.00338  0.0060  1.008  0.01114  0.247 -0.207  0.071  0.515  0.934  0.955  0.653  -0.0126  0.0116  0.338
    0.60   1.293 -0.00282  0.0030  1.088  0.01019  0.233 -0.705 -0.429 -0.003  0.394  0.559  0.653  -0.0329  0.0202  0.349
    0.70   1.336 -0.00258  0.0025  1.084  0.00979  0.220 -1.144 -0.866 -0.449 -0.111  0.188  0.652  -0.0501  0.0274  0.351
    0.80   1.386 -0.00242  0.0022  1.088  0.00944  0.232 -1.609 -1.325 -0.928 -0.620 -0.246  0.647  -0.0650  0.0336  0.356
    0.90   1.433 -0.00232  0.0020  1.109  0.00972  0.220 -2.023 -1.732 -1.349 -1.066 -0.643  0.653  -0.0781  0.0391  0.348
    1.00   1.479 -0.00220  0.0020  1.115  0.01005  0.211 -2.451 -2.152 -1.776 -1.523 -1.084  0.657  -0.0899  0.0440  0.338
    1.25   1.551 -0.00207  0.0020  1.083  0.01003  0.251 -3.243 -2.923 -2.542 -2.327 -1.936  0.660  -0.1148  0.0545  0.313
    1.50   1.621 -0.00224  0.0020  1.091  0.00928  0.248 -3.888 -3.548 -3.169 -2.979 -2.661  0.664  -0.1351  0.0630  0.306
    2.00   1.694 -0.00201  0.0025  1.055  0.00833  0.263 -4.783 -4.410 -4.039 -3.871 -3.640  0.669  -0.1672  0.0764  0.283
    2.50   1.748 -0.00187  0.0028  1.052  0.00776  0.262 -5.444 -5.049 -4.698 -4.496 -4.341  0.671  -0.1921  0.0869  0.287
    3.00   1.759 -0.00147  0.0032  1.025  0.00644  0.307 -5.839 -5.431 -5.089 -4.893 -4.758  0.667  -0.2124  0.0954  0.278
    4.00   1.826 -0.00195  0.0040  1.044  0.00590  0.353 -6.598 -6.181 -5.882 -5.698 -5.588  0.647  -0.2445  0.1088  0.273
    5.00   1.825 -0.00237  0.0050  1.065  0.00510  0.248 -6.752 -6.347 -6.051 -5.873 -5.798  0.643  -0.2694  0.1193  0.275
    """)


class ZhaoEtAl2006SInter(ZhaoEtAl2006Asc):
    """
    Implements GMPE developed by John X. Zhao et al and published as
    "Attenuation Relations of Strong Ground Motion in Japan Using Site
    Classification Based on Predominant Period" (2006, Bulletin of the
    Seismological Society of America, Volume 96, No. 3, pages
    898-913). This class implements the equations for 'Subduction
    Interface' (that's why the class name ends with 'SInter'). This
    class extends the
    :class:`openquake.hazardlib.gsim.zhao_2006.ZhaoEtAl2006Asc`
    because the equation for subduction interface is obtained from the
    equation for active shallow crust, by removing the faulting style
    term and adding a subduction interface term.
    """
    #: Supported tectonic region type is subduction interface, this means
    #: that factors FR, SS and SSL are assumed 0 in equation 1, p. 901.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    #: Required rupture parameters are magnitude and focal depth.
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'hypo_depth'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            # extracting dictionary of coefficients specific to required
            # intensity measure type.
            C = self.COEFFS_ASC[imt]
            C_SINTER = self.COEFFS_SINTER[imt]

            # mean value as given by equation 1, p. 901, without considering
            # faulting style and intraslab terms (that is FR, SS, SSL = 0) and
            # inter and intra event terms, plus the magnitude-squared term
            # correction factor (equation 5 p. 909)
            mean_i = _compute_magnitude_term(C, ctx.mag) +\
                _compute_distance_term(C, ctx.mag, ctx.rrup) +\
                _compute_focal_depth_term(C, ctx.hypo_depth) +\
                _compute_site_class_term(C, ctx.vs30) + \
                _compute_magnitude_squared_term(P=0.0, M=6.3,
                                                Q=C_SINTER['QI'],
                                                W=C_SINTER['WI'],
                                                mag=ctx.mag) + C_SINTER['SI']

            # Convert from cm/s**2 to g then back into natural log
            ln_mean = np.log(np.exp(mean_i) * 1e-2 / g)
            
            # Get basin adjustments if specified
            fb = _get_us23_nshm_adjustments(ln_mean, imt, ctx,
                                            self.cb14_basin_term,
                                            self.m9_basin_term)

            mean[m] = ln_mean + fb
            _set_stddevs(sig[m], tau[m], phi[m], C['sigma'], C_SINTER['tauI'])

    #: Coefficient table containing subduction interface coefficients,
    #: taken from table 4, p. 903 (only column SI), and table 6, p. 907
    #: (only columns QI, WI, TauI)
    COEFFS_SINTER = CoeffsTable(sa_damping=5, table="""\
        IMT    SI     QI      WI      tauI
        pga    0.000  0.0     0.0     0.308
        0.05   0.000  0.0     0.0     0.343
        0.10   0.000  0.0     0.0     0.403
        0.15   0.000 -0.0138  0.0286  0.367
        0.20   0.000 -0.0256  0.0352  0.328
        0.25   0.000 -0.0348  0.0403  0.289
        0.30   0.000 -0.0423  0.0445  0.280
        0.40  -0.041 -0.0541  0.0511  0.271
        0.50  -0.053 -0.0632  0.0562  0.277
        0.60  -0.103 -0.0707  0.0604  0.296
        0.70  -0.146 -0.0771  0.0639  0.313
        0.80  -0.164 -0.0825  0.0670  0.329
        0.90  -0.206 -0.0874  0.0697  0.324
        1.00  -0.239 -0.0917  0.0721  0.328
        1.25  -0.256 -0.1009  0.0772  0.339
        1.50  -0.306 -0.1083  0.0814  0.352
        2.00  -0.321 -0.1202  0.0880  0.360
        2.50  -0.337 -0.1293  0.0931  0.356
        3.00  -0.331 -0.1368  0.0972  0.338
        4.00  -0.390 -0.1486  0.1038  0.307
        5.00  -0.498 -0.1578  0.1090  0.272
        """)


class ZhaoEtAl2006SSlab(ZhaoEtAl2006Asc):
    """
    Implements GMPE developed by John X. Zhao et al and published as
    "Attenuation Relations of Strong Ground Motion in Japan Using Site
    Classification Based on Predominant Period" (2006, Bulletin of the
    Seismological Society of America, Volume 96, No. 3, pages
    898-913). This class implements the equations for 'Subduction
    Slab'. (that's why the class name ends with 'SSlab'). This class
    extends the
    :class:`openquake.hazardlib.gsim.zhao_2006.ZhaoEtAl2006Asc`
    because the equation for subduction slab is obtained from the
    equation for active shallow crust, by removing the faulting style
    term and adding subduction slab terms.
    """
    #: Supported tectonic region type is subduction interface, this means
    #: that factors FR, SS and SSL are assumed 0 in equation 1, p. 901.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB

    #: Required rupture parameters are magnitude and focal depth.
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'hypo_depth'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            # extracting dictionary of coefficients specific to required
            # intensity measure type.
            C = self.COEFFS_ASC[imt]
            C_SSLAB = self.COEFFS_SSLAB[imt]

            # to avoid singularity at 0.0 (in the calculation of the
            # slab correction term), replace 0 values with 0.1
            d = np.array(ctx.rrup)  # make a copy
            d[d == 0.0] = 0.1

            # mean value as given by equation 1, p. 901, without considering
            # faulting style and intraslab terms (that is FR, SS, SSL = 0) and
            # inter and intra event terms, plus the magnitude-squared term
            # correction factor (equation 5 p. 909)
            mean_i = _compute_magnitude_term(C, ctx.mag) +\
                _compute_distance_term(C, ctx.mag, d) +\
                _compute_focal_depth_term(C, ctx.hypo_depth) +\
                _compute_site_class_term(C, ctx.vs30) +\
                _compute_magnitude_squared_term(
                    P=C_SSLAB['PS'],
                    M=6.5,
                    Q=C_SSLAB['QS'],
                    W=C_SSLAB['WS'],
                    mag=ctx.mag) + C_SSLAB['SS'] +\
                    _compute_slab_correction_term(C_SSLAB, d)

            # Convert from cm/s**2 to g and back into natural log
            ln_mean = np.log(np.exp(mean_i) * 1e-2 / g)

            # Get basin adjustments if specified
            fb = _get_us23_nshm_adjustments(ln_mean, imt, ctx,
                                            self.cb14_basin_term,
                                            self.m9_basin_term)

            mean[m] = ln_mean + fb
            _set_stddevs(sig[m], tau[m], phi[m], C['sigma'], C_SSLAB['tauS'])

    #: Coefficient table containing subduction slab coefficients taken from
    #: table 4, p. 903 (only columns for SS and SSL), and table 6, p. 907
    #: (only columns for PS, QS, WS, TauS)
    COEFFS_SSLAB = CoeffsTable(sa_damping=5, table="""\
        IMT    SS     SSL     PS      QS       WS      tauS
        pga    2.607 -0.528   0.1392  0.1584  -0.0529  0.321
        0.05   2.764 -0.551   0.1636  0.1932  -0.0841  0.378
        0.10   2.156 -0.420   0.1690  0.2057  -0.0877  0.420
        0.15   2.161 -0.431   0.1669  0.1984  -0.0773  0.372
        0.20   1.901 -0.372   0.1631  0.1856  -0.0644  0.324
        0.25   1.814 -0.360   0.1588  0.1714  -0.0515  0.294
        0.30   2.181 -0.450   0.1544  0.1573  -0.0395  0.284
        0.40   2.432 -0.506   0.1460  0.1309  -0.0183  0.278
        0.50   2.629 -0.554   0.1381  0.1078  -0.0008  0.272
        0.60   2.702 -0.575   0.1307  0.0878   0.0136  0.285
        0.70   2.654 -0.572   0.1239  0.0705   0.0254  0.290
        0.80   2.480 -0.540   0.1176  0.0556   0.0352  0.299
        0.90   2.332 -0.522   0.1116  0.0426   0.0432  0.289
        1.00   2.233 -0.509   0.1060  0.0314   0.0498  0.286
        1.25   2.029 -0.469   0.0933  0.0093   0.0612  0.277
        1.50   1.589 -0.379   0.0821 -0.0062   0.0674  0.282
        2.00   0.966 -0.248   0.0628 -0.0235   0.0692  0.300
        2.50   0.789 -0.221   0.0465 -0.0287   0.0622  0.292
        3.00   1.037 -0.263   0.0322 -0.0261   0.0496  0.274
        4.00   0.561 -0.169   0.0083 -0.0065   0.0150  0.281
        5.00   0.225 -0.120  -0.0117  0.0246  -0.0268  0.296
        """)


class ZhaoEtAl2006SInterNSHMP2008(ZhaoEtAl2006SInter):
    """
    Extend :class:`ZhaoEtAl2006SInter` and fix hypocentral depth at 20 km
    as defined the by National Seismic Hazard Mapping Project for the 2008 US
    hazard model.

    The calculation of the total standard deviation is done considering the
    inter-event standard deviation as defined in table 5, page 903 of Zhao's
    paper.

    The class implement the equation as coded in ``subroutine zhao`` in
    ``hazSUBXnga.f`` Fotran code available at:
    http://earthquake.usgs.gov/hazards/products/conterminous/2008/software/
    """
    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.

        Call super class method with hypocentral depth fixed at 20 km
        """
        # create new rupture context to avoid changing the original one
        ctx = copy.copy(ctx)
        ctx.hypo_depth = 20.
        super().compute(ctx, imts, mean, sig, tau, phi)

    COEFFS_SINTER = CoeffsTable(sa_damping=5, table="""\
        IMT    SI     QI      WI      tauI
        pga    0.000  0.0     0.0     0.3976
        0.05   0.000  0.0     0.0     0.4437
        0.10   0.000  0.0     0.0     0.4903
        0.15   0.000 -0.0138  0.0286  0.4603
        0.20   0.000 -0.0256  0.0352  0.4233
        0.25   0.000 -0.0348  0.0403  0.3908
        0.30   0.000 -0.0423  0.0445  0.3790
        0.40  -0.041 -0.0541  0.0511  0.3897
        0.50  -0.053 -0.0632  0.0562  0.3890
        0.60  -0.103 -0.0707  0.0604  0.4014
        0.70  -0.146 -0.0771  0.0639  0.4079
        0.80  -0.164 -0.0825  0.0670  0.4183
        0.90  -0.206 -0.0874  0.0697  0.4106
        1.00  -0.239 -0.0917  0.0721  0.4101
        1.25  -0.256 -0.1009  0.0772  0.4021
        1.50  -0.306 -0.1083  0.0814  0.4076
        2.00  -0.321 -0.1202  0.0880  0.4138
        2.50  -0.337 -0.1293  0.0931  0.4108
        3.00  -0.331 -0.1368  0.0972  0.3961
        4.00  -0.390 -0.1486  0.1038  0.3821
        5.00  -0.498 -0.1578  0.1090  0.3766
        """)


class ZhaoEtAl2006SSlabNSHMP2014(ZhaoEtAl2006SSlab):
    """
    For the 2014 US National Seismic Hazard Maps the magnitude of Zhao et al.
    (2006) for the subduction inslab events is capped at magnitude Mw 7.8
    """
    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            # extracting dictionary of coefficients specific to required
            # intensity measure type.
            C = self.COEFFS_ASC[imt]
            C_SSLAB = self.COEFFS_SSLAB[imt]

            # to avoid singularity at 0.0 (in the calculation of the
            # slab correction term), replace 0 values with 0.1
            d = np.array(ctx.rrup)  # make a copy
            d[d == 0.0] = 0.1

            rup_mag = np.clip(ctx.mag, 0., 7.8)
            # mean value as given by equation 1, p. 901, without considering
            # faulting style and intraslab terms (that is FR, SS, SSL = 0) and
            # inter and intra event terms, plus the magnitude-squared term
            # correction factor (equation 5 p. 909)
            mean_i = _compute_magnitude_term(C, rup_mag) +\
                _compute_distance_term(C, rup_mag, d) +\
                _compute_focal_depth_term(C, ctx.hypo_depth) +\
                _compute_site_class_term(C, ctx.vs30) +\
                _compute_magnitude_squared_term(P=C_SSLAB['PS'], M=6.5,
                                                Q=C_SSLAB['QS'],
                                                W=C_SSLAB['WS'],
                                                mag=rup_mag) +\
                C_SSLAB['SS'] + _compute_slab_correction_term(C_SSLAB, d)

            # Convert from cm/s**2 to g and back into natural log
            ln_mean = np.log(np.exp(mean_i) * 1e-2 / g)

            # Get basin adjustments if specified
            fb = _get_us23_nshm_adjustments(ln_mean, imt, ctx,
                                            self.cb14_basin_term,
                                            self.m9_basin_term)
            mean[m] = ln_mean + fb
            _set_stddevs(sig[m], tau[m], phi[m], C['sigma'], C_SSLAB['tauS'])


# Coefficient table taken from Gail Atkinson's "White paper on
# Proposed Ground-motion Prediction Equations (GMPEs) for 2015
# National Seismic Hazard Maps" (2012, page 16).
# Values were interpolated to include all listed periods.
# MF is the linear multiplicative factor.
COEFFS_SITE_FACTORS = CoeffsTable(sa_damping=5, table="""\
    IMT    MF
    pga    0.50
    pgv    1.00
    0.05   0.44
    0.10   0.44
    0.15   0.53
    0.20   0.60
    0.25   0.72
    0.30   0.81
    0.40   1.00
    0.50   1.01
    0.60   1.02
    0.70   1.02
    0.80   1.03
    0.90   1.04
    1.00   1.04
    1.25   1.19
    1.50   1.31
    2.00   1.51
    2.50   1.34
    3.00   1.21
    4.00   1.09
    5.00   1.00
    """)


class ZhaoEtAl2006SInterCascadia(ZhaoEtAl2006SInter):
    """
    Implements the interface GMPE developed by John X. Zhao et al modified
    by the Japan/Cascadia site factors as proposed by Atkinson, G. M.
    (2012). White paper on proposed ground-motion prediction equations
    (GMPEs) for 2015 National Seismic Hazard Maps Final Version,
    Nov. 2012, 50 pp. This class extends the
    :class:`openquake.hazardlib.gsim.zhao_2006.ZhaoEtAl2006Asc`
    because the equation for subduction interface is obtained from the
    equation for active shallow crust, by removing the faulting style
    term and adding a subduction interface term.
    """
    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            # extracting dictionary of coefficients specific to required
            # intensity measure type.
            C = self.COEFFS_ASC[imt]
            C_SINTER = self.COEFFS_SINTER[imt]
            C_SF = COEFFS_SITE_FACTORS[imt]

            # mean value as given by equation 1, p. 901, without considering
            # faulting style and intraslab terms (that is FR, SS, SSL = 0) and
            # inter and intra event terms, plus the magnitude-squared term
            # correction factor (equation 5 p. 909)
            mean_i = _compute_magnitude_term(C, ctx.mag) +\
                _compute_distance_term(C, ctx.mag, ctx.rrup) +\
                _compute_focal_depth_term(C, ctx.hypo_depth) +\
                _compute_site_class_term(C, ctx.vs30) + \
                _compute_magnitude_squared_term(P=0.0, M=6.3,
                                                Q=C_SINTER['QI'],
                                                W=C_SINTER['WI'],
                                                mag=ctx.mag) + C_SINTER['SI']

            # multiply by site factor to "convert" Japan values to Cascadia
            # values then convert from cm/s**2 to g
            ln_mean = np.log((np.exp(mean_i) * C_SF["MF"]) * 1e-2 / g)

            # Get basin adjustments if specified
            fb = _get_us23_nshm_adjustments(ln_mean, imt, ctx,
                                            self.cb14_basin_term,
                                            self.m9_basin_term)
            
            mean[m] = ln_mean + fb            
            _set_stddevs(sig[m], tau[m], phi[m], C['sigma'], C_SINTER['tauI'])


class ZhaoEtAl2006SSlabCascadia(ZhaoEtAl2006SSlab):
    """
    Implements GMPE developed by John X. Zhao et al modified
    by the Japan/Cascadia site factors as proposed by Atkinson, G. M.
    (2012). White paper on proposed ground-motion prediction equations
    (GMPEs) for 2015 National Seismic Hazard Maps Final Version,
    Nov. 2012, 50 pp. This class extends the
    :class:`openquake.hazardlib.gsim.zhao_2006.ZhaoEtAl2006Asc`
    because the equation for subduction slab is obtained from the
    equation for active shallow crust, by removing the faulting style
    term and adding subduction slab terms.
    """

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            # extracting dictionary of coefficients specific to required
            # intensity measure type.
            C = self.COEFFS_ASC[imt]
            C_SSLAB = self.COEFFS_SSLAB[imt]
            C_SF = COEFFS_SITE_FACTORS[imt]

            # to avoid singularity at 0.0 (in the calculation of the
            # slab correction term), replace 0 values with 0.1
            d = np.array(ctx.rrup)  # make a copy
            d[d == 0.0] = 0.1

            # mean value as given by equation 1, p. 901, without considering
            # faulting style and intraslab terms (that is FR, SS, SSL = 0) and
            # inter and intra event terms, plus the magnitude-squared term
            # correction factor (equation 5 p. 909)
            mean_i = _compute_magnitude_term(C, ctx.mag) +\
                _compute_distance_term(C, ctx.mag, d) +\
                _compute_focal_depth_term(C, ctx.hypo_depth) +\
                _compute_site_class_term(C, ctx.vs30) +\
                _compute_magnitude_squared_term(P=C_SSLAB['PS'], M=6.5,
                                                Q=C_SSLAB['QS'],
                                                W=C_SSLAB['WS'],
                                                mag=ctx.mag) +\
                C_SSLAB['SS'] + _compute_slab_correction_term(C_SSLAB, d)

            # multiply by site factor to "convert" Japan values to Cascadia
            # values then convert from cm/s**2 to g and back into natural log
            ln_mean = np.log((np.exp(mean_i) * C_SF["MF"]) * 1e-2 / g)

            # Get basin adjustments if specified
            fb = _get_us23_nshm_adjustments(ln_mean, imt, ctx,
                                            self.cb14_basin_term,
                                            self.m9_basin_term)
            mean[m] = ln_mean + fb
            _set_stddevs(sig[m], tau[m], phi[m], C['sigma'], C_SSLAB['tauS'])


class ZhaoEtAl2006AscSGS(ZhaoEtAl2006Asc):
    """
    This class extends the original base class
    :class:`openquake.hazardlib.gsim.zhao_2006.ZhaoEtAl2006Asc`
    by introducing a distance filter for the near field, as implemented
    by SGS for the national PSHA model for Saudi Arabia.
    """

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        Using a minimum distance of 5km for the calculation.
        """
        ctx = copy.deepcopy(ctx)
        ctx.rrup[ctx.rrup <= 5.] = 5.
        super().compute(ctx, imts, mean, sig, tau, phi)
