#!/usr/bin/env python
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
:mod:`openquake.hmtk.regionalisation.tectonic_regionalisation` implements
:class:`openquake.hmtk.ancillary.tectonic_regionalisation.TectonicRegion`,
defining the methods and attributes associated with a region, and the
:class:`openquake.hmtk.ancillary.tectonic_regionalisation.TectonicRegionalisation` defining a regionalisation as a set of regions
'''
from math import fabs
import numpy as np
from openquake.hazardlib.scalerel.wc1994 import WC1994

DEFAULT_SHEAR_MODULUS = [(30.0, 1.0)]
DEFAULT_DLR = [(1.25E-5, 1.0)]
DEFAULT_MSR = [(WC1994(), 1.0)]


def _check_list_weights(parameter, name):
    '''
    Checks that the weights in a list of tuples sums to 1.0
    '''
    if not isinstance(parameter, list):
        raise ValueError('%s must be formatted with a list of tuples' % name)
    weight = np.sum([val[1] for val in parameter])
    if fabs(weight - 1.) > 1E-8:
        raise ValueError('%s weights do not sum to 1.0!' % name)
    return parameter


class TectonicRegion(object):
    '''
    Definition of the tectonic region
    '''
    def __init__(self, identifier, name, shear_modulus=None,
                 disp_length_ratio=None, scaling_rel=None):

        shear_modulus = shear_modulus or DEFAULT_SHEAR_MODULUS
        disp_length_ratio = disp_length_ratio or DEFAULT_DLR
        scaling_rel = scaling_rel or DEFAULT_MSR

        self.id = identifier
        self.region_name = name
        self.shear_modulus = _check_list_weights(
            shear_modulus, 'Shear Modulus ' + self.region_name)
        self.disp_length_ratio = _check_list_weights(
            disp_length_ratio,
            'Displacement to Length Ratio ' + self.region_name)

        self.scaling_rel = _check_list_weights(
            scaling_rel,
            'Scaling Relation ' + self.region_name)


class TectonicRegionalisation(object):
    '''
    Defines a set of regionalisations
    '''
    def __init__(self):
        '''
        '''
        self.regionalisation = []
        self.key_list = []

    def populate_regions(self, tectonic_region_dict):
        '''
        Populates the tectonic region from the list of dictionaries, where each
        region is a dictionary of with the following format::

         region = {'Shear_Modulus': [(val1, weight1), (val2, weight2), ...],
                   'Displacement_Length_Ratio': [(val1, weight1), ...],
                   'Magnitude_Scaling_Relation': [(val1, weight1), ...]}
        '''
        for tect_reg in tectonic_region_dict:
            if 'Shear_Modulus' in tect_reg.keys():
                shear_modulus = tect_reg['Shear_Modulus']
            else:
                shear_modulus = DEFAULT_SHEAR_MODULUS

            if 'Displacement_Length_Ratio' in tect_reg.keys():
                disp_length_ratio = tect_reg['Displacement_Length_Ratio']
            else:
                disp_length_ratio = DEFAULT_DLR

            if 'Magnitude_Scaling_Relation' in tect_reg.keys():
                scaling_relation = tect_reg['Magnitude_Scaling_Relation']
            else:
                scaling_relation = DEFAULT_MSR

            self.regionalisation.append(
                TectonicRegion(
                    tect_reg['Code'], tect_reg['Name'],
                    shear_modulus, disp_length_ratio, scaling_relation))
            self.key_list.append(tect_reg['Name'])

    def get_number_regions(self):
        '''
        Returns the number of tectonic regions in a regionalisation
        '''
        return len(self.key_list)
