# -*- coding: utf-8 -*-
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

from __future__ import division
import numpy as np
from scipy.constants import g
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGV, PGA, SA
from openquake.hazardlib.gsim.edwards_fah_2013a_coeffs import (
                                                    COEFFS_ALPINE_60Bars,
                                                    COEFFS_ALPINE_10Bars,
                                                    COEFFS_ALPINE_20Bars,
                                                    COEFFS_ALPINE_30Bars,
                                                    COEFFS_ALPINE_50Bars,
                                                    COEFFS_ALPINE_75Bars,
                                                    COEFFS_ALPINE_90Bars,
                                                    COEFFS_ALPINE_120Bars)

class EdwardsFah2013Alpine60MPa(GMPE):

    """
    This function implements the GMPE developed by Ben Edwars and Donath Fah 
    and published as "A Stochastic Ground-Motion Model for Switzerland" 
    Bulletin of the Seismological Society of America, 
    Vol. 103, No. 1, pp. 78–98, February 2013.
    The GMPE was parametrized by Carlo Cauzzi to be implemented in OpenQuake.
    This class implements the equations for 'Alpine' and 'Foreland - two
    tectonic regionalizations defined for the Switzerland -
    therefore this GMPE is region specific".
    @ implemented by laurentiu.danciu@sed.ethz.zh
    """
    #: Supported tectonic region type is ALPINE which
    #: is a sub-region of Active Shallow Crust.
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST
    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration, see tables 3 and 4, pages 227 and 228.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGV,
        PGA,
        SA
    ])
    #: Supported intensity measure component is ?
    #: ask Carlo Cauzzi
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL
    #: Supported standard deviation types is total,
    #: Carlo Cauzzi - Personal Communications
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL
    ])

    #: Required site parameter is only Vs30 (used to distinguish rock
    #: and deep soil).
    REQUIRES_SITES_PARAMETERS = set(('vs30', ))
    #: Required rupture parameters: magnitude
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', ))

    #: Required distance measure is Rrup
    REQUIRES_DISTANCES = set(('rrup', ))

    #: Vs30 value representing typical rock conditions in Switzerland.
    #: confirmed by the Swiss GMPE group
    ROCK_VS30 = 1105
    #: [g] = 9.81 m/s

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """

        C = self.COEFFS[imt]
        R = self._compute_term_r(C, rup.mag, dists.rrup)

        mean = 10 ** (self._compute_mean(C, rup.mag, R))

        # Convert units to g,
        # but only for PGA and SA (not PGV):
        if isinstance(imt, (PGA, SA)):
            mean = np.log(mean / 981)
        else:
            # PGV:
            mean = np.log(mean)

        stddevs = self._get_stddevs(C, stddev_types, sites.vs30.shape[0])

        return mean, stddevs

        # return stddevs
    def _get_stddevs(self, C, stddev_types, num_sites):
        """
        Return standard deviations
        """
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(C['sigma_tot'] + np.zeros(num_sites))
            elif stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(C['phi_SS'] + np.zeros(num_sites))
            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(C['tau'] + np.zeros(num_sites))
        return stddevs

    def _compute_term_r(self, C, mag, rrup):
        """
        Compute distance term
        d = log10(max(R,rmin));
        """
        if mag > self.M1:
            rrup_min = 0.55

        elif mag > self.M2:
            rrup_min = -2.80 * mag + 14.55

        else:
            rrup_min = -0.295 * mag + 2.65

        R = np.maximum(rrup_min, rrup)

        return np.log10(R)

    def _compute_term_1(self, C, mag):
        """
        Compute term 1
        a1 + a2.*M + a3.*M.^2 + a4.*M.^3 + a5.*M.^4 + a6.*M.^5 + a7.*M.^6
        """
        return (
            C['a1'] + C['a2'] * mag + C['a3'] *
            np.power(mag, 2) + C['a4'] * np.power(mag, 3)
            + C['a5'] * np.power(mag, 4) + C['a6'] *
            np.power(mag, 5) + C['a7'] * np.power(mag, 6)
        )

    def _compute_term_2(self, C, mag, R):
        """
        (a8 + a9.*M + a10.*M.*M + a11.*M.*M.*M).*d(r)
        """
        return (
            (C['a8'] + C['a9'] * mag + C['a10'] * np.power(mag, 2) +
             C['a11'] * np.power(mag, 3)) * R
        )

    def _compute_term_3(self, C, mag, R):
        """
        (a12 + a13.*M + a14.*M.*M + a15.*M.*M.*M).*(d(r).^2)
        """
        return (
            (C['a12'] + C['a13'] * mag + C['a14'] * np.power(mag, 2) +
             C['a15'] * np.power(mag, 3)) * np.power(R, 2)
        )

    def _compute_term_4(self, C, mag, R):
        """
        (a16 + a17.*M + a18.*M.*M + a19.*M.*M.*M).*(d(r).^3)
        """
        return (
            (C['a16'] + C['a17'] * mag + C['a18'] * np.power(mag, 2) +
             C['a19'] * np.power(mag, 3)) * np.power(R, 3)
        )

    def _compute_term_5(self, C, mag, R):
        """
        (a20 + a21.*M + a22.*M.*M + a23.*M.*M.*M).*(d(r).^4)
        """
        return (
            (C['a20'] + C['a21'] * mag + C['a22'] * np.power(mag, 2) +
             C['a23'] * np.power(mag, 3)) * np.power(R, 4)
        )

    def _compute_mean(self, C, mag, term_dist_r):
        """
        compute mean
        """
        return (
            self._compute_term_1(C, mag) +
            self._compute_term_2(C, mag, term_dist_r) +
            self._compute_term_3(C, mag, term_dist_r) +
            self._compute_term_4(C, mag, term_dist_r) +
            self._compute_term_5(C, mag, term_dist_r)
        )

    #: Fixed magnitude terms
    M1 = 5.00
    M2 = 4.70

    COEFFS=COEFFS_ALPINE_60Bars

class EdwardsFah2013Alpine10MPa(EdwardsFah2013Alpine60MPa):

    COEFFS=COEFFS_ALPINE_10Bars

class EdwardsFah2013Alpine20MPa(EdwardsFah2013Alpine60MPa):

    COEFFS=COEFFS_ALPINE_20Bars

class EdwardsFah2013Alpine30MPa(EdwardsFah2013Alpine60MPa):

    COEFFS=COEFFS_ALPINE_30Bars

class EdwardsFah2013Alpine50MPa(EdwardsFah2013Alpine60MPa):

    COEFFS=COEFFS_ALPINE_50Bars

class EdwardsFah2013Alpine75MPa(EdwardsFah2013Alpine60MPa):

    COEFFS=COEFFS_ALPINE_75Bars

class EdwardsFah2013Alpine90MPa(EdwardsFah2013Alpine60MPa):

    COEFFS=COEFFS_ALPINE_90Bars

class EdwardsFah2013Alpine120MPa(EdwardsFah2013Alpine60MPa):

    COEFFS=COEFFS_ALPINE_120Bars

class EdwardsFah2013Alpine60MPaMR(EdwardsFah2013Alpine60MPa):
    """
    Adjustment of a single station sigma for magnitude and distance dependance
    """

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):

        mean, stddevs = super(EdwardsFah2013Alpine60MPaMR, self).\
            get_mean_and_stddevs(sites, rup, dists, imt, stddev_types)
        stddevs = self._apply_adjustments(stddevs, sites, rup, 
                        dists, imt, stddev_types)
        return mean, stddevs

    def _apply_adjustments(self, stddevs, sites, rup, dists, imt, 
                           stddev_types):

        C_ADJ = self.COEFFS[imt]
        c1_rrup = self._compute_C1_term(C_ADJ, imt, dists)
        phi_ss_mr = self._compute_phi_ss(C_ADJ, rup, c1_rrup, imt)
        
        std_corr = self._get_corr_stddevs(
            self.COEFFS[imt], stddev_types, len(sites.vs30), phi_ss_mr)
        stddevs = np.array(std_corr)

        return stddevs

    def _compute_C1_term(self, C, imt, dists):
        """
        Return C1 coeffs as function of Rrup as proposed by 
        Rodriguez-Marek et al (2013)
        The C1 coeff are used to compute the single station sigma
        """
        c1_rrup = np.zeros_like(dists.rrup)
        idx = dists.rrup < C['Rc11']
        c1_rrup[idx] = C['phi_11']
        idx = (dists.rrup >= C['Rc11']) & (dists.rrup <= C['Rc21'])
        c1_rrup[idx] = C['phi_11'] + \
            (C['phi_21'] - C['phi_11']) *  \
            ((dists.rrup[idx] - C['Rc11']) / (C['Rc21'] - C['Rc11']))
        idx = dists.rrup > C['Rc21']
        c1_rrup[idx] = C['phi_21']
        return c1_rrup

    def _compute_phi_ss(self, C, rup, c1_rrup, imt):
        """
        Return C1 coeffs as function of Rrup as proposed 
        by Rodriguez-Marek et al (2013)
        The C1 coeff are used to compute the single station sigma
        """
        phi_ss = 0

        if rup.mag < C['Mc1']:
            phi_ss = c1_rrup
        elif rup.mag >= C['Mc1'] and rup.mag <= C['Mc2']:
            phi_ss = c1_rrup + \
                (C['C2'] - c1_rrup) * \
                ((rup.mag - C['Mc1']) / (C['Mc2'] - C['Mc1']))
        elif rup.mag > C['Mc2']:
            phi_ss = C['C2']
        return phi_ss

    def _get_corr_stddevs(self, C, stddev_types, num_sites, phi_ss):
        """
        Return standard deviations adjusted for single station sigma
        as proposed to be used in the new Swiss Hazard Model [2014].
        """
        stddevs = []
        for stddev_type in stddev_types:
            assert stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(
                    np.sqrt(C['tau'] ** 2 + phi_ss ** 2) + np.zeros(num_sites))
        return stddevs
    COEFFS=COEFFS_ALPINE_60Bars


class EdwardsFah2013Alpine10MPaMR(EdwardsFah2013Alpine60MPaMR):

    COEFFS=COEFFS_ALPINE_10Bars

class EdwardsFah2013Alpine20MPaMR(EdwardsFah2013Alpine60MPaMR):

    COEFFS=COEFFS_ALPINE_20Bars

class EdwardsFah2013Alpine30MPaMR(EdwardsFah2013Alpine60MPaMR):

    COEFFS=COEFFS_ALPINE_30Bars

class EdwardsFah2013Alpine50MPaMR(EdwardsFah2013Alpine60MPaMR):

    COEFFS=COEFFS_ALPINE_50Bars

class EdwardsFah2013Alpine75MPaMR(EdwardsFah2013Alpine60MPaMR):

    COEFFS=COEFFS_ALPINE_75Bars

class EdwardsFah2013Alpine90MPaMR(EdwardsFah2013Alpine60MPaMR):

    COEFFS=COEFFS_ALPINE_90Bars

class EdwardsFah2013Alpine120MPaMR(EdwardsFah2013Alpine60MPaMR):

    COEFFS=COEFFS_ALPINE_120Bars
