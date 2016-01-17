# -*- coding: utf-8 -*-
# The Hazard Library
# Copyright (C) 2012-2014, GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Module
:mod:`openquake.hazardlib.gsim.kanno_2006`
exports
:class:`Kanno2006Shallow`
:class:`Kanno2006Deep`
"""
# :class:`Kanno2006ShallowNortheastJapan`
# :class:`Kanno2006DeepNortheastJapan`

from __future__ import division
import warnings
import numpy as np
from scipy.constants import g
from openquake.hazardlib import const, imt
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
# from openquake.hazardlib.gsim.si_midorikawa_1999 \
#    import _get_min_distance_to_sub_trench


class Kanno2006Shallow(GMPE):
    # pylint: disable=too-few-public-methods
    """
    Implements GMPE of Kanno et al. (2006) for shallow events based on data
    predominantly from Japan.

    Note that "both crustal and subduction interface events fall into the
    category of shallow events" (p. 883) where "shallow" is defined as "focal
    depth of 30 km or less" (p. 895).

    Verification of mean value data was done by digitizing Figures 4 and 5
    using http://arohatgi.info/WebPlotDigitizer/ app/. The maximum error was
    15% while the average error was 3-4%.

    Page number citations in this documentation refer to:

    Kanno, T., Narita, A., Morikawa, N., Fujiwara, H., and Fukushima, Y.
    (2006). A new attenuation relation for strong ground motion in Japan based
    on recorded data. Bull. Seism. Soc. Am. 96(3):879–897.
    """

    #: This model is generally considered to be intended for subduction
    #: regions, but the authors do not constrain the type of event, only the
    #: depth: "both crustal and subduction interface events fall into the
    #: category of shallow events." (p. 883)
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    #: "regression coefficients for the base model in equations (5) and (6)
    #: for PGA , PGV , and 5% damped response spectral acceleration are given"
    #: (p. 883)
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([imt.PGA, imt.PGV, imt.SA])

    #: "The peak value is the peak square root of the sum of squares
    #: of two orthogonal horizontal components in the time domain" (p. 880)
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.PEAK_SRSS_HORIZONTAL

    #: Although interevent and intraevent residuals are separately discussed
    #: in the context of focal depth and site conditions, only the total
    #: standard deviation is tabulated.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([const.StdDev.TOTAL])

    #: "Coefficients p and q were derived by regression analysis on the
    #: residuals averaged at intervals of every 100 m/sec in AVS30." (p. 884)
    REQUIRES_SITES_PARAMETERS = set(('vs30',))

    #: Sole required rupture parameter is magnitude; faulting style is not
    #: addressed.
    REQUIRES_RUPTURE_PARAMETERS = set(('mag',))

    #: "The source distance is the closest distance from a fault plane to the
    #: observation site and is the hypocentral distance in the case of
    #: earthquakes for which the fault model is not available." (p. 880)
    REQUIRES_DISTANCES = set(('rrup',))

    def get_mean_and_stddevs(self, sites, rup, dists, im_type, stddev_types):
        # pylint: disable=too-many-arguments
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
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

        assert im_type.__class__ in self.DEFINED_FOR_INTENSITY_MEASURE_TYPES

        # obtain coefficients for required intensity measure type (IMT)
        coeffs = self.COEFFS_BASE[im_type].copy()
        coeffs.update(self.COEFFS_SITE[im_type])

        # obtain IMT-independent coefficients
        coeffs.update(self.CONSTS)

        # raise warning outside applicable range
        is_valid = ~((dists.rrup < coeffs['R_valid']) &
                     (rup.mag > coeffs['M_valid']))
        if not is_valid.all():
            warnings.warn('%s used outside applicable range for M=%g at %g km'
                          % (self.__class__.__name__,
                             rup.mag, dists.rrup[is_valid][0]))

        # compute bedrock motion, equation (5)
        log_mean = self._compute_mag_dist_terms(rup, dists, coeffs)

        # make site corrections, equation (9)
        log_mean += self._compute_site_amplification(sites, coeffs)

        # retrieve standard deviations
        log_stddevs = self._get_stddevs(coeffs, stddev_types)

        # convert from common to natural logarithm
        ln_mean = log_mean*np.log(10)
        ln_stddevs = log_stddevs*np.log(10)

        # convert accelerations from cm/s^2 to g
        if im_type.__class__.__name__ != 'PGV':
            ln_mean -= np.log(100*g)

        return ln_mean, [ln_stddevs]

    def _compute_mag_dist_terms(self, rup, dists, coeffs):
        # pylint: disable=no-self-use
        """
        Compute equation (5) and implcitly equation (6):

        ``log(pre) = c + a*M + b*X - log(X + d*10^(e*M)) + epsilon``
        """

        log_pre = coeffs['c'] + coeffs['a']*rup.mag + coeffs['b']*dists.rrup \
            - np.log10(dists.rrup + coeffs['d']*10**(coeffs['e']*rup.mag))

        return log_pre

    def _compute_site_amplification(self, sites, coeffs):
        # pylint: disable=no-self-use
        """
        Compute equation (8):

        ``G = p*log(VS30) + q``
        """

        return coeffs['p']*np.log10(sites.vs30) + coeffs['q']

    def _get_stddevs(self, coeffs, stddev_types):
        """
        Equation (11) on p. 207 for total standard error at a given site:

        ``σ{ln(ε_site)} = sqrt(σ{ln(ε_br)}**2 + σ{ln(δ_site)}**2)``
        """
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES

        return coeffs['epsilon']

    #: Coefficients taken from Table 3, p. 884.
    COEFFS_BASE = CoeffsTable(sa_damping=5., table="""\
      IMT     a       b     c       d  epsilon
      pga  0.56 -0.0031  0.26  0.0055     0.37
     0.05  0.54 -0.0035  0.48  0.0061     0.37
     0.06  0.54 -0.0037  0.57  0.0065     0.38
     0.07  0.53 -0.0039  0.67  0.0066     0.38
     0.08  0.52 -0.0040  0.75  0.0069     0.39
     0.09  0.52 -0.0041  0.80  0.0071     0.40
      0.1  0.52 -0.0041  0.85  0.0073     0.40
     0.11  0.50 -0.0040  0.96  0.0061     0.40
     0.12  0.51 -0.0040  0.93  0.0062     0.40
     0.13  0.51 -0.0039  0.91  0.0062     0.40
     0.15  0.52 -0.0038  0.89  0.0060     0.41
     0.17  0.53 -0.0037  0.84  0.0056     0.41
      0.2  0.54 -0.0034  0.76  0.0053     0.40
     0.22  0.54 -0.0032  0.73  0.0048     0.40
     0.25  0.54 -0.0029  0.66  0.0044     0.40
      0.3  0.56 -0.0026  0.51  0.0039     0.39
     0.35  0.56 -0.0024  0.42  0.0036     0.40
      0.4  0.58 -0.0021  0.26  0.0033     0.40
     0.45  0.59 -0.0019  0.13  0.0030     0.41
      0.5  0.59 -0.0016  0.04  0.0022     0.41
      0.6  0.62 -0.0014 -0.22  0.0025     0.41
      0.7  0.63 -0.0012 -0.37  0.0022     0.41
      0.8  0.65 -0.0011 -0.54  0.0020     0.41
      0.9  0.68 -0.0009 -0.80  0.0019     0.41
        1  0.71 -0.0009 -1.04  0.0021     0.41
      1.1  0.72 -0.0007 -1.19  0.0018     0.41
      1.2  0.73 -0.0006 -1.32  0.0014     0.41
      1.3  0.74 -0.0006 -1.44  0.0014     0.41
      1.5  0.77 -0.0005 -1.70  0.0017     0.40
      1.7  0.79 -0.0005 -1.89  0.0019     0.39
        2  0.80 -0.0004 -2.08  0.0020     0.39
      2.2  0.82 -0.0004 -2.24  0.0022     0.38
      2.5  0.84 -0.0003 -2.46  0.0023     0.38
        3  0.86 -0.0002 -2.72  0.0021     0.38
      3.5  0.90 -0.0003 -2.99  0.0032     0.37
        4  0.92 -0.0005 -3.21  0.0045     0.38
      4.5  0.94 -0.0007 -3.39  0.0064     0.38
        5  0.92 -0.0004 -3.35  0.0030     0.38
      pgv  0.70 -0.0009 -1.93  0.0022     0.32
    """)

    #: Coefficients taken from Table 5, p. 888.
    COEFFS_SITE = CoeffsTable(sa_damping=5., table="""\
      IMT     p     q
      pga -0.55  1.35
     0.05 -0.32  0.80
     0.06 -0.26  0.65
     0.07 -0.24  0.60
     0.08 -0.26  0.64
     0.09 -0.29  0.72
      0.1 -0.32  0.78
     0.11 -0.35  0.84
     0.12 -0.39  0.94
     0.13 -0.43  1.04
     0.15 -0.53  1.28
     0.17 -0.61  1.47
      0.2 -0.68  1.65
     0.22 -0.72  1.74
     0.25 -0.75  1.82
      0.3 -0.80  1.96
     0.35 -0.85  2.09
      0.4 -0.87  2.13
     0.45 -0.89  2.18
      0.5 -0.91  2.25
      0.6 -0.92  2.30
      0.7 -0.96  2.41
      0.8 -0.98  2.46
      0.9 -0.97  2.44
        1 -0.93  2.32
      1.1 -0.92  2.30
      1.2 -0.91  2.26
      1.3 -0.88  2.20
      1.5 -0.85  2.12
      1.7 -0.83  2.06
        2 -0.78  1.92
      2.2 -0.76  1.88
      2.5 -0.72  1.80
        3 -0.68  1.70
      3.5 -0.66  1.64
        4 -0.62  1.54
      4.5 -0.60  1.50
        5 -0.59  1.46
      pgv -0.71  1.77
    """)

    #: "coefficient e_1 = 0.5 was selected for all periods in the present
    #: study." (p. 881)
    #: "the region within several tens of kilometers from the subduction
    #: interface of a large magnitude event is out of the applicable range,
    #: [so] predicted values for M w + 8.0 and a distance of less than 20 km
    #: are indicated by dotted lines in Figure 4". (p. 883)
    CONSTS = {
        'e': 0.5,
        'M_valid': 8.,
        'R_valid': 20.,
    }


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

    #: Coefficients taken from Table 4, p. 884.
    COEFFS_BASE = CoeffsTable(sa_damping=5., table="""\
      IMT     a       b     c  d  epsilon
      pga  0.41 -0.0039  1.56  0     0.40
     0.05  0.39 -0.0040  1.76  0     0.42
     0.06  0.39 -0.0041  1.86  0     0.43
     0.07  0.38 -0.0042  1.96  0     0.45
     0.08  0.38 -0.0042  2.03  0     0.45
     0.09  0.38 -0.0043  2.08  0     0.46
      0.1  0.38 -0.0043  2.12  0     0.46
     0.11  0.38 -0.0044  2.14  0     0.46
     0.12  0.38 -0.0044  2.14  0     0.46
     0.13  0.38 -0.0044  2.13  0     0.46
     0.15  0.39 -0.0044  2.12  0     0.46
     0.17  0.40 -0.0043  2.08  0     0.45
      0.2  0.40 -0.0042  2.02  0     0.44
     0.22  0.40 -0.0041  1.99  0     0.43
     0.25  0.41 -0.0040  1.88  0     0.42
      0.3  0.43 -0.0038  1.75  0     0.42
     0.35  0.43 -0.0036  1.62  0     0.41
      0.4  0.45 -0.0034  1.49  0     0.41
     0.45  0.46 -0.0032  1.33  0     0.41
      0.5  0.47 -0.0030  1.19  0     0.40
      0.6  0.49 -0.0028  0.95  0     0.40
      0.7  0.51 -0.0026  0.72  0     0.40
      0.8  0.53 -0.0025  0.49  0     0.40
      0.9  0.56 -0.0023  0.27  0     0.40
        1  0.57 -0.0022  0.08  0     0.41
      1.1  0.59 -0.0022 -0.08  0     0.41
      1.2  0.60 -0.0021 -0.24  0     0.41
      1.3  0.62 -0.0020 -0.40  0     0.41
      1.5  0.64 -0.0020 -0.63  0     0.41
      1.7  0.66 -0.0018 -0.83  0     0.40
        2  0.68 -0.0017 -1.12  0     0.40
      2.2  0.69 -0.0017 -1.27  0     0.40
      2.5  0.71 -0.0017 -1.48  0     0.39
        3  0.73 -0.0017 -1.72  0     0.39
      3.5  0.75 -0.0017 -1.97  0     0.38
        4  0.77 -0.0016 -2.22  0     0.37
      4.5  0.79 -0.0016 -2.45  0     0.36
        5  0.82 -0.0017 -2.70  0     0.35
      pgv  0.55 -0.0032 -0.57  0     0.36
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
#    REQUIRES_SITES_PARAMETERS = set(('vs30', 'lons', 'lats'))
#
#    #: There aren't even plots of results for northeast Japan in the paper
#    #: so results cannot be verified without a dataset from the authors.
#    non_verified = True
#
#    def get_mean_and_stddevs(self, sites, rup, dists, im_type, stddev_types):
#        # pylint: disable=too-many-arguments
#        """
#        See :meth:`superclass method
#        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
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
#        parent = super(Kanno2006ShallowNortheastJapan, self)
#        ln_mean, [ln_stddevs] = parent.get_mean_and_stddevs(
#            sites, rup, dists, im_type, stddev_types)
#
#        # compute site corrections, equation (9)
#        coeffs = self.COEFFS_NORTHEAST[im_type].copy()
#        log_amp = self._compute_depth_correction(sites, rup, coeffs)
#
#        # convert correction factor from common to natural logarithm
#        ln_mean += log_amp*np.log(10.0)
#
#        return ln_mean, [ln_stddevs]
#
#    def _compute_depth_correction(self, sites, rup, coeffs):
#        """
#        Compute equation (10):
#
#        ``A = log(obs/pre) = (alpha*R_tr + beta)*(D - 30)``
#        """
#
#        r_trench = _get_min_distance_to_sub_trench(sites.lons, sites.lats)
#
#        log_amp = (coeffs['alpha']*r_trench + coeffs['beta']) * \
#            (rup.hypo_depth - self.REF_DEPTH_KM)
#
#        return log_amp
#
#    #: The choice of reference depth is not discussed in detail; it may
#    #: just be a coincidence that it is the same depth as is used to
#    #: distinguish between shallow and deep events.
#    REF_DEPTH_KM = 30
#
#    #: Coefficients taken from Table 2(b), p. 203.
#    COEFFS_NORTHEAST = CoeffsTable(sa_damping=5., table="""\
#     IMT     alpha    beta
#     pga -6.73e-05  0.0209
#    0.05 -7.78e-05  0.0237
#    0.06 -8.02e-05  0.0242
#    0.07 -8.15e-05  0.0247
#    0.08 -8.22e-05   0.025
#    0.09 -8.26e-05  0.0255
#     0.1 -8.23e-05  0.0254
#    0.11 -8.18e-05  0.0256
#    0.12 -8.08e-05  0.0253
#    0.13 -7.99e-05  0.0251
#    0.15 -7.99e-05  0.0251
#    0.17 -7.53e-05  0.0238
#     0.2 -6.99e-05  0.0223
#    0.22 -6.54e-05  0.0209
#    0.25 -6.07e-05  0.0196
#     0.3 -5.47e-05  0.0178
#    0.35 -5.06e-05  0.0167
#     0.4 -4.62e-05  0.0154
#    0.45 -4.62e-05  0.0151
#     0.5 -4.41e-05  0.0144
#     0.6  -3.6e-05  0.0119
#     0.7 -2.88e-05 0.00948
#     0.8  -2.5e-05 0.00819
#     0.9 -2.16e-05 0.00735
#       1 -2.18e-05 0.00761
#     1.1 -1.95e-05 0.00708
#     1.2 -1.63e-05 0.00652
#     1.3 -1.38e-05 0.00585
#     1.5 -1.18e-05 0.00552
#     1.7 -8.53e-06  0.0048
#       2 -4.53e-06 0.00405
#     2.2 -1.18e-06 0.00311
#     2.5   2.6e-06 0.00215
#       3  3.01e-06 0.00201
#     3.5  2.49e-06 0.00206
#       4  9.28e-06 0.00227
#     4.5 -2.13e-06 0.00295
#       5 -4.61e-06 0.00344
#     pgv -1.94e-05 0.00724
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
