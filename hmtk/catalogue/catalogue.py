#!/usr/bin/env/python
""" Prototype of a 'Catalogue' class
"""

import numpy as np
from parsers.catalogue.csv_formats import CatalogueCSVParser

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

file_parser = {'csv': CatalogueCSVParser()}

class MTKCatalogue(object):
    '''General Catalogue Class'''

    def __init__(self):
        '''Initilise the catalogue dictionary'''
        self.data = {}
        self.processes = {'declustering': None,
                          'completeness': None,
                          'recurrence': None,
                          'Poisson Tests': None}

        for attribute in TOTAL_ATTRIBUTE_LIST:
            if attribute in FLOAT_ATTRIBUTE_LIST:
                self.data[attribute] = np.array([], dtype=float)
            elif attribute in INT_ATTRIBUTE_LIST:
                self.data[attribute] = np.array([], dtype=int)
            else:
                self.data[attribute] = []
        self.data['xyz'] = None
        self.data['flag_vector'] = None
        self.number_earthquakes = 0
        self.default_completeness = None
    
    def read_catalogue(self, input_file, filetype):
        '''Reads the catalogue according to the file type'''
        # Check to see if file type supported
        if filetype in file_parser.keys():
            # Is supported 
            self.data = file_parser[filetype].parse_catalogue(self.data, 
                                                              input_file)
            self.number_earthquakes = len(self.data['eventID'])
            self.default_completeness = np.array([[
                np.min(self.data['year']), np.min(self.data['magnitude'])]])
        else:
            # Throw error
            raise ValueError('Catalogue file type not supported!')

    def write_catalogue(self, output_file, filetype):
        # Nothing here yet!
        raise AttributeError('Not implemented yet!')
