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
Module
:mod:`openquake.hazardlib.gsim.kanno_2006`
exports
:class:`Kanno2006Shallow`
:class:`Kanno2006Deep`
"""
import numpy as np
from scipy.constants import g

from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable

LOG10 = np.log(10)

#: "coefficient e_1 = 0.5 was selected for all periods in the present
#: study." (p. 881)
CONSTS = {'e': 0.5}


def _compute_mag_dist_terms(ctx, coeffs):
    """
    Compute equation (5) and implcitly equation (6):

    ``log(pre) = c + a*M + b*X - log(X + d*10^(e*M)) + epsilon``
    """
    log_pre = coeffs['c'] + coeffs['a']*ctx.mag + coeffs['b']*ctx.rrup \
        - np.log10(ctx.rrup + coeffs['d']*10**(coeffs['e']*ctx.mag))

    return log_pre


def _compute_site_amplification(ctx, coeffs):
    """
    Compute equation (8):

    ``G = p*log(VS30) + q``
    """
    return coeffs['p']*np.log10(ctx.vs30) + coeffs['q']


class Kanno2006Shallow(GMPE):
    # pylint: disable=too-few-public-methods
    """
    Implements GMPE of Kanno et al. (2006) for shallow events based on data
    predominantly from Japan.

    Note that "both crustal and subduction interface events fall into the
    category of shallow events" (p. 883) where "shallow" is defined as "focal
    depth of 30 km or less" (p. 895).

    Verification of mean value data was performed against a test vector kindly
    provided by the lead author.

    **Reference**

    Page number citations in this documentation refer to:

    Kanno, T., Narita, A., Morikawa, N., Fujiwara, H., and Fukushima, Y.
    (2006). A new attenuation relation for strong ground motion in Japan based
    on recorded data. *Bull. Seism. Soc. Am.* 96(3):879–897.
    """

    #: This model is generally considered to be intended for subduction
    #: regions, but the authors do not constrain the type of event, only the
    #: depth: "both crustal and subduction interface events fall into the
    #: category of shallow events." (p. 883)
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    #: "regression coefficients for the base model in equations (5) and (6)
    #: for PGA , PGV , and 5% damped response spectral acceleration are given"
    #: (p. 883)
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    #: "The peak value is the peak square root of the sum of squares
    #: of two orthogonal horizontal components in the time domain" (p. 880)
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.PEAK_SRSS_HORIZONTAL

    #: Although interevent and intraevent residuals are separately discussed
    #: in the context of focal depth and site conditions, only the total
    #: standard deviation is tabulated.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    DEFINED_FOR_REFERENCE_VELOCITY = 800

    #: "Coefficients p and q were derived by regression analysis on the
    #: residuals averaged at intervals of every 100 m/sec in AVS30." (p. 884)
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Sole required rupture parameter is magnitude; faulting style is not
    #: addressed.
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: "The source distance is the closest distance from a fault plane to the
    #: observation site and is the hypocentral distance in the case of
    #: earthquakes for which the fault model is not available." (p. 880)
    REQUIRES_DISTANCES = {'rrup'}

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        # pylint: disable=too-many-arguments
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for specification of input and result values.

        Implements the following equations:

        Equation (5) on p. 881 predicts ground motion for shallow events
        (depth <= 30 km):

        ``log(pre) = a*M + b*X - log(X + d*10^(e*M)) + c + epsilon``

        "where pre is the predicted PGA (cm/sec^2), PGV (cm/sec), or 5%
        damped response spectral acceleration (cm/sec^2)" (p. 883) and a,
        b, c and d are tabulated regression coefficients. Note that
        subscripts on the regression coeffients have been dropped -
        subscript `1` denoted "shallow" while subscript `2` denoted "deep"
        - so that the "deep" model of equation (6) can be implemented trivally
        by changing coefficients and setting d = 0.

        Equation (8) on p. 883 gives the model used for site amplitfication:

        ``G = p*log(VS30) + q``

        Where p and q are tabulated regression coefficients.

        Equation (9) on p. 884 for the ground motion at a given site:

        ``log(pre_G) = log(pre) + G``

        No adjustment of epsilon is made as a function of VS30.

        Note finally that "log represents log_10 in the present study"
        (p. 880).
        """
        for m, imt in enumerate(imts):
            # merge coefficients
            coeffs = CONSTS.copy()
            cb = self.COEFFS_BASE[imt]
            cs = self.COEFFS_SITE[imt]
            for n in cb.dtype.names:
                coeffs[n] = cb[n]
            for n in cs.dtype.names:
                coeffs[n] = cs[n]

            # compute bedrock motion, equation (5)
            log_mean = _compute_mag_dist_terms(ctx, coeffs)

            # make site corrections, equation (9)
            log_mean += _compute_site_amplification(ctx, coeffs)

            # retrieve standard deviations
            log_stddev = coeffs['epsilon']

            # convert from common to natural logarithm
            mean[m] = log_mean * LOG10
            sig[m] = log_stddev * LOG10

            # convert accelerations from cm/s^2 to g
            if not imt.string == "PGV":
                mean[m] -= np.log(100*g)

    #: Coefficients obtained from author via personal communcation with
    #: slightly more precision than Table 3, p. 884.
    COEFFS_BASE = CoeffsTable(sa_damping=5., table="""\
      IMT      a         b       c        d  epsilon
      pga  0.556 -0.003070  0.2560  0.00547    0.366
     0.05  0.540 -0.003540  0.4790  0.00611    0.374
     0.06  0.536 -0.003720  0.5660  0.00648    0.379
     0.07  0.528 -0.003850  0.6690  0.00664    0.384
     0.08  0.524 -0.003970  0.7470  0.00687    0.393
     0.09  0.523 -0.004050  0.7950  0.00710    0.399
      0.1  0.520 -0.004090  0.8470  0.00732    0.404
     0.11  0.501 -0.003990  0.9600  0.00607    0.404
     0.12  0.510 -0.003970  0.9280  0.00619    0.404
     0.13  0.514 -0.003930  0.9140  0.00616    0.403
     0.15  0.518 -0.003800  0.8920  0.00595    0.405
     0.17  0.525 -0.003650  0.8440  0.00557    0.406
      0.2  0.535 -0.003390  0.7610  0.00525    0.401
     0.22  0.535 -0.003190  0.7340  0.00482    0.399
     0.25  0.541 -0.002930  0.6590  0.00436    0.399
      0.3  0.556 -0.002580  0.5050  0.00389    0.392
     0.35  0.561 -0.002370  0.4210  0.00359    0.398
      0.4  0.577 -0.002120  0.2620  0.00329    0.404
     0.45  0.589 -0.001890  0.1290  0.00297    0.405
      0.5  0.593 -0.001610  0.0375  0.00216    0.405
      0.6  0.623 -0.001390 -0.2220  0.00250    0.409
      0.7  0.634 -0.001180 -0.3700  0.00215    0.413
      0.8  0.651 -0.001070 -0.5440  0.00197    0.408
      0.9  0.681 -0.000942 -0.8030  0.00187    0.407
        1  0.710 -0.000878 -1.0400  0.00208    0.406
      1.1  0.722 -0.000737 -1.1900  0.00176    0.405
      1.2  0.732 -0.000614 -1.3200  0.00142    0.405
      1.3  0.742 -0.000554 -1.4400  0.00140    0.405
      1.5  0.773 -0.000518 -1.7000  0.00167    0.398
      1.7  0.791 -0.000464 -1.8900  0.00194    0.391
        2  0.804 -0.000356 -2.0800  0.00195    0.387
      2.2  0.821 -0.000372 -2.2400  0.00216    0.384
      2.5  0.844 -0.000308 -2.4600  0.00228    0.382
        3  0.862 -0.000197 -2.7200  0.00207    0.378
      3.5  0.895 -0.000348 -2.9900  0.00322    0.374
        4  0.921 -0.000512 -3.2100  0.00446    0.375
      4.5  0.944 -0.000703 -3.3900  0.00639    0.377
        5  0.916 -0.000360 -3.3500  0.00303    0.377
      pgv  0.702 -0.000925 -1.9300  0.00217    0.321
    """)

    #: Coefficients obtained from author via personal communcation with
    #: slightly more precision Table 5, p. 888.
    COEFFS_SITE = CoeffsTable(sa_damping=5., table="""\
      IMT       p       q
      pga -0.5514  1.3490
     0.05 -0.3244  0.7962
     0.06 -0.2614  0.6450
     0.07 -0.2418  0.5974
     0.08 -0.2616  0.6417
     0.09 -0.2929  0.7154
      0.1 -0.3199  0.7776
     0.11 -0.3477  0.8406
     0.12 -0.3900  0.9399
     0.13 -0.4307  1.0350
     0.15 -0.5308  1.2760
     0.17 -0.6113  1.4680
      0.2 -0.6831  1.6470
     0.22 -0.7184  1.7370
     0.25 -0.7499  1.8200
      0.3 -0.8045  1.9630
     0.35 -0.8518  2.0870
      0.4 -0.8676  2.1310
     0.45 -0.8851  2.1760
      0.5 -0.9094  2.2470
      0.6 -0.9238  2.2970
      0.7 -0.9622  2.4070
      0.8 -0.9759  2.4570
      0.9 -0.9685  2.4390
        1 -0.9264  2.3220
      1.1 -0.9176  2.2960
      1.2 -0.9062  2.2630
      1.3 -0.8825  2.2020
      1.5 -0.8531  2.1210
      1.7 -0.8294  2.0590
        2 -0.7756  1.9210
      2.2 -0.7567  1.8750
      2.5 -0.7244  1.7960
        3 -0.6845  1.6990
      3.5 -0.6597  1.6390
        4 -0.6182  1.5370
      4.5 -0.6035  1.4990
        5 -0.5861  1.4560
      pgv -0.7057  1.7650
    """)


class Kanno2006Deep(Kanno2006Shallow):
    # pylint: disable=too-few-public-methods
    """
    Implements GMPE of Kanno et al. (2006) for deep events based on data
    predominantly from Japan.

    Deep events are defined as having "(focal depth of more than 30 km)"
    (p. 895).
    """

    #: Although "only a slight difference can be seen between [shallow]
    #: crustal and subduction interface earthquakes ... the focal depth of the
    #: two types of events is comparatively shallower than that of slab
    #: events." (p. 881)
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTRASLAB

    #: Coefficients obtained from author via personal communcation with
    #: slightly more precision than Table 4, p. 884.
    COEFFS_BASE = CoeffsTable(sa_damping=5., table="""\
      IMT      a        b       c  d  epsilon
      pga  0.409 -0.00389  1.5600  0    0.397
     0.05  0.394 -0.00404  1.7600  0    0.418
     0.06  0.388 -0.00410  1.8600  0    0.431
     0.07  0.382 -0.00418  1.9600  0    0.445
     0.08  0.379 -0.00422  2.0300  0    0.453
     0.09  0.377 -0.00428  2.0800  0    0.458
      0.1  0.377 -0.00431  2.1200  0    0.461
     0.11  0.377 -0.00435  2.1400  0    0.462
     0.12  0.381 -0.00437  2.1400  0    0.461
     0.13  0.384 -0.00439  2.1300  0    0.459
     0.15  0.388 -0.00436  2.1200  0    0.455
     0.17  0.395 -0.00433  2.0800  0    0.447
      0.2  0.401 -0.00422  2.0200  0    0.438
     0.22  0.403 -0.00413  1.9900  0    0.433
     0.25  0.414 -0.00401  1.8800  0    0.424
      0.3  0.425 -0.00378  1.7500  0    0.415
     0.35  0.434 -0.00357  1.6200  0    0.411
      0.4  0.445 -0.00338  1.4900  0    0.407
     0.45  0.459 -0.00319  1.3300  0    0.406
      0.5  0.471 -0.00303  1.1900  0    0.404
      0.6  0.491 -0.00283  0.9500  0    0.400
      0.7  0.512 -0.00262  0.7180  0    0.401
      0.8  0.534 -0.00245  0.4860  0    0.402
      0.9  0.555 -0.00234  0.2730  0    0.404
        1  0.574 -0.00223  0.0794  0    0.405
      1.1  0.590 -0.00216 -0.0846  0    0.407
      1.2  0.604 -0.00211 -0.2400  0    0.407
      1.3  0.619 -0.00204 -0.3950  0    0.405
      1.5  0.640 -0.00195 -0.6320  0    0.405
      1.7  0.655 -0.00182 -0.8310  0    0.403
        2  0.680 -0.00171 -1.1200  0    0.399
      2.2  0.692 -0.00167 -1.2700  0    0.396
      2.5  0.711 -0.00167 -1.4800  0    0.393
        3  0.729 -0.00169 -1.7200  0    0.387
      3.5  0.748 -0.00167 -1.9700  0    0.377
        4  0.769 -0.00163 -2.2200  0    0.368
      4.5  0.791 -0.00163 -2.4500  0    0.359
        5  0.818 -0.00167 -2.7000  0    0.346
      pgv  0.552 -0.00324 -0.5710  0    0.356
   """)


# class Kanno2006ShallowNortheastJapan(Kanno2006Shallow):
#    # pylint: disable=too-few-public-methods
#    """
#    Implements GMPE of Kanno et al. (2006) for shallow events in
#    northeastern Japan.
#
#    > Intermediate and deep earthquakes occurring in the Pacific
#    > plate usually generate anomalous seismic intensity in
#    > Japan’s northeast. This anomalous seismic intensity is a
#    > large-scale abnormal distribution of relatively larger ground
#    > motions that cannot be explained by source or site effects.
#    > These anomalous larger ground motions have been observed
#    > more commonly in fore-arc side (south or east of volcanoes)
#    > than in back-arc side (north or west of volcanoes; Figure
#    > 10a). This phenomenon is explained by a unique Q structure
#    > beneath the island-arc region shown in Figure 10c (Utsu,
#    > 1967). Namely, seismic waves to a fore-arc propagate
#    > shorter in low-Q zone than those to a back-arc. Actually, a
#    > considerable contrast in Q is expected; it is about 300 or less
#    > and 1500 or more for low Q and high Q, respectively
#
#    """
#
#    #: "D is the focal depth (km)" is used to discriminate between shallow
#    #: and deep events in equations (5) and (6) on p. 881 but it is only in
#    #: the application to northeast Japan via equation (10) that it actually
#    #: becomes and input parameter to ground motion prediction.
#    REQUIRES_DISTANCES = set(('rrup', 'hypo_depth'))
#
#    #: Since "R_tr is the shortest distance from the observation site to the
#    #: Kuril, Japan, and Izu-Bonin trenches" this attenuation model is not
#    #: trivially adaptable to other regions.
#    REQUIRES_SITES_PARAMETERS = set(('vs30', 'lon', 'lat'))
#
#    #: There aren't even plots of results for northeast Japan in the paper
#    #: so results cannot be verified without a dataset from the authors.
#    non_verified = True
#
#    def compute(self, ctx, imts, mean, sig, tau, phi):
#        # pylint: disable=too-many-arguments
#        """
#        See :meth:`superclass method
#        <.base.GroundShakingIntensityModel.compute>`
#        for specification of input and result values.
#
#        Implements equation (10) on p. 883 which is a depth correction for
#        northeastern Japan:
#
#        ``A = log(obs/pre) = (alpha*R_tr + beta)*(D - 30)``
#
#        Where alpha and beta are tabulated regression coefficients and R_tr is
#        the "shortest distance from the observationsite to the Kuril, Japan,
#        and Izu-Bonin trenches" (p. 887).
#
#        Since the "procedure is the same as that of Morikawa et al. (2003),"
#        (p. 887) who in turn "proposed additional correction terms for the
#        attenuation relations given by Si and Midorikawa (1999)" (p. 887),
#        R_tr is computed using the `_get_min_distance_to_sub_trench()` method
#        of `:mod:openquake.hazardlib.gsim.si_midorikawa_1999`.
#
#        Equation (11) on p. 884 gives the resulting corrected ground motion:
#
#        ``log(pre_A) = log(pre) + A``
#        """
#        # compute mean and standard deviations as per parent class
#        parent = super()
#        ln_mean, [ln_stddevs] = parent.compute(
#            ctx, imts, mean, sig, tau, phi)
#
#        # compute site corrections, equation (9)
#        coeffs = self.COEFFS_NORTHEAST[imt].copy()
#        log_amp = self._compute_depth_correction(ctx, coeffs)
#
#        # convert correction factor from common to natural logarithm
#        ln_mean += log_amp*np.log(10.0)
#
#        return ln_mean, [ln_stddevs]
#
#    def _compute_depth_correction(self, ctx, coeffs):
#        """
#        Compute equation (10):
#
#        ``A = log(obs/pre) = (alpha*R_tr + beta)*(D - 30)``
#        """
#
#        r_trench = _get_min_distance_to_sub_trench(ctx.lon, ctx.lat)
#
#        log_amp = (coeffs['alpha']*r_trench + coeffs['beta']) * \
#            (ctx.hypo_depth - self.REF_DEPTH_KM)
#
#        return log_amp
#
#    #: The choice of reference depth is not discussed in detail; it may
#    #: just be a coincidence that it is the same depth as is used to
#    #: distinguish between shallow and deep events.
#    REF_DEPTH_KM = 30
#
#    #: Coefficients obtained from author via personal communcation with
#    #: slightly more precision than Table 6, p. 890.
#    COEFFS_NORTHEAST = CoeffsTable(sa_damping=5., table="""\
#      IMT         alpha      beta
#      pga -6.725997e-05  0.020897
#     0.05 -7.775639e-05  0.023664
#     0.06 -8.016678e-05  0.024170
#     0.07 -8.150424e-05  0.024712
#     0.08 -8.220022e-05  0.025008
#     0.09 -8.263188e-05  0.025490
#      0.1 -8.231173e-05  0.025395
#     0.11 -8.181056e-05  0.025583
#     0.12 -8.082911e-05  0.025293
#     0.13 -7.985925e-05  0.025125
#     0.15 -7.987062e-05  0.025144
#     0.17 -7.532868e-05  0.023841
#      0.2 -6.988024e-05  0.022275
#     0.22 -6.535384e-05  0.020912
#     0.25 -6.071708e-05  0.019593
#      0.3 -5.468015e-05  0.017811
#     0.35 -5.055145e-05  0.016665
#      0.4 -4.619140e-05  0.015375
#     0.45 -4.619738e-05  0.015126
#      0.5 -4.411651e-05  0.014360
#      0.6 -3.601382e-05  0.011902
#      0.7 -2.884134e-05  0.009483
#      0.8 -2.501885e-05  0.008191
#      0.9 -2.161131e-05  0.007350
#        1 -2.180311e-05  0.007611
#      1.1 -1.952808e-05  0.007077
#      1.2 -1.631392e-05  0.006516
#      1.3 -1.377592e-05  0.005855
#      1.5 -1.179873e-05  0.005521
#      1.7 -8.530805e-06  0.004798
#        2 -4.534562e-06  0.004054
#      2.2 -1.184015e-06  0.003108
#      2.5  2.595425e-06  0.002148
#        3  3.012975e-06  0.002009
#      3.5  2.486900e-06  0.002065
#        4  9.281249e-07  0.002269
#      4.5 -2.133004e-06  0.002947
#        5 -4.610887e-06  0.003442
#      pgv -1.937499e-05  0.007243
#    """)
#
#
# class Kanno2006DeepNortheastJapan(Kanno2006Deep,
#                                  Kanno2006ShallowNortheastJapan):
#    # pylint: disable=too-few-public-methods
#    """
#    Implements GMPE of Kanno et al. (2006) for deep events in northeastern
#    Japan.
#
#    See :class:`Kanno2006Deep` and :class:`Kanno2006ShallowNortheastJapan`.
#
#    """
#    pass
