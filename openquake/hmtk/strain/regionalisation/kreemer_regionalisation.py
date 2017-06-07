# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (c) 2010-2017, GEM Foundation, G. Weatherill, M. Pagani,
# D. Monelli.
#
# The Hazard Modeller's Toolkit is free software: you can redistribute
# it and/or modify it under the terms of the GNU Affero General Public
#License as published by the Free Software Foundation, either version
#3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
#DISCLAIMER
#
# The software Hazard Modeller's Toolkit (openquake.hmtk) provided herein
#is released as a prototype implementation on behalf of
# scientists and engineers working within the GEM Foundation (Global
#Earthquake Model).
#
# It is distributed for the purpose of open collaboration and in the
# hope that it will be useful to the scientific, engineering, disaster
# risk and software design communities.
#
# The software is NOT distributed as part of GEM's OpenQuake suite
# (http://www.globalquakemodel.org/openquake) and must be considered as a
# separate entity. The software provided herein is designed and implemented
# by scientific staff. It is not developed to the design standards, nor
# subject to same level of critical review by professional software
# developers, as GEM's OpenQuake software suite.
#
# Feedback and contribution to the software is welcome, and can be
# directed to the hazard scientific staff of the GEM Model Facility
# (hazard@globalquakemodel.org).
#
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed WITHOUT
#ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
#for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

'''
Modules: openquake.hmtk.strain.regionalisation.kreemer_regionalisation implements the
class KreemerRegionalisation, which assigns a strain model to a tectonic
region according to the classification of Kreemer, Holt and Haines (2003)
'''
import os
import numpy as np
from linecache import getlines

KREEMER_GLOBAL_0506 = os.path.join(os.path.dirname(__file__),
                                   'kreemer_polygons_area.txt')


def _build_kreemer_cell(data, loc):
    '''
    Constructs the "Kreemer Cell" from the input file. The Kreemer cell is
    simply a set of five lines describing the four nodes of the square (closed)
    :param list data:
        Strain data as list of text lines (input from linecache.getlines)
    :param int loc:
        Pointer to location in data
    :returns:
        temp_poly - 5 by 2 numpy array of cell longitudes and latitudes
    '''

    temp_poly = np.empty([5, 2], dtype=float)
    for ival in range(1, 6):
        value = data[loc + ival].rstrip('\n')
        value = value.lstrip(' ')
        value = np.array((value.split(' ', 1))).astype(float)
        temp_poly[ival - 1, :] = value.flatten()
    return temp_poly


class KreemerRegionalisation(object):
    '''
    Class for implmenting a regionalisation using the file type defined by
    Kreemer et al. (2003)

    :param str filename:
        Name of file
    :param strain:
        Strain model as instance of openquake.hmtk.strain.geodetic_strain.GeodeticStrain

    '''
    def __init__(self, filename=KREEMER_GLOBAL_0506):
        '''
        '''
        self.filename = filename
        self.strain = None

    def get_regionalisation(self, strain_model):
        '''
        Gets the tectonic region type for every element inside the strain model

        :paramm strain_model:
            Input strain model as instance of
            openquake.hmtk.strain.geodetic_strain.GeodeticStrain


        :returns:
            Strain model with complete regionalisation
        '''
        self.strain = strain_model
        self.strain.data['region'] = np.array(
            ['IPL'
             for _ in range(self.strain.get_number_observations())],
            dtype='|S13')
        self.strain.data['area'] = np.array(
            [np.nan
             for _ in range(self.strain.get_number_observations())])

        regional_model = self.define_kreemer_regionalisation()
        for polygon in regional_model:
            self._point_in_tectonic_region(polygon)
        return self.strain

    def _point_in_tectonic_region(self, polygon):
        '''
        Returns the region type and area according to the tectonic
        region
        :param polygon: Dictionary containing the following attributes -
            'long_lims' - Longitude limits (West, East)
            'lat_lims' - Latitude limits (South, North)
            'region_type' - Tectonic region type (str)
            'area' - Area of cell in m ^ 2
        '''

        marker = np.zeros(self.strain.get_number_observations(), dtype=bool)
        idlong = np.logical_and(
            self.strain.data['longitude'] >= polygon['long_lims'][0],
            self.strain.data['longitude'] < polygon['long_lims'][1])
        id0 = np.where(np.logical_and(idlong, np.logical_and(
            self.strain.data['latitude'] >= polygon['lat_lims'][0],
            self.strain.data['latitude'] < polygon['lat_lims'][1])))[0]
        if len(id0) > 0:
            marker[id0] = True
            for iloc in id0:
                self.strain.data['region'][iloc] = \
                    polygon['region_type']
                self.strain.data['area'][iloc] = polygon['area']
        marker = np.logical_not(marker)
        return marker

    def define_kreemer_regionalisation(self, north=90., south=-90., east=180.,
                                       west=-180.):
        '''
        Applies the regionalisation defined according to the regionalisation
        typology of Corne Kreemer
        '''
        '''Applies the regionalisation of Kreemer (2003)
        :param input_file:
            Filename (str) of input file contraining Kreemer regionalisation
        :param north:
            Northern limit (decimal degrees)for consideration (float)
        :param south:
            Southern limit (decimal degrees)for consideration (float)
        :param east:
            Eastern limit (decimal degrees)for consideration (float)
        :param west:
            Western limit (decimal degrees)for consideration (float)
        :returns: List of polygons corresonding to the Kreemer cells.
        '''
        input_data = getlines(self.filename)
        kreemer_polygons = []

        for line_loc, line in enumerate(input_data):
            if '>' in line[0]:
                polygon_dict = {}
                # Get region type (char) and area (m ^ 2) from header
                primary_data = line[2:].rstrip('\n')
                primary_data = primary_data.split(' ', 1)
                polygon_dict['region_type'] = primary_data[0].strip(' ')
                polygon_dict['area'] = float(primary_data[1].strip(' '))
                polygon_dict['cell'] = _build_kreemer_cell(input_data,
                                                           line_loc)
                polygon_dict['long_lims'] = np.array([
                    np.min(polygon_dict['cell'][:, 0]),
                    np.max(polygon_dict['cell'][:, 0])])
                polygon_dict['lat_lims'] = np.array([
                    np.min(polygon_dict['cell'][:, 1]),
                    np.max(polygon_dict['cell'][:, 1])])
                polygon_dict['cell'] = None

                if polygon_dict['long_lims'][0] >= 180.0:
                    polygon_dict['long_lims'] = \
                        polygon_dict['long_lims'] - 360.0
                valid_check = [
                    polygon_dict['long_lims'][0] >= west,
                    polygon_dict['long_lims'][1] <= east,
                    polygon_dict['lat_lims'][0] >= south,
                    polygon_dict['lat_lims'][1] <= north]
                if all(valid_check):
                    kreemer_polygons.append(polygon_dict)

        return kreemer_polygons
