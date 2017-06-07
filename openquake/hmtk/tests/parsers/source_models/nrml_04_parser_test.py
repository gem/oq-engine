#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (c) 2015-2017, GEM Foundation
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
"""
Test suite for the NRML Source Model parser
"""
import os
import unittest
from openquake.hazardlib.scalerel.wc1994 import WC1994
from openquake.hazardlib import mfd
from openquake.hmtk.sources.point_source import mtkPointSource
from openquake.hmtk.sources.area_source import mtkAreaSource
from openquake.hmtk.sources.simple_fault_source import mtkSimpleFaultSource
from openquake.hmtk.sources.complex_fault_source import mtkComplexFaultSource
from openquake.hmtk.parsers.source_model.nrml04_parser import nrmlSourceModelParser

BASE_PATH = os.path.join(os.path.dirname(__file__), "data")


class NRMLParserFullModelTestCase(unittest.TestCase):
    """
    Tests the NRML parser for the case in which a full and validated NRML
    source model is input
    """
    def setUp(self):
        self.nrml_file = os.path.join(BASE_PATH,
                                      "mixed_source_model_nrml4_2.xml")
    
    def test_execution_full(self):
        """
        Tests the execution of the reader for the full model
        """
        parser = nrmlSourceModelParser(self.nrml_file)
        model = parser.read_file("XXX")
        # Basic tests
        self.assertEqual(model.id, "XXX")
        self.assertEqual(model.name, "Some Source Model")
        self.assertEqual(len(model.sources), 5)
        # Area Source
        self._check_area_source(model.sources[0])
        self._check_point_source(model.sources[2])
        self._check_simple_fault_source(model.sources[3])
        self._check_complex_fault_source(model.sources[4])
    
    def _check_area_source(self, source):
        self.assertTrue(isinstance(source, mtkAreaSource))
        self.assertEqual(source.id, "1")
        self.assertEqual(source.name, "Quito")
        self.assertEqual(source.geometry.wkt,
                         'POLYGON((-122.5 38.0, -122.0 38.5, -121.5 38.0, '
                         '-122.0 37.5, -122.5 38.0))')
        self.assertAlmostEqual(source.upper_depth, 0.0)
        self.assertAlmostEqual(source.lower_depth, 10.0)
        self.assertAlmostEqual(source.rupt_aspect_ratio, 1.5)
        for iloc, (prob, npd) in enumerate(source.nodal_plane_dist.data):
            if iloc == 0:
                self.assertAlmostEqual(prob, 0.3),
                self.assertAlmostEqual(npd.strike, 0.0)
                self.assertAlmostEqual(npd.dip, 90.0)
                self.assertAlmostEqual(npd.rake, 0.0)
            else:
                self.assertAlmostEqual(prob, 0.7),
                self.assertAlmostEqual(npd.strike, 90.0)
                self.assertAlmostEqual(npd.dip, 45.0)
                self.assertAlmostEqual(npd.rake, 90.0)
            
        for iloc, (prob, hdd) in enumerate(source.hypo_depth_dist.data):
            if iloc == 0:
                self.assertAlmostEqual(prob, 0.5)
                self.assertAlmostEqual(hdd, 4.0)
            else:
                self.assertAlmostEqual(prob, 0.5)
                self.assertAlmostEqual(hdd, 8.0)
        self.assertTrue(isinstance(source.mfd, mfd.EvenlyDiscretizedMFD))

    def _check_point_source(self, source):
        self.assertTrue(isinstance(source, mtkPointSource))
        self.assertEqual(source.id, "3")
        self.assertEqual(source.name, "point")
        self.assertAlmostEqual(source.geometry.x, -122.0)
        self.assertAlmostEqual(source.geometry.y, 38.0)
        self.assertAlmostEqual(source.upper_depth, 0.0)
        self.assertAlmostEqual(source.lower_depth, 10.0)
        self.assertAlmostEqual(source.rupt_aspect_ratio, 0.5)
        self.assertTrue(isinstance(source.mfd, mfd.TruncatedGRMFD))
        self.assertAlmostEqual(source.mfd.a_val, -3.5)
        self.assertAlmostEqual(source.mfd.b_val, 1.0)
        self.assertAlmostEqual(source.mfd.min_mag, 5.0)
        self.assertAlmostEqual(source.mfd.max_mag, 6.5)
        for iloc, (prob, npd) in enumerate(source.nodal_plane_dist.data):
            if iloc == 0:
                self.assertAlmostEqual(prob, 0.3),
                self.assertAlmostEqual(npd.strike, 0.0)
                self.assertAlmostEqual(npd.dip, 90.0)
                self.assertAlmostEqual(npd.rake, 0.0)
            else:
                self.assertAlmostEqual(prob, 0.7),
                self.assertAlmostEqual(npd.strike, 90.0)
                self.assertAlmostEqual(npd.dip, 45.0)
                self.assertAlmostEqual(npd.rake, 90.0)
            
        for iloc, (prob, hdd) in enumerate(source.hypo_depth_dist.data):
            if iloc == 0:
                self.assertAlmostEqual(prob, 0.5)
                self.assertAlmostEqual(hdd, 4.0)
            else:
                self.assertAlmostEqual(prob, 0.5)
                self.assertAlmostEqual(hdd, 8.0)
    
    def _check_simple_fault_source(self, source):
        self.assertTrue(isinstance(source, mtkSimpleFaultSource))
        self.assertEqual(source.id, "4")
        self.assertEqual(source.name, "Mount Diablo Thrust")
        self.assertTrue(isinstance(source.mag_scale_rel, WC1994))
        self.assertAlmostEqual(source.rake, 30.0)
        self.assertAlmostEqual(source.rupt_aspect_ratio, 1.5)
        self.assertAlmostEqual(source.dip, 45.0)
        self.assertAlmostEqual(source.upper_depth, 10.0)
        self.assertAlmostEqual(source.lower_depth, 20.0)
        self.assertEqual(
            str(source.fault_trace.points[0]),
            "<Latitude=37.730100, Longitude=-121.822900, Depth=0.0000>")
        self.assertEqual(
            str(source.fault_trace.points[1]),
            "<Latitude=37.877100, Longitude=-122.038800, Depth=0.0000>")
    
    def _check_complex_fault_source(self, source):
        self.assertTrue(isinstance(source, mtkComplexFaultSource))
        self.assertEqual(source.id, "5")
        self.assertEqual(source.name, "Cascadia Megathrust")
        self.assertTrue(isinstance(source.mag_scale_rel, WC1994))
        self.assertAlmostEqual(source.rake, 30.0)
        self.assertAlmostEqual(source.rupt_aspect_ratio, 2.0)
        self.assertAlmostEqual(source.dip, 10.4179999)
        self.assertAlmostEqual(source.upper_depth, 4.89734)


class NRMLParserPartialModelTestCase(unittest.TestCase):
    """
    Tests the NRML parser for the case in which a full and validated NRML
    source model is input
    """
    def setUp(self):
        self.nrml_file = os.path.join(BASE_PATH,
                                      "mixed_source_model_nrml4_2_minimum.xml")

    def test_execution_full(self):
        """
        Tests the execution of the reader for the full model
        """
        parser = nrmlSourceModelParser(self.nrml_file)
        model = parser.read_file("XXX")
        # Basic tests
        self.assertEqual(model.id, "XXX")
        self.assertEqual(model.name, "Some Source Model")
        self.assertEqual(len(model.sources), 4)
        # Area Source
        self._check_area_source(model.sources[0])
        self._check_point_source(model.sources[1])
        self._check_simple_fault_source(model.sources[2])
        self._check_complex_fault_source(model.sources[3])

    def _check_area_source(self, source):
        self.assertTrue(isinstance(source, mtkAreaSource))
        self.assertEqual(source.id, "1")
        self.assertEqual(source.name, "Quito")
        self.assertEqual(source.geometry.wkt,
            'POLYGON((-122.5 38.0, -122.0 38.5, -121.5 38.0, '
            '-122.0 37.5, -122.5 38.0))')
        self.assertAlmostEqual(source.upper_depth, 0.0)
        self.assertAlmostEqual(source.lower_depth, 10.0)
        self.assertFalse(source.rupt_aspect_ratio)
        self.assertFalse(source.mag_scale_rel)
        self.assertFalse(source.mfd)
        self.assertFalse(source.nodal_plane_dist)
        self.assertFalse(source.hypo_depth_dist)
        
    def _check_point_source(self, source):
        self.assertTrue(isinstance(source, mtkPointSource))
        self.assertEqual(source.id, "2")
        self.assertEqual(source.name, "point")
        self.assertAlmostEqual(source.geometry.x, -122.0)
        self.assertAlmostEqual(source.geometry.y, 38.0)
        self.assertAlmostEqual(source.upper_depth, 0.0)
        self.assertAlmostEqual(source.lower_depth, 10.0)
        self.assertFalse(source.rupt_aspect_ratio)
        self.assertFalse(source.mag_scale_rel)
        self.assertFalse(source.mfd)
        self.assertFalse(source.nodal_plane_dist)
        self.assertFalse(source.hypo_depth_dist)

    def _check_simple_fault_source(self, source):
        self.assertTrue(isinstance(source, mtkSimpleFaultSource))
        self.assertEqual(source.id, "3")
        self.assertEqual(source.name, "Mount Diablo Thrust")
        self.assertAlmostEqual(source.dip, 45.0)
        self.assertAlmostEqual(source.upper_depth, 10.0)
        self.assertAlmostEqual(source.lower_depth, 20.0)
        self.assertEqual(
            str(source.fault_trace.points[0]),
            "<Latitude=37.730100, Longitude=-121.822900, Depth=0.0000>")
        self.assertEqual(
            str(source.fault_trace.points[1]),
            "<Latitude=37.877100, Longitude=-122.038800, Depth=0.0000>")
        self.assertFalse(source.rupt_aspect_ratio)
        self.assertFalse(source.mag_scale_rel)
        self.assertFalse(source.mfd)

    def _check_complex_fault_source(self, source):
        self.assertTrue(isinstance(source, mtkComplexFaultSource))
        self.assertEqual(source.id, "4")
        self.assertEqual(source.name, "Cascadia Megathrust")
        self.assertAlmostEqual(source.dip, 10.4179999)
        self.assertAlmostEqual(source.upper_depth, 4.89734)
        self.assertFalse(source.rupt_aspect_ratio)
        self.assertFalse(source.mag_scale_rel)
        self.assertFalse(source.mfd)

