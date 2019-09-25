# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2019 GEM Foundation
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
Module exports :class:`AfshariStewart2016`,
               :class:`AfshariStewart2016Japan`
"""
import numpy as np

from openquake.hazardlib.gsim.base import CoeffsTable, GMPE
from openquake.hazardlib import const
from openquake.hazardlib.imt import RSD595, RSD575, RSD2080


class AfshariStewart2016(GMPE):
    """
    Implements the GMPE of Afshari & Stewart (2016) for relative significant
    duration for 5 - 75 %, 5 - 95 % and 20 - 80 % Arias Intensity.

    Afshari, K. and Stewart, J. P. (2016) "Physically Parameterized Prediction
    Equations for Signficant Duration in Active Crustal Regions", Earthquake
    Spectra, 32(4), 2057 - 2081
    """
    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are 5 - 95 % Arias and 5 - 75 % Arias
    #: significant duration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        RSD595,
        RSD575,
        RSD2080
    ])

    #: Supported intensity measure component is the geometric mean horizontal
    #: component
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Supported standard deviation type is only total, see table 7, page 35
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    ])

    #: Requires vs30
    REQUIRES_SITES_PARAMETERS = set(('vs30', 'z1pt0'))

    #: Required rupture parameters are magnitude and top of rupture depth
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', 'rake'))

    #: Required distance measure is closest distance to rupture
    REQUIRES_DISTANCES = set(('rrup', ))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        C = self.COEFFS[imt]
        mean = (np.log(self.get_magnitude_term(C, rup) +
                       self.get_distance_term(C, dists.rrup)) +
                self.get_site_amplification(C, sites))
        stddevs = self.get_stddevs(C, sites.vs30.shape, rup.mag, stddev_types)
        return mean, stddevs

    def get_magnitude_term(self, C, rup):
        """
        Returns the magnitude scaling term in equation 3
        """
        b0, stress_drop = self._get_sof_terms(C, rup.rake)
        if rup.mag <= C["m1"]:
            return b0
        else:
            # Calculate moment (equation 5)
            m_0 = 10.0 ** (1.5 * rup.mag + 16.05)
            # Get stress-drop scaling (equation 6)
            if rup.mag > C["m2"]:
                stress_drop += (C["b2"] * (C["m2"] - self.CONSTANTS["mstar"]) +
                                (C["b3"] * (rup.mag - C["m2"])))
            else:
                stress_drop += (C["b2"] * (rup.mag - self.CONSTANTS["mstar"]))
            stress_drop = np.exp(stress_drop)
            # Get corner frequency (equation 4)
            f0 = 4.9 * 1.0E6 * 3.2 * ((stress_drop / m_0) ** (1. / 3.))
            return 1. / f0

    def get_distance_term(self, C, rrup):
        """
        Returns the distance scaling term in equation 7
        """
        f_p = C["c1"] * rrup
        idx = np.logical_and(rrup > self.CONSTANTS["r1"],
                             rrup <= self.CONSTANTS["r2"])
        f_p[idx] = (C["c1"] * self.CONSTANTS["r1"]) +\
            C["c2"] * (rrup[idx] - self.CONSTANTS["r1"])
        idx = rrup > self.CONSTANTS["r2"]
        f_p[idx] = C["c1"] * self.CONSTANTS["r1"] +\
            C["c2"] * (self.CONSTANTS["r2"] - self.CONSTANTS["r1"]) +\
            C["c3"] * (rrup[idx] - self.CONSTANTS["r2"])
        return f_p

    def _get_sof_terms(self, C, rake):
        """
        Returns the style-of-faulting scaling parameters
        """
        if rake >= 45.0 and rake <= 135.0:
            # Reverse faulting
            return C["b0R"], C["b1R"]
        elif rake <= -45. and rake >= -135.0:
            # Normal faulting
            return C["b0N"], C["b1N"]
        else:
            # Strike slip
            return C["b0SS"], C["b1SS"]

    def _get_lnmu_z1(self, vs30):
        """
        Returns the z1.0 normalisation term for California (equation 11)
        """
        return (-7.15 / 4.) * np.log(
            (vs30 ** 4. + 570.94 ** 4) / (1360.0 ** 4. + 570.94 ** 4.)) -\
            np.log(1000.0)

    def get_site_amplification(self, C, sites):
        """
        Returns the site amplification term
        """
        # Gets delta normalised z1
        dz1 = sites.z1pt0 - np.exp(self._get_lnmu_z1(sites.vs30))
        f_s = C["c5"] * dz1
        # Calculates site amplification term
        f_s[dz1 > self.CONSTANTS["dz1ref"]] = (C["c5"] *
                                               self.CONSTANTS["dz1ref"])
        idx = sites.vs30 > self.CONSTANTS["v1"]
        f_s[idx] += (C["c4"] * np.log(self.CONSTANTS["v1"] / C["vref"]))
        idx = np.logical_not(idx)
        f_s[idx] += (C["c4"] * np.log(sites.vs30[idx] / C["vref"]))
        return f_s

    def get_stddevs(self, C, nsites, mag, stddev_types):
        """
        Returns the standard deviations
        """
        tau = self._get_tau(C, mag) + np.zeros(nsites)
        phi = self._get_phi(C, mag) + np.zeros(nsites)
        stddevs = []
        for stddev in stddev_types:
            assert stddev in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
            if stddev == const.StdDev.TOTAL:
                stddevs.append(np.sqrt(tau ** 2. + phi ** 2.))
            elif stddev == const.StdDev.INTER_EVENT:
                stddevs.append(tau)
            elif stddev == const.StdDev.INTRA_EVENT:
                stddevs.append(phi)
        return stddevs

    def _get_tau(self, C, mag):
        """
        Returns magnitude dependent inter-event standard deviation (tau)
        (equation 14)
        """
        if mag < 6.5:
            return C["tau1"]
        elif mag < 7.:
            return C["tau1"] + (C["tau2"] - C["tau1"]) * ((mag - 6.5) / 0.5)
        else:
            return C["tau2"]

    def _get_phi(self, C, mag):
        """
        Returns the magnitude dependent intra-event standard deviation (phi)
        (equation 15)
        """
        if mag < 5.5:
            return C["phi1"]
        elif mag < 5.75:
            return C["phi1"] + (C["phi2"] - C["phi1"]) * ((mag - 5.5) / 0.25)
        else:
            return C["phi2"]

    COEFFS = CoeffsTable(sa_damping=5, table="""\
    imt        m1     m2    b0N     b0R    b0SS     b0U    b1N    b1R   b1SS    b1U      b2      b3      c1      c2      c3       c4      c5   vref  tau1  tau2  phi1  phi2
    rsd575   5.35   7.15  1.555  0.7806  1.2790   1.280  4.992  7.061  5.578  5.576  0.9011  -1.684  0.1159  0.1065  0.0682  -0.2246  0.0006  368.2  0.28  0.25  0.54  0.41
    rsd595    5.2   7.40  2.541  1.6120  2.3020   2.182  3.170  4.536  3.467  3.628  0.9443  -3.911  0.3165  0.2539  0.0932  -0.3183  0.0006  369.9  0.25  0.19  0.43  0.35
    rsd2080   5.2   7.40  1.409  0.7729  0.8804  0.8822  4.778  6.579  6.188  6.182  0.7414  -3.164  0.0646  0.0865  0.0373  -0.4237  0.0005  369.6  0.30  0.19  0.56  0.45
    """)

    CONSTANTS = {"mstar": 6.0,
                 "r1": 10.0,
                 "r2": 50.0,
                 "v1": 600.0,
                 "dz1ref": 200.0}


class AfshariStewart2016Japan(AfshariStewart2016):
    """
    Adaption of the Afshari & Stewart (2016) GMPE for relative significant
    duration for the case when the Japan basin model is preferred
    """
    def _get_lnmu_z1(self, vs30):
        """
        Returns the z1.0 normalisation term for Japan (equation 12)
        """
        return (-5.23 / 2.) * np.log(
            (vs30 ** 2. + 412.39 ** 2) / (1360.0 ** 2. + 412.39 ** 2.)) -\
            np.log(1000.0)

