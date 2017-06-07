# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (c) 2010-2017, GEM Foundation, G. Weatherill, M. Pagani,
# D. Monelli.
#
# The Hazard Modeller's Toolkit is free software: you can redistribute
# it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
# DISCLAIMER
#
# The software Hazard Modeller's Toolkit (openquake.hmtk) provided herein
# is released as a prototype implementation on behalf of
# scientists and engineers working within the GEM Foundation (Global
# Earthquake Model).
#
# It is distributed for the purpose of open collaboration and in the
# hope that it will be useful to the scientific, engineering, disaster
# risk and software design communities.
#
# The software is NOT distributed as part of GEM’s OpenQuake suite
# (http://www.globalquakemodel.org/openquake) and must be considered as a
# separate entity. The software provided herein is designed and implemented
# by scientific staff. It is not developed to the design standards, nor
# subject to same level of critical review by professional software
# developers, as GEM’s OpenQuake software suite.
#
# Feedback and contribution to the software is welcome, and can be
# directed to the hazard scientific staff of the GEM Model Facility
# (hazard@globalquakemodel.org).
#
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

# -*- coding: utf-8 -*-:

"""
Module :mod:`openquake.hmtk.seismicity.declusterer.dec_gardner_knopoff`
defines the Gardner and Knopoff declustering algorithm
"""

import numpy as np

from openquake.hmtk.seismicity.declusterer.base import (
    BaseCatalogueDecluster, DECLUSTERER_METHODS)
from openquake.hmtk.seismicity.utils import decimal_year, haversine
from openquake.hmtk.seismicity.declusterer.distance_time_windows import (
    TIME_DISTANCE_WINDOW_FUNCTIONS)


@DECLUSTERER_METHODS.add(
    "decluster",
    time_distance_window=TIME_DISTANCE_WINDOW_FUNCTIONS,
    fs_time_prop=np.float)
class GardnerKnopoffType1(BaseCatalogueDecluster):
    """
    This class implements the Gardner Knopoff algorithm as described in
    this paper:
    Gardner, J. K. and Knopoff, L. (1974). Is the sequence of aftershocks
    in Southern California, with aftershocks removed, poissonian?. Bull.
    Seism. Soc. Am., 64(5): 1363-1367.
    """

    def decluster(self, catalogue, config):
        """
        The configuration of this declustering algorithm requires two
        objects:
        - A time-distance window object (key is 'time_distance_window')
        - A value in the interval [0,1] expressing the fraction of the
        time window used for aftershocks (key is 'fs_time_prop')

        :param catalogue:
            Catalogue of earthquakes
        :type catalogue: Dictionary
        :param config:
            Configuration parameters
        :type config: Dictionary

        :returns:
          **vcl vector** indicating cluster number,
          **flagvector** indicating which eq events belong to a cluster
        :rtype: numpy.ndarray
        """
        # Get relevant parameters
        neq = len(catalogue.data['magnitude'])  # Number of earthquakes
        # Get decimal year (needed for time windows)
        year_dec = decimal_year(
            catalogue.data['year'], catalogue.data['month'],
            catalogue.data['day'])
        # Get space and time windows corresponding to each event
        sw_space, sw_time = (
            config['time_distance_window'].calc(catalogue.data['magnitude']))
        # Initial Position Identifier
        eqid = np.arange(0, neq, 1)
        # Pre-allocate cluster index vectors
        vcl = np.zeros(neq, dtype=int)
        # Sort magnitudes into descending order
        id0 = np.flipud(np.argsort(catalogue.data['magnitude'],
                                   kind='heapsort'))
        longitude = catalogue.data['longitude'][id0]
        latitude = catalogue.data['latitude'][id0]
        sw_space = sw_space[id0]
        sw_time = sw_time[id0]
        year_dec = year_dec[id0]
        eqid = eqid[id0]
        flagvector = np.zeros(neq, dtype=int)
        # Begin cluster identification
        clust_index = 0
        for i in range(0, neq - 1):
            if vcl[i] == 0:
                # Find Events inside both fore- and aftershock time windows
                dt = year_dec - year_dec[i]
                vsel = np.logical_and(
                    vcl == 0,
                    np.logical_and(
                        dt >= (-sw_time[i] * config['fs_time_prop']),
                        dt <= sw_time[i]))
                # Of those events inside time window,
                # find those inside distance window
                vsel1 = haversine(longitude[vsel],
                                  latitude[vsel],
                                  longitude[i],
                                  latitude[i]) <= sw_space[i]
                vsel[vsel] = vsel1
                temp_vsel = np.copy(vsel)
                temp_vsel[i] = False
                if any(temp_vsel):
                    # Allocate a cluster number
                    vcl[vsel] = clust_index + 1
                    flagvector[vsel] = 1
                    # For those events in the cluster before the main event,
                    # flagvector is equal to -1
                    temp_vsel[dt >= 0.0] = False
                    flagvector[temp_vsel] = -1
                    flagvector[i] = 0
                    clust_index += 1

        # Re-sort the catalog_matrix into original order
        id1 = np.argsort(eqid, kind='heapsort')
        eqid = eqid[id1]
        vcl = vcl[id1]
        flagvector = flagvector[id1]

        return vcl, flagvector
