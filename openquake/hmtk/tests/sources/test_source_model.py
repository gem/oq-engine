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
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

# -*- coding: utf-8 -*-
'''
Tests the construction and methods of the
:class: openquake.hmtk.sources.source_model.mtkSourceModel
'''

import os
import unittest
import operator
from openquake.hazardlib.tom import PoissonTOM
from openquake.hmtk.parsers.source_model.nrml04_parser import nrmlSourceModelParser
from openquake.hmtk.sources.source_model import mtkSourceModel
from openquake.hazardlib.source.point import PointSource
from openquake.hazardlib.source.area import AreaSource
from openquake.hazardlib.source.simple_fault import SimpleFaultSource
from openquake.hazardlib.source.complex_fault import ComplexFaultSource
from openquake.hmtk.sources.point_source import mtkPointSource

TOM = PoissonTOM(1.0)

BASE_PATH = os.path.join(os.path.dirname(__file__), 'test_source_files')

MODEL_PATH = os.path.join(BASE_PATH, 'mixed_source_model_nrml4_2.xml')
TEST_PATH = os.path.join(BASE_PATH, 'source_model_writer_test.xml')


class TestSourceModel(unittest.TestCase):
    '''
    Module to test the :class: openquake.hmtk.sources.source_model.mtkSourceModel
    '''
    def setUp(self):
        self.source_model = None

    def test_core_instantiation(self):
        '''
        Simple test to ensure the class is correctly instantiated
        '''
        self.source_model = mtkSourceModel('101', 'Model Name')
        self.assertEqual(self.source_model.id, '101')
        self.assertEqual(self.source_model.name, 'Model Name')
        # No sources on input
        self.assertEqual(self.source_model.get_number_sources(), 0)

        # Input correctly
        good_model = [mtkPointSource('101', 'Point 1'),
                      mtkPointSource('102', 'Point 2')]
        self.source_model = mtkSourceModel('1001', 'Good Model', good_model)
        self.assertEqual(self.source_model.get_number_sources(), 2)

        # Input incorrectly - source not as list
        with self.assertRaises(ValueError) as ver:
            self.source_model = mtkSourceModel(
                '1002', 'Bad Model', mtkPointSource('103', 'Point 3'))
            self.assertEqual(str(ver.exception),
                             'Sources must be input as list!')

    def test_nrml_writer(self):
        '''
        Tests the source model writer
        '''
        # Load a full source model
        parser = nrmlSourceModelParser(MODEL_PATH)
        source_model = parser.read_file(2.0)
        # Write to file
        source_model.serialise_to_nrml(TEST_PATH, True)
        # Load file back
        parser = nrmlSourceModelParser(TEST_PATH)
        source_model_test = parser.read_file(2.0)
        orig_sources = sorted(source_model.sources,
                              key=operator.attrgetter('name'))
        test_sources = sorted(source_model_test.sources,
                              key=operator.attrgetter('name'))
        for orig_source, test_source in zip(orig_sources, test_sources):
            self.assertEqual(orig_source.name, test_source.name)
            self.assertEqual(orig_source.mag_scale_rel.__class__.__name__,
                             test_source.mag_scale_rel.__class__.__name__)
        # Remove the test file
        os.system('rm ' + TEST_PATH)

    def test_source_model_to_hazardlib_converter(self):
        """
        Tests the converter of a source model to an oq-hazardlib format
        """
        # Load a full source model
        parser = nrmlSourceModelParser(MODEL_PATH)
        source_model = parser.read_file(2.0)
        oq_source_model = source_model.convert_to_oqhazardlib(TOM,
                                                              1.0,
                                                              10.0,
                                                              10.0,
                                                              True)
        self.assertIsInstance(oq_source_model[0], AreaSource)
        self.assertIsInstance(oq_source_model[1], AreaSource)
        self.assertIsInstance(oq_source_model[2], PointSource)
        self.assertIsInstance(oq_source_model[3], SimpleFaultSource)
        self.assertIsInstance(oq_source_model[4], ComplexFaultSource)

        source_model.sources[3] = 'Rubbish!'
        with self.assertRaises(ValueError) as ver:
            oq_source_model = source_model.convert_to_oqhazardlib(TOM,
                                                                  1.0,
                                                                  10.0,
                                                                  10.0,
                                                                  True)

            self.assertEqual(str(ver.exception),
                             'Source type not recognised!')
