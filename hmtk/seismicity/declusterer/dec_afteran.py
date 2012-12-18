import numpy as np

from hmtk.seismicity.declusterer.base import BaseCatalogueDecluster
from hmtk.seismicity.declusterer.utils import decimal_year, haversine

class Afteran(BaseCatalogueDecluster):
    """ 
    This implements the Afteran algorithm as described in this paper:
    Musson, R. 
    
    """
    def decluster(self, catalogue, config):
        """
        catalogue_matrix, window_opt=TDW_GARDNERKNOPOFF, time_window=60.):

        :param catalogue: a catalogue object
        :type catalogue: TO ADD HERE
        :keyword window_opt: method used in calculating distance and time 
            windows
        :type window_opt: string
        :keyword time_window: Length (in days) of moving time window
        :type time_window: positive float
        :returns: **vcl vector** indicating cluster number, 
                  **vmain_shock catalog** containing non-clustered events, 
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
        year_dec = decimal_year(catalogue.data['year'], catalogue.data['month'],
                                catalogue.data['day'])
        # Get space windows corresponding to each event
        sw_space, _ = (
            config['time_distance_window'].calc(catalogue.data['magnitude']))
        # Initial Position Identifier
        eqid = np.arange(0, neq, 1)  
        # Pre-allocate cluster index vectors
        vcl = np.zeros((neq, 1), dtype=int)
        flagvector = np.zeros((neq, 1), dtype=int)
        # Sort magnitudes into descending order
        id0 = np.flipud(np.argsort(mag, kind='heapsort'))
        mag = mag[id0]
        longitude = catalogue.data['longitude'][id0]
        latitude = catalogue.data['latitude'][id0]
        sw_space = sw_space[id0]
        year_dec = year_dec[id0]
        eqid = eqid[id0]
        i = 0
        clust_index = 0
        while i < neq:
            # Earthquake not allocated to cluster - perform calculation
            if vcl[i] == 0:
                # Perform distance calculation
                mdist = haversine(longitude, latitude,
                                  longitude[i], latitude[i])
                # Select earthquakes inside distance window and not in cluster
                vsel = np.logical_and(mdist <= sw_space[i], vcl == 0)
                dtime = year_dec[vsel] - year_dec[i]
                # Number of events inside valid window
                nval = np.shape(dtime)[0] 
                # 
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
        # Pre-allocate boolean array (all True)
        vsel = np.ones(nval, dtype=bool)
        # Start with the mainshock
        initval = dtime[0] 
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
