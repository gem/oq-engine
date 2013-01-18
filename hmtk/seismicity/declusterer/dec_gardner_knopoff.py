# -*- coding: utf-8 -*-:

"""
Module :mod:`hmtk.seismicity.declusterer.dec_gardner_knopoff' defines the 
Gardner and Knopoff declustering algorithm 
"""

import numpy as np

from hmtk.seismicity.declusterer.base import BaseCatalogueDecluster
from hmtk.seismicity.utils import decimal_year, haversine

class GardnerKnopoffType1(BaseCatalogueDecluster):
    """
    This class implements the Gardner Knopoff algorithm as described in 
    this paper:
    Gardner, J. K. and Knopoff, L. (1974). Is the sequence of aftershocks 
    in Southern California, with aftershocks removed, poissonian?. Bull.
    Seism. Soc. Am., 64(5): 1363-1367.
    """
    
    def _check_config(self, config):
        """
        Check that the configuration dictionary contains the necessary 
        information
        """
        if not config.has_key('time_distance_window'):
            raise RuntimeError('Declustering configuration not complete: ' +
                               'time_distance_window missing')
        if not config.has_key('fs_time_prop'):
            raise RuntimeError('Declustering configuration not complete: ' +
                               'fs_time_prop missing')
        
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
        
        # Check declustering configuration
        self._check_config(config)
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
