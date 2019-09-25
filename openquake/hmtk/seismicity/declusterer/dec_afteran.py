# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (C) 2010-2019 GEM Foundation, G. Weatherill, M. Pagani,
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
# (https://www.globalquakemodel.org/tools-products) and must be considered as a
# separate entity. The software provided herein is designed and implemented
# by scientific staff. It is not developed to the design standards, nor
# subject to same level of critical review by professional software
# developers, as GEM’s OpenQuake software suite.
#
# Feedback and contribution to the software is welcome, and can be
# directed to the hazard scientific staff of the GEM Model Facility
# (hazard@globalquakemodel.org).
#
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

import numpy as np

from openquake.hmtk.seismicity.declusterer.base import (
    BaseCatalogueDecluster, DECLUSTERER_METHODS)
from openquake.hmtk.seismicity.utils import decimal_year, haversine
from openquake.hmtk.seismicity.declusterer.distance_time_windows import (
    TIME_DISTANCE_WINDOW_FUNCTIONS)


@DECLUSTERER_METHODS.add(
    "decluster",
    time_distance_window=TIME_DISTANCE_WINDOW_FUNCTIONS,
    time_window=np.float)
class Afteran(BaseCatalogueDecluster):
    """
    This implements the Afteran algorithm as described in this paper:
    Musson, R. (1999), Probabilistic seismic hazard maps for the North
    Balkan Region, Annali Di Geofisica, 42(6), 1109 - 1124
    """

    def decluster(self, catalogue, config):
        """
        catalogue_matrix, window_opt=TDW_GARDNERKNOPOFF, time_window=60.):

        :param catalogue: a catalogue object
        :type catalogue: Instance of the openquake.hmtk.seismicity.catalogue.Catalogue()
                         class
        :keyword window_opt: method used in calculating distance and time
            windows
        :type window_opt: string
        :keyword time_window: Length (in days) of moving time window
        :type time_window: positive float
        :returns: **vcl vector** indicating cluster number,
                  **flagvector** indicating which earthquakes belong to a
                  cluster
        :rtype: numpy.ndarray
        """
        # Convert time window from days to decimal years
        time_window = config['time_window'] / 365.
        # Pre-processing steps are the same as for Gardner & Knopoff
        # Get relevent parameters
        mag = catalogue.data['magnitude']
        neq = np.shape(mag)[0]  # Number of earthquakes
        # Get decimal year (needed for time windows)
        year_dec = decimal_year(catalogue.data['year'],
                                catalogue.data['month'],
                                catalogue.data['day'])
        # Get space windows corresponding to each event
        sw_space, _ = (
            config['time_distance_window'].calc(catalogue.data['magnitude']))

        # Pre-allocate cluster index vectors
        vcl = np.zeros(neq, dtype=int)
        flagvector = np.zeros(neq, dtype=int)
        # Rank magnitudes into descending order
        id0 = np.flipud(np.argsort(mag, kind='heapsort'))

        clust_index = 0
        for imarker in id0:
            # Earthquake not allocated to cluster - perform calculation
            if vcl[imarker] == 0:
                # Perform distance calculation
                mdist = haversine(
                    catalogue.data['longitude'],
                    catalogue.data['latitude'],
                    catalogue.data['longitude'][imarker],
                    catalogue.data['latitude'][imarker]).flatten()

                # Select earthquakes inside distance window, later than
                # mainshock and not already assigned to a cluster
                vsel1 = np.where(
                    np.logical_and(vcl == 0,
                                   np.logical_and(
                                       mdist <= sw_space[imarker],
                                       year_dec > year_dec[imarker])))[0]
                has_aftershocks = False
                if len(vsel1) > 0:
                    # Earthquakes after event inside distance window
                    temp_vsel1, has_aftershocks = self._find_aftershocks(
                        vsel1,
                        year_dec,
                        time_window,
                        imarker,
                        neq)
                    if has_aftershocks:
                        flagvector[temp_vsel1] = 1
                        vcl[temp_vsel1] = clust_index + 1

                # Select earthquakes inside distance window, earlier than
                # mainshock and not already assigned to a cluster
                has_foreshocks = False
                vsel2 = np.where(
                    np.logical_and(
                        vcl == 0,
                        np.logical_and(mdist <= sw_space[imarker],
                                       year_dec < year_dec[imarker])))[0]
                if len(vsel2) > 0:
                    # Earthquakes before event inside distance window
                    temp_vsel2, has_foreshocks = self._find_foreshocks(
                        vsel2,
                        year_dec,
                        time_window,
                        imarker,
                        neq)
                    if has_foreshocks:
                        flagvector[temp_vsel2] = -1
                        vcl[temp_vsel2] = clust_index + 1

                if has_aftershocks or has_foreshocks:
                    # Assign mainshock to cluster
                    vcl[imarker] = clust_index + 1
                    clust_index += 1

        return vcl, flagvector

    def _find_aftershocks(self, vsel, year_dec, time_window, imarker, neq):
        '''
        Function to identify aftershocks from a set of potential
        events inside the distance window of an earthquake.
        :param vsel: Pointer vector to the location of the events in distance
                     window
        :type vsel: numpy.ndarray
        :param year_dec: Vector of decimal catalogue event times
        :type year_dec: numpy.ndarray
        :param time_window: Moving time window for selection of time clusters
        :type time_window: float
        :param imarker: Index of the mainshock in the catalogue vector
        :type imarker: Integer
        :param neq: Number of events in distance window of mainshock
        :type neq: Integer
        '''
        temp_vsel1 = np.zeros(neq, dtype=bool)
        has_aftershocks = False

        # Finds the time difference between events
        delta_time = np.diff(
            np.hstack([year_dec[imarker], year_dec[vsel]]))
        for iloc in range(0, len(vsel)):
            # If time difference between event is smaller than
            # time window - is an aftershock -> continue

            if delta_time[iloc] < time_window:
                temp_vsel1[vsel[iloc]] = True
                has_aftershocks = True
            else:
                # Time difference between events is larger than
                # window -> no more aftershocks -> return
                return temp_vsel1, has_aftershocks

        return temp_vsel1, has_aftershocks

    def _find_foreshocks(self, vsel, year_dec, time_window, imarker, neq):
        '''
        Finds foreshocks from a set of potential events within
        the distance window of a mainshock.
        :param vsel: Pointer vector to the location of the events in distance
                     window
        :type vsel: numpy.ndarray
        :param year_dec: Vector of decimal catalogue event times
        :type year_dec: numpy.ndarray
        :param time_window: Moving time window for selection of time clusters
        :type time_window: float
        :param imarker: Index of the mainshock in the catalogue vector
        :type imarker: Integer
        :param neq: Number of events in distance window of mainshock
        :type neq: Integer
        '''

        temp_vsel2 = np.zeros(neq, dtype=bool)
        has_foreshocks = False

        # The initial time is the time of the mainshock
        initial_time = year_dec[imarker]
        year_dec = year_dec[vsel]
        for jloc in range(len(vsel) - 1, -1, -1):
            # If the time between the mainshock and the preceeding
            # event is smaller than the time_window then event
            # is a foreshock

            if (initial_time - year_dec[jloc]) < time_window:
                temp_vsel2[vsel[jloc]] = True
                has_foreshocks = True
                # Update target time to consider current foreshock
                # Then continue
                initial_time = year_dec[jloc]
            else:
                # No events inside time window
                # end of foreshock sequence - return
                return temp_vsel2, has_foreshocks

        return temp_vsel2, has_foreshocks
