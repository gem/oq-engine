""" Prototype of a 'Catalogue' class
"""

import numpy as np

class Catalogue(object):
    """General Catalogue Class"""

    TOTAL_ATTRIBUTE_LIST = ['eventID', 'Agency', 'Identifier', 'year', 'month', 
                        'day', 'hour', 'minute', 'second', 'timeError', 
                        'longitude', 'latitude', 'SemiMajor90', 'SemiMinor90', 
                        'ErrorStrike','depth','depthError','magnitude', 
                        'sigmaMagnitude', 'magnitudeType', 'focalMechanism', 
                        'validIndex']

    FLOAT_ATTRIBUTE_LIST = ['second', 'timeError', 'longitude', 'latitude', 
                        'SemiMajor90', 'SemiMinor90', 'ErrorStrike', 'depth',
                        'depthError', 'magnitude', 'sigmaMagnitude']

    INT_ATTRIBUTE_LIST = ['eventID','year', 'month', 'day', 'hour', 'minute']

    STRING_ATTRIBUTE_LIST = ['Agency', 'magnitudeType']


    def __init__(self):
        '''Initilise the catalogue dictionary'''
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
        self.data['xyz'] = None
        self.data['flag_vector'] = None
        self.number_earthquakes = 0
        self.default_completeness = None
    
    def get_number_events(self):
        return len(self.data[self.data.keys()[0]])

    def add_event(self):
        # TODO
        raise AttributeError('Not implemented yet!')

    def write_catalogue(self, output_file, filetype):
        # TODO 
        raise AttributeError('Not implemented yet!')
