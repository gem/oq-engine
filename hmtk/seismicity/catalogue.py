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

# -*- coding: utf-8 -*-

""" 
Prototype of a 'Catalogue' class
"""

import numpy as np
from hmtk.seismicity.utils import decimal_time
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.utils import spherical_to_cartesian

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
        if not 'eventID' in keys:
            self.data['eventID'] = np.array(range(0, np.shape(data_array)[0]),
                                            dtype=int)

        for i, key in enumerate(keys):
            self.data[key] = data_array[:, i]
    
    def catalogue_mt_filter(self, mt_table, flag=None):
        """
        Filter the catalogue using a magnitude-time table. The table has 
        two columns and n-rows. 
        :param nump.ndarray mt_table:
            Magnitude time table with n-rows where column 1 is year and column
            2 is magnitude

        """
        if flag is None:
            # No flag defined, therefore all events are initially valid
            flag = np.ones(self.get_number_events(), dtype=bool)
        
        for comp_val in mt_table:
            id0 = np.logical_and(self.data['year'].astype(float) < comp_val[0],
                                 self.data['magnitude'] < comp_val[1])
            flag[id0] = False
        if not np.all(flag):
            self.purge_catalogue(flag)
    

    def get_decimal_time(self):                                                 
        '''                                                                     
        Returns the time of the catalogue as a decimal                          
        '''                                                                     
        return decimal_time(self.data['year'],                             
                            self.data['month'],                            
                            self.data['day'],                              
                            self.data['hour'],                             
                            self.data['minute'],                           
                            self.data['second'])                           
                                                                                
    def hypocentres_as_mesh(self):                                              
        '''                                                                     
        Render the hypocentres to a nhlib.geo.mesh.Mesh object                  
        '''                                                                     
        return Mesh(self.data['longitude'], 
                    self.data['latitude'], 
                    self.data['depth'])                                    
                                                                                
                                                                                
    def hypocentres_to_cartesian(self):                                         
        '''                                                                     
        Render the hypocentres to a cartesian array                             
        '''                                                                     
        return spherical_to_cartesian(self.data['longitude'], 
                                        self.data['latitude'], 
                                        self.data['depth'])


    def purge_catalogue(self, flag_vector):            
        '''                                                                         
        Purges present catalogue with invalid events defined by flag_vector
                                                                                 
        :param numpy.ndarray flag_vector:                                           
            Boolean vector showing if events are selected (True) or not (False)     
                                                                                    
        '''                                                                         
        
        id0 = np.where(flag_vector)[0]                                          
                                                                                 
        for key in self.data.keys():
            if isinstance(self.data[key], np.ndarray) and \
                len(self.data[key]) > 0:
                # Dictionary element is numpy array - use logical indexing
                self.data[key] = self.data[key][id0]
            elif isinstance(self.data[key], list) and \
                len(self.data[key]) > 0:
                # Dictionary element is list
                self.data[key] = [self.data[key][iloc] for iloc in id0]
            else:
                continue
        self.get_number_events()
