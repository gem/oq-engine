# Copyright (c) 2012-2013, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.


import json
import numpy
import os
import StringIO
import tempfile
import unittest

from collections import namedtuple

from lxml import etree

from openquake.nrmllib.hazard import writers
from openquake.nrmllib.hazard import parsers

from tests import _utils as utils

HazardCurveData = namedtuple('HazardCurveData', 'location, poes')
UHSData = namedtuple('UHSData', 'location, imls')
Location = namedtuple('Location', 'x, y')
GmfNode = namedtuple('GmfNode', 'gmv, location')


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

    def __init__(self, ordinal, investigation_time, ruptures):
        self.ordinal = ordinal
        self.investigation_time = investigation_time
        self.ruptures = ruptures

    def __iter__(self):
        return iter(self.ruptures)


class SESRupture(object):

    tag = "TAG"

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


class HazardCurveWriterTestCase(unittest.TestCase):

    FAKE_PATH = 'TODO'  # use a place in /tmp
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

        _, self.path = tempfile.mkstemp()

    def tearDown(self):
        os.unlink(self.path)

    def test_serialize(self):
        # Just a basic serialization test.
        expected = StringIO.StringIO("""\
<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <hazardCurves sourceModelTreePath="b1_b2_b4" gsimTreePath="b1_b4_b5" IMT="SA" investigationTime="50.0" saPeriod="0.025" saDamping="5.0">
    <IMLs>0.005 0.007 0.0098</IMLs>
    <hazardCurve>
      <gml:Point>
        <gml:pos>38.0 -20.1</gml:pos>
      </gml:Point>
      <poEs>0.1 0.2 0.3</poEs>
    </hazardCurve>
    <hazardCurve>
      <gml:Point>
        <gml:pos>38.1 -20.2</gml:pos>
      </gml:Point>
      <poEs>0.4 0.5 0.6</poEs>
    </hazardCurve>
    <hazardCurve>
      <gml:Point>
        <gml:pos>38.2 -20.3</gml:pos>
      </gml:Point>
      <poEs>0.7 0.8 0.8</poEs>
    </hazardCurve>
  </hazardCurves>
</nrml>
""")

        metadata = dict(
            investigation_time=self.TIME, imt='SA', imls=self.IMLS,
            sa_period=0.025, sa_damping=5.0, smlt_path='b1_b2_b4',
            gsimlt_path='b1_b4_b5'
        )
        writer = writers.HazardCurveXMLWriter(self.path, **metadata)
        writer.serialize(self.data)

        utils.assert_xml_equal(expected, self.path)
        self.assertTrue(utils.validates_against_xml_schema(self.path))

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
                            u'investigationTime': u'50.0',
                            u'IMLs': [0.005, 0.007, 0.0098],
                            u'saDamping': u'5.0',
                            u'saPeriod': u'0.025',
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
        writer = writers.HazardCurveGeoJSONWriter(self.path, **metadata)
        writer.serialize(self.data)

        actual = json.load(open(self.path))
        self.assertEqual(expected, actual)


    def test_serialize_quantile(self):
        # Test serialization of qunatile curves.
        expected = StringIO.StringIO("""\
<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <hazardCurves statistics="quantile" quantileValue="0.15" IMT="SA" investigationTime="50.0" saPeriod="0.025" saDamping="5.0">
    <IMLs>0.005 0.007 0.0098</IMLs>
    <hazardCurve>
      <gml:Point>
        <gml:pos>38.0 -20.1</gml:pos>
      </gml:Point>
      <poEs>0.1 0.2 0.3</poEs>
    </hazardCurve>
    <hazardCurve>
      <gml:Point>
        <gml:pos>38.1 -20.2</gml:pos>
      </gml:Point>
      <poEs>0.4 0.5 0.6</poEs>
    </hazardCurve>
    <hazardCurve>
      <gml:Point>
        <gml:pos>38.2 -20.3</gml:pos>
      </gml:Point>
      <poEs>0.7 0.8 0.8</poEs>
    </hazardCurve>
  </hazardCurves>
</nrml>
""")

        metadata = dict(
            investigation_time=self.TIME, imt='SA', imls=self.IMLS,
            sa_period=0.025, sa_damping=5.0, statistics='quantile',
            quantile_value=0.15
        )
        writer = writers.HazardCurveXMLWriter(self.path, **metadata)
        writer.serialize(self.data)

        utils.assert_xml_equal(expected, self.path)
        self.assertTrue(utils.validates_against_xml_schema(self.path))

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
                            u'investigationTime': u'50.0',
                            u'IMLs': [0.005, 0.007, 0.0098],
                            u'saDamping': u'5.0',
                            u'saPeriod': u'0.025',
                            u'statistics': u'quantile',
                            u'quantileValue': u'0.15'},
            u'oqnrmlversion': u'0.4',
            u'oqtype': u'HazardCurve',
            u'type': u'FeatureCollection'
        }

        metadata = dict(
            investigation_time=self.TIME, imt='SA', imls=self.IMLS,
            sa_period=0.025, sa_damping=5.0, statistics='quantile',
            quantile_value=0.15
        )
        writer = writers.HazardCurveGeoJSONWriter(self.path, **metadata)
        writer.serialize(self.data)

        actual = json.load(open(self.path))
        self.assertEqual(expected, actual)


class MultiHazardCurveXMLWriterSerializeTestCase(unittest.TestCase):
    """
    Tests for the `serialize` method of the hazard curve XML writer.
    """

    def setUp(self):
        self.data1 = [
            HazardCurveData(location=Location(38.0, -20.1),
                            poes=[0.1, 0.2, 0.3]),
            HazardCurveData(location=Location(38.1, -20.2),
                            poes=[0.4, 0.5, 0.6]),
            HazardCurveData(location=Location(38.2, -20.3),
                            poes=[0.7, 0.8, 0.8]),
        ]

        self.data2 = [
            HazardCurveData(location=Location(38.0, -20.1),
                            poes=[0.01, 0.02, 0.03]),
            HazardCurveData(location=Location(38.1, -20.2),
                            poes=[0.04, 0.05, 0.06]),
            HazardCurveData(location=Location(38.2, -20.3),
                            poes=[0.07, 0.08, 0.08]),
        ]

        _, self.path = tempfile.mkstemp()

    def tearDown(self):
        os.unlink(self.path)

    def test_serialize(self):
        # Just a basic serialization test.
        expected = StringIO.StringIO("""\
<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
  <hazardCurves sourceModelTreePath="b1_b2_b4"
                gsimTreePath="b1_b4_b5" IMT="SA" investigationTime="50"
                saPeriod="0.025" saDamping="5.0">
    <IMLs>0.005 0.007 0.0098</IMLs>
    <hazardCurve>
      <gml:Point>
        <gml:pos>38.0 -20.1</gml:pos>
      </gml:Point>
      <poEs>0.1 0.2 0.3</poEs>
    </hazardCurve>
    <hazardCurve>
      <gml:Point>
        <gml:pos>38.1 -20.2</gml:pos>
      </gml:Point>
      <poEs>0.4 0.5 0.6</poEs>
    </hazardCurve>
    <hazardCurve>
      <gml:Point>
        <gml:pos>38.2 -20.3</gml:pos>
      </gml:Point>
      <poEs>0.7 0.8 0.8</poEs>
    </hazardCurve>
  </hazardCurves>
  <hazardCurves sourceModelTreePath="b1_b2_b4" gsimTreePath="b1_b4_b5" IMT="PGA"
                investigationTime="30">
    <IMLs>0.05 0.07 0.8</IMLs>
    <hazardCurve>
      <gml:Point>
        <gml:pos>38.0 -20.1</gml:pos>
      </gml:Point>
      <poEs>0.01 0.02 0.03</poEs>
    </hazardCurve>
    <hazardCurve>
      <gml:Point>
        <gml:pos>38.1 -20.2</gml:pos>
      </gml:Point>
      <poEs>0.04 0.05 0.06</poEs>
    </hazardCurve>
    <hazardCurve>
      <gml:Point>
        <gml:pos>38.2 -20.3</gml:pos>
      </gml:Point>
      <poEs>0.07 0.08 0.08</poEs>
    </hazardCurve>
  </hazardCurves>
</nrml>
""")

        metadata1 = dict(
            investigation_time=50, imt='SA', imls=[0.005, 0.007, 0.0098],
            sa_period=0.025, sa_damping=5.0, smlt_path='b1_b2_b4',
            gsimlt_path='b1_b4_b5'
        )

        metadata2 = dict(
            investigation_time=30, imt='PGA', imls=[0.05, 0.07, 0.8],
            smlt_path='b1_b2_b4', gsimlt_path='b1_b4_b5'
        )

        writer = writers.MultiHazardCurveXMLWriter(
            self.path, [metadata1, metadata2])
        writer.serialize([self.data1, self.data2])

        utils.assert_xml_equal(expected, self.path)
        self.assertTrue(utils.validates_against_xml_schema(self.path))


class EventBasedGMFXMLWriterTestCase(unittest.TestCase):

    def test_serialize(self):
        # Test data is:
        # - 1 gmf collection
        # - 3 gmf sets
        # for each set:
        # - 2 ground motion fields
        # for each ground motion field:
        # - 2 nodes
        # Total nodes: 12
        locations = [Location(i * 0.1, i * 0.1) for i in xrange(12)]
        gmf_nodes = [GmfNode(i * 0.2, locations[i]) for i in xrange(12)]
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

        expected = StringIO.StringIO("""\
<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <gmfCollection sourceModelTreePath="b1_b2_b3" gsimTreePath="b1_b7_b15">
    <gmfSet investigationTime="50.0" stochasticEventSetId="1">
      <gmf IMT="SA" saPeriod="0.1" saDamping="5.0" ruptureId="i=1">
        <node gmv="0.0" lon="0.0" lat="0.0"/>
        <node gmv="0.2" lon="0.1" lat="0.1"/>
      </gmf>
      <gmf IMT="SA" saPeriod="0.2" saDamping="5.0" ruptureId="i=2">
        <node gmv="0.4" lon="0.2" lat="0.2"/>
        <node gmv="0.6" lon="0.3" lat="0.3"/>
      </gmf>
    </gmfSet>
    <gmfSet investigationTime="40.0" stochasticEventSetId="2">
      <gmf IMT="SA" saPeriod="0.3" saDamping="5.0" ruptureId="i=3">
        <node gmv="0.8" lon="0.4" lat="0.4"/>
        <node gmv="1.0" lon="0.5" lat="0.5"/>
      </gmf>
      <gmf IMT="PGA" ruptureId="i=4">
        <node gmv="1.2" lon="0.6" lat="0.6"/>
        <node gmv="1.4" lon="0.7" lat="0.7"/>
      </gmf>
    </gmfSet>
    <gmfSet investigationTime="30.0" stochasticEventSetId="3">
      <gmf IMT="PGA" ruptureId="i=5">
        <node gmv="1.6" lon="0.8" lat="0.8"/>
        <node gmv="1.8" lon="0.9" lat="0.9"/>
      </gmf>
      <gmf IMT="PGA" ruptureId="i=6">
        <node gmv="2.0" lon="1.0" lat="1.0"/>
        <node gmv="2.2" lon="1.1" lat="1.1"/>
      </gmf>
    </gmfSet>
  </gmfCollection>
</nrml>
""")

        sm_lt_path = 'b1_b2_b3'
        gsim_lt_path = 'b1_b7_b15'

        try:
            # Make a temp file to save the results to:
            _, path = tempfile.mkstemp()
            writer = writers.EventBasedGMFXMLWriter(
                path, sm_lt_path, gsim_lt_path)
            writer.serialize(gmf_collection)

            utils.assert_xml_equal(expected, path)
            self.assertTrue(utils.validates_against_xml_schema(path))
        finally:
            os.unlink(path)

    def test_serialize_complete_lt_gmf(self):
        # Test data is:
        # - 1 gmf set
        # for each set:
        # - 2 ground motion fields
        # for each ground motion field:
        # - 2 nodes
        # Total nodes: 12
        locations = [Location(i * 0.1, i * 0.1) for i in xrange(12)]
        gmf_nodes = [GmfNode(i * 0.2, locations[i]) for i in xrange(12)]
        gmfs = [
            Gmf('SA', 0.1, 5.0, gmf_nodes[:2], 'i=1'),
            Gmf('SA', 0.2, 5.0, gmf_nodes[2:4], 'i=2'),
            Gmf('SA', 0.3, 5.0, gmf_nodes[4:6], 'i=3'),
            Gmf('PGA', None, None, gmf_nodes[6:8], 'i=4'),
            Gmf('PGA', None, None, gmf_nodes[8:10], 'i=5'),
            Gmf('PGA', None, None, gmf_nodes[10:], 'i=6'),
        ]
        gmf_set = GmfSet(gmfs, 350.0, 1)

        expected = StringIO.StringIO("""\
<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <gmfSet investigationTime="350.0" stochasticEventSetId="1">
    <gmf IMT="SA" saPeriod="0.1" saDamping="5.0" ruptureId="i=1">
      <node gmv="0.0" lon="0.0" lat="0.0"/>
      <node gmv="0.2" lon="0.1" lat="0.1"/>
    </gmf>
    <gmf IMT="SA" saPeriod="0.2" saDamping="5.0" ruptureId="i=2">
      <node gmv="0.4" lon="0.2" lat="0.2"/>
      <node gmv="0.6" lon="0.3" lat="0.3"/>
    </gmf>
    <gmf IMT="SA" saPeriod="0.3" saDamping="5.0" ruptureId="i=3">
      <node gmv="0.8" lon="0.4" lat="0.4"/>
      <node gmv="1.0" lon="0.5" lat="0.5"/>
    </gmf>
    <gmf IMT="PGA" ruptureId="i=4">
      <node gmv="1.2" lon="0.6" lat="0.6"/>
      <node gmv="1.4" lon="0.7" lat="0.7"/>
    </gmf>
    <gmf IMT="PGA" ruptureId="i=5">
      <node gmv="1.6" lon="0.8" lat="0.8"/>
      <node gmv="1.8" lon="0.9" lat="0.9"/>
    </gmf>
    <gmf IMT="PGA" ruptureId="i=6">
      <node gmv="2.0" lon="1.0" lat="1.0"/>
      <node gmv="2.2" lon="1.1" lat="1.1"/>
    </gmf>
  </gmfSet>
</nrml>
""")

        try:
            # Make a temp file to save the results to:
            _, path = tempfile.mkstemp()
            writer = writers.EventBasedGMFXMLWriter(
                path, None, None)
            writer.serialize([gmf_set])

            utils.assert_xml_equal(expected, path)
            self.assertTrue(utils.validates_against_xml_schema(path))
        finally:
            os.unlink(path)


class SESXMLWriterTestCase(unittest.TestCase):

    def test_serialize(self):
        ruptures1 = [
            SESRupture(1,
                       5.5, 1.0, 40.0, 10.0, 'Active Shallow Crust',
                       False, False,
                       top_left_corner=(1.1, 1.01, 10.0),
                       top_right_corner=(2.1, 2.01, 20.0),
                       bottom_right_corner=(3.1, 3.01, 30.0),
                       bottom_left_corner=(4.1, 4.01, 40.0)),
            SESRupture(2,
                       6.5, 0.0, 41.0, 0.0, 'Active Shallow Crust',
                       True, False,
                       lons=[[5.1, 6.1],
                             [7.1, 8.1],
                             ],
                       lats=[[5.01, 6.01],
                             [7.01, 8.01],
                             ],
                       depths=[[10.5, 10.6],
                               [10.7, 10.8],
                               ]),
        ]
        ses1 = SES(1, 50.0, ruptures1)

        ruptures2 = [
            SESRupture(
                3,
                5.4, 2.0, 42.0, 12.0, 'Stable Shallow Crust',
                False, False,
                top_left_corner=(1.1, 1.01, 10.0),
                top_right_corner=(2.1, 2.01, 20.0),
                bottom_left_corner=(4.1, 4.01, 40.0),
                bottom_right_corner=(3.1, 3.01, 30.0)),
            SESRupture(
                4,
                6.4, 3.0, 43.0, 13.0, 'Stable Shallow Crust',
                True, False,
                lons=[
                    [5.2, 6.2],
                    [7.2, 8.2],
                ],
                lats=[
                    [5.02, 6.02],
                    [7.02, 8.02],
                ],
                depths=[
                    [10.1, 10.2],
                    [10.3, 10.4],
                ]),
            SESRupture(
                5,
                7.4, 4.0, 44.0, 14.0, 'Stable Shallow Crust',
                False, True,
                lons = [-1.0, 1.0, -1.0, 1.0, 0.0, 1.1, 0.9, 2.0],
                lats = [1.0, 1.0, -1.0, -1.0, 1.1, 2.0, 0.0, 0.9],
                depths = [21.0, 21.0, 59.0, 59.0, 20.0, 20.0, 80.0, 80.0])
        ]
        ses2 = SES(2, 40.0, ruptures2)

        sm_lt_path = 'b8_b9_b10'
        gsim_lt_path = 'b1_b2_b3'

        expected = StringIO.StringIO("""\
<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <stochasticEventSetCollection sourceModelTreePath="b8_b9_b10" gsimTreePath="b1_b2_b3">
    <stochasticEventSet id="1" investigationTime="50.0">
      <rupture id="TAG" magnitude="5.5" strike="1.0" dip="40.0" rake="10.0" tectonicRegion="Active Shallow Crust">
        <planarSurface>
          <topLeft lon="1.1" lat="1.01" depth="10.0"/>
          <topRight lon="2.1" lat="2.01" depth="20.0"/>
          <bottomLeft lon="4.1" lat="4.01" depth="40.0"/>
          <bottomRight lon="3.1" lat="3.01" depth="30.0"/>
        </planarSurface>
      </rupture>
      <rupture id="TAG" magnitude="6.5" strike="0.0" dip="41.0" rake="0.0" tectonicRegion="Active Shallow Crust">
        <mesh rows="2" cols="2">
          <node row="0" col="0" lon="5.1" lat="5.01" depth="10.5"/>
          <node row="0" col="1" lon="6.1" lat="6.01" depth="10.6"/>
          <node row="1" col="0" lon="7.1" lat="7.01" depth="10.7"/>
          <node row="1" col="1" lon="8.1" lat="8.01" depth="10.8"/>
        </mesh>
      </rupture>
    </stochasticEventSet>
    <stochasticEventSet id="2" investigationTime="40.0">
      <rupture id="TAG" magnitude="5.4" strike="2.0" dip="42.0" rake="12.0" tectonicRegion="Stable Shallow Crust">
        <planarSurface>
          <topLeft lon="1.1" lat="1.01" depth="10.0"/>
          <topRight lon="2.1" lat="2.01" depth="20.0"/>
          <bottomLeft lon="4.1" lat="4.01" depth="40.0"/>
          <bottomRight lon="3.1" lat="3.01" depth="30.0"/>
        </planarSurface>
      </rupture>
      <rupture id="TAG" magnitude="6.4" strike="3.0" dip="43.0" rake="13.0" tectonicRegion="Stable Shallow Crust">
        <mesh rows="2" cols="2">
          <node row="0" col="0" lon="5.2" lat="5.02" depth="10.1"/>
          <node row="0" col="1" lon="6.2" lat="6.02" depth="10.2"/>
          <node row="1" col="0" lon="7.2" lat="7.02" depth="10.3"/>
          <node row="1" col="1" lon="8.2" lat="8.02" depth="10.4"/>
        </mesh>
      </rupture>
      <rupture id="TAG" magnitude="7.4" strike="4.0" dip="44.0" rake="14.0" tectonicRegion="Stable Shallow Crust">
        <planarSurface>
          <topLeft lon="-1.0" lat="1.0" depth="21.0"/>
          <topRight lon="1.0" lat="1.0" depth="21.0"/>
          <bottomLeft lon="-1.0" lat="-1.0" depth="59.0"/>
          <bottomRight lon="1.0" lat="-1.0" depth="59.0"/>
        </planarSurface>
        <planarSurface>
          <topLeft lon="0.0" lat="1.1" depth="20.0"/>
          <topRight lon="1.1" lat="2.0" depth="20.0"/>
          <bottomLeft lon="0.9" lat="0.0" depth="80.0"/>
          <bottomRight lon="2.0" lat="0.9" depth="80.0"/>
        </planarSurface>
      </rupture>
    </stochasticEventSet>
  </stochasticEventSetCollection>
</nrml>
""")

        try:
            _, path = tempfile.mkstemp()
            writer = writers.SESXMLWriter(path, sm_lt_path, gsim_lt_path)
            writer.serialize([ses1, ses2])
            utils.assert_xml_equal(expected, path)
            self.assertTrue(utils.validates_against_xml_schema(path))
        finally:
            os.unlink(path)

    def test_serialize_complete_lt_ses(self):
        ruptures = [
            SESRupture(1,
                       5.5, 1.0, 40.0, 10.0, 'Active Shallow Crust',
                       False, False,
                       top_left_corner=(1.1, 1.01, 10.0),
                       top_right_corner=(2.1, 2.01, 20.0),
                       bottom_right_corner=(3.1, 3.01, 30.0),
                       bottom_left_corner=(4.1, 4.01, 40.0)),
            SESRupture(2,
                       6.5, 0.0, 41.0, 0.0, 'Active Shallow Crust',
                       True, False,
                       lons=[[5.1, 6.1],
                             [7.1, 8.1],
                             ],
                       lats=[[5.01, 6.01],
                             [7.01, 8.01],
                             ],
                       depths=[[10.5, 10.6],
                               [10.7, 10.8],
                               ]),
            SESRupture(3,
                       5.4, 2.0, 42.0, 12.0, 'Stable Shallow Crust',
                       False, False,
                       top_left_corner=(1.1, 1.01, 10.0),
                       top_right_corner=(2.1, 2.01, 20.0),
                       bottom_right_corner=(3.1, 3.01, 30.0),
                       bottom_left_corner=(4.1, 4.01, 40.0)),
            SESRupture(4,
                       6.4, 3.0, 43.0, 13.0, 'Stable Shallow Crust',
                       True, False,
                       lons=[[5.2, 6.2],
                             [7.2, 8.2],
                             ],
                       lats=[[5.02, 6.02],
                             [7.02, 8.02],
                             ],
                       depths=[[10.1, 10.2],
                               [10.3, 10.4],
                               ]),

        ]
        complete_lt_ses = SES(1, 250.0, ruptures)

        expected = StringIO.StringIO("""\
<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <stochasticEventSet id="1" investigationTime="250.0">
    <rupture id="TAG" magnitude="5.5" strike="1.0" dip="40.0" rake="10.0" tectonicRegion="Active Shallow Crust">
      <planarSurface>
        <topLeft lon="1.1" lat="1.01" depth="10.0"/>
        <topRight lon="2.1" lat="2.01" depth="20.0"/>
        <bottomLeft lon="4.1" lat="4.01" depth="40.0"/>
        <bottomRight lon="3.1" lat="3.01" depth="30.0"/>
      </planarSurface>
    </rupture>
    <rupture id="TAG" magnitude="6.5" strike="0.0" dip="41.0" rake="0.0" tectonicRegion="Active Shallow Crust">
      <mesh rows="2" cols="2">
        <node row="0" col="0" lon="5.1" lat="5.01" depth="10.5"/>
        <node row="0" col="1" lon="6.1" lat="6.01" depth="10.6"/>
        <node row="1" col="0" lon="7.1" lat="7.01" depth="10.7"/>
        <node row="1" col="1" lon="8.1" lat="8.01" depth="10.8"/>
      </mesh>
    </rupture>
    <rupture id="TAG" magnitude="5.4" strike="2.0" dip="42.0" rake="12.0" tectonicRegion="Stable Shallow Crust">
      <planarSurface>
        <topLeft lon="1.1" lat="1.01" depth="10.0"/>
        <topRight lon="2.1" lat="2.01" depth="20.0"/>
        <bottomLeft lon="4.1" lat="4.01" depth="40.0"/>
        <bottomRight lon="3.1" lat="3.01" depth="30.0"/>
      </planarSurface>
    </rupture>
    <rupture id="TAG" magnitude="6.4" strike="3.0" dip="43.0" rake="13.0" tectonicRegion="Stable Shallow Crust">
      <mesh rows="2" cols="2">
        <node row="0" col="0" lon="5.2" lat="5.02" depth="10.1"/>
        <node row="0" col="1" lon="6.2" lat="6.02" depth="10.2"/>
        <node row="1" col="0" lon="7.2" lat="7.02" depth="10.3"/>
        <node row="1" col="1" lon="8.2" lat="8.02" depth="10.4"/>
      </mesh>
    </rupture>
  </stochasticEventSet>
</nrml>
""")
        try:
            _, path = tempfile.mkstemp()
            writer = writers.SESXMLWriter(path, None, None)
            writer.serialize([complete_lt_ses])
            utils.assert_xml_equal(expected, path)
            self.assertTrue(utils.validates_against_xml_schema(path))
        finally:
            os.unlink(path)

    def test__create_rupture_mesh_raises_on_empty_mesh(self):
        # When creating the mesh, we should raise a `ValueError` if the mesh is
        # empty.
        rup_elem = etree.Element('test_rup_elem')
        rupture = SESRupture(1,
                             6.5, 0.0, 41.0, 0.0, 'Active Shallow Crust',
                             True, False,
                             lons=[[], []],
                             lats=[[5.01, 6.01],
                                   [7.01, 8.01]],
                             depths=[[10.5, 10.6],
                                     [10.7, 10.8]])

        self.assertRaises(
            ValueError, writers.SESXMLWriter._create_rupture_mesh,
            rupture, rup_elem)


class HazardMapWriterTestCase(unittest.TestCase):

    def setUp(self):
        self.data = [
            (-1.0, 1.0, 0.01),
            (1.0, 1.0, 0.02),
            (1.0, -1.0, 0.03),
            (-1.0, -1.0, 0.04),
        ]

        _, self.path = tempfile.mkstemp()

    def tearDown(self):
        os.unlink(self.path)

    def test_serialize_xml(self):
        expected = StringIO.StringIO("""\
<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <hazardMap sourceModelTreePath="b1_b2_b4" gsimTreePath="b1_b4_b5" IMT="SA" investigationTime="50.0" saPeriod="0.025" saDamping="5.0" poE="0.1">
    <node lon="-1.0" lat="1.0" iml="0.01"/>
    <node lon="1.0" lat="1.0" iml="0.02"/>
    <node lon="1.0" lat="-1.0" iml="0.03"/>
    <node lon="-1.0" lat="-1.0" iml="0.04"/>
  </hazardMap>
</nrml>
""")

        metadata = dict(
            investigation_time=50.0, imt='SA', poe=0.1, sa_period=0.025,
            sa_damping=5.0, smlt_path='b1_b2_b4', gsimlt_path='b1_b4_b5'
        )
        writer = writers.HazardMapXMLWriter(self.path, **metadata)
        writer.serialize(self.data)

        utils.assert_xml_equal(expected, self.path)
        self.assertTrue(utils.validates_against_xml_schema(self.path))

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
        writer = writers.HazardMapGeoJSONWriter(self.path, **metadata)
        writer.serialize(self.data)

        actual = json.load(open(self.path))
        self.assertEqual(expected, actual)

    def test_serialize_quantile_xml(self):
        expected = StringIO.StringIO("""\
<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <hazardMap statistics="quantile" quantileValue="0.85" IMT="SA" investigationTime="50.0" saPeriod="0.025" saDamping="5.0" poE="0.1">
    <node lon="-1.0" lat="1.0" iml="0.01"/>
    <node lon="1.0" lat="1.0" iml="0.02"/>
    <node lon="1.0" lat="-1.0" iml="0.03"/>
    <node lon="-1.0" lat="-1.0" iml="0.04"/>
  </hazardMap>
</nrml>
""")

        metadata = dict(
            investigation_time=50.0, imt='SA', poe=0.1, sa_period=0.025,
            sa_damping=5.0, statistics='quantile', quantile_value=0.85
        )
        writer = writers.HazardMapXMLWriter(self.path, **metadata)
        writer.serialize(self.data)

        utils.assert_xml_equal(expected, self.path)
        self.assertTrue(utils.validates_against_xml_schema(self.path))

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
        writer = writers.HazardMapGeoJSONWriter(self.path, **metadata)
        writer.serialize(self.data)

        actual = json.load(open(self.path))
        self.assertEqual(expected, actual)



class DisaggXMLWriterTestCase(unittest.TestCase):

    def setUp(self):
        self.expected_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  %(metaelem)s
    <disaggMatrix type="Mag" dims="2" poE="0.021" iml="2.129">
      <prob index="0" value="0.0"/>
      <prob index="1" value="0.01"/>
    </disaggMatrix>
    <disaggMatrix type="Dist" dims="3" poE="0.022" iml="2.128">
      <prob index="0" value="0.0"/>
      <prob index="1" value="0.01"/>
      <prob index="2" value="0.02"/>
    </disaggMatrix>
    <disaggMatrix type="TRT" dims="2" poE="0.023" iml="2.127">
      <prob index="0" value="0.0"/>
      <prob index="1" value="0.01"/>
    </disaggMatrix>
    <disaggMatrix type="Mag,Dist" dims="2,3" poE="0.024" iml="2.126">
      <prob index="0,0" value="0.0"/>
      <prob index="0,1" value="0.01"/>
      <prob index="0,2" value="0.02"/>
      <prob index="1,0" value="0.03"/>
      <prob index="1,1" value="0.04"/>
      <prob index="1,2" value="0.05"/>
    </disaggMatrix>
    <disaggMatrix type="Mag,Dist,Eps" dims="2,3,4" poE="0.025" iml="2.125">
      <prob index="0,0,0" value="0.0"/>
      <prob index="0,0,1" value="0.01"/>
      <prob index="0,0,2" value="0.02"/>
      <prob index="0,0,3" value="0.03"/>
      <prob index="0,1,0" value="0.04"/>
      <prob index="0,1,1" value="0.05"/>
      <prob index="0,1,2" value="0.06"/>
      <prob index="0,1,3" value="0.07"/>
      <prob index="0,2,0" value="0.08"/>
      <prob index="0,2,1" value="0.09"/>
      <prob index="0,2,2" value="0.1"/>
      <prob index="0,2,3" value="0.11"/>
      <prob index="1,0,0" value="0.12"/>
      <prob index="1,0,1" value="0.13"/>
      <prob index="1,0,2" value="0.14"/>
      <prob index="1,0,3" value="0.15"/>
      <prob index="1,1,0" value="0.16"/>
      <prob index="1,1,1" value="0.17"/>
      <prob index="1,1,2" value="0.18"/>
      <prob index="1,1,3" value="0.19"/>
      <prob index="1,2,0" value="0.2"/>
      <prob index="1,2,1" value="0.21"/>
      <prob index="1,2,2" value="0.22"/>
      <prob index="1,2,3" value="0.23"/>
    </disaggMatrix>
    <disaggMatrix type="Lon,Lat" dims="5,5" poE="0.026" iml="2.124">
      <prob index="0,0" value="0.0"/>
      <prob index="0,1" value="0.01"/>
      <prob index="0,2" value="0.02"/>
      <prob index="0,3" value="0.03"/>
      <prob index="0,4" value="0.04"/>
      <prob index="1,0" value="0.05"/>
      <prob index="1,1" value="0.06"/>
      <prob index="1,2" value="0.07"/>
      <prob index="1,3" value="0.08"/>
      <prob index="1,4" value="0.09"/>
      <prob index="2,0" value="0.1"/>
      <prob index="2,1" value="0.11"/>
      <prob index="2,2" value="0.12"/>
      <prob index="2,3" value="0.13"/>
      <prob index="2,4" value="0.14"/>
      <prob index="3,0" value="0.15"/>
      <prob index="3,1" value="0.16"/>
      <prob index="3,2" value="0.17"/>
      <prob index="3,3" value="0.18"/>
      <prob index="3,4" value="0.19"/>
      <prob index="4,0" value="0.2"/>
      <prob index="4,1" value="0.21"/>
      <prob index="4,2" value="0.22"/>
      <prob index="4,3" value="0.23"/>
      <prob index="4,4" value="0.24"/>
    </disaggMatrix>
    <disaggMatrix type="Mag,Lon,Lat" dims="2,5,5" poE="0.027" iml="2.123">
      <prob index="0,0,0" value="0.0"/>
      <prob index="0,0,1" value="0.01"/>
      <prob index="0,0,2" value="0.02"/>
      <prob index="0,0,3" value="0.03"/>
      <prob index="0,0,4" value="0.04"/>
      <prob index="0,1,0" value="0.05"/>
      <prob index="0,1,1" value="0.06"/>
      <prob index="0,1,2" value="0.07"/>
      <prob index="0,1,3" value="0.08"/>
      <prob index="0,1,4" value="0.09"/>
      <prob index="0,2,0" value="0.1"/>
      <prob index="0,2,1" value="0.11"/>
      <prob index="0,2,2" value="0.12"/>
      <prob index="0,2,3" value="0.13"/>
      <prob index="0,2,4" value="0.14"/>
      <prob index="0,3,0" value="0.15"/>
      <prob index="0,3,1" value="0.16"/>
      <prob index="0,3,2" value="0.17"/>
      <prob index="0,3,3" value="0.18"/>
      <prob index="0,3,4" value="0.19"/>
      <prob index="0,4,0" value="0.2"/>
      <prob index="0,4,1" value="0.21"/>
      <prob index="0,4,2" value="0.22"/>
      <prob index="0,4,3" value="0.23"/>
      <prob index="0,4,4" value="0.24"/>
      <prob index="1,0,0" value="0.25"/>
      <prob index="1,0,1" value="0.26"/>
      <prob index="1,0,2" value="0.27"/>
      <prob index="1,0,3" value="0.28"/>
      <prob index="1,0,4" value="0.29"/>
      <prob index="1,1,0" value="0.3"/>
      <prob index="1,1,1" value="0.31"/>
      <prob index="1,1,2" value="0.32"/>
      <prob index="1,1,3" value="0.33"/>
      <prob index="1,1,4" value="0.34"/>
      <prob index="1,2,0" value="0.35"/>
      <prob index="1,2,1" value="0.36"/>
      <prob index="1,2,2" value="0.37"/>
      <prob index="1,2,3" value="0.38"/>
      <prob index="1,2,4" value="0.39"/>
      <prob index="1,3,0" value="0.4"/>
      <prob index="1,3,1" value="0.41"/>
      <prob index="1,3,2" value="0.42"/>
      <prob index="1,3,3" value="0.43"/>
      <prob index="1,3,4" value="0.44"/>
      <prob index="1,4,0" value="0.45"/>
      <prob index="1,4,1" value="0.46"/>
      <prob index="1,4,2" value="0.47"/>
      <prob index="1,4,3" value="0.48"/>
      <prob index="1,4,4" value="0.49"/>
    </disaggMatrix>
    <disaggMatrix type="Lon,Lat,TRT" dims="5,5,2" poE="0.028" iml="2.122">
      <prob index="0,0,0" value="0.0"/>
      <prob index="0,0,1" value="0.01"/>
      <prob index="0,1,0" value="0.02"/>
      <prob index="0,1,1" value="0.03"/>
      <prob index="0,2,0" value="0.04"/>
      <prob index="0,2,1" value="0.05"/>
      <prob index="0,3,0" value="0.06"/>
      <prob index="0,3,1" value="0.07"/>
      <prob index="0,4,0" value="0.08"/>
      <prob index="0,4,1" value="0.09"/>
      <prob index="1,0,0" value="0.1"/>
      <prob index="1,0,1" value="0.11"/>
      <prob index="1,1,0" value="0.12"/>
      <prob index="1,1,1" value="0.13"/>
      <prob index="1,2,0" value="0.14"/>
      <prob index="1,2,1" value="0.15"/>
      <prob index="1,3,0" value="0.16"/>
      <prob index="1,3,1" value="0.17"/>
      <prob index="1,4,0" value="0.18"/>
      <prob index="1,4,1" value="0.19"/>
      <prob index="2,0,0" value="0.2"/>
      <prob index="2,0,1" value="0.21"/>
      <prob index="2,1,0" value="0.22"/>
      <prob index="2,1,1" value="0.23"/>
      <prob index="2,2,0" value="0.24"/>
      <prob index="2,2,1" value="0.25"/>
      <prob index="2,3,0" value="0.26"/>
      <prob index="2,3,1" value="0.27"/>
      <prob index="2,4,0" value="0.28"/>
      <prob index="2,4,1" value="0.29"/>
      <prob index="3,0,0" value="0.3"/>
      <prob index="3,0,1" value="0.31"/>
      <prob index="3,1,0" value="0.32"/>
      <prob index="3,1,1" value="0.33"/>
      <prob index="3,2,0" value="0.34"/>
      <prob index="3,2,1" value="0.35"/>
      <prob index="3,3,0" value="0.36"/>
      <prob index="3,3,1" value="0.37"/>
      <prob index="3,4,0" value="0.38"/>
      <prob index="3,4,1" value="0.39"/>
      <prob index="4,0,0" value="0.4"/>
      <prob index="4,0,1" value="0.41"/>
      <prob index="4,1,0" value="0.42"/>
      <prob index="4,1,1" value="0.43"/>
      <prob index="4,2,0" value="0.44"/>
      <prob index="4,2,1" value="0.45"/>
      <prob index="4,3,0" value="0.46"/>
      <prob index="4,3,1" value="0.47"/>
      <prob index="4,4,0" value="0.48"/>
      <prob index="4,4,1" value="0.49"/>
    </disaggMatrix>
  </disaggMatrices>
</nrml>
"""
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
        _, self.path = tempfile.mkstemp()

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

    def tearDown(self):
        os.unlink(self.path)

    def test_serialize(self):
        metaelem = (
            '<disaggMatrices sourceModelTreePath="b1_b2_b3" '
            'gsimTreePath="b1_b7_b15" IMT="SA" investigationTime="50.0" '
            'saPeriod="0.1" saDamping="5.0" lon="8.33" lat="47.22" '
            'magBinEdges="5, 6" distBinEdges="0, 20, 40" '
            'lonBinEdges="6, 7, 8, 9, 10" latBinEdges="46, 47, 48, 49, 50" '
            'epsBinEdges="-0.5, 0.5, 1.5, 2.5" '
            'tectonicRegionTypes="active shallow crust, stable continental">'
        )
        self.expected_xml %= dict(metaelem=metaelem)

        writer = writers.DisaggXMLWriter(self.path, **self.metadata)
        writer.serialize(self.data)

        expected = StringIO.StringIO(self.expected_xml)
        utils.assert_xml_equal(expected, self.path)
        self.assertTrue(utils.validates_against_xml_schema(self.path))


class ScenarioGMFXMLWriterTestCase(unittest.TestCase):

    def test_serialize(self):
        locations = [Location(i * 0.1, i * 0.1) for i in xrange(12)]
        gmf_nodes = [GmfNode(i * 0.2, locations[i])
                     for i in xrange(12)]
        gmfs = [
            Gmf('SA', 0.1, 5.0, gmf_nodes[:2]),
            Gmf('SA', 0.2, 5.0, gmf_nodes[2:4]),
            Gmf('SA', 0.3, 5.0, gmf_nodes[4:6]),
            Gmf('PGA', None, None, gmf_nodes[6:8]),
            Gmf('PGA', None, None, gmf_nodes[8:10]),
            Gmf('PGA', None, None, gmf_nodes[10:]),
        ]

        expected = StringIO.StringIO("""\
<?xml version="1.0" encoding="utf-8"?>
<nrml
xmlns="http://openquake.org/xmlns/nrml/0.4"
xmlns:gml="http://www.opengis.net/gml"
>
    <gmfSet>
        <gmf
        IMT="SA"
        saDamping="5.0"
        saPeriod="0.1"
        >
            <node gmv="0.0" lat="0.0" lon="0.0"/>
            <node gmv="0.2" lat="0.1" lon="0.1"/>
        </gmf>
        <gmf
        IMT="SA"
        saDamping="5.0"
        saPeriod="0.2"
        >
            <node gmv="0.4" lat="0.2" lon="0.2"/>
            <node gmv="0.6" lat="0.3" lon="0.3"/>
        </gmf>
        <gmf
        IMT="SA"
        saDamping="5.0"
        saPeriod="0.3"
        >
            <node gmv="0.8" lat="0.4" lon="0.4"/>
            <node gmv="1.0" lat="0.5" lon="0.5"/>
        </gmf>
        <gmf
        IMT="PGA"
        >
            <node gmv="1.2" lat="0.6" lon="0.6"/>
            <node gmv="1.4" lat="0.7" lon="0.7"/>
        </gmf>
        <gmf
        IMT="PGA"
        >
            <node gmv="1.6" lat="0.8" lon="0.8"/>
            <node gmv="1.8" lat="0.9" lon="0.9"/>
        </gmf>
        <gmf
        IMT="PGA"
        >
            <node gmv="2.0" lat="1.0" lon="1.0"/>
            <node gmv="2.2" lat="1.1" lon="1.1"/>
        </gmf>
    </gmfSet>
</nrml>
""")
        try:
            # Make a temp file to save the results to:
            _, path = tempfile.mkstemp()
            writer = writers.ScenarioGMFXMLWriter(path)
            writer.serialize(gmfs)
            utils.assert_xml_equal(expected, path)
            self.assertTrue(utils.validates_against_xml_schema(path))
        finally:
            os.unlink(path)


class UHSXMLWriterTestCase(unittest.TestCase):

    TIME = 50.0
    POE = 0.1
    FAKE_PATH = 'fake'

    @classmethod
    def setUpClass(cls):
        cls.expected_xml = StringIO.StringIO("""\
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
        cls.expected_mean_xml = StringIO.StringIO("""\
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
        cls.expected_quantile_xml = StringIO.StringIO("""\
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
        try:
            _, path = tempfile.mkstemp()
            writer = writers.UHSXMLWriter(path, **self.metadata)

            writer.serialize(self.data)

            utils.assert_xml_equal(self.expected_xml, path)
        finally:
            os.unlink(path)

    def test_serialize_mean(self):
        del self.metadata['smlt_path']
        del self.metadata['gsimlt_path']
        self.metadata['statistics'] = 'mean'

        try:
            _, path = tempfile.mkstemp()
            writer = writers.UHSXMLWriter(path, **self.metadata)

            writer.serialize(self.data)

            utils.assert_xml_equal(self.expected_mean_xml, path)
        finally:
            os.unlink(path)

    def test_serialize_quantile(self):
        del self.metadata['smlt_path']
        del self.metadata['gsimlt_path']
        self.metadata['statistics'] = 'quantile'
        self.metadata['quantile_value'] = 0.95

        try:
            _, path = tempfile.mkstemp()
            writer = writers.UHSXMLWriter(path, **self.metadata)

            writer.serialize(self.data)

            utils.assert_xml_equal(self.expected_quantile_xml, path)
        finally:
            os.unlink(path)


class SourceModelXMLWriterTestCase(unittest.TestCase):

    def test_serialize(self):
        # Parse an XML model into a source model object, re-serialize using the
        # SourceModelXMLWriter, and compare the new file with the original.
        test_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <sourceModel name="Some Source Model">
    <areaSource id="1" name="Quito" tectonicRegion="Active Shallow Crust">
      <areaGeometry>
        <gml:Polygon>
          <gml:exterior>
            <gml:LinearRing>
              <gml:posList>-122.5 37.5 -121.5 37.5 -121.5 38.5 -122.5 38.5</gml:posList>
            </gml:LinearRing>
          </gml:exterior>
        </gml:Polygon>
        <upperSeismoDepth>0.0</upperSeismoDepth>
        <lowerSeismoDepth>10.0</lowerSeismoDepth>
      </areaGeometry>
      <magScaleRel>PeerMSR</magScaleRel>
      <ruptAspectRatio>1.5</ruptAspectRatio>
      <incrementalMFD minMag="6.55" binWidth="0.1">
        <occurRates>0.0010614989 0.00088291627 0.00073437777 0.0006108288 0.0005080653</occurRates>
      </incrementalMFD>
      <nodalPlaneDist>
        <nodalPlane probability="0.3" strike="0.0" dip="90.0" rake="0.0"/>
        <nodalPlane probability="0.7" strike="90.0" dip="45.0" rake="90.0"/>
      </nodalPlaneDist>
      <hypoDepthDist>
        <hypoDepth probability="0.5" depth="4.0"/>
        <hypoDepth probability="0.5" depth="8.0"/>
      </hypoDepthDist>
    </areaSource>
    <pointSource id="2" name="point" tectonicRegion="Stable Continental Crust">
      <pointGeometry>
        <gml:Point>
          <gml:pos>-122.0 38.0</gml:pos>
        </gml:Point>
        <upperSeismoDepth>0.0</upperSeismoDepth>
        <lowerSeismoDepth>10.0</lowerSeismoDepth>
      </pointGeometry>
      <magScaleRel>WC1994</magScaleRel>
      <ruptAspectRatio>0.5</ruptAspectRatio>
      <truncGutenbergRichterMFD aValue="-3.5" bValue="1.0" minMag="5.0" maxMag="6.5"/>
      <nodalPlaneDist>
        <nodalPlane probability="0.3" strike="0.0" dip="90.0" rake="0.0"/>
        <nodalPlane probability="0.7" strike="90.0" dip="45.0" rake="90.0"/>
      </nodalPlaneDist>
      <hypoDepthDist>
        <hypoDepth probability="0.5" depth="4.0"/>
        <hypoDepth probability="0.5" depth="8.0"/>
      </hypoDepthDist>
    </pointSource>
    <simpleFaultSource id="3" name="Mount Diablo Thrust" tectonicRegion="Active Shallow Crust">
      <simpleFaultGeometry>
        <gml:LineString>
          <gml:posList>-121.8229 37.7301 -122.0388 37.8771</gml:posList>
        </gml:LineString>
        <dip>45.0</dip>
        <upperSeismoDepth>10.0</upperSeismoDepth>
        <lowerSeismoDepth>20.0</lowerSeismoDepth>
      </simpleFaultGeometry>
      <magScaleRel>WC1994</magScaleRel>
      <ruptAspectRatio>1.5</ruptAspectRatio>
      <incrementalMFD minMag="5.0" binWidth="0.1">
        <occurRates>0.0010614989 0.00088291627 0.00073437777 0.0006108288 0.0005080653</occurRates>
      </incrementalMFD>
      <rake>30.0</rake>
    </simpleFaultSource>
    <complexFaultSource id="4" name="Cascadia Megathrust" tectonicRegion="Subduction Interface">
      <complexFaultGeometry>
        <faultTopEdge>
          <gml:LineString>
            <gml:posList>-124.704 40.363 5.49326 -124.977 41.214 4.98856 -125.14 42.096 4.89734</gml:posList>
          </gml:LineString>
        </faultTopEdge>
        <intermediateEdge>
          <gml:LineString>
            <gml:posList>-124.704 40.363 5.59326 -124.977 41.214 5.08856 -125.14 42.096 4.99734</gml:posList>
          </gml:LineString>
        </intermediateEdge>
        <intermediateEdge>
          <gml:LineString>
            <gml:posList>-124.704 40.363 5.69326 -124.977 41.214 5.18856 -125.14 42.096 5.09734</gml:posList>
          </gml:LineString>
        </intermediateEdge>
        <faultBottomEdge>
          <gml:LineString>
            <gml:posList>-123.829 40.347 20.3849 -124.137 41.218 17.4139 -124.252 42.115 17.5274</gml:posList>
          </gml:LineString>
        </faultBottomEdge>
      </complexFaultGeometry>
      <magScaleRel>WC1994</magScaleRel>
      <ruptAspectRatio>2.0</ruptAspectRatio>
      <truncGutenbergRichterMFD aValue="-3.5" bValue="1.0" minMag="5.0" maxMag="6.5"/>
      <rake>30.0</rake>
    </complexFaultSource>
    <characteristicFaultSource id="5" name="characteristic source, simple fault" tectonicRegion="Volcanic">
      <truncGutenbergRichterMFD aValue="-3.5" bValue="1.0" minMag="5.0" maxMag="6.5"/>
      <rake>30.0</rake>
      <surface>
        <simpleFaultGeometry>
          <gml:LineString>
            <gml:posList>-121.8229 37.7301 -122.0388 37.8771</gml:posList>
          </gml:LineString>
          <dip>45.0</dip>
          <upperSeismoDepth>10.0</upperSeismoDepth>
          <lowerSeismoDepth>20.0</lowerSeismoDepth>
        </simpleFaultGeometry>
      </surface>
    </characteristicFaultSource>
    <characteristicFaultSource id="6" name="characteristic source, complex fault" tectonicRegion="Volcanic">
      <incrementalMFD minMag="5.0" binWidth="0.1">
        <occurRates>0.0010614989 0.00088291627 0.00073437777 0.0006108288 0.0005080653</occurRates>
      </incrementalMFD>
      <rake>60.0</rake>
      <surface>
        <complexFaultGeometry>
          <faultTopEdge>
            <gml:LineString>
              <gml:posList>-124.704 40.363 5.49326 -124.977 41.214 4.98856 -125.14 42.096 4.89734</gml:posList>
            </gml:LineString>
          </faultTopEdge>
          <intermediateEdge>
            <gml:LineString>
              <gml:posList>-124.704 40.363 5.59326 -124.977 41.214 5.08856 -125.14 42.096 4.99734</gml:posList>
            </gml:LineString>
          </intermediateEdge>
          <intermediateEdge>
            <gml:LineString>
              <gml:posList>-124.704 40.363 5.69326 -124.977 41.214 5.18856 -125.14 42.096 5.09734</gml:posList>
            </gml:LineString>
          </intermediateEdge>
          <faultBottomEdge>
            <gml:LineString>
              <gml:posList>-123.829 40.347 20.3849 -124.137 41.218 17.4139 -124.252 42.115 17.5274</gml:posList>
            </gml:LineString>
          </faultBottomEdge>
        </complexFaultGeometry>
      </surface>
    </characteristicFaultSource>
    <characteristicFaultSource id="7" name="characteristic source, multi surface" tectonicRegion="Volcanic">
      <truncGutenbergRichterMFD aValue="-3.6" bValue="1.0" minMag="5.2" maxMag="6.4"/>
      <rake>90.0</rake>
      <surface>
        <planarSurface strike="0.0" dip="90.0">
          <topLeft lon="-1.0" lat="1.0" depth="21.0"/>
          <topRight lon="1.0" lat="1.0" depth="21.0"/>
          <bottomLeft lon="-1.0" lat="-1.0" depth="59.0"/>
          <bottomRight lon="1.0" lat="-1.0" depth="59.0"/>
        </planarSurface>
        <planarSurface strike="20.0" dip="45.0">
          <topLeft lon="1.0" lat="1.0" depth="20.0"/>
          <topRight lon="3.0" lat="1.0" depth="20.0"/>
          <bottomLeft lon="1.0" lat="-1.0" depth="80.0"/>
          <bottomRight lon="3.0" lat="-1.0" depth="80.0"/>
        </planarSurface>
      </surface>
    </characteristicFaultSource>
  </sourceModel>
</nrml>"""

        parser = parsers.SourceModelParser(StringIO.StringIO(test_xml))
        source_model = parser.parse()

        _, path = tempfile.mkstemp()
        try:
            writer = writers.SourceModelXMLWriter(path)
            writer.serialize(source_model)

            utils.assert_xml_equal(StringIO.StringIO(test_xml), path)
        finally:
            # cleanup temp files
            os.unlink(path)
