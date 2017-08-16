# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2017 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import sys
import json
import numpy
import os
import io
import tempfile
import unittest

from collections import namedtuple

from openquake.commonlib import hazard_writers as writers
from openquake.commonlib.tests import _utils as utils, check_equal

HazardCurveData = namedtuple('HazardCurveData', 'location, poes')
UHSData = namedtuple('UHSData', 'location, imls')
Location = namedtuple('Location', 'x, y')
GmfNode = namedtuple('GmfNode', 'gmv, location')

path = None


def setUpModule():
    global path
    path = tempfile.NamedTemporaryFile().name


def tearDownModule():
    if sys.exc_info()[0] is None and os.path.exists(path):  # remove TMP
        os.remove(path)


class GmfCollection(object):

    def __init__(self, gmf_sets):
        self.gmf_sets = gmf_sets

    def __iter__(self):
        return iter(self.gmf_sets)


class GmfSet(object):

    def __init__(self, gmfs, investigation_time, stochastic_event_set_id=None):
        self.gmfs = gmfs
        self.investigation_time = investigation_time
        self.stochastic_event_set_id = stochastic_event_set_id

    def __iter__(self):
        return iter(self.gmfs)


class Gmf(object):

    def __init__(self, imt, sa_period, sa_damping, gmf_nodes, rupture_id=None):
        self.imt = imt
        self.sa_period = sa_period
        self.sa_damping = sa_damping
        self.rupture_id = rupture_id
        self.gmf_nodes = gmf_nodes

    def __iter__(self):
        return iter(self.gmf_nodes)


class SES(object):

    def __init__(self, ordinal, investigation_time, sesruptures):
        self.ordinal = ordinal
        self.investigation_time = investigation_time
        self.sesruptures = sesruptures

    def __iter__(self):
        return iter(self.sesruptures)


class ProbabilisticRupture(object):

    def __init__(self, rupture_id,
                 magnitude, strike, dip, rake, tectonic_region_type,
                 is_from_fault_source, is_multi_surface,
                 lons=None, lats=None, depths=None,
                 top_left_corner=None, top_right_corner=None,
                 bottom_right_corner=None, bottom_left_corner=None):
        self.id = rupture_id
        self.magnitude = magnitude
        self.strike = strike
        self.dip = dip
        self.rake = rake
        self.tectonic_region_type = tectonic_region_type
        self.is_from_fault_source = is_from_fault_source
        self.is_multi_surface = is_multi_surface
        self.lons = lons
        self.lats = lats
        self.depths = depths
        self.top_left_corner = top_left_corner
        self.top_right_corner = top_right_corner
        self.bottom_right_corner = bottom_right_corner
        self.bottom_left_corner = bottom_left_corner


class EBRupture(object):

    def __init__(self, rupture, ses, seed=0):
        self.rupture = rupture
        self.ses = ses
        self.seed = seed


class HazardWriterTestCase(unittest.TestCase):
    pass


class HazardCurveWriterTestCase(unittest.TestCase):

    FAKE_PATH = 'fake.xml'  # used when the writer raises ValueError
    TIME = 50.0
    IMLS = [0.005, 0.007, 0.0098]

    def test_validate_metadata_stats_and_smlt_path(self):
        # statistics + smlt path
        metadata = dict(
            investigation_time=self.TIME, imt='PGA', imls=self.IMLS,
            statistics='mean', smlt_path='foo'
        )
        self.assertRaises(
            ValueError, writers.HazardCurveXMLWriter,
            self.FAKE_PATH, **metadata
        )

    def test_validate_metadata_stats_and_gsimlt_path(self):
        # statistics + gsimlt path
        metadata = dict(
            investigation_time=self.TIME, imt='PGA', imls=self.IMLS,
            statistics='mean', gsimlt_path='foo'
        )
        self.assertRaises(
            ValueError, writers.HazardCurveXMLWriter,
            self.FAKE_PATH, **metadata
        )

    def test_validate_metadata_only_smlt_path(self):
        # only 1 logic tree path specified
        metadata = dict(
            investigation_time=self.TIME, imt='PGA', imls=self.IMLS,
            smlt_path='foo'
        )
        self.assertRaises(
            ValueError, writers.HazardCurveXMLWriter,
            self.FAKE_PATH, **metadata
        )

    def test_validate_metadata_only_gsimlt_path(self):
        # only 1 logic tree path specified
        metadata = dict(
            investigation_time=self.TIME, imt='PGA', imls=self.IMLS,
            gsimlt_path='foo'
        )
        self.assertRaises(
            ValueError, writers.HazardCurveXMLWriter,
            self.FAKE_PATH, **metadata
        )

    def test_validate_metadata_invalid_stats(self):
        # invalid stats type
        metadata = dict(
            investigation_time=self.TIME, imt='PGA', imls=self.IMLS,
            statistics='invalid'
        )
        self.assertRaises(
            ValueError, writers.HazardCurveXMLWriter,
            self.FAKE_PATH, **metadata
        )

    def test_validate_metadata_quantile_stats_with_no_value(self):
        # quantile statistics with no quantile value
        metadata = dict(
            investigation_time=self.TIME, imt='PGA', imls=self.IMLS,
            statistics='quantile'
        )
        self.assertRaises(
            ValueError, writers.HazardCurveXMLWriter,
            self.FAKE_PATH, **metadata
        )

    def test_validate_metadata_sa_with_no_period(self):
        # damping but no sa period
        metadata = dict(
            investigation_time=self.TIME, imt='SA', imls=self.IMLS,
            statistics='mean', sa_damping=5.0
        )
        self.assertRaises(
            ValueError, writers.HazardCurveXMLWriter,
            self.FAKE_PATH, **metadata
        )

    def test_validate_metadata_sa_with_no_damping(self):
        # sa period but no damping
        metadata = dict(
            investigation_time=self.TIME, imt='SA', imls=self.IMLS,
            statistics='mean', sa_period=5.0
        )
        self.assertRaises(
            ValueError, writers.HazardCurveXMLWriter,
            self.FAKE_PATH, **metadata
        )

    def test_validate_metadata_mean_stats_with_quantile_value(self):
        metadata = dict(
            investigation_time=self.TIME, imt='PGA', imls=self.IMLS,
            statistics='mean', quantile_value=5.0
        )
        self.assertRaises(
            ValueError, writers.HazardCurveXMLWriter,
            self.FAKE_PATH, **metadata
        )

    def test_validate_metadata_no_stats_with_quantile_value(self):
        metadata = dict(
            investigation_time=self.TIME, imt='PGA', imls=self.IMLS,
            quantile_value=5.0
        )
        self.assertRaises(
            ValueError, writers.HazardCurveXMLWriter,
            self.FAKE_PATH, **metadata
        )


class HazardCurveWriterSerializeTestCase(HazardCurveWriterTestCase):
    """
    Tests for the `serialize` method of the hazard curve writers.
    """

    def setUp(self):
        self.data = [
            HazardCurveData(location=Location(38.0, -20.1),
                            poes=[0.1, 0.2, 0.3]),
            HazardCurveData(location=Location(38.1, -20.2),
                            poes=[0.4, 0.5, 0.6]),
            HazardCurveData(location=Location(38.2, -20.3),
                            poes=[0.7, 0.8, 0.8]),
        ]

    def test_serialize(self):
        # Just a basic serialization test
        metadata = dict(
            investigation_time=self.TIME, imt='SA', imls=self.IMLS,
            sa_period=0.025, sa_damping=5.0, smlt_path='b1_b2_b4',
            gsimlt_path='b1_b4_b5'
        )
        writer = writers.HazardCurveXMLWriter(path, **metadata)
        writer.serialize(self.data)
        check_equal(__file__, 'expected_hazard_curves.xml', path)

    def test_serialize_geojson(self):
        expected = {
            u'features': [
                {u'geometry': {u'coordinates': [38.0, -20.1],
                               u'type': u'Point'},
                 u'properties': {u'poEs': [0.1, 0.2, 0.3]},
                 u'type': u'Feature'},
                {u'geometry': {u'coordinates': [38.1, -20.2],
                               u'type': u'Point'},
                 u'properties': {u'poEs': [0.4, 0.5, 0.6]},
                 u'type': u'Feature'},
                {u'geometry': {u'coordinates': [38.2, -20.3],
                               u'type': u'Point'},
                 u'properties': {u'poEs': [0.7, 0.8, 0.8]},
                 u'type': u'Feature'}],
            u'oqmetadata': {u'IMT': u'SA',
                            u'gsimTreePath': u'b1_b4_b5',
                            u'investigationTime': u'5.000000000E+01',
                            u'IMLs': [0.005, 0.007, 0.0098],
                            u'saDamping': u'5.000000000E+00',
                            u'saPeriod': u'2.500000000E-02',
                            u'sourceModelTreePath': u'b1_b2_b4'},
            u'oqnrmlversion': u'0.4',
            u'oqtype': u'HazardCurve',
            u'type': u'FeatureCollection'
        }

        metadata = dict(
            investigation_time=self.TIME, imt='SA', imls=self.IMLS,
            sa_period=0.025, sa_damping=5.0, smlt_path='b1_b2_b4',
            gsimlt_path='b1_b4_b5'
        )
        writer = writers.HazardCurveGeoJSONWriter(path, **metadata)
        writer.serialize(self.data)

        actual = json.load(open(path))
        self.assertEqual(expected, actual)

    def test_serialize_quantile(self):
        # Test serialization of qunatile curves.
        metadata = dict(
            investigation_time=self.TIME, imt='SA', imls=self.IMLS,
            sa_period=0.025, sa_damping=5.0, statistics='quantile',
            quantile_value=0.15
        )
        writer = writers.HazardCurveXMLWriter(path, **metadata)
        writer.serialize(self.data)
        check_equal(__file__, 'expected_quantile_curves.xml', path)

    def test_serialize_quantile_geojson(self):
        expected = {
            u'features': [
                {u'geometry': {u'coordinates': [38.0, -20.1],
                               u'type': u'Point'},
                 u'properties': {u'poEs': [0.1, 0.2, 0.3]},
                 u'type': u'Feature'},
                {u'geometry': {u'coordinates': [38.1, -20.2],
                               u'type': u'Point'},
                 u'properties': {u'poEs': [0.4, 0.5, 0.6]},
                 u'type': u'Feature'},
                {u'geometry': {u'coordinates': [38.2, -20.3],
                               u'type': u'Point'},
                 u'properties': {u'poEs': [0.7, 0.8, 0.8]},
                 u'type': u'Feature'}],
            u'oqmetadata': {u'IMT': u'SA',
                            u'investigationTime': u'5.000000000E+01',
                            u'IMLs': [0.005, 0.007, 0.0098],
                            u'saDamping': u'5.000000000E+00',
                            u'saPeriod': u'2.500000000E-02',
                            u'statistics': u'quantile',
                            u'quantileValue': u'1.500000000E-01'},
            u'oqnrmlversion': u'0.4',
            u'oqtype': u'HazardCurve',
            u'type': u'FeatureCollection'
        }

        metadata = dict(
            investigation_time=self.TIME, imt='SA', imls=self.IMLS,
            sa_period=0.025, sa_damping=5.0, statistics='quantile',
            quantile_value=0.15
        )
        writer = writers.HazardCurveGeoJSONWriter(path, **metadata)
        writer.serialize(self.data)

        actual = json.load(open(path))
        self.assertEqual(expected, actual)


class EventBasedGMFXMLWriterTestCase(HazardWriterTestCase):

    def test_serialize(self):
        # Test data is:
        # - 1 gmf collection
        # - 3 gmf sets
        # for each set:
        # - 2 ground motion fields
        # for each ground motion field:
        # - 2 nodes
        # Total nodes: 12
        locations = [Location(i * 0.1, i * 0.1) for i in range(12)]
        gmf_nodes = [GmfNode(i * 0.2, locations[i]) for i in range(12)]
        gmfs = [
            Gmf('SA', 0.1, 5.0, gmf_nodes[:2], 'i=1'),
            Gmf('SA', 0.2, 5.0, gmf_nodes[2:4], 'i=2'),
            Gmf('SA', 0.3, 5.0, gmf_nodes[4:6], 'i=3'),
            Gmf('PGA', None, None, gmf_nodes[6:8], 'i=4'),
            Gmf('PGA', None, None, gmf_nodes[8:10], 'i=5'),
            Gmf('PGA', None, None, gmf_nodes[10:], 'i=6'),
        ]
        gmf_sets = [
            GmfSet(gmfs[:2], 50.0, 1),
            GmfSet(gmfs[2:4], 40.0, 2),
            GmfSet(gmfs[4:], 30.0, 3),
        ]
        gmf_collection = GmfCollection(gmf_sets)

        sm_lt_path = 'b1_b2_b3'
        gsim_lt_path = 'b1_b7_b15'

        writer = writers.EventBasedGMFXMLWriter(
            path, sm_lt_path, gsim_lt_path)
        writer.serialize(gmf_collection)
        check_equal(__file__, 'expected_gmf.xml', path)


class HazardMapWriterTestCase(HazardWriterTestCase):

    def setUp(self):
        self.data = [
            (-1.0, 1.0, 0.01),
            (1.0, 1.0, 0.02),
            (1.0, -1.0, 0.03),
            (-1.0, -1.0, 0.04),
        ]

    def test_serialize_xml(self):
        metadata = dict(
            investigation_time=50.0, imt='SA', poe=0.1, sa_period=0.025,
            sa_damping=5.0, smlt_path='b1_b2_b4', gsimlt_path='b1_b4_b5'
        )
        writer = writers.HazardMapXMLWriter(path, **metadata)
        writer.serialize(self.data)
        check_equal(__file__, 'expected_hazard_map.xml',  path)

    def test_serialize_geojson(self):
        expected = {
            'type': 'FeatureCollection',
            'oqnrmlversion': '0.4',
            'oqtype': 'HazardMap',
            'oqmetadata': {
                'sourceModelTreePath': 'b1_b2_b4',
                'gsimTreePath': 'b1_b4_b5',
                'IMT': 'SA',
                'saPeriod': '0.025',
                'saDamping': '5.0',
                'investigationTime': '50.0',
                'poE': '0.1',
            },
            'features': [
                {'type': 'Feature',
                 'geometry': {'type': 'Point', 'coordinates': [-1.0, 1.0]},
                 'properties': {'iml': 0.01},
                 },
                {'type': 'Feature',
                 'geometry': {'type': 'Point', 'coordinates': [1.0, 1.0]},
                 'properties': {'iml': 0.02},
                 },
                {'type': 'Feature',
                 'geometry': {'type': 'Point', 'coordinates': [1.0, -1.0]},
                 'properties': {'iml': 0.03},
                 },
                {'type': 'Feature',
                 'geometry': {'type': 'Point', 'coordinates': [-1.0, -1.0]},
                 'properties': {'iml': 0.04},
                 },
            ],
        }

        metadata = dict(
            investigation_time=50.0, imt='SA', poe=0.1, sa_period=0.025,
            sa_damping=5.0, smlt_path='b1_b2_b4', gsimlt_path='b1_b4_b5'
        )
        writer = writers.HazardMapGeoJSONWriter(path, **metadata)
        writer.serialize(self.data)

        actual = json.load(open(path))
        self.assertEqual(expected, actual)

    def test_serialize_quantile_xml(self):
        metadata = dict(
            investigation_time=50.0, imt='SA', poe=0.1, sa_period=0.025,
            sa_damping=5.0, statistics='quantile', quantile_value=0.85
        )
        writer = writers.HazardMapXMLWriter(path, **metadata)
        writer.serialize(self.data)

        check_equal(__file__, 'expected_quantile.xml', path)

    def test_serialize_quantile_geojson(self):
        expected = {
            'type': 'FeatureCollection',
            'oqnrmlversion': '0.4',
            'oqtype': 'HazardMap',
            'oqmetadata': {
                'statistics': 'quantile',
                'quantileValue': '0.85',
                'IMT': 'SA',
                'saPeriod': '0.025',
                'saDamping': '5.0',
                'investigationTime': '50.0',
                'poE': '0.1',
            },
            'features': [
                {'type': 'Feature',
                 'geometry': {'type': 'Point', 'coordinates': [-1.0, 1.0]},
                 'properties': {'iml': 0.01},
                 },
                {'type': 'Feature',
                 'geometry': {'type': 'Point', 'coordinates': [1.0, 1.0]},
                 'properties': {'iml': 0.02},
                 },
                {'type': 'Feature',
                 'geometry': {'type': 'Point', 'coordinates': [1.0, -1.0]},
                 'properties': {'iml': 0.03},
                 },
                {'type': 'Feature',
                 'geometry': {'type': 'Point', 'coordinates': [-1.0, -1.0]},
                 'properties': {'iml': 0.04},
                 },
            ],
        }

        metadata = dict(
            investigation_time=50.0, imt='SA', poe=0.1, sa_period=0.025,
            sa_damping=5.0, statistics='quantile', quantile_value=0.85
        )
        writer = writers.HazardMapGeoJSONWriter(path, **metadata)
        writer.serialize(self.data)

        actual = json.load(open(path))
        self.assertEqual(expected, actual)


class DisaggXMLWriterTestCase(HazardWriterTestCase):

    def setUp(self):
        self.metadata = dict(
            investigation_time=50.0,
            imt='SA',
            lon=8.33,
            lat=47.22,
            sa_period=0.1,
            sa_damping=5.0,
            mag_bin_edges=[5, 6],
            dist_bin_edges=[0, 20, 40],
            lon_bin_edges=[6, 7, 8, 9, 10],
            lat_bin_edges=[46, 47, 48, 49, 50],
            eps_bin_edges=[-0.5, 0.5, 1.5, 2.5],
            tectonic_region_types=['active shallow crust',
                                   'stable continental'],
            smlt_path='b1_b2_b3',
            gsimlt_path='b1_b7_b15',

        )

        poe = 0.02
        iml = 2.13

        matrices = [
            # mag
            numpy.array([x * 0.01 for x in range(2)]),
            # dist
            numpy.array([x * 0.01 for x in range(3)]),
            # TRT
            numpy.array([x * 0.01 for x in range(2)]),
            # mag, dist
            numpy.array([x * 0.01 for x in range(6)]).reshape((2, 3)),
            # mag, dist, eps
            numpy.array([x * 0.01 for x in range(24)]).reshape((2, 3, 4)),
            # lon, lat
            numpy.array([x * 0.01 for x in range(25)]).reshape((5, 5)),
            # mag, lon, lat
            numpy.array([x * 0.01 for x in range(50)]).reshape((2, 5, 5)),
            # lon, lat, trt
            numpy.array([x * 0.01 for x in range(50)]).reshape((5, 5, 2)),
        ]

        class DissMatrix(object):
            def __init__(self, matrix, dim_labels, poe, iml):
                self.matrix = matrix
                self.dim_labels = dim_labels
                self.poe = poe
                self.iml = iml

        self.data = [
            DissMatrix(matrices[0], ['Mag'],
                       poe + 0.001, iml - 0.001),
            DissMatrix(matrices[1], ['Dist'],
                       poe + 0.002, iml - 0.002),
            DissMatrix(matrices[2], ['TRT'],
                       poe + 0.003, iml - 0.003),
            DissMatrix(matrices[3], ['Mag', 'Dist'],
                       poe + 0.004, iml - 0.004),
            DissMatrix(matrices[4], ['Mag', 'Dist', 'Eps'],
                       poe + 0.005, iml - 0.005),
            DissMatrix(matrices[5], ['Lon', 'Lat'],
                       poe + 0.006, iml - 0.006),
            DissMatrix(matrices[6], ['Mag', 'Lon', 'Lat'],
                       poe + 0.007, iml - 0.007),
            DissMatrix(matrices[7], ['Lon', 'Lat', 'TRT'],
                       poe + 0.008, iml - 0.008),
        ]

    def test_serialize(self):
        writer = writers.DisaggXMLWriter(path, **self.metadata)
        writer.serialize(self.data)
        check_equal(__file__, 'expected_disagg.xml', path)


class UHSXMLWriterTestCase(unittest.TestCase):

    TIME = 50.0
    POE = 0.1
    FAKE_PATH = 'fake'

    @classmethod
    def setUpClass(cls):
        cls.expected_xml = io.StringIO(u"""\
<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <uniformHazardSpectra sourceModelTreePath="foo" gsimTreePath="bar" investigationTime="50.0" poE="0.1">
    <periods>0.0 0.025 0.1 0.2</periods>
    <uhs>
      <gml:Point>
        <gml:pos>0.0 0.0</gml:pos>
      </gml:Point>
      <IMLs>0.3 0.5 0.2 0.1</IMLs>
    </uhs>
    <uhs>
      <gml:Point>
        <gml:pos>1.0 1.0</gml:pos>
      </gml:Point>
      <IMLs>0.4 0.6 0.3 0.05</IMLs>
    </uhs>
  </uniformHazardSpectra>
</nrml>
""")
        cls.expected_mean_xml = io.StringIO(u"""\
<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <uniformHazardSpectra statistics="mean" investigationTime="50.0" poE="0.1">
    <periods>0.0 0.025 0.1 0.2</periods>
    <uhs>
      <gml:Point>
        <gml:pos>0.0 0.0</gml:pos>
      </gml:Point>
      <IMLs>0.3 0.5 0.2 0.1</IMLs>
    </uhs>
    <uhs>
      <gml:Point>
        <gml:pos>1.0 1.0</gml:pos>
      </gml:Point>
      <IMLs>0.4 0.6 0.3 0.05</IMLs>
    </uhs>
  </uniformHazardSpectra>
</nrml>
""")
        cls.expected_quantile_xml = io.StringIO(u"""\
<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <uniformHazardSpectra statistics="quantile" quantileValue="0.95" investigationTime="50.0" poE="0.1">
    <periods>0.0 0.025 0.1 0.2</periods>
    <uhs>
      <gml:Point>
        <gml:pos>0.0 0.0</gml:pos>
      </gml:Point>
      <IMLs>0.3 0.5 0.2 0.1</IMLs>
    </uhs>
    <uhs>
      <gml:Point>
        <gml:pos>1.0 1.0</gml:pos>
      </gml:Point>
      <IMLs>0.4 0.6 0.3 0.05</IMLs>
    </uhs>
  </uniformHazardSpectra>
</nrml>
""")
        cls.data = [
            UHSData(Location(0.0, 0.0), [0.3, 0.5, 0.2, 0.1]),
            UHSData(Location(1.0, 1.0), [0.4, 0.6, 0.3, 0.05]),
        ]

    def setUp(self):
        self.metadata = dict(
            investigation_time=self.TIME,
            poe=0.1,
            smlt_path='foo',
            gsimlt_path='bar',
            periods=[0.0, 0.025, 0.1, 0.2],
        )

    def test_constructor_poe_is_none_or_missing(self):
        self.metadata['poe'] = None
        self.assertRaises(
            ValueError, writers.UHSXMLWriter,
            self.FAKE_PATH, **self.metadata
        )

        del self.metadata['poe']
        self.assertRaises(
            ValueError, writers.UHSXMLWriter,
            self.FAKE_PATH, **self.metadata
        )

    def test_constructor_periods_is_none_or_missing(self):
        self.metadata['periods'] = None
        self.assertRaises(
            ValueError, writers.UHSXMLWriter,
            self.FAKE_PATH, **self.metadata
        )

        del self.metadata['periods']
        self.assertRaises(
            ValueError, writers.UHSXMLWriter,
            self.FAKE_PATH, **self.metadata
        )

    def test_constructor_periods_is_empty_list(self):
        self.metadata['periods'] = []
        self.assertRaises(
            ValueError, writers.UHSXMLWriter,
            self.FAKE_PATH, **self.metadata
        )

    def test_constructor_periods_not_sorted(self):
        self.metadata['periods'] = [0.025, 0.0, 0.1, 0.2]
        self.assertRaises(
            ValueError, writers.UHSXMLWriter,
            self.FAKE_PATH, **self.metadata
        )

    def test_serialize(self):
        writer = writers.UHSXMLWriter(path, **self.metadata)

        writer.serialize(self.data)

        utils.assert_xml_equal(self.expected_xml, path)

    def test_serialize_mean(self):
        del self.metadata['smlt_path']
        del self.metadata['gsimlt_path']
        self.metadata['statistics'] = 'mean'

        writer = writers.UHSXMLWriter(path, **self.metadata)
        writer.serialize(self.data)
        utils.assert_xml_equal(self.expected_mean_xml, path)

    def test_serialize_quantile(self):
        del self.metadata['smlt_path']
        del self.metadata['gsimlt_path']
        self.metadata['statistics'] = 'quantile'
        self.metadata['quantile_value'] = 0.95

        writer = writers.UHSXMLWriter(path, **self.metadata)
        writer.serialize(self.data)
        utils.assert_xml_equal(self.expected_quantile_xml, path)
