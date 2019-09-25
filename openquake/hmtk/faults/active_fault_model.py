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
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

'''
Module :mod:`openquake.hmtk.faults.active_fault_model.mtkActiveFaultModel`
implements a wrapper class for a set of active fault sources
'''
from copy import deepcopy
import numpy as np
from openquake.hazardlib.scalerel.wc1994 import WC1994
from openquake.hmtk.sources.source_model import mtkSourceModel


class mtkActiveFaultModel(object):
    '''
    Class to define a compilation of active fault sources

    :param str id:
        Identifier for the model
    :param str name:
        Fault model name
    :param list faults:
        Active faults as a list of tuples where each tuple is an instance
        of (openquake.hmtk.faults.fault_model.mtkActiveFault,
        [list of MFD configurations for that fault])
    :param source_model:
        Instance of openquake.hmtk.source.source_model.mtkSourceModel class
    '''

    def __init__(self, identifier=None, name=None, faults=None):
        '''
        '''
        self.id = identifier
        self.name = name
        if isinstance(faults, list):
            self.faults = faults
        else:
            if faults:
                raise ValueError('Faults must be input as list')
            else:
                self.faults = []
        self.source_model = None

    def get_number_faults(self):
        '''
        Returns the number of faults in the model
        '''
        return len(self.faults)

    def build_fault_model(self, collapse=False, rendered_msr=WC1994(),
                          mfd_config=None):
        '''
        Constructs a full fault model with epistemic uncertainty by
        enumerating all the possible recurrence models of each fault as
        separate faults, with the recurrence rates multiplied by the
        corresponding weights.

        :param bool collapse:
            Determines whether or not to collapse the branches
        :param rendered_msr:
            If the option is taken to collapse the branches then a recurrence
            model for rendering must be defined
        :param list/dict mfd_config:
            Universal list or dictionay of configuration parameters for the
            magnitude frequency distribution - will overwrite whatever is
            previously defined for the fault!
        '''
        self.source_model = mtkSourceModel(self.id, self.name)
        for fault in self.faults:
            fault.generate_recurrence_models(collapse,
                                             config=mfd_config,
                                             rendered_msr=rendered_msr)
            src_model, src_weight = fault.generate_fault_source_model()
            for iloc, model in enumerate(src_model):

                new_model = deepcopy(model)
                new_model.id = str(model.id) + '_%g' % (iloc + 1)
                new_model.mfd.occurrence_rates = \
                    (np.array(new_model.mfd.occurrence_rates) *
                     src_weight[iloc]).tolist()
                self.source_model.sources.append(new_model)
