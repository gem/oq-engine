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
from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib.gsim.base import GMPE, registry
from openquake.hazardlib.imt import SA

class GenericGmpeAvgSA(GMPE):
    """
    Implements a modified GMPE class that can be used to compute average
    ground motion over several spectral ordinates.

    :param gmpe_name:
        The name of a GMPE class
    """

    # Parameters
    REQUIRES_SITES_PARAMETERS = set(('vs30'))
    REQUIRES_DISTANCES = set()
    REQUIRES_RUPTURE_PARAMETERS = set()
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = ''
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set()
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set()
    DEFINED_FOR_TECTONIC_REGION_TYPE = ''
    DEFINED_FOR_REFERENCE_VELOCITY = None

    def __init__(self, gmpe_name, avg_periods):
        super().__init__(gmpe_name=gmpe_name)
        self.gmpe = registry[gmpe_name]()
        self.set_parameters()
        self.avg_periods = [float(t) for t in avg_periods.split(',')]

        # Check if this GMPE has the necessary requirements
        # TO DO

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stds_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        mean_avgsa = 0.
        tnum = len(self.avg_periods)
        # Loop over averaging periods
        for period in self.avg_periods:
            imt_local = SA(float(period))
            # compute mean and standard deviation
            mean, stddvs = self.gmpe.get_mean_and_stddevs(sites, rup, dists,
                                                          imt_local,
                                                          stds_types)
            mean_avgsa += (1./tnum) * mean

        return mean_avgsa, stddvs

