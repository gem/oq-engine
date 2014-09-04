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
from openquake.hazardlib.gsim.edwards_fah_2013a import (
                                        EdwardsFah2013Alpine60MPa,
                                        EdwardsFah2013Alpine60MPaMR)
from openquake.hazardlib.gsim.edwards_fah_2013f_coeffs import (
                                        COEFFS_FORELAND_60Bars,
                                        COEFFS_FORELAND_10Bars,
                                        COEFFS_FORELAND_20Bars,
                                        COEFFS_FORELAND_30Bars,
                                        COEFFS_FORELAND_50Bars,
                                        COEFFS_FORELAND_75Bars,
                                        COEFFS_FORELAND_90Bars,
                                        COEFFS_FORELAND_120Bars)

class EdwardsFah2013Foreland60MPa(EdwardsFah2013Alpine60MPa):

    """
    This function implements the GMPE developed by Ben Edwards and 
    Donath Fah and published as "A Stochastic Ground-Motion Model 
    for Switzerland" Bulletin of the Seismological
    Society of America, Vol. 103, No. 1, pp. 78–98, February 2013.
    The GMPE was parametrized by Carlo Cauzzi to be implemented in OpenQuake.
    This class implements the equations for 'Foreland - two
    tectonic regionalizations defined for the Switzerland -
    therefore this GMPE is region specific".
    """

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        compute mean for Foreland
        """
        C = self.COEFFS[imt]
        R = self._compute_term_d(C, rup.mag, dists.rrup)

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

    def _compute_term_d(self, C, mag, rrup):
        """
        Compute distance term: original implementation from Carlo Cauzzi
        if M > 5.5     rmin = 0.55;
        elseif M > 4.7 rmin = -2.067.*M +11.92;
        else           rmin = -0.291.*M + 3.48;
        end
        d = log10(max(R,rmin));
        """
        if mag > self.M1:
            rrup_min = 0.55
        elif mag > self.M2:
            rrup_min = -2.067 * mag + 11.92
        else:
            rrup_min = -0.291 * mag + 3.48

        R = np.maximum(rrup_min, rrup)

        return np.log10(R)

    #: Fixed magnitude terms

    M1 = 5.00
    M2 = 4.70

    COEFFS=COEFFS_FORELAND_60Bars

class EdwardsFah2013Foreland10MPa(EdwardsFah2013Foreland60MPa):

    COEFFS=COEFFS_FORELAND_10Bars

class EdwardsFah2013Foreland20MPa(EdwardsFah2013Foreland60MPa):

    COEFFS=COEFFS_FORELAND_20Bars

class EdwardsFah2013Foreland30MPa(EdwardsFah2013Foreland60MPa):

    COEFFS=COEFFS_FORELAND_30Bars

class EdwardsFah2013Foreland50MPa(EdwardsFah2013Foreland60MPa):

    COEFFS=COEFFS_FORELAND_50Bars

class EdwardsFah2013Foreland75MPa(EdwardsFah2013Foreland60MPa):

    COEFFS=COEFFS_FORELAND_75Bars

class EdwardsFah2013Foreland90MPa(EdwardsFah2013Foreland60MPa):

    COEFFS=COEFFS_FORELAND_90Bars

class EdwardsFah2013Foreland120MPa(EdwardsFah2013Foreland60MPa):

    COEFFS=COEFFS_FORELAND_120Bars

class EdwardsFah2013Foreland60MPaMR(EdwardsFah2013Foreland60MPa):
    """
    Adjustment of a single station sigma for magnitude and distance dependance
    """

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):

        mean, stddevs = super(EdwardsFah2013Foreland60MPaMR, self).\
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

class EdwardsFah2013Foreland10MPaMR(EdwardsFah2013Foreland60MPaMR):
    COEFFS=COEFFS_FORELAND_10Bars

class EdwardsFah2013Foreland20MPaMR(EdwardsFah2013Foreland60MPaMR):
    COEFFS=COEFFS_FORELAND_20Bars

class EdwardsFah2013Foreland30MPaMR(EdwardsFah2013Foreland60MPaMR):
    COEFFS=COEFFS_FORELAND_30Bars

class EdwardsFah2013Foreland50MPaMR(EdwardsFah2013Foreland60MPaMR):
    COEFFS=COEFFS_FORELAND_50Bars

class EdwardsFah2013Foreland75MPaMR(EdwardsFah2013Foreland60MPaMR):
    COEFFS=COEFFS_FORELAND_75Bars

class EdwardsFah2013Foreland90MPaMR(EdwardsFah2013Foreland60MPaMR):
    COEFFS=COEFFS_FORELAND_90Bars

class EdwardsFah2013Foreland120MPaMR(EdwardsFah2013Foreland60MPaMR):
    COEFFS=COEFFS_FORELAND_120Bars

