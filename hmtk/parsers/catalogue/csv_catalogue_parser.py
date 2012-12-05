"""
Module :mod:`hmtk.parsers.catalogue.csv_catalogue_parser` 
implements :class:`CsvCatalogueParser`.
"""
import csv
import numpy as np

from hmtk.catalogue.catalogue import Catalogue
from hmtk.parsers.catalogue.base import BaseCatalogueParser

class CsvCatalogueParser(BaseCatalogueParser):
    """CSV Catalogue Parser Class
    """

    def read_file(self):
        """
        """
        filedata = open(self.input_file, 'rt')
        catalogue = Catalogue()
        # Reading the data file
        data = csv.DictReader(filedata)
        # Parsing the data content
        for irow, row in enumerate(data):
            if irow == 0:
                valid_key_list = self._header_check(row.keys(), 
                    catalogue.TOTAL_ATTRIBUTE_LIST)
            for key in valid_key_list:
                if key in catalogue.FLOAT_ATTRIBUTE_LIST:
                    catalogue.data[key] = self._float_check(
                                                        catalogue.data[key], 
                                                        row[key])
                elif key in catalogue.INT_ATTRIBUTE_LIST:
                    catalogue.data[key] = self._int_check(
                                                        catalogue.data[key],
                                                        row[key])
                else:
                    catalogue.data[key].append(row[key])
        return catalogue

    def _header_check(self, input_keys, catalogue_keys):
        valid_key_list = []
        for element in input_keys:
            print element
            if element in catalogue_keys:
                valid_key_list.append(element)
            else:
                print 'Catalogue Attribute %s is not a recognised catalogue key'\
                    % element
        return valid_key_list

    def _float_check(self, attribute_array, value):
        '''Checks if value is valid float, appends to array if valid, appends
        nan if not'''
        value = value.strip(' ')
        if value:
            attribute_array = np.hstack([attribute_array, float(value)])
        else:    
            attribute_array = np.hstack([attribute_array, np.nan])
        return attribute_array

    def _int_check(self, attribute_array, value):
        '''Checks if value is valid integer, appends to array if valid, appends
        nan if not'''
        value = value.strip(' ')
        if value:
            attribute_array = np.hstack([attribute_array, int(value)])
            print int(value)
        else:    
            attribute_array = np.hstack([attribute_array, np.nan])
        return attribute_array
