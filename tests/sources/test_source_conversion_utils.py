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
Tests the methods of the module hmtk.sources.source_conversion_utils
'''

import unittest
import numpy as np
from openquake.nrmllib import models
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib import mfd
from openquake.hazardlib.scalerel.wc1994 import WC1994
from openquake.hazardlib.geo.line import Line
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.nodalplane import NodalPlane
from hmtk.sources import source_conversion_utils as conv

class TestMFDConverters(unittest.TestCase):
    '''
    Tests the magnitude frequency conversion utils functions
    :class: hmtk.sources.source_conversion_utils.ConvertTruncGR and
    :class: hmtk.sources.source_conversion_utils.ConvertIncremental
    '''

    def setUp(self):
        '''
        '''
        self.model = None
        self.model_gr = mfd.truncated_gr.TruncatedGRMFD(
            min_mag=5.0,
            max_mag=8.0,
            bin_width=0.1,
            a_val=4.0,
            b_val=1.0)

        self.model_ed = mfd.evenly_discretized.EvenlyDiscretizedMFD(
            min_mag=5.0,
            bin_width=0.1,
            occurrence_rates=[1., 1., 1., 1., 1.])

    def test_truncgr(self):
        '''
        Tests the truncated Gutenberg Richter class
        '''
        expected = {'a_val': 4.0, 'b_val': 1.0, 'min_mag': 5.0, 'max_mag': 8.0}
        self.model = conv.ConvertTruncGR()
        output = self.model.convert(self.model_gr)
        for key in expected.keys():
            self.assertAlmostEqual(expected[key], output.__dict__[key])

    def test_incrementalmfd(self):
        '''
        Tests the evenly discretized MFD class
        '''
        expected = {'min_mag': 5.0, 'bin_width': 0.1,
                    'occur_rates': np.ones(5, dtype=float)}
        self.model = conv.ConvertIncremental()
        output = self.model.convert(self.model_ed)
        self.assertAlmostEqual(output.__dict__['min_mag'], 5.0)
        self.assertAlmostEqual(output.__dict__['bin_width'], 0.1)
        np.testing.assert_array_almost_equal(
            output.__dict__['occur_rates'], np.ones(5, dtype=float))

    def test_render_mfd_truncgr(self):
        '''
        Tests the function to render the mfd given a valid :class:
        openquake.hazardlib.mfd.truncated_gr.TruncGRMFD
        '''
        expected = {'a_val': 4.0, 'b_val': 1.0, 'min_mag': 5.0, 'max_mag': 8.0}
        output = conv.render_mfd(self.model_gr)
        for key in expected.keys():
            self.assertAlmostEqual(expected[key], output.__dict__[key])

    def test_render_mfd_evenly_discrtized(self):
        '''
        Tests the function to render the mfd given a valid :class:
        openquake.hazardlib.mfd.evenly_discretized.EvenlyDiscretizedMFD
        '''
        expected = {'min_mag': 5.0, 'bin_width': 0.1,
                    'occur_rates': np.ones(5, dtype=float)}
        output = conv.render_mfd(self.model_ed)
        self.assertAlmostEqual(output.__dict__['min_mag'], 5.0)
        self.assertAlmostEqual(output.__dict__['bin_width'], 0.1)
        np.testing.assert_array_almost_equal(
            output.__dict__['occur_rates'], np.ones(5, dtype=float))

    def test_raise_error_unrecognised_mfd(self):
        '''
        Tests that the render_mfd function raises an error when
        rendering an unsupported MFD
        '''
        class BadInput(object):
            def __init__(self):
                return

        with self.assertRaises(ValueError) as ae:
            _ = conv.render_mfd(BadInput())
            self.assertEqual(ae.exception.message,
                             'Magnitude frequency distribution BadInput not '
                             'supported')

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
            _ = conv.render_aspect_ratio(None)
            self.assertEqual(ae.exception.message,
                             'Rupture aspect ratio not defined!')

class TestRenderMagScaleRel(unittest.TestCase):
    '''
    Tests the function to render the magnitude scaling relation
    '''
    def setUp(self):
        '''
        '''
        self.msr = WC1994()

    def test_valid_mag_scale_rel(self):
        '''
        When input with a valid MSR class should return name of class
        '''
        self.assertEqual(conv.render_mag_scale_rel(self.msr), 'WC1994')


    def test_missing_value_with_default(self):
        '''
        Tests the case when the attibute is missing but the use_defaults
        option is selected
        '''
        self.assertAlmostEqual(
            conv.render_mag_scale_rel(None, use_default=True),
            'WC1994')

    def test_missing_value_no_default(self):
        '''
        Tests the case when the attribute is missing and the use_defaults
        option is not selected. Should raise ValueError
        '''
        with self.assertRaises(ValueError) as ae:
            _ = conv.render_mag_scale_rel(None)
            self.assertEqual(ae.exception.message,
                             'Magnitude Scaling Relation Not Defined!')



class TestRenderNodalPlane(unittest.TestCase):
    '''
    Tests the rendering of the models.NodalPlane
    '''
    def setUp(self):
        '''
        '''
        self.npd_as_list = [models.NodalPlane(0.5, 0., 90., 0.),
                            models.NodalPlane(0.5, 90., 90., 180.)]

        self.npd_as_pmf = PMF([(0.5, NodalPlane(0., 90., 0.)),
                               (0.5, NodalPlane(90., 90., 180.))])

        self.npd_as_pmf_bad = PMF([(0.5, None),
                                    (0.5, NodalPlane(90., 90., 180.))])

    def test_render_nodal_planes_as_list(self):
        '''
        Tests the workflow when nodal planes already input as a list of
        models.NodalPlane class
        '''
        output = conv.render_npd(self.npd_as_list)
        self.assertAlmostEqual(output[0].probability, 0.5)
        self.assertAlmostEqual(output[0].strike, 0.)
        self.assertAlmostEqual(output[0].dip, 90.)
        self.assertAlmostEqual(output[0].rake, 0.)
        self.assertAlmostEqual(output[1].probability, 0.5)
        self.assertAlmostEqual(output[1].strike, 90.)
        self.assertAlmostEqual(output[1].dip, 90.)
        self.assertAlmostEqual(output[1].rake, 180.)

    def test_render_nodal_planes_as_pmf_good(self):
        '''
        Tests the workflow when nodal planes input as a PMF
        '''
        output = conv.render_npd(self.npd_as_pmf)
        self.assertAlmostEqual(output[0].probability, 0.5)
        self.assertAlmostEqual(output[0].strike, 0.)
        self.assertAlmostEqual(output[0].dip, 90.)
        self.assertAlmostEqual(output[0].rake, 0.)
        self.assertAlmostEqual(output[1].probability, 0.5)
        self.assertAlmostEqual(output[1].strike, 90.)
        self.assertAlmostEqual(output[1].dip, 90.)
        self.assertAlmostEqual(output[1].rake, 180.)

    def test_render_nodal_planes_as_pmf_bad_1(self):
        '''
        Tests the workflow when nodal planes input as a PMF without instance
        of openquake.hazardlib.geo.nodal_plane.NodalPlane :class:
        '''
        with self.assertRaises(ValueError) as ae:
            output = conv.render_npd(self.npd_as_pmf_bad)
            self.assertEqual(ae.exception.message,
                'Nodal Planes incorrectly formatted!')

    def test_render_nodal_planes_as_pmf_bad_2(self):
        '''
        Tests the workflow when nodal planes input as a PMF without
        probabilities summing to 1.0
        '''
        self.npd_as_pmf.data[1] = (0.4, NodalPlane(90., 90., 180.))
        with self.assertRaises(ValueError) as ae:
            output = conv.render_npd(self.npd_as_pmf)
            self.assertEqual(ae.exception.message,
                'Nodal Plane probabilities do not sum to 1.0')

    def test_render_nodal_planes_null_default(self):
        '''
        Tests the rendering of the nodal planes when no input is specified,
        but the use_defaults is on.
        '''
        output = conv.render_npd(None, use_default=True)
        self.assertAlmostEqual(output[0].probability, 1.0)
        self.assertAlmostEqual(output[0].strike, 0.)
        self.assertAlmostEqual(output[0].dip, 90.)
        self.assertAlmostEqual(output[0].rake, 0.)

    def test_render_nodal_planes_null(self):
        '''
        Tests the rendering of the nodal planes when no input is specified
        and no defaults are permitted. Should raise ValueError
        '''
        with self.assertRaises(ValueError) as ae:
            output = conv.render_npd(None)
            self.assertEqual(ae.exception.message,
                'Nodal Plane distribution not defined')


class TestRenderHypoDepth(unittest.TestCase):
    '''
    Tests the rendering of the hypocentral depth distribution
    '''
    def setUp(self):
        '''
        '''
        self.depth_as_list = [models.HypocentralDepth(0.5, 5.),
                              models.HypocentralDepth(0.5, 10.)]

        self.depth_as_pmf = PMF([(0.5, 5.), (0.5, 10.)])

    def test_good_instance_list(self):
        '''
        Tests good output when list of instances of :class:
        models.HypocentralDepth are passed
        '''
        output = conv.render_hdd(self.depth_as_list)
        self.assertAlmostEqual(output[0].probability, 0.5)
        self.assertAlmostEqual(output[0].depth, 5.)
        self.assertAlmostEqual(output[1].probability, 0.5)
        self.assertAlmostEqual(output[1].depth, 10.)

    def test_good_instance_pmf(self):
        '''
        Tests good output when openquake.hazardlib.pmf.PMF class is passed
        '''
        output = conv.render_hdd(self.depth_as_pmf)
        self.assertAlmostEqual(output[0].probability, 0.5)
        self.assertAlmostEqual(output[0].depth, 5.)
        self.assertAlmostEqual(output[1].probability, 0.5)
        self.assertAlmostEqual(output[1].depth, 10.)

    def test_bad_instance_pmf(self):
        '''
        Tests function when openquake.hazardlib.pmf.PMF class is passed
        with probabilities not equal to 1.0. Should raise ValueError
        '''
        self.depth_as_pmf.data[1] = (0.4, 10.)
        with self.assertRaises(ValueError) as ae:
            output = conv.render_hdd(self.depth_as_pmf)
            self.assertEqual(ae.exception.message,
                'Hypocentral depth distribution probabilities do not sum to '
                '1.0')

    def test_no_input_with_defaults(self):
        '''
        Tests hypocentral depth distribution renderer when no input is
        supplied but the user opts to accept defaults
        '''
        output = conv.render_hdd(None, use_default=True)
        self.assertAlmostEqual(output[0].probability, 1.0)
        self.assertAlmostEqual(output[0].depth, 10.0)

    def test_no_input_without_defaults(self):
        '''
        Tests hypocentral depth distribution renderer when no input is
        supplied but the user does not accept defaults. Should raise
        ValueError
        '''
        with self.assertRaises(ValueError) as ae:
            output = conv.render_hdd(None)
            self.assertEqual(ae.exception.message,
                'Hypocentral depth distribution not defined!')


class TestConvertSourceGeometries(unittest.TestCase):
    '''
    Class to test the functions simple_trace_to_wkt_linestring and
    complex_trace_to_wkt_linestring, which convert a simple edge or
    set of edges to linestrings
    '''
    def setUp(self):
        '''
        '''
        self.simple_edge = Line([Point(10.5, 10.5, 1.0),
                                 Point(11.35, 11.45, 2.0)])

        top_edge = Line([Point(10.5, 10.5, 1.0), Point(11.35, 11.45, 2.0)])
        int_edge = Line([Point(10.5, 10.5, 20.0), Point(11.35, 11.45, 21.0)])
        low_edge = Line([Point(10.5, 10.5, 40.0), Point(11.35, 11.45, 40.0)])

        self.complex_edge = [top_edge, int_edge, low_edge]

    def test_simple_trace_to_wkt(self):
        '''
        Tests the conversion of a simple trace to a 2-D linestring
        '''
        expected = 'LINESTRING (10.5 10.5, 11.35 11.45)'
        self.assertEqual(
            conv.simple_trace_to_wkt_linestring(self.simple_edge),
            expected)

    def test_simple_edge_to_wkt(self):
        '''
        Tests the conversion of a simple trace to a 3-D linestring
        '''
        expected = 'LINESTRING (10.5 10.5 1.0, 11.35 11.45 2.0)'
        self.assertEqual(
            conv.simple_edge_to_wkt_linestring(self.simple_edge),
            expected)


    def test_complex_trace_to_wkt(self):
        '''
        Tests the conversion of a list of instances of the :class:
        openquake.hazardlib.geo.line.Line to :class:
        models.ComplexFaultGeometry
        '''
        model = conv.complex_trace_to_wkt_linestring(self.complex_edge)
        self.assertEqual(model.top_edge_wkt,
                        'LINESTRING (10.5 10.5 1.0, 11.35 11.45 2.0)')
        self.assertListEqual(model.int_edges,
                             ['LINESTRING (10.5 10.5 20.0, 11.35 11.45 21.0)'])
        self.assertEqual(model.bottom_edge_wkt,
                        'LINESTRING (10.5 10.5 40.0, 11.35 11.45 40.0)')
