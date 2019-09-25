# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (C) 2010-2019 GEM Foundation, G. Weatherill, M. Pagani,
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
# (https://www.globalquakemodel.org/tools-products) and must be considered as a
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
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

'''
Module: openquake.hmtk.parsers.fault.fault_yaml_parser implements parser of a fault
model from the Yaml format

'''

import yaml
import numpy as np
from math import fabs
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.line import Line
from openquake.hazardlib.scalerel import get_available_scalerel
from openquake.hmtk.faults.fault_geometries import (
    SimpleFaultGeometry, ComplexFaultGeometry)
from openquake.hmtk.faults.fault_models import mtkActiveFault
from openquake.hmtk.faults.active_fault_model import mtkActiveFaultModel
from openquake.hmtk.faults.tectonic_regionalisation import (
    TectonicRegionalisation)


SCALE_REL_MAP = get_available_scalerel()


def weight_list_to_tuple(data, attr_name):
    '''
    Converts a list of values and corresponding weights to a tuple of values
    '''

    if len(data['Value']) != len(data['Weight']):
        raise ValueError('Number of weights do not correspond to number of '
                         'attributes in %s' % attr_name)
    weight = np.array(data['Weight'])
    if fabs(np.sum(weight) - 1.) > 1E-7:
        raise ValueError('Weights do not sum to 1.0 in %s' % attr_name)

    data_tuple = []
    for iloc, value in enumerate(data['Value']):
        data_tuple.append((value, weight[iloc]))
    return data_tuple


def parse_tect_region_dict_to_tuples(region_dict):
    '''
    Parses the tectonic regionalisation dictionary attributes to tuples
    '''
    output_region_dict = []
    tuple_keys = ['Displacement_Length_Ratio', 'Shear_Modulus']
    # Convert MSR string name to openquake.hazardlib.scalerel object
    for region in region_dict:
        for val_name in tuple_keys:
            region[val_name] = weight_list_to_tuple(region[val_name],
                                                    val_name)
        # MSR works differently - so call get_scaling_relation_tuple
        region['Magnitude_Scaling_Relation'] = weight_list_to_tuple(
            region['Magnitude_Scaling_Relation'],
            'Magnitude Scaling Relation')
        output_region_dict.append(region)
    return output_region_dict


def get_scaling_relation_tuple(msr_dict):
    '''
    For a dictionary of scaling relation values convert string list to
    object list and then to tuple
    '''

    # Convert MSR string name to openquake.hazardlib.scalerel object
    for iloc, value in enumerate(msr_dict['Value']):
        if not value in SCALE_REL_MAP.keys():
            raise ValueError('Scaling relation %s not supported!' % value)
        msr_dict['Value'][iloc] = SCALE_REL_MAP[value]()
    return weight_list_to_tuple(msr_dict,
                                'Magnitude Scaling Relation')


class FaultYmltoSource(object):
    '''
    Class to parse a fault model definition from Yaml format to a fault model
    class
    '''

    def __init__(self, filename):
        '''
        :param str filename:
            Name of input file (in yml format)
        '''
        self.data = yaml.load(open(filename, 'rt'))
        if 'Fault_Model' not in self.data:
            raise ValueError('Fault Model not defined in input file!')

    def read_file(self, mesh_spacing=1.0):
        '''
        Reads the file and returns an instance of the FaultSource class.

        :param float mesh_spacing:
            Fault mesh spacing (km)
        '''

        # Process the tectonic regionalisation
        tectonic_reg = self.process_tectonic_regionalisation()

        model = mtkActiveFaultModel(self.data['Fault_Model_ID'],
                                    self.data['Fault_Model_Name'])
        for fault in self.data['Fault_Model']:
            fault_geometry = self.read_fault_geometry(fault['Fault_Geometry'],
                                                      mesh_spacing)
            if fault['Shear_Modulus']:
                fault['Shear_Modulus'] = weight_list_to_tuple(
                    fault['Shear_Modulus'], '%s Shear Modulus' % fault['ID'])

            if fault['Displacement_Length_Ratio']:
                fault['Displacement_Length_Ratio'] = weight_list_to_tuple(
                    fault['Displacement_Length_Ratio'],
                    '%s Displacement to Length Ratio' % fault['ID'])

            fault_source = mtkActiveFault(
                fault['ID'],
                fault['Fault_Name'],
                fault_geometry,
                weight_list_to_tuple(fault['Slip'], '%s - Slip' % fault['ID']),
                float(fault['Rake']),
                fault['Tectonic_Region'],
                float(fault['Aseismic']),
                weight_list_to_tuple(
                    fault['Scaling_Relation_Sigma'],
                    '%s Scaling_Relation_Sigma' % fault['ID']),
                neotectonic_fault=None,
                scale_rel=get_scaling_relation_tuple(
                    fault['Magnitude_Scaling_Relation']),
                aspect_ratio=fault['Aspect_Ratio'],
                shear_modulus=fault['Shear_Modulus'],
                disp_length_ratio=fault['Displacement_Length_Ratio'])

            if tectonic_reg:
                fault_source.get_tectonic_regionalisation(
                    tectonic_reg,
                    fault['Tectonic_Region'])
            assert isinstance(fault['MFD_Model'], list)
            fault_source.generate_config_set(fault['MFD_Model'])
            model.faults.append(fault_source)

        return model, tectonic_reg

    def process_tectonic_regionalisation(self):
        '''
        Processes the tectonic regionalisation from the yaml file
        '''

        if 'tectonic_regionalisation' in self.data.keys():
            tectonic_reg = TectonicRegionalisation()
            tectonic_reg.populate_regions(
                parse_tect_region_dict_to_tuples(
                    self.data['tectonic_regionalisation']))
        else:
            tectonic_reg = None
        return tectonic_reg

    def read_fault_geometry(self, geo_dict, mesh_spacing=1.0):
        '''
        Creates the fault geometry from the parameters specified in the
        dictionary.

        :param dict geo_dict:
            Sub-dictionary of main fault dictionary containing only
            the geometry attributes
        :param float mesh_spacing:
            Fault mesh spacing (km)
        :returns:
            Instance of SimpleFaultGeometry or ComplexFaultGeometry, depending
            on typology
        '''
        if geo_dict['Fault_Typology'] == 'Simple':
            # Simple fault geometry
            raw_trace = geo_dict['Fault_Trace']
            trace = Line([Point(raw_trace[ival], raw_trace[ival + 1])
                          for ival in range(0, len(raw_trace), 2)])
            geometry = SimpleFaultGeometry(trace,
                                           geo_dict['Dip'],
                                           geo_dict['Upper_Depth'],
                                           geo_dict['Lower_Depth'],
                                           mesh_spacing)

        elif geo_dict['Fault_Typology'] == 'Complex':
            # Complex Fault Typology
            trace = []
            for raw_trace in geo_dict['Fault_Trace']:
                fault_edge = Line(
                    [Point(raw_trace[ival], raw_trace[ival + 1],
                           raw_trace[ival + 2]) for ival in range(0, len(raw_trace),
                                                                  3)])
                trace.append(fault_edge)
            geometry = ComplexFaultGeometry(trace, mesh_spacing)
        else:
            raise ValueError('Unrecognised or unsupported fault geometry!')
        return geometry
