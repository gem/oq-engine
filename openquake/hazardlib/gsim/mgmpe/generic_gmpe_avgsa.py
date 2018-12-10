# The Hazard Library
# Copyright (C) 2012-2018 GEM Foundation
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
Module :mod:`openquake.hazardlib.mgmp.generic_gmpe_avgsa` implements
:class:`~openquake.hazardlib.mgmpe.GenericGmpeAvgSA`
"""

import copy
import numpy as np
from openquake.hazardlib.gsim.base import GMPE, registry
from openquake.hazardlib import const
from openquake.hazardlib.imt import SA

class GenericGmpeAvgSA(GMPE):
    """
    Implements a modified GMPE class that can be used to compute average
    ground motion over several spectral ordinates.

    :param gmpe_name:
        The name of a GMPE class
    """

    # Parameters
    REQUIRES_SITES_PARAMETERS = set()
    REQUIRES_DISTANCES = set()
    REQUIRES_RUPTURE_PARAMETERS = set()
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = ''
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([SA])
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([const.StdDev.TOTAL])
    DEFINED_FOR_TECTONIC_REGION_TYPE = ''
    DEFINED_FOR_REFERENCE_VELOCITY = None

    def __init__(self, gmpe_name, avg_periods):
        super().__init__(gmpe_name=gmpe_name)
        self.gmpe = registry[gmpe_name]()
        self.set_parameters()
        self.avg_periods = [float(t) for t in avg_periods.split(',')]
        self.tnum = len(self.avg_periods)

        # Check if this GMPE has the necessary requirements
        # TO DO

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stds_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """

        mean_list = []
        stddvs_list = []

        # Loop over averaging periods
        for period in self.avg_periods:
            imt_local = SA(float(period))
            # compute mean and standard deviation
            mean, stddvs = self.gmpe.get_mean_and_stddevs(sites, rup, dists,
                                                          imt_local,
                                                          stds_types)
            mean_list.append(mean)
            stddvs_list.append(stddvs[0]) # Support only for total!

        mean_avgsa = 0.
        stddvs_avgsa = 0.

        for i1 in range(self.tnum):
            mean_avgsa += mean_list[i1]
            for i2 in range(self.tnum):
                rho = baker_jayaram_correlation(self.avg_periods[i1],
                                                self.avg_periods[i2])
                stddvs_avgsa += rho * stddvs_list[i1] * stddvs_list[i2]

        mean_avgsa *= (1./self.tnum)
        stddvs_avgsa = (1./self.tnum) * np.sqrt(stddvs_avgsa)

        return mean_avgsa, [stddvs_avgsa]


def baker_jayaram_correlation(t1, t2):
    """
    NOTE: subroutine taken from: https://usgs.github.io/shakemap/shakelib
    
    Produce inter-period correlation for any two spectral periods.

    Based upon:
    Baker, J.W. and Jayaram, N., "Correlation of spectral acceleration
    values from NGA ground motion models," Earthquake Spectra, (2007).

    Args:
        t1, t2 (float):
            The two periods of interest.

    Returns:
        rho (float): The predicted correlation coefficient

    """
    t_min = min(t1, t2)
    t_max = max(t1, t2)

    c1 = 1.0 - np.cos(np.pi / 2.0 - np.log(t_max / max(t_min, 0.109)) * 0.366)

    if t_max < 0.2:
        c2 = 1.0 - 0.105 * (1.0 - 1.0 / (1.0 + np.exp(100.0 * t_max - 5.0)))
        c2 *= (t_max - t_min) / (t_max - 0.0099)
    else:
        c2 = 0

    if t_max < 0.109:
        c3 = c2
    else:
        c3 = c1

    c4 = c1 + 0.5 * (np.sqrt(c3) - c3) * (1.0 + np.cos(np.pi * t_min / 0.109))

    if t_max <= 0.109:
        rho = c2
    elif t_min > 0.109:
        rho = c1
    elif t_max < 0.2:
        rho = min(c2, c4)
    else:
        rho = c4

    return rho