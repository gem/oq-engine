# Copyright (c) 2010-2012, GEM Foundation.
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


import os
import StringIO
import tempfile
import unittest

from collections import namedtuple

from lxml import etree

from nrml import writers

HazardCurveData = namedtuple('HazardCurveData', 'location, poes')
Location = namedtuple('Location', 'x, y')
GmfNode = namedtuple('GmfNode', 'iml, location')


class GmfCollection(object):

    def __init__(self, gmf_sets):
        self.gmf_sets = gmf_sets

    def __iter__(self):
        return iter(self.gmf_sets)


class GmfSet(object):

    def __init__(self, gmfs, investigation_time):
        self.gmfs = gmfs
        self.investigation_time = investigation_time

    def __iter__(self):
        return iter(self.gmfs)


class Gmf(object):

    def __init__(self, imt, sa_period, sa_damping, gmf_nodes):
        self.imt = imt
        self.sa_period = sa_period
        self.sa_damping = sa_damping
        self.gmf_nodes = gmf_nodes

    def __iter__(self):
        return iter(self.gmf_nodes)


class SES(object):

    def __init__(self, investigation_time, ruptures):
        self.investigation_time = investigation_time
        self.ruptures = ruptures

    def __iter__(self):
        return iter(self.ruptures)


class SESRupture(object):

    def __init__(self, magnitude, strike, dip, rake, tectonic_region_type,
                 is_from_fault_source, lons=None, lats=None, depths=None,
                 top_left_corner=None, top_right_corner=None,
                 bottom_right_corner=None, bottom_left_corner=None):
        self.magnitude = magnitude
        self.strike = strike
        self.dip = dip
        self.rake = rake
        self.tectonic_region_type = tectonic_region_type
        self.is_from_fault_source = is_from_fault_source
        self.lons = lons
        self.lats = lats
        self.depths = depths
        self.top_left_corner = top_left_corner
        self.top_right_corner = top_right_corner
        self.bottom_right_corner = bottom_right_corner
        self.bottom_left_corner = bottom_left_corner


class HazardCurveXMLWriterTestCase(unittest.TestCase):

    FAKE_PATH = 'TODO'  # use a place in /tmp
    TIME = 50.0
    IMLS = [0.005, 0.007, 0.0098]

    def test_validate_metadata_stats_and_smlt_path(self):
        # statistics + smlt path
        metadata = dict(statistics='mean', smlt_path='foo')
        writer = writers.HazardCurveXMLWriter(
            self.FAKE_PATH, self.TIME, 'PGA', self.IMLS, **metadata)
        self.assertRaises(ValueError, writer.validate_metadata)

    def test_validate_metadata_stats_and_gsimlt_path(self):
        # statistics + gsimlt path
        metadata = dict(statistics='mean', gsimlt_path='foo')
        writer = writers.HazardCurveXMLWriter(
            self.FAKE_PATH, self.TIME, 'PGA', self.IMLS, **metadata)
        self.assertRaises(ValueError, writer.validate_metadata)

    def test_validate_metadata_only_smlt_path(self):
        # only 1 logic tree path specified
        metadata = dict(smlt_path='foo')
        writer = writers.HazardCurveXMLWriter(
            self.FAKE_PATH, self.TIME, 'PGA', self.IMLS, **metadata)
        self.assertRaises(ValueError, writer.validate_metadata)

    def test_validate_metadata_only_gsimlt_path(self):
        # only 1 logic tree path specified
        metadata = dict(gsimlt_path='foo')
        writer = writers.HazardCurveXMLWriter(
            self.FAKE_PATH, self.TIME, 'PGA', self.IMLS, **metadata)
        self.assertRaises(ValueError, writer.validate_metadata)

    def test_validate_metadata_invalid_stats(self):
        # invalid stats type
        metadata = dict(statistics='invalid')
        writer = writers.HazardCurveXMLWriter(
            self.FAKE_PATH, self.TIME, 'PGA', self.IMLS, **metadata)
        self.assertRaises(ValueError, writer.validate_metadata)

    def test_validate_metadata_quantile_stats_with_no_value(self):
        # quantile statistics with no quantile value
        metadata = dict(statistics='quantile')
        writer = writers.HazardCurveXMLWriter(
            self.FAKE_PATH, self.TIME, 'PGA', self.IMLS, **metadata)
        self.assertRaises(ValueError, writer.validate_metadata)

    def test_validate_metadata_sa_with_no_period(self):
        # damping but no sa period
        metadata = dict(statistics='mean', sa_damping=5.0)
        writer = writers.HazardCurveXMLWriter(
            self.FAKE_PATH, self.TIME, 'SA', self.IMLS, **metadata)
        self.assertRaises(ValueError, writer.validate_metadata)

    def test_validate_metadata_sa_with_no_damping(self):
        # sa period but no damping
        metadata = dict(statistics='mean', sa_period=5.0)
        writer = writers.HazardCurveXMLWriter(
            self.FAKE_PATH, self.TIME, 'SA', self.IMLS, **metadata)
        self.assertRaises(ValueError, writer.validate_metadata)

    def test_validate_metadata_mean_stats_with_quantile_value(self):
        metadata = dict(statistics='mean', quantile_value=5.0)
        writer = writers.HazardCurveXMLWriter(
            self.FAKE_PATH, self.TIME, 'PGA', self.IMLS, **metadata)
        self.assertRaises(ValueError, writer.validate_metadata)

    def test_validate_metadata_no_stats_with_quantile_value(self):
        metadata = dict(quantile_value=5.0)
        writer = writers.HazardCurveXMLWriter(
            self.FAKE_PATH, self.TIME, 'PGA', self.IMLS, **metadata)
        self.assertRaises(ValueError, writer.validate_metadata)

    def test_serialize(self):
        # Just a basic serialization test.
        expected = StringIO.StringIO("""\
<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <hazardCurves IMT="SA" investigationTime="50.0" sourceModelTreePath="b1_b2_b4" gsimTreePath="b1_b4_b5" saPeriod="0.025" saDamping="5.0">
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

        data = [
            HazardCurveData(location=Location(38.0, -20.1),
                            poes=[0.1, 0.2, 0.3]),
            HazardCurveData(location=Location(38.1, -20.2),
                            poes=[0.4, 0.5, 0.6]),
            HazardCurveData(location=Location(38.2, -20.3),
                            poes=[0.7, 0.8, 0.8]),
        ]

        try:
            _, path = tempfile.mkstemp()
            metadata = dict(
                sa_period=0.025, sa_damping=5.0, smlt_path='b1_b2_b4',
                gsimlt_path='b1_b4_b5')
            writer = writers.HazardCurveXMLWriter(
                path, self.TIME, 'SA', self.IMLS, **metadata)
            writer.serialize(data)

            expected_text = expected.readlines()
            fh = open(path, 'r')
            text = fh.readlines()
            self.assertEqual(expected_text, text)
        finally:
            os.unlink(path)


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
            Gmf('SA', 0.1, 5.0, gmf_nodes[:2]),
            Gmf('SA', 0.2, 5.0, gmf_nodes[2:4]),
            Gmf('SA', 0.3, 5.0, gmf_nodes[4:6]),
            Gmf('PGA', None, None, gmf_nodes[6:8]),
            Gmf('PGA', None, None, gmf_nodes[8:10]),
            Gmf('PGA', None, None, gmf_nodes[10:]),
        ]
        gmf_sets = [
            GmfSet(gmfs[:2], 50.0),
            GmfSet(gmfs[2:4], 40.0),
            GmfSet(gmfs[4:], 30.0),
        ]
        gmf_collection = GmfCollection(gmf_sets)

        expected = StringIO.StringIO("""\
<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <gmfCollection sourceModelTreePath="b1_b2_b3" gsimTreePath="b1_b7_b15">
    <gmfSet investigationTime="50.0">
      <gmf IMT="SA" saPeriod="0.1" saDamping="5.0">
        <node iml="0.0" lon="0.0" lat="0.0"/>
        <node iml="0.2" lon="0.1" lat="0.1"/>
      </gmf>
      <gmf IMT="SA" saPeriod="0.2" saDamping="5.0">
        <node iml="0.4" lon="0.2" lat="0.2"/>
        <node iml="0.6" lon="0.3" lat="0.3"/>
      </gmf>
    </gmfSet>
    <gmfSet investigationTime="40.0">
      <gmf IMT="SA" saPeriod="0.3" saDamping="5.0">
        <node iml="0.8" lon="0.4" lat="0.4"/>
        <node iml="1.0" lon="0.5" lat="0.5"/>
      </gmf>
      <gmf IMT="PGA">
        <node iml="1.2" lon="0.6" lat="0.6"/>
        <node iml="1.4" lon="0.7" lat="0.7"/>
      </gmf>
    </gmfSet>
    <gmfSet investigationTime="30.0">
      <gmf IMT="PGA">
        <node iml="1.6" lon="0.8" lat="0.8"/>
        <node iml="1.8" lon="0.9" lat="0.9"/>
      </gmf>
      <gmf IMT="PGA">
        <node iml="2.0" lon="1.0" lat="1.0"/>
        <node iml="2.2" lon="1.1" lat="1.1"/>
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

            expected_text = expected.readlines()
            fh = open(path, 'r')
            text = fh.readlines()
            self.assertEqual(expected_text, text)
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
            Gmf('SA', 0.1, 5.0, gmf_nodes[:2]),
            Gmf('SA', 0.2, 5.0, gmf_nodes[2:4]),
            Gmf('SA', 0.3, 5.0, gmf_nodes[4:6]),
            Gmf('PGA', None, None, gmf_nodes[6:8]),
            Gmf('PGA', None, None, gmf_nodes[8:10]),
            Gmf('PGA', None, None, gmf_nodes[10:]),
        ]
        gmf_set = GmfSet(gmfs, 350.0)

        expected = StringIO.StringIO("""\
<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <gmfSet investigationTime="350.0">
    <gmf IMT="SA" saPeriod="0.1" saDamping="5.0">
      <node iml="0.0" lon="0.0" lat="0.0"/>
      <node iml="0.2" lon="0.1" lat="0.1"/>
    </gmf>
    <gmf IMT="SA" saPeriod="0.2" saDamping="5.0">
      <node iml="0.4" lon="0.2" lat="0.2"/>
      <node iml="0.6" lon="0.3" lat="0.3"/>
    </gmf>
    <gmf IMT="SA" saPeriod="0.3" saDamping="5.0">
      <node iml="0.8" lon="0.4" lat="0.4"/>
      <node iml="1.0" lon="0.5" lat="0.5"/>
    </gmf>
    <gmf IMT="PGA">
      <node iml="1.2" lon="0.6" lat="0.6"/>
      <node iml="1.4" lon="0.7" lat="0.7"/>
    </gmf>
    <gmf IMT="PGA">
      <node iml="1.6" lon="0.8" lat="0.8"/>
      <node iml="1.8" lon="0.9" lat="0.9"/>
    </gmf>
    <gmf IMT="PGA">
      <node iml="2.0" lon="1.0" lat="1.0"/>
      <node iml="2.2" lon="1.1" lat="1.1"/>
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

            expected_text = expected.readlines()
            fh = open(path, 'r')
            text = fh.readlines()
            self.assertEqual(expected_text, text)
        finally:
            os.unlink(path)



class SESXMLWriterTestCase(unittest.TestCase):

    def test_serialize(self):
        ruptures1 = [
            SESRupture(
                5.5, 1.0, 40.0, 10.0, 'Active Shallow Crust', False,
                top_left_corner=(1.1, 1.01, 10.0),
                top_right_corner=(2.1, 2.01, 20.0),
                bottom_right_corner=(3.1, 3.01, 30.0),
                bottom_left_corner=(4.1, 4.01, 40.0)),
            SESRupture(
                6.5, 0.0, 41.0, 0.0, 'Active Shallow Crust', True,
                lons=[
                    [5.1, 6.1],
                    [7.1, 8.1],
                ],
                lats=[
                    [5.01, 6.01],
                    [7.01, 8.01],
                ],
                depths=[
                    [10.5, 10.6],
                    [10.7, 10.8],
                ]),
        ]
        ses1 = SES(50.0, ruptures1)

        ruptures2 = [
            SESRupture(
                5.4, 2.0, 42.0, 12.0, 'Stable Shallow Crust', False,
                top_left_corner=(1.1, 1.01, 10.0),
                top_right_corner=(2.1, 2.01, 20.0),
                bottom_right_corner=(3.1, 3.01, 30.0),
                bottom_left_corner=(4.1, 4.01, 40.0)),
            SESRupture(
                6.4, 3.0, 43.0, 13.0, 'Stable Shallow Crust', True,
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
        ]
        ses2 = SES(40.0, ruptures2)

        sm_lt_path = 'b8_b9_b10'
        gsim_lt_path = 'b1_b2_b3'

        expected = StringIO.StringIO("""\
<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <stochasticEventSetCollection sourceModelTreePath="b8_b9_b10" gsimTreePath="b1_b2_b3">
    <stochasticEventSet investigationTime="50.0">
      <rupture magnitude="5.5" strike="1.0" dip="40.0" rake="10.0" tectonicRegion="Active Shallow Crust">
        <planarSurface>
          <topLeft lon="1.1" lat="1.01" depths="10.0"/>
          <topRight lon="2.1" lat="2.01" depths="20.0"/>
          <bottomRight lon="3.1" lat="3.01" depths="30.0"/>
          <bottomLeft lon="4.1" lat="4.01" depths="40.0"/>
        </planarSurface>
      </rupture>
      <rupture magnitude="6.5" strike="0.0" dip="41.0" rake="0.0" tectonicRegion="Active Shallow Crust">
        <mesh rows="2" cols="2">
          <node row="0" col="0" lon="5.1" lat="5.01" depth="10.5"/>
          <node row="0" col="1" lon="6.1" lat="6.01" depth="10.6"/>
          <node row="1" col="0" lon="7.1" lat="7.01" depth="10.7"/>
          <node row="1" col="1" lon="8.1" lat="8.01" depth="10.8"/>
        </mesh>
      </rupture>
    </stochasticEventSet>
    <stochasticEventSet investigationTime="40.0">
      <rupture magnitude="5.4" strike="2.0" dip="42.0" rake="12.0" tectonicRegion="Stable Shallow Crust">
        <planarSurface>
          <topLeft lon="1.1" lat="1.01" depths="10.0"/>
          <topRight lon="2.1" lat="2.01" depths="20.0"/>
          <bottomRight lon="3.1" lat="3.01" depths="30.0"/>
          <bottomLeft lon="4.1" lat="4.01" depths="40.0"/>
        </planarSurface>
      </rupture>
      <rupture magnitude="6.4" strike="3.0" dip="43.0" rake="13.0" tectonicRegion="Stable Shallow Crust">
        <mesh rows="2" cols="2">
          <node row="0" col="0" lon="5.2" lat="5.02" depth="10.1"/>
          <node row="0" col="1" lon="6.2" lat="6.02" depth="10.2"/>
          <node row="1" col="0" lon="7.2" lat="7.02" depth="10.3"/>
          <node row="1" col="1" lon="8.2" lat="8.02" depth="10.4"/>
        </mesh>
      </rupture>
    </stochasticEventSet>
  </stochasticEventSetCollection>
</nrml>
""")

        try:
            _, path = tempfile.mkstemp()
            writer = writers.SESXMLWriter(path, sm_lt_path, gsim_lt_path)
            writer.serialize([ses1, ses2])

            expected_text = expected.readlines()
            fh = open(path, 'r')
            text = fh.readlines()
            self.assertEqual(expected_text, text)
        finally:
            os.unlink(path)

    def test_serialize_complete_lt_ses(self):
        ruptures = [
            SESRupture(
                5.5, 1.0, 40.0, 10.0, 'Active Shallow Crust', False,
                top_left_corner=(1.1, 1.01, 10.0),
                top_right_corner=(2.1, 2.01, 20.0),
                bottom_right_corner=(3.1, 3.01, 30.0),
                bottom_left_corner=(4.1, 4.01, 40.0)),
            SESRupture(
                6.5, 0.0, 41.0, 0.0, 'Active Shallow Crust', True,
                lons=[
                    [5.1, 6.1],
                    [7.1, 8.1],
                ],
                lats=[
                    [5.01, 6.01],
                    [7.01, 8.01],
                ],
                depths=[
                    [10.5, 10.6],
                    [10.7, 10.8],
                ]),
            SESRupture(
                5.4, 2.0, 42.0, 12.0, 'Stable Shallow Crust', False,
                top_left_corner=(1.1, 1.01, 10.0),
                top_right_corner=(2.1, 2.01, 20.0),
                bottom_right_corner=(3.1, 3.01, 30.0),
                bottom_left_corner=(4.1, 4.01, 40.0)),
            SESRupture(
                6.4, 3.0, 43.0, 13.0, 'Stable Shallow Crust', True,
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

        ]
        complete_lt_ses = SES(250.0, ruptures)

        expected = StringIO.StringIO("""\
<?xml version='1.0' encoding='UTF-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml" xmlns="http://openquake.org/xmlns/nrml/0.4">
  <stochasticEventSet investigationTime="250.0">
    <rupture magnitude="5.5" strike="1.0" dip="40.0" rake="10.0" tectonicRegion="Active Shallow Crust">
      <planarSurface>
        <topLeft lon="1.1" lat="1.01" depths="10.0"/>
        <topRight lon="2.1" lat="2.01" depths="20.0"/>
        <bottomRight lon="3.1" lat="3.01" depths="30.0"/>
        <bottomLeft lon="4.1" lat="4.01" depths="40.0"/>
      </planarSurface>
    </rupture>
    <rupture magnitude="6.5" strike="0.0" dip="41.0" rake="0.0" tectonicRegion="Active Shallow Crust">
      <mesh rows="2" cols="2">
        <node row="0" col="0" lon="5.1" lat="5.01" depth="10.5"/>
        <node row="0" col="1" lon="6.1" lat="6.01" depth="10.6"/>
        <node row="1" col="0" lon="7.1" lat="7.01" depth="10.7"/>
        <node row="1" col="1" lon="8.1" lat="8.01" depth="10.8"/>
      </mesh>
    </rupture>
    <rupture magnitude="5.4" strike="2.0" dip="42.0" rake="12.0" tectonicRegion="Stable Shallow Crust">
      <planarSurface>
        <topLeft lon="1.1" lat="1.01" depths="10.0"/>
        <topRight lon="2.1" lat="2.01" depths="20.0"/>
        <bottomRight lon="3.1" lat="3.01" depths="30.0"/>
        <bottomLeft lon="4.1" lat="4.01" depths="40.0"/>
      </planarSurface>
    </rupture>
    <rupture magnitude="6.4" strike="3.0" dip="43.0" rake="13.0" tectonicRegion="Stable Shallow Crust">
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

            expected_text = expected.readlines()
            fh = open(path, 'r')
            text = fh.readlines()
            self.assertEqual(expected_text, text)
        finally:
            os.unlink(path)


    def test__create_rupture_mesh_raises_on_empty_mesh(self):
        # When creating the mesh, we should raise a `ValueError` if the mesh is
        # empty.
        rup_elem = etree.Element('test_rup_elem')
        rupture = SESRupture(
            6.5, 0.0, 41.0, 0.0, 'Active Shallow Crust', True,
            lons=[[], []],
            lats=[[5.01, 6.01],
                  [7.01, 8.01]],
            depths=[[10.5, 10.6],
                    [10.7, 10.8]])

        self.assertRaises(
            ValueError, writers.SESXMLWriter._create_rupture_mesh,
            rupture, rup_elem)
