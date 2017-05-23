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
# License as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
# DISCLAIMER
#
# The software Hazard Modeller's Toolkit (openquake.hmtk) provided herein
# is released as a prototype implementation on behalf of
# scientists and engineers working within the GEM Foundation (Global
# Earthquake Model).
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
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

'''
Module: openquake.hmtk.parsers.strain.strain_csv_parser contains the :classes:
ReadStrainCsv and WriteStrainCsv to read and write strain data from and
to csv format.
'''

import csv
import numpy as np
from collections import OrderedDict
from openquake.hmtk.strain.geodetic_strain import GeodeticStrain

STRAIN_VARIABLES = ['exx', 'eyy', 'exy', 'var_exx', 'var_eyy', 'var_exy',
                    'cc_xx_xx', 'cc_xx_yy', 'cc_xx_xy']


class ReadStrainCsv(object):
    '''
    :class:`openquake.hmtk.parsers.strain_csv_parser.ReadStrainCsv` reads a
    strain model (defined by :class:
    `openquake.hmtk.strain.geodetic_strain.GeodeticStrain`) from
    a headed csv file

    :param str filename:
        Name of strain file in csv format
    :param strain:
        Container for the strain data as instance of :class:
        `openquake.hmtk.strain.geodetic_strain.GeodeticStrain`
    '''
    def __init__(self, strain_file):
        '''
        '''
        self.filename = strain_file
        self.strain = GeodeticStrain()

    def read_data(self, scaling_factor=1E-9, strain_headers=None):
        '''
        Reads the data from the csv file

        :param float scaling_factor:
            Scaling factor used for all strain values (default 1E-9 for
            nanostrain)

        :param list strain_headers:
            List of the variables in the file that correspond to strain
            parameters

        :returns:
            strain - Strain model as an instance of the :class:
            openquake.hmtk.strain.geodetic_strain.GeodeticStrain

        '''
        if strain_headers:
            self.strain.data_variables = strain_headers
        else:
            self.strain.data_variables = STRAIN_VARIABLES

        datafile = open(self.filename, 'rU')
        reader = csv.DictReader(datafile)
        self.strain.data = OrderedDict([(name, [])
                                       for name in reader.fieldnames])
        for row in reader:
            for name in row.keys():
                if 'region' in name.lower():
                    self.strain.data[name].append(row[name])
                elif name in self.strain.data_variables:
                    self.strain.data[name].append(
                        scaling_factor * float(row[name]))
                else:
                    self.strain.data[name].append(float(row[name]))

        for key in self.strain.data.keys():
            if 'region' in key:
                self.strain.data[key] = np.array(self.strain.data[key],
                                                 dtype='S13')
            else:
                self.strain.data[key] = np.array(self.strain.data[key])

        self._check_invalid_longitudes()

        if 'region' not in self.strain.data:
            print('No tectonic regionalisation found in input file!')
        self.strain.data_variables = self.strain.data.keys()

        # Update data with secondary data (i.e. 2nd invariant, e1h, e2h etc.
        self.strain.get_secondary_strain_data()
        return self.strain

    def _check_invalid_longitudes(self):
        '''
        Checks to ensure that all longitudes are in the range -180. to 180
        '''
        idlon = self.strain.data['longitude'] > 180.
        if np.any(idlon):
            self.strain.data['longitude'][idlon] = \
                self.strain.data['longitude'][idlon] - 360.


class WriteStrainCsv(object):
    '''
    :class:`openquake.hmtk.parsers.strain_csv_parser.WriteStrainCsv` writes a
    strain model (defined by :class:
    `openquake.hmtk.strain.geodetic_strain.GeodeticStrain`)
    to a headed csv file

    :param str filename:
        Name of output file for writing
    '''
    def __init__(self, filename):
        '''
        '''
        self.filename = filename

    def write_file(self, strain, scaling_factor=1E-9):
        '''
        Main writer function for the csv file

        :param strain:
            Instance of :class: openquake.hmtk.strain.geodetic_strain.GeodeticStrain
        :param float scaling_factor:
            Scaling factor used for all strain values (default 1E-9 for
            nanostrain)
        '''
        if not isinstance(strain, GeodeticStrain):
            raise ValueError('Strain data must be instance of GeodeticStrain')

        for key in strain.data.keys():
            if key in strain.data_variables:
                # Return strain value back to original scaling
                if key in ['longitude', 'latitude']:
                    continue
                strain.data[key] = strain.data[key] / scaling_factor

        # Slice seismicity rates into separate dictionary vectors
        strain, output_variables = self.slice_rates_to_data(strain)

        outfile = open(self.filename, 'wt')
        print('Writing strain data to file %s' % self.filename)
        writer = csv.DictWriter(outfile,
                                fieldnames=output_variables)
        writer.writeheader()
        for iloc in range(0, strain.get_number_observations()):
            row_dict = {}
            for key in output_variables:
                if len(strain.data[key]) > 0:
                    # Ignores empty dictionary attributes
                    row_dict[key] = strain.data[key][iloc]
            writer.writerow(row_dict)
        outfile.close()
        print('done!')

    def slice_rates_to_data(self, strain):
        '''
        For the strain data, checks to see if seismicity rates have been
        calculated. If so, each column in the array is sliced and stored as a
        single vector in the strain.data dictionary with the corresponding
        magnitude as a key.

        :param strain:
            Instance of :class: openquake.hmtk.strain.geodetic_strain.GeodeticStrain

        :returns:
            strain - Instance of strain class with updated data dictionary
            output_variables - Updated list of headers
        '''
        output_variables = list(strain.data)
        cond = (isinstance(strain.target_magnitudes, np.ndarray) or
                isinstance(strain.target_magnitudes, list))
        if cond:
            magnitude_list = ['%.3f' % mag for mag in strain.target_magnitudes]
        else:
            return strain, output_variables

        # Ensure that the number of rows in the rate array corresponds to the
        # number of observations
        assert np.shape(strain.seismicity_rate)[0] == \
            strain.get_number_observations()

        for iloc, magnitude in enumerate(magnitude_list):
            strain.data[magnitude] = strain.seismicity_rate[:, iloc]
        output_variables.extend(magnitude_list)
        return strain, output_variables
