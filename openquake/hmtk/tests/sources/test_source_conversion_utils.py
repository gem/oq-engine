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
Tests the methods of the module openquake.hmtk.sources.source_conversion_utils
'''

import unittest
import numpy as np
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib import mfd
from openquake.hazardlib.scalerel.wc1994 import WC1994
from openquake.hazardlib.geo.line import Line
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.nodalplane import NodalPlane
from openquake.hmtk.sources import source_conversion_utils as conv

class TestRenderAspectRatio(unittest.TestCase):
    '''
    Tests the function to render the aspect ratio
    '''
    def setUp(self):
        '''
        '''

    def test_good_aspect_ratio(self):
        '''
        Test the simple case when a valid aspect ratio is input
        '''
        self.assertAlmostEqual(conv.render_aspect_ratio(1.5), 1.5)

    def test_missing_value_with_default(self):
        '''
        Tests the case when the attibute is missing but the use_defaults
        option is selected
        '''
        self.assertAlmostEqual(
            conv.render_aspect_ratio(None, use_default=True),
            1.0)

    def test_missing_value_no_default(self):
        '''
        Tests the case when the attribute is missing and the use_defaults
        option is not selected. Should raise ValueError
        '''
        with self.assertRaises(ValueError) as ae:
            conv.render_aspect_ratio(None)
        self.assertEqual(str(ae.exception),
                         'Rupture aspect ratio not defined!')


class TestRenderMSRToHazardlib(unittest.TestCase):
    """
    Tests the function to render the msr to the oq-hazardlib instance
    """
    def setUp(self):
        """
        """
        self.msr = WC1994()

    def test_valid_msr_in_hazlib_format(self):
        """
        Tests the case when the input is already in hazardlib format
        """
        self.assertIsInstance(conv.mag_scale_rel_to_hazardlib(self.msr),
                              WC1994)

    def test_valid_msr_in_str_format(self):
        """
        Tests the case when the input is already in hazardlib format
        """
        self.assertIsInstance(conv.mag_scale_rel_to_hazardlib('WC1994'),
                              WC1994)

    def test_missing_value_with_default(self):
        # Tests the case when the attibute is missing but the use_defaults
        # option is selected
        self.assertIsInstance(
            conv.mag_scale_rel_to_hazardlib(None, use_default=True),
            WC1994)

    def test_missing_value_no_default(self):
        # Tests the case when the attribute is missing and the use_defaults
        # option is not selected. Should raise ValueError
        with self.assertRaises(ValueError) as ae:
            conv.mag_scale_rel_to_hazardlib('rubbish')
        self.assertEqual(str(ae.exception),
                         'Magnitude scaling relation rubbish not supported!')


class TestNPDtoPMF(unittest.TestCase):
    """
    Tests the function to convert the nodal plane distribution to the :class:
    openquake.hazardlib.pmf.PMF
    """
    def setUp(self):
        self.npd_as_pmf = PMF([(0.5, NodalPlane(0., 90., 0.)),
                               (0.5, NodalPlane(90., 90., 180.))])

        self.npd_as_pmf_bad = PMF([(0.5, None),
                                   (0.5, NodalPlane(90., 90., 180.))])

    def test_class_as_pmf(self):
        # Tests the case when a PMF is already input

        output = conv.npd_to_pmf(self.npd_as_pmf)
        self.assertAlmostEqual(output.data[0][0], 0.5)
        self.assertAlmostEqual(output.data[0][1].strike, 0.)
        self.assertAlmostEqual(output.data[0][1].dip, 90.)
        self.assertAlmostEqual(output.data[0][1].rake, 0.)
        self.assertAlmostEqual(output.data[1][0], 0.5)
        self.assertAlmostEqual(output.data[1][1].strike, 90.)
        self.assertAlmostEqual(output.data[1][1].dip, 90.)
        self.assertAlmostEqual(output.data[1][1].rake, 180.)

    def test_default(self):
        # Tests the case when the default class is raised

        output = conv.npd_to_pmf(None, True)
        self.assertAlmostEqual(output.data[0][0], 1.0)
        self.assertAlmostEqual(output.data[0][1].strike, 0.)
        self.assertAlmostEqual(output.data[0][1].dip, 90.)
        self.assertAlmostEqual(output.data[0][1].rake, 0.)

    def test_render_nodal_planes_null(self):
        # Tests the rendering of the nodal planes when no input is specified
        # and no defaults are permitted. Should raise ValueError

        with self.assertRaises(ValueError) as ae:
            conv.npd_to_pmf(None)
        self.assertEqual(str(ae.exception),
                         'Nodal Plane distribution not defined')


class TestHDDtoHazardlib(unittest.TestCase):
    """
    Class to test the function hdd_to_pmf, which converts the hypocentral
    distribution to the :class: openquake.hazardlib.pmf.PMF
    """
    def setUp(self):
        self.depth_as_pmf = PMF([(0.5, 5.), (0.5, 10.)])

    def test_input_as_pmf(self):
        # Tests the function when a valid PMF is input

        output = conv.hdd_to_pmf(self.depth_as_pmf)
        self.assertIsInstance(output, PMF)
        self.assertAlmostEqual(output.data[0][0], 0.5)
        self.assertAlmostEqual(output.data[0][1], 5.)
        self.assertAlmostEqual(output.data[1][0], 0.5)
        self.assertAlmostEqual(output.data[1][1], 10.)

    def test_default_input(self):
        # Tests the case when a default value is selected

        output = conv.hdd_to_pmf(None, True)
        self.assertIsInstance(output, PMF)
        self.assertAlmostEqual(output.data[0][0], 1.0)
        self.assertAlmostEqual(output.data[0][1], 10.0)

    def test_bad_input(self):
        # Tests raises value error when no input and no defaults are selected

        with self.assertRaises(ValueError) as ae:
            conv.hdd_to_pmf(None)
        self.assertEqual(str(ae.exception),
                         'Hypocentral depth distribution not defined!')


class TestConvertSourceGeometries(unittest.TestCase):
    '''
    Class to test the functions simple_trace_to_wkt_linestring and
    complex_trace_to_wkt_linestring, which convert a simple edge or
    set of edges to linestrings
    '''
    def setUp(self):
        self.simple_edge = Line([Point(10.5, 10.5, 1.0),
                                 Point(11.35, 11.45, 2.0)])

        top_edge = Line([Point(10.5, 10.5, 1.0), Point(11.35, 11.45, 2.0)])
        int_edge = Line([Point(10.5, 10.5, 20.0), Point(11.35, 11.45, 21.0)])
        low_edge = Line([Point(10.5, 10.5, 40.0), Point(11.35, 11.45, 40.0)])

        self.complex_edge = [top_edge, int_edge, low_edge]

    def test_simple_trace_to_wkt(self):
        # Tests the conversion of a simple trace to a 2-D linestring
        expected = 'LINESTRING (10.5 10.5, 11.35 11.45)'
        self.assertEqual(
            conv.simple_trace_to_wkt_linestring(self.simple_edge),
            expected)

    def test_simple_edge_to_wkt(self):
        # Tests the conversion of a simple trace to a 3-D linestring
        expected = 'LINESTRING (10.5 10.5 1.0, 11.35 11.45 2.0)'
        self.assertEqual(
            conv.simple_edge_to_wkt_linestring(self.simple_edge),
            expected)
