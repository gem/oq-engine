import numpy as np

from hmtk.catalogue.declusterer.base import BaseCatalogueDecluster
from hmtk.catalogue.declusterer.utils import decimal_year, haversine

class Afteran(BaseCatalogueDecluster):
    """ 
    This implements the Afteran algorithm as described in this paper:
    Musson, R. 
    
    """
    def decluster(self, catalogue, config):
        '''catalogue_matrix, window_opt=TDW_GARDNERKNOPOFF, time_window=60.):

        :param catalog_matrix: eq catalog in a matrix format with these columns in
                                order: `year`, `month`, `day`, `longitude`,
                                `latitude`, `Mw`
        :type catalog_matrix: numpy.ndarray
        :keyword window_opt: method used in calculating distance and time windows
        :type window_opt: string
        :keyword time_window: Length (in days) of moving time window
        :type time_window: positive float
        :returns: **vcl vector** indicating cluster number, **vmain_shock catalog**
                  containing non-clustered events, **flagvector** indicating
                  which eq events belong to a cluster
        :rtype: numpy.ndarray
        '''

        #Convert time window from days to decimal years
        time_window = config['time_window'] / 365.

        # Pre-processing steps are the same as for Gardner & Knopoff
        # Get relevent parameters
        mag = catalogue['magnitude']
        neq = np.shape(mag)[0]  # Number of earthquakes
        # Get decimal year (needed for time windows)
        year_dec = decimal_year(catalogue['year'], catalogue['month'],
                                catalogue['day'])

        # Get space windows corresponding to each event
        sw_space = time_dist_windows[config['window_opt']].calc(mag)[0]

        eqid = np.arange(0, neq, 1)  # Initial Position Identifier

        # Pre-allocate cluster index vectors
        vcl = np.zeros((neq, 1), dtype=int)
        flagvector = np.zeros((neq, 1), dtype=int)
        # Sort magnitudes into descending order
        id0 = np.flipud(np.argsort(mag, kind='heapsort'))
        mag = mag[id0]
        #catalogue_matrix = catalogue_matrix[id0, :]
        longitude = catalogue['longitude'][id0]
        latitude = catalogue['latitude'][id0]
        sw_space = sw_space[id0]
        year_dec = year_dec[id0]
        eqid = eqid[id0]

        i = 0
        clust_index = 0
        while i < neq:
            if vcl[i] == 0:
                # Earthquake not allocated to cluster - perform calculation
                # Perform distance calculation
                mdist = haversine(longitude, latitude,
                                  longitude[i], latitude[i])

                # Select earthquakes inside distance window and not in cluster
                vsel = np.logical_and(mdist <= sw_space[i], vcl == 0).flatten()
                dtime = year_dec[vsel] - year_dec[i]

                nval = np.shape(dtime)[0] #Number of events inside valid window
                # Pre-allocate boolean array (all True)

                vsel1 = self._find_aftershocks(dtime, nval, time_window)
                vsel2 = self._find_foreshocks(dtime, nval, time_window, vsel1)

                temp_vsel = np.copy(vsel)
                temp_vsel[vsel] = np.logical_or(vsel1, vsel2)
                if np.shape(np.nonzero(temp_vsel)[0])[0] > 1:
                    # Contains clustered events - allocate a cluster index
                    vcl[temp_vsel] = clust_index + 1
                    # Remove mainshock from cluster
                    vsel1[0] = False
                    # Assign markers to aftershocks and foreshocks
                    temp_vsel = np.copy(vsel)
                    temp_vsel[vsel] = vsel1
                    flagvector[temp_vsel] = 1
                    vsel[vsel] = vsel2
                    flagvector[vsel] = -1
                    clust_index += 1
            i += 1

        # Now have events - re-sort array back into chronological order
        # Re-sort the data into original order
        id1 = np.argsort(eqid, kind='heapsort')
        eqid = eqid[id1]
        #catalogue_matrix = catalogue_matrix[id1, :]
        vcl = vcl[id1]
        flagvector = flagvector[id1]
        return vcl.flatten(), flagvector.flatten()

        #if config['purge']:
        #    # Now to produce a catalogue with aftershocks purged
        #    vmain_shock = purge_catalogue(catalogue, flagvector)
        #else:
        #    vmain_shock = None
        #return vcl.flatten(), vmain_shock, flagvector.flatten()

    def _find_aftershocks(self, dtime, nval, time_window):
        """
        Searches for aftershocks within the moving
        time window
        :param dtime: time since main event
        :type dtime: numpy.ndarray
        :param nval: number of events in search window
        :type nval: int
        :param time_window: Length (in days) of moving time window
        :type time_window: positive float
        :returns: **vsel** index vector for aftershocks
        :rtype: numpy.ndarray
        """

        vsel = np.array(np.ones(nval), dtype=bool)
        initval = dtime[0]  # Start with the mainshock

        j = 1
        while j < nval:
            ddt = dtime[j] - initval
            # Is event after previous event and within time window?
            vsel[j] = np.logical_and(ddt >= 0.0, ddt <= time_window)
            if vsel[j]:
                # Reset time window to new event time
                initval = dtime[j]
            j += 1
        return vsel


    def _find_foreshocks(self, dtime, nval, time_window, vsel_aftershocks):
        """
        Searches for foreshocks within the moving
        time window
        :param dtime: time since main event
        :type dtime: numpy.ndarray
        :param nval: number of events in search window
        :type nval: int
        :param time_window: Length (in days) of moving time window
        :type time_window: positive float
        :param vsel_aftershocks: index vector for aftershocks
        :type vsel_aftershocks: numpy.ndarray
        :returns: **vsel** index vector for foreshocks
        :rtype: numpy.ndarray
        """

        j = 1
        vsel = np.array(np.zeros(nval), dtype=bool)
        initval = dtime[0]

        while j < nval:
            if vsel_aftershocks[j]:
            # Event already allocated as an aftershock - skip
                j += 1
            else:
                ddt = dtime[j] - initval
                # Is event before previous event and within time window?
                vsel[j] = np.logical_and(ddt <= 0.0,
                                          ddt >= -(time_window))
                if vsel[j]:
                # Yes, reset time window to new event
                    initval = dtime[j]
            j += 1

        return vsel
