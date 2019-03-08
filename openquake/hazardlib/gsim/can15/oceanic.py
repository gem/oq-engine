#
# Copyright (C) 2014-2019 GEM Foundation
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
:module:`openquake.hazardlib.gsim.can15.western` implements
:class:`OceanicCan15Mid`, :class:`OceanicCan15Low`, :class:`OceanicCan15Upp`
"""

import copy
import numpy as np
from openquake.hazardlib.gsim.can15.utils import \
    get_equivalent_distances_west
from openquake.hazardlib.gsim.can15.western import WesternCan15Mid
from openquake.hazardlib.gsim.can15.western import get_sigma


class OceanicCan15Mid(WesternCan15Mid):
    """
    Implements the GMPE for oceanic sources
    """

    #: GMPE not tested against independent implementation so raise
    #: not verified warning
    non_verified = True

    #: Shear-wave velocity for reference soil conditions in [m s-1]
    DEFINED_FOR_REFERENCE_VELOCITY = 760.

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """ """
        rupl = copy.deepcopy(rup)
        rupl.mag -= 0.5
        # distances
        distsl = copy.copy(dists)
        distsl.rjb, distsl.rrup = \
            get_equivalent_distances_west(rup.mag, dists.repi)
        mean, stddevs = super().get_mean_and_stddevs(sites, rupl, distsl, imt,
                                                     stddev_types)
        stddevs = [np.ones(len(dists.repi))*get_sigma(imt)]
        return mean, stddevs


class OceanicCan15Low(WesternCan15Mid):
    """
    Implements the GMPE for oceanic sources. This is the model giving lower
    ground motion values.
    """

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """ """
        rupl = copy.deepcopy(rup)
        rupl.mag -= 0.5
        # distances
        distsl = copy.copy(dists)
        distsl.rjb, distsl.rrup = \
            get_equivalent_distances_west(rup.mag, dists.repi)
        mean, stddevs = super().get_mean_and_stddevs(sites, rupl, distsl, imt,
                                                     stddev_types)
        # adjust mean values using the reccomended delta (see Atkinson and
        # Adams, 2013)
        tmp = 0.1+0.0007*distsl.rjb
        tmp = np.vstack((tmp, np.ones_like(tmp)*0.3))
        delta = np.log(10.**(np.amin(tmp, axis=0)))
        mean_adj = mean - delta
        stddevs = [np.ones(len(dists.repi))*get_sigma(imt)]
        return mean_adj, stddevs


class OceanicCan15Upp(WesternCan15Mid):
    """
    Implements the GMPE for oceanic sources. This is the model giving higher
    ground motion values.
    """

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """ """
        rupl = copy.deepcopy(rup)
        rupl.mag -= 0.5
        # distances
        distsl = copy.copy(dists)
        distsl.rjb, distsl.rrup = \
            get_equivalent_distances_west(rup.mag, dists.repi)
        mean, stddevs = super().get_mean_and_stddevs(sites, rupl, distsl, imt,
                                                     stddev_types)
        # Adjust mean values using the reccomended delta (see Atkinson and
        # Adams, 2013)
        tmp = 0.1+0.0007*distsl.rjb
        tmp = np.vstack((tmp, np.ones_like(tmp)*0.3))
        delta = np.log(10.**(np.amin(tmp, axis=0)))
        mean_adj = mean + delta
        stddevs = [np.ones(len(dists.repi))*get_sigma(imt)]
        return mean_adj, stddevs
