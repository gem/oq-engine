# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2017 GEM Foundation
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
:mod:`openquake.hazardlib.gsim.raghukanth_iyengar_2007`
exports
:class:`RaghukanthIyengar2007`
:class:`RaghukanthIyengar2007KoynaWarna`
:class:`RaghukanthIyengar2007Southern`
:class:`RaghukanthIyengar2007WesternCentral`
"""

from __future__ import division
import warnings
import numpy as np

from openquake.hazardlib import const
from openquake.hazardlib.imt import SA, PGA
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable


class RaghukanthIyengar2007(GMPE):
    """
    Implements GMPE of Raghukanth & Iyengar (2007) for stable continental
    regions of peninsular India.

    This model is intended to be used to predict ground motions in
    peninsular India, a  stable continental region with nonetheless
    significant seismic hazard (see Section 1 "Introduction", p. 199 and
    Section 2 "Seismological model", p. 200)

    Page number citations in this documentation refer to:

    Raghukanth, S. and Iyengar, R. (2007). Estimation of seismic spectral
    acceleration in peninsular India. Journal of Earth System Science,
    116(3):199–214.
    """

    #: Supported tectonic region type is 'stable continental' since
    #: peninsular India "is similar to many other stable continental
    #: regions (SCR) of the world" (p. 200).
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.STABLE_CONTINENTAL

    #: Set of :mod:`intensity measure types <openquake.hazardlib.imt>`
    #: this GSIM can calculate. A set should contain classes from
    #: module :mod:`openquake.hazardlib.imt`.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([SA, PGA])

    #: This is not clear in the paper, but Figure 7 shows the model
    #: "compared with the average of the response spectrum of
    #: the two horizontal components" of a particular recording.
    #: :attr:`~openquake.hazardlib.const.IMC.AVERAGE_HORIZONTAL`,
    #: see p. 211.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Although "the coefficients of [equation (1)] are obtained
    #: from the simulated database of SA by a two-step stratified
    #: regression following Joyner and Boore (1981)" (p. 203), the
    #: standard deviations of the intermediate steps are not
    #: reported, so only total standard deviation is supported.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([const.StdDev.TOTAL])

    #: Required site parameter Vs30 is used to determing the NEHRP
    #: site class, and thus to choose site amplification coefficients
    #: and site amplification stanard error from Table 5 on p. 208.
    REQUIRES_SITES_PARAMETERS = set(('vs30',))

    #: Sole required rupture parameter is magnitude, since faulting
    #: style is not addressed.
    REQUIRES_RUPTURE_PARAMETERS = set(('mag',))

    #: Required distance measure is hypocentral distance, see p. 203.
    REQUIRES_DISTANCES = set(('rhypo',))

    #: Verification of mean value data was done by digitizing Figures 3 and
    #: 5 using http://arohatgi.info/WebPlotDigitizer/ app/. Maximum error
    #: was relatively high, approximately 10%, but could be reduced to
    #: approximately 1.5% by making the following changes to what may be
    #: typographical errors in the published coefficients. In each case the
    #: value sugstituted is interpolated from neighbouring values.
    #:
    #: RaghukanthIyengar2007 COEFFS_BEDROCK (Table 3) at 1.200 s:
    #:
    #: * change c1 from 0.2904 to 0.1904
    #:
    #: RaghukanthIyengar2007 COEFFS_NEHRP_C (Table 5) at 0.750 s:
    #:
    #: * change a1 from 0.36 to -0.30
    #:
    #: RaghukanthIyengar2007Southern COEFFS_BEDROCK (Table 2(b)) at 2.000 s:
    #:
    #: * change c4 from 0.0001 to 0.0010
    #:
    #: Note that these would be in addition to the following more obvious
    #: correction which was implemented.
    #:
    #: RaghukanthIyengar2007Southern COEFFS_BEDROCK (Table 2(b)) at 0.150 s:
    #:
    #: * change c1 from .1941 to 2.1941
    #:
    #: Note that since test data was dervied from Figures 3 and 5, PGA is
    #: not covered.
    non_verified = True

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        # pylint: disable=too-many-arguments
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for specification of input and result values.

        Implements the following equations:

        Equation (8) on p. 203 for the bedrock ground motion:

        ``ln(y_br) = c1 + c2*(M - 6) + c3*(M - 6)**2 - lnR - c4*R + ln(ε_br)``

        Equation (9) on p. 207 gives the site amplification factor:

        ``ln(F_s) = a1*y_br + a2 + ln(δ_site)``

        Equation (10) on p. 207 for the ground motion at a given site:

        ``y_site = y_br*F_s``

        Equation (11) on p. 207 for total standard error at a given site:

        ``σ{ln(ε_site)} = sqrt(σ{ln(ε_br)}**2 + σ{ln(δ_site)}**2)``

        """

        # obtain coefficients for required intensity measure type
        coeffs = self.COEFFS_BEDROCK[imt].copy()

        # obtain site-class specific coefficients
        a_1, a_2, sigma_site = self._get_site_coeffs(sites, imt)
        coeffs.update({'a1': a_1, 'a2': a_2, 'sigma_site': sigma_site})

        # compute bedrock motion, equation (8)
        ln_mean = (self._compute_magnitude_terms(rup, coeffs) +
                   self._compute_distance_terms(dists, coeffs))

        # adjust for site class, equation (10)
        ln_mean += self._compute_site_amplification(ln_mean, coeffs)
        # No need to convert to g since "In [equation (8)], y_br = (SA/g)"

        ln_stddevs = self._get_stddevs(coeffs, stddev_types)

        return ln_mean, [ln_stddevs]

    def _compute_magnitude_terms(self, rup, coeffs):
        """
        First three terms of equation (8) on p. 203:

        ``c1 + c2*(M - 6) + c3*(M - 6)**2``
        """

        adj_mag = rup.mag - self.CONSTS['ref_mag']
        return coeffs['c1'] + coeffs['c2']*adj_mag + coeffs['c3']*adj_mag**2

    @classmethod
    def _compute_distance_terms(cls, dists, coeffs):
        """
        Fourth and fifth terms of equation (8) on p. 203:

        ``- ln(R) - c4*R``
        """
        return - np.log(dists.rhypo) - coeffs['c4']*dists.rhypo

    @classmethod
    def _compute_site_amplification(cls, ln_mean_bedrock, coeffs):
        """
        Equation (9) on p. 207 gives the site amplification factor:

        ``ln(F_s) = a1*y_br + a2 + ln(δ_site)``
        """
        return coeffs['a1']*np.exp(ln_mean_bedrock) + coeffs['a2']

    def _get_stddevs(self, coeffs, stddev_types):
        """
        Equation (11) on p. 207 for total standard error at a given site:

        ``σ{ln(ε_site)} = sqrt(σ{ln(ε_br)}**2 + σ{ln(δ_site)}**2)``
        """
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES

        return np.sqrt(coeffs['sigma_bedrock']**2 + coeffs['sigma_site']**2)

    def _get_site_coeffs(self, sites, imt):
        """
        Extracts correct coefficients for each site from Table 5 on p. 208
        for each site.

        :raises UserWarning:
            If vs30 is below limit for site class D, since "E- and F-type
            sites [...] are susceptible for liquefaction and failure." p. 205.
        """

        site_classes = self.get_nehrp_classes(sites)
        is_bedrock = self.is_bedrock(sites)

        if 'E' in site_classes:
            msg = ('Site class E and F not supported by %s'
                   % type(self).__name__)
            warnings.warn(msg, UserWarning)

        a_1 = np.nan*np.ones_like(sites.vs30)
        a_2 = np.nan*np.ones_like(sites.vs30)
        sigma = np.nan*np.ones_like(sites.vs30)
        for key in self.COEFFS_NEHRP.keys():
            indices = (site_classes == key) & ~is_bedrock
            a_1[indices] = self.COEFFS_NEHRP[key][imt]['a1']
            a_2[indices] = self.COEFFS_NEHRP[key][imt]['a2']
            sigma[indices] = self.COEFFS_NEHRP[key][imt]['sigma']

        a_1[is_bedrock] = 0.
        a_2[is_bedrock] = 0.
        sigma[is_bedrock] = 0.

        return (a_1, a_2, sigma)

    def is_bedrock(self, sites):
        """
        A threshhold is not explicitly defined but the intention can be
        inferred from the statement that "The above results are valid at the
        bedrock level, with Vs nearly equal to 3.6 km/s." p. 203
        """

        return sites.vs30 > self.CONSTS['vs_bedrock']

    def get_nehrp_classes(self, sites):
        """
        Site classification threshholds from Section 4 "Site correction
        coefficients" p. 205. Note that site classes E and F are not
        supported.
        """

        classes = sorted(self.NEHRP_VS30_UPPER_BOUNDS.keys())
        bounds = [self.NEHRP_VS30_UPPER_BOUNDS[item] for item in classes]
        bounds = np.reshape(np.array(bounds), (-1, 1))
        vs30s = np.reshape(sites.vs30, (1, -1))
        site_classes = np.choose((vs30s < bounds).sum(axis=0) - 1, classes)

        return site_classes.astype('object')

    #: Coefficients taken from Table 3, p. 205.
    COEFFS_BEDROCK = CoeffsTable(sa_damping=5., table="""\
      IMT      c1      c2      c3      c4   sigma_bedrock
      PGA  1.6858  0.9241 -0.0760  0.0057  0.4648
    0.010  1.7510  0.9203 -0.0748  0.0056  0.4636
    0.015  1.8602  0.9184 -0.0666  0.0053  0.4230
    0.020  2.0999  0.9098 -0.0630  0.0056  0.4758
    0.030  2.6310  0.8999 -0.0582  0.0060  0.5189
    0.040  2.8084  0.9022 -0.0583  0.0059  0.4567
    0.050  2.7800  0.9090 -0.0605  0.0055  0.4130
    0.060  2.6986  0.9173 -0.0634  0.0052  0.4201
    0.075  2.5703  0.9308 -0.0687  0.0049  0.4305
    0.090  2.4565  0.9450 -0.0748  0.0046  0.4572
    0.100  2.3890  0.9548 -0.0791  0.0044  0.4503
    0.150  2.1200  1.0070 -0.1034  0.0038  0.4268
    0.200  1.9192  1.0619 -0.1296  0.0034  0.3932
    0.300  1.6138  1.1708 -0.1799  0.0028  0.3984
    0.400  1.3720  1.2716 -0.2219  0.0024  0.3894
    0.500  1.1638  1.3615 -0.2546  0.0021  0.3817
    0.600  0.9770  1.4409 -0.2791  0.0019  0.3744
    0.700  0.8061  1.5111 -0.2970  0.0017  0.3676
    0.750  0.7254  1.5432 -0.3040  0.0016  0.3645
    0.800  0.6476  1.5734 -0.3099  0.0016  0.3616
    0.900  0.4996  1.6291 -0.3188  0.0015  0.3568
    1.000  0.3604  1.6791 -0.3248  0.0014  0.3531
    1.200  0.2904  1.7464 -0.3300  0.0013  0.3748
    1.500 -0.2339  1.8695 -0.3290  0.0011  0.3479
    2.000 -0.7096  1.9983 -0.3144  0.0011  0.3140
    2.500 -1.1064  2.0919 -0.2945  0.0010  0.3222
    3.000 -1.4468  2.1632 -0.2737  0.0011  0.3493
    4.000 -2.0090  2.2644 -0.2350  0.0011  0.3182
    """)

    CONSTS = {
        'ref_mag': 6.,
        'vs_bedrock': 3600.,
    }

    #: Site class coefficients taken from Table 5, p. 208.
    COEFFS_NEHRP = {
        'A': CoeffsTable(sa_damping=5., table="""\
      IMT  a1    a2  sigma
      PGA  0.  0.36   0.03
    0.010  0.  0.35   0.04
    0.015  0.  0.31   0.06
    0.020  0.  0.26   0.08
    0.030  0.  0.25   0.04
    0.040  0.  0.31   0.01
    0.050  0.  0.36   0.01
    0.060  0.  0.39   0.01
    0.075  0.  0.43   0.01
    0.090  0.  0.46   0.01
    0.100  0.  0.47   0.01
    0.150  0.  0.50   0.02
    0.200  0.  0.51   0.02
    0.300  0.  0.53   0.03
    0.400  0.  0.52   0.03
    0.500  0.  0.51   0.06
    0.600  0.  0.49   0.01
    0.700  0.  0.49   0.01
    0.750  0.  0.48   0.02
    0.800  0.  0.47   0.01
    0.900  0.  0.46   0.01
    1.000  0.  0.45   0.02
    1.200  0.  0.43   0.01
    1.500  0.  0.39   0.02
    2.000  0.  0.36   0.03
    2.500  0.  0.34   0.04
    3.000  0.  0.32   0.04
    4.000  0.  0.31   0.05
    """),
        'B': CoeffsTable(sa_damping=5., table="""\
      IMT  a1    a2  sigma
      PGA  0.  0.49   0.08
    0.010  0.  0.43   0.11
    0.015  0.  0.36   0.16
    0.020  0.  0.24   0.09
    0.030  0.  0.18   0.03
    0.040  0.  0.29   0.01
    0.050  0.  0.40   0.02
    0.060  0.  0.48   0.02
    0.075  0.  0.56   0.03
    0.090  0.  0.62   0.02
    0.100  0.  0.71   0.01
    0.150  0.  0.74   0.01
    0.200  0.  0.76   0.02
    0.300  0.  0.76   0.02
    0.400  0.  0.74   0.01
    0.500  0.  0.72   0.02
    0.600  0.  0.69   0.02
    0.700  0.  0.68   0.02
    0.750  0.  0.66   0.02
    0.800  0.  0.63   0.01
    0.900  0.  0.61   0.02
    1.000  0.  0.62   0.11
    1.200  0.  0.57   0.03
    1.500  0.  0.51   0.04
    2.000  0.  0.44   0.06
    2.500  0.  0.40   0.08
    3.000  0.  0.38   0.10
    4.000  0.  0.36   0.11
    """),
        'C': CoeffsTable(sa_damping=5., table="""\
      IMT    a1    a2  sigma
      PGA -0.89  0.66   0.23
    0.010 -0.89  0.66   0.23
    0.015 -0.89  0.54   0.23
    0.020 -0.91  0.32   0.19
    0.030 -0.94 -0.01   0.21
    0.040 -0.87 -0.05   0.21
    0.050 -0.83  0.11   0.18
    0.060 -0.83  0.27   0.18
    0.075 -0.81  0.50   0.19
    0.090 -0.83  0.68   0.18
    0.100 -0.84  0.79   0.15
    0.150 -0.93  1.11   0.16
    0.200 -0.78  1.16   0.18
    0.300  0.06  1.03   0.13
    0.400 -0.06  0.99   0.13
    0.500 -0.17  0.97   0.12
    0.600 -0.04  0.93   0.12
    0.700 -0.25  0.88   0.12
    0.750  0.36  0.86   0.09
    0.800 -0.34  0.84   0.12
    0.900 -0.29  0.81   0.12
    1.000  0.24  0.78   0.10
    1.200 -0.11  0.67   0.09
    1.500 -0.10  0.62   0.09
    2.000 -0.13  0.47   0.08
    2.500 -0.15  0.39   0.08
    3.000 -0.17  0.32   0.09
    4.000 -0.19  0.35   0.08
    """),
        'D': CoeffsTable(sa_damping=5., table="""\
      IMT    a1    a2  sigma
      PGA -2.61  0.80   0.36
    0.010 -2.62  0.80   0.37
    0.015 -2.62  0.69   0.37
    0.020 -2.61  0.55   0.34
    0.030 -2.54  0.42   0.31
    0.040 -2.44  0.58   0.31
    0.050 -2.34  0.65   0.29
    0.060 -2.78  0.83   0.29
    0.075 -2.32  0.93   0.19
    0.090 -2.27  1.04   0.29
    0.100 -2.25  1.12   0.19
    0.150 -2.38  1.40   0.28
    0.200 -2.32  1.57   0.19
    0.300 -1.86  1.51   0.16
    0.400 -1.28  1.43   0.16
    0.500 -0.69  1.34   0.21
    0.600 -0.56  1.32   0.21
    0.700 -0.42  1.29   0.21
    0.750 -0.36  1.28   0.19
    0.800 -0.18  1.27   0.21
    0.900  0.17  1.25   0.21
    1.000  0.53  1.23   0.15
    1.200  0.77  1.14   0.17
    1.500  1.13  1.01   0.17
    2.000  0.61  0.79   0.15
    2.500  0.37  0.68   0.15
    3.000  0.13  0.60   0.13
    4.000  0.12  0.44   0.15
    """),
    }

    NEHRP_VS30_UPPER_BOUNDS = {
        'A': np.inf,
        'B': 1500.,
        'C': 760.,
        'D': 360.,
        'E': 180.,
        }


class RaghukanthIyengar2007KoynaWarna(RaghukanthIyengar2007):
    # pylint: disable=too-few-public-methods
    """
    Implements GMPE of Raghukanth & Iyengar (2007) for the Koyna-Warna
    region of India.

    The Koyna-Warna region is defined for the purpose of this GMPE by
    Figure 2. It is approximately a circle of 2° radius centered on 17°N
    75°E.
    """

    #: Coefficients taken from Table 2(a), p. 202.
    COEFFS_BEDROCK = CoeffsTable(sa_damping=5., table="""\
      IMT      c1      c2      c3      c4   sigma_bedrock
      PGA  1.7615  0.9325 -0.0706  0.0086  0.3292
    0.010  1.8163  0.9313 -0.0698  0.0087  0.3322
    0.015  1.9414  0.9249 -0.0674  0.0090  0.3491
    0.020  2.1897  0.9148 -0.0634  0.0094  0.3925
    0.030  2.7216  0.9030 -0.0583  0.0099  0.4143
    0.040  2.8862  0.9053 -0.0587  0.0097  0.3391
    0.050  2.8514  0.9127 -0.0611  0.0093  0.3061
    0.060  2.7665  0.9215 -0.0643  0.0089  0.2976
    0.075  2.6372  0.9356 -0.0699  0.0085  0.2917
    0.090  2.5227  0.9505 -0.0763  0.0082  0.2873
    0.100  2.4556  0.9608 -0.0809  0.0080  0.2845
    0.150  2.1864  1.0152 -0.1064  0.0072  0.2737
    0.200  1.9852  1.0723 -0.1337  0.0067  0.2666
    0.300  1.6781  1.1848 -0.1853  0.0059  0.2586
    0.400  1.4334  1.2880 -0.2278  0.0054  0.2531
    0.500  1.2230  1.3797 -0.2604  0.0050  0.2470
    0.600  1.0331  1.4603 -0.2845  0.0048  0.2407
    0.700  0.8597  1.5314 -0.3020  0.0045  0.2346
    0.750  0.7784  1.5638 -0.3088  0.0044  0.2318
    0.800  0.6989  1.5944 -0.3144  0.0043  0.2294
    0.900  0.5488  1.6505 -0.3229  0.0042  0.2253
    1.000  0.4082  1.7010 -0.3284  0.0041  0.2224
    1.200  0.1484  1.7880 -0.3331  0.0039  0.2202
    1.500 -0.1937  1.8927 -0.3306  0.0037  0.2226
    2.000 -0.6747  2.0218 -0.3147  0.0035  0.2337
    2.500 -1.0761  2.1156 -0.2938  0.0034  0.2458
    3.000 -1.4190  2.1869 -0.2723  0.0033  0.2557
    4.000 -1.9856  2.2879 -0.2328  0.0033  0.2685
   """)


class RaghukanthIyengar2007Southern(RaghukanthIyengar2007):
    # pylint: disable=too-few-public-methods
    """
    Implements GMPE of Raghukanth & Iyengar (2007) for southern India.

    Southern India is defined for the purpose of this GMPE by Figure 2, p.
    201. It is that part of India which is south of a line from from
    approximately 22°N 72°E to 17°N 83°E and excluding the Koyna-Warna
    region, approximately a circle of 2° radius centered on 17°N 75°E.

    Note that in Table 2(b) coefficient c1 at 0.150 s is inexplicably
    missing the digit before the decimal point. This was assumed to be "2".
    """

    #: Coefficients taken from Table 2(b), p. 203.
    COEFFS_BEDROCK = CoeffsTable(sa_damping=5., table="""\
      IMT      c1      c2      c3      c4   sigma_bedrock
      PGA  1.7816  0.9205 -0.0673  0.0035  0.3136
    0.010  1.8375  0.9196 -0.0666  0.0035  0.3172
    0.015  1.9657  0.9136 -0.0643  0.0036  0.3383
    0.020  2.2153  0.9054 -0.0607  0.0037  0.3920
    0.030  2.7418  0.8988 -0.0570  0.0037  0.3171
    0.040  2.9025  0.9034 -0.0578  0.0036  0.3344
    0.050  2.8652  0.9113 -0.0604  0.0035  0.3000
    0.060  2.7795  0.9202 -0.0637  0.0034  0.2917
    0.075  2.6483  0.9343 -0.0693  0.0032  0.2865
    0.090  2.5333  0.9492 -0.0757  0.0031  0.2825
    0.100  2.4651  0.9595 -0.0803  0.0030  0.2801
    0.150  2.1941  1.0139 -0.1058  0.0027  0.2703
    0.200  1.9917  1.0708 -0.1331  0.0025  0.2637
    0.300  1.6832  1.1830 -0.1846  0.0021  0.2563
    0.400  1.4379  1.2859 -0.2269  0.0019  0.2510
    0.500  1.2262  1.3770 -0.2592  0.0017  0.2450
    0.600  1.0361  1.4571 -0.2830  0.0015  0.2386
    0.700  0.8621  1.5276 -0.3001  0.0014  0.2323
    0.750  0.7800  1.5598 -0.3067  0.0013  0.2290
    0.800  0.7008  1.5900 -0.3121  0.0013  0.2268
    0.900  0.5501  1.6456 -0.3203  0.0012  0.2225
    1.000  0.4087  1.6955 -0.3255  0.0012  0.2194
    1.200  0.1489  1.7814 -0.3298  0.0011  0.2163
    1.500 -0.1943  1.8847 -0.3268  0.0010  0.2175
    2.000 -0.6755  2.0119 -0.3105  0.0001  0.2265
    2.500 -1.0762  2.1041 -0.2895  0.0010  0.2365
    3.000 -1.4191  2.1741 -0.2680  0.0010  0.2447
    4.000 -1.9847  2.2730 -0.2287  0.0011  0.2544
    """)


class RaghukanthIyengar2007WesternCentral(RaghukanthIyengar2007):
    # pylint: disable=too-few-public-methods
    """
    Implements GMPE of Raghukanth & Iyengar (2007) for western-central India.

    Western-central India is defined for the purpose of this GMPE by Figure
    2, p. 201. It is that part of India which is north of a line from from
    approximately 22°N 72°E to 17°N 83°E.
    """

    #: Coefficients taken from Table 2(c), p. 204.
    COEFFS_BEDROCK = CoeffsTable(sa_damping=5., table="""\
      IMT      c1      c2      c3      c4   sigma_bedrock
      PGA  1.7236  0.9453 -0.0725  0.0064  0.3439
    0.010  1.8063  0.9379 -0.0725  0.0062  0.3405
    0.015  1.9263  0.9320 -0.0703  0.0066  0.3572
    0.020  2.1696  0.9224 -0.0663  0.0072  0.3977
    0.030  2.7092  0.9087 -0.0602  0.0081  0.4152
    0.040  2.8823  0.9090 -0.0597  0.0078  0.3422
    0.050  2.8509  0.9153 -0.0617  0.0073  0.3087
    0.060  2.7684  0.9235 -0.0648  0.0067  0.2988
    0.075  2.6403  0.9372 -0.0703  0.0061  0.2919
    0.090  2.5270  0.9518 -0.0766  0.0056  0.2868
    0.100  2.4597  0.9620 -0.0811  0.0053  0.2839
    0.150  2.1912  1.0160 -0.1065  0.0043  0.2726
    0.200  1.9900  1.0728 -0.1338  0.0037  0.2654
    0.300  1.6827  1.1852 -0.1854  0.0029  0.2575
    0.400  1.4382  1.2883 -0.2279  0.0023  0.2520
    0.500  1.2271  1.3799 -0.2606  0.0019  0.2461
    0.600  1.0376  1.4605 -0.2848  0.0017  0.2398
    0.700  0.8639  1.5316 -0.3023  0.0015  0.2337
    0.750  0.7821  1.5639 -0.3090  0.0014  0.2310
    0.800  0.7031  1.5945 -0.3147  0.0013  0.2285
    0.900  0.5527  1.6506 -0.3231  0.0011  0.2244
    1.000  0.4115  1.7010 -0.3287  0.0010  0.2215
    1.200  0.1521  1.7878 -0.3334  0.0009  0.2191
    1.500 -0.1909  1.8922 -0.3308  0.0007  0.2214
    2.000 -0.6722  2.0209 -0.3148  0.0006  0.2321
    2.500 -1.0731  2.1142 -0.2939  0.0006  0.2437
    3.000 -1.4164  2.1850 -0.2724  0.0006  0.2531
    4.000 -1.9828  2.2851 -0.2329  0.0006  0.2649
    """)
