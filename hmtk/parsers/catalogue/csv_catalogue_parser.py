# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (c) 2010-2013, GEM Foundation, G. Weatherill, M. Pagani, 
# D. Monelli.
#
# The Hazard Modeller's Toolkit is free software: you can redistribute 
# it and/or modify it under the terms of the GNU Affero General Public 
# License as published by the Free Software Foundation, either version 
# 3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
# DISCLAIMER
# 
# The software Hazard Modeller's Toolkit (hmtk) provided herein 
# is released as a prototype implementation on behalf of 
# scientists and engineers working within the GEM Foundation (Global 
# Earthquake Model). 
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
# The Hazard Modeller's Toolkit (hmtk) is therefore distributed WITHOUT 
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or 
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License 
# for more details.
# 
# The GEM Foundation, and the authors of the software, assume no 
# liability for use of the software. 

"""
Module :mod:`hmtk.parsers.catalogue.csv_catalogue_parser` 
implements :class:`CsvCatalogueParser`.
"""
import csv
import numpy as np

from hmtk.seismicity.catalogue import Catalogue
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
        else:    
            attribute_array = np.hstack([attribute_array, np.nan])
        return attribute_array
