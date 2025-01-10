# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2025 GEM Foundation
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
Module exports :class:'ShahjoueiPezeshk2016'.
"""
import numpy as np

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA


def _compute_magnitude(ctx, C):
    """
    Compute the first term of the equation described on p. 742:

    "c1 + (c2 * M) + (c3 * M**2) "
    """
    return C['c1'] + C['c2'] * ctx.mag + C['c3'] * ctx.mag ** 2


def _compute_attenuation(ctx, imt, C):
    """
    Compute the second term of the equation described on p. 742:

    " [(c4 + c5 * M) * min{ log10(R), log10(60.) }] +
    [(c6 + c7 * M) * max{ min{ log10(R/60.), log10(120./60.) }, 0.}] +
    [(c8 + c9 * M) * max{ log10(R/120.), 0}] "
    """
    vec = np.ones(len(ctx.rjb))

    a1 = (np.log10(np.sqrt(ctx.rjb ** 2.0 + C['c11'] ** 2.0)),
          np.log10(60. * vec))

    a = np.column_stack([a1[0], a1[1]])

    b3 = (np.log10(np.sqrt(ctx.rjb ** 2.0 + C['c11'] ** 2.0) /
                   (60. * vec)), np.log10((120. / 60.) * vec))

    b2 = np.column_stack([b3[0], b3[1]])
    b1 = ([np.min(b2, axis=1), 0. * vec])
    b = np.column_stack([b1[0], b1[1]])

    c1 = (np.log10(np.sqrt(ctx.rjb ** 2.0 + C['c11'] ** 2.0) /
          (120.) * vec), 0. * vec)
    c = np.column_stack([c1[0], c1[1]])

    return (((C['c4'] + C['c5'] * ctx.mag) * np.min(a, axis=1)) +
            ((C['c6'] + C['c7'] * ctx.mag) * np.max(b, axis=1)) +
            ((C['c8'] + C['c9'] * ctx.mag) * np.max(c, axis=1)))


def _compute_distance(ctx, imt, C):
    """
    Compute the third term of the equation described on p. 742:

    " c10 * R "
    """
    return (C['c10'] * np.sqrt(ctx.rjb ** 2.0 + C['c11'] ** 2.0))


def _compute_standard_dev(ctx, imt, C):
    """
    Compute the the standard deviation in terms of magnitude
    described on page 744, eq. 4
    """
    sigma_mean = 0.
    if imt.string.startswith(('PGA', 'SA')):
        psi = -6.898E-3
    else:
        psi = -3.054E-5
    sigma_mean = np.where(ctx.mag <= 6.5,
                          (C['c12'] * ctx.mag) + C['c13'],
                          (psi * ctx.mag) + C['c14'])
    return sigma_mean


class ShahjoueiPezeshk2016(GMPE):
    """
    Implements GMPE developed by Alireza Shahjouei and Shahram Pezeshk.
    Published as "Alternative Hybrid Empirical Ground‐Motion Model for
    Central and Eastern North America Using Hybrid Simulations and
    NGA‐West2 Models", 2016, Bulletin of the Seismological
    Society of America, vol. 106, no. 2, 734 - 754.
    """
    #: Supported tectonic region type is 'stable continental region'
    #: equation has been derived from data from Eastern North America (ENA)
    # 'Introduction', page 735.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.STABLE_CONTINENTAL

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration. See Table 7 on page 743
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    #: An orientation-independent alternative to :attr:`GEOMETRIC_MEAN`.
    #: Defined at Boore et al. (2006, Bull. Seism. Soc. Am. 96, 1502-1511)
    #: and is used for all the NGA GMPEs. See page 742.
    #: :attr:'~openquake.hazardlib.const.IMC.RotD50'.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50

    #: Supported standard deviation types is total.
    #: See equation 4 and 5, page 744.
    #: We use aleatory uncertainty as the total
    #: standard deviation since page 745 states,
    #: The epistemic uncertainty for an individual GMM is infrequently
    #: employed...
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}

    #: No site parameters are needed. The GMPE was developed for hard-rock site
    # with Vs30 >= 3000 m/s (NEHRP site class A) only. Page 734.
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameters are magnitude (eq. 4, page 742).
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is Rjb (eq. 3 page 742).
    REQUIRES_DISTANCES = {'rjb'}

    #: GMPE not tested against independent implementation so raise
    #: not verified warning
    non_verified = True

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]

            imean = (_compute_magnitude(ctx, C) +
                     _compute_attenuation(ctx, imt, C) +
                     _compute_distance(ctx, imt, C))

            mean[m] = np.log(10.0 ** imean)

            sigma_mean = _compute_standard_dev(ctx, imt, C)
            sigma_tot = np.sqrt(sigma_mean ** 2 + C['SigmaReg'] ** 2)
            sig[m] = np.log(10.0 ** np.log10(np.exp(sigma_tot)))

    #: Equation coefficients, described in Table 2 on pp. 1865
    COEFFS = CoeffsTable(sa_damping=5, table="""
    IMT    c1      c2      c3       c4      c5     c6       c7        c8      c9      c10        c11    c12     c13   c14   SigmaReg SigmaPar
    pgv    -2.3891 1.259   -0.07901 -2.9386 0.3034 -0.00929 -0.04605  -2.7548 0.3467  -0.0007623 -4.598 -0.0554 0.978 0.663 0.1      0.288
    pga    -0.3002 0.5066  -0.04526 -3.224  0.2998 -1.283   0.1045    -3.0856 0.2778  -0.0007711 3.81   -0.041  0.876 0.611 0.194    0.373
    0.010  -0.3472 0.4838  -0.04093 -3.0832 0.2712 -0.9676  0.04983   -2.9695 0.2693  -0.0006695 -4.434 -0.056  0.982 0.664 0.132    0.281
    0.020  0.832   0.1934  -0.0206  -3.1134 0.2786 -1.133   0.05994   -3.5023 0.2901  -0.0005857 -4.412 -0.0559 0.983 0.665 0.0928   0.281
    0.030  1.185   0.1064  -0.01423 -3.1029 0.2792 -1.078   0.05239   -3.5722 0.2865  -0.000622  -4.353 -0.0577 1     0.676 0.0833   0.277
    0.040  1.246   0.08986 -0.01268 -3.0785 0.2773 -0.9743  0.0416    -3.5083 0.2769  -0.0006818 -4.303 -0.0577 1.01  0.688 0.0798   0.279
    0.050  1.1793  0.1037  -0.01321 -3.0488 0.2744 -0.8635  0.03077   -3.3986 0.2659  -0.0007439 -4.266 -0.0578 1.03  0.701 0.0776   0.272
    0.075  0.8045  0.1866  -0.01788 -2.9697 0.266  -0.6122  0.007491  -3.0852 0.2391  -0.0008801 -4.214 -0.0561 1.03  0.721 0.0738   0.252
    0.100  0.35    0.2871  -0.02381 -2.894  0.2576 -0.4123  -0.01012  -2.7947 0.2163  -0.0009848 4.201  -0.0565 1.05  0.732 0.0717   0.265
    0.150  -0.5264 0.4782  -0.03519 -2.761  0.2426 -0.1319  -0.03338  -2.3312 0.1818  -0.001125  4.239  -0.0559 1.04  0.724 0.0716   0.276
    0.200  -1.2884 0.6413  -0.04486 -2.6504 0.2301 0.04637  -0.0469   -1.9927 0.1576  -0.001209  4.325  -0.056  1.03  0.715 0.0743   0.258
    0.250  -1.9422 0.7789  -0.05295 -2.5573 0.2196 0.1631   -0.05478  -1.7399 0.1398  -0.001258  4.438  -0.0537 1.02  0.712 0.0779   0.268
    0.300  -2.5071 0.8961  -0.05976 -2.478  0.2107 0.2407   -0.05919  -1.547  0.1265  -0.001286  4.571  -0.0511 1.01  0.718 0.0815   0.284
    0.400  -3.436  1.085   -0.07059 -2.3495 0.1961 0.3244   -0.06197  -1.2793 0.1085  -0.001304  -4.872 -0.047  0.987 0.725 0.0876   0.34
    0.500  -4.1699 1.231   -0.07878 -2.251  0.1849 0.3544   -0.06046  -1.1111 0.09757 -0.001294  -5.211 -0.0442 0.981 0.736 0.0923   0.357
    0.750  -5.4797 1.482   -0.09245 -2.0865 0.1659 0.3284   -0.04979  -0.9131 0.0857  -0.001219  -6.154 -0.0384 0.967 0.76  0.0991   0.374
    1.000  -6.3464 1.641   -0.1006  -1.9931 0.1546 0.253    -0.03709  -0.8641 0.08405 -0.001123  -7.174 -0.0314 0.933 0.77  0.102    0.392
    1.500  -7.4087 1.823   -0.1093  -1.9162 0.1438 0.09019  -0.01551  -0.92   0.09103 -0.0009407 -9.253 -0.0227 0.883 0.776 0.105    0.426
    2.000  -8.0057 1.916   -0.113   -1.9173 0.1418 -0.03828 -0.001252 -1.0327 0.1016  -0.0007926 -11.22 -0.0184 0.857 0.778 0.106    0.44
    3.000  -8.5793 1.985   -0.1146  -2.0184 0.1499 -0.1744  0.009393  -1.2453 0.1214  -0.0005919 14.38  -0.0189 0.859 0.777 0.107    0.58
    4.000  -8.8246 1.99    -0.1131  -2.1475 0.1635 -0.1844  0.003919  -1.3849 0.1357  -0.0004855 16.19  -0.016  0.83  0.766 0.107    0.589
    5.000  -8.9855 1.975   -0.1105  -2.2496 0.1764 -0.1043  -0.01187  -1.4511 0.1446  -0.0004439 16.71  -0.0153 0.826 0.766 0.107    0.631
    7.500  -9.3927 1.925   -0.1032  -2.3572 0.1973 0.3465   -0.07832  -1.3728 0.149   -0.0005176 14.58  -0.0143 0.815 0.762 0.113    0.721
    10.000 -9.735  1.879   -0.09666 -2.4139 0.2117 1.01     -0.1678   -1.0631 0.137   -0.000742  11.23  -0.017  0.822 0.752 0.14     0.739
    """)
