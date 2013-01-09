# -*- coding: utf-8 -*-

""" 
Prototype of a 'Catalogue' class
"""

import numpy as np

class Catalogue(object):
    """
    General Catalogue Class
    """

    FLOAT_ATTRIBUTE_LIST = ['second', 'timeError', 'longitude', 'latitude', 
                        'SemiMajor90', 'SemiMinor90', 'ErrorStrike', 'depth',
                        'depthError', 'magnitude', 'sigmaMagnitude']

    INT_ATTRIBUTE_LIST = ['eventID','year', 'month', 'day', 'hour', 'minute',
                          'flag']

    STRING_ATTRIBUTE_LIST = ['Agency', 'magnitudeType','comment']
    
    TOTAL_ATTRIBUTE_LIST = list( 
        (set(FLOAT_ATTRIBUTE_LIST).union(
            set(INT_ATTRIBUTE_LIST))).union(
                 set(STRING_ATTRIBUTE_LIST)))

    def __init__(self):
        """
        Initialise the catalogue dictionary
        """
        self.data = {}
        self.processes = {'declustering': None,
                          'completeness': None,
                          'recurrence': None,
                          'Poisson Tests': None}

        for attribute in self.TOTAL_ATTRIBUTE_LIST:
            if attribute in self.FLOAT_ATTRIBUTE_LIST:
                self.data[attribute] = np.array([], dtype=float)
            elif attribute in self.INT_ATTRIBUTE_LIST:
                self.data[attribute] = np.array([], dtype=int)
            else:
                self.data[attribute] = []

        # Consider removing
#        self.data['xyz'] = None
#        self.data['flag_vector'] = None
        self.number_earthquakes = 0
#        self.default_completeness = None
    
    def get_number_events(self):
        return len(self.data[self.data.keys()[0]])

    def add_event(self):
        # TODO
        raise AttributeError('Not implemented yet!')

    def write_catalogue(self, output_file, filetype):
        # TODO 
        raise AttributeError('Not implemented yet!')
    
    def load_to_array(self, keys):
        """
        This loads the data contained in the catalogue into a numpy array. The
        method works only for float data
        
        :param keys:
            A list of keys to be uploaded into the array 
        :type list:
        """
        # Preallocate the numpy array
        data = np.empty( (len(self.data[keys[0]]), len(keys)) )
        for i in range(0, len(self.data[keys[0]]) ):
            for j,key in enumerate(keys):
                data[i,j] = self.data[key][i]
        return data  
    
    def load_from_array(self, keys, data_array):
        """
        This loads the data contained in an array into the catalogue object
        
        :param keys:
            A list of keys explaining the content of the columns in the array
        :type list:
        """
        for i,key in enumerate(keys):
            self.data[key] = data_array[:,i]
    
    def catalogue_mt_filter(self, mt_table):
        """
        Filter the catalogue using a magnitude-time table. The table has 
        two columns and n-rows. The first column contains the magnitude 
        the second years.
        """
        flag = np.ones(np.shape(self.data['magnitude'])[0], dtype=bool)
        for comp_val in mt_table:
            id0 = np.logical_and(self.data['year'] < comp_val[0],
                                 self.data['magnitude'] < comp_val[1])
            flag[id0] = False
        for key in self.data.keys():
            if len(self.data[key]):
                self.data[key] = self.data[key][np.nonzero(flag)]

