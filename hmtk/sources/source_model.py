#!/usr/bin/env/python
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
# License as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
# DISCLAIMER
#
# The software Hazard Modeller's Toolkit (hmtk) provided herein
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
# The Hazard Modeller's Toolkit (hmtk) is therefore distributed WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

# -*- coding: utf-8 -*-
'''
Module implements :class: hmtk.sources.source_model.mtkSourceModel, the
general class to describe a set of seismogenic sources
'''

from openquake.nrmllib import models
from openquake.nrmllib.hazard.writers import SourceModelXMLWriter
from hmtk.sources.area_source import mtkAreaSource
from hmtk.sources.point_source import mtkPointSource
from hmtk.sources.simple_fault_source import mtkSimpleFaultSource
from hmtk.sources.complex_fault_source import mtkComplexFaultSource
from hmtk.seismicity.selector import CatalogueSelector


class mtkSourceModel(object):
    '''
    Object to describe a seismogenic source model (composite of
    multiple sources with mixed typologies)

    :param str id:
        Identifier for the source model
    :param str name:
        Source model name
    :param list sources:
        List of seismogenic sources
    '''

    def __init__(self, identifier=None, name=None, sources=None):
        self.id = identifier
        self.name = name
        if isinstance(sources, list):
            self.sources = sources
        else:
            if sources:
                raise ValueError('Sources must be input as list!')
            self.sources = []

    def __iter__(self):
        return iter(self.sources)

    def get_number_sources(self):
        '''
        Returns the number of sources in the model
        '''
        return len(self.sources)

    def serialise_to_nrml(self, filename, use_defaults=False):
        '''
        Writes the source model to a nrml source model file given by the
        filename

        :param str filename:
            Path to output file

        :param bool use_defaults:
            Boolean to indicate whether to use default values (True) or not.
            If set to False, ValueErrors will be raised when an essential
            attribute is missing.
        '''
        output_model = models.SourceModel(name=self.name, sources=[])

        for source in self.sources:
            output_model.sources.append(
                source.create_oqnrml_source(use_defaults))

        writer = SourceModelXMLWriter(filename)
        writer.serialize(output_model)
