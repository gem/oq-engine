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
Module exports :class:`Campbell1997`
"""
import numpy as np

from openquake.hazardlib.gsim.base import GMPE
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA


class Campbell1997(GMPE):
    """
    Implements GMPE (PGA) by Campbell, Kenneth W. "Empirical near-source
    attenuation relationships for horizontal and vertical components of peak
    ground acceleration, peak ground velocity, and pseudo-absolute acceleration
    response spectra." Seismological research letters 68.1 (1997): 154-179.
    """
    #: Supported TRT active...we specify active_shallow_crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types are PGA, PGV, PSA, but we only define
    #: PGA because this is the only IMT used by an implemented model (09/18)
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA
    ])

    #: Supported intensity measure component is the horizontal component
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Supported standard deviation type is only total, see equation 4, pg 164
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
    ])

    #: Requires vs30
    REQUIRES_SITES_PARAMETERS = set(('vs30',))

    #: Required rupture parameters are magnitude and top of rupture depth
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', 'rake'))

    #: Required distance measure is closest distance to rupture. In the
    #: publication, Rseis is used. We assume Rrup=Rseis, justified by 
    #: our calculations matching the verification tables
    REQUIRES_DISTANCES = set(('rrup', ))

    #: Verification of the mean value was done by digitizing Figs. 9 and 10
    #: using Engauge Digitizer. The tests check varied magnitude, distance,
    #: vs30, and faulting type. Maximum error was ~1.3%. OpenQuake trellis
    #: plots match these figures. Also tested against a matlab implementation
    #: (web.stanford.edu/~bakerjw/GMPEs/C_1997_horiz.m), which also has no
    #: verification tables.

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        R = (dists.rrup)
        M = rup.mag
        # get constants
        Ssr = self.get_Ssr_term(sites.vs30)
        Shr = self.get_Shr_term(sites.vs30)
        rake = rup.rake
        F = self.get_fault_term(rake)

        # compute mean
        mean = -3.512 + (0.904 * M) - (1.328 * np.log(np.sqrt(R**2
               + (0.149 * np.exp(0.647 * M))**2))) \
               + (1.125 - 0.112 * np.log(R) - 0.0957 * M) * F \
               + (0.440 - 0.171 * np.log(R)) * Ssr \
               + (0.405 - 0.222 * np.log(R)) * Shr
        stddevs = self.get_stddevs(mean, stddev_types)
        return mean, stddevs

    def get_fault_term(self, rake):
        """
        Returns coefficient for faulting style (pg 156)
        """
        rake = rake + 360 if rake < 0 else rake

        if (rake >= 45) & (rake <= 135):
            f = 1.
        elif (rake >= 225) & (rake <= 315):
            f = 0.5
        else:
            f = 0.
        return f

    def get_Ssr_term(self, vs30):
        """
        Returns site term for soft rock (pg 157)
        """
        return (vs30 >= 760) & (vs30 < 1500)

    def get_Shr_term(self, vs30):
        """
        Returns site term for hard rock (pg 157)
        """
        return vs30 >= 1500

    def get_stddevs(self, mean, stddev_types):
        """
        Returns the standard deviations from mean (pg 164; more robust than
        estimate using magnitude)
        """
        mean = np.exp(mean)
        sigma = 0.39 + np.zeros(mean.shape)
        sigma[mean < 0.068] = 0.55
        idx = np.logical_and(mean >= 0.068, mean <= 0.21)
        sigma[idx] = 0.173- 0.140 * np.log(mean[idx])
        stddevs = []
        for stddev in stddev_types:
            if stddev == const.StdDev.TOTAL:
                stddevs.append(sigma)
        return stddevs
