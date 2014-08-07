# The Hazard Library
# Copyright (C) 2012 GEM Foundation
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
Module exports :class:`ChiouYoungs2008`.
"""
from __future__ import division

import numpy as np

from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA


class ChiouYoungs2008(GMPE):

    """
    Implements GMPE developed by Brian S.-J. Chiou and Robert R. Youngs
    and published as "An NGA Model for the Average Horizontal Component
    of Peak Ground Motion and Response Spectra" (2008, Earthquake Spectra,
    Volume 24, No. 1, pages 173-215).
    """
    #: Supported tectonic region type is active shallow crust, see page 174.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are spectral acceleration,
    #: peak ground velocity and peak ground acceleration, see tables
    #: at pages 198 and 199.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        PGV,
        SA
    ])

    #: Supported intensity measure component is orientation-independent
    #: measure :attr:`~openquake.hazardlib.const.IMC.GMRotI50`, see page 174.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GMRotI50

    #: Supported standard deviation types are inter-event, intra-event
    #: and total, see chapter "Variance model".
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    ])

    #: Required site parameters are Vs30 (eq. 13b), Vs30 measured flag (eq. 20)
    #: and Z1.0 (eq. 13b).
    REQUIRES_SITES_PARAMETERS = set(('vs30', 'vs30measured', 'z1pt0'))

    #: Required rupture parameters are magnitude, rake (eq. 13a and 13b),
    #: dip (eq. 13a) and ztor (eq. 13a).
    REQUIRES_RUPTURE_PARAMETERS = set(('dip', 'rake', 'mag', 'ztor'))

    #: Required distance measures are RRup, Rjb and Rx (all are in eq. 13a).
    REQUIRES_DISTANCES = set(('rrup', 'rjb', 'rx'))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extracting dictionary of coefficients specific to required
        # intensity measure type.
        C = self.COEFFS[imt]
        # intensity on a reference soil is used for both mean
        # and stddev calculations.
        ln_y_ref = self._get_ln_y_ref(rup, dists, C)
        # exp1 and exp2 are parts of eq. 10 and eq. 13b,
        # calculate it once for both.
        exp1 = np.exp(C['phi3'] * (sites.vs30.clip(-np.inf, 1130) - 360))
        exp2 = np.exp(C['phi3'] * (1130 - 360))

        mean = self._get_mean(sites, C, ln_y_ref, exp1, exp2)
        stddevs = self._get_stddevs(sites, rup, C, stddev_types,
                                    ln_y_ref, exp1, exp2)
        return mean, stddevs

    def _get_mean(self, sites, C, ln_y_ref, exp1, exp2):
        """
        Add site effects to an intensity.

        Implements eq. 13b.
        """
        # we do not support estimating of basin depth and instead
        # rely on it being available (since we require it).
        z1pt0 = sites.z1pt0

        # we consider random variables being zero since we want
        # to find the exact mean value.
        eta = epsilon = 0

        ln_y = (
            # first line of eq. 13b
            ln_y_ref + C['phi1'] * np.log(sites.vs30 / 1130).clip(-np.inf, 0)
            # second line
            + C['phi2'] * (exp1 - exp2)
            * np.log((np.exp(ln_y_ref) + C['phi4']) / C['phi4'])
            # third line
            + C['phi5']
            * (1.0 - 1.0 / np.cosh(
                C['phi6'] * (z1pt0 - C['phi7']).clip(0, np.inf)))
            + C['phi8'] / np.cosh(0.15 * (z1pt0 - 15).clip(0, np.inf))
            # fourth line
            + eta + epsilon
        )
        return ln_y

    def _get_stddevs(self, sites, rup, C, stddev_types, ln_y_ref, exp1, exp2):
        """
        Get standard deviation for a given intensity on reference soil.

        Implements equations 19, 20 and 21 for inter-event, intra-event
        and total standard deviations respectively.
        """
        # aftershock flag is zero, we consider only main shock.
        AS = 0
        Fmeasured = sites.vs30measured
        Finferred = 1 - sites.vs30measured

        # eq. 19 to calculate inter-event standard error
        mag_test = min(max(rup.mag, 5.0), 7.0) - 5.0
        tau = C['tau1'] + (C['tau2'] - C['tau1']) / 2 * mag_test

        # b and c coeffs from eq. 10
        b = C['phi2'] * (exp1 - exp2)
        c = C['phi4']

        y_ref = np.exp(ln_y_ref)
        # eq. 20
        NL = b * y_ref / (y_ref + c)
        sigma = (
            # first line of eq. 20
            (C['sig1']
             + 0.5 * (C['sig2'] - C['sig1']) * mag_test
             + C['sig4'] * AS)
            # second line
            * np.sqrt((C['sig3'] * Finferred + 0.7 * Fmeasured)
                      + (1 + NL) ** 2)
        )

        ret = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                # eq. 21
                ret += [np.sqrt(((1 + NL) ** 2) * (tau ** 2) + (sigma ** 2))]
            elif stddev_type == const.StdDev.INTRA_EVENT:
                ret.append(sigma)
            elif stddev_type == const.StdDev.INTER_EVENT:
                # this is implied in eq. 21
                ret.append(np.abs((1 + NL) * tau))
        return ret

    def _get_ln_y_ref(self, rup, dists, C):
        """
        Get an intensity on a reference soil.

        Implements eq. 13a.
        """
        # reverse faulting flag
        Frv = 1 if 30 <= rup.rake <= 150 else 0
        # normal faulting flag
        Fnm = 1 if -120 <= rup.rake <= -60 else 0
        # hanging wall flag
        Fhw = (dists.rx >= 0)
        # aftershock flag. always zero since we only consider main shock
        AS = 0

        ln_y_ref = (
            # first line of eq. 13a
            C['c1']
            + (C['c1a'] * Frv
               + C['c1b'] * Fnm
               + C['c7'] * (rup.ztor - 4))
            * (1 - AS)
            + (C['c10'] + C['c7a'] * (rup.ztor - 4)) * AS
            # second line
            + C['c2'] * (rup.mag - 6)
            + ((C['c2'] - C['c3']) / C['cn'])
            * np.log(1 + np.exp(C['cn'] * (C['cm'] - rup.mag)))
            # third line
            + C['c4']
            * np.log(dists.rrup
                     + C['c5']
                     * np.cosh(C['c6'] * max(rup.mag - C['chm'], 0)))
            # fourth line
            + (C['c4a'] - C['c4'])
            * np.log(np.sqrt(dists.rrup ** 2 + C['crb'] ** 2))
            # fifth line
            + (C['cg1'] + C['cg2'] / (np.cosh(max(rup.mag - C['cg3'], 0))))
            * dists.rrup
            # sixth line
            + C['c9'] * Fhw
            * np.tanh(dists.rx
                      * (np.cos(np.radians(rup.dip)) ** 2)
                      / C['c9a'])
            * (1 - np.sqrt(dists.rjb ** 2 + rup.ztor ** 2)
               / (dists.rrup + 0.001))
        )
        return ln_y_ref

    #: Coefficient tables are constructed from values in tables 1, 2 and 3
    #: (pages 197, 198 and 199). Spectral acceleration is defined for damping
    #: of 5%, see page 208.
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT    c2   c3    c4   c4a crb  chm cg3  c1      c1a     c1b    cn    cm     c5     c6     c7     c7a    c9     c9a     c10     cg1      cg2      phi1    phi2    phi3     phi4     phi5   phi6     phi7   phi8   tau1   tau2   sig1   sig2   sig3   sig4
    pga    1.06 3.45 -2.1 -0.5 50.0 3.0 4.0 -1.2687  0.1000 -0.2550 2.996 4.1840 6.1600 0.4893 0.0512 0.0860 0.7900 1.5005 -0.3218 -0.00804 -0.00785 -0.4417 -0.1417 -0.007010 0.102151 0.2289 0.014996 580.0  0.0700 0.3437 0.2637 0.4458 0.3459 0.8000 0.0663
    pgv    1.06 3.45 -2.1 -0.5 50.0 3.0 4.0  2.2884  0.1094 -0.0626 1.648 4.2979 5.1700 0.4407 0.0207 0.0437 0.3079 2.6690 -0.1166 -0.00275 -0.00625 -0.7861 -0.0699 -0.008444 5.410000 0.2899 0.006718 459.0  0.1138 0.2539 0.2381 0.4496 0.3554 0.7504 0.0133
    0.010  1.06 3.45 -2.1 -0.5 50.0 3.0 4.0 -1.2687  0.1000 -0.2550 2.996 4.1840 6.1600 0.4893 0.0512 0.0860 0.7900 1.5005 -0.3218 -0.00804 -0.00785 -0.4417 -0.1417 -0.007010 0.102151 0.2289 0.014996 580.0  0.0700 0.3437 0.2637 0.4458 0.3459 0.8000 0.0663
    0.020  1.06 3.45 -2.1 -0.5 50.0 3.0 4.0 -1.2515  0.1000 -0.2550 3.292 4.1879 6.1580 0.4892 0.0512 0.0860 0.8129 1.5028 -0.3323 -0.00811 -0.00792 -0.4340 -0.1364 -0.007279 0.108360 0.2289 0.014996 580.0  0.0699 0.3471 0.2671 0.4458 0.3459 0.8000 0.0663
    0.030  1.06 3.45 -2.1 -0.5 50.0 3.0 4.0 -1.1744  0.1000 -0.2550 3.514 4.1556 6.1550 0.4890 0.0511 0.0860 0.8439 1.5071 -0.3394 -0.00839 -0.00819 -0.4177 -0.1403 -0.007354 0.119888 0.2289 0.014996 580.0  0.0701 0.3603 0.2803 0.4535 0.3537 0.8000 0.0663
    0.040  1.06 3.45 -2.1 -0.5 50.0 3.0 4.0 -1.0671  0.1000 -0.2550 3.563 4.1226 6.1508 0.4888 0.0508 0.0860 0.8740 1.5138 -0.3453 -0.00875 -0.00855 -0.4000 -0.1591 -0.006977 0.133641 0.2289 0.014996 579.9  0.0702 0.3718 0.2918 0.4589 0.3592 0.8000 0.0663
    0.050  1.06 3.45 -2.1 -0.5 50.0 3.0 4.0 -0.9464  0.1000 -0.2550 3.547 4.1011 6.1441 0.4884 0.0504 0.0860 0.8996 1.5230 -0.3502 -0.00912 -0.00891 -0.3903 -0.1862 -0.006467 0.148927 0.2290 0.014996 579.9  0.0701 0.3848 0.3048 0.4630 0.3635 0.8000 0.0663
    0.075  1.06 3.45 -2.1 -0.5 50.0 3.0 4.0 -0.7051  0.1000 -0.2540 3.448 4.0860 6.1200 0.4872 0.0495 0.0860 0.9442 1.5597 -0.3579 -0.00973 -0.00950 -0.4040 -0.2538 -0.005734 0.190596 0.2292 0.014996 579.6  0.0686 0.3878 0.3129 0.4702 0.3713 0.8000 0.0663
    0.10   1.06 3.45 -2.1 -0.5 50.0 3.0 4.0 -0.5747  0.1000 -0.2530 3.312 4.1030 6.0850 0.4854 0.0489 0.0860 0.9677 1.6104 -0.3604 -0.00975 -0.00952 -0.4423 -0.2943 -0.005604 0.230662 0.2297 0.014996 579.2  0.0646 0.3835 0.3152 0.4747 0.3769 0.8000 0.0663
    0.15   1.06 3.45 -2.1 -0.5 50.0 3.0 4.0 -0.5309  0.1000 -0.2500 3.044 4.1717 5.9871 0.4808 0.0479 0.0860 0.9660 1.7549 -0.3565 -0.00883 -0.00862 -0.5162 -0.3113 -0.005845 0.266468 0.2326 0.014988 577.2  0.0494 0.3719 0.3128 0.4798 0.3847 0.8000 0.0612
    0.20   1.06 3.45 -2.1 -0.5 50.0 3.0 4.0 -0.6352  0.1000 -0.2449 2.831 4.2476 5.8699 0.4755 0.0471 0.0860 0.9334 1.9157 -0.3470 -0.00778 -0.00759 -0.5697 -0.2927 -0.006141 0.255253 0.2386 0.014964 573.9 -0.0019 0.3601 0.3076 0.4816 0.3902 0.8000 0.0530
    0.25   1.06 3.45 -2.1 -0.5 50.0 3.0 4.0 -0.7766  0.1000 -0.2382 2.658 4.3184 5.7547 0.4706 0.0464 0.0860 0.8946 2.0709 -0.3379 -0.00688 -0.00671 -0.6109 -0.2662 -0.006439 0.231541 0.2497 0.014881 568.5 -0.0479 0.3522 0.3047 0.4815 0.3946 0.7999 0.0457
    0.30   1.06 3.45 -2.1 -0.5 50.0 3.0 4.0 -0.9278  0.0999 -0.2313 2.505 4.3844 5.6527 0.4665 0.0458 0.0860 0.8590 2.2005 -0.3314 -0.00612 -0.00598 -0.6444 -0.2405 -0.006704 0.207277 0.2674 0.014639 560.5 -0.0756 0.3438 0.3005 0.4801 0.3981 0.7997 0.0398
    0.40   1.06 3.45 -2.1 -0.5 50.0 3.0 4.0 -1.2176  0.0997 -0.2146 2.261 4.4979 5.4997 0.4607 0.0445 0.0850 0.8019 2.3886 -0.3256 -0.00498 -0.00486 -0.6931 -0.1975 -0.007125 0.165464 0.3120 0.013493 540.0 -0.0960 0.3351 0.2984 0.4758 0.4036 0.7988 0.0312
    0.50   1.06 3.45 -2.1 -0.5 50.0 3.0 4.0 -1.4695  0.0991 -0.1972 2.087 4.5881 5.4029 0.4571 0.0429 0.0830 0.7578 2.5000 -0.3189 -0.00420 -0.00410 -0.7246 -0.1633 -0.007435 0.133828 0.3610 0.011133 512.9 -0.0998 0.3353 0.3036 0.4710 0.4079 0.7966 0.0255
    0.75   1.06 3.45 -2.1 -0.5 50.0 3.0 4.0 -1.9278  0.0936 -0.1620 1.812 4.7571 5.2900 0.4531 0.0387 0.0690 0.6788 2.6224 -0.2702 -0.00308 -0.00301 -0.7708 -0.1028 -0.008120 0.085153 0.4353 0.006739 441.9 -0.0765 0.3429 0.3205 0.4621 0.4157 0.7792 0.0175
    1.0    1.06 3.45 -2.1 -0.5 50.0 3.0 4.0 -2.2453  0.0766 -0.1400 1.648 4.8820 5.2480 0.4517 0.0350 0.0450 0.6196 2.6690 -0.2059 -0.00246 -0.00241 -0.7990 -0.0699 -0.008444 0.058595 0.4629 0.005749 391.8 -0.0412 0.3577 0.3419 0.4581 0.4213 0.7504 0.0133
    1.5    1.06 3.45 -2.1 -0.5 50.0 3.0 4.0 -2.7307  0.0022 -0.1184 1.511 5.0697 5.2194 0.4507 0.0280 0.0134 0.5101 2.6985 -0.0852 -0.00180 -0.00176 -0.8382 -0.0425 -0.007707 0.031787 0.4756 0.005544 348.1  0.0140 0.3769 0.3703 0.4493 0.4213 0.7136 0.0090
    2.0    1.06 3.45 -2.1 -0.5 50.0 3.0 4.0 -3.1413 -0.0591 -0.1100 1.470 5.2173 5.2099 0.4504 0.0213 0.0040 0.3917 2.7085  0.0160 -0.00147 -0.00143 -0.8663 -0.0302 -0.004792 0.019716 0.4785 0.005521 332.5  0.0544 0.4023 0.4023 0.4459 0.4213 0.7035 0.0068
    3.0    1.06 3.45 -2.1 -0.5 50.0 3.0 4.0 -3.7413 -0.0931 -0.1040 1.456 5.4385 5.2040 0.4501 0.0106 0.0010 0.1244 2.7145  0.1876 -0.00117 -0.00115 -0.9032 -0.0129 -0.001828 0.009643 0.4796 0.005517 324.1  0.1232 0.4406 0.4406 0.4433 0.4213 0.7006 0.0045
    4.0    1.06 3.45 -2.1 -0.5 50.0 3.0 4.0 -4.1814 -0.0982 -0.1020 1.465 5.5977 5.2020 0.4501 0.0041 0.0000 0.0086 2.7164  0.3378 -0.00107 -0.00104 -0.9231 -0.0016 -0.001523 0.005379 0.4799 0.005517 321.7  0.1859 0.4784 0.4784 0.4424 0.4213 0.7001 0.0034
    5.0    1.06 3.45 -2.1 -0.5 50.0 3.0 4.0 -4.5187 -0.0994 -0.1010 1.478 5.7276 5.2010 0.4500 0.0010 0.0000 0.0000 2.7172  0.4579 -0.00102 -0.00099 -0.9222  0.0000 -0.001440 0.003223 0.4799 0.005517 320.9  0.2295 0.5074 0.5074 0.4420 0.4213 0.7000 0.0027
    7.5    1.06 3.45 -2.1 -0.5 50.0 3.0 4.0 -5.1224 -0.0999 -0.1010 1.498 5.9891 5.2000 0.4500 0.0000 0.0000 0.0000 2.7177  0.7514 -0.00096 -0.00094 -0.8346  0.0000 -0.001369 0.001134 0.4800 0.005517 320.3  0.2660 0.5328 0.5328 0.4416 0.4213 0.7000 0.0018
    10.0   1.06 3.45 -2.1 -0.5 50.0 3.0 4.0 -5.5872 -0.1000 -0.1000 1.502 6.1930 5.2000 0.4500 0.0000 0.0000 0.0000 2.7180  1.1856 -0.00094 -0.00091 -0.7332  0.0000 -0.001361 0.000515 0.4800 0.005517 320.1  0.2682 0.5542 0.5542 0.4414 0.4213 0.7000 0.0014
    """)


class ChiouYoungs2008SWISS01(ChiouYoungs2008):

    """
    --------------------------------------------------------------------
    This class implments an extension of the Chiou & Youngs (2008) model,
    adjusted to be used for the new Swiss Hazard Model [2014].
    1) kappa value
       K-adjustments corresponding to model 01 (lower bound)- as prepared by Ben Edwards
       K-value for PGA were not provided but infered from SA[]0.01s]
       the model considers a fixed value of vs30=1100m/s
    2) small-magnitude correction
    3) single station sigma - mean inter-event adjustment
    4) single station sigma - inter-event magnitude/distance dependent
    ------------------------------------------------------------------------
    Disclaimer: these equations are modified to be used for the
    new Swiss Seismic Hazard Model [2014].
    The use of these models is the soly responsability of the hazard modeler.
    --------------------------------------------------------------------
    Model implmented by laurentiu.danciu@sed.ethz.ch
    --------------------------------------------------------------------
    """

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):

        C_ADJ = self.COEFFS_FS_ROCK[imt]
        C = self.COEFFS[imt]
        C1_rrup = self._compute_C1_term(C_ADJ, imt, dists)
        phi_ss = self._compute_phi_ss(C_ADJ, rup, C1_rrup, imt)

        ln_y_ref = self._get_ln_y_ref(rup, dists, self.COEFFS[imt])

        exp1 = np.exp(C['phi3'] * (sites.vs30.clip(-np.inf, 1130) - 360))

        exp2 = np.exp(C['phi3'] * (1130 - 360))

        mean, stddevs = super(ChiouYoungs2008SWISS01, self).\
            get_mean_and_stddevs(sites, rup, dists, imt, stddev_types)

        mean_corr = np.exp(
            mean) * C_ADJ['k_adj'] * self._compute_small_mag_correction_term(C_ADJ, rup.mag, dists.rrup)
        mean = np.log(mean_corr)

        std_corr = self._get_corr_stddevs(
            C, rup, stddev_types, ln_y_ref, exp1, exp2, phi_ss, sites)
        stddevs = np.array(std_corr)

        return mean, stddevs

    def _compute_small_mag_correction_term(self, C, mag, rrup):
        """
        small magnitude correction applied to the median values
        """
        if mag >= 3.00 and mag < 5.5:
            return 1 / np.exp(((5.50 - mag) / C['a1']) ** C['a2'] * (C['b1'] + C['b2'] * np.log(np.maximum(np.minimum(rrup, C['Rm']), 10) / 20)))
        elif mag >= 5.50:
            return 1
        else:
            return 1

    def _get_corr_stddevs(self, C, rup, stddev_types, ln_y_ref, exp1, exp2, phi_ss, sites):
        """
        Return standard deviations adjusted for single station sigma
        as the total standard deviation - as proposed to be used in
        the new Swiss Hazard Model [2014].
        """
        # aftershock flag is zero, we consider only main shock.
        AS = 0
        Fmeasured = sites.vs30measured
        Finferred = 1 - sites.vs30measured

        # eq. 19 to calculate inter-event standard error
        mag_test = min(max(rup.mag, 5.0), 7.0) - 5.0
        tau = C['tau1'] + (C['tau2'] - C['tau1']) / 2 * mag_test

        # b and c coeffs from eq. 10
        b = C['phi2'] * (exp1 - exp2)
        c = C['phi4']

        y_ref = np.exp(ln_y_ref)
        # eq. 20
        NL = b * y_ref / (y_ref + c)
        ret = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                # eq. 21
                ret += [np.sqrt(((1 + NL) ** 2) * (tau ** 2) + (phi_ss ** 2))]
            elif stddev_type == const.StdDev.INTRA_EVENT:
                ret.append(phi_ss)
            elif stddev_type == const.StdDev.INTER_EVENT:
                # this is implied in eq. 21
                ret.append(np.abs((1 + NL) * tau))
        return ret

    def _compute_C1_term(self, C, imt, dists):
        """
        Return C1 coeffs as function of Rrup as proposed by Rodriguez-Marek et al (2013)
        The C1 coeff are used to compute the single station sigma
        """
        C1_rrup = 0.0
        if (dists.rrup < C['Rc11']).any():
            C1_rrup = C['phi_11']
        elif ((dists.rrup >= C['Rc11']).any()
                and (dists.rrup <= C['Rc21']).any()):
            C1_rrup = C['phi_11'] + (C['phi_21'] - C['phi_11']) * \
                ((dists.rrup - C['Rc11']) / (C['Rc21'] - C['Rc11']))
        elif (dists.rrup > C['Rc21']).any():
            C1_rrup = C['phi_21']
        return C1_rrup

    def _compute_phi_ss(self, C, rup, C1_rrup, imt):
        """
        Return C1 coeffs as function of Rrup as proposed by Rodriguez-Marek et al (2013)
        The C1 coeff are used to compute the single station sigma
        retunr phi_ss in log10 units
        """
        phi_ss = 0

        if rup.mag < C['Mc1']:
            phi_ss = C1_rrup
        elif rup.mag >= C['Mc1'] and rup.mag <= C['Mc2']:
            phi_ss = C1_rrup + \
                (C['C2'] - C1_rrup) * \
                ((rup.mag - C['Mc1']) / (C['Mc2'] - C['Mc1']))
        elif rup.mag > C['Mc2']:
            phi_ss = C['C2']
        return (phi_ss)

    COEFFS_FS_ROCK = CoeffsTable(sa_damping=5, table="""\
 IMT     k_adj           a1              a2              b1              b2              Rm             phi_11   phi_21   C2       Mc1  Mc2 Rc11    Rc21  phi_SS
 pga     0.770968000     6.308282E+00    1.000000E+00    9.814496E-01    -7.784689E-01   7.056087E+01   0.58000  0.47000  0.35000  5    7   16      36    0.46000
 0.010   0.770968000     6.308282E+00    1.000000E+00    9.814496E-01    -7.784689E-01   7.056087E+01   0.58000  0.47000  0.35000  5    7   16      36    0.46000
 0.050   0.781884504     6.242341E+00    1.000000E+00    9.792917E-01    -7.239180E-01   7.736220E+01   0.55204  0.44903  0.40592  5    7   16      36    0.45301
 0.100   0.745908877     5.332961E+00    1.000000E+00    9.742506E-01    -1.092188E+00   4.880096E+01   0.54000  0.44000  0.43000  5    7   16      36    0.45000
 0.150   0.744117229     4.545627E+00    1.000000E+00    9.824773E-01    -9.934861E-01   5.436996E+01   0.58095  0.47510  0.40075  5    7   16      36    0.46755
 0.200   0.744577747     3.987006E+00    1.000000E+00    9.883142E-01    -9.234564E-01   5.832123E+01   0.61000  0.50000  0.38000  5    7   16      36    0.48000
 0.250   0.748103885     3.824292E+00    1.000000E+00    9.902861E-01    -8.590989E-01   6.387936E+01   0.62651  0.50000  0.37450  5    7   16      36    0.48000
 0.300   0.755136175     3.691346E+00    1.000000E+00    9.918973E-01    -8.065151E-01   6.842068E+01   0.64000  0.50000  0.37000  5    7   16      36    0.48000
 0.400   0.767879693     4.056852E+00    1.000000E+00    9.932212E-01    -8.277473E-01   6.639628E+01   0.61747  0.48874  0.37000  5    7   16      36    0.46874
 0.500   0.778052686     3.955542E+00    1.000000E+00    9.943901E-01    -7.686919E-01   7.702964E+01   0.60000  0.48000  0.37000  5    7   16      36    0.46000
 0.750   0.796961618     3.771458E+00    1.000000E+00    9.965141E-01    -6.613849E-01   9.635109E+01   0.56490  0.46245  0.38755  5    7   16      36    0.45415
 1.000   0.804115657     3.640847E+00    1.000000E+00    9.980211E-01    -5.852493E-01   1.100599E+02   0.54000  0.45000  0.40000  5    7   16      36    0.45000
 1.500   0.806238935     3.010737E+00    1.000000E+00    9.987325E-01    -5.862774E-01   1.098648E+02   0.53631  0.43155  0.40000  5    7   16      36    0.43524
 2.000   0.809163942     2.563667E+00    1.000000E+00    9.992372E-01    -5.870069E-01   1.097264E+02   0.53369  0.41845  0.40000  5    7   16      36    0.42476
 3.000   0.822779154     2.563667E+00    1.000000E+00    9.992372E-01    -5.870069E-01   1.097264E+02   0.53000  0.40000  0.40000  5    7   16      36    0.41000
 4.000   0.835713694     2.563667E+00    1.000000E+00    9.992372E-01    -5.870069E-01   1.097264E+02   0.53000  0.40000  0.40000  5    7   16      36    0.41000
 5.000   0.847331737     2.563667E+00    1.000000E+00    9.992372E-01    -5.870069E-01   1.097264E+02   0.53000  0.40000  0.40000  5    7   16      36    0.41000
 7.500   0.874425160     2.563667E+00    1.000000E+00    9.992372E-01    -5.870069E-01   1.097264E+02   0.53000  0.40000  0.40000  5    7   16      36    0.41000
 10.00   0.894172022     2.563667E+00    1.000000E+00    9.992372E-01    -5.870069E-01   1.097264E+02   0.53000  0.40000  0.40000  5    7   16      36    0.41000

    """)


class ChiouYoungs2008SWISS06(ChiouYoungs2008):

    """
    --------------------------------------------------------------------
    This class implments an extension of the Chiou & Youngs (2008) model,
    adjusted to be used for the new Swiss Hazard Model [2014].
    1) kappa value
       K-adjustments corresponding to model 06 (mid model)- as prepared by Ben Edwards
       K-value for PGA were not provided but infered from SA[]0.01s]
       the model considers a fixed value of vs30=1100m/s
    2) small-magnitude correction
    3) single station sigma - mean inter-event adjustment
    4) single station sigma - inter-event magnitude/distance dependent
    ------------------------------------------------------------------------
    Disclaimer: these equations are modified to be used for the
    new Swiss Seismic Hazard Model [2014].
    The use of these models is the soly responsability of the hazard modeler.
    --------------------------------------------------------------------
    Model implmented by laurentiu.danciu@sed.ethz.ch
    --------------------------------------------------------------------
    """

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):

        C_ADJ = self.COEFFS_FS_ROCK[imt]
        C = self.COEFFS[imt]
        C1_rrup = self._compute_C1_term(C_ADJ, imt, dists)
        phi_ss = self._compute_phi_ss(C_ADJ, rup, C1_rrup, imt)

        ln_y_ref = self._get_ln_y_ref(rup, dists, self.COEFFS[imt])

        exp1 = np.exp(C['phi3'] * (sites.vs30.clip(-np.inf, 1130) - 360))

        exp2 = np.exp(C['phi3'] * (1130 - 360))

        mean, stddevs = super(ChiouYoungs2008SWISS06, self).\
            get_mean_and_stddevs(sites, rup, dists, imt, stddev_types)

        mean_corr = np.exp(
            mean) * C_ADJ['k_adj'] * self._compute_small_mag_correction_term(C_ADJ, rup.mag, dists.rrup)
        mean = np.log(mean_corr)

        std_corr = self._get_corr_stddevs(
            C, rup, stddev_types, ln_y_ref, exp1, exp2, phi_ss, sites)
        stddevs = np.array(std_corr)

        return mean, stddevs

    def _compute_small_mag_correction_term(self, C, mag, rrup):
        """
        small magnitude correction applied to the median values
        """
        if mag >= 3.00 and mag < 5.5:
            return 1 / np.exp(((5.50 - mag) / C['a1']) ** C['a2'] * (C['b1'] + C['b2'] * np.log(np.maximum(np.minimum(rrup, C['Rm']), 10) / 20)))
        elif mag >= 5.50:
            return 1
        else:
            return 1

    def _get_corr_stddevs(self, C, rup, stddev_types, ln_y_ref, exp1, exp2, phi_ss, sites):
        """
        Return standard deviations adjusted for single station sigma
        as the total standard deviation - as proposed to be used in
        the new Swiss Hazard Model [2014].
        """
        # aftershock flag is zero, we consider only main shock.
        AS = 0
        Fmeasured = sites.vs30measured
        Finferred = 1 - sites.vs30measured

        # eq. 19 to calculate inter-event standard error
        mag_test = min(max(rup.mag, 5.0), 7.0) - 5.0
        tau = C['tau1'] + (C['tau2'] - C['tau1']) / 2 * mag_test

        # b and c coeffs from eq. 10
        b = C['phi2'] * (exp1 - exp2)
        c = C['phi4']

        y_ref = np.exp(ln_y_ref)
        # eq. 20
        NL = b * y_ref / (y_ref + c)
        ret = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                # eq. 21
                ret += [np.sqrt(((1 + NL) ** 2) * (tau ** 2) + (phi_ss ** 2))]
            elif stddev_type == const.StdDev.INTRA_EVENT:
                ret.append(phi_ss)
            elif stddev_type == const.StdDev.INTER_EVENT:
                # this is implied in eq. 21
                ret.append(np.abs((1 + NL) * tau))
        return ret

    def _compute_C1_term(self, C, imt, dists):
        """
        Return C1 coeffs as function of Rrup as proposed by Rodriguez-Marek et al (2013)
        The C1 coeff are used to compute the single station sigma
        """
        C1_rrup = 0.0
        if (dists.rrup < C['Rc11']).any():
            C1_rrup = C['phi_11']
        elif ((dists.rrup >= C['Rc11']).any()
                and (dists.rrup <= C['Rc21']).any()):
            C1_rrup = C['phi_11'] + (C['phi_21'] - C['phi_11']) * \
                ((dists.rrup - C['Rc11']) / (C['Rc21'] - C['Rc11']))
        elif (dists.rrup > C['Rc21']).any():
            C1_rrup = C['phi_21']
        return C1_rrup

    def _compute_phi_ss(self, C, rup, C1_rrup, imt):
        """
        Return C1 coeffs as function of Rrup as proposed by Rodriguez-Marek et al (2013)
        The C1 coeff are used to compute the single station sigma
        retunr phi_ss in log10 units
        """
        phi_ss = 0

        if rup.mag < C['Mc1']:
            phi_ss = C1_rrup
        elif rup.mag >= C['Mc1'] and rup.mag <= C['Mc2']:
            phi_ss = C1_rrup + \
                (C['C2'] - C1_rrup) * \
                ((rup.mag - C['Mc1']) / (C['Mc2'] - C['Mc1']))
        elif rup.mag > C['Mc2']:
            phi_ss = C['C2']
        return (phi_ss)

    COEFFS_FS_ROCK = CoeffsTable(sa_damping=5, table="""\
 IMT     k_adj                   a1              a2              b1              b2              Rm     phi_11   phi_21   C2       Mc1  Mc2 Rc11    Rc21 phi_SS
 pga     0.907406000     6.308282E+00    1.000000E+00    9.814496E-01    -7.784689E-01   7.056087E+01   0.58000  0.47000  0.35000  5    7   16      36   0.46000
 0.010   0.907406000     6.308282E+00    1.000000E+00    9.814496E-01    -7.784689E-01   7.056087E+01   0.58000  0.47000  0.35000  5    7   16      36   0.46000
 0.050   1.052062325     6.242341E+00    1.000000E+00    9.792917E-01    -7.239180E-01   7.736220E+01   0.55204  0.44903  0.40592  5    7   16      36   0.45301
 0.100   0.903944171     5.332961E+00    1.000000E+00    9.742506E-01    -1.092188E+00   4.880096E+01   0.54000  0.44000  0.43000  5    7   16      36   0.45000
 0.150   0.846557682     4.545627E+00    1.000000E+00    9.824773E-01    -9.934861E-01   5.436996E+01   0.58095  0.47510  0.40075  5    7   16      36   0.46755
 0.200   0.8152693       3.987006E+00    1.000000E+00    9.883142E-01    -9.234564E-01   5.832123E+01   0.61000  0.50000  0.38000  5    7   16      36   0.48000
 0.250   0.797908534     3.824292E+00    1.000000E+00    9.902861E-01    -8.590989E-01   6.387936E+01   0.62651  0.50000  0.37450  5    7   16      36   0.48000
 0.300   0.789245393     3.691346E+00    1.000000E+00    9.918973E-01    -8.065151E-01   6.842068E+01   0.64000  0.50000  0.37000  5    7   16      36   0.48000
 0.400   0.78042074      4.056852E+00    1.000000E+00    9.932212E-01    -8.277473E-01   6.639628E+01   0.61747  0.48874  0.37000  5    7   16      36   0.46874
 0.500   0.777925382     3.955542E+00    1.000000E+00    9.943901E-01    -7.686919E-01   7.702964E+01   0.60000  0.48000  0.37000  5    7   16      36   0.46000
 0.750   0.786471408     3.771458E+00    1.000000E+00    9.965141E-01    -6.613849E-01   9.635109E+01   0.56490  0.46245  0.38755  5    7   16      36   0.45415
 1.000   0.804234088     3.640847E+00    1.000000E+00    9.980211E-01    -5.852493E-01   1.100599E+02   0.54000  0.45000  0.40000  5    7   16      36   0.45000
 1.500   0.839944334     3.010737E+00    1.000000E+00    9.987325E-01    -5.862774E-01   1.098648E+02   0.53631  0.43155  0.40000  5    7   16      36   0.43524
 2.000   0.865068228     2.563667E+00    1.000000E+00    9.992372E-01    -5.870069E-01   1.097264E+02   0.53369  0.41845  0.40000  5    7   16      36   0.42476
 3.000   0.893179655     2.563667E+00    1.000000E+00    9.992372E-01    -5.870069E-01   1.097264E+02   0.53000  0.40000  0.40000  5    7   16      36   0.41000
 4.000   0.904833501     2.563667E+00    1.000000E+00    9.992372E-01    -5.870069E-01   1.097264E+02   0.53000  0.40000  0.40000  5    7   16      36   0.41000
 5.000   0.911805616     2.563667E+00    1.000000E+00    9.992372E-01    -5.870069E-01   1.097264E+02   0.53000  0.40000  0.40000  5    7   16      36   0.41000
 7.500   0.929535851     2.563667E+00    1.000000E+00    9.992372E-01    -5.870069E-01   1.097264E+02   0.53000  0.40000  0.40000  5    7   16      36   0.41000
 10.00   0.942324350     2.563667E+00    1.000000E+00    9.992372E-01    -5.870069E-01   1.097264E+02   0.53000  0.40000  0.40000  5    7   16      36   0.41000
    """)


class ChiouYoungs2008SWISS04(ChiouYoungs2008):

    """
    --------------------------------------------------------------------
    This class implments an extension of the Chiou & Youngs (2008) model,
    adjusted to be used for the new Swiss Hazard Model [2014].
    1) kappa value
       K-adjustments corresponding to model 04 (upper bound) - as prepared by Ben Edwards
       K-value for PGA were not provided but infered from SA[]0.01s]
       the model considers a fixed value of vs30=1100m/s
    2) small-magnitude correction
    3) single station sigma - mean inter-event adjustment
    4) single station sigma - inter-event magnitude/distance dependent
    ------------------------------------------------------------------------
    Disclaimer: these equations are modified to be used for the
    new Swiss Seismic Hazard Model [2014].
    The use of these models is the soly responsability of the hazard modeler.
    --------------------------------------------------------------------
    Model implmented by laurentiu.danciu@sed.ethz.ch
    --------------------------------------------------------------------
    """

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):

        C_ADJ = self.COEFFS_FS_ROCK[imt]
        C = self.COEFFS[imt]
        C1_rrup = self._compute_C1_term(C_ADJ, imt, dists)
        phi_ss = self._compute_phi_ss(C_ADJ, rup, C1_rrup, imt)

        ln_y_ref = self._get_ln_y_ref(rup, dists, self.COEFFS[imt])

        exp1 = np.exp(C['phi3'] * (sites.vs30.clip(-np.inf, 1130) - 360))

        exp2 = np.exp(C['phi3'] * (1130 - 360))

        mean, stddevs = super(ChiouYoungs2008SWISS04, self).\
            get_mean_and_stddevs(sites, rup, dists, imt, stddev_types)

        mean_corr = np.exp(
            mean) * C_ADJ['k_adj'] * self._compute_small_mag_correction_term(C_ADJ, rup.mag, dists.rrup)
        mean = np.log(mean_corr)

        std_corr = self._get_corr_stddevs(
            C, rup, stddev_types, ln_y_ref, exp1, exp2, phi_ss, sites)
        stddevs = np.array(std_corr)

        return mean, stddevs

    def _compute_small_mag_correction_term(self, C, mag, rrup):
        """
        small magnitude correction applied to the median values
        """
        if mag >= 3.00 and mag < 5.5:
            return 1 / np.exp(((5.50 - mag) / C['a1']) ** C['a2'] * (C['b1'] + C['b2'] * np.log(np.maximum(np.minimum(rrup, C['Rm']), 10) / 20)))
        elif mag >= 5.50:
            return 1
        else:
            return 1

    def _get_corr_stddevs(self, C, rup, stddev_types, ln_y_ref, exp1, exp2, phi_ss, sites):
        """
        Return standard deviations adjusted for single station sigma
        as the total standard deviation - as proposed to be used in
        the new Swiss Hazard Model [2014].
        """
        # aftershock flag is zero, we consider only main shock.
        AS = 0
        Fmeasured = sites.vs30measured
        Finferred = 1 - sites.vs30measured

        # eq. 19 to calculate inter-event standard error
        mag_test = min(max(rup.mag, 5.0), 7.0) - 5.0
        tau = C['tau1'] + (C['tau2'] - C['tau1']) / 2 * mag_test

        # b and c coeffs from eq. 10
        b = C['phi2'] * (exp1 - exp2)
        c = C['phi4']

        y_ref = np.exp(ln_y_ref)
        # eq. 20
        NL = b * y_ref / (y_ref + c)
        ret = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                # eq. 21
                ret += [np.sqrt(((1 + NL) ** 2) * (tau ** 2) + (phi_ss ** 2))]
            elif stddev_type == const.StdDev.INTRA_EVENT:
                ret.append(phi_ss)
            elif stddev_type == const.StdDev.INTER_EVENT:
                # this is implied in eq. 21
                ret.append(np.abs((1 + NL) * tau))
        return ret

    def _compute_C1_term(self, C, imt, dists):
        """
        Return C1 coeffs as function of Rrup as proposed by Rodriguez-Marek et al (2013)
        The C1 coeff are used to compute the single station sigma
        """
        C1_rrup = 0.0
        if (dists.rrup < C['Rc11']).any():
            C1_rrup = C['phi_11']
        elif ((dists.rrup >= C['Rc11']).any()
                and (dists.rrup <= C['Rc21']).any()):
            C1_rrup = C['phi_11'] + (C['phi_21'] - C['phi_11']) * \
                ((dists.rrup - C['Rc11']) / (C['Rc21'] - C['Rc11']))
        elif (dists.rrup > C['Rc21']).any():
            C1_rrup = C['phi_21']
        return C1_rrup

    def _compute_phi_ss(self, C, rup, C1_rrup, imt):
        """
        Return C1 coeffs as function of Rrup as proposed by Rodriguez-Marek et al (2013)
        The C1 coeff are used to compute the single station sigma
        retunr phi_ss in log10 units
        """
        phi_ss = 0

        if rup.mag < C['Mc1']:
            phi_ss = C1_rrup
        elif rup.mag >= C['Mc1'] and rup.mag <= C['Mc2']:
            phi_ss = C1_rrup + \
                (C['C2'] - C1_rrup) * \
                ((rup.mag - C['Mc1']) / (C['Mc2'] - C['Mc1']))
        elif rup.mag > C['Mc2']:
            phi_ss = C['C2']
        return (phi_ss)

    COEFFS_FS_ROCK = CoeffsTable(sa_damping=5, table="""\
IMT     k_adj                   a1              a2              b1              b2              Rm      phi_11   phi_21   C2       Mc1  Mc2 Rc11    Rc21  phi_SS
pga     1.144220000    6.308282E+00    1.000000E+00    9.814496E-01    -7.784689E-01   7.056087E+01     0.58000  0.47000  0.35000  5    7   16      36    0.46000
0.010   1.144220000    6.308282E+00    1.000000E+00    9.814496E-01    -7.784689E-01   7.056087E+01     0.58000  0.47000  0.35000  5    7   16      36    0.46000
0.050   1.582364006    6.242341E+00    1.000000E+00    9.792917E-01    -7.239180E-01   7.736220E+01     0.55204  0.44903  0.40592  5    7   16      36    0.45301
0.100   1.134260083    5.332961E+00    1.000000E+00    9.742506E-01    -1.092188E+00   4.880096E+01     0.54000  0.44000  0.43000  5    7   16      36    0.45000
0.150   0.997131538    4.545627E+00    1.000000E+00    9.824773E-01    -9.934861E-01   5.436996E+01     0.58095  0.47510  0.40075  5    7   16      36    0.46755
0.200   0.931483355    3.987006E+00    1.000000E+00    9.883142E-01    -9.234564E-01   5.832123E+01     0.61000  0.50000  0.38000  5    7   16      36    0.48000
0.250   0.896609692    3.824292E+00    1.000000E+00    9.902861E-01    -8.590989E-01   6.387936E+01     0.62651  0.50000  0.37450  5    7   16      36    0.48000
0.300   0.879037052    3.691346E+00    1.000000E+00    9.918973E-01    -8.065151E-01   6.842068E+01     0.64000  0.50000  0.37000  5    7   16      36    0.48000
0.400   0.861457717    4.056852E+00    1.000000E+00    9.932212E-01    -8.277473E-01   6.639628E+01     0.61747  0.48874  0.37000  5    7   16      36    0.46874
0.500   0.853567498    3.955542E+00    1.000000E+00    9.943901E-01    -7.686919E-01   7.702964E+01     0.60000  0.48000  0.37000  5    7   16      36    0.46000
0.750   0.848145374    3.771458E+00    1.000000E+00    9.965141E-01    -6.613849E-01   9.635109E+01     0.56490  0.46245  0.38755  5    7   16      36    0.45415
1.000   0.842662116    3.640847E+00    1.000000E+00    9.980211E-01    -5.852493E-01   1.100599E+02     0.54000  0.45000  0.40000  5    7   16      36    0.45000
1.500   0.831445701    3.010737E+00    1.000000E+00    9.987325E-01    -5.862774E-01   1.098648E+02     0.53631  0.43155  0.40000  5    7   16      36    0.43524
2.000   0.827607473    2.563667E+00    1.000000E+00    9.992372E-01    -5.870069E-01   1.097264E+02     0.53369  0.41845  0.40000  5    7   16      36    0.42476
3.000   0.835774855    2.563667E+00    1.000000E+00    9.992372E-01    -5.870069E-01   1.097264E+02     0.53000  0.40000  0.40000  5    7   16      36    0.41000
4.000   0.848240349    2.563667E+00    1.000000E+00    9.992372E-01    -5.870069E-01   1.097264E+02     0.53000  0.40000  0.40000  5    7   16      36    0.41000
5.000   0.861360769    2.563667E+00    1.000000E+00    9.992372E-01    -5.870069E-01   1.097264E+02     0.53000  0.40000  0.40000  5    7   16      36    0.41000
7.500   0.892087590    2.563667E+00    1.000000E+00    9.992372E-01    -5.870069E-01   1.097264E+02     0.53000  0.40000  0.40000  5    7   16      36    0.41000
10.00   0.914551086    2.563667E+00    1.000000E+00    9.992372E-01    -5.870069E-01   1.097264E+02     0.53000  0.40000  0.40000  5    7   16      36    0.41000
    """)


class ChiouYoungs2008SWISS01T(ChiouYoungs2008SWISS01):

    """
    --------------------------------------------------------------------
    This class implments an extension of the Chiou & Youngs(2008) model,
    adjusted to be used for the new Swiss Hazard Model [2014].
    1) kappa value
       K-adjustments corresponding to model 01 - as prepared by Ben Edwards
       K-value for PGA were not provided but infered from SA[]0.01s]
       the model considers a fixed value of vs30=1100m/s
    2) small-magnitude correction
    3) single station sigma - mean inter-event adjustment
    4) single station sigma - inter-event magnitude/distance dependent
    --------------------------------------------------------------------
    This implmentation of the CY2008 Model considers the mean inter-event
    adjustement when computing the single station sigma (reported as total
    standard deviation))
    ------------------------------------------------------------------------
    Disclaimer: these equations are modified to be used for the
    new Swiss Seismic Hazard Model [2014].
    The use of these models is the soly responsability of the hazard modeler.
    --------------------------------------------------------------------
    Model implmented by laurentiu.danciu@sed.ethz.ch
    --------------------------------------------------------------------
    """

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):

        C_ADJ = self.COEFFS_FS_ROCK[imt]

        C = self.COEFFS[imt]

        ln_y_ref = self._get_ln_y_ref(rup, dists, C)
        exp1 = np.exp(C['phi3'] * (sites.vs30.clip(-np.inf, 1130) - 360))
        exp2 = np.exp(C['phi3'] * (1130 - 360))

        mean, stddevs = super(ChiouYoungs2008SWISS01T, self).\
            get_mean_and_stddevs(sites, rup, dists, imt, stddev_types)

        std_corr = self._get_corr_stddevs(
            C, rup, stddev_types, ln_y_ref, exp1, exp2, C_ADJ['phi_SS'], sites)
        stddevs = np.array(std_corr)

        return mean, stddevs


class ChiouYoungs2008SWISS06T(ChiouYoungs2008SWISS06):

    """
    --------------------------------------------------------------------
    This class implments an extension of the Chiou & Youngs(2008) model,
    adjusted to be used for the new Swiss Hazard Model [2014].
    1) kappa value
       K-adjustments corresponding to model 06 (mid model)- as prepared by Ben Edwards
       K-value for PGA were not provided but infered from SA[]0.01s]
       the model considers a fixed value of vs30=1100m/s
    2) small-magnitude correction
    3) single station sigma - mean inter-event adjustment
    4) single station sigma - inter-event magnitude/distance dependent
    --------------------------------------------------------------------
    This implmentation of the CY2008 Model considers the mean inter-event
    adjustement when computing the single station sigma (reported as total
    standard deviation))
    ------------------------------------------------------------------------
    Disclaimer: these equations are modified to be used for the
    new Swiss Seismic Hazard Model [2014].
    The use of these models is the soly responsability of the hazard modeler.
    --------------------------------------------------------------------
    Model implmented by laurentiu.danciu@sed.ethz.ch
    --------------------------------------------------------------------
    """

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):

        C_ADJ = self.COEFFS_FS_ROCK[imt]
        C = self.COEFFS[imt]

        C1_rrup = self._compute_C1_term(C_ADJ, imt, dists)
        phi_ss = self._compute_phi_ss(C_ADJ, rup, C1_rrup, imt)

        ln_y_ref = self._get_ln_y_ref(rup, dists, self.COEFFS[imt])
        exp1 = np.exp(C['phi3'] * (sites.vs30.clip(-np.inf, 1130) - 360))
        exp2 = np.exp(C['phi3'] * (1130 - 360))

        mean, stddevs = super(ChiouYoungs2008SWISS06T, self).\
            get_mean_and_stddevs(sites, rup, dists, imt, stddev_types)

        std_corr = self._get_corr_stddevs(
            C, rup, stddev_types, ln_y_ref, exp1, exp2, C_ADJ['phi_SS'], sites)
        stddevs = np.array(std_corr)

        return mean, stddevs


class ChiouYoungs2008SWISS04T(ChiouYoungs2008SWISS04):

    """
    --------------------------------------------------------------------
    This class implments an extension of the Chiou & Youngs(2008) model,
    adjusted to be used for the new Swiss Hazard Model [2014].
    1) kappa value
       K-adjustments corresponding to model 04 (upper bound) - as prepared by Ben Edwards
       K-value for PGA were not provided but infered from SA[]0.01s]
       the model considers a fixed value of vs30=1100m/s
    2) small-magnitude correction
    3) single station sigma - mean inter-event adjustment
    4) single station sigma - inter-event magnitude/distance dependent
    --------------------------------------------------------------------
    This implmentation of the CY2008 Model considers the mean inter-event
    adjustement when computing the single station sigma (reported as total
    standard deviation))
    ------------------------------------------------------------------------
    Disclaimer: these equations are modified to be used for the
    new Swiss Seismic Hazard Model [2014].
    The use of these models is the soly responsability of the hazard modeler.
    --------------------------------------------------------------------
    Model implmented by laurentiu.danciu@sed.ethz.ch
    --------------------------------------------------------------------
    """

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):

        C_ADJ = self.COEFFS_FS_ROCK[imt]
        C = self.COEFFS[imt]

        C1_rrup = self._compute_C1_term(C_ADJ, imt, dists)
        phi_ss = self._compute_phi_ss(C_ADJ, rup, C1_rrup, imt)

        ln_y_ref = self._get_ln_y_ref(rup, dists, self.COEFFS[imt])
        exp1 = np.exp(C['phi3'] * (sites.vs30.clip(-np.inf, 1130) - 360))
        exp2 = np.exp(C['phi3'] * (1130 - 360))

        mean, stddevs = super(ChiouYoungs2008SWISS04T, self).\
            get_mean_and_stddevs(sites, rup, dists, imt, stddev_types)

        std_corr = self._get_corr_stddevs(
            C, rup, stddev_types, ln_y_ref, exp1, exp2, C_ADJ['phi_SS'], sites)
        stddevs = np.array(std_corr)

        return mean, stddevs
